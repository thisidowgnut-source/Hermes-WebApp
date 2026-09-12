#!/usr/bin/env python3
"""Clean up Hermes-WebApp zombie tasks safely.

Original version aggressively killed cloudflared/uvicorn/node by name unless
cmdline contained "n8n", which silently destroyed the production pipeline
(cloudflared tunnel to 9220, uvicorn Hermes-WebApp backend).

This version is opt-in for dangerous kills via CLI flag, and whitelist-aware:
processes whose cmdline references the Hermes-WebApp project path or is a
known long-running service are NEVER killed without --force.

Usage:
    python cleanup_tasks.py              # safe cleanup only (zombie task wrappers)
    python cleanup_tasks.py --force      # also kill stale cloudflared/uvicorn/node by name
    python cleanup_tasks.py --dry-run    # show what would be killed, don't kill
"""

import argparse
import sys
import psutil

# Project identifiers — processes whose cmdline contains any of these are
# considered part of the production pipeline and must NEVER be killed
# without explicit --force.
PROJECT_PATHS = [
    r"C:/Users/megat/Hermes-WebApp",
    r"C:/Users/megat/Hermes-WebApp/scripts",
    r"C:/Users/megat/Hermes-WebApp/cloudflared",
    "/c/Users/megat/Hermes-WebApp",
]

SAFE_KILL_NAMES = {
    # These can be killed freely when they're actually zombies — but we require
    # --force so a dry-run prints them first.
    "cloudflared.exe",
    "uvicorn.exe",
    "node.exe",
}

WRAPPER_INDICATORS = (
    # task wrappers of the form task-xxxxxxxx.log are always safe to kill
    "task-",
    ".log",
    # old psql/uvicorn wrappers from previous startups
    "pwsh.exe",
    "wrapper.log",
)


def is_project_pipeline(cmd: str) -> bool:
    cmd_lower = cmd.lower().replace("\\", "/")
    return any(p.lower().replace("\\", "/") in cmd_lower for p in PROJECT_PATHS)


def is_wrapper(cmd: str) -> bool:
    return all(needle.lower() in cmd.lower() for needle in WRAPPER_INDICATORS[:2])


def collect(force: bool = False, dry_run: bool = False):
    """Yield (process_info, reason) tuples for processes meant to be killed."""
    for p in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            info = p.info
            cmd = " ".join(info.get("cmdline") or [])
            name = (info.get("name") or "").lower()

            # 1. Always-safe: task wrappers with .log
            if is_wrapper(cmd):
                yield info, f"task wrapper: {cmd[:80]}"
                continue

            # 2. Project pipeline is NEVER killed without --force
            if is_project_pipeline(cmd):
                continue

            # 3. Stale service processes — require --force
            if force and name in SAFE_KILL_NAMES and "n8n" not in cmd.lower():
                yield info, f"stale {name} (--force): {cmd[:80]}"
                continue

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass


def main():
    parser = argparse.ArgumentParser(description="Hermes-WebApp safe zombie cleanup")
    parser.add_argument("--force", action="store_true", help="kill stale cloudflared/uvicorn/node by name (off by default)")
    parser.add_argument("--dry-run", action="store_true", help="report what would be killed without killing")
    args = parser.parse_args()

    mode = "DRY RUN" if args.dry_run else ("FORCE CLEANUP" if args.force else "SAFE CLEANUP")
    print(f"[cleanup_tasks.py] {mode}")
    if not args.force:
        print("  ↳ project pipeline processes protected:")
        for p in PROJECT_PATHS:
            print(f"     - {p}")

    killed = skipped = 0
    for info, reason in collect(force=args.force, dry_run=args.dry_run):
        pid = info["pid"]
        if args.dry_run:
            print(f"  [dry-run] WOULD KILL pid={pid} {reason}")
            continue
        try:
            psutil.Process(pid).kill()
            print(f"  KILLED pid={pid}  {reason}")
            killed += 1
        except Exception as exc:
            print(f"  FAILED pid={pid}  {exc}")
            skipped += 1

    print(f"[cleanup_tasks.py] done. killed={killed} skipped={skipped}")


if __name__ == "__main__":
    main()
