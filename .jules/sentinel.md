# Sentinel Security Journal

## 2026-02-01 - XSS Prevention in Leads Dashboard
**Vulnerability:** Systemic Cross-Site Scripting (XSS) in `leads_dashboard.html`. The application fetched data from various API endpoints (leads, workflows, tasks, etc.) and injected it directly into the DOM using `innerHTML` without sanitization. Malicious data in fields like lead names or workflow titles could execute arbitrary JavaScript in the user's browser.
**Learning:** The dashboard followed a consistent pattern of using template literals and `innerHTML` for rendering API data. This made the vulnerability widespread but also allowed for a comprehensive fix by introducing a central `escapeHTML` utility. Additionally, passing string data directly into inline `onclick` handlers was identified as a secondary injection vector.
**Prevention:** Always escape user-provided or API-sourced data before injecting it into HTML. Use `textContent` instead of `innerHTML` when possible. For complex HTML structures, use a dedicated escaping utility. Avoid passing dynamic strings to inline event handlers; instead, use `data-*` attributes and access them via `dataset` within the handler function.
