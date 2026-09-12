import asyncio
import os
import logging
from typing import Optional, Tuple
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiohttp import web
import aiohttp

from backend.config import config

logger = logging.getLogger(__name__)

# Global instances for bot bridge state
bot: Optional[Bot] = None
dp: Optional[Dispatcher] = None
_polling_task: Optional[asyncio.Task] = None

N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://127.0.0.1:5678/webhook/telegram-inbound")


async def cmd_start(message: types.Message):
    """
    Bot-to-Bot Communication Mode: Loop Prevention for /start command.
    Auto-registers Chat Menu Button on /start.
    """
    if message.from_user and message.from_user.is_bot:
        logger.warning(f"BLOCKED: Infinite loop prevented from bot ID {message.from_user.id}")
        return

    # Automatically set Chat Menu Button if webapp URL is available or dynamically set
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(config.BASE_DIR, ".env"), override=True)
        webapp_url = os.getenv("WEBAPP_URL", "https://trycloudflare.com")
        if bot and webapp_url:
            kb = types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton(text="🦅 Open Hermes OS", web_app=types.WebAppInfo(url=webapp_url))
            ]])
            await message.answer("🦅 **Hermes OS Command Center** Beroperasi.\nTekan butang di bawah atau gunakan **Menu Button** Telegram untuk membuka dashboard skrin penuh.", reply_markup=kb)
            return
    except Exception as e:
        logger.warning(f"Could not send inline webapp button: {e}")

    await message.answer("Sistem Omnichannel Beroperasi. Gunakan Telegram Command Center untuk arahan.")



async def forward_to_n8n(message: types.Message):
    """
    Forward incoming user message to n8n webhook with anti-loop check.
    """
    if message.from_user and message.from_user.is_bot:
        logger.info(f"Ignored message from bot ID {message.from_user.id} to prevent loop.")
        return

    async with aiohttp.ClientSession() as session:
        payload = {
            "chat_id": message.chat.id,
            "text": message.text,
            "user": message.from_user.username if message.from_user else "unknown"
        }
        try:
            async with session.post(N8N_WEBHOOK_URL, json=payload) as response:
                if response.status == 200:
                    logger.info("Message forwarded to n8n successfully.")
        except Exception as e:
            logger.error(f"Failed to reach n8n: {e}")


async def handle_n8n_webhook(request: web.Request) -> web.Response:
    """
    Webhook handler for n8n to send outbound Telegram messages.
    """
    global bot
    if not bot:
        return web.json_response({"status": "error", "message": "Bot not initialized"}, status=500)

    try:
        data = await request.json()
        chat_id = data.get('chat_id')
        text = data.get('text', 'Hello from n8n!')
        
        if chat_id:
            await bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.MARKDOWN_V2)
            return web.json_response({"status": "success"})
        else:
            return web.json_response({"status": "error", "message": "chat_id missing"}, status=400)
    except Exception as e:
        logger.error(f"Error handling n8n webhook: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def init_bot_bridge(token: Optional[str] = None) -> Tuple[Bot, Dispatcher]:
    """
    Initializes Bot and Dispatcher with anti-loop protection handlers.
    Imports TELEGRAM_BOT_TOKEN dynamically from backend.config.config.TELEGRAM_BOT_TOKEN.
    """
    global bot, dp
    bot_token = token or config.TELEGRAM_BOT_TOKEN
    if not bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN is missing or empty in configuration.")
        
    bot = Bot(token=bot_token)
    dp = Dispatcher()

    # Register handlers
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(forward_to_n8n)

    logger.info("Bot bridge initialized successfully.")
    return bot, dp


async def start_bot_polling() -> asyncio.Task:
    """
    Starts polling task for the bot.
    """
    global bot, dp, _polling_task
    if not bot or not dp:
        await init_bot_bridge()

    if _polling_task is None or _polling_task.done():
        _polling_task = asyncio.create_task(dp.start_polling(bot))
        logger.info("Bot polling task started.")
    
    return _polling_task


async def stop_bot_polling():
    """
    Stops polling task gracefully and closes bot session.
    """
    global bot, dp, _polling_task
    if dp and _polling_task and not _polling_task.done():
        await dp.stop_polling()
        _polling_task.cancel()
        try:
            await _polling_task
        except asyncio.CancelledError:
            pass
        _polling_task = None
        logger.info("Bot polling stopped.")

    if bot:
        await bot.session.close()
        logger.info("Bot session closed.")
