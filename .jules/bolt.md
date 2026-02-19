## 2026-01-31 - [Async LLM calls]
**Learning:** In an asyncio-based system, synchronous LLM API calls (using `requests`) block the entire event loop for seconds, delaying heartbeats and other concurrent tasks.
**Action:** Convert synchronous API calls to asynchronous using `asyncio.to_thread` or an async HTTP client to maintain system responsiveness.

## 2026-02-03 - [Optimize JSON storage with mtime-based caching]
**Learning:** For disk-based JSON storage, using `os.path.getmtime` to validate an in-memory cache provides a massive performance boost (~37x in this case) with minimal complexity and high reliability.
**Action:** Always check for redundant file I/O in frequently called data retrieval functions and implement mtime-based caching.

## 2026-02-05 - [AI content caching for frequently polled endpoints]
**Learning:** Polled dashboard endpoints that trigger expensive AI generation can cause massive latency and cost if not cached. Shared in-memory caching with a lock-protected double-check pattern is highly effective.
**Action:** Implement time-based caching with `asyncio.Lock` for all AI-dependent endpoints to prevent redundant calls and thundering herd issues.
