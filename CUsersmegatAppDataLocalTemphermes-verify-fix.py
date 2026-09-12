import requests
import sys

BASE_LOCAL = "http://127.0.0.1:9220"
BASE_TUNNEL = "https://organized-shelf-alabama-annie.trycloudflare.com"

tests = [
    ("Local /api/stats", f"{BASE_LOCAL}/api/stats"),
    ("Tunnel /api/stats", f"{BASE_TUNNEL}/api/stats"),
    ("Local /api/queue", f"{BASE_LOCAL}/api/queue"),
    ("Local /api/processes", f"{BASE_LOCAL}/api/processes"),
    ("Local /api/system/kanban", f"{BASE_LOCAL}/api/system/kanban"),
    ("Local /", f"{BASE_LOCAL}/"),
    ("Tunnel /", f"{BASE_TUNNEL}/"),
]

print("=" * 60)
print("HERMES-WEBAPP FIX VERIFICATION")
print("=" * 60)

all_passed = True
for name, url in tests:
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            if "TelegramConflictError" in r.text or "getUpdates request" in r.text:
                print(f"FAIL {name}: HTTP 200 BUT CONTAINS TELEGRAM CONFLICT ERROR")
                all_passed = False
            else:
                print(f"OK {name}: HTTP {r.status_code} - CLEAN")
        else:
            print(f"FAIL {name}: HTTP {r.status_code}")
            all_passed = False
    except Exception as e:
        print(f"FAIL {name}: {e}")
        all_passed = False

print("=" * 60)
if all_passed:
    print("VERIFICATION PASSED - Fix confirmed working")
    sys.exit(0)
else:
    print("VERIFICATION FAILED")
    sys.exit(1)
