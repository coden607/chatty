## 2026-01-31 - [Async LLM calls]
**Learning:** In an asyncio-based system, synchronous LLM API calls (using `requests`) block the entire event loop for seconds, delaying heartbeats and other concurrent tasks.
**Action:** Convert synchronous API calls to asynchronous using `asyncio.to_thread` or an async HTTP client to maintain system responsiveness.

## 2026-02-03 - [Optimize JSON storage with mtime-based caching]
**Learning:** For disk-based JSON storage, using `os.path.getmtime` to validate an in-memory cache provides a massive performance boost (~37x in this case) with minimal complexity and high reliability.
**Action:** Always check for redundant file I/O in frequently called data retrieval functions and implement mtime-based caching.

## 2026-02-24 - [Cache expensive AI generation]
**Learning:** AI-powered API endpoints are a major performance bottleneck due to high latency and cost. Implementing an in-memory cache with an `asyncio.Lock` (using double-checked locking) provides a massive responsiveness boost (~125x) and protects against thundering herd problems.
**Action:** Identify endpoints polled by the UI and apply time-based caching with concurrency controls to redundant LLM calls.

## 2026-02-20 - [Thundering herd prevention with asyncio.Lock]
**Learning:** When implementing an in-memory cache for an expensive async operation (like AI generation), simply checking the cache before the logic is not enough to prevent redundant calls under high concurrency.
**Action:** Wrap the entire cache-check and generation logic in an `asyncio.Lock` to ensure only one request triggers the expensive logic while others wait for the cached result.

## 2026-02-21 - [In-memory caching for async LLM endpoints]
**Learning:** For expensive and frequently polled AI content generation endpoints, implementing a simple in-memory cache with an 'asyncio.Lock' prevents redundant LLM calls and avoids race conditions ('cache stampedes') while drastically improving response times for subsequent requests.
**Action:** Identify endpoints that poll slow external services and apply time-based in-memory caching with proper concurrency locks.

## 2025-05-14 - [Cache expensive AI summary calls]
**Learning:** Endpoints that trigger AI content generation (like weekly briefs) can take 5-30 seconds per request, creating a massive bottleneck and unnecessary cost if polled frequently by a dashboard.
**Action:** Implement in-memory caching with a reasonable TTL (e.g., 120s) and use an asyncio.Lock to prevent race conditions where multiple requests trigger simultaneous AI calls for the same data.
