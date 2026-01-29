#!/usr/bin/env python3
"""
Transparency logging for outbound actions.
Writes sanitized JSONL entries to generated_content/transparency_log.jsonl.
"""

import hashlib
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

_RUN_ID = os.getenv("CHATTY_RUN_ID") or str(uuid.uuid4())
_LOG_PATH = Path("generated_content") / "transparency_log.jsonl"


def _mask_email(value: str) -> str:
    if "@" not in value:
        return value
    name, domain = value.split("@", 1)
    if len(name) <= 2:
        return f"{name[:1]}***@{domain}"
    return f"{name[:2]}***@{domain}"


def _scrub(value: Any) -> Any:
    if isinstance(value, str):
        lower = value.lower()
        if "sk_" in value or "key" in lower or "secret" in lower or "token" in lower:
            return "redacted"
        if "@" in value:
            return _mask_email(value)
        return value
    if isinstance(value, dict):
        return {k: _scrub(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_scrub(v) for v in value]
    return value


def log_transparency(event: str, status: str, details: Dict[str, Any] = None) -> None:
    _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "run_id": _RUN_ID,
        "event": event,
        "status": status,
        "details": _scrub(details or {}),
    }
    with _LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")

