#!/usr/bin/env python3
"""
ACTION CENTER
Queue actions and review current status/history for CHATTY.
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


BASE_DIR = Path("generated_content")
REQUESTS_PATH = BASE_DIR / "action_requests.json"
HISTORY_PATH = BASE_DIR / "action_history.jsonl"
STATUS_PATH = BASE_DIR / "earnings_status.md"


def _load_requests():
    if not REQUESTS_PATH.exists():
        return {"requests": []}
    return json.loads(REQUESTS_PATH.read_text(encoding="utf-8"))


def _save_requests(payload):
    REQUESTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    REQUESTS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _add_request(action, notes=""):
    payload = _load_requests()
    request = {
        "id": str(uuid.uuid4()),
        "action": action,
        "status": "pending",
        "notes": notes,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    payload["requests"].append(request)
    _save_requests(payload)
    print(f"Queued: {action} ({request['id']})")


def _tail_file(path, lines=20):
    if not path.exists():
        print(f"No file found: {path}")
        return
    data = path.read_text(encoding="utf-8").splitlines()
    for line in data[-lines:]:
        print(line)


def main():
    print("CHATTY Action Center")
    print("=" * 40)
    print("1) Generate earnings report now")
    print("2) Run investor weekly update now")
    print("3) Run investor daily outreach now")
    print("4) Run investor narrative update now")
    print("5) Show current earnings status")
    print("6) Show recent action history")
    print("0) Exit")
    choice = input("Select: ").strip()

    if choice == "1":
        _add_request("write_earnings_report")
    elif choice == "2":
        _add_request("investor_weekly_update")
    elif choice == "3":
        _add_request("investor_daily_outreach")
    elif choice == "4":
        _add_request("investor_narrative_update")
    elif choice == "5":
        _tail_file(STATUS_PATH, lines=80)
    elif choice == "6":
        _tail_file(HISTORY_PATH, lines=40)
    elif choice == "0":
        return
    else:
        print("Unknown selection.")


if __name__ == "__main__":
    main()
