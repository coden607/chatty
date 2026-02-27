## 2026-02-03 - [Cross-Site Scripting (XSS) in Lead Intelligence Dashboard]
**Vulnerability:** API-provided lead data was injected directly into the DOM using `innerHTML` without sanitization. This allowed for script execution via lead names, emails, or sources.
**Learning:** Even when using template literals, data must be escaped if assigned to `innerHTML`. Event handlers like `onclick` are particularly tricky as they require additional care to avoid breaking with quotes or allowing attribute injection.
**Prevention:** Always use a helper like `escapeHTML` for dynamic content in `innerHTML`. For event handlers, prefer passing `this` and retrieving data from the DOM or using `dataset` to avoid complex string escaping in attributes.

## 2026-02-04 - [Remote Code Execution (RCE) in Workflow Engine]
**Vulnerability:** The `calculate` task in `pydantic_n8n_engine.py` used the built-in `eval()` function on unsanitized user-provided expressions, allowing arbitrary Python code execution.
**Learning:** `eval()` is extremely dangerous and should never be used on untrusted input. Even for simple mathematical expressions, a hardened parser is required.
**Prevention:** Use the `ast` (Abstract Syntax Tree) module to implement a secure evaluator that whitelists only specific nodes (e.g., constants and basic math operators) and explicitly excludes dangerous ones like `ast.Call` or `ast.Pow` (to prevent DoS). Ensure exceptions propagate correctly to maintain API error reporting standards.
