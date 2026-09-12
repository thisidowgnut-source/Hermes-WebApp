import requests
import os
import json

BOT_TOKEN = "8655264276:AAG6hhn802TSm6EKnxgSb6xeCMrpMqFj1ck"
CHAT_ID = "<YOUR_CHAT_ID>" # Replace later

def send_approval_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "✅ Lulus & Post", "callback_data": "action_approve"},
                {"text": "❌ Batal", "callback_data": "action_reject"}
            ],
            [
                {"text": "✏️ Minta Hermes Edit", "callback_data": "action_revise"}
            ]
        ]
    }
    
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "reply_markup": json.dumps(keyboard)
    }
    
    response = requests.post(url, json=payload)
    print(response.json())

if __name__ == "__main__":
    send_approval_message("Draf Artikel SEO untuk Klien A dah siap. Sila sahkan:")
