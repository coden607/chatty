#!/usr/bin/env python3
"""Publish the single approved NarcoGuard awareness post to X."""

from __future__ import annotations

import os
from pathlib import Path


SECRETS_FILE = Path.home() / ".config" / "chatty" / "secrets.env"
POST = (
    "NarcoGuard is developing NG2, a wearable concept designed to explore "
    "faster overdose detection and emergency response. We're seeking "
    "public-health partners, researchers, funders, and pilot collaborators. "
    "https://narcoguard-pwa.vercel.app"
)
REQUIRED_KEYS = (
    "X_BEARER_TOKEN",
    "X_CONSUMER_KEY",
    "X_CONSUMER_SECRET",
    "X_ACCESS_TOKEN",
    "X_ACCESS_SECRET",
)


def unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] == '"':
        value = value[1:-1]
        value = value.replace('\\"', '"').replace("\\\\", "\\")
    return value


def load_secrets() -> dict[str, str]:
    secrets: dict[str, str] = {}
    if not SECRETS_FILE.exists():
        return secrets
    for line in SECRETS_FILE.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        secrets[key.strip()] = unquote(value)
    return secrets


def confirm_from_terminal() -> bool:
    print("\nExact post to publish:\n")
    print(POST)
    print("\nThis is an external communication from the official account.")
    try:
        with open("/dev/tty", "r+", encoding="utf-8") as terminal:
            terminal.write("Type PUBLISH to send this one post: ")
            terminal.flush()
            return terminal.readline().strip() == "PUBLISH"
    except OSError:
        print("A real interactive terminal is required.")
        return False


def main() -> int:
    secrets = load_secrets()
    missing = [key for key in REQUIRED_KEYS if not secrets.get(key)]
    if missing:
        print("Missing X credentials: " + ", ".join(missing))
        print("Run configure_x_keys.py first.")
        return 1

    try:
        import tweepy
    except ImportError:
        print("Missing dependency. Run: python3 -m pip install 'tweepy>=4.14,<5'")
        return 1

    if not confirm_from_terminal():
        print("Cancelled. Nothing was published.")
        return 1

    client = tweepy.Client(
        bearer_token=secrets["X_BEARER_TOKEN"],
        consumer_key=secrets["X_CONSUMER_KEY"],
        consumer_secret=secrets["X_CONSUMER_SECRET"],
        access_token=secrets["X_ACCESS_TOKEN"],
        access_token_secret=secrets["X_ACCESS_SECRET"],
    )
    response = client.create_tweet(text=POST, user_auth=True)
    tweet_id = response.data.get("id") if response.data else None
    if not tweet_id:
        print("X did not return a post ID; publication could not be verified.")
        return 1
    print(f"Published successfully: https://x.com/i/web/status/{tweet_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
