"""Daily digest for Stephen ONLY.

The only recipient is OPP_DIGEST_TO. If RESEND_API_KEY / OPP_DIGEST_FROM /
OPP_DIGEST_TO are missing, the digest is written to a file instead of sent.
Every job credits its source and links to the source listing (Remotive /
Remote OK / USAJOBS attribution requirements).
"""

from __future__ import annotations

import html
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional

import httpx

from .config import Settings, get_settings
from .store import Store

logger = logging.getLogger("opportunities.digest")

EMAIL_RE = re.compile(r"^[^@\s,;]+@[^@\s,;]+\.[^@\s,;]+$")


def build(jobs: List[Dict], prospect_summary: Optional[Dict] = None) -> Dict[str, str]:
    today = datetime.now().strftime("%a %b %d, %Y")
    subject = f"Opportunity digest: {len(jobs)} new matching jobs ({today})"
    lines = [f"{len(jobs)} new US-remote matches for Python / TypeScript / AI automation.", ""]
    rows = []
    for j in jobs:
        sal = ""
        if j.get("salary_min") or j.get("salary_max"):
            lo, hi = j.get("salary_min"), j.get("salary_max")
            sal = f" | ${lo:,}" + (f"-${hi:,}" if hi and hi != lo else "") if lo else f" | up to ${hi:,}"
        jt = f" | {j['job_type'].replace('_', ' ')}" if j.get("job_type") else ""
        lines.append(f"[{j['score']}] {j['title']} - {j['company']}{jt}{sal}")
        lines.append(f"    {j.get('location') or 'Remote'} | via {j['source']}: {j['source_url'] or j['url']}")
        rows.append(
            f"<tr><td style='padding:6px 8px;font-weight:bold'>{j['score']}</td>"
            f"<td style='padding:6px 8px'><a href=\"{html.escape(j['url'] or j['source_url'])}\">{html.escape(j['title'])}</a>"
            f"<br><span style='color:#555'>{html.escape(j['company'])} · {html.escape(j.get('location') or 'Remote')}{html.escape(jt + sal)}</span>"
            f"<br><span style='color:#888;font-size:12px'>{html.escape('; '.join(j.get('reasons', [])[:3]))}</span></td>"
            f"<td style='padding:6px 8px;font-size:12px'>via <a href=\"{html.escape(j['source_url'] or j['url'])}\">{html.escape(j['source'])}</a></td></tr>"
        )
    if prospect_summary:
        g = prospect_summary.get("grades", {})
        lines += ["", f"Cortese prospects: A={g.get('A', 0)} B={g.get('B', 0)} C={g.get('C', 0)}; "
                      f"{prospect_summary.get('drafts_saved', 0)} new email drafts saved for review (not sent)."]
    text = "\n".join(lines)
    body_html = (
        f"<div style='font-family:system-ui,Arial,sans-serif'><h2 style='margin:0 0 8px'>Opportunity digest - {today}</h2>"
        f"<p>{len(jobs)} new US-remote matches for Python / TypeScript / AI automation.</p>"
        f"<table style='border-collapse:collapse'>{''.join(rows)}</table>"
        + (f"<p>{html.escape(lines[-1])}</p>" if prospect_summary else "")
        + "<p style='color:#888;font-size:12px'>Listings link back to their original source (Remotive, Remote OK, Himalayas, "
          "Hacker News, USAJOBS, Adzuna, company career pages).</p></div>"
    )
    return {"subject": subject, "text": text, "html": body_html}


def send_or_save(digest: Dict[str, str], settings: Settings) -> Dict:
    out_dir = settings.output_dir / "digests"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"digest_{datetime.now().strftime('%Y%m%d_%H%M')}.html"
    path.write_text(digest["html"], encoding="utf-8")

    to = settings.digest_to
    if not (settings.resend_api_key and settings.resend_from and to):
        missing = [n for n, v in (("RESEND_API_KEY", settings.resend_api_key), ("OPP_DIGEST_FROM", settings.resend_from), ("OPP_DIGEST_TO", to)) if not v]
        logger.info("📄 digest saved to %s (not emailed: missing %s)", path, ", ".join(missing))
        return {"sent": False, "path": str(path), "missing": missing}
    if not EMAIL_RE.match(to):
        logger.error("OPP_DIGEST_TO must be exactly one address; got %r. Digest saved, not sent.", to)
        return {"sent": False, "path": str(path), "error": "OPP_DIGEST_TO must be a single address"}
    r = httpx.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {settings.resend_api_key}"},
        json={"from": settings.resend_from, "to": [to], "subject": digest["subject"], "text": digest["text"], "html": digest["html"]},
        timeout=30,
    )
    if r.status_code >= 400:
        logger.error("Resend error %s: %s", r.status_code, r.text[:200])
        return {"sent": False, "path": str(path), "error": f"resend {r.status_code}"}
    logger.info("📧 digest emailed to %s", to)
    return {"sent": True, "path": str(path), "to": to}


def run_digest(settings: Optional[Settings] = None, store: Optional[Store] = None, limit: int = 40, send: bool = True) -> Dict:
    settings = settings or get_settings()
    store = store or Store(settings.db_path)
    jobs = store.list_jobs(min_score=settings.min_score, limit=limit, only_undigested=True)
    if not jobs:
        logger.info("No new jobs for the digest.")
        return {"sent": False, "jobs": 0}
    runs = [r for r in store.last_runs(20) if r["kind"] == "prospects"]
    d = build(jobs, runs[0]["summary"] if runs else None)
    result = send_or_save(d, settings) if send else {"sent": False, "preview": d["text"]}
    if result.get("sent") or (send and result.get("path")):
        store.mark_digested(j["dedupe_key"] for j in jobs)
    result["jobs"] = len(jobs)
    return result
