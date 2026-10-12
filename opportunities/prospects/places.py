"""Google Places API (New) Text Search with a hard monthly budget guard.

ToS notes: we store place_id indefinitely, and other Places content is purged
after OPP_PLACES_CACHE_DAYS (default 30) by Store.purge_stale_places_content.
"""

from __future__ import annotations

import logging
from typing import List

from ..models import Prospect
from ..net import request
from ..store import Store, utcnow

logger = logging.getLogger("opportunities.prospects.places")

URL = "https://places.googleapis.com/v1/places:searchText"
FIELD_MASK = ",".join([
    "places.id", "places.displayName", "places.formattedAddress", "places.nationalPhoneNumber",
    "places.websiteUri", "places.rating", "places.userRatingCount",
    "places.regularOpeningHours.weekdayDescriptions", "places.businessStatus",
])
SERVICE = "google_places_text_search"


class BudgetExceeded(RuntimeError):
    pass


def calls_remaining(store: Store, settings) -> int:
    return max(0, settings.places_monthly_call_cap - store.usage(SERVICE))


def search(query: str, vertical: str, metro: str, city: str, state: str, settings, store: Store) -> List[Prospect]:
    if calls_remaining(store, settings) <= 0:
        raise BudgetExceeded(
            f"Places monthly budget reached (${settings.places_monthly_budget_usd:.2f} ≈ {settings.places_monthly_call_cap} calls)"
        )
    store.add_usage(SERVICE, 1)  # count before calling, so failures can't overspend
    resp = request(
        "POST", URL, user_agent=settings.ua(), min_interval=0.2, retries=1,
        headers={"X-Goog-Api-Key": settings.google_places_api_key, "X-Goog-FieldMask": FIELD_MASK, "Content-Type": "application/json"},
        json={"textQuery": f"{query} in {city}, {state}", "pageSize": 20, "regionCode": "US", "languageCode": "en"},
    )
    if resp.status_code >= 400:
        raise RuntimeError(f"Places {resp.status_code}: {resp.text[:200]}")
    now = utcnow()
    out: List[Prospect] = []
    for p in resp.json().get("places", []):
        if p.get("businessStatus") not in (None, "OPERATIONAL"):
            continue
        addr = p.get("formattedAddress", "")
        out.append(Prospect(
            source="Google Places",
            source_id=p.get("id", ""),
            name=(p.get("displayName") or {}).get("text", ""),
            vertical=vertical, metro=metro,
            phone=p.get("nationalPhoneNumber", ""),
            website=p.get("websiteUri", ""),
            address=addr, city=city, state=state,
            rating=p.get("rating"), review_count=p.get("userRatingCount"),
            hours=list((p.get("regularOpeningHours") or {}).get("weekdayDescriptions") or []),
            signals={"places_query": query},
            fetched_at=now,
        ))
    return out
