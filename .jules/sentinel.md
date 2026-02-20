## 2026-02-03 - [Cross-Site Scripting (XSS) in Lead Intelligence Dashboard]
**Vulnerability:** API-provided lead data was injected directly into the DOM using `innerHTML` without sanitization. This allowed for script execution via lead names, emails, or sources.
**Learning:** Even when using template literals, data must be escaped if assigned to `innerHTML`. Event handlers like `onclick` are particularly tricky as they require additional care to avoid breaking with quotes or allowing attribute injection.
**Prevention:** Always use a helper like `escapeHTML` for dynamic content in `innerHTML`. For event handlers, prefer passing `this` and retrieving data from the DOM or using `dataset` to avoid complex string escaping in attributes.

## 2026-02-20 - [Remote Code Execution (RCE) in Pydantic n8n Engine]
**Vulnerability:** A raw `eval()` call was used in the `_calculate_task` method of `pydantic_n8n_engine.py` to evaluate user-provided mathematical expressions. This allowed for arbitrary code execution if an attacker could register a workflow with a malicious expression.
**Learning:** Using `eval()` on any external input, even if intended for simple math, is extremely dangerous in Python as it provides full access to the interpreter.
**Prevention:** Always use a restricted AST-based evaluator or `ast.literal_eval()` for parsing data. For mathematical expressions, implement a whitelist-based AST visitor that only allows specific safe operators and constants.
