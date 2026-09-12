"""Doh-Nut live link client (Hermes <-> Vercel production storefront).

Pulls real catalog data from the deployed Doh-Nut app
(https://dowgnut-custom.vercel.app). 12-Factor III: endpoint and keys come
from environment variables, not code. All functions are fail-soft: any
network/auth failure returns None so callers fall back to seed data.
"""

import json
import logging
import os
import time
import urllib.request
from datetime import datetime

logger = logging.getLogger("dohnut_link")

DOHNUT_API_URL = os.getenv("DOHNUT_API_URL", "https://dowgnut-custom.vercel.app").rstrip("/")
DOHNUT_ADMIN_API_KEY = os.getenv("DOHNUT_ADMIN_API_KEY", "")
_TIMEOUT_S = 6
_CACHE_TTL_S = 30

_cache = {"ts": 0.0, "section": None}


def _fetch_json(path: str, headers: dict = None):
    """GET {DOHNUT_API_URL}{path} and decode JSON. Raises on any failure."""
    req = urllib.request.Request(f"{DOHNUT_API_URL}{path}", headers=headers or {})
    with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_live_catalog():
    """GET /api/donuts (public). Returns the donut catalog list, or None."""
    if not DOHNUT_API_URL:
        return None
    try:
        data = _fetch_json("/api/donuts")
        return data if isinstance(data, list) and data else None
    except Exception as exc:  # fail-soft: seed fallback
        logger.warning("live catalog fetch failed: %s", exc)
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

    section = {
        "source": "vercel:dowgnut-custom",
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
