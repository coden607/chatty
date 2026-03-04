## 2026-01-31 - [Dashboard Accessibility & Interactivity]
**Learning:** Interactive dashboards in this repo often use simple HTML/JS without formal frameworks, making accessibility labels and ARIA roles critical for screen reader compatibility as they are easily missed. Additionally, adding simple utility features like "Copy to Clipboard" significantly improves user efficiency in data-heavy interfaces.
**Action:** Always check for `placeholder`-only inputs and modal containers that lack standard ARIA dialog roles. Implement visual feedback (e.g., "Copied!" state) for all clipboard interactions to ensure the user is aware of the successful action.

## 2026-02-05 - [Interactive Dashboard Polish]
**Learning:** For multi-panel dashboards, a delegated 'Enter' key listener targeting the panel's primary button significantly reduces friction for power users. Additionally, providing 'Refreshing...' state on the primary refresh button prevents redundant clicks and confirms the system is active.
**Action:** Implement delegated 'Enter' key handlers in complex command interfaces and always disable/label-swap async trigger buttons during network requests using a `finally` block for resilience.

## 2026-03-04 - [Centralized UI Feedback & A11y in Vanilla JS Dashboards]
**Learning:** In vanilla JS dashboards lacking framework-level state management, centralizing asynchronous UI feedback (loading states/disabling) into a reusable helper prevents inconsistent interactivity and reduces code duplication. Descriptive ARIA labels on dynamic table actions are essential for providing context that is otherwise lost to screen readers in dense data views.
**Action:** Use a `uiAction`-style wrapper for all async triggers and always include entity-specific metadata in ARIA labels for repetitive row actions.
