## 2026-02-03 - [Cross-Site Scripting (XSS) in Lead Intelligence Dashboard]
**Vulnerability:** API-provided lead data was injected directly into the DOM using `innerHTML` without sanitization. This allowed for script execution via lead names, emails, or sources.
**Learning:** Even when using template literals, data must be escaped if assigned to `innerHTML`. Event handlers like `onclick` are particularly tricky as they require additional care to avoid breaking with quotes or allowing attribute injection.
**Prevention:** Always use a helper like `escapeHTML` for dynamic content in `innerHTML`. For event handlers, prefer passing `this` and retrieving data from the DOM or using `dataset` to avoid complex string escaping in attributes.

## 2026-02-05 - [Remote Code Execution (RCE) via eval() in Workflow Engine]
**Vulnerability:** The `_calculate_task` in `pydantic_n8n_engine.py` used raw `eval()` on user-provided expressions, allowing arbitrary Python code execution.
**Learning:** AI-driven systems often need to evaluate expressions or conditions, which are high-risk areas for RCE. Memory/documentation might falsely claim a vulnerability is fixed; code must always be the source of truth.
**Prevention:** Use `ast.parse` and a strict whitelist of allowed nodes (e.g., constants and basic math operators) to safely evaluate expressions. Never use `eval()` or `exec()` on untrusted input without such validation.
