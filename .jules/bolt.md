## 2026-01-31 - [Async LLM calls]
**Learning:** In an asyncio-based system, synchronous LLM API calls (using `requests`) block the entire event loop for seconds, delaying heartbeats and other concurrent tasks.
**Action:** Convert synchronous API calls to asynchronous using `asyncio.to_thread` or an async HTTP client to maintain system responsiveness.

## 2026-02-03 - [Optimize JSON storage with mtime-based caching]
**Learning:** For disk-based JSON storage, using `os.path.getmtime` to validate an in-memory cache provides a massive performance boost (~37x in this case) with minimal complexity and high reliability.
**Action:** Always check for redundant file I/O in frequently called data retrieval functions and implement mtime-based caching.

## 2026-02-04 - [Batch API requests and AI result caching]
**Learning:** Consolidated 16 separate dashboard polling requests into a single aggregated batch endpoint and implemented time-based caching for AI-generated summaries. This reduces dashboard load time from multiple seconds to milliseconds (when cached) and minimizes server overhead.
**Action:** Use batch endpoints for dashboards with many components and always cache expensive, non-real-time AI results.
