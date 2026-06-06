"""
cache_utils.py — simple ZIP-level filesystem cache for SnapReport (MVP).
Stores JSON blobs under `snapreport/cache/` with a TTL (default 24h).
"""

import os
import json
import time

CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")
TTL = int(os.getenv("SNAP_CACHE_TTL", 60 * 60 * 24))  # 24 hours by default


def _path_for(key: str) -> str:
    return os.path.join(CACHE_DIR, f"{key}.json")


def load_market_data(zip_code: str):
    path = _path_for(f"market_{zip_code}")
    if not os.path.exists(path):
        return None
    try:
        mtime = os.path.getmtime(path)
        if time.time() - mtime > TTL:
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_market_data(zip_code: str, data: dict):
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = _path_for(f"market_{zip_code}")
    try:
        # strip non-serializable types if present
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        # best-effort cache; don't raise to avoid breaking generation
        return
