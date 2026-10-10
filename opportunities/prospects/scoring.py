"""A/B/C scoring for missed-call-recovery fit."""

from __future__ import annotations

import re
from typing import List, Tuple

from ..models import Prospect
from .verticals import VERTICALS

A_MIN, B_MIN = 65, 40


def _close_hour(desc: str):
    """'Monday: 8:00 AM – 5:00 PM' -> 17 (last closing hour of the day)."""
    times = re.findall(r"(\d{1,2})(?::\d{2})?\s?([AP]M)", desc, re.I)
    if not times:
        return None
    h, ap = times[-1]
    h = int(h) % 12 + (12 if ap.upper() == "PM" else 0)
    return h


def hours_signals(hours: List[str]) -> dict:
    if not hours:
        return {}
    text = " ".join(hours).lower()
    if "open 24 hours" in text:
        return {"open_24h": True}
    sat = next((h for h in hours if h.lower().startswith("saturday")), "")
    sun = next((h for h in hours if h.lower().startswith("sunday")), "")
    weekdays = [h for h in hours if h.split(":")[0].lower() in ("monday", "tuesday", "wednesday", "thursday", "friday")]
    closes = [c for c in (_close_hour(h) for h in weekdays if "closed" not in h.lower()) if c is not None]
    return {
        "closed_weekends": "closed" in sat.lower() and "closed" in sun.lower(),
        "closes_by_6pm": bool(closes) and sum(1 for c in closes if c <= 18) >= max(1, len(closes) - 1),
    }


def score_prospect(p: Prospect) -> Tuple[str, int, List[str]]:
    s, reasons = 0, []
    sig = dict(p.signals)
    sig.update(hours_signals(p.hours))
    p.signals = sig

    if not p.phone:
        return "C", 0, ["no phone listed"]

    v = VERTICALS.get(p.vertical, {})
    s += v.get("weight", 5)
    reasons.append(f"{v.get('label', p.vertical)} (phone-dependent)")

    if not p.website:
        if p.source == "Google Places":
            s += 15
            reasons.append("no website: nearly all leads arrive by phone")
        else:
            reasons.append("website unknown (NPI record)")
    else:
        s += 5
    if sig.get("website_checked"):
        if not sig.get("online_booking"):
            s += 25
            reasons.append("no online booking on site")
        if not sig.get("chat_or_text_widget"):
            s += 20
            reasons.append("no chat/text-back widget")
        if not sig.get("after_hours_mention") and not sig.get("open_24h"):
            s += 10
            reasons.append("no after-hours/answering line advertised")

    if sig.get("closed_weekends"):
        s += 10
        reasons.append("closed weekends")
    if sig.get("closes_by_6pm"):
        s += 10
        reasons.append("closes by 6pm on weekdays")
    if sig.get("open_24h"):
        s -= 10
        reasons.append("advertises 24h availability")

    rc = p.review_count or 0
    if 10 <= rc <= 400:
        s += 15
        reasons.append(f"{rc} reviews (established independent)")
    elif rc > 1500:
        s -= 10
        reasons.append(f"{rc} reviews (likely chain/large org)")
    if p.rating and p.rating >= 4.0:
        s += 5
        reasons.append(f"rating {p.rating}")

    if p.source == "NPI Registry" and not sig.get("website_checked"):
        s += 10  # independent licensed practice with a public phone
        reasons.append("independent licensed practice (NPI)")

    s = max(0, min(100, s))
    grade = "A" if s >= A_MIN else "B" if s >= B_MIN else "C"
    return grade, s, reasons
