"""Remotive public API (keyless).

ToS: jobs are delayed 24h; link back to the Remotive URL and credit Remotive;
max ~2 requests/minute (we make one per run); don't republish to job boards.
"""

from __future__ import annotations

from ...models import Job
from ...net import get_json
from . import SourceResult, normalize_type, parse_salary, strip_html, us_eligibility

NAME = "Remotive"
REQUIRES: list = []
URL = "https://remotive.com/api/remote-jobs"


def fetch(settings) -> SourceResult:
    res = SourceResult(NAME)
    data = get_json(URL, user_agent=settings.ua(), params={"category": "software-dev", "limit": 300}, min_interval=31)
    for it in data.get("jobs", []):
        loc = it.get("candidate_required_location") or ""
        smin, smax = parse_salary(it.get("salary") or "")
        res.jobs.append(Job(
            source=NAME,
            source_url=it.get("url", ""),
            title=it.get("title", "").strip(),
            company=it.get("company_name", "").strip(),
            url=it.get("url", ""),
            location=loc,
            remote=True,
            us_eligible=us_eligibility(loc),
            job_type=normalize_type(it.get("job_type", "")),
            salary_min=smin, salary_max=smax,
            posted_at=(it.get("publication_date") or "") + ("" if not it.get("publication_date") or "+" in it.get("publication_date", "") else "+00:00"),
            description=strip_html(it.get("description", ""))[:4000],
            tags=[t for t in it.get("tags", []) if isinstance(t, str)],
            attribution="Job via Remotive (remotive.com)",
        ))
    return res
