#!/usr/bin/env python3
"""
FREE_WEB_SCRAPER.py - Completely free web scraping using:
  1. trafilatura  - best-in-class text extraction, 100% free
  2. httpx        - async HTTP with retry/proxy support
  3. BeautifulSoup4 - structured data extraction
  4. playwright   - JavaScript-heavy sites (optional, free)
  5. DuckDuckGo   - free web search (no API key needed)

No paid APIs required. No Brave, no SerpAPI.
"""

import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus, urljoin, urlparse

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Dependency checks
# ─────────────────────────────────────────────────────────────

try:
    import httpx
    HTTPX_OK = True
except ImportError:
    HTTPX_OK = False
    logger.warning("httpx not installed: pip install httpx")

try:
    import trafilatura
    from trafilatura.settings import use_config
    TRAFILATURA_OK = True
except ImportError:
    TRAFILATURA_OK = False
    logger.warning("trafilatura not installed: pip install trafilatura")

try:
    from bs4 import BeautifulSoup
    BS4_OK = True
except ImportError:
    BS4_OK = False

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_OK = True
except ImportError:
    PLAYWRIGHT_OK = False

# ─────────────────────────────────────────────────────────────
# Data models
# ─────────────────────────────────────────────────────────────

@dataclass
class ScrapedPage:
    url: str
    title: str = ""
    text: str = ""
    html: str = ""
    links: List[str] = field(default_factory=list)
    images: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    scraped_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    success: bool = False
    error: Optional[str] = None
    strategy: str = "unknown"

@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str = ""

# ─────────────────────────────────────────────────────────────
# Rate limiter
# ─────────────────────────────────────────────────────────────

class RateLimiter:
    def __init__(self, rps: float = 1.0):
        self._rps = rps
        self._last: float = 0.0

    async def wait(self):
        elapsed = time.time() - self._last
        gap = 1.0 / self._rps
        if elapsed < gap:
            await asyncio.sleep(gap - elapsed)
        self._last = time.time()

# ─────────────────────────────────────────────────────────────
# Core scraper
# ─────────────────────────────────────────────────────────────

class FreeWebScraper:
    """
    Multi-strategy web scraper. Tries trafilatura first (fast, clean),
    falls back to playwright for JS-heavy sites.
    """

    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }

    def __init__(self, rps: float = 1.0, timeout: int = 30):
        self.rate_limiter = RateLimiter(rps)
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers=self.DEFAULT_HEADERS,
                timeout=self.timeout,
                follow_redirects=True,
                verify=False,   # some sites have cert issues
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    # ── Fetch raw HTML ─────────────────────────────────────────

    async def _fetch_html(self, url: str) -> Optional[str]:
        """Fetch HTML with httpx."""
        if not HTTPX_OK:
            return None
        await self.rate_limiter.wait()
        try:
            client = await self._get_client()
            r = await client.get(url)
            r.raise_for_status()
            return r.text
        except Exception as e:
            logger.debug(f"httpx fetch failed for {url}: {e}")
            return None

    async def _fetch_playwright(self, url: str) -> Optional[str]:
        """Fetch HTML using headless browser for JS-heavy pages."""
        if not PLAYWRIGHT_OK:
            return None
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url, wait_until="networkidle", timeout=self.timeout * 1000)
                html = await page.content()
                await browser.close()
                return html
        except Exception as e:
            logger.debug(f"Playwright failed for {url}: {e}")
            return None

    # ── Text extraction ────────────────────────────────────────

    def _extract_with_trafilatura(self, html: str, url: str) -> Optional[str]:
        if not TRAFILATURA_OK:
            return None
        try:
            config = use_config()
            config.set("DEFAULT", "EXTRACTION_TIMEOUT", "20")
            text = trafilatura.extract(
                html,
                url=url,
                include_links=False,
                include_images=False,
                favor_recall=True,
                config=config,
            )
            return text
        except Exception:
            return None

    def _extract_with_bs4(self, html: str, url: str) -> str:
        """Fallback: strip tags and return visible text."""
        if not BS4_OK:
            # Ultra-basic: strip HTML tags
            text = re.sub(r"<[^>]+>", " ", html)
            text = re.sub(r"\s+", " ", text).strip()
            return text[:10000]
        soup = BeautifulSoup(html, "html.parser")
        # Remove noise
        for tag in soup(["script", "style", "nav", "footer", "header",
                          "aside", "form", "meta", "noscript"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)[:10000]

    def _extract_metadata(self, html: str, url: str) -> Dict[str, Any]:
        if not BS4_OK:
            return {}
        soup = BeautifulSoup(html, "html.parser")
        meta = {}
        title_tag = soup.find("title")
        if title_tag:
            meta["title"] = title_tag.get_text(strip=True)
        for m in soup.find_all("meta"):
            name = m.get("name") or m.get("property", "")
            content = m.get("content", "")
            if name and content and name in {
                "description", "og:description", "og:title",
                "author", "keywords", "og:image",
            }:
                meta[name] = content
        return meta

    def _extract_links(self, html: str, base_url: str) -> List[str]:
        if not BS4_OK:
            return []
        soup = BeautifulSoup(html, "html.parser")
        links = []
        for a in soup.find_all("a", href=True)[:50]:
            href = a["href"]
            full = urljoin(base_url, href)
            if full.startswith("http"):
                links.append(full)
        return list(dict.fromkeys(links))  # deduplicate preserving order

    # ── Public scrape API ──────────────────────────────────────

    async def scrape(self, url: str, use_js: bool = False) -> ScrapedPage:
        """
        Scrape a URL and extract clean text.
        Tries trafilatura first, falls back to playwright if text is thin.
        """
        page = ScrapedPage(url=url)

        # Step 1: fetch HTML
        html = None
        if not use_js:
            html = await self._fetch_html(url)

        # If JS mode or thin content, try playwright
        if use_js or (html and len(html) < 1000):
            pw_html = await self._fetch_playwright(url)
            if pw_html:
                html = pw_html
                page.strategy = "playwright"
            elif html:
                page.strategy = "httpx"
        else:
            page.strategy = "httpx"

        if not html:
            page.error = "Could not fetch page with any strategy"
            return page

        page.html = html[:50000]  # cap stored HTML

        # Step 2: metadata
        page.metadata = self._extract_metadata(html, url)
        page.title    = page.metadata.get("title", "")
        page.links    = self._extract_links(html, url)

        # Step 3: text extraction (trafilatura > bs4)
        text = self._extract_with_trafilatura(html, url)
        if not text or len(text) < 100:
            text = self._extract_with_bs4(html, url)
            page.strategy += "+bs4_fallback"
        else:
            page.strategy += "+trafilatura"

        page.text = (text or "").strip()
        page.success = bool(page.text)
        if not page.success:
            page.error = "No text extracted"

        logger.info(f"🌐 Scraped {url}: {len(page.text)} chars via {page.strategy}")
        return page

    async def scrape_text(self, url: str) -> str:
        """Convenience: return just the extracted text."""
        page = await self.scrape(url)
        return page.text

    # ── DuckDuckGo search (no API key) ────────────────────────

    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """
        Search via DuckDuckGo HTML interface. No API key needed.
        """
        results: List[SearchResult] = []

        # Try duckduckgo_search library first (cleaner)
        # Try ddgs (new name) or duckduckgo_search (old name)
        for mod_name in ("ddgs", "duckduckgo_search"):
            try:
                if mod_name == "ddgs":
                    from ddgs import DDGS
                else:
                    from duckduckgo_search import DDGS
                with DDGS() as ddgs:
                    for r in ddgs.text(query, max_results=max_results):
                        results.append(SearchResult(
                            title=r.get("title", ""),
                            url=r.get("href", ""),
                            snippet=r.get("body", ""),
                        ))
                if results:
                    logger.info(f"🔍 DDG search: {len(results)} results for '{query}'")
                    return results
                break
            except ImportError:
                continue
            except Exception as e:
                logger.debug(f"{mod_name} search failed: {e}")
                break

        # Fallback: scrape DDG HTML
        try:
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            html = await self._fetch_html(url)
            if html and BS4_OK:
                soup = BeautifulSoup(html, "html.parser")
                for result_div in soup.find_all("div", class_="result__body")[:max_results]:
                    title_el  = result_div.find("a", class_="result__a")
                    snip_el   = result_div.find("a", class_="result__snippet")
                    if title_el:
                        results.append(SearchResult(
                            title=title_el.get_text(strip=True),
                            url=title_el.get("href", ""),
                            snippet=snip_el.get_text(strip=True) if snip_el else "",
                        ))
            logger.info(f"🔍 DDG HTML search: {len(results)} results")
        except Exception as e:
            logger.warning(f"DDG HTML search failed: {e}")

        return results

    async def search_and_scrape(
        self,
        query: str,
        max_results: int = 5,
        max_pages: int = 3,
    ) -> List[ScrapedPage]:
        """Search for query, then scrape the top results."""
        search_results = await self.search(query, max_results=max_results)
        scraped = []
        for sr in search_results[:max_pages]:
            if sr.url:
                page = await self.scrape(sr.url)
                if page.success:
                    scraped.append(page)
        return scraped

    # ── Batch scraping ─────────────────────────────────────────

    async def scrape_many(
        self,
        urls: List[str],
        concurrency: int = 3,
    ) -> List[ScrapedPage]:
        """Scrape multiple URLs with concurrency control."""
        sem = asyncio.Semaphore(concurrency)

        async def _scrape_one(url: str) -> ScrapedPage:
            async with sem:
                return await self.scrape(url)

        tasks = [_scrape_one(u) for u in urls]
        return await asyncio.gather(*tasks, return_exceptions=False)

    # ── Save results ───────────────────────────────────────────

    def save_results(self, pages: List[ScrapedPage], filename: str = "scraped_results"):
        out_dir = Path("generated_content")
        out_dir.mkdir(exist_ok=True)
        path = out_dir / f"{filename}.json"
        data = [
            {
                "url": p.url,
                "title": p.title,
                "text": p.text[:5000],
                "links": p.links[:20],
                "metadata": p.metadata,
                "success": p.success,
                "strategy": p.strategy,
                "scraped_at": p.scraped_at,
            }
            for p in pages
        ]
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"💾 Saved {len(pages)} scraped pages to {path}")
        return path


# ── Module singleton ───────────────────────────────────────────
_scraper: Optional[FreeWebScraper] = None

def get_scraper(rps: float = 1.0) -> FreeWebScraper:
    global _scraper
    if _scraper is None:
        _scraper = FreeWebScraper(rps=rps)
    return _scraper


# ── Quick test ─────────────────────────────────────────────────
if __name__ == "__main__":
    async def demo():
        scraper = FreeWebScraper()

        print("\n🔍 Testing DuckDuckGo search...")
        results = await scraper.search("Python web scraping best practices 2025", max_results=5)
        for r in results:
            print(f"  • {r.title[:60]} → {r.url[:80]}")

        if results:
            print(f"\n🌐 Scraping first result: {results[0].url}")
            page = await scraper.scrape(results[0].url)
            print(f"  Title: {page.title}")
            print(f"  Text ({len(page.text)} chars): {page.text[:500]}...")

        await scraper.close()

    asyncio.run(demo())
