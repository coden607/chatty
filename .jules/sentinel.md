## 2026-02-03 - [Cross-Site Scripting (XSS) in Lead Intelligence Dashboard]
**Vulnerability:** API-provided lead data was injected directly into the DOM using `innerHTML` without sanitization. This allowed for script execution via lead names, emails, or sources.
**Learning:** Even when using template literals, data must be escaped if assigned to `innerHTML`. Event handlers like `onclick` are particularly tricky as they require additional care to avoid breaking with quotes or allowing attribute injection.
**Prevention:** Always use a helper like `escapeHTML` for dynamic content in `innerHTML`. For event handlers, prefer passing `this` and retrieving data from the DOM or using `dataset` to avoid complex string escaping in attributes.

## 2026-02-04 - [Remote Code Execution (RCE) via insecure eval in Workflow Engine]
**Vulnerability:** The `_calculate_task` method in `pydantic_n8n_engine.py` used the built-in `eval()` function to process mathematical expressions from workflow metadata. This allowed arbitrary Python code execution.
**Learning:** `eval()` should never be used on untrusted or even partially trusted input. Even for "safe" calculations, an AST-based whitelist approach is necessary to restrict the execution environment.
**Prevention:** Use a custom AST evaluator (`ast.parse`) with a strict whitelist of operators and constants. Explicitly exclude potentially dangerous operators like `Pow` (**), which can lead to DoS, and any function calls.

## 2026-02-04 - [Privilege Escalation via Mass Assignment in User Registration]
**Vulnerability:** The `/api/auth/register` endpoint in `backend/server.py` allowed the `role` field to be passed in the request body, which was then used directly to create the `User` object, allowing anyone to register as an 'admin'.
**Learning:** Marshmallow schemas used for input validation must explicitly exclude sensitive fields from the loading process (using `dump_only=True`). Business logic should also explicitly set default roles rather than relying on request data.
**Prevention:** Mark administrative or sensitive fields as `dump_only=True` in Marshmallow schemas and hardcode default roles in the controller logic during object creation.
