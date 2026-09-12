import os
import sys
import json
import uuid
import time
import psutil
import threading
import subprocess
from datetime import datetime, timezone
from backend.config import config

SWARM_QUEUE_FILE = os.path.join(config.BASE_DIR, ".queue", "swarm_agents.json")

class SwarmManager:
    """
    Singleton service managing multi-agent swarm processes, process metrics,
    state persistence, logs, and process lifecycle.
    """
    def __init__(self, file_path: str = SWARM_QUEUE_FILE):
        self.file_path = file_path
        self._lock = threading.Lock()
        self._processes = {}  # agent_id -> subprocess.Popen
        self.agents = {}      # agent_id -> agent dict
        self._load_state()

    def _load_state(self):
        with self._lock:
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            if os.path.exists(self.file_path):
                try:
                    with open(self.file_path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        if content:
                            data = json.loads(content)
                            if isinstance(data, dict):
                                self.agents = data
                            else:
                                self.agents = {}
                        else:
                            self.agents = {}
                except Exception:
                    self.agents = {}

            if not isinstance(self.agents, dict):
                self.agents = {}

            # Sync active processes status on startup
            changed = False
            for agent_id, agent in self.agents.items():
                if agent.get("status") == "running":
                    pid = agent.get("pid")
                    if not pid or not psutil.pid_exists(pid):
                        agent["status"] = "failed" if agent.get("exit_code") != 0 else "completed"
                        agent["finished_at"] = datetime.now(timezone.utc).isoformat()
                        changed = True
            if changed:
                self._save_state_unlocked()

    def _save_state_unlocked(self):
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.agents, f, indent=2)

    def _save_state(self):
        with self._lock:
            self._save_state_unlocked()

    def spawn_agent(self, name: str = None, task: str = None, command: str = None) -> dict:
        agent_id = f"agent-{uuid.uuid4().hex[:8]}"
        name = name.strip() if name else f"Subagent-{agent_id}"
        task = task.strip() if task else "Background swarm execution"

        if not command:
            # Default cross-platform Python script simulating agent work
            py_code = (
                "import time, sys; "
                f"print('Agent {name} starting task: {task}'); "
                "sys.stdout.flush(); "
                "time.sleep(12); "
                "print('Agent task completed successfully.'); "
                "sys.stdout.flush()"
            )
            command = f'"{sys.executable}" -c "{py_code}"'

        timestamp = datetime.now(timezone.utc).isoformat()
        time_str = datetime.now(timezone.utc).strftime("%H:%M:%S")

        # Spawn process
        proc = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        agent_data = {
            "id": agent_id,
            "name": name,
            "task": task,
            "command": command,
            "pid": proc.pid,
            "status": "running",
            "created_at": timestamp,
            "finished_at": None,
            "exit_code": None,
            "logs": [f"[{time_str}] Swarm agent spawned (PID {proc.pid})"]
        }

        with self._lock:
            self._processes[agent_id] = proc
            self.agents[agent_id] = agent_data
            self._save_state_unlocked()

        # Start log collector thread
        t = threading.Thread(target=self._monitor_process, args=(agent_id, proc), daemon=True)
        t.start()

        return self.get_agent(agent_id)

    def _monitor_process(self, agent_id: str, proc: subprocess.Popen):
        try:
            if proc.stdout:
                for line in iter(proc.stdout.readline, ''):
                    if not line:
                        break
                    clean_line = line.rstrip()
                    if clean_line:
                        time_str = datetime.now(timezone.utc).strftime("%H:%M:%S")
                        with self._lock:
                            if agent_id in self.agents:
                                self.agents[agent_id]["logs"].append(f"[{time_str}] {clean_line}")
                                self._save_state_unlocked()
        except Exception:
            pass

        proc.wait()
        exit_code = proc.returncode

        with self._lock:
            if agent_id in self.agents:
                agent = self.agents[agent_id]
                # Only update status if not already set to failed (e.g., via termination)
                if agent["status"] == "running":
                    agent["status"] = "completed" if exit_code == 0 else "failed"
                agent["exit_code"] = exit_code
                agent["finished_at"] = datetime.now(timezone.utc).isoformat()
                time_str = datetime.now(timezone.utc).strftime("%H:%M:%S")
                agent["logs"].append(f"[{time_str}] Process exited with code {exit_code} ({agent['status']})")
                self._save_state_unlocked()
            if agent_id in self._processes:
                del self._processes[agent_id]

    def get_agent_metrics(self, agent_id: str) -> dict:
        with self._lock:
            agent = self.agents.get(agent_id)
        if not agent or agent.get("status") != "running":
            return {"cpu_percent": 0.0, "memory_mb": 0.0, "memory_percent": 0.0}

        pid = agent.get("pid")
        if not pid:
            return {"cpu_percent": 0.0, "memory_mb": 0.0, "memory_percent": 0.0}

        try:
            p = psutil.Process(pid)
            with p.oneshot():
                cpu = p.cpu_percent(interval=None)
                mem = p.memory_info().rss / (1024 * 1024)
                mem_pct = p.memory_percent()
            return {
                "cpu_percent": round(cpu, 1),
                "memory_mb": round(mem, 1),
                "memory_percent": round(mem_pct, 1)
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return {"cpu_percent": 0.0, "memory_mb": 0.0, "memory_percent": 0.0}

    def get_agent(self, agent_id: str) -> dict:
        with self._lock:
            agent = self.agents.get(agent_id)
            if not agent:
                return None
            agent_copy = json.loads(json.dumps(agent))

        agent_copy["metrics"] = self.get_agent_metrics(agent_id)
        return agent_copy

    def get_agents(self) -> list:
        with self._lock:
            agent_ids = list(self.agents.keys())
        
        result = []
        for aid in agent_ids:
            a = self.get_agent(aid)
            if a:
                result.append(a)
        
        # Sort newest first
        result.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return result

    def terminate_agent(self, agent_id: str) -> dict:
        with self._lock:
            agent = self.agents.get(agent_id)
            if not agent:
                return None
            
            proc = self._processes.get(agent_id)
            pid = agent.get("pid")

        if agent.get("status") == "running":
            # Attempt to kill process via Popen handle or psutil
            if proc and proc.poll() is None:
                try:
                    proc.terminate()
                    proc.wait(timeout=1.0)
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass
            elif pid and psutil.pid_exists(pid):
                try:
                    p = psutil.Process(pid)
                    p.terminate()
                    p.wait(timeout=1.0)
                except Exception:
                    try:
                        p.kill()
                    except Exception:
                        pass

            with self._lock:
                agent["status"] = "failed"
                agent["finished_at"] = datetime.now(timezone.utc).isoformat()
                time_str = datetime.now(timezone.utc).strftime("%H:%M:%S")
                agent["logs"].append(f"[{time_str}] Process manually terminated")
                self._save_state_unlocked()

        return self.get_agent(agent_id)

    def get_telemetry(self) -> dict:
        agents = self.get_agents()
        active_agents = [a for a in agents if a.get("status") == "running"]
        
        total_cpu = round(sum(a["metrics"]["cpu_percent"] for a in active_agents), 1)
        total_mem_mb = round(sum(a["metrics"]["memory_mb"] for a in active_agents), 1)

        sys_cpu = psutil.cpu_percent(interval=None)
        sys_mem = psutil.virtual_memory().percent

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "active_count": len(active_agents),
            "total_count": len(agents),
            "swarm_metrics": {
                "total_cpu_percent": total_cpu,
                "total_memory_mb": total_mem_mb
            },
            "system_metrics": {
                "cpu_percent": sys_cpu,
                "memory_percent": sys_mem
            },
            "agents": agents
        }

swarm_manager = SwarmManager()
