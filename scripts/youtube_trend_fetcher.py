#!/usr/bin/env python3
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime


ROOT = os.path.dirname(os.path.dirname(__file__))
DEFAULT_CONFIG = os.path.join(ROOT, "trend_sources.json")
DEFAULT_ENV = os.path.join(ROOT, ".env")
API_BASE = os.getenv("CHATTY_API_BASE", "http://localhost:8080")


def _load_env(path: str) -> dict:
    env = {}
    if not os.path.exists(path):
        return env
    with open(path, "r", encoding="ascii") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def _load_config(path: str) -> dict:
    if not os.path.exists(path):
        return {
            "youtube_queries": ["NarcoGuard", "overdose prevention tech", "harm reduction AI"],
            "max_results": 8
        }
    with open(path, "r", encoding="ascii") as handle:
        return json.load(handle)


def _fetch_youtube(query: str, api_key: str, max_results: int) -> list:
    params = {
        "part": "snippet",
        "type": "video",
        "order": "date",
        "maxResults": max_results,
        "q": query,
        "key": api_key
    }
    url = "https://www.googleapis.com/youtube/v3/search?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=15) as response:
        payload = json.loads(response.read().decode("utf-8"))
    items = []
    for item in payload.get("items", []):
        snippet = item.get("snippet", {})
        video_id = item.get("id", {}).get("videoId")
        title = snippet.get("title", "Untitled")
        published = snippet.get("publishedAt")
        items.append({
            "title": title,
            "source": "youtube",
            "query": query,
            "published_at": published,
            "url": f"https://www.youtube.com/watch?v={video_id}" if video_id else ""
        })
    return items


def _post_trends(items: list, source: str) -> None:
    payload = json.dumps({"source": source, "items": items}).encode("utf-8")
    req = urllib.request.Request(
        f"{API_BASE}/api/trends/ingest",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        response.read()


def main() -> int:
    env = _load_env(DEFAULT_ENV)
    api_key = (
        os.getenv("YOUTUBE_KEY")
        or env.get("YOUTUBE_KEY")
        or os.getenv("YOUTUBE_API_KEY")
        or env.get("YOUTUBE_API_KEY")
    )
    if not api_key:
        print("Missing YOUTUBE_API_KEY in environment or .env", file=sys.stderr)
        return 1

    config = _load_config(DEFAULT_CONFIG)
    queries = config.get("youtube_queries", [])
    max_results = int(config.get("max_results", 8))
    all_items = []
    for query in queries:
        all_items.extend(_fetch_youtube(query, api_key, max_results))

    if not all_items:
        print("No items fetched")
        return 0

    _post_trends(all_items, "youtube")
    stamp = datetime.now().isoformat()
    print(f"Ingested {len(all_items)} YouTube items at {stamp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
