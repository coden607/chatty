## 2026-02-03 - [Cross-Site Scripting (XSS) in Lead Intelligence Dashboard]
**Vulnerability:** API-provided lead data was injected directly into the DOM using `innerHTML` without sanitization. This allowed for script execution via lead names, emails, or sources.
**Learning:** Even when using template literals, data must be escaped if assigned to `innerHTML`. Event handlers like `onclick` are particularly tricky as they require additional care to avoid breaking with quotes or allowing attribute injection.
**Prevention:** Always use a helper like `escapeHTML` for dynamic content in `innerHTML`. For event handlers, prefer passing `this` and retrieving data from the DOM or using `dataset` to avoid complex string escaping in attributes.

## 2026-03-05 - [Privilege Escalation via Mass Assignment in User Registration]
**Vulnerability:** The registration endpoint in `backend/server.py` accepted the `role` field directly from user input via the `UserSchema` and applied it to the new user record, allowing attackers to create administrative accounts.
**Learning:** Even when using validation schemas like Marshmallow, security-critical fields must be explicitly marked as `dump_only` or excluded entirely from input schemas to prevent mass assignment (overposting) attacks.
**Prevention:** Always hardcode default roles in the backend logic during registration and ensure that sensitive fields in schemas are read-only for API consumers.
