"""AI-drafted first-touch emails, saved as DRAFTS ONLY.

There is intentionally no send function in this module or anywhere in the
prospect pipeline. Drafts go to SQLite + markdown files for human review.
No recipient addresses are scraped or guessed.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Dict, Optional, Tuple

import httpx

from .verticals import VERTICALS

logger = logging.getLogger("opportunities.prospects.drafts")

SYSTEM = (
    "You write short, honest, plain-text cold emails for a small US agency. No hype, no fake familiarity, "
    "no claims you can't back up, no emojis, under 120 words, one clear low-friction ask. Never invent facts "
    "about the recipient beyond the observations provided."
)


def _observations(p: Dict) -> list:
    sig = p.get("signals") or {}
    obs = []
    if sig.get("website_checked") and not sig.get("online_booking"):
        obs.append("your site doesn't seem to offer online booking, so most new business comes in by phone")
    if sig.get("website_checked") and not sig.get("chat_or_text_widget"):
        obs.append("there's no text-back or chat option on the site")
    if sig.get("closed_weekends"):
        obs.append("you're closed on weekends")
    if sig.get("closes_by_6pm"):
        obs.append("the office closes by 6pm on weekdays")
    if not p.get("website") and p.get("source") == "Google Places":
        obs.append("you don't list a website, so calls are likely your main channel")
    return obs[:2]


def template_draft(p: Dict, settings) -> Tuple[str, str]:
    v = VERTICALS.get(p.get("vertical"), {})
    name = p.get("name") or "there"
    obs = _observations(p)
    line = f"I noticed {obs[0]}." if obs else f"I work with {v.get('label', 'local business').lower()}s in {p.get('metro') or 'your area'}."
    subject = f"Missed calls at {name}"[:78]
    body = (
        f"Hi {name} team,\n\n"
        f"{line} In most {v.get('label', 'local business').lower()}s, {v.get('pain', 'unanswered calls turn into lost customers')}.\n\n"
        f"{settings.sender_company} sets up missed-call text-back: when a call isn't answered, the caller gets an instant text "
        f"so you can book them before they call someone else. Setup takes about a day and works with your current phone number.\n\n"
        f"Would a quick 10-minute call next week be worth it to see how many calls you might be missing?\n\n"
        f"{settings.sender_name}\n{settings.sender_company}" + (f"\n{settings.sender_site}" if settings.sender_site else "")
    )
    return subject, body + footer(settings)


def footer(settings) -> str:
    return (
        "\n\n--\n"
        f"{settings.sender_company}, {settings.sender_address}\n"
        "If you'd rather not hear from me, just reply \"no thanks\" and I won't email again."
    )


def _llm_endpoint(settings) -> Optional[Tuple[str, str, str]]:
    if settings.openrouter_api_key:
        return "https://openrouter.ai/api/v1/chat/completions", settings.openrouter_api_key, settings.draft_model or "openai/gpt-4o-mini"
    if settings.xai_api_key:
        return "https://api.x.ai/v1/chat/completions", settings.xai_api_key, settings.draft_model or "grok-3-mini"
    return None


def llm_draft(p: Dict, settings) -> Optional[Tuple[str, str]]:
    ep = _llm_endpoint(settings)
    if not ep:
        return None
    url, key, model = ep
    v = VERTICALS.get(p.get("vertical"), {})
    prompt = (
        f"Business: {p.get('name')} ({v.get('label')}) in {p.get('city')}, {p.get('state')}.\n"
        f"Observations (only use these): {'; '.join(_observations(p)) or 'none'}.\n"
        f"Industry pain: {v.get('pain')}.\n"
        f"Offer: {settings.sender_company} sets up missed-call text-back and call capture so unanswered calls get an instant text "
        f"and can still be booked. Works with their existing number.\n"
        f"Sender: {settings.sender_name}, {settings.sender_company}.\n"
        "Return exactly:\nSUBJECT: <subject under 60 chars>\nBODY:\n<email body, signed by the sender>"
    )
    try:
        r = httpx.post(url, headers={"Authorization": f"Bearer {key}"}, timeout=40, json={
            "model": model, "temperature": 0.5, "max_tokens": 400,
            "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
        })
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"]
    except Exception as exc:
        logger.warning("LLM draft failed (%s); using template", str(exc)[:120])
        return None
    m = re.search(r"SUBJECT:\s*(.+?)\s*\n+BODY:\s*\n?(.*)", text, re.S | re.I)
    if not m:
        return None
    return m.group(1).strip()[:78], m.group(2).strip() + footer(settings)


def draft_for(p: Dict, settings) -> Tuple[str, str, str]:
    res = llm_draft(p, settings)
    if res:
        return res[0], res[1], "llm"
    s, b = template_draft(p, settings)
    return s, b, "template"


def write_draft_file(out_dir: Path, p: Dict, subject: str, body: str, generator: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", (p.get("name") or "prospect").lower()).strip("-")[:50]
    path = out_dir / f"{p.get('grade', 'X')}-{slug}-{re.sub(r'[^A-Za-z0-9]', '', str(p.get('source_id')))[:16]}.md"
    path.write_text(
        "<!-- DRAFT ONLY - not sent. Review, find the right contact, and send manually. -->\n"
        f"To: (find decision-maker email - not scraped)\nSubject: {subject}\n"
        f"Prospect: {p.get('name')} | {p.get('phone')} | {p.get('website') or 'no website'} | {p.get('address')}\n"
        f"Grade: {p.get('grade')} ({p.get('score')}) - {'; '.join(p.get('reasons') or [])}\n"
        f"Generator: {generator}\n\n{body}\n",
        encoding="utf-8",
    )
    return path
