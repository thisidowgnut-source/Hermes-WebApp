"""Tests for legacy social data migration (dry-run and live import)."""
import json
from pathlib import Path
import sqlite3
import pytest

from backend.cli.migrate_legacy_social import migrate_legacy_social, MigrationReport


@pytest.fixture
def legacy_sqlite(tmp_path):
    """Creates a sample legacy social_autopilot.db SQLite database."""
    db_path = tmp_path / "social_autopilot.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE omnichannel_drafts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            fb_content TEXT,
            ig_content TEXT,
            tiktok_script TEXT,
            youtube_content TEXT,
            thumbnail_url TEXT,
            image_prompt TEXT,
            status TEXT DEFAULT 'pending_approval',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            published_at DATETIME
        )
    """)
    conn.execute("""
        INSERT INTO omnichannel_drafts (
            topic, fb_content, ig_content, tiktok_script, youtube_content,
            status, created_at, published_at
        ) VALUES (
            'Donut Launch Promo',
            'Try our fresh glazed donuts today!',
            'Glazed goodness awaits you #donuts',
            'TikTok viral script for donuts',
            'Full review of our top 5 donuts',
            'published',
            '2026-08-01 12:00:00',
            '2026-08-01 12:30:00'
        )
    """)
    conn.execute("""
        INSERT INTO omnichannel_drafts (
            topic, fb_content, ig_content, status, created_at
        ) VALUES (
            'Weekend Special',
            'Buy 1 Free 1 on weekend!',
            'Weekend promo #bogo',
            'pending_approval',
            '2026-08-02 10:00:00'
        )
    """)
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def legacy_json(tmp_path):
    """Creates a sample legacy JSON export file."""
    json_path = tmp_path / "legacy_drafts.json"
    items = [
        {
            "id": 101,
            "topic": "JSON Post 1",
            "fb_content": "Facebook content from JSON",
            "ig_content": "Instagram content from JSON",
            "status": "pending_approval",
        },
        {
            "id": 102,
            "topic": "JSON Post 2",
            "content": "Universal content post",
            "platform": "x",
            "status": "published",
            "published_at": "2026-08-10T15:00:00Z",
        },
    ]
    json_path.write_text(json.dumps(items), encoding="utf-8")
    return json_path


def test_dry_run_migration_changes_no_destination_data(legacy_sqlite, tmp_path):
    """Dry run mode must compute source SHA256, find candidates, and write 0 rows."""
    dest_db = tmp_path / "missions_dest.db"

    report = migrate_legacy_social(legacy_sqlite, dest_db, dry_run=True)
    assert isinstance(report, MigrationReport)
    assert report.written_rows == 0
    assert report.total_candidates == 2
    assert len(report.source_sha256) == 64
    assert report.manifest_id is None
    # Destination file should not have been created in dry run
    assert not dest_db.exists()


def test_live_migration_imports_sqlite_records_and_manifest(legacy_sqlite, tmp_path):
    """Live migration imports rows into campaigns, approvals, publication_attempts, and manifest."""
    dest_db = tmp_path / "missions_live.db"
    initial_src_bytes = legacy_sqlite.read_bytes()

    report = migrate_legacy_social(legacy_sqlite, dest_db, dry_run=False)
    assert isinstance(report, MigrationReport)
    assert report.written_rows > 0
    assert report.total_candidates == 2
    assert report.manifest_id is not None
    assert len(report.source_sha256) == 64

    # Source file MUST NOT be altered
    assert legacy_sqlite.read_bytes() == initial_src_bytes

    # Inspect destination database rows
    conn = sqlite3.connect(str(dest_db))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    campaigns = cursor.execute("SELECT * FROM campaigns").fetchall()
    assert len(campaigns) == 2

    approvals = cursor.execute("SELECT * FROM approvals").fetchall()
    assert len(approvals) >= 2

    attempts = cursor.execute("SELECT * FROM publication_attempts").fetchall()
    assert len(attempts) >= 1  # 1 published post in fixture

    manifests = cursor.execute("SELECT * FROM migration_manifests").fetchall()
    assert len(manifests) == 1
    assert manifests[0]["id"] == report.manifest_id

    conn.close()


def test_migration_from_json_source(legacy_json, tmp_path):
    """Live migration parses JSON candidates, computes hashes, and writes records."""
    dest_db = tmp_path / "missions_json.db"

    report = migrate_legacy_social(legacy_json, dest_db, dry_run=False)
    assert report.written_rows > 0
    assert report.total_candidates == 2
    assert len(report.source_sha256) == 64

    conn = sqlite3.connect(str(dest_db))
    cursor = conn.cursor()
    campaigns = cursor.execute("SELECT * FROM campaigns").fetchall()
    assert len(campaigns) == 2
    conn.close()


def test_migration_nonexistent_source_raises_file_not_found(tmp_path):
    dest_db = tmp_path / "missions_err.db"
    with pytest.raises(FileNotFoundError):
        migrate_legacy_social("nonexistent_legacy_file_path.db", dest_db, dry_run=True)
