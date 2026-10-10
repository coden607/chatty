"""Run all job sources, dedupe, filter, score, and store."""

from __future__ import annotations

import logging
from typing import Dict, Iterable, List, Optional

from ..config import Settings, get_settings
from ..models import Job
from ..store import Store, utcnow
from .scoring import score_job
from .sources import SourceResult, adzuna, ats, himalayas, hn, remoteok, remotive, usajobs

logger = logging.getLogger("opportunities.jobs")

SOURCES = {
    "remotive": remotive,
    "remoteok": remoteok,
    "himalayas": himalayas,
    "hn": hn,
    "ats": ats,
    "adzuna": adzuna,
    "usajobs": usajobs,
}
KEYLESS = [k for k, m in SOURCES.items() if not m.REQUIRES]


def run_source(key: str, settings: Settings) -> SourceResult:
    mod = SOURCES[key]
    try:
        res = mod.fetch(settings)
    except Exception as exc:  # network/parse errors never abort the run
        logger.warning("❌ job source %s failed: %s", mod.NAME, exc)
        return SourceResult(mod.NAME, error=str(exc)[:300])
    if res.skipped:
        logger.info("⏭️  job source %s skipped: %s", mod.NAME, res.skipped)
    else:
        logger.info("✅ job source %s: %d listings%s", mod.NAME, len(res.jobs), f" (partial: {res.error[:120]})" if res.error else "")
    return res


def dedupe(jobs: Iterable[Job]) -> List[Job]:
    by_key: Dict[str, Job] = {}
    by_url: Dict[str, str] = {}
    for j in jobs:
        if not j.title or not (j.url or j.source_url):
            continue
        k = by_url.get(j.url_key) or j.dedupe_key
        if k in by_key:
            keep = by_key[k]
            if j.source != keep.source and j.source not in keep.also_on:
                keep.also_on.append(j.source)
            # prefer the record that has salary info
            if not (keep.salary_min or keep.salary_max) and (j.salary_min or j.salary_max):
                keep.salary_min, keep.salary_max = j.salary_min, j.salary_max
            continue
        by_key[k] = j
        by_url[j.url_key] = k
    return list(by_key.values())


def find_jobs(settings: Optional[Settings] = None, sources: Optional[List[str]] = None, store: Optional[Store] = None, persist: bool = True) -> Dict:
    settings = settings or get_settings()
    started = utcnow()
    keys = sources or list(SOURCES)
    results = [run_source(k, settings) for k in keys if k in SOURCES]
    raw = [j for r in results for j in r.jobs]
    unique = dedupe(raw)
    scored: List[Job] = []
    for j in unique:
        j.score, j.reasons = score_job(j, settings)
        if j.us_eligible is False:
            continue  # US-remote only
        if settings.remote_only and not j.remote:
            continue
        if j.score >= settings.min_score:
            scored.append(j)
    scored.sort(key=lambda j: (j.score, j.posted_at), reverse=True)
    summary = {
        "sources": {r.name: {"count": len(r.jobs), "skipped": r.skipped, "error": r.error} for r in results},
        "raw": len(raw), "unique": len(unique), "matched": len(scored),
    }
    if persist:
        store = store or Store(settings.db_path)
        summary["stored"] = store.upsert_jobs(scored)
        store.log_run("jobs", started, summary)
    logger.info("🎯 jobs: %d raw → %d unique → %d matched (min score %d)", len(raw), len(unique), len(scored), settings.min_score)
    return {"summary": summary, "jobs": scored}
