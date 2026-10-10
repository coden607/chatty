"""Public ATS job-board APIs (keyless, one employer per board): Greenhouse, Lever, Ashby."""

from __future__ import annotations

import logging

from ...models import Job
from ...net import FetchError, get_json
from . import SourceResult, iso_from_epoch, normalize_type, strip_html, us_eligibility

logger = logging.getLogger("opportunities.jobs.ats")

NAME = "Company boards"
REQUIRES: list = []


def _greenhouse(settings, board: str):
    data = get_json(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs", user_agent=settings.ua(), params={"content": "true"}, min_interval=1)
    for it in data.get("jobs", []):
        loc = (it.get("location") or {}).get("name", "")
        yield Job(
            source="Greenhouse", source_url=it.get("absolute_url", ""), title=it.get("title", ""),
            company=board.replace("-", " ").title(), url=it.get("absolute_url", ""), location=loc,
            remote="remote" in loc.lower(), us_eligible=us_eligibility(loc), job_type="",
            posted_at=it.get("updated_at", ""), description=strip_html(it.get("content", ""))[:4000],
            attribution=f"{board} careers (Greenhouse)",
        )


def _lever(settings, board: str):
    data = get_json(f"https://api.lever.co/v0/postings/{board}", user_agent=settings.ua(), params={"mode": "json"}, min_interval=1)
    for it in data if isinstance(data, list) else []:
        cats = it.get("categories") or {}
        loc = cats.get("location") or ""
        workplace = (it.get("workplaceType") or "").lower()
        yield Job(
            source="Lever", source_url=it.get("hostedUrl", ""), title=it.get("text", ""),
            company=board.replace("-", " ").title(), url=it.get("hostedUrl", ""), location=loc,
            remote=workplace == "remote" or "remote" in loc.lower(), us_eligible=us_eligibility(loc),
            job_type=normalize_type(cats.get("commitment", "")),
            posted_at=iso_from_epoch((it.get("createdAt") or 0) // 1000),
            description=(it.get("descriptionPlain") or "")[:4000],
            attribution=f"{board} careers (Lever)",
        )


def _ashby_remote(it: dict, loc: str) -> bool:
    wp = (it.get("workplaceType") or "").lower()
    if wp:
        return wp == "remote"
    return bool(it.get("isRemote")) or "remote" in loc.lower()


def _ashby(settings, board: str):
    data = get_json(f"https://api.ashbyhq.com/posting-api/job-board/{board}", user_agent=settings.ua(), params={"includeCompensation": "true"}, min_interval=1)
    for it in data.get("jobs", []):
        if it.get("isListed") is False:
            continue
        loc = it.get("location") or ""
        addr = ((it.get("address") or {}).get("postalAddress") or {})
        country = addr.get("addressCountry") or ""
        loc_full = ", ".join(x for x in [loc, country] if x)
        yield Job(
            source="Ashby", source_url=it.get("jobUrl", ""), title=it.get("title", ""),
            company=board.replace("-", " ").title(), url=it.get("applyUrl") or it.get("jobUrl", ""), location=loc_full,
            remote=_ashby_remote(it, loc), us_eligible=us_eligibility(loc_full),
            job_type=normalize_type(it.get("employmentType", "")), posted_at=it.get("publishedAt", ""),
            description=(it.get("descriptionPlain") or "")[:4000], attribution=f"{board} careers (Ashby)",
        )


def fetch(settings) -> SourceResult:
    res = SourceResult(NAME)
    errors = []
    for kind, boards, fn in (("greenhouse", settings.greenhouse_boards, _greenhouse), ("lever", settings.lever_boards, _lever), ("ashby", settings.ashby_boards, _ashby)):
        for b in boards:
            try:
                res.jobs.extend(fn(settings, b))
            except (FetchError, ValueError) as exc:
                errors.append(f"{kind}:{b}: {exc}")
                logger.warning("ATS board %s:%s failed: %s", kind, b, exc)
    if errors:
        res.error = "; ".join(errors)[:500]
    return res
