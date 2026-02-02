## 2026-02-02 - [In-memory caching for JSON storage]
**Learning:** Implementing an in-memory cache with `mtime` validation in `leads_storage.py` provided a ~35x speedup for lead retrieval (from ~0.000387s to ~0.000011s per call). This significantly reduces disk I/O and JSON parsing overhead, which is critical given the frequent polling from the frontend.
**Action:** Always consider `mtime`-validated caching for file-based data structures that are read frequently but updated relatively infrequently. Ensure `global` declarations are at the top of functions to avoid `SyntaxError`.
