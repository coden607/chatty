"""Job source adapters. Each exposes ``NAME``, ``REQUIRES`` (env keys) and ``fetch(settings)``."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from ...models import Job


@dataclass
class SourceResult:
    name: str
    jobs: List[Job] = field(default_factory=list)
    skipped: Optional[str] = None   # reason the source did not run (e.g. missing key)
    error: Optional[str] = None     # error while running


_TAG_RE = re.compile(r"<[^>]+>")


def strip_html(text: str) -> str:
    text = re.sub(r"<\s*(br|p|li|/p|/li|div|/div)[^>]*>", "\n", text or "", flags=re.I)
    text = _TAG_RE.sub("", text)
    return re.sub(r"\n{3,}", "\n\n", html.unescape(text)).strip()


def iso_from_epoch(value) -> str:
    try:
        return datetime.fromtimestamp(int(value), tz=timezone.utc).replace(microsecond=0).isoformat()
    except (TypeError, ValueError, OSError):
        return ""


_US_STRONG = re.compile(r"\b(us|u\.s\.?|usa|united states|america|americas|north america|us-based|us only)\b", re.I)
_WORLDWIDE = re.compile(r"\b(worldwide|anywhere|global|any location)\b", re.I)
_US_TZ = re.compile(r"\b(est|edt|pst|pdt|cst|cdt|mst|mdt|eastern|pacific|central|mountain)\b", re.I)
_US_CITY_STATE = re.compile(
    r"\b[a-z .]+,\s?(al|ak|az|ar|ca|co|ct|de|fl|ga|hi|id|il|in|ia|ks|ky|la|me|md|ma|mi|mn|ms|mo|mt|ne|nv|nh|nj|nm|ny|nc|nd|oh|ok|or|pa|ri|sc|sd|tn|tx|ut|vt|va|wa|wv|wi|wy|dc)\b",
    re.I,
)
_NON_US = re.compile(
    r"\b(europe|emea|eu|uk|united kingdom|england|ireland|germany|france|spain|portugal|netherlands|poland|"
    r"india|apac|asia|latam|latin america|brazil|argentina|colombia|mexico|canada|australia|philippines|africa|"
    r"israel|ukraine|romania|singapore|japan|berlin|london|paris|amsterdam|toronto|bangalore|bengaluru|dublin)\b",
    re.I,
)


def us_eligibility(location: str, remote: bool = True) -> Optional[bool]:
    """Best-effort: True if US workers are eligible, False if clearly not, None if unknown."""
    loc = (location or "").strip()
    if not loc:
        return None
    if _US_STRONG.search(loc):
        return True
    if _NON_US.search(loc):
        return False
    if _WORLDWIDE.search(loc) or _US_TZ.search(loc) or _US_CITY_STATE.search(loc):
        return True
    return None


def parse_salary(text: str):
    """Extract a (min, max) annual USD salary from free text like '$120k - $150k'."""
    if not text:
        return None, None
    nums = []
    for m in re.finditer(r"\$?\s?(\d{2,3}(?:[,.]\d{3})?)\s?(k|K)?", text):
        raw, k = m.group(1), m.group(2)
        try:
            val = float(raw.replace(",", ""))
        except ValueError:
            continue
        if k:
            val *= 1000
        elif val < 1000:
            continue
        if 15000 <= val <= 1_000_000:
            nums.append(int(val))
    if not nums:
        return None, None
    return min(nums), max(nums)


def normalize_type(text: str) -> str:
    t = (text or "").lower().replace("-", "_").replace(" ", "_")
    if "contract" in t or "freelance" in t:
        return "contract"
    if "part" in t:
        return "part_time"
    if "full" in t or t in {"permanent", "fulltime"}:
        return "full_time"
    if "intern" in t:
        return "internship"
    return t or ""
