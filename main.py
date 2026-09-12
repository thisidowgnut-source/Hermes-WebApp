import logging
import uvicorn
import socket
from backend.main import app
from backend.config import config

logger = logging.getLogger("uvicorn")

def is_port_available(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return True
        except Exception:
            return False

if __name__ == "__main__":
    candidate_ports = [config.PORT, 9230, 9225, 9255, 9290, 8080]
    seen = set()
    ports = [p for p in candidate_ports if not (p in seen or seen.add(p))]

    for p in ports:
        if is_port_available(config.HOST, p):
            print(f"[*] Launching Hermes OS WebApp on http://{config.HOST}:{p}")
            uvicorn.run(app, host=config.HOST, port=p)
            break
        else:
            print(f"[-] Port {p} unavailable. Trying next port...")
