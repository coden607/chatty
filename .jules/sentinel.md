## 2026-02-03 - [Cross-Site Scripting (XSS) in Lead Intelligence Dashboard]
**Vulnerability:** API-provided lead data was injected directly into the DOM using `innerHTML` without sanitization. This allowed for script execution via lead names, emails, or sources.
**Learning:** Even when using template literals, data must be escaped if assigned to `innerHTML`. Event handlers like `onclick` are particularly tricky as they require additional care to avoid breaking with quotes or allowing attribute injection.
**Prevention:** Always use a helper like `escapeHTML` for dynamic content in `innerHTML`. For event handlers, prefer passing `this` and retrieving data from the DOM or using `dataset` to avoid complex string escaping in attributes.

## 2026-02-21 - [Remote Code Execution (RCE) in Workflow Engine]
**Vulnerability:** The `_calculate_task` method in `pydantic_n8n_engine.py` used the native `eval()` function on untrusted user-provided expressions, allowing for arbitrary Python code execution.
**Learning:** Even simple mathematical calculations can be a vector for RCE if not properly sandboxed. Native `eval()` should never be used on untrusted input. Furthermore, AST-based evaluators must be carefully hardened against Denial of Service (DoS) by restricting constant types and expensive operators like `Pow`.
**Prevention:** Always use a whitelist-based AST parser for dynamic expression evaluation. Restrict constants to numeric types only to prevent memory-based DoS via string repetition, and exclude operators like `Pow` that can lead to CPU exhaustion.
