"""CLI: python -m opportunities {jobs,prospects,digest,export,status}"""

from __future__ import annotations

import argparse
import json
import logging
import sys

from .config import get_settings
from .store import Store


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m opportunities", description="Coding-job + Cortese prospect finder")
    ap.add_argument("-v", "--verbose", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)

    j = sub.add_parser("jobs", help="fetch, score and store jobs")
    j.add_argument("--dry-run", action="store_true", help="don't write to the database; print results")
    j.add_argument("--keyless", action="store_true", help="only keyless sources")
    j.add_argument("--sources", help="comma list: remotive,remoteok,himalayas,hn,ats,adzuna,usajobs")
    j.add_argument("--top", type=int, default=20)

    p = sub.add_parser("prospects", help="discover, score, export and draft (drafts are never sent)")
    p.add_argument("--dry-run", action="store_true", help="no DB/CSV/drafts written; print results")
    p.add_argument("--metros", type=int, help="number of metros (default OPP_METRO_LIMIT=100)")
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--no-places", action="store_true")
    p.add_argument("--no-npi", action="store_true")
    p.add_argument("--no-web", action="store_true", help="skip homepage checks")
    p.add_argument("--max-places-calls", type=int)
    p.add_argument("--draft-grades", default="A")
    p.add_argument("--max-drafts", type=int, default=25)
    p.add_argument("--top", type=int, default=20)

    d = sub.add_parser("digest", help="build the daily digest (to OPP_DIGEST_TO only)")
    d.add_argument("--preview", action="store_true", help="print, don't send or mark as digested")

    e = sub.add_parser("export", help="export stored prospects to CSV")
    e.add_argument("--grade")
    e.add_argument("--out")

    sub.add_parser("status", help="show config readiness and last runs")

    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if a.verbose else logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    if not a.verbose:
        logging.getLogger("httpx").setLevel(logging.WARNING)
    s = get_settings()

    if a.cmd == "jobs":
        from .jobs.finder import KEYLESS, find_jobs
        srcs = KEYLESS if a.keyless else (a.sources.split(",") if a.sources else None)
        r = find_jobs(s, sources=srcs, persist=not a.dry_run)
        print(json.dumps(r["summary"], indent=2))
        for job in r["jobs"][: a.top]:
            print(f"[{job.score:3}] {job.title[:70]} | {job.company[:30]} | {job.location[:40] or 'Remote'} | via {job.source}\n       {job.url}")
        return 0

    if a.cmd == "prospects":
        from .prospects.finder import find_prospects
        r = find_prospects(
            s, store=Store(":memory:") if a.dry_run else None, metro_limit=a.metros, metro_offset=a.offset,
            use_places=not a.no_places, use_npi=not a.no_npi, check_websites=False if a.no_web else None,
            max_places_calls=a.max_places_calls, draft_grades=a.draft_grades, max_drafts=a.max_drafts, persist=not a.dry_run,
        )
        print(json.dumps(r["summary"], indent=2, default=str))
        for p in r["prospects"][: a.top]:
            print(f"[{p.grade} {p.score:3}] {p.name[:45]} | {p.vertical} | {p.phone} | {p.city}, {p.state} | {p.source} | {'; '.join(p.reasons[:3])}")
        return 0

    if a.cmd == "digest":
        from .digest import run_digest
        r = run_digest(s, send=not a.preview)
        print(r.get("preview") or json.dumps(r, indent=2))
        return 0

    if a.cmd == "export":
        from pathlib import Path
        from .prospects.export import to_csv
        rows = Store(s.db_path).list_prospects(grade=a.grade)
        out = Path(a.out) if a.out else s.output_dir / "cortese_prospects_export.csv"
        to_csv(rows, out)
        print(f"wrote {len(rows)} prospects to {out}")
        return 0

    if a.cmd == "status":
        from .readiness import readiness
        print(json.dumps(readiness(s), indent=2, default=str))
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
