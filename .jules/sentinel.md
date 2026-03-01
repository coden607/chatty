## 2026-02-03 - [Cross-Site Scripting (XSS) in Lead Intelligence Dashboard]
**Vulnerability:** API-provided lead data was injected directly into the DOM using `innerHTML` without sanitization. This allowed for script execution via lead names, emails, or sources.
**Learning:** Even when using template literals, data must be escaped if assigned to `innerHTML`. Event handlers like `onclick` are particularly tricky as they require additional care to avoid breaking with quotes or allowing attribute injection.
**Prevention:** Always use a helper like `escapeHTML` for dynamic content in `innerHTML`. For event handlers, prefer passing `this` and retrieving data from the DOM or using `dataset` to avoid complex string escaping in attributes.

## 2026-02-04 - [Remote Code Execution (RCE) in Pydantic n8n Engine]
**Vulnerability:** The `_calculate_task` in `pydantic_n8n_engine.py` used `eval()` to process mathematical expressions from workflow tasks, allowing arbitrary Python code execution.
**Learning:** Even "internal" tools like calculation tasks must be hardened against malicious input, especially in autonomous systems where tasks might be generated or influenced by AI/external data.
**Prevention:** Never use `eval()` or `exec()` for user-provided or externally-influenced strings. Use a dedicated safe evaluation library or implement a strict AST-based parser that only allows a whitelist of safe nodes and operations.
