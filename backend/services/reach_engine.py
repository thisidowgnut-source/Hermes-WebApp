"""
🌐 Hermes-Agent: Agent-Reach Ingestion Engine (v3.9.0)
Connects 15-platform Internet Capability Router (yt-dlp, Jina Reader, feedparser, public APIs)
directly to Hermes-WebApp's viral engine and omnichannel draft system.
"""

from __future__ import annotations

import asyncio
import glob
import json
import logging
import os
import re
import shutil
import sqlite3
import tempfile
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

try:
    import feedparser
except ImportError:
    feedparser = None

from backend.config import config
from backend.services.social_validator import SocialValidator

logger = logging.getLogger("hermes.reach_engine")

AGENT_REACH_BIN = os.getenv(
    "AGENT_REACH_BIN",
    r"C:\Users\megat\AppData\Local\hermes\hermes-agent\venv\Scripts\agent-reach.exe"
)
YT_DLP_BIN = os.getenv(
    "YT_DLP_BIN",
    r"C:\Users\megat\AppData\Local\hermes\hermes-agent\venv\Scripts\yt-dlp.exe"
)
DB_PATH = os.path.join(config.BASE_DIR, "var", "lib", "social_autopilot.db")


class ReachEngine:
    """Core ingestion engine leveraging agent-reach capabilities."""

    @staticmethod
    def _find_binary(preferred_path: str, default_name: str) -> str:
        """Resolves binary from preferred path or system PATH."""
        if os.path.isfile(preferred_path):
            return preferred_path
        which_path = shutil.which(default_name)
        if which_path:
            return which_path
        return preferred_path

    @classmethod
    async def get_status(cls, timeout: float = 8.0) -> Dict[str, Any]:
        """Runs `agent-reach doctor --json` or returns structured fallback."""
        bin_path = cls._find_binary(AGENT_REACH_BIN, "agent-reach")
        if os.path.isfile(bin_path):
            try:
                proc = await asyncio.create_subprocess_exec(
                    bin_path,
                    "doctor",
                    "--json",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
                if proc.returncode == 0 and stdout:
                    raw_json = stdout.decode("utf-8", errors="ignore").strip()
                    data = json.loads(raw_json)
                    return {
                        "status": "online",
                        "engine": "agent-reach-cli",
                        "binary": bin_path,
                        "platforms": data,
                    }
            except Exception as err:
                logger.warning(f"agent-reach doctor check encountered error: {err}")

        # Fail-soft structured fallback
        yt_ready = os.path.isfile(cls._find_binary(YT_DLP_BIN, "yt-dlp"))
        return {
            "status": "online",
            "engine": "hermes-native-reach",
            "binary": bin_path if os.path.isfile(bin_path) else "fallback",
            "platforms": {
                "youtube": {"status": "ok" if yt_ready else "off", "active_backend": "yt-dlp"},
                "web": {"status": "ok", "active_backend": "Jina Reader"},
                "rss": {"status": "ok" if feedparser else "off", "active_backend": "feedparser"},
                "v2ex": {"status": "ok", "active_backend": "V2EX API (public)"},
                "bilibili": {"status": "ok", "active_backend": "B站搜索 API"},
                "github": {"status": "ok", "active_backend": "gh CLI"},
            },
        }

    @classmethod
    async def read_url_jina(cls, url: str, timeout: float = 15.0) -> Dict[str, Any]:
        """Reads any URL via Jina Reader (https://r.jina.ai/) into clean markdown."""
        target_url = url.strip()
        if not target_url.startswith(("http://", "https://")):
            target_url = f"https://{target_url}"

        jina_endpoint = f"https://r.jina.ai/{target_url}"
        headers = {
            "User-Agent": "agent-reach/1.5.0 (Hermes-OS/3.9.0)",
            "Accept": "text/plain, text/markdown, application/json",
            "X-No-Cache": "true",
        }

        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                resp = await client.get(jina_endpoint, headers=headers)
                if resp.status_code == 200 and resp.text:
                    markdown = resp.text.strip()
                    title = ""
                    for line in markdown.splitlines():
                        if line.startswith("# "):
                            title = line.replace("# ", "").strip()
                            break
                    if not title:
                        title = target_url.split("//")[-1].split("/")[0]

                    return {
                        "status": "success",
                        "source": "jina-reader",
                        "url": target_url,
                        "title": title,
                        "word_count": len(markdown.split()),
                        "content": markdown[:10000],
                    }
                else:
                    logger.warning(f"Jina Reader non-200: {resp.status_code}")
        except Exception as e:
            logger.warning(f"Jina Reader fetch failed: {e}")

        # Fallback to direct fetch
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                direct_resp = await client.get(target_url, headers={"User-Agent": "Mozilla/5.0"})
                if direct_resp.status_code == 200:
                    text_content = direct_resp.text
                    clean_text = re.sub(r"<[^>]+>", " ", text_content)
                    clean_text = re.sub(r"\s+", " ", clean_text).strip()
                    return {
                        "status": "success",
                        "source": "direct-http-fallback",
                        "url": target_url,
                        "title": target_url,
                        "word_count": len(clean_text.split()),
                        "content": clean_text[:8000],
                    }
        except Exception as direct_err:
            logger.error(f"Direct fetch fallback error: {direct_err}")

        return {
            "status": "error",
            "source": "failed",
            "url": target_url,
            "title": target_url,
            "content": f"Failed to retrieve content from {target_url}",
            "error": "Connection or reading timeout",
        }

    @classmethod
    async def extract_youtube(cls, url: str, timeout: float = 30.0) -> Dict[str, Any]:
        """Extracts YouTube subtitles and metadata using yt-dlp without downloading media."""
        bin_path = cls._find_binary(YT_DLP_BIN, "yt-dlp")
        target_url = url.strip()

        with tempfile.TemporaryDirectory() as temp_dir:
            metadata: Dict[str, Any] = {}
            try:
                proc_meta = await asyncio.create_subprocess_exec(
                    bin_path,
                    "--dump-single-json",
                    "--skip-download",
                    "--no-warnings",
                    target_url,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout_meta, _ = await asyncio.wait_for(proc_meta.communicate(), timeout=timeout / 2)
                if proc_meta.returncode == 0 and stdout_meta:
                    metadata = json.loads(stdout_meta.decode("utf-8", errors="ignore"))
            except Exception as meta_err:
                logger.warning(f"yt-dlp dump-json error: {meta_err}")

            subtitles_text = ""
            sub_source = "none"
            try:
                sub_out_template = os.path.join(temp_dir, "%(id)s.%(ext)s")
                proc_sub = await asyncio.create_subprocess_exec(
                    bin_path,
                    "--write-sub",
                    "--write-auto-sub",
                    "--sub-lang", "en.*,ms.*,id.*",
                    "--sub-format", "vtt/srt/best",
                    "--skip-download",
                    "--no-warnings",
                    "-o", sub_out_template,
                    target_url,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await asyncio.wait_for(proc_sub.communicate(), timeout=timeout / 2)

                sub_files = glob.glob(os.path.join(temp_dir, "*.vtt")) + glob.glob(os.path.join(temp_dir, "*.srt"))
                if sub_files:
                    with open(sub_files[0], "r", encoding="utf-8", errors="ignore") as sf:
                        raw_sub = sf.read()
                    cleaned = re.sub(r"\d{2}:\d{2}:\d{2}\.\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}\.\d{3}.*", "", raw_sub)
                    cleaned = re.sub(r"\d{2}:\d{2}\.\d{3}\s*-->\s*\d{2}:\d{2}\.\d{3}.*", "", cleaned)
                    cleaned = re.sub(r"<[^>]+>", "", cleaned)
                    cleaned = re.sub(r"^\d+$", "", cleaned, flags=re.MULTILINE)
                    cleaned = re.sub(r"WEBVTT.*", "", cleaned)
                    lines = [ln.strip() for ln in cleaned.splitlines() if ln.strip()]
                    dedup_lines: List[str] = []
                    for ln in lines:
                        if not dedup_lines or dedup_lines[-1] != ln:
                            dedup_lines.append(ln)
                    subtitles_text = " ".join(dedup_lines)[:10000]
                    sub_source = "extracted-subtitles"
            except Exception as sub_err:
                logger.warning(f"yt-dlp subtitle extraction error: {sub_err}")

            title = metadata.get("title") or "YouTube Video"
            description = metadata.get("description") or ""
            duration = metadata.get("duration") or 0
            channel = metadata.get("uploader") or metadata.get("channel") or "Unknown Creator"

            final_content = subtitles_text if subtitles_text else description
            if not final_content:
                final_content = f"Title: {title}\nChannel: {channel}\nURL: {target_url}"

            return {
                "status": "success",
                "source": sub_source,
                "url": target_url,
                "title": title,
                "channel": channel,
                "duration_seconds": duration,
                "has_subtitles": bool(subtitles_text),
                "transcript": subtitles_text[:10000],
                "description": description[:3000],
                "content": final_content[:10000],
            }

    @classmethod
    def read_rss(cls, url: str, limit: int = 5) -> Dict[str, Any]:
        """Reads RSS/Atom feed using feedparser."""
        if not feedparser:
            return {"status": "error", "message": "feedparser library not installed"}
        try:
            feed = feedparser.parse(url)
            entries = []
            for item in feed.entries[:limit]:
                entries.append({
                    "title": getattr(item, "title", "No Title"),
                    "link": getattr(item, "link", ""),
                    "summary": getattr(item, "summary", "")[:500],
                    "published": getattr(item, "published", ""),
                })
            return {
                "status": "success",
                "feed_title": feed.feed.get("title", url),
                "entries_count": len(entries),
                "entries": entries,
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @classmethod
    def synthesize_omnichannel_copy(
        cls,
        title: str,
        content: str,
        source_type: str = "web",
        target_audience: str = "Usahawan & Peminat Teknologi",
        language: str = "Bahasa Melayu & English",
        tone: str = "Berpengaruh, santai, praktikal",
    ) -> Dict[str, str]:
        """Synthesizes high-conversion omnichannel copy from ingested content."""
        clean_title = title.strip() or "Trend & Inspirasi Terkini"
        summary_snippet = content[:600].replace("\n", " ").strip()

        # 1. Facebook
        fb_content = (
            f"🔥 **{clean_title}**\n\n"
            f"Korang perasan tak trend terbaru ni? Berdasarkan analisa mendalam:\n\n"
            f"📌 **Intipati Utama:**\n"
            f"{summary_snippet}...\n\n"
            f"💡 **Pengajaran untuk Bisnes & Creator:**\n"
            f"1. Pasaran bergerak pantas, siapa lambat adaptasi akan tertinggal.\n"
            f"2. Manfaatkan automasi dan content berimpak tinggi untuk kekal relevan.\n"
            f"3. Konsistensi merentas pelbagai platform (omnichannel) adalah kunci utama.\n\n"
            f"Apa pandangan korang tentang isu ni? Setuju ke tak? Komen di bawah! 👇\n\n"
            f"#Trending #BisnesOnline #Inovasi #HermesOS #OmnichannelAutopilot"
        )

        # 2. Instagram Carousel
        ig_content = (
            f"📸 5 KUNCI PENTING: {clean_title.upper()}\n\n"
            f"Swipe left untuk ringkasan penuh! 👉\n\n"
            f"Slide 1: Kenapa topik ini meletup dan jadi bualan ramai?\n"
            f"Slide 2: Ringkasan Analisa — {summary_snippet[:150]}...\n"
            f"Slide 3: Strategi pelaksanaan pantas untuk usahawan & pencipta kandungan.\n"
            f"Slide 4: Kesilapan biasa yang patut korang elakkan.\n"
            f"Slide 5: Simpan post ini dan tag rakan bisnes korang!\n\n"
            f"---\n"
            f"💡 Nak blueprint automasi penuh macam ni? Komen 'BLUEPRINT' sekarang!\n\n"
            f"#InstagramMarketing #ContentStrategy #ViralTrends #DohNut #HermesAgent"
        )

        # 3. TikTok 30-Second Script
        tiktok_script = (
            f"🎬 [TIKTOK SHORT SCRIPT - 30 SAAT]\n"
            f"⏱️ 00:00 - 00:03 (HOOK): 'Stop scroll! Korang tahu tak pasal {clean_title[:35]} yang tengah viral sekarang?'\n"
            f"⏱️ 00:04 - 00:15 (BODY): 'Ramai yang terlepas pandang rahsia ni. {summary_snippet[:140]}...'\n"
            f"⏱️ 00:16 - 00:25 (PROOF): 'Bila kitorang kaji flow dia, strategi ni memang jimat masa dan terus naikkan engagement berganda.'\n"
            f"⏱️ 00:26 - 00:30 (CTA): 'Tekan butang follow sekarang kalau korang nak lebih banyak tip viral RM0 macam ni!'"
        )

        # 4. YouTube Video / Shorts Content
        youtube_content = (
            f"▶️ TAJUK: Bedah Siasat: {clean_title} | Strategi & Analisa Terkini 2026 #Shorts\n\n"
            f"📝 DESKRIPSI:\n"
            f"Video ini merungkai analisa terperinci mengenai {clean_title}.\n\n"
            f"Poin Penting:\n"
            f"{summary_snippet[:300]}...\n\n"
            f"⏱️ TIMESTAMPS:\n"
            f"0:00 - Pengenalan & Hook\n"
            f"0:45 - Bedah Siasat Data & Trend\n"
            f"2:10 - Tindakan Pantas Usahawan\n"
            f"3:30 - Kesimpulan\n\n"
            f"🏷️ TAGS: {clean_title[:30]}, viral trend, AI automasi, Hermes Agent, omnichannel marketing"
        )

        img_prompt = (
            f"Hyper-detailed cinematic YouTube thumbnail about {clean_title[:50]}, "
            f"sleek neon obsidian aesthetic, 8k resolution, bold typography visual"
        )

        return {
            "topic": clean_title,
            "fb_content": fb_content,
            "ig_content": ig_content,
            "tiktok_script": tiktok_script,
            "youtube_content": youtube_content,
            "image_prompt": img_prompt,
        }

    @classmethod
    async def ingest_to_omnichannel(
        cls,
        url: str,
        source_type: str = "auto",
        target_audience: str = "Usahawan & Peminat Teknologi",
        language: str = "Bahasa Melayu & English",
        tone: str = "Berpengaruh, santai, praktikal",
        auto_save: bool = True,
    ) -> Dict[str, Any]:
        """Complete workflow: Ingests URL/Video -> Synthesizes Omnichannel Copy -> Saves Draft -> Validates."""
        target_url = url.strip()

        is_youtube = "youtube.com" in target_url.lower() or "youtu.be" in target_url.lower()
        if source_type == "youtube" or (source_type == "auto" and is_youtube):
            ingest_result = await cls.extract_youtube(target_url)
            resolved_source = "youtube"
        else:
            ingest_result = await cls.read_url_jina(target_url)
            resolved_source = "web"

        title = ingest_result.get("title", "Ingested Content")
        content = ingest_result.get("content", "")

        copy_pack = cls.synthesize_omnichannel_copy(
            title=title,
            content=content,
            source_type=resolved_source,
            target_audience=target_audience,
            language=language,
            tone=tone,
        )

        encoded_prompt = urllib.parse.quote(copy_pack["image_prompt"])
        thumbnail_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720&nologo=true"

        draft_id = None
        if auto_save:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO omnichannel_drafts 
                    (topic, fb_content, ig_content, tiktok_script, youtube_content, thumbnail_url, image_prompt, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'pending_approval')
                """, (
                    copy_pack["topic"],
                    copy_pack["fb_content"],
                    copy_pack["ig_content"],
                    copy_pack["tiktok_script"],
                    copy_pack["youtube_content"],
                    thumbnail_url,
                    copy_pack["image_prompt"],
                ))
                draft_id = cursor.lastrowid
                conn.commit()

        fb_val = SocialValidator.validate_post("facebook", copy_pack["fb_content"])
        ig_val = SocialValidator.validate_post("instagram", copy_pack["ig_content"])
        tiktok_val = SocialValidator.validate_post("tiktok", copy_pack["tiktok_script"], media_aspect_ratio="9:16")
        yt_val = SocialValidator.validate_post("youtube", copy_pack["youtube_content"], media_aspect_ratio="9:16")

        return {
            "status": "success",
            "source_type": resolved_source,
            "url": target_url,
            "draft_id": draft_id,
            "title": title,
            "content_preview": content[:300],
            "facebook": copy_pack["fb_content"],
            "instagram": copy_pack["ig_content"],
            "tiktok": copy_pack["tiktok_script"],
            "youtube": copy_pack["youtube_content"],
            "thumbnail_url": thumbnail_url,
            "state": "pending_approval",
            "validation": {
                "facebook": fb_val.model_dump(),
                "instagram": ig_val.model_dump(),
                "tiktok": tiktok_val.model_dump(),
                "youtube": yt_val.model_dump(),
            },
        }
