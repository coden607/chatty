## 2026-02-03 - [Cross-Site Scripting (XSS) in Lead Intelligence Dashboard]
**Vulnerability:** API-provided lead data was injected directly into the DOM using `innerHTML` without sanitization. This allowed for script execution via lead names, emails, or sources.
**Learning:** Even when using template literals, data must be escaped if assigned to `innerHTML`. Event handlers like `onclick` are particularly tricky as they require additional care to avoid breaking with quotes or allowing attribute injection.
**Prevention:** Always use a helper like `escapeHTML` for dynamic content in `innerHTML`. For event handlers, prefer passing `this` and retrieving data from the DOM or using `dataset` to avoid complex string escaping in attributes.

## 2026-02-24 - [Remote Code Execution (RCE) in Workflow Engine]
**Vulnerability:** The workflow engine used raw `eval()` to process mathematical expressions in tasks, allowing for arbitrary code execution.
**Learning:** Even simple "utility" functions like calculators can be dangerous if they use `eval()` on user-controllable input. A pre-existing syntax error in the backend server also blocked security verification scripts.
**Prevention:** Use the `ast` module to implement a hardened `_safe_eval` method that whitelists only necessary operators and numeric constants. Always ensure core server modules are syntax-valid to allow security auditing tools to run.
