## 2025-05-15 - [Consistency in Dashboard UX Patterns]
**Learning:** Even when UX patterns like async feedback (loading states) and ARIA attributes for progress bars are documented or used in parts of the app, they may be inconsistently applied in newer or less-touched areas like the lead dashboard.
**Action:** Always audit the primary dashboard buttons and data visualization elements (like score bars) for these standardized patterns during any UI-related task.

## 2025-05-15 - [Keyboard Accessibility for Modals]
**Learning:** Modals in this application's static HTML dashboards often lack keyboard listeners. Users expect the "Escape" key to close overlays.
**Action:** Implement a global 'keydown' listener for the 'Escape' key whenever a modal system is present in a dashboard.
