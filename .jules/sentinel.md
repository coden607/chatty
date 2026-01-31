## 2024-05-24 - [XSS in Dashboard via API Data]
**Vulnerability:** The admin dashboard (`leads_dashboard.html`) was vulnerable to Multiple Cross-Site Scripting (XSS) attacks because it directly injected data from API endpoints into the DOM using `innerHTML` without any sanitization or escaping.

**Learning:** Even internal management dashboards are high-risk targets for XSS when they display data submitted by anonymous users (e.g., leads from a landing page). Simple HTML escaping with `escapeHTML` is effective for most `innerHTML` sinks, but attributes like `onclick` require additional care, such as using `dataset` to pass data to event handlers safely.

**Prevention:** Always use `textContent` instead of `innerHTML` when possible. If `innerHTML` is necessary, use a robust escaping utility. Avoid string interpolation of user data into inline event handler attributes; use `dataset` or event delegation instead.
