"""Hacker News "Ask HN: Who is hiring?" monthly thread via the official Algolia HN API (keyless)."""

from __future__ import annotations

import re

from ...models import Job
from ...net import get_json
from . import SourceResult, iso_from_epoch, normalize_type, parse_salary, strip_html, us_eligibility

NAME = "HN Who is hiring"
REQUIRES: list = []
SEARCH = "https://hn.algolia.com/api/v1/search_by_date"
ITEM = "https://hn.algolia.com/api/v1/items/{id}"


def _latest_story_id(settings) -> str | None:
    data = get_json(SEARCH, user_agent=settings.ua(), params={"tags": "story,author_whoishiring", "query": "who is hiring", "hitsPerPage": 5})
    for hit in data.get("hits", []):
        if "who is hiring" in (hit.get("title") or "").lower():
            return hit.get("objectID")
    return None


_LOC_WORDS = re.compile(r"\b(remote|onsite|on-site|hybrid|in-office|usa?|united states|europe|emea|worldwide|anywhere|canada|uk)\b", re.I)
_CITY_ST = re.compile(
    r"\b[A-Z][a-z]+(?: [A-Z][a-z]+)*, (?:AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY|DC)\b"
)


def parse_comment(c: dict) -> Job | None:
    text = strip_html(c.get("text") or "")
    if not text:
        return None
    first = text.splitlines()[0].strip()
    if "|" not in first or "remote" not in first.lower():
        return None  # only posts whose header line advertises remote work
    parts = [p.strip() for p in first.split("|") if p.strip()]
    company = re.sub(r"\s*\(.*?\)\s*", " ", parts[0]).strip()[:120]
    role = next((p for p in parts[1:] if re.search(r"engineer|developer|dev\b|programmer|architect|scientist|ml|ai|full.?stack|backend|frontend|sre|devops", p, re.I)), parts[1] if len(parts) > 1 else "Engineering roles")
    location = " | ".join(p for p in parts[1:] if _LOC_WORDS.search(p) or _CITY_ST.search(p))
    smin, smax = parse_salary(first)
    jtype = "contract" if re.search(r"contract|freelance", first, re.I) else ("full_time" if re.search(r"full.?time", first, re.I) else "")
    url = f"https://news.ycombinator.com/item?id={c.get('id')}"
    link = re.search(r"https?://[^\s)]+", text)
    return Job(
        source=NAME,
        source_url=url,
        title=role[:160],
        company=company,
        url=url,
        location=location or "Remote (see post)",
        remote=True,
        us_eligible=us_eligibility(location or first),
        job_type=normalize_type(jtype),
        salary_min=smin, salary_max=smax,
        posted_at=iso_from_epoch(c.get("created_at_i")) or (c.get("created_at") or ""),
        description=text[:4000] + (f"\n\nCompany link: {link.group(0)}" if link else ""),
        tags=[],
        attribution="Posted in Hacker News 'Who is hiring?'",
    )


def fetch(settings) -> SourceResult:
    res = SourceResult(NAME)
    story = _latest_story_id(settings)
    if not story:
        res.error = "no 'Who is hiring?' thread found"
        return res
    item = get_json(ITEM.format(id=story), user_agent=settings.ua(), timeout=40)
    for child in item.get("children", []):
        job = parse_comment(child)
        if job:
            res.jobs.append(job)
    return res
