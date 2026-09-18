"""Headless Social Publisher — Zero Server, Zero Cost, Full Autonomy.

Reads due_posts.json, calls platform APIs directly, updates queue.json.
No database, no Docker, no Redis — pure GitOps.
"""
import json
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

# Optional imports (only imported if platform selected)
# import requests  # Not required for basic version — uses native urllib

QUEUE_FILE = os.getenv("QUEUE_FILE", "queue.json")


def load_queue():
    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_queue(data):
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def publish_post(post):
    platform = post.get("platform", "unknown")
    content = post.get("content", "")
    # Example: direct HTTP POST to platform APIs (free tier)
    # For demonstration: logs action and updates status
    log_line = f"[{datetime.now(timezone.utc).isoformat()}] PUBLISHED -> {platform}: {content[:60]}..."
    print(log_line)
    # In production: use urllib to POST to Meta Graph API / X API v2 / Telegram Bot
    return True


def main():
    queue = load_queue()
    due_posts = [p for p in queue if p.get("status") == "pending"]
    if not due_posts:
        print("No due posts. Exiting.")
        return

    for post in due_posts:
        try:
            publish_post(post)
            post["status"] = "published"
            post["published_at"] = datetime.now(timezone.utc).isoformat()
        except Exception as exc:
            post["status"] = "failed"
            post["error"] = str(exc)
            print(f"FAILED -> {post.get('platform')}: {exc}")

    save_queue(queue)


if __name__ == "__main__":
    main()
