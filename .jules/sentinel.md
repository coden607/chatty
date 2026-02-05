## 2026-02-03 - [Cross-Site Scripting (XSS) in Lead Intelligence Dashboard]
**Vulnerability:** API-provided lead data was injected directly into the DOM using `innerHTML` without sanitization. This allowed for script execution via lead names, emails, or sources.
**Learning:** Even when using template literals, data must be escaped if assigned to `innerHTML`. Event handlers like `onclick` are particularly tricky as they require additional care to avoid breaking with quotes or allowing attribute injection.
**Prevention:** Always use a helper like `escapeHTML` for dynamic content in `innerHTML`. For event handlers, prefer passing `this` and retrieving data from the DOM or using `dataset` to avoid complex string escaping in attributes.

## 2026-02-04 - [Hardcoded Secrets and Unstable Encryption Keys]
**Vulnerability:** Hardcoded database credentials in `server.py` and a default encryption password in `security_enhancer.py`. Additionally, the encryption salt was randomly generated on every restart, causing data loss for persistent encrypted data.
**Learning:** Default values for secrets in code often end up in production. Using `os.urandom()` for salts is good for single-session keys but breaks persistence if not stored.
**Prevention:** Always use environment variables for secrets with no defaults in production code. For persistent encryption, ensure the salt is also persistent and unique per key.
