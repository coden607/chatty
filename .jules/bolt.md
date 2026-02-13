## 2026-01-31 - [Async LLM calls]
**Learning:** In an asyncio-based system, synchronous LLM API calls (using `requests`) block the entire event loop for seconds, delaying heartbeats and other concurrent tasks.
**Action:** Convert synchronous API calls to asynchronous using `asyncio.to_thread` or an async HTTP client to maintain system responsiveness.

## 2026-02-03 - [Optimize JSON storage with mtime-based caching]
**Learning:** For disk-based JSON storage, using `os.path.getmtime` to validate an in-memory cache provides a massive performance boost (~37x in this case) with minimal complexity and high reliability.
**Action:** Always check for redundant file I/O in frequently called data retrieval functions and implement mtime-based caching.

## 2026-02-05 - [Batch API Consolidation]
**Learning:** Consolidating multiple sequential API calls into a single batch endpoint using `asyncio.gather` reduces network overhead and improves dashboard responsiveness by ~4x.
**Action:** Batch multiple related data-fetching calls into a single endpoint to minimize HTTP overhead and leverage concurrent backend processing.
