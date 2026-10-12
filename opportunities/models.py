"""Normalized records shared by all sources."""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()


@dataclass
class Job:
    source: str               # e.g. "Remotive" (shown to users for attribution)
    source_url: str           # canonical listing URL on the source (attribution link)
    title: str
    company: str
    url: str                  # apply / listing URL
    location: str = ""
    remote: bool = False
    us_eligible: Optional[bool] = None   # True=US ok, False=excluded, None=unknown
    job_type: str = ""        # full_time | contract | part_time | ...
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    posted_at: str = ""       # ISO8601
    description: str = ""
    tags: List[str] = field(default_factory=list)
    attribution: str = ""     # human-readable credit line required by some sources
    score: int = 0
    reasons: List[str] = field(default_factory=list)
    also_on: List[str] = field(default_factory=list)

    @property
    def dedupe_key(self) -> str:
        return hashlib.sha1(f"{_norm(self.company)}|{_norm(self.title)}".encode()).hexdigest()

    @property
    def url_key(self) -> str:
        return hashlib.sha1((self.url or self.source_url).strip().lower().rstrip("/").encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["dedupe_key"] = self.dedupe_key
        return d


@dataclass
class Prospect:
    source: str               # "Google Places" | "NPI Registry"
    source_id: str            # place_id or NPI number
    name: str
    vertical: str
    metro: str
    phone: str = ""
    website: str = ""
    address: str = ""
    city: str = ""
    state: str = ""
    rating: Optional[float] = None
    review_count: Optional[int] = None
    hours: List[str] = field(default_factory=list)
    signals: Dict[str, Any] = field(default_factory=dict)
    grade: str = ""
    score: int = 0
    reasons: List[str] = field(default_factory=list)
    fetched_at: str = ""

    @property
    def key(self) -> str:
        return f"{self.source}:{self.source_id}"

    @property
    def dedupe_key(self) -> str:
        phone = re.sub(r"\D", "", self.phone)[-10:]
        return phone or _norm(f"{self.name} {self.city} {self.state}")

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["key"] = self.key
        return d
