#!/usr/bin/env python3
"""Securely configure X API credentials for Chatty."""

from __future__ import annotations

import getpass
import os
import subprocess
import tempfile
from pathlib import Path


SECRETS_FILE = Path.home() / ".config" / "chatty" / "secrets.env"
X_DEVELOPER_PORTAL = "https://developer.x.com/en/portal/dashboard"
X_KEYS = (
    "X_BEARER_TOKEN",
    "X_CONSUMER_KEY",
    "X_CONSUMER_SECRET",
    "X_ACCESS_TOKEN",
    "X_ACCESS_SECRET",
)


def load_lines() -> list[str]:
    if not SECRETS_FILE.exists():
        return []
    return SECRETS_FILE.read_text(encoding="utf-8").splitlines()


def configured_keys(lines: list[str]) -> set[str]:
    configured: set[str] = set()
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        if key.strip() in X_KEYS and value.strip():
            configured.add(key.strip())
    return configured


def quote_env(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def merge_values(lines: list[str], replacements: dict[str, str]) -> list[str]:
    output: list[str] = []
    written: set[str] = set()
    for line in lines:
        stripped = line.strip()
        key = stripped.split("=", 1)[0].strip() if "=" in stripped else ""
        if key in replacements:
            output.append(f"{key}={quote_env(replacements[key])}")
            written.add(key)
        else:
            output.append(line)

    if replacements.keys() - written:
        if output and output[-1] != "":
            output.append("")
        output.append("# X / Twitter API credentials")
        for key in X_KEYS:
            if key in replacements and key not in written:
                output.append(f"{key}={quote_env(replacements[key])}")
    return output


def atomic_write(lines: list[str]) -> None:
    SECRETS_FILE.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(SECRETS_FILE.parent, 0o700)
    fd, temp_name = tempfile.mkstemp(prefix="secrets.", dir=SECRETS_FILE.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write("\n".join(lines).rstrip() + "\n")
        os.chmod(temp_name, 0o600)
        os.replace(temp_name, SECRETS_FILE)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def open_developer_portal() -> None:
    """Open X's developer portal using Termux when available."""
    print("Opening the X Developer Portal in your browser...")
    try:
        result = subprocess.run(
            ["termux-open-url", X_DEVELOPER_PORTAL],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if result.returncode == 0:
            return
    except FileNotFoundError:
        pass
    print(f"Open this URL manually: {X_DEVELOPER_PORTAL}")


def main() -> int:
    lines = load_lines()
    existing = configured_keys(lines)
    replacements: dict[str, str] = {}

    print("Chatty X credential setup")
    print("Values are hidden and will not be printed.")
    print("Press Enter to preserve an existing value or skip a missing one.\n")

    open_developer_portal()
    print("Sign in, select the official NarcoGuard app, and regenerate its keys and tokens.")
    print("Regeneration invalidates the old exposed credentials.")
    getpass.getpass("Press Enter here after the new credentials are visible in the portal: ")
    print()

    for key in X_KEYS:
        status = "configured" if key in existing else "missing"
        value = getpass.getpass(f"{key} [{status}]: ").strip()
        if "\n" in value or "\r" in value:
            raise ValueError(f"{key} contains an invalid newline")
        if value:
            replacements[key] = value

    if not replacements:
        print("No changes made.")
        return 0

    atomic_write(merge_values(lines, replacements))
    final_status = configured_keys(load_lines())
    print(f"Saved securely to {SECRETS_FILE}")
    print(f"Configured X credentials: {len(final_status)}/{len(X_KEYS)}")
    if len(final_status) != len(X_KEYS):
        print("Run this command again to enter the remaining credentials.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
