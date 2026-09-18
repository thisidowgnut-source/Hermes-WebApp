"""Migration CLI and service to import legacy social drafts into durable mission ledger."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
from typing import Any, Dict, List, Optional, Union
import uuid

from pydantic import BaseModel, ConfigDict, Field

try:
    from backend.services.mission_store import MissionStore
except ImportError:
    MissionStore = None  # type: ignore


class MigrationReport(BaseModel):
    """Execution report for social migration."""
    model_config = ConfigDict(extra="ignore")

    written_rows: int = 0
    total_candidates: int = 0
    source_sha256: str
    manifest_id: Optional[str] = None
    errors: List[str] = Field(default_factory=list)

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)

    def get(self, item: str, default: Any = None) -> Any:
        return getattr(self, item, default)


def _hash_content(content: str) -> str:
    """Compute SHA256 hex digest of UTF-8 content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _extract_candidates(src_path: Path) -> List[Dict[str, Any]]:
    """Extract candidate records from JSON or SQLite legacy files."""
    if src_path.suffix.lower() == ".json":
        text = src_path.read_text(encoding="utf-8")
        data = json.loads(text)
        if isinstance(data, list):
            return [dict(d) for d in data if isinstance(d, dict)]
        if isinstance(data, dict):
            for key in ("candidates", "posts", "drafts", "items"):
                if key in data and isinstance(data[key], list):
                    return [dict(d) for d in data[key] if isinstance(d, dict)]
            return [data]
        return []

    # Assume SQLite database
    conn = sqlite3.connect(str(src_path))
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]

        target_table = None
        for candidate_table in ("omnichannel_drafts", "posts", "drafts", "social_posts", "campaigns"):
            if candidate_table in tables:
                target_table = candidate_table
                break

        if not target_table and tables:
            target_table = tables[0]

        if not target_table:
            return []

        cursor.execute(f"SELECT * FROM {target_table}")
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def migrate_legacy_social(
    source: Union[Path, str],
    destination: Union[Path, str],
    dry_run: bool = True,
) -> MigrationReport:
    """Migrates legacy social autopilot posts/drafts into the durable missions schema.

    - Reads legacy social posts / drafts (from SQLite or JSON).
    - Validates and hashes content using SHA256.
    - In dry-run mode (dry_run=True): writes 0 rows to destination, computes SHA256 checksums,
      returns MigrationReport(written_rows=0, total_candidates=N, source_sha256=...).
    - In live mode (dry_run=False): inserts migrated rows into missions.db
      campaigns/approvals/publication_attempts tables with migration manifest record.
    """
    src_path = Path(source)
    if not src_path.exists():
        raise FileNotFoundError(f"Legacy social source file does not exist: {source}")

    # Compute source SHA256
    source_bytes = src_path.read_bytes()
    source_sha256 = hashlib.sha256(source_bytes).hexdigest()

    # Extract raw candidates
    raw_candidates = _extract_candidates(src_path)

    # Validate and structure each candidate
    structured_candidates: List[Dict[str, Any]] = []
    errors: List[str] = []

    for idx, raw in enumerate(raw_candidates):
        try:
            topic = raw.get("topic") or raw.get("title") or f"Legacy Post {idx + 1}"
            
            # Map platform contents
            platform_contents: Dict[str, str] = {}
            if raw.get("fb_content"):
                platform_contents["facebook"] = str(raw["fb_content"])
            if raw.get("ig_content"):
                platform_contents["instagram"] = str(raw["ig_content"])
            if raw.get("tiktok_script"):
                platform_contents["tiktok"] = str(raw["tiktok_script"])
            if raw.get("youtube_content"):
                platform_contents["youtube"] = str(raw["youtube_content"])
            if raw.get("content"):
                plat = raw.get("platform") or "all"
                platform_contents[plat] = str(raw["content"])

            if not platform_contents:
                # If no specific platform content, create a default body from whatever text is available
                fallback_text = str(raw.get("text") or raw.get("body") or topic)
                platform_contents["general"] = fallback_text

            # Compute content hashes
            content_hashes = {p: _hash_content(c) for p, c in platform_contents.items()}

            structured_candidates.append({
                "legacy_id": raw.get("id"),
                "topic": topic,
                "platform_contents": platform_contents,
                "content_hashes": content_hashes,
                "status": str(raw.get("status") or "pending_approval"),
                "created_at": str(raw.get("created_at") or datetime.now(timezone.utc).isoformat()),
                "published_at": raw.get("published_at"),
                "remote_post_id": raw.get("remote_post_id"),
            })
        except Exception as exc:
            errors.append(f"Candidate {idx} parsing failed: {str(exc)}")

    total_candidates = len(structured_candidates)

    # Dry-run mode: NEVER write to destination
    if dry_run:
        return MigrationReport(
            written_rows=0,
            total_candidates=total_candidates,
            source_sha256=source_sha256,
            manifest_id=None,
            errors=errors,
        )

    # Live mode: initialize destination and write records
    dest_path = Path(destination)
    if MissionStore is not None:
        store = MissionStore(dest_path)
        store.initialize()
    else:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        # Fallback table initialization
        with sqlite3.connect(str(dest_path)) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS campaigns (
                    id TEXT PRIMARY KEY,
                    project_slug TEXT NOT NULL,
                    source_facts TEXT NOT NULL,
                    drafts TEXT NOT NULL,
                    brand_truth_hash TEXT NOT NULL,
                    content_hashes TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS approvals (
                    id TEXT PRIMARY KEY,
                    campaign_id TEXT,
                    mission_id TEXT,
                    platform TEXT NOT NULL,
                    account_id TEXT NOT NULL,
                    content_sha256 TEXT NOT NULL,
                    media_sha256 TEXT NOT NULL DEFAULT '[]',
                    status TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    decided_at TEXT,
                    decided_by TEXT
                );
                CREATE TABLE IF NOT EXISTS publication_attempts (
                    id TEXT PRIMARY KEY,
                    campaign_id TEXT NOT NULL,
                    approval_id TEXT,
                    platform TEXT NOT NULL,
                    state TEXT NOT NULL,
                    remote_post_id TEXT,
                    published_at TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS migration_manifests (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    applied_at TEXT NOT NULL
                );
            """)

    written_rows = 0
    manifest_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    conn = sqlite3.connect(str(dest_path), isolation_level=None)
    try:
        conn.execute("BEGIN IMMEDIATE;")
        cursor = conn.cursor()

        for item in structured_candidates:
            campaign_id = str(uuid.uuid4())
            source_facts = json.dumps({
                "source": str(src_path),
                "source_sha256": source_sha256,
                "legacy_id": item["legacy_id"],
                "topic": item["topic"],
            })
            drafts_json = json.dumps(item["platform_contents"])
            content_hashes_json = json.dumps(item["content_hashes"])

            cursor.execute(
                """
                INSERT INTO campaigns (
                    id, project_slug, source_facts, drafts, brand_truth_hash, content_hashes, created_at
                )
                VALUES (?, 'doh-nut', ?, ?, 'legacy_unattested', ?, ?)
                """,
                (campaign_id, source_facts, drafts_json, content_hashes_json, item["created_at"]),
            )
            written_rows += 1

            for platform, content_str in item["platform_contents"].items():
                c_hash = item["content_hashes"][platform]
                approval_id = str(uuid.uuid4())
                is_pub = item["status"] in ("published", "approved")
                app_status = "approved" if is_pub else "pending"

                cursor.execute(
                    """
                    INSERT INTO approvals (
                        id, campaign_id, mission_id, platform, account_id,
                        content_sha256, media_sha256, status, expires_at,
                        created_at, decided_at, decided_by
                    )
                    VALUES (?, ?, NULL, ?, 'dohnut_official', ?, '[]', ?, ?, ?, ?, ?)
                    """,
                    (
                        approval_id,
                        campaign_id,
                        platform,
                        c_hash,
                        app_status,
                        now_iso,
                        item["created_at"],
                        now_iso if is_pub else None,
                        "legacy_migrator" if is_pub else None,
                    ),
                )
                written_rows += 1

                if item.get("published_at") or item["status"] == "published":
                    attempt_id = str(uuid.uuid4())
                    cursor.execute(
                        """
                        INSERT INTO publication_attempts (
                            id, campaign_id, approval_id, platform, state,
                            remote_post_id, published_at, created_at
                        )
                        VALUES (?, ?, ?, ?, 'published', ?, ?, ?)
                        """,
                        (
                            attempt_id,
                            campaign_id,
                            approval_id,
                            platform,
                            item.get("remote_post_id"),
                            item.get("published_at") or now_iso,
                            item["created_at"],
                        ),
                    )
                    written_rows += 1

        # Record migration manifest
        manifest_name = f"legacy_social_{src_path.stem}_{source_sha256[:8]}"
        cursor.execute(
            """
            INSERT INTO migration_manifests (id, name, applied_at)
            VALUES (?, ?, ?)
            """,
            (manifest_id, manifest_name, now_iso),
        )
        written_rows += 1

        conn.execute("COMMIT;")
    except Exception:
        conn.execute("ROLLBACK;")
        conn.close()
        raise
    finally:
        conn.close()

    return MigrationReport(
        written_rows=written_rows,
        total_candidates=total_candidates,
        source_sha256=source_sha256,
        manifest_id=manifest_id,
        errors=errors,
    )


def main() -> None:
    """CLI entrypoint for running legacy social migrations."""
    parser = argparse.ArgumentParser(description="Migrate legacy social posts into missions.db")
    parser.add_argument("--source", required=True, help="Path to legacy SQLite or JSON source")
    parser.add_argument("--destination", required=True, help="Path to destination missions.db")
    parser.add_argument("--live", action="store_true", help="Perform live migration (default is dry-run)")

    args = parser.parse_args()
    report = migrate_legacy_social(
        source=args.source,
        destination=args.destination,
        dry_run=not args.live,
    )
    print(json.dumps(report.model_dump(), indent=2))
    sys.exit(0 if not report.errors else 1)


if __name__ == "__main__":
    main()
