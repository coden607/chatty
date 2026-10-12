"""CSV export of prospects."""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Dict, Iterable, Optional

COLUMNS = ["grade", "score", "name", "vertical", "metro", "phone", "website", "address", "city", "state",
           "rating", "review_count", "reasons", "source", "source_id", "first_seen"]


def to_csv(rows: Iterable[Dict], path: Optional[Path] = None) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLUMNS, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        r = dict(r)
        r["reasons"] = "; ".join(r.get("reasons") or [])
        w.writerow(r)
    text = buf.getvalue()
    if path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return text
