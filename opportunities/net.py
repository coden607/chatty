"""Small, polite HTTP helper: identifying UA, timeouts, per-host spacing, retries."""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import httpx

logger = logging.getLogger("opportunities.http")

_last_hit: Dict[str, float] = {}
_lock = threading.Lock()


class FetchError(RuntimeError):
    pass


def _space(host: str, min_interval: float) -> None:
    with _lock:
        last = _last_hit.get(host, 0.0)
        wait = last + min_interval - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        _last_hit[host] = time.monotonic()


def request(
    method: str,
    url: str,
    *,
    user_agent: str,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    json: Any = None,
    timeout: float = 20.0,
    min_interval: float = 1.0,
    retries: int = 2,
) -> httpx.Response:
    host = urlparse(url).netloc
    hdrs = {"User-Agent": user_agent, "Accept": "application/json"}
    if headers:
        hdrs.update(headers)
    last_exc: Optional[Exception] = None
    for attempt in range(retries + 1):
        _space(host, min_interval)
        try:
            resp = httpx.request(method, url, params=params, headers=hdrs, json=json, timeout=timeout, follow_redirects=True)
        except httpx.HTTPError as exc:
            last_exc = exc
            logger.warning("HTTP error %s %s (attempt %d): %s", method, host, attempt + 1, exc)
            time.sleep(1.5 * (attempt + 1))
            continue
        if resp.status_code == 429 or resp.status_code >= 500:
            last_exc = FetchError(f"{resp.status_code} from {host}")
            retry_after = resp.headers.get("Retry-After")
            delay = float(retry_after) if retry_after and retry_after.isdigit() else 2.0 * (attempt + 1)
            logger.warning("%s from %s; backing off %.1fs", resp.status_code, host, min(delay, 30))
            time.sleep(min(delay, 30))
            continue
        return resp
    raise FetchError(f"{method} {url} failed: {last_exc}")


def get_json(url: str, *, user_agent: str, **kw: Any) -> Any:
    resp = request("GET", url, user_agent=user_agent, **kw)
    if resp.status_code >= 400:
        raise FetchError(f"GET {urlparse(url).netloc} -> {resp.status_code}")
    return resp.json()
