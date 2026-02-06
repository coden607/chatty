## 2026-02-03 - [Cross-Site Scripting (XSS) in Lead Intelligence Dashboard]
**Vulnerability:** API-provided lead data was injected directly into the DOM using `innerHTML` without sanitization. This allowed for script execution via lead names, emails, or sources.
**Learning:** Even when using template literals, data must be escaped if assigned to `innerHTML`. Event handlers like `onclick` are particularly tricky as they require additional care to avoid breaking with quotes or allowing attribute injection.
**Prevention:** Always use a helper like `escapeHTML` for dynamic content in `innerHTML`. For event handlers, prefer passing `this` and retrieving data from the DOM or using `dataset` to avoid complex string escaping in attributes.

## 2026-02-06 - [Admin Privilege Escalation via Mass Assignment in User Registration]
**Vulnerability:** The user registration endpoint allowed clients to specify their own role, including 'admin', by passing it in the JSON payload.
**Learning:** Never trust client-provided data for sensitive fields like roles or permissions. Rely on server-side defaults and explicit administrative actions for privilege escalation.
**Prevention:** Hardcode sensitive fields to safe defaults during public registration and implement a separate, protected mechanism for assigning elevated roles.

## 2026-02-06 - [Security Monitoring Thread Crash due to Deque Slice Assignment]
**Vulnerability:** The security monitoring thread crashed on its first iteration because it attempted to use slice assignment on a 'collections.deque' object, which is unsupported in Python.
**Learning:** Standard Python data structures have subtle behavioral differences. 'deque' is optimized for fast appends/pops but lacks list-like slice assignment capabilities.
**Prevention:** Use '.clear()' and '.extend()' for bulk updates to 'deque' objects. Always verify that background threads are resilient to runtime exceptions to prevent silent security failures.
