"""Doh-Nut live link client (Hermes <-> Vercel production storefront).

Pulls real catalog data from the deployed Doh-Nut app
(https://dowgnut-custom.vercel.app). 12-Factor III: endpoint and keys come
from environment variables, not code. All functions are fail-soft: any
network/auth failure returns None so callers fall back to seed data.
"""

import json
import logging
import os
import sqlite3
import time
import urllib.request
from datetime import datetime

logger = logging.getLogger("dohnut_link")

DEFAULT_VERCEL_URL = "https://dowgnut-custom.vercel.app"
LOCAL_DEV_URL = "http://127.0.0.1:3000"
DOHNUT_ADMIN_API_KEY = os.getenv("DOHNUT_ADMIN_API_KEY", "")
_TIMEOUT_S = 6
_CACHE_TTL_S = 30

_cache = {"ts": 0.0, "section": None}


def resolve_dohnut_url() -> tuple[str, str]:
    """
    Intelligently resolves whether local dev server (http://127.0.0.1:3000) or
    production Vercel (https://dowgnut-custom.vercel.app) is active.
    Returns (base_url, source_label).
    """
    env_url = os.getenv("DOHNUT_API_URL", "").strip().rstrip("/")
    if env_url:
        source = "local:3000" if ("3000" in env_url or "127.0.0.1" in env_url or "localhost" in env_url) else "custom_env"
        return env_url, source

    # Probe local server on 127.0.0.1:3000 with 300ms timeout
    try:
        req = urllib.request.Request(f"{LOCAL_DEV_URL}/api/donuts", headers={"User-Agent": "Hermes-DohnutProbe"})
        with urllib.request.urlopen(req, timeout=0.3) as resp:
            if resp.status == 200:
                return LOCAL_DEV_URL, "local:nextjs-dev"
    except Exception:
        pass

    return DEFAULT_VERCEL_URL, "vercel:dowgnut-custom"


def get_local_sqlite_catalog() -> list | None:
    """Fallback to direct SQLite query if G:\\Doh-Nut DB file exists on host."""
    local_db_paths = [
        r"G:\Doh-Nut\db\custom.db",
        r"G:\Doh-Nut\prisma\dev.db",
    ]
    for db_path in local_db_paths:
        if os.path.exists(db_path):
            try:
                with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=1.0) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM Donut ORDER BY createdAt DESC")
                    rows = [dict(r) for r in cursor.fetchall()]
                    if rows:
                        return rows
            except Exception as e:
                logger.debug("Local sqlite read error: %s", e)
    return None


def _fetch_json(path: str, headers: dict = None):
    """GET {base_url}{path} and decode JSON. Raises on any failure."""
    base_url, _ = resolve_dohnut_url()
    req = urllib.request.Request(f"{base_url}{path}", headers=headers or {})
    with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_live_catalog():
    """GET /api/donuts (public). Returns the donut catalog list, or None."""
    try:
        data = _fetch_json("/api/donuts")
        if isinstance(data, list) and data:
            return data
    except Exception as exc:
        logger.debug("live HTTP catalog fetch failed: %s", exc)

    # Fallback to local SQLite if HTTP is unreachable
    local_data = get_local_sqlite_catalog()
    if local_data:
        return local_data

    return None


def get_live_admin_stats():
    """GET /api/admin/stats (needs DOHNUT_ADMIN_API_KEY). Returns dict or None."""
    if not DOHNUT_API_URL or not DOHNUT_ADMIN_API_KEY:
        return None
    try:
        return _fetch_json(
            "/api/admin/stats",
            {"Authorization": f"Bearer {DOHNUT_ADMIN_API_KEY}"},
        )
    except Exception as exc:  # fail-soft: seed fallback
        logger.warning("live admin stats fetch failed: %s", exc)
        return None


def build_live_section():
    """Additive 'live' block for /api/dohnut/stats, cached for _CACHE_TTL_S.

    Returns None when the storefront is unreachable — callers keep seed data.
    """
    now = time.time()
    if _cache["section"] is not None and (now - _cache["ts"]) < _CACHE_TTL_S:
        return _cache["section"]

    catalog = get_live_catalog()
    if not catalog:
        return None

    _, source = resolve_dohnut_url()
    section = {
        "source": source,
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "catalog_count": len(catalog),
        "catalog": catalog[:8],
        "types": sorted({d.get("type", "unknown") for d in catalog}),
        "lowest_stock": sorted(catalog, key=lambda d: d.get("stock", 0))[:3],
    }

    admin = get_live_admin_stats()
    if admin:
        section["admin"] = {
            "total_revenue": admin.get("totalRevenue"),
            "total_orders": admin.get("totalOrders"),
            "top_donuts": admin.get("topDonuts"),
        }

    _cache["ts"] = now
    _cache["section"] = section
    return section
