## 2025-02-12 - [Critical RCE Fix in n8n Engine]
**Vulnerability:** The `_calculate_task` function in `pydantic_n8n_engine.py` was using a raw `eval()` on user-provided input, allowing for arbitrary code execution (RCE).
**Learning:** Even mathematical expression evaluators can be dangerous if they use `eval()`. Standard library `collections.deque` does not support slice assignment (`[:]`), which can cause silent failures or crashes in security monitoring loops if not handled with `.clear()` and `.extend()`.
**Prevention:** Always use a combination of input whitelisting (regex) and restricted execution environments (empty builtins) when using `eval()`. Use `statistics` instead of `numpy` for basic math to reduce external dependency risks and maintain environment stability.
