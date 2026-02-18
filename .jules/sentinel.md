## 2026-02-03 - [Cross-Site Scripting (XSS) in Lead Intelligence Dashboard]
**Vulnerability:** API-provided lead data was injected directly into the DOM using `innerHTML` without sanitization. This allowed for script execution via lead names, emails, or sources.
**Learning:** Even when using template literals, data must be escaped if assigned to `innerHTML`. Event handlers like `onclick` are particularly tricky as they require additional care to avoid breaking with quotes or allowing attribute injection.
**Prevention:** Always use a helper like `escapeHTML` for dynamic content in `innerHTML`. For event handlers, prefer passing `this` and retrieving data from the DOM or using `dataset` to avoid complex string escaping in attributes.

## 2026-02-04 - [Remote Code Execution (RCE) in Pydantic n8n Engine]
**Vulnerability:** The engine used a raw `eval()` call on user-provided expressions in the `_calculate_task` method, allowing for arbitrary code execution.
**Learning:** Raw `eval()` should never be used on untrusted input. Even for simple mathematical expressions, a restricted evaluator using the `ast` module is necessary to whitelist only safe operations.
**Prevention:** Use a whitelist-based AST parser to allow only specific mathematical operators and constants. Avoid using `eval()` or `exec()` entirely in production code.
