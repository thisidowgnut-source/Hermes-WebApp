import os
import re
import time
import urllib.request
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

LOG_FILE = os.path.join(BASE_DIR, "logs", "cloudflared.log")

# Your Telegram user ID (per-chat override = higher priority)
USER_CHAT_ID = 6798585537

def get_bot_token():
    return os.getenv("TELEGRAM_BOT_TOKEN")

def extract_url_from_log():
    if not os.path.exists(LOG_FILE):
        return None

    url = None
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in reversed(lines):
            match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
            if match:
                url = match.group(0)
                break
    return url

def update_telegram_menu_button(token, url):
    # Set for BOTH: default (all users) + per-chat (this user specifically)
    # Per-chat override has higher priority and bypasses cache

    # 1. Set default for all new chats
    api_url = f"https://api.telegram.org/bot{token}/setChatMenuButton"
    data_default = {
        "menu_button": {
            "type": "web_app",
            "text": "OPEN Hermes OS",
            "web_app": {"url": url}
        }
    }
    req1 = urllib.request.Request(api_url, data=json.dumps(data_default).encode(), headers={'Content-Type': 'application/json'})
    try:
        resp1 = json.loads(urllib.request.urlopen(req1).read().decode())
        logging.info(f"Default menu button: {'OK' if resp1.get('ok') else 'FAIL'}")
    except Exception as e:
        logging.error(f"Default menu button error: {e}")

    # 2. Set per-chat for this user (force override, bypasses cache)
    data_perchat = {
        "chat_id": USER_CHAT_ID,
        "menu_button": {
            "type": "web_app",
            "text": "OPEN Hermes OS",
            "web_app": {"url": url}
        }
    }
    req2 = urllib.request.Request(api_url, data=json.dumps(data_perchat).encode(), headers={'Content-Type': 'application/json'})
    try:
        resp2 = json.loads(urllib.request.urlopen(req2).read().decode())
        logging.info(f"Per-chat menu button: {'OK' if resp2.get('ok') else 'FAIL'}")
        return resp2.get("ok", False)
    except Exception as e:
        logging.error(f"Per-chat menu button error: {e}")
        return False

def main():
    token = get_bot_token()
    if not token:
        logging.error("TELEGRAM_BOT_TOKEN not found in .env!")
        return

    logging.info("Waiting for Cloudflare Tunnel URL in logs...")

    max_retries = 30
    retries = 0

    while retries < max_retries:
        url = extract_url_from_log()
        if url:
            logging.info(f"Found tunnel URL: {url}")
            success = update_telegram_menu_button(token, url)
            if success:
                logging.info(f"Telegram menu updated → {url}")
                return
        time.sleep(2)
        retries += 1

    logging.error("Timeout: No Cloudflare URL found after 60 seconds.")

if __name__ == "__main__":
    main()
