## 2026-02-03 - [Cross-Site Scripting (XSS) in Lead Intelligence Dashboard]
**Vulnerability:** API-provided lead data was injected directly into the DOM using `innerHTML` without sanitization. This allowed for script execution via lead names, emails, or sources.
**Learning:** Even when using template literals, data must be escaped if assigned to `innerHTML`. Event handlers like `onclick` are particularly tricky as they require additional care to avoid breaking with quotes or allowing attribute injection.
**Prevention:** Always use a helper like `escapeHTML` for dynamic content in `innerHTML`. For event handlers, prefer passing `this` and retrieving data from the DOM or using `dataset` to avoid complex string escaping in attributes.
## 2026-02-04 - [Remote Code Execution in Workflow Engine]
**Vulnerability:** The 'calculate' task in the Pydantic AI n8n engine used raw `eval()` on user-provided expressions, allowing arbitrary Python code execution.
**Learning:** Even for "simple math," `eval()` is never safe if the input is controlled by a user or an external system. The `ast` module provides a powerful way to implement a safe subset of Python for expressions.
**Prevention:** Use a whitelist-based AST parser for dynamic expression evaluation. Only allow specific nodes (Constant, BinOp, UnaryOp) and safe operators.

## 2026-02-04 - [Privilege Escalation via Mass Assignment]
**Vulnerability:** The user registration endpoint allowed the 'role' field to be set in the request body, enabling anyone to register as an admin.
**Learning:** Schema validation should not only check types but also enforce "dump-only" or "read-only" constraints on sensitive fields. Core logic should explicitly set sensitive defaults rather than relying on optional input fields.
**Prevention:** Mark sensitive fields like 'role' as `dump_only` in schemas and hardcode them during object creation in public endpoints.
