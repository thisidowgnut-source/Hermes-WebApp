import subprocess
import re
import requests
import sys
import os
import time
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PORT = os.getenv("PORT", "9230")

def update_env_webapp_url(url: str):
    """Save latest active Cloudflare tunnel URL to .env as WEBAPP_URL."""
    env_file = os.path.join(BASE_DIR, ".env")
    if not os.path.exists(env_file):
        return
    try:
        with open(env_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        updated = False
        new_lines = []
        for line in lines:
            if line.startswith("WEBAPP_URL="):
                new_lines.append(f'WEBAPP_URL="{url}"\n')
                updated = True
            else:
                new_lines.append(line)
                
        if not updated:
            new_lines.append(f'\nWEBAPP_URL="{url}"\n')
            
        with open(env_file, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print(f"[+] Updated WEBAPP_URL in .env -> {url}")
    except Exception as e:
        print(f"[-] Could not update .env: {e}")

def main():
    print(f"Starting cloudflared tunnel forwarding to http://localhost:{PORT}...")
    
    # Run cloudflared as a subprocess and merge stderr into stdout
    process = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", f"http://localhost:{PORT}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    url_pattern = re.compile(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com')
    tunnel_url = None
    
    for line in process.stdout:
        print(line, end="")
        if not tunnel_url:
            match = url_pattern.search(line)
            if match:
                tunnel_url = match.group(0)
                print(f"\n[+] Found Live Tunnel URL: {tunnel_url}")
                
                # Persist WEBAPP_URL to .env for bot bridge
                update_env_webapp_url(tunnel_url)
                
                # Set Telegram Chat Menu Button to launch WebApp full-screen
                tokens_to_update = []
                if BOT_TOKEN and "***" not in BOT_TOKEN:
                    tokens_to_update.append(BOT_TOKEN)
                # Additional bot tokens can be added via TELEGRAM_EXTRA_TOKENS env var (comma-separated)
                extra_tokens = os.getenv("TELEGRAM_EXTRA_TOKENS", "")
                for extra in extra_tokens.split(","):
                    extra = extra.strip()
                    if extra and extra not in tokens_to_update:
                        tokens_to_update.append(extra)
                
                for token in tokens_to_update:
                    bot_id = token.split(':')[0]
                    print(f"[+] Setting Telegram Chat Menu Button for Bot {bot_id}: {tunnel_url}")
                    try:
                        menu_payload = {
                            "menu_button": {
                                "type": "web_app",
                                "text": "Open Hermes OS",
                                "web_app": {"url": tunnel_url}
                            }
                        }
                        menu_res = requests.post(f"https://api.telegram.org/bot{token}/setChatMenuButton", json=menu_payload, timeout=10)
                        if menu_res.status_code == 200 and menu_res.json().get('ok'):
                            print(f"[+] SUCCESS: Chat Menu Button set for Bot {bot_id}!")
                        else:
                            print(f"[-] Failed for Bot {bot_id}: {menu_res.text}")
                    except Exception as e:
                        print(f"[-] Error setting Chat Menu Button for Bot {bot_id}: {e}")

    process.wait()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting cloudflared updater...")
        sys.exit(0)
