## 2026-02-03 - [Cross-Site Scripting (XSS) in Lead Intelligence Dashboard]
**Vulnerability:** API-provided lead data was injected directly into the DOM using `innerHTML` without sanitization. This allowed for script execution via lead names, emails, or sources.
**Learning:** Even when using template literals, data must be escaped if assigned to `innerHTML`. Event handlers like `onclick` are particularly tricky as they require additional care to avoid breaking with quotes or allowing attribute injection.
**Prevention:** Always use a helper like `escapeHTML` for dynamic content in `innerHTML`. For event handlers, prefer passing `this` and retrieving data from the DOM or using `dataset` to avoid complex string escaping in attributes.

## 2026-02-25 - [Remote Code Execution (RCE) in Workflow Engine]
**Vulnerability:** The `_calculate_task` in `pydantic_n8n_engine.py` used the raw `eval()` function on user-provided strings. This allowed arbitrary Python code execution.
**Learning:** Raw `eval()` is never safe for user input. Even "simple" expressions can be exploited via `__import__` or other built-ins. AST-based whitelisting is a robust alternative for restricted evaluation.
**Prevention:** Use `ast.parse` and a strict whitelist of allowed nodes (operators, constants) and types (numeric only) to evaluate expressions. Explicitly exclude dangerous operators like `Pow` (** ) to prevent DoS.

## 2026-02-25 - [Privilege Escalation via Mass Assignment]
**Vulnerability:** The user registration endpoint in `backend/server.py` allowed users to specify their own `role` (e.g., 'admin') in the JSON payload, which was then directly passed to the database model.
**Learning:** Mass assignment vulnerabilities occur when user input is mapped directly to internal models without filtering. Schemas must explicitly distinguish between input (load) and output (dump) fields for sensitive attributes.
**Prevention:** Mark sensitive fields like `role` as `dump_only=True` in Marshmallow schemas and hardcode default roles in registration logic to ensure the principle of least privilege.
