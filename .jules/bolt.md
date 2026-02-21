## 2026-01-31 - [Async LLM calls]
**Learning:** In an asyncio-based system, synchronous LLM API calls (using `requests`) block the entire event loop for seconds, delaying heartbeats and other concurrent tasks.
**Action:** Convert synchronous API calls to asynchronous using `asyncio.to_thread` or an async HTTP client to maintain system responsiveness.

## 2026-02-03 - [Optimize JSON storage with mtime-based caching]
**Learning:** For disk-based JSON storage, using `os.path.getmtime` to validate an in-memory cache provides a massive performance boost (~37x in this case) with minimal complexity and high reliability.
**Action:** Always check for redundant file I/O in frequently called data retrieval functions and implement mtime-based caching.
## 2026-02-21 - [In-memory caching for async LLM endpoints]
**Learning:** For expensive and frequently polled AI content generation endpoints, implementing a simple in-memory cache with an 'asyncio.Lock' prevents redundant LLM calls and avoids race conditions ('cache stampedes') while drastically improving response times for subsequent requests.
**Action:** Identify endpoints that poll slow external services and apply time-based in-memory caching with proper concurrency locks.
