## 2026-02-03 - [Cross-Site Scripting (XSS) in Lead Intelligence Dashboard]
**Vulnerability:** API-provided lead data was injected directly into the DOM using `innerHTML` without sanitization. This allowed for script execution via lead names, emails, or sources.
**Learning:** Even when using template literals, data must be escaped if assigned to `innerHTML`. Event handlers like `onclick` are particularly tricky as they require additional care to avoid breaking with quotes or allowing attribute injection.
**Prevention:** Always use a helper like `escapeHTML` for dynamic content in `innerHTML`. For event handlers, prefer passing `this` and retrieving data from the DOM or using `dataset` to avoid complex string escaping in attributes.

## 2026-02-13 - [Remote Code Execution (RCE) in Pydantic AI n8n Engine]
**Vulnerability:** The `_calculate_task` function used `eval()` on unsanitized user input, allowing arbitrary Python code execution.
**Learning:** Even internal utility functions for "simple" tasks like calculations can become RCE vectors if they accept string expressions from potentially untrusted sources (like workflow definitions).
**Prevention:** Always use a multi-layered defense for `eval()`: first, validate the input against a strict whitelist (regex) of allowed characters; second, restrict the execution environment by clearing `__builtins__` and providing an empty or limited globals dictionary.
