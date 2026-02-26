## 2026-02-03 - [Cross-Site Scripting (XSS) in Lead Intelligence Dashboard]
**Vulnerability:** API-provided lead data was injected directly into the DOM using `innerHTML` without sanitization. This allowed for script execution via lead names, emails, or sources.
**Learning:** Even when using template literals, data must be escaped if assigned to `innerHTML`. Event handlers like `onclick` are particularly tricky as they require additional care to avoid breaking with quotes or allowing attribute injection.
**Prevention:** Always use a helper like `escapeHTML` for dynamic content in `innerHTML`. For event handlers, prefer passing `this` and retrieving data from the DOM or using `dataset` to avoid complex string escaping in attributes.

## 2026-02-26 - [Remote Code Execution (RCE) in Pydantic n8n Engine]
**Vulnerability:** The workflow engine used raw `eval()` to process mathematical expressions in the 'calculate' task, allowing for arbitrary Python code execution.
**Learning:** Even "simple" calculation features can be exploited if they use `eval()`. Untrusted input must never reach such functions without strict sandboxing.
**Prevention:** Use `ast.parse` with a strict whitelist of operators and constants to implement a safe evaluator. Avoid `eval()` entirely.
