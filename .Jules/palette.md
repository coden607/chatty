## 2026-01-31 - [Dashboard Accessibility & Interactivity]
**Learning:** Interactive dashboards in this repo often use simple HTML/JS without formal frameworks, making accessibility labels and ARIA roles critical for screen reader compatibility as they are easily missed. Additionally, adding simple utility features like "Copy to Clipboard" significantly improves user efficiency in data-heavy interfaces.
**Action:** Always check for `placeholder`-only inputs and modal containers that lack standard ARIA dialog roles. Implement visual feedback (e.g., "Copied!" state) for all clipboard interactions to ensure the user is aware of the successful action.

## 2026-02-04 - [Dashboard UX Feedback & Accessibility]
**Learning:** In data-heavy static HTML dashboards, users need immediate visual feedback for long-running refresh operations to prevent duplicate actions. Furthermore, accessibility for dynamic elements (like progress bars) and keyboard shortcuts (like Escape to close modals) are often overlooked but significantly enhance the "pro" feel of the system.
**Action:** Ensure all "Refresh" buttons implement a disabled loading state. Always add `role="progressbar"` to score bars and implement global `keydown` listeners for modal navigation.
