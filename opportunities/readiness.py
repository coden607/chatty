"""Which sources are enabled given the current env (no secrets are returned)."""

from __future__ import annotations

from .config import Settings
from .store import Store


def readiness(s: Settings) -> dict:
    store = Store(s.db_path)
    return {
        "jobs": {
            "keyless (always on)": ["Remotive", "Remote OK", "Himalayas", "HN Who is hiring", "Greenhouse/Lever/Ashby boards"],
            "Adzuna": "ready" if s.adzuna_app_id and s.adzuna_app_key else "needs ADZUNA_APP_ID + ADZUNA_APP_KEY",
            "USAJOBS": "ready" if s.usajobs_api_key and s.usajobs_email else "needs USAJOBS_API_KEY + USAJOBS_EMAIL",
        },
        "prospects": {
            "NPI Registry": "ready (keyless)",
            "Google Places": "ready" if s.google_places_api_key else "needs GOOGLE_PLACES_API_KEY",
            "places_budget": {
                "monthly_usd": s.places_monthly_budget_usd, "cost_per_call_usd": s.places_cost_per_call_usd,
                "monthly_call_cap": s.places_monthly_call_cap, "used_this_month": store.usage("google_places_text_search"),
            },
            "email drafts": "LLM (OpenRouter/xAI)" if (s.openrouter_api_key or s.xai_api_key) else "template (set OPENROUTER_API_KEY or XAI_API_KEY for AI drafts)",
            "sender_address_set": "CAN-SPAM" not in s.sender_address,
        },
        "digest": {
            "to": s.digest_to or "needs OPP_DIGEST_TO",
            "delivery": "email via Resend" if (s.resend_api_key and s.resend_from and s.digest_to) else "saved to file (needs RESEND_API_KEY + OPP_DIGEST_FROM + OPP_DIGEST_TO)",
        },
        "db": str(s.db_path),
        "last_runs": store.last_runs(5),
    }
