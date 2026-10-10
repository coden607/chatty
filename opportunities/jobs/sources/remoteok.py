"""Remote OK public API (keyless).

ToS (shipped inside the response): link back to the Remote OK URL with a
followed link and mention Remote OK as the source; don't use their logo.
"""

from __future__ import annotations

from ...models import Job
from ...net import get_json
from . import SourceResult, iso_from_epoch, strip_html, us_eligibility

NAME = "Remote OK"
REQUIRES: list = []
URL = "https://remoteok.com/api"


def fetch(settings) -> SourceResult:
    res = SourceResult(NAME)
    data = get_json(URL, user_agent=settings.ua(), min_interval=5)
    for it in data if isinstance(data, list) else []:
        if not isinstance(it, dict) or "position" not in it:
            continue  # first element is the legal notice
        loc = it.get("location") or ""
        smin = int(it["salary_min"]) if str(it.get("salary_min") or "").isdigit() and int(it["salary_min"]) > 0 else None
        smax = int(it["salary_max"]) if str(it.get("salary_max") or "").isdigit() and int(it["salary_max"]) > 0 else None
        res.jobs.append(Job(
            source=NAME,
            source_url=it.get("url", ""),
            title=(it.get("position") or "").strip(),
            company=(it.get("company") or "").strip(),
            url=it.get("url", ""),   # link to the Remote OK listing (required attribution)
            location=loc,
            remote=True,
            us_eligible=us_eligibility(loc),
            job_type="",
            salary_min=smin, salary_max=smax,
            posted_at=it.get("date") or iso_from_epoch(it.get("epoch")),
            description=strip_html(it.get("description", ""))[:4000],
            tags=[t for t in it.get("tags", []) if isinstance(t, str)],
            attribution="Job via Remote OK (remoteok.com)",
        ))
    return res
