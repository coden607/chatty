"""CMS NPPES NPI Registry API (free, keyless): organizational providers by taxonomy + city."""

from __future__ import annotations

import string
from typing import List

from ..models import Prospect
from ..net import get_json
from ..store import utcnow

URL = "https://npiregistry.cms.hhs.gov/api/"


def _fmt_phone(raw: str) -> str:
    digits = "".join(c for c in raw or "" if c.isdigit())[-10:]
    return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}" if len(digits) == 10 else raw or ""


def search(taxonomy: str, vertical: str, metro: str, city: str, state: str, settings) -> List[Prospect]:
    data = get_json(URL, user_agent=settings.ua(), min_interval=0.5, params={
        "version": "2.1", "taxonomy_description": taxonomy, "city": city, "state": state,
        "enumeration_type": "NPI-2", "limit": min(200, settings.npi_max_per_query),
    })
    now = utcnow()
    out: List[Prospect] = []
    for r in data.get("results", []) or []:
        basic = r.get("basic", {})
        if basic.get("status") not in (None, "A"):
            continue
        loc = next((a for a in r.get("addresses", []) if a.get("address_purpose") == "LOCATION"), None)
        if not loc or not loc.get("telephone_number"):
            continue
        name = basic.get("organization_name") or ""
        out.append(Prospect(
            source="NPI Registry",
            source_id=str(r.get("number")),
            name=string.capwords(name.lower()) if name.isupper() else name,
            vertical=vertical, metro=metro,
            phone=_fmt_phone(loc.get("telephone_number", "")),
            address=", ".join(x for x in [loc.get("address_1"), loc.get("city"), loc.get("state"), (loc.get("postal_code") or "")[:5]] if x),
            city=(loc.get("city") or "").title(), state=loc.get("state", ""),
            signals={"npi_taxonomy": taxonomy, "taxonomies": [t.get("desc") for t in r.get("taxonomies", [])][:3]},
            fetched_at=now,
        ))
    return out
