## 2026-01-31 - [Dashboard Accessibility & Interactivity]
**Learning:** Interactive dashboards in this repo often use simple HTML/JS without formal frameworks, making accessibility labels and ARIA roles critical for screen reader compatibility as they are easily missed. Additionally, adding simple utility features like "Copy to Clipboard" significantly improves user efficiency in data-heavy interfaces.
**Action:** Always check for `placeholder`-only inputs and modal containers that lack standard ARIA dialog roles. Implement visual feedback (e.g., "Copied!" state) for all clipboard interactions to ensure the user is aware of the successful action.

## 2026-02-05 - [Interactive Dashboard Polish]
**Learning:** For multi-panel dashboards, a delegated 'Enter' key listener targeting the panel's primary button significantly reduces friction for power users. Additionally, providing 'Refreshing...' state on the primary refresh button prevents redundant clicks and confirms the system is active.
**Action:** Implement delegated 'Enter' key handlers in complex command interfaces and always disable/label-swap async trigger buttons during network requests using a `finally` block for resilience.

## 2026-02-16 - [Consistent Utility & Layout Polish]
**Learning:** Repetitive UI patterns (like 'Refresh' buttons) should consistently provide visual feedback to prevent user uncertainty during async operations. Furthermore, CSS classes intended for multiple element types (like `.prompt-textarea`) must explicitly handle different heights for `input` vs `textarea` to prevent layout breakage in auto-generated or template-driven forms.
**Action:** Always wrap async button actions in a loading state handler and use element-specific CSS selectors to refine shared class behaviors.
