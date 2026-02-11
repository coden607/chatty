## 2026-02-03 - [Cross-Site Scripting (XSS) in Lead Intelligence Dashboard]
**Vulnerability:** API-provided lead data was injected directly into the DOM using `innerHTML` without sanitization. This allowed for script execution via lead names, emails, or sources.
**Learning:** Even when using template literals, data must be escaped if assigned to `innerHTML`. Event handlers like `onclick` are particularly tricky as they require additional care to avoid breaking with quotes or allowing attribute injection.
**Prevention:** Always use a helper like `escapeHTML` for dynamic content in `innerHTML`. For event handlers, prefer passing `this` and retrieving data from the DOM or using `dataset` to avoid complex string escaping in attributes.

## 2026-02-11 - [Remote Code Execution (RCE) in Pydantic n8n Engine]
**Vulnerability:** The `_calculate_task` function in `pydantic_n8n_engine.py` used an unrestricted `eval()` on user-provided expressions, allowing for arbitrary Python code execution.
**Learning:** Even internal utility functions like "calculate" can be dangerous if they use `eval()` or `exec()` without strict input validation. Whitelisting allowed characters and restricting the execution environment (empty built-ins) are essential defense-in-depth measures.
**Prevention:** Always validate input against a strict whitelist (e.g., regex) before passing it to `eval()`. Use restricted execution environments by passing empty dictionaries for globals and locals, and disabling `__builtins__`.
