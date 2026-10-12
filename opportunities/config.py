"""Settings for the opportunity finder, read from the environment.

Secrets come from env vars (optionally loaded from CHATTY_SECRETS_FILE / .env by
the caller). Nothing here is required: missing keys simply disable a source.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

try:  # Load secrets if python-dotenv is available; never fatal.
    from dotenv import load_dotenv

    _secrets = os.getenv("CHATTY_SECRETS_FILE") or os.path.expanduser("~/.config/chatty/secrets.env")
    if os.path.exists(_secrets):
        load_dotenv(_secrets, override=False)
    load_dotenv(override=False)
except Exception:  # pragma: no cover
    pass

REPO_ROOT = Path(__file__).resolve().parent.parent


def _list(name: str, default: str) -> List[str]:
    raw = os.getenv(name, default)
    return [p.strip() for p in raw.split(",") if p.strip()]


def _float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


@dataclass
class Settings:
    # Storage / output
    db_path: Path = field(default_factory=lambda: Path(os.getenv("OPP_DB_PATH") or REPO_ROOT / "generated_content" / "opportunities" / "opportunities.db"))
    output_dir: Path = field(default_factory=lambda: Path(os.getenv("OPP_OUTPUT_DIR") or REPO_ROOT / "generated_content" / "opportunities"))
    user_agent: str = field(default_factory=lambda: os.getenv("OPP_USER_AGENT", "CorteseDigital-OpportunityFinder/1.0 (+contact: set OPP_CONTACT_EMAIL)"))
    contact_email: str = field(default_factory=lambda: os.getenv("OPP_CONTACT_EMAIL", ""))

    # Job targeting
    job_keywords: List[str] = field(default_factory=lambda: _list("OPP_JOB_KEYWORDS", "python,typescript,ai automation"))
    job_bonus_terms: List[str] = field(default_factory=lambda: _list(
        "OPP_JOB_BONUS_TERMS",
        "python,typescript,javascript,node,react,next.js,fastapi,django,flask,llm,ai,machine learning,automation,agent,agents,openai,langchain,n8n,zapier,integration,api,backend,full stack,full-stack",
    ))
    job_negative_terms: List[str] = field(default_factory=lambda: _list(
        "OPP_JOB_NEGATIVE_TERMS",
        "clearance required,active clearance,ts/sci,on-site only,onsite only,unpaid,commission only,internship",
    ))
    job_types: List[str] = field(default_factory=lambda: _list("OPP_JOB_TYPES", "full_time,contract"))
    remote_only: bool = field(default_factory=lambda: os.getenv("OPP_REMOTE_ONLY", "true").lower() in ("1", "true", "yes"))
    min_salary: int = field(default_factory=lambda: _int("OPP_MIN_SALARY_USD", 0))
    min_score: int = field(default_factory=lambda: _int("OPP_MIN_JOB_SCORE", 40))
    max_job_age_days: int = field(default_factory=lambda: _int("OPP_MAX_JOB_AGE_DAYS", 30))

    # ATS boards (public job-board APIs, one employer each)
    greenhouse_boards: List[str] = field(default_factory=lambda: _list("OPP_GREENHOUSE_BOARDS", "anthropic,vercel,gitlab,cloudflare,airtable"))
    lever_boards: List[str] = field(default_factory=lambda: _list("OPP_LEVER_BOARDS", "palantir,spotify"))
    ashby_boards: List[str] = field(default_factory=lambda: _list("OPP_ASHBY_BOARDS", "openai,supabase,linear,ramp,notion,replit"))

    # Keys (all optional)
    adzuna_app_id: str = field(default_factory=lambda: os.getenv("ADZUNA_APP_ID", ""))
    adzuna_app_key: str = field(default_factory=lambda: os.getenv("ADZUNA_APP_KEY", ""))
    usajobs_api_key: str = field(default_factory=lambda: os.getenv("USAJOBS_API_KEY", ""))
    usajobs_email: str = field(default_factory=lambda: os.getenv("USAJOBS_EMAIL", ""))
    google_places_api_key: str = field(default_factory=lambda: os.getenv("GOOGLE_PLACES_API_KEY", ""))
    resend_api_key: str = field(default_factory=lambda: os.getenv("RESEND_API_KEY", ""))
    resend_from: str = field(default_factory=lambda: os.getenv("OPP_DIGEST_FROM") or os.getenv("RESEND_FROM_EMAIL", ""))
    openrouter_api_key: str = field(default_factory=lambda: os.getenv("OPENROUTER_API_KEY", ""))
    xai_api_key: str = field(default_factory=lambda: os.getenv("XAI_API_KEY", ""))
    draft_model: str = field(default_factory=lambda: os.getenv("OPP_DRAFT_MODEL", ""))

    # Digest (Stephen only)
    digest_to: str = field(default_factory=lambda: os.getenv("OPP_DIGEST_TO", "").strip())
    digest_hour_local: int = field(default_factory=lambda: _int("OPP_DIGEST_HOUR", 8))

    # Prospects
    verticals: List[str] = field(default_factory=lambda: _list("OPP_VERTICALS", "dental,med_spa,home_services,law_firm,auto_repair"))
    metro_limit: int = field(default_factory=lambda: _int("OPP_METRO_LIMIT", 100))
    places_monthly_budget_usd: float = field(default_factory=lambda: _float("OPP_PLACES_MONTHLY_BUDGET_USD", 50.0))
    # Text Search with phone/website/hours/rating fields bills at the Enterprise SKU (~$35/1k at entry tier).
    places_cost_per_call_usd: float = field(default_factory=lambda: _float("OPP_PLACES_COST_PER_CALL_USD", 0.035))
    places_max_calls_per_run: int = field(default_factory=lambda: _int("OPP_PLACES_MAX_CALLS_PER_RUN", 250))
    places_cache_days: int = field(default_factory=lambda: _int("OPP_PLACES_CACHE_DAYS", 30))
    npi_max_per_query: int = field(default_factory=lambda: _int("OPP_NPI_MAX_PER_QUERY", 50))
    website_checks: bool = field(default_factory=lambda: os.getenv("OPP_WEBSITE_CHECKS", "true").lower() in ("1", "true", "yes"))

    # Sender identity for drafts (CAN-SPAM)
    sender_name: str = field(default_factory=lambda: os.getenv("CORTESE_SENDER_NAME", "Stephen Blanford"))
    sender_company: str = field(default_factory=lambda: os.getenv("CORTESE_COMPANY", "Cortese Digital"))
    sender_address: str = field(default_factory=lambda: os.getenv("CORTESE_POSTAL_ADDRESS", "[YOUR BUSINESS POSTAL ADDRESS - required by CAN-SPAM]"))
    sender_site: str = field(default_factory=lambda: os.getenv("CORTESE_WEBSITE", ""))

    # Scheduling
    jobs_interval_hours: float = field(default_factory=lambda: _float("OPP_JOBS_INTERVAL_HOURS", 24))
    prospects_interval_hours: float = field(default_factory=lambda: _float("OPP_PROSPECTS_INTERVAL_HOURS", 24 * 7))

    @property
    def places_monthly_call_cap(self) -> int:
        if self.places_cost_per_call_usd <= 0:
            return 0
        return int(self.places_monthly_budget_usd / self.places_cost_per_call_usd)

    def ua(self) -> str:
        if self.contact_email and "set OPP_CONTACT_EMAIL" in self.user_agent:
            return f"CorteseDigital-OpportunityFinder/1.0 (+{self.contact_email})"
        return self.user_agent


def get_settings() -> Settings:
    return Settings()
