"""Background loop used by START_COMPLETE_AUTOMATION (opportunity_finder task)."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from .config import get_settings
from .digest import run_digest
from .jobs.finder import find_jobs
from .prospects.finder import find_prospects
from .store import Store

logger = logging.getLogger("opportunities.scheduler")


def _due(store: Store, key: str, hours: float) -> bool:
    last = store.get(key)
    if not last:
        return True
    try:
        return datetime.now(timezone.utc) - datetime.fromisoformat(last) >= timedelta(hours=hours)
    except ValueError:
        return True


def _mark(store: Store, key: str) -> None:
    store.set(key, datetime.now(timezone.utc).isoformat())


def tick() -> dict:
    settings = get_settings()
    store = Store(settings.db_path)
    out = {}
    if _due(store, "last_jobs_run", settings.jobs_interval_hours):
        out["jobs"] = find_jobs(settings, store=store)["summary"]
        _mark(store, "last_jobs_run")
    if _due(store, "last_prospects_run", settings.prospects_interval_hours):
        out["prospects"] = find_prospects(settings, store=store)["summary"]
        _mark(store, "last_prospects_run")
    if datetime.now().hour >= settings.digest_hour_local and _due(store, "last_digest", 20):
        out["digest"] = run_digest(settings, store=store)
        _mark(store, "last_digest")
    return out


async def run_forever(poll_minutes: int = 30) -> None:
    logger.info("🔎 Opportunity finder loop started (jobs daily, prospects weekly, digest daily)")
    while True:
        try:
            await asyncio.to_thread(tick)
        except Exception as exc:  # never crash the orchestrator
            logger.error("Opportunity finder tick failed: %s", exc)
        await asyncio.sleep(poll_minutes * 60)
