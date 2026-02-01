## 2025-02-01 - [Leads Storage Optimization]
**Learning:** Redundant disk I/O and JSON parsing in polling endpoints (like `/api/leads`) can be significantly reduced by implementing an in-memory cache validated against the file's `mtime`. This provides O(1) performance for the common case where the data hasn't changed, while still ensuring correctness in multi-process environments.
**Action:** Use `os.path.getmtime` to invalidate local caches for file-based storage systems to achieve dramatic speedups (e.g., 30x) with minimal complexity.
