"""SQLite persistence for jobs, prospects, drafts, and Places budget usage."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .models import Job, Prospect

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    dedupe_key TEXT PRIMARY KEY,
    url_key TEXT,
    source TEXT, source_url TEXT, title TEXT, company TEXT, url TEXT,
    location TEXT, remote INTEGER, us_eligible INTEGER, job_type TEXT,
    salary_min INTEGER, salary_max INTEGER, posted_at TEXT,
    description TEXT, tags TEXT, attribution TEXT,
    score INTEGER, reasons TEXT, also_on TEXT,
    first_seen TEXT, last_seen TEXT, digested_at TEXT, status TEXT DEFAULT 'new'
);
CREATE INDEX IF NOT EXISTS idx_jobs_url ON jobs(url_key);
CREATE INDEX IF NOT EXISTS idx_jobs_score ON jobs(score);

CREATE TABLE IF NOT EXISTS prospects (
    key TEXT PRIMARY KEY,
    dedupe_key TEXT,
    source TEXT, source_id TEXT, name TEXT, vertical TEXT, metro TEXT,
    phone TEXT, website TEXT, address TEXT, city TEXT, state TEXT,
    rating REAL, review_count INTEGER, hours TEXT, signals TEXT,
    grade TEXT, score INTEGER, reasons TEXT,
    fetched_at TEXT, first_seen TEXT, last_seen TEXT, status TEXT DEFAULT 'new'
);
CREATE INDEX IF NOT EXISTS idx_prospects_dedupe ON prospects(dedupe_key);

CREATE TABLE IF NOT EXISTS drafts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prospect_key TEXT UNIQUE,
    subject TEXT, body TEXT, generator TEXT,
    status TEXT DEFAULT 'draft',
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS api_usage (
    service TEXT, month TEXT, calls INTEGER DEFAULT 0,
    PRIMARY KEY (service, month)
);

CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT);

CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT, started_at TEXT, finished_at TEXT, summary TEXT
);
"""


def utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class Store:
    def __init__(self, path: Path | str):
        self.path = Path(path)
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    # ---------------------------------------------------------------- jobs
    def upsert_jobs(self, jobs: Iterable[Job]) -> Dict[str, int]:
        new = updated = 0
        now = utcnow()
        cur = self.conn.cursor()
        for j in jobs:
            row = cur.execute("SELECT dedupe_key FROM jobs WHERE dedupe_key=? OR url_key=?", (j.dedupe_key, j.url_key)).fetchone()
            vals = (
                j.url_key, j.source, j.source_url, j.title, j.company, j.url, j.location,
                int(j.remote), None if j.us_eligible is None else int(j.us_eligible), j.job_type,
                j.salary_min, j.salary_max, j.posted_at, (j.description or "")[:4000],
                json.dumps(j.tags), j.attribution, j.score, json.dumps(j.reasons), json.dumps(j.also_on),
            )
            if row:
                cur.execute(
                    """UPDATE jobs SET url_key=?, source=?, source_url=?, title=?, company=?, url=?, location=?,
                       remote=?, us_eligible=?, job_type=?, salary_min=?, salary_max=?, posted_at=?, description=?,
                       tags=?, attribution=?, score=?, reasons=?, also_on=?, last_seen=? WHERE dedupe_key=?""",
                    vals + (now, row["dedupe_key"]),
                )
                updated += 1
            else:
                cur.execute(
                    """INSERT INTO jobs (url_key, source, source_url, title, company, url, location, remote, us_eligible,
                       job_type, salary_min, salary_max, posted_at, description, tags, attribution, score, reasons, also_on,
                       first_seen, last_seen, dedupe_key) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    vals + (now, now, j.dedupe_key),
                )
                new += 1
        self.conn.commit()
        return {"new": new, "updated": updated}

    def list_jobs(self, min_score: int = 0, limit: int = 200, only_undigested: bool = False) -> List[Dict[str, Any]]:
        q = "SELECT * FROM jobs WHERE score >= ?"
        if only_undigested:
            q += " AND digested_at IS NULL"
        q += " ORDER BY score DESC, posted_at DESC LIMIT ?"
        return [self._job_row(r) for r in self.conn.execute(q, (min_score, limit))]

    def mark_digested(self, keys: Iterable[str]) -> None:
        now = utcnow()
        self.conn.executemany("UPDATE jobs SET digested_at=? WHERE dedupe_key=?", [(now, k) for k in keys])
        self.conn.commit()

    @staticmethod
    def _job_row(r: sqlite3.Row) -> Dict[str, Any]:
        d = dict(r)
        for k in ("tags", "reasons", "also_on"):
            d[k] = json.loads(d.get(k) or "[]")
        d["remote"] = bool(d.get("remote"))
        return d

    # ----------------------------------------------------------- prospects
    def upsert_prospects(self, prospects: Iterable[Prospect]) -> Dict[str, int]:
        new = updated = 0
        now = utcnow()
        cur = self.conn.cursor()
        for p in prospects:
            existing = cur.execute("SELECT key FROM prospects WHERE key=?", (p.key,)).fetchone()
            if not existing and p.dedupe_key:
                existing = cur.execute("SELECT key FROM prospects WHERE dedupe_key=?", (p.dedupe_key,)).fetchone()
            vals = (
                p.dedupe_key, p.source, p.source_id, p.name, p.vertical, p.metro, p.phone, p.website,
                p.address, p.city, p.state, p.rating, p.review_count, json.dumps(p.hours), json.dumps(p.signals),
                p.grade, p.score, json.dumps(p.reasons), p.fetched_at or now,
            )
            if existing:
                cur.execute(
                    """UPDATE prospects SET dedupe_key=?, source=?, source_id=?, name=?, vertical=?, metro=?, phone=?,
                       website=?, address=?, city=?, state=?, rating=?, review_count=?, hours=?, signals=?, grade=?,
                       score=?, reasons=?, fetched_at=?, last_seen=? WHERE key=?""",
                    vals + (now, existing["key"]),
                )
                updated += 1
            else:
                cur.execute(
                    """INSERT INTO prospects (dedupe_key, source, source_id, name, vertical, metro, phone, website,
                       address, city, state, rating, review_count, hours, signals, grade, score, reasons, fetched_at,
                       first_seen, last_seen, key) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    vals + (now, now, p.key),
                )
                new += 1
        self.conn.commit()
        return {"new": new, "updated": updated}

    def list_prospects(self, grade: Optional[str] = None, vertical: Optional[str] = None, limit: int = 1000) -> List[Dict[str, Any]]:
        q, args = "SELECT * FROM prospects WHERE 1=1", []
        if grade:
            q += " AND grade=?"
            args.append(grade.upper())
        if vertical:
            q += " AND vertical=?"
            args.append(vertical)
        q += " ORDER BY score DESC LIMIT ?"
        args.append(limit)
        out = []
        for r in self.conn.execute(q, args):
            d = dict(r)
            for k in ("hours", "reasons"):
                d[k] = json.loads(d.get(k) or "[]")
            d["signals"] = json.loads(d.get("signals") or "{}")
            out.append(d)
        return out

    def purge_stale_places_content(self, max_age_days: int) -> int:
        """Google Maps ToS: keep place_id indefinitely, but don't cache other Places content > 30 days."""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=max_age_days)).replace(microsecond=0).isoformat()
        cur = self.conn.execute(
            """UPDATE prospects SET name='[expired - refresh]', phone='', website='', address='', rating=NULL,
               review_count=NULL, hours='[]' WHERE source='Google Places' AND fetched_at < ? AND name != '[expired - refresh]'""",
            (cutoff,),
        )
        self.conn.commit()
        return cur.rowcount

    # --------------------------------------------------------------- drafts
    def save_draft(self, prospect_key: str, subject: str, body: str, generator: str) -> bool:
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO drafts (prospect_key, subject, body, generator, status, created_at) VALUES (?,?,?,?, 'draft', ?)",
            (prospect_key, subject, body, generator, utcnow()),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def list_drafts(self, limit: int = 200) -> List[Dict[str, Any]]:
        return [dict(r) for r in self.conn.execute("SELECT * FROM drafts ORDER BY id DESC LIMIT ?", (limit,))]

    def has_draft(self, prospect_key: str) -> bool:
        return self.conn.execute("SELECT 1 FROM drafts WHERE prospect_key=?", (prospect_key,)).fetchone() is not None

    # ---------------------------------------------------------------- usage
    def usage(self, service: str, month: Optional[str] = None) -> int:
        month = month or datetime.now(timezone.utc).strftime("%Y-%m")
        r = self.conn.execute("SELECT calls FROM api_usage WHERE service=? AND month=?", (service, month)).fetchone()
        return int(r["calls"]) if r else 0

    def add_usage(self, service: str, n: int = 1) -> int:
        month = datetime.now(timezone.utc).strftime("%Y-%m")
        self.conn.execute(
            "INSERT INTO api_usage (service, month, calls) VALUES (?,?,?) ON CONFLICT(service, month) DO UPDATE SET calls = calls + ?",
            (service, month, n, n),
        )
        self.conn.commit()
        return self.usage(service, month)

    # ------------------------------------------------------------------ kv
    def get(self, k: str, default: Optional[str] = None) -> Optional[str]:
        r = self.conn.execute("SELECT v FROM kv WHERE k=?", (k,)).fetchone()
        return r["v"] if r else default

    def set(self, k: str, v: str) -> None:
        self.conn.execute("INSERT INTO kv (k, v) VALUES (?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v", (k, v))
        self.conn.commit()

    def log_run(self, kind: str, started_at: str, summary: Dict[str, Any]) -> None:
        self.conn.execute("INSERT INTO runs (kind, started_at, finished_at, summary) VALUES (?,?,?,?)", (kind, started_at, utcnow(), json.dumps(summary)))
        self.conn.commit()

    def last_runs(self, limit: int = 10) -> List[Dict[str, Any]]:
        out = []
        for r in self.conn.execute("SELECT * FROM runs ORDER BY id DESC LIMIT ?", (limit,)):
            d = dict(r)
            d["summary"] = json.loads(d.get("summary") or "{}")
            out.append(d)
        return out
