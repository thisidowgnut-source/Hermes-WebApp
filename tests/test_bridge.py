import pytest
import asyncio
import logging
from unittest.mock import AsyncMock
from aiogram.types import Message, User, Chat
from scripts.aiogram_bridge import cmd_start

@pytest.mark.asyncio
async def test_bot_to_bot_loop_prevention(caplog):
    # Simulate a message from another bot
    bot_user = User(id=123, is_bot=True, first_name="OtherBot")
    chat = Chat(id=456, type="private")
    msg = Message(message_id=1, date=0, chat=chat, from_user=bot_user, text="/start")
    answer_mock = AsyncMock()
    object.__setattr__(msg, "answer", answer_mock)
    
    with caplog.at_level(logging.WARNING):
        await cmd_start(msg)
    
    # Assert that answer was NOT called due to loop prevention
    answer_mock.assert_not_called()
    assert "BLOCKED: Infinite loop prevented from bot ID 123" in caplog.text

@pytest.mark.asyncio
async def test_human_allowed():
    human_user = User(id=789, is_bot=False, first_name="Human")
    chat = Chat(id=456, type="private")
    msg = Message(message_id=2, date=0, chat=chat, from_user=human_user, text="/start")
    answer_mock = AsyncMock()
    object.__setattr__(msg, "answer", answer_mock)
    
    await cmd_start(msg)
    
    # Assert that answer WAS called
    answer_mock.assert_called_once()
