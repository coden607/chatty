## 2026-01-31 - [Async LLM calls]
**Learning:** In an asyncio-based system, synchronous LLM API calls (using `requests`) block the entire event loop for seconds, delaying heartbeats and other concurrent tasks.
**Action:** Convert synchronous API calls to asynchronous using `asyncio.to_thread` or an async HTTP client to maintain system responsiveness.

## 2026-02-03 - [Optimize JSON storage with mtime-based caching]
**Learning:** For disk-based JSON storage, using `os.path.getmtime` to validate an in-memory cache provides a massive performance boost (~37x in this case) with minimal complexity and high reliability.
**Action:** Always check for redundant file I/O in frequently called data retrieval functions and implement mtime-based caching.

## 2026-02-10 - [Batch API Consolidation for Dashboards]
**Learning:** Consolidating multiple sequential API calls into a single batched endpoint reduces network overhead, bypasses browser connection limits, and eliminates the "waterfall" effect, improving dashboard latency from ~600ms to ~6ms.
**Action:** For data-heavy UIs, implement an aggregated `/all` or `/batch` endpoint that utilizes `asyncio.gather` on the backend.
