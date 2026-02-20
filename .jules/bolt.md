## 2026-01-31 - [Async LLM calls]
**Learning:** In an asyncio-based system, synchronous LLM API calls (using `requests`) block the entire event loop for seconds, delaying heartbeats and other concurrent tasks.
**Action:** Convert synchronous API calls to asynchronous using `asyncio.to_thread` or an async HTTP client to maintain system responsiveness.

## 2026-02-03 - [Optimize JSON storage with mtime-based caching]
**Learning:** For disk-based JSON storage, using `os.path.getmtime` to validate an in-memory cache provides a massive performance boost (~37x in this case) with minimal complexity and high reliability.
**Action:** Always check for redundant file I/O in frequently called data retrieval functions and implement mtime-based caching.

## 2026-02-20 - [Thundering herd prevention with asyncio.Lock]
**Learning:** When implementing an in-memory cache for an expensive async operation (like AI generation), simply checking the cache before the logic is not enough to prevent redundant calls under high concurrency.
**Action:** Wrap the entire cache-check and generation logic in an `asyncio.Lock` to ensure only one request triggers the expensive logic while others wait for the cached result.
