#!/usr/bin/env python3
"""
Hermes WebApp - Telegram Menu Button Setup
===========================================
Configures the Telegram Bot Menu Button to launch the Mini App.
Run after deploying the WebApp and setting up Cloudflare Tunnel.

Usage:
    python scripts/setup_telegram_menu.py
"""

import os
import json
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import config


async def setup_menu_button():
    """Set up Telegram Menu Button for the Mini App."""
    
    token = config.TELEGRAM_BOT_TOKEN
    webapp_url = config.WEBAPP_URL
    
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN not configured in .env")
        return False
    
    if not webapp_url or "trycloudflare.com" not in webapp_url:
        print("❌ WEBAPP_URL not configured properly in .env")
        print("   Should be your Cloudflare Tunnel URL (https://*.trycloudflare.com)")
        return False
    
    import aiohttp
    
    # Menu button configuration
    menu_button = {
        "type": "web_app",
        "text": "🦅 Hermes OS",
        "web_app": {
            "url": webapp_url.rstrip('/')
        }
    }
    
    url = f"https://api.telegram.org/bot{token}/setChatMenuButton"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json={"menu_button": menu_button}) as resp:
                result = await resp.json()
                
                if result.get("ok"):
                    print(f"✅ Menu button configured successfully!")
                    print(f"   Text: {menu_button['text']}")
                    print(f"   URL:  {menu_button['web_app']['url']}")
                    return True
                else:
                    print(f"❌ Failed to set menu button: {result}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error: {e}")
            return False


async def remove_menu_button():
    """Remove the menu button (reset to default)."""
    
    token = config.TELEGRAM_BOT_TOKEN
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN not configured")
        return False
    
    import aiohttp
    
    url = f"https://api.telegram.org/bot{token}/setChatMenuButton"
    payload = {"menu_button": {"type": "default"}}
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload) as resp:
                result = await resp.json()
                
                if result.get("ok"):
                    print("✅ Menu button removed (reset to default)")
                    return True
                else:
                    print(f"❌ Failed to remove menu button: {result}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error: {e}")
            return False


async def get_menu_button():
    """Get current menu button configuration."""
    
    token = config.TELEGRAM_BOT_TOKEN
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN not configured")
        return False
    
    import aiohttp
    
    url = f"https://api.telegram.org/bot{token}/getChatMenuButton"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                result = await resp.json()
                
                if result.get("ok"):
                    menu = result.get("result", {})
                    print(f"✅ Current menu button: {json.dumps(menu, indent=2)}")
                    return True
                else:
                    print(f"❌ Failed to get menu button: {result}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error: {e}")
            return False


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Telegram Menu Button Setup for Hermes OS")
    parser.add_argument("action", choices=["set", "remove", "get"], help="Action to perform")
    args = parser.parse_args()
    
    print("🦅 Hermes OS - Telegram Menu Button Setup")
    print("=" * 50)
    
    if args.action == "set":
        await setup_menu_button()
    elif args.action == "remove":
        await remove_menu_button()
    elif args.action == "get":
        await get_menu_button()


if __name__ == "__main__":
    asyncio.run(main())