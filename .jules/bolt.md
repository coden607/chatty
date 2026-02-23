## 2026-01-31 - [Async LLM calls]
**Learning:** In an asyncio-based system, synchronous LLM API calls (using `requests`) block the entire event loop for seconds, delaying heartbeats and other concurrent tasks.
**Action:** Convert synchronous API calls to asynchronous using `asyncio.to_thread` or an async HTTP client to maintain system responsiveness.

## 2026-02-03 - [Optimize JSON storage with mtime-based caching]
**Learning:** For disk-based JSON storage, using `os.path.getmtime` to validate an in-memory cache provides a massive performance boost (~37x in this case) with minimal complexity and high reliability.
**Action:** Always check for redundant file I/O in frequently called data retrieval functions and implement mtime-based caching.

## 2026-02-04 - [Caching AI-powered endpoints]
**Learning:** AI generation endpoints (like `/api/weekly/brief`) are extremely expensive and slow. Implementing a simple in-memory cache with `asyncio.Lock` and a TTL (e.g., 120s) can improve performance by >100x for polled resources while significantly reducing API costs.
**Action:** Identify polled AI endpoints and implement thread-safe in-memory caching for frequently requested summaries.
