## 2026-02-03 - [Cross-Site Scripting (XSS) in Lead Intelligence Dashboard]
**Vulnerability:** API-provided lead data was injected directly into the DOM using `innerHTML` without sanitization. This allowed for script execution via lead names, emails, or sources.
**Learning:** Even when using template literals, data must be escaped if assigned to `innerHTML`. Event handlers like `onclick` are particularly tricky as they require additional care to avoid breaking with quotes or allowing attribute injection.
**Prevention:** Always use a helper like `escapeHTML` for dynamic content in `innerHTML`. For event handlers, prefer passing `this` and retrieving data from the DOM or using `dataset` to avoid complex string escaping in attributes.

## 2026-02-15 - [Remote Code Execution (RCE) in Workflow Engine]
**Vulnerability:** The `_calculate_task` in `pydantic_n8n_engine.py` used the raw `eval()` function on user-provided expressions. This allowed arbitrary Python code execution, including system commands.
**Learning:** `eval()` should never be used on untrusted input. Even for simple mathematical tasks, a sandboxed or AST-based evaluator is required to restrict the execution environment.
**Prevention:** Use an AST-based evaluator with a strict whitelist of operators and constants. Avoid `eval()` and `exec()` entirely in favor of specialized parsers for domain-specific expressions.
