## 2026-02-03 - [Cross-Site Scripting (XSS) in Lead Intelligence Dashboard]
**Vulnerability:** API-provided lead data was injected directly into the DOM using `innerHTML` without sanitization. This allowed for script execution via lead names, emails, or sources.
**Learning:** Even when using template literals, data must be escaped if assigned to `innerHTML`. Event handlers like `onclick` are particularly tricky as they require additional care to avoid breaking with quotes or allowing attribute injection.
**Prevention:** Always use a helper like `escapeHTML` for dynamic content in `innerHTML`. For event handlers, prefer passing `this` and retrieving data from the DOM or using `dataset` to avoid complex string escaping in attributes.

## 2026-02-14 - [Privilege Escalation via Mass Assignment in User Registration]
**Vulnerability:** The user registration endpoint in `backend/server.py` accepted a `role` field from the client request and directly assigned it to the new user. This allowed any user to register as an 'admin'.
**Learning:** Marshmallow schemas must use `dump_only=True` for sensitive fields like `role` or `permissions` to ensure they are never accepted during deserialization (`load`). Additionally, application logic should explicitly enforce default roles during user creation as a defense-in-depth measure.
**Prevention:** Always audit registration and profile update endpoints for mass assignment vulnerabilities. Use schema-level restrictions and explicit property assignment in the backend to control sensitive attributes.
