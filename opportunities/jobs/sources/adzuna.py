"""Adzuna US search API (free key: ADZUNA_APP_ID + ADZUNA_APP_KEY; ~250 calls/day)."""

from __future__ import annotations

from ...models import Job
from ...net import get_json
from . import SourceResult, normalize_type, strip_html

NAME = "Adzuna"
REQUIRES = ["ADZUNA_APP_ID", "ADZUNA_APP_KEY"]
URL = "https://api.adzuna.com/v1/api/jobs/us/search/1"


def fetch(settings) -> SourceResult:
    res = SourceResult(NAME)
    if not (settings.adzuna_app_id and settings.adzuna_app_key):
        res.skipped = "missing ADZUNA_APP_ID / ADZUNA_APP_KEY"
        return res
    for kw in settings.job_keywords:
        data = get_json(URL, user_agent=settings.ua(), min_interval=3, params={
            "app_id": settings.adzuna_app_id, "app_key": settings.adzuna_app_key,
            "what": kw, "what_or": "remote", "results_per_page": 50, "max_days_old": settings.max_job_age_days,
            "content-type": "application/json", "sort_by": "date",
        })
        for it in data.get("results", []):
            desc = strip_html(it.get("description", ""))
            loc = (it.get("location") or {}).get("display_name", "")
            remote = "remote" in (desc + " " + it.get("title", "")).lower()
            res.jobs.append(Job(
                source=NAME, source_url=it.get("redirect_url", ""), title=it.get("title", "").strip(),
                company=(it.get("company") or {}).get("display_name", ""), url=it.get("redirect_url", ""),
                location=loc, remote=remote, us_eligible=True,
                job_type=normalize_type(it.get("contract_time") or it.get("contract_type") or ""),
                salary_min=int(it["salary_min"]) if it.get("salary_min") else None,
                salary_max=int(it["salary_max"]) if it.get("salary_max") else None,
                posted_at=it.get("created", ""), description=desc[:4000], attribution="Jobs by Adzuna",
            ))
    return res
