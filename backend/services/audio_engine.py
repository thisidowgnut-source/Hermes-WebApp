import math
import numpy as np
import logging

logger = logging.getLogger(__name__)

class AudioEngine:
    """
    Audio Engine for Hermes-WebApp R2:
    - Voice Activity Detection (VAD) via RMS & dB thresholding.
    - STEM Demux Frequency Filtering (Vocals, Drums, Bass, Other).
    - Voice CLI Command Intent Parser for speech-to-action automation.
    """
    def __init__(self, vad_threshold: float = 0.02, sample_rate: int = 16000):
        self.vad_threshold = float(vad_threshold)
        self.sample_rate = int(sample_rate)
        self.processed_frames = 0
        
        # Command intent map (keyword phrases -> action & CLI command)
        self.intent_rules = [
            {
                "keywords": ["open terminal", "launch terminal", "terminal", "powershell", "open shell", "cli"],
                "intent": "open_terminal",
                "command": "pwsh.exe",
                "action_type": "macro"
            },
            {
                "keywords": ["system status", "status", "system stats", "cpu usage", "metrics", "health"],
                "intent": "system_status",
                "command": "get-system-stats",
                "action_type": "info"
            },
            {
                "keywords": ["show swarm", "swarm control", "agents list", "swarm agents", "active swarm"],
                "intent": "swarm_control",
                "command": "swarm-agents-list",
                "action_type": "navigation"
            },
            {
                "keywords": ["clean temp", "clear temp", "cleanup temporary", "clean cache"],
                "intent": "clean_temp",
                "command": "powershell -Command Remove-Item $env:TEMP\\* -Recurse -Force",
                "action_type": "macro"
            },
            {
                "keywords": ["lock pc", "lock workstation", "lock computer", "lock screen"],
                "intent": "lock_pc",
                "command": "rundll32.exe user32.dll,LockWorkStation",
                "action_type": "macro"
            },
            {
                "keywords": ["kill zombies", "cleanup zombies", "terminate zombies", "kill zombie processes"],
                "intent": "cleanup_zombies",
                "command": "python scripts/cleanup_tasks.py",
                "action_type": "macro"
            },
            {
                "keywords": ["obsidian", "open obsidian", "vault notes", "notes context"],
                "intent": "open_obsidian",
                "command": "obsidian-context",
                "action_type": "navigation"
            },
            {
                "keywords": ["kanban", "show kanban", "tasks board", "kanban tasks"],
                "intent": "view_kanban",
                "command": "kanban-view",
                "action_type": "navigation"
            },
            {
                "keywords": ["clear queue", "clean queue", "reset queue"],
                "intent": "clear_queue",
                "command": "queue-clear",
                "action_type": "macro"
            },
            {
                "keywords": ["stop agents", "terminate agents", "kill all agents"],
                "intent": "stop_agents",
                "command": "stop-all-agents",
                "action_type": "macro"
            },
            {
                "keywords": ["help", "voice help", "command list"],
                "intent": "show_help",
                "command": "voice-help",
                "action_type": "info"
            }
        ]

    def set_vad_threshold(self, threshold: float) -> float:
        self.vad_threshold = float(max(0.001, min(1.0, float(threshold))))
        return self.vad_threshold

    def pcm_to_float_array(self, pcm_bytes: bytes) -> np.ndarray:
        """Converts 16-bit PCM little-endian byte stream to normalized float array [-1.0, 1.0]."""
        if not pcm_bytes:
            return np.array([], dtype=np.float32)
        if len(pcm_bytes) % 2 != 0:
            pcm_bytes = pcm_bytes[: len(pcm_bytes) - 1]
        if len(pcm_bytes) == 0:
            return np.array([], dtype=np.float32)
            
        int_data = np.frombuffer(pcm_bytes, dtype=np.int16)
        float_data = int_data.astype(np.float32) / 32768.0
        return float_data

    def detect_vad(self, pcm_bytes: bytes) -> dict:
        """
        Voice Activity Detection (VAD) using Root Mean Square (RMS) energy.
        """
        samples = self.pcm_to_float_array(pcm_bytes)
        if len(samples) == 0:
            return {
                "is_speech": False,
                "rms": 0.0,
                "db": -100.0,
                "vad_threshold": float(self.vad_threshold)
            }

        rms_val = float(np.sqrt(np.mean(samples ** 2)))
        db_val = float(20.0 * math.log10(rms_val + 1e-9))
        is_speech = bool(rms_val >= self.vad_threshold)

        return {
            "is_speech": is_speech,
            "rms": float(round(rms_val, 6)),
            "db": float(round(db_val, 2)),
            "vad_threshold": float(round(float(self.vad_threshold), 4))
        }

    def process_stem(self, pcm_bytes: bytes, sample_rate: int = 16000) -> dict:
        """
        STEM Demux frequency band filter processing:
        Splits spectral energy into 4 stems: Vocals, Drums, Bass, Other.
        Calculates energy distribution and 32-bin downsampled spectral envelope.
        """
        self.processed_frames += 1
        samples = self.pcm_to_float_array(pcm_bytes)
        
        if len(samples) == 0:
            return {
                "status": "empty",
                "stems": {"vocals": 0.0, "drums": 0.0, "bass": 0.0, "other": 0.0},
                "spectrum": [0.0] * 32,
                "sample_rate": int(sample_rate)
            }

        # Real FFT calculation
        n = len(samples)
        fft_vals = np.abs(np.fft.rfft(samples))
        freqs = np.fft.rfftfreq(n, d=1.0 / float(sample_rate))

        # Spectral energy calculation per frequency band (STEMs)
        bass_mask = (freqs >= 20) & (freqs < 250)
        drums_mask = ((freqs >= 60) & (freqs < 250)) | ((freqs >= 2500) & (freqs < 6000))
        vocals_mask = (freqs >= 250) & (freqs < 3400)
        other_mask = (freqs >= 3400)

        total_energy = float(np.sum(fft_vals)) + 1e-9

        bass_energy = float(np.sum(fft_vals[bass_mask])) if np.any(bass_mask) else 0.0
        drums_energy = float(np.sum(fft_vals[drums_mask])) if np.any(drums_mask) else 0.0
        vocals_energy = float(np.sum(fft_vals[vocals_mask])) if np.any(vocals_mask) else 0.0
        other_energy = float(np.sum(fft_vals[other_mask])) if np.any(other_mask) else 0.0

        norm_factor = float(max(1.0, (bass_energy + drums_energy + vocals_energy + other_energy)))
        
        stems = {
            "vocals": float(round(float(min(1.0, (vocals_energy * 1.5) / norm_factor)), 4)),
            "drums": float(round(float(min(1.0, (drums_energy * 1.4) / norm_factor)), 4)),
            "bass": float(round(float(min(1.0, (bass_energy * 1.6) / norm_factor)), 4)),
            "other": float(round(float(min(1.0, (other_energy * 1.2) / norm_factor)), 4))
        }

        # Downsample spectrum into 32 frequency bins
        bin_count = 32
        max_fft = float(np.max(fft_vals)) + 1e-9
        bins = np.array_split(fft_vals, bin_count)
        spectrum = [float(round(float(np.mean(b)) / max_fft, 4)) for b in bins if len(b) > 0]
        while len(spectrum) < bin_count:
            spectrum.append(0.0)

        return {
            "status": "success",
            "stems": stems,
            "spectrum": [float(x) for x in spectrum[:bin_count]],
            "sample_rate": int(sample_rate),
            "samples_count": int(len(samples))
        }

    def parse_command(self, text: str) -> dict:
        """
        Voice CLI Command Intent Parser:
        Matches input transcript/phrase against defined intent rules.
        """
        if not text or not str(text).strip():
            return {
                "raw_text": "",
                "matched": False,
                "intent": "unknown",
                "command": None,
                "confidence": 0.0
            }

        text_clean = str(text).strip().lower()

        best_match = None
        highest_score = 0.0

        for rule in self.intent_rules:
            for kw in rule["keywords"]:
                if kw in text_clean:
                    score = float(len(kw) / max(len(text_clean), 1))
                    if kw == text_clean:
                        score = 1.0
                    else:
                        score = min(0.95, score + 0.5)

                    if score > highest_score:
                        highest_score = score
                        best_match = rule

        if best_match and highest_score >= 0.3:
            return {
                "raw_text": str(text).strip(),
                "matched": True,
                "intent": best_match["intent"],
                "command": best_match["command"],
                "action_type": best_match["action_type"],
                "confidence": float(round(highest_score, 2))
            }

        return {
            "raw_text": str(text).strip(),
            "matched": False,
            "intent": "unknown",
            "command": None,
            "confidence": 0.0
        }

    def get_status(self) -> dict:
        return {
            "status": "active",
            "vad_threshold": float(self.vad_threshold),
            "sample_rate": int(self.sample_rate),
            "processed_frames": int(self.processed_frames),
            "stems_supported": ["vocals", "drums", "bass", "other"],
            "intent_rules_count": len(self.intent_rules)
        }

audio_engine = AudioEngine()
