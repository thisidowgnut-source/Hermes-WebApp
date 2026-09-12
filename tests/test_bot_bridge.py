import pytest
import asyncio
import logging
from unittest.mock import AsyncMock, patch, MagicMock

from aiogram.types import Message, User, Chat
from backend.config import config
from backend import bot_bridge
from backend.bot_bridge import (
    init_bot_bridge,
    start_bot_polling,
    stop_bot_polling,
    cmd_start,
    forward_to_n8n
)


@pytest.mark.asyncio
async def test_init_bot_bridge_success():
    # Test initialization with dynamic config token
    valid_token = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
    with patch.object(config, "TELEGRAM_BOT_TOKEN", valid_token):
        bot, dp = await init_bot_bridge()
        assert bot is not None
        assert dp is not None
        assert bot.token == valid_token
        assert bot_bridge.bot == bot
        assert bot_bridge.dp == dp


@pytest.mark.asyncio
async def test_init_bot_bridge_missing_token():
    # Test ValueError raised when token is empty
    with patch.object(config, "TELEGRAM_BOT_TOKEN", ""):
        with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN is missing or empty"):
            await init_bot_bridge(token="")


@pytest.mark.asyncio
async def test_cmd_start_bot_to_bot_loop_prevention(caplog):
    # Simulate message coming from another bot
    bot_user = User(id=999, is_bot=True, first_name="AutomatedBot")
    chat = Chat(id=100, type="private")
    msg = Message(message_id=1, date=0, chat=chat, from_user=bot_user, text="/start")
    
    answer_mock = AsyncMock()
    object.__setattr__(msg, "answer", answer_mock)

    with caplog.at_level(logging.WARNING):
        await cmd_start(msg)

    # Verify loop prevention: message.answer should NOT be called
    answer_mock.assert_not_called()
    assert "BLOCKED: Infinite loop prevented from bot ID 999" in caplog.text


@pytest.mark.asyncio
async def test_cmd_start_human_user_allowed():
    # Simulate message coming from a human user
    human_user = User(id=888, is_bot=False, first_name="HumanUser")
    chat = Chat(id=100, type="private")
    msg = Message(message_id=2, date=0, chat=chat, from_user=human_user, text="/start")

    answer_mock = AsyncMock()
    object.__setattr__(msg, "answer", answer_mock)

    await cmd_start(msg)

    # Verify human request is processed and answered
    answer_mock.assert_called_once()


@pytest.mark.asyncio
async def test_forward_to_n8n_loop_prevention(caplog):
    # Simulate message coming from another bot
    bot_user = User(id=777, is_bot=True, first_name="BotSender")
    chat = Chat(id=200, type="private")
    msg = Message(message_id=3, date=0, chat=chat, from_user=bot_user, text="Hello world")

    with patch("aiohttp.ClientSession.post") as mock_post:
        with caplog.at_level(logging.INFO):
            await forward_to_n8n(msg)
        
        # HTTP post to n8n should NOT be made for bot user
        mock_post.assert_not_called()
        assert "Ignored message from bot ID 777 to prevent loop." in caplog.text


@pytest.mark.asyncio
async def test_forward_to_n8n_human_allowed():
    # Simulate message coming from human user
    human_user = User(id=666, is_bot=False, first_name="UserSender", username="testuser")
    chat = Chat(id=200, type="private")
    msg = Message(message_id=4, date=0, chat=chat, from_user=human_user, text="Hello n8n")

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_post_context = AsyncMock()
    mock_post_context.__aenter__.return_value = mock_response

    with patch("aiohttp.ClientSession.post", return_value=mock_post_context) as mock_post:
        await forward_to_n8n(msg)
        mock_post.assert_called_once()


@pytest.mark.asyncio
async def test_start_and_stop_bot_polling():
    valid_token = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
    with patch.object(config, "TELEGRAM_BOT_TOKEN", valid_token):
        await init_bot_bridge()
        
        with patch.object(bot_bridge.dp, "start_polling", new_callable=AsyncMock) as mock_start_polling, \
             patch.object(bot_bridge.dp, "stop_polling", new_callable=AsyncMock) as mock_stop_polling, \
             patch.object(bot_bridge.bot.session, "close", new_callable=AsyncMock) as mock_close_session:
            
            # Start polling
            task = await start_bot_polling()
            assert task is not None
            
            # Stop polling
            await stop_bot_polling()
            mock_stop_polling.assert_called_once()
            mock_close_session.assert_called_once()
