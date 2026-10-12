"""Himalayas public jobs API (keyless). Credit Himalayas and link to the listing."""

from __future__ import annotations

from ...models import Job
from ...net import get_json
from . import SourceResult, iso_from_epoch, normalize_type, strip_html

NAME = "Himalayas"
REQUIRES: list = []
URL = "https://himalayas.app/jobs/api/search"


def _eligible(restrictions) -> bool | None:
    if not restrictions:
        return True  # no restriction = worldwide
    names = {str(r).lower() for r in restrictions}
    return True if {"united states", "usa", "us"} & names else False


def fetch(settings) -> SourceResult:
    res = SourceResult(NAME)
    seen = set()
    for kw in settings.job_keywords:
        data = get_json(URL, user_agent=settings.ua(), params={"q": kw, "country": "US", "limit": 50}, min_interval=2)
        for it in data.get("jobs", []):
            guid = it.get("guid") or it.get("applicationLink")
            if not guid or guid in seen:
                continue
            seen.add(guid)
            restr = it.get("locationRestrictions") or []
            res.jobs.append(Job(
                source=NAME,
                source_url=guid,
                title=(it.get("title") or "").strip(),
                company=(it.get("companyName") or "").strip(),
                url=it.get("applicationLink") or guid,
                location=", ".join(restr[:5]) + ("..." if len(restr) > 5 else "") if restr else "Worldwide",
                remote=True,
                us_eligible=_eligible(restr),
                job_type=normalize_type(it.get("employmentType", "")),
                salary_min=it.get("minSalary") if (it.get("currency") in (None, "USD")) else None,
                salary_max=it.get("maxSalary") if (it.get("currency") in (None, "USD")) else None,
                posted_at=iso_from_epoch(it.get("pubDate")),
                description=strip_html(it.get("description") or it.get("excerpt") or "")[:4000],
                tags=list(it.get("categories") or [])[:10],
                attribution="Job via Himalayas (himalayas.app)",
            ))
    return res
