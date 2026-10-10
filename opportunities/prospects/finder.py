"""Discover, enrich, score, store, export, and draft for Cortese prospects."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List, Optional

from ..config import Settings, get_settings
from ..models import Prospect
from ..store import Store, utcnow
from . import npi, places, website
from .drafts import draft_for, write_draft_file
from .export import to_csv
from .metros import METROS
from .scoring import score_prospect
from .verticals import VERTICALS

logger = logging.getLogger("opportunities.prospects")

CURSOR_KEY = "places_cursor"


def _work_items(settings: Settings, metros) -> List[tuple]:
    items = []
    for metro, city, state in metros:
        for vkey in settings.verticals:
            v = VERTICALS.get(vkey)
            if not v:
                continue
            for q in v["places_queries"]:
                items.append((q, vkey, metro, city, state))
    return items


def discover_places(settings: Settings, store: Store, metros, max_calls: int) -> Dict:
    if not settings.google_places_api_key:
        logger.info("⏭️  Google Places skipped: missing GOOGLE_PLACES_API_KEY")
        return {"skipped": "missing GOOGLE_PLACES_API_KEY", "prospects": []}
    items = _work_items(settings, metros)
    if not items:
        return {"prospects": []}
    start = int(store.get(CURSOR_KEY, "0") or 0) % len(items)
    found: List[Prospect] = []
    calls = 0
    stop_reason = None
    for i in range(len(items)):
        if calls >= max_calls:
            stop_reason = f"per-run cap {max_calls}"
            break
        idx = (start + i) % len(items)
        q, vkey, metro, city, state = items[idx]
        try:
            found.extend(places.search(q, vkey, metro, city, state, settings, store))
            calls += 1
        except places.BudgetExceeded as exc:
            stop_reason = str(exc)
            logger.warning("💸 %s", exc)
            break
        except Exception as exc:
            calls += 1
            logger.warning("Places query '%s' in %s failed: %s", q, metro, exc)
        store.set(CURSOR_KEY, str(idx + 1))
    remaining = places.calls_remaining(store, settings)
    logger.info("✅ Google Places: %d calls this run, %d businesses, %d calls left this month (cap %d ≈ $%.0f)",
                calls, len(found), remaining, settings.places_monthly_call_cap, settings.places_monthly_budget_usd)
    return {"calls": calls, "stopped": stop_reason, "remaining_calls_this_month": remaining, "prospects": found}


def discover_npi(settings: Settings, metros) -> Dict:
    found: List[Prospect] = []
    errors = 0
    for metro, city, state in metros:
        for vkey in settings.verticals:
            for tax in VERTICALS.get(vkey, {}).get("npi_taxonomies", []):
                try:
                    found.extend(npi.search(tax, vkey, metro, city, state, settings))
                except Exception as exc:
                    errors += 1
                    logger.warning("NPI %s in %s failed: %s", tax, metro, exc)
    logger.info("✅ NPI Registry: %d organizations (%d errors)", len(found), errors)
    return {"prospects": found, "errors": errors}


def find_prospects(
    settings: Optional[Settings] = None,
    store: Optional[Store] = None,
    metro_limit: Optional[int] = None,
    metro_offset: int = 0,
    use_places: bool = True,
    use_npi: bool = True,
    check_websites: Optional[bool] = None,
    max_places_calls: Optional[int] = None,
    draft_grades: str = "A",
    max_drafts: int = 25,
    persist: bool = True,
) -> Dict:
    settings = settings or get_settings()
    store = store or Store(settings.db_path if persist else ":memory:")
    started = utcnow()
    limit = metro_limit or settings.metro_limit
    metros = METROS[metro_offset:metro_offset + limit]

    purged = store.purge_stale_places_content(settings.places_cache_days)
    prospects: List[Prospect] = []
    summary: Dict = {"metros": len(metros), "purged_stale_places_rows": purged}

    if use_places:
        pr = discover_places(settings, store, METROS[: settings.metro_limit], max_places_calls or settings.places_max_calls_per_run)
        prospects += pr.pop("prospects")
        summary["google_places"] = pr
    if use_npi:
        nr = discover_npi(settings, metros)
        prospects += nr.pop("prospects")
        summary["npi"] = nr

    # Dedupe by phone / name+city
    seen, unique = set(), []
    for p in prospects:
        if p.dedupe_key in seen:
            continue
        seen.add(p.dedupe_key)
        unique.append(p)

    do_web = settings.website_checks if check_websites is None else check_websites
    checked = 0
    for p in unique:
        if do_web and p.website:
            p.signals.update(website.check_site(p.website, settings))
            checked += 1
        p.grade, p.score, p.reasons = score_prospect(p)
    unique.sort(key=lambda p: p.score, reverse=True)

    grades = {g: sum(1 for p in unique if p.grade == g) for g in "ABC"}
    summary.update({"found": len(prospects), "unique": len(unique), "websites_checked": checked, "grades": grades})
    logger.info("🎯 prospects: %d found → %d unique; grades A=%d B=%d C=%d", len(prospects), len(unique), grades["A"], grades["B"], grades["C"])

    if persist:
        summary["stored"] = store.upsert_prospects(unique)
        # CSV export of everything stored
        stamp = datetime.now().strftime("%Y%m%d")
        csv_path = settings.output_dir / f"cortese_prospects_{stamp}.csv"
        to_csv(store.list_prospects(), csv_path)
        summary["csv"] = str(csv_path)

        # Drafts (saved only, never sent)
        made = 0
        draft_dir = settings.output_dir / "drafts"
        for p in unique:
            if made >= max_drafts:
                break
            if p.grade not in draft_grades.upper() or store.has_draft(p.key):
                continue
            pd = p.to_dict()
            subject, body, gen = draft_for(pd, settings)
            store.save_draft(p.key, subject, body, gen)
            write_draft_file(draft_dir, pd, subject, body, gen)
            made += 1
        summary["drafts_saved"] = made
        summary["drafts_dir"] = str(draft_dir)
        store.log_run("prospects", started, summary)
    return {"summary": summary, "prospects": unique}
