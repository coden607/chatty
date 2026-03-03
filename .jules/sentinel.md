## 2026-02-03 - [Cross-Site Scripting (XSS) in Lead Intelligence Dashboard]
**Vulnerability:** API-provided lead data was injected directly into the DOM using `innerHTML` without sanitization. This allowed for script execution via lead names, emails, or sources.
**Learning:** Even when using template literals, data must be escaped if assigned to `innerHTML`. Event handlers like `onclick` are particularly tricky as they require additional care to avoid breaking with quotes or allowing attribute injection.
**Prevention:** Always use a helper like `escapeHTML` for dynamic content in `innerHTML`. For event handlers, prefer passing `this` and retrieving data from the DOM or using `dataset` to avoid complex string escaping in attributes.

## 2026-02-04 - [Remote Code Execution (RCE) in Workflow Engine]
**Vulnerability:** The workflow engine used the built-in `eval()` function to process mathematical expressions in the 'calculate' task. This allowed attackers to execute arbitrary Python code.
**Learning:** `eval()` is extremely dangerous as it has access to the full Python interpreter. Even with empty globals/locals, it can often be escaped (e.g., via `__import__` or `__subclasses__`).
**Prevention:** Never use `eval()` on untrusted input. Use a hardened evaluator based on `ast.parse()` and a strict whitelist of allowed operators and constants. Explicitly exclude dangerous operators like `**` (Pow) to prevent DoS.
