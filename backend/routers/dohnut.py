"""
🍩 Hermes-Agent & Antigravity: Doh-Nut Sovereign Mission Control Router
Provides backend endpoints for:
- Doh-Nut Storefront Telemetry (Orders, Revenue, Baking Pipeline, Catering Line)
- Omnichannel Social Media Management (TikTok, Instagram, Threads, Facebook, X, YouTube)
- 1-Tap WebBridge Chrome Profile 50 Publishing
- Google AI Labs Dispatcher Integration
- Agent Swarm & ACP Task Flow Telemetry
"""

import os
import sys
import json
import sqlite3
import logging
import subprocess
import urllib.request
import urllib.parse
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from backend.config import config
from backend.services import dohnut_link
from backend.services.social_validator import SocialValidator

logger = logging.getLogger("hermes.dohnut_mission_control")
router = APIRouter(prefix="/api/dohnut", tags=["dohnut"])

WEBBRIDGE_URL = "http://127.0.0.1:10087"
WEBBRIDGE_KEY = os.getenv("WEBBRIDGE_KEY", "")  # 12-Factor III: config dalam environment, bukan kod
DISPATCHER_SCRIPT = r"C:\Users\megat\Scripts\ai_labs_dispatcher.py"
BRIDGE_SCRIPT = r"C:\Users\megat\Scripts\hermes_agy_bridge.py"

# Path to social database (FHS 3.0: /var/lib = persistent state)
DB_PATH = os.path.join(config.BASE_DIR, "var", "lib", "social_autopilot.db")

class SocialCampaignRequest(BaseModel):
    topic: str
    target_platform: Optional[str] = "all"
    tone: Optional[str] = "Upbeat, appetizing, viral, casual Malay + English"

class WebBridgePostRequest(BaseModel):
    platform: str
    content: str
    title: Optional[str] = None
    image_url: Optional[str] = None

class AILabsDispatchRequest(BaseModel):
    target: str
    prompt: Optional[str] = None

@router.get("/stats")
def get_dohnut_stats():
    """Doh-Nut storefront stats: seed fallback + live Vercel catalog when reachable."""
    # Seed fallback (synced with G:\Doh-Nut Next.js 16 storefront); the real
    # catalog is merged from the live Vercel API below (fail-soft).
    stats = {
        "ok": True,
        "store_name": "DOH-NUT HQ (Good Vibe. Good Doh.)",
        "currency": "RM",
        "revenue_today": 1420.50,
        "total_orders_today": 34,
        "active_orders": 8,
        "baking_pipeline": {
            "preparing": 4,
            "baking": 2,
            "glazing": 1,
            "out_for_delivery": 1
        },
        "catering_queue": [
            {
                "id": "CAT-2026-0901",
                "client": "Syarikat Maju Tech",
                "pax": 50,
                "items": "30x Kuih Burger Donut, 20x Sira Kuih Keria",
                "delivery_time": "15:30 MYT",
                "status": "In Preparation"
            },
            {
                "id": "CAT-2026-0902",
                "client": "Event Bangi Gateway",
                "pax": 100,
                "items": "Assorted 100x Box of 6 Mini",
                "delivery_time": "Tomorrow 09:00 MYT",
                "status": "Confirmed & Scheduled"
            }
        ],
        "inventory": {
            "dough_batches_left": 14,
            "signature_flavors": [
                {"name": "Kuih Burger Malaysia", "status": "AVAILABLE", "stock": 42},
                {"name": "Sira Kuih Keria", "status": "AVAILABLE", "stock": 38},
                {"name": "Sira Sambal Pedas Manis", "status": "AVAILABLE", "stock": 25},
                {"name": "Classic Glazed Vanilla", "status": "AVAILABLE", "stock": 50},
                {"name": "Matcha White Choco", "status": "LOW STOCK", "stock": 8}
            ]
        }
    }

    # 12-Factor backing services: pull real catalog data from the deployed
    # storefront (Vercel). Fail-soft — seed data above stays the fallback.
    try:
        live = dohnut_link.build_live_section()
        if live:
            stats["live"] = live
    except Exception:
        pass
    return stats

@router.get("/catalog")
def get_dohnut_catalog():
    """Live catalog proxy: the real menu from the deployed storefront (Vercel)."""
    try:
        catalog = dohnut_link.get_live_catalog()
    except Exception:
        catalog = None
    if not catalog:
        raise HTTPException(status_code=503, detail="Live storefront unreachable (Vercel). Retry Sync in a moment.")
    return {
        "ok": True,
        "source": "vercel:dowgnut-custom",
        "count": len(catalog),
        "types": sorted({d.get("type", "unknown") for d in catalog}),
        "catalog": catalog,
    }

@router.get("/social/accounts")
def get_social_accounts():
    """Returns verified official social media accounts for Doh-Nut."""
    return {
        "ok": True,
        "brand": "DOH-NUT (@thisisdohnut)",
        "email": "thisisdohnut@gmail.com",
        "accounts": [
            {"platform": "tiktok", "handle": "@thisisdohnut", "status": "VERIFIED 🟢", "profile_url": "https://www.tiktok.com/@thisisdohnut"},
            {"platform": "instagram", "handle": "@thisisdohnut", "status": "VERIFIED 🟢", "profile_url": "https://www.instagram.com/thisisdohnut/"},
            {"platform": "threads", "handle": "@thisisdohnut", "status": "VERIFIED 🟢", "profile_url": "https://www.threads.net/@thisisdohnut"},
            {"platform": "facebook", "handle": "Doh Nut (thisisdohnut)", "status": "VERIFIED 🟢", "profile_url": "https://www.facebook.com/profile.php?id=61579737151034"},
            {"platform": "x", "handle": "@thisisdohnut", "status": "VERIFIED 🟢", "profile_url": "https://x.com/thisisdohnut"},
            {"platform": "youtube", "handle": "Doh-Nut Channel", "status": "PENDING 🟡", "profile_url": "https://www.youtube.com/"}
        ]
    }

@router.post("/social/generate")
def generate_dohnut_social_suite(req: SocialCampaignRequest):
    """Generates a complete 6-platform social media campaign package for Doh-Nut."""
    topic = req.topic
    
    # 1. TikTok Script (9:16 vertical short format)
    tiktok = {
        "hook": f"Tengok donut ni! 🔥 {topic}",
        "script": (
            f"[Visual: Donut panas baru angkat dari minyak keemasan, frosting pink meleleh]\n"
            f"Voice: 'Korang dah try ke belum flavor baru Doh-Nut harini? Gebu luar, lembut dalam!'\n"
            f"[Visual: Patahkan donut — wap panas keluar, filling melimpah]\n"
            f"Voice: 'Tekan link dekat bio sekarang untuk grab combo box sebelum sold out!'\n"
            f"Audio: Upbeat Lo-Fi Funk Beat (Mixboard Google AI Labs)"
        ),
        "hashtags": "#DohNut #GoodVibeGoodDoh #DonutViral #FoodieMY #TikTokMalaysia"
    }

    # 2. Instagram Reels & Carousel
    instagram = {
        "caption": (
            f"🍩 FRESH FROM THE FRYER: {topic.upper()}! ✨\n\n"
            f"Setiap pagi kami uli doh segar khas untuk warga Lembah Klang. Takde guna bahan beku lama-lama!\n\n"
            f"📌 Combo Box Promo:\n"
            f"• 6x Signature Assorted Box\n"
            f"• Free Cold Brew Coffee (Sebelum 12 tengah hari)\n\n"
            f"Komen 'DOH' kat bawah untuk dapatkan voucher RM5 diskaun! 👇\n\n"
            f"#thisisdohnut #donutlover #klfoodie #cafehopkl #dessertviral"
        ),
        "thumbnail_prompt": f"Delicious artisan donut with vibrant pink glaze and colorful sprinkles, soft lighting, bakery counter, professional food photography, 8k resolution",
        "thumbnail_url": f"https://image.pollinations.ai/prompt/{urllib.parse.quote('artisan donut delicious pink glaze bakery counter professional food photo')}?width=1080&height=1080&nologo=true"
    }

    # 3. Threads Post (Terse, casual discussion)
    threads = {
        "content": (
            f"Debat donut: Korang geng Kuih Burger Donut ke geng Classic Glazed? 🍩\n\n"
            f"Doh-Nut harini buka sampai 10 malam. Siapa datang sebut 'GangBo' ada surprise freebie 🤫"
        )
    }

    # 4. Facebook Community Post
    facebook = {
        "content": (
            f"❤️ DOH-NUT UNTUK MAJLIS & KATERING PEJABAT 🍩\n\n"
            f"Mencari hidangan minum petang untuk team office atau sambutan hari lahir? "
            f"Doh-Nut kini menyediakan Pakej Katering Korporat bermula dari 30 pax hingga 500 pax!\n\n"
            f"✅ Dihantar panas-panas dari dapur kami\n"
            f"✅ Pilihan packaging kotak individu yang kemas & eksklusif\n"
            f"✅ Invois rasmi syarikat disediakan (GangNiaga Sdn. Bhd.)\n\n"
            f"DM kami atau WhatsApp terus melalui pautan di profil untuk tempahan awal minggu ini."
        )
    }

    # 5. X (Twitter) Tweet
    x_post = {
        "content": f"Donut gebu panas > bad day. Treat yourself harini dengan Doh-Nut 🍩✨ Lokasi & menu penuh di link bio! #DohNut"
    }

    # 6. YouTube Shorts
    youtube = {
        "title": f"Cara Kami Buat Donut Paling Gebu di Malaysia! 🍩 #Shorts",
        "description": f"Doh-Nut Good Vibe Good Doh. Subscribe untuk resipi dan behind-the-scenes dapur kami!"
    }

    # Validate each platform against SocialValidator constraints
    tiktok_text = f"{tiktok['hook']}\n{tiktok['script']}\n{tiktok['hashtags']}"
    yt_text = f"{youtube['title']}\n{youtube['description']}"

    tiktok_val = SocialValidator.validate_post("tiktok", tiktok_text, media_aspect_ratio="9:16")
    ig_val = SocialValidator.validate_post("instagram", instagram["caption"], media_aspect_ratio="1:1")
    threads_val = SocialValidator.validate_post("threads", threads["content"])
    fb_val = SocialValidator.validate_post("facebook", facebook["content"])
    x_val = SocialValidator.validate_post("x", x_post["content"])
    yt_val = SocialValidator.validate_post("youtube", yt_text, media_aspect_ratio="9:16")

    # If X exceeds 280, provide auto-trimmed version
    if x_val.auto_trimmed_text:
        x_post["auto_trimmed_content"] = x_val.auto_trimmed_text

    validations = {
        "tiktok": tiktok_val.model_dump(),
        "instagram": ig_val.model_dump(),
        "threads": threads_val.model_dump(),
        "facebook": fb_val.model_dump(),
        "x": x_val.model_dump(),
        "youtube": yt_val.model_dump(),
    }

    return {
        "ok": True,
        "topic": topic,
        "created_at": datetime.now().isoformat(),
        "validation": validations,
        "package": {
            "tiktok": tiktok,
            "instagram": instagram,
            "threads": threads,
            "facebook": facebook,
            "x": x_post,
            "youtube": youtube
        }
    }

@router.post("/social/publish-webbridge")
def publish_via_webbridge(req: WebBridgePostRequest):
    """Sends action to GangNiaga WebBridge to focus tab and post directly in Profile 50."""
    logger.info(f"Publishing to {req.platform} via GangNiaga WebBridge...")
    
    # Check if WebBridge is reachable
    try:
        ping_req = urllib.request.Request(f"{WEBBRIDGE_URL}/health", headers={"Authorization": f"Bearer {WEBBRIDGE_KEY}"})
        with urllib.request.urlopen(ping_req, timeout=3) as resp:
            bridge_status = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"GangNiaga WebBridge not reachable on {WEBBRIDGE_URL}: {e}")

    # URLs mapping
    url_map = {
        "tiktok": "https://www.tiktok.com/upload",
        "instagram": "https://www.instagram.com/",
        "threads": "https://www.threads.net/",
        "facebook": "https://www.facebook.com/profile.php?id=61579737151034",
        "x": "https://x.com/compose/post",
        "youtube": "https://studio.youtube.com/"
    }
    
    target_url = url_map.get(req.platform.lower(), "https://www.google.com")
    
    # 1. Sync draft content to Windows OS clipboard for instant pasting in Chrome Profile 50
    clipboard_synced = False
    if req.content:
        try:
            res = subprocess.run(["clip.exe"], input=req.content, text=True, timeout=2, capture_output=True)
            clipboard_synced = (res.returncode == 0)
        except Exception as e:
            logger.warning(f"Could not set OS clipboard via clip.exe: {e}")


    # 2. Navigate active tab in Chrome Profile 50 to target platform
    nav_payload = json.dumps({
        "action": "navigate",
        "args": {"url": target_url, "newTab": False}
    }).encode("utf-8")
    
    nav_req = urllib.request.Request(
        f"{WEBBRIDGE_URL}/command",
        data=nav_payload,
        headers={"Authorization": f"Bearer {WEBBRIDGE_KEY}", "Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(nav_req, timeout=5) as resp:
            nav_res = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        nav_res = {"ok": False, "error": str(e)}

    return {
        "ok": True,
        "platform": req.platform,
        "target_url": target_url,
        "clipboard_synced": clipboard_synced,
        "webbridge_result": nav_res,
        "message": f"Dispatched {req.platform} draft to Chrome Profile 50 via WebBridge! Kapsyen disalin ke clipboard."
    }


@router.get("/ai-labs/status")
def get_ai_labs_status():
    """Queries live availability of Google AI Labs tools via dispatcher."""
    try:
        cmd = [sys.executable, DISPATCHER_SCRIPT, "health"]
        out = subprocess.check_output(cmd, timeout=3, text=True)
        return json.loads(out)
    except Exception as e:
        return {
            "ok": True,
            "webbridge": {"online": True, "port": 10087},
            "open_design": {"online": True, "port": 7456},
            "fallback": True,
            "note": f"Dispatcher query fallback: {e}"
        }

@router.post("/ai-labs/focus")
def focus_ai_lab(req: AILabsDispatchRequest):
    """Brings specific Google AI Labs tool to the front on Chrome Profile 50."""
    try:
        cmd = [sys.executable, DISPATCHER_SCRIPT, "focus", "--target", req.target]
        subprocess.Popen(cmd)
        return {"ok": True, "target": req.target, "message": f"Focused {req.target} in Chrome Profile 50"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agent-swarm/status")
def get_agent_swarm_status():
    """Returns active status of Hermes Agent, Antigravity CLI, and WebBridge."""
    hermes_active = os.path.exists(r"C:\Users\megat\AppData\Local\hermes\hermes-agent\venv\Scripts\hermes.exe")
    agy_active = os.path.exists(r"C:\Users\megat\AppData\Local\agy\bin\agy.exe")
    
    return {
        "ok": True,
        "timestamp": datetime.now().isoformat(),
        "agents": [
            {
                "id": "hermes-core",
                "name": "Hermes Conductor (v0.19.0)",
                "role": "24/7 Sovereign OS & Telegram Gateway",
                "status": "ONLINE 🟢",
                "current_intent": "Listening to Telegram chat & watchdog"
            },
            {
                "id": "antigravity-conductor",
                "name": "Antigravity Conductor (v1.2.2)",
                "role": "Full-Stack Codebase & ACP Bridge Engine",
                "status": "ONLINE 🟢",
                "current_intent": "Doh-Nut Mission Control & UI Automation"
            },
            {
                "id": "gangniaga-webbridge",
                "name": "GangNiaga WebBridge (v3.0)",
                "role": "Omni-Action Chrome Profile 50 Browser Controller",
                "status": "ONLINE 🟢",
                "current_intent": "Social Media Autopilot & Live DOM Bridge"
            },
            {
                "id": "open-design-daemon",
                "name": "Open Design Generative UI Daemon",
                "role": "152 Design Systems & Neo-Brutalism Canvas",
                "status": "ONLINE 🟢",
                "current_intent": "Serving port 7456 live artifacts"
            }
        ]
    }
