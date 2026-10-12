"""Rule-based job scoring (0-100) with human-readable reasons."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import List, Tuple

from ..models import Job

ROLE_RE = re.compile(
    r"engineer|developer|programmer|software|full.?stack|back.?end|front.?end|devops|sre|platform|"
    r"automation|ml|machine learning|ai\b|llm|data engineer|solutions architect|integration|forward deployed",
    re.I,
)
NON_ROLE_RE = re.compile(
    r"\b(sales|account executive|recruiter|marketing manager|customer success|support specialist|nurse|"
    r"teacher|accountant|paralegal|driver|cashier|designer only|copywriter)\b",
    re.I,
)


def _has(term: str, text: str) -> bool:
    t = re.escape(term.lower()).replace(r"\ ", r"[\s\-]")
    return re.search(rf"(?<![a-z0-9]){t}(?![a-z0-9])", text) is not None


def _age_days(iso: str) -> float | None:
    if not iso:
        return None
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - dt).total_seconds() / 86400
    except ValueError:
        return None


def score_job(job: Job, settings) -> Tuple[int, List[str]]:
    reasons: List[str] = []
    title = job.title.lower()
    body = f"{job.title} {' '.join(job.tags)} {job.description[:3000]}".lower()
    score = 0

    # Role fit (title)
    if ROLE_RE.search(title):
        score += 25
        reasons.append("engineering/automation role")
    elif NON_ROLE_RE.search(title):
        return 0, ["non-engineering role"]

    # Primary keywords
    primary_hits = [k for k in settings.job_keywords if _has(k, body)]
    if not primary_hits:
        # "ai automation" style multi-word keywords: accept partial (both words anywhere)
        primary_hits = [k for k in settings.job_keywords if all(_has(w, body) for w in k.split())]
    if primary_hits:
        score += min(30, 15 * len(primary_hits))
        reasons.append("matches " + ", ".join(primary_hits))

    # Bonus stack terms
    bonus = [t for t in settings.job_bonus_terms if _has(t, body)]
    if bonus:
        score += min(15, 3 * len(bonus))
        reasons.append("stack: " + ", ".join(bonus[:6]))

    # Remote + US eligibility
    if job.remote:
        score += 10
        reasons.append("remote")
    if job.us_eligible is True:
        score += 10
        reasons.append("US-eligible")
    elif job.us_eligible is False:
        score -= 60
        reasons.append("not open to US-based workers")

    # Employment type
    if job.job_type and job.job_type not in settings.job_types:
        score -= 20
        reasons.append(f"type {job.job_type} not in {','.join(settings.job_types)}")
    elif job.job_type in ("contract",):
        reasons.append("contract")

    # Salary
    top = job.salary_max or job.salary_min
    if top and settings.min_salary and top < settings.min_salary:
        score -= 25
        reasons.append(f"salary below ${settings.min_salary:,}")
    elif top:
        score += 5
        reasons.append(f"salary listed (${top:,})")

    # Freshness
    age = _age_days(job.posted_at)
    if age is not None:
        if age <= 3:
            score += 5
            reasons.append("posted ≤3 days ago")
        elif age > settings.max_job_age_days:
            score -= 20
            reasons.append(f"older than {settings.max_job_age_days} days")

    # Deal-breakers
    neg = [t for t in settings.job_negative_terms if _has(t, body)]
    if neg:
        score -= 30
        reasons.append("flags: " + ", ".join(neg))

    return max(0, min(100, score)), reasons
