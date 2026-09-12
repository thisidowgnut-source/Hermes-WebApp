import asyncio
import os
import json
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiohttp import web
import aiohttp

# Configuration
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
N8N_WEBHOOK_URL = "http://127.0.0.1:5678/webhook/telegram-inbound"
PORT = 9221

# Initialize Bot and Dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

# Webhook handler for n8n to send messages
async def handle_n8n_webhook(request):
    try:
        data = await request.json()
        chat_id = data.get('chat_id')
        text = data.get('text', 'Hello from n8n!')
        
        # Prevent Bot loop if n8n accidentally sends to another bot chat without checks
        if chat_id:
            await bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.MARKDOWN_V2)
            return web.json_response({"status": "success"})
        else:
            return web.json_response({"status": "error", "message": "chat_id missing"}, status=400)
    except Exception as e:
        logging.error(f"Error handling n8n webhook: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)

# Telegram Command Handler
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """
    Bot-to-Bot Communication Mode: Loop Prevention
    """
    if message.from_user.is_bot:
        logging.warning(f"BLOCKED: Infinite loop prevented from bot ID {message.from_user.id}")
        return
        
    await message.answer("Sistem Omnichannel Beroperasi. Gunakan Telegram Command Center untuk arahan.")

@dp.message()
async def forward_to_n8n(message: types.Message):
    # Bot-to-Bot Loop Prevention
    if message.from_user.is_bot:
        logging.info("Ignored message from another bot to prevent loop.")
        return
    
    # Forward the message to n8n Webhook
    async with aiohttp.ClientSession() as session:
        payload = {
            "chat_id": message.chat.id,
            "text": message.text,
            "user": message.from_user.username
        }
        try:
            async with session.post(N8N_WEBHOOK_URL, json=payload) as response:
                if response.status == 200:
                    logging.info("Message forwarded to n8n successfully.")
        except Exception as e:
            logging.error(f"Failed to reach n8n: {e}")

async def start_server():
    app = web.Application()
    app.router.add_post('/webhook/n8n', handle_n8n_webhook)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    logging.info(f"Microservice Bridge listening on port {PORT}")

async def main():
    # Start web server for incoming n8n requests
    await start_server()
    # Start polling for Telegram messages
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
