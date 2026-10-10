"""Lightweight homepage check for missed-call signals.

Respects robots.txt, identifies itself, fetches one page per site, and never
submits forms or calls numbers.
"""

from __future__ import annotations

import logging
import re
from typing import Dict
from urllib import robotparser
from urllib.parse import urlparse

import httpx

logger = logging.getLogger("opportunities.prospects.website")

BOOKING = re.compile(
    r"book(ing)?[\s-]?(now|online|an appointment|appointment)|schedule[\s-]?(online|now|an appointment|appointment|service)|"
    r"request[\s-]an[\s-]appointment|zocdoc|nexhealth|localmed|lighthouse 360|solutionreach|weave\.com|calendly|acuityscheduling|"
    r"vagaro|boulevard|mindbody|square ?appointments|housecallpro|servicetitan|jobber|schedulicity|setmore|clio grow|lawmatics|"
    r"tekmetric|shopmonkey|mechanicnet|autoops|book\.?online",
    re.I,
)
CHAT_TEXT = re.compile(
    r"podium|birdeye|intercom|drift\.com|tawk\.to|livechat|tidio|zendesk|hubspot.*(chat|conversations)|olark|"
    r"smith\.ai|ruby\.com|ngage|apex chat|text us|text-us|sms us|webchat|chat with us|leadconnector|gohighlevel",
    re.I,
)
AFTER_HOURS = re.compile(r"24/7|24 hours|after[\s-]hours|answering service|emergency (service|line|calls)", re.I)


def _allowed(url: str, ua: str, timeout: float) -> bool:
    parts = urlparse(url)
    robots_url = f"{parts.scheme}://{parts.netloc}/robots.txt"
    rp = robotparser.RobotFileParser()
    try:
        r = httpx.get(robots_url, headers={"User-Agent": ua}, timeout=timeout, follow_redirects=True)
        if r.status_code >= 400:
            return True  # no robots.txt: allowed
        rp.parse(r.text.splitlines())
        return rp.can_fetch(ua, url)
    except httpx.HTTPError:
        return True


def check_site(url: str, settings, timeout: float = 10.0) -> Dict:
    if not url:
        return {"website_checked": False}
    if not url.startswith("http"):
        url = "https://" + url
    ua = settings.ua()
    if not _allowed(url, ua, timeout):
        return {"website_checked": False, "robots_disallowed": True}
    try:
        r = httpx.get(url, headers={"User-Agent": ua}, timeout=timeout, follow_redirects=True)
    except httpx.HTTPError as exc:
        return {"website_checked": False, "website_error": str(exc)[:120]}
    if r.status_code >= 400:
        return {"website_checked": False, "website_error": f"HTTP {r.status_code}"}
    html = r.text[:600_000]
    return analyze_html(html, base=str(r.url))


def analyze_html(html: str, base: str = "") -> Dict:
    return {
        "website_checked": True,
        "online_booking": bool(BOOKING.search(html)),
        "chat_or_text_widget": bool(CHAT_TEXT.search(html)),
        "after_hours_mention": bool(AFTER_HOURS.search(html)),
        "tel_links": len(re.findall(r'href=["\']tel:', html, re.I)),
        "final_url": base,
    }
