## 2026-02-03 - [Cross-Site Scripting (XSS) in Lead Intelligence Dashboard]
**Vulnerability:** API-provided lead data was injected directly into the DOM using `innerHTML` without sanitization. This allowed for script execution via lead names, emails, or sources.
**Learning:** Even when using template literals, data must be escaped if assigned to `innerHTML`. Event handlers like `onclick` are particularly tricky as they require additional care to avoid breaking with quotes or allowing attribute injection.
**Prevention:** Always use a helper like `escapeHTML` for dynamic content in `innerHTML`. For event handlers, prefer passing `this` and retrieving data from the DOM or using `dataset` to avoid complex string escaping in attributes.

## 2026-02-08 - [Wildcard CORS and Missing Security Headers in Automation API]
**Vulnerability:** The API server used a wildcard CORS policy (`allow_origins=["*"]`) and lacked basic security headers, making it susceptible to cross-origin attacks and clickjacking.
**Learning:** Automation and control APIs, often intended for local use, frequently overlook production-grade security defaults. Even if an API is "internal," permissive CORS allows any website visited by the user to interact with the local API if they are on the same machine/network.
**Prevention:** Always restrict CORS to specific trusted origins or use a robust regex. Implement essential security headers (CSP, X-Frame-Options, HSTS) as standard middleware from the start to provide defense-in-depth.
