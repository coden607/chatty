"""USAJOBS search API (free key: USAJOBS_API_KEY + the registered USAJOBS_EMAIL).

ToS: credit USAJOBS and send applicants to the USAJOBS listing; don't resell or
redistribute the data as a standalone feed.
"""

from __future__ import annotations

from ...models import Job
from ...net import get_json
from . import SourceResult

NAME = "USAJOBS"
REQUIRES = ["USAJOBS_API_KEY", "USAJOBS_EMAIL"]
URL = "https://data.usajobs.gov/api/Search"


def fetch(settings) -> SourceResult:
    res = SourceResult(NAME)
    if not (settings.usajobs_api_key and settings.usajobs_email):
        res.skipped = "missing USAJOBS_API_KEY / USAJOBS_EMAIL"
        return res
    headers = {"Host": "data.usajobs.gov", "Authorization-Key": settings.usajobs_api_key}
    for kw in settings.job_keywords:
        data = get_json(URL, user_agent=settings.usajobs_email, headers=headers, min_interval=2, params={
            "Keyword": kw, "RemoteIndicator": "True", "ResultsPerPage": 100, "DatePosted": settings.max_job_age_days,
        })
        for item in (data.get("SearchResult") or {}).get("SearchResultItems", []):
            d = item.get("MatchedObjectDescriptor", {})
            pay = (d.get("PositionRemuneration") or [{}])[0]
            try:
                smin, smax = int(float(pay.get("MinimumRange"))), int(float(pay.get("MaximumRange")))
            except (TypeError, ValueError):
                smin = smax = None
            if pay.get("RateIntervalCode") not in (None, "PA"):
                smin = smax = None
            sched = ", ".join(s.get("Name", "") for s in d.get("PositionSchedule", []))
            res.jobs.append(Job(
                source=NAME, source_url=d.get("PositionURI", ""), title=d.get("PositionTitle", ""),
                company=d.get("OrganizationName", ""), url=(d.get("ApplyURI") or [d.get("PositionURI", "")])[0],
                location=d.get("PositionLocationDisplay", ""), remote=True, us_eligible=True,
                job_type="full_time" if "Full" in sched else sched.lower(),
                salary_min=smin, salary_max=smax, posted_at=d.get("PublicationStartDate", ""),
                description=((d.get("UserArea") or {}).get("Details") or {}).get("JobSummary", "")[:4000],
                attribution="Listing from USAJOBS (usajobs.gov)",
            ))
    return res
