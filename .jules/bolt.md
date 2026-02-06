## 2026-01-31 - [Async LLM calls]
**Learning:** In an asyncio-based system, synchronous LLM API calls (using `requests`) block the entire event loop for seconds, delaying heartbeats and other concurrent tasks.
**Action:** Convert synchronous API calls to asynchronous using `asyncio.to_thread` or an async HTTP client to maintain system responsiveness.

## 2026-02-03 - [Optimize JSON storage with mtime-based caching]
**Learning:** For disk-based JSON storage, using `os.path.getmtime` to validate an in-memory cache provides a massive performance boost (~37x in this case) with minimal complexity and high reliability.
**Action:** Always check for redundant file I/O in frequently called data retrieval functions and implement mtime-based caching.

## 2026-02-04 - [Dashboard Batch API and AI Caching]
**Learning:** Sequential frontend API calls (even 16 small ones) create massive latency overhead due to network round-trips (~600ms total). Consolidating them into a single `/api/dashboard/all` endpoint using `asyncio.gather` reduced response time to ~6ms (100x improvement).
**Action:** Identify dashboards with multiple refresh timers and consolidate them into a single batch endpoint to minimize network overhead and server load.
