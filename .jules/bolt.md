## 2026-01-31 - [Async LLM calls]
**Learning:** In an asyncio-based system, synchronous LLM API calls (using `requests`) block the entire event loop for seconds, delaying heartbeats and other concurrent tasks.
**Action:** Convert synchronous API calls to asynchronous using `asyncio.to_thread` or an async HTTP client to maintain system responsiveness.

## 2026-02-03 - [Optimize JSON storage with mtime-based caching]
**Learning:** For disk-based JSON storage, using `os.path.getmtime` to validate an in-memory cache provides a massive performance boost (~37x in this case) with minimal complexity and high reliability.
**Action:** Always check for redundant file I/O in frequently called data retrieval functions and implement mtime-based caching.

## 2026-02-12 - [Dashboard Request Aggregation & AI Caching]
**Learning:** Sequential dashboard polling of ~16 endpoints leads to high network overhead. Consolidating into a single batch endpoint using `asyncio.gather` reduced dashboard latency from ~600ms to ~6ms. Additionally, AI-generated weekly summaries require caching to prevent redundant LLM costs and latency.
**Action:** Consolidate component-based polling into aggregated API responses and apply short-lived (60s) TTL caching to expensive AI-generated dashboard metrics.
