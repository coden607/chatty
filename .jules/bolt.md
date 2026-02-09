## 2026-01-31 - [Async LLM calls]
**Learning:** In an asyncio-based system, synchronous LLM API calls (using `requests`) block the entire event loop for seconds, delaying heartbeats and other concurrent tasks.
**Action:** Convert synchronous API calls to asynchronous using `asyncio.to_thread` or an async HTTP client to maintain system responsiveness.

## 2026-02-03 - [Optimize JSON storage with mtime-based caching]
**Learning:** For disk-based JSON storage, using `os.path.getmtime` to validate an in-memory cache provides a massive performance boost (~37x in this case) with minimal complexity and high reliability.
**Action:** Always check for redundant file I/O in frequently called data retrieval functions and implement mtime-based caching.

## 2026-02-09 - [Dashboard API Consolidation]
**Learning:** Consolidating 16 sequential API calls into a single batch endpoint using `asyncio.gather` reduced dashboard latency by ~89% (from ~51ms to ~6ms) and eliminated frontend network congestion.
**Action:** Identify fragmented polling patterns in UIs and batch them into aggregated endpoints to minimize RTT and improve perceived performance.
