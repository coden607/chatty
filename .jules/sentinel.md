## 2026-02-03 - [Cross-Site Scripting (XSS) in Lead Intelligence Dashboard]
**Vulnerability:** API-provided lead data was injected directly into the DOM using `innerHTML` without sanitization. This allowed for script execution via lead names, emails, or sources.
**Learning:** Even when using template literals, data must be escaped if assigned to `innerHTML`. Event handlers like `onclick` are particularly tricky as they require additional care to avoid breaking with quotes or allowing attribute injection.
**Prevention:** Always use a helper like `escapeHTML` for dynamic content in `innerHTML`. For event handlers, prefer passing `this` and retrieving data from the DOM or using `dataset` to avoid complex string escaping in attributes.

## 2026-02-07 - [Privilege Escalation via Mass Assignment in User Registration]
**Vulnerability:** The registration endpoint allowed users to specify their `role` in the request payload. A malicious user could register as an `admin` by including `"role": "admin"` in the JSON request.
**Learning:** Schemas used for data validation (like Marshmallow) must be restricted to only allow user-editable fields. Sensitive fields like roles or permissions should be explicitly set by the backend logic and excluded from the public-facing schema.
**Prevention:** Always use separate schemas for internal and external data representation, or strictly whitelist allowed fields. Explicitly override sensitive fields in the business logic before saving to the database.
