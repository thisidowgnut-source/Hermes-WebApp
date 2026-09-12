import hmac
import hashlib
import urllib.parse
import json
import logging
import os
from typing import Dict, Any, Optional

from fastapi import Header, HTTPException
from backend.config import config

logger = logging.getLogger(__name__)

def verify_telegram_init_data(init_data: str, bot_token: str) -> Dict[str, Any]:
    """
    Parse and verify Telegram WebApp initData HMAC-SHA256 signature.
    
    Telegram WebApp validation algorithm:
    1. Parse init_data query string into key-value pairs.
    2. Extract and remove 'hash'.
    3. Sort remaining keys alphabetically and join as key=value separated by newline (\n).
    4. Calculate secret_key = HMAC-SHA256(b"WebAppData", bot_token).
    5. Calculate expected_hash = HMAC-SHA256(secret_key, data_check_string).hexdigest().
    6. Verify expected_hash matches received hash using constant-time comparison.
    7. Return user data dict if valid; raise HTTPException 401 if invalid.
    """
    if not init_data or not isinstance(init_data, str):
        raise HTTPException(status_code=401, detail="Invalid Telegram initData: payload missing or empty")
    
    if not bot_token:
        raise HTTPException(status_code=401, detail="Telegram bot token not provided for verification")

    try:
        parsed_pairs = urllib.parse.parse_qsl(init_data, keep_blank_values=True)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid Telegram initData format: {str(e)}")
        
    data_dict = dict(parsed_pairs)
    
    if "hash" not in data_dict:
        raise HTTPException(status_code=401, detail="Invalid Telegram initData: missing hash parameter")
        
    received_hash = data_dict.pop("hash")
    
    # Sort remaining keys alphabetically
    sorted_items = sorted(data_dict.items(), key=lambda item: item[0])
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted_items)
    
    # Calculate HMAC-SHA256 signature
    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    
    if not hmac.compare_digest(calculated_hash.lower(), received_hash.lower()):
        raise HTTPException(status_code=401, detail="Invalid Telegram WebApp signature")
        
    # Return user data dict if valid
    user_data: Dict[str, Any] = {}
    if "user" in data_dict:
        try:
            user_data = json.loads(data_dict["user"])
        except json.JSONDecodeError:
            user_data = {"raw_user": data_dict["user"]}
    else:
        user_data = data_dict.copy()
        
    return user_data

def telegram_auth_guard(init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data")) -> Dict[str, Any]:
    """
    FastAPI dependency that enforces Telegram WebApp authentication.
    If TELEGRAM_BOT_TOKEN is not set or empty, bypass in dev mode with a warning log.
    """
    bot_token = config.TELEGRAM_BOT_TOKEN or os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    if not bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN is not set. Bypassing Telegram authentication guard in dev mode.")
        if init_data:
            try:
                parsed = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
                if "user" in parsed:
                    return json.loads(parsed["user"])
            except Exception:
                pass
        return {"id": 0, "first_name": "DevUser", "username": "dev_user", "dev_mode": True}
        
    if not init_data:
        raise HTTPException(status_code=401, detail="Authentication required: X-Telegram-Init-Data header missing")
        
    return verify_telegram_init_data(init_data, bot_token)
