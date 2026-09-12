import os
import json
import subprocess

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
QUEUE_FILE = os.path.join(BASE_DIR, ".queue", "queue.json")

def add_to_queue(post_data: dict, queue_file: str = None) -> bool:
    target_queue_file = queue_file or QUEUE_FILE
    os.makedirs(os.path.dirname(target_queue_file), exist_ok=True)
    data = []
    
    if os.path.exists(target_queue_file):
        try:
            with open(target_queue_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    data = json.loads(content)
        except json.JSONDecodeError as e:
            backup_path = os.path.join(os.path.dirname(target_queue_file), "queue_corrupted.json")
            if os.path.exists(target_queue_file):
                os.replace(target_queue_file, backup_path)
            raise ValueError(f"Corrupted JSON in queue file. Backed up to {backup_path}") from e
            
    data.append(post_data)
    
    with open(target_queue_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
        
    if queue_file is None:
        try:
            subprocess.run(["git", "add", target_queue_file], cwd=BASE_DIR, check=True)
            subprocess.run(["git", "commit", "-m", "chore: update staging queue"], cwd=BASE_DIR, check=True)
        except subprocess.CalledProcessError:
            pass # Ignore git errors in testing
        
    return True

