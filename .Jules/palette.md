## 2026-01-31 - [Dashboard Accessibility & Interactivity]
**Learning:** Interactive dashboards in this repo often use simple HTML/JS without formal frameworks, making accessibility labels and ARIA roles critical for screen reader compatibility as they are easily missed. Additionally, adding simple utility features like "Copy to Clipboard" significantly improves user efficiency in data-heavy interfaces.
**Action:** Always check for `placeholder`-only inputs and modal containers that lack standard ARIA dialog roles. Implement visual feedback (e.g., "Copied!" state) for all clipboard interactions to ensure the user is aware of the successful action.

## 2026-02-05 - [Interactive Dashboard Polish]
**Learning:** For multi-panel dashboards, a delegated 'Enter' key listener targeting the panel's primary button significantly reduces friction for power users. Additionally, providing 'Refreshing...' state on the primary refresh button prevents redundant clicks and confirms the system is active.
**Action:** Implement delegated 'Enter' key handlers in complex command interfaces and always disable/label-swap async trigger buttons during network requests using a `finally` block for resilience.

## 2026-02-12 - [Dashboard Loading Feedback]
**Learning:** For dashboards with multiple data-fetching operations, providing per-button loading states (disabling and label-swapping) is more intuitive than a global loading indicator. Using `Promise.all` for parallel sub-fetches ensures that the loading state accurately reflects the completion of all concurrent tasks, preventing "UI flickering" where a button re-enables before all data is actually present.
**Action:** Implement `Promise.all` for all aggregate "Sync" or "Refresh All" buttons and ensure the UI state (disabled/label) is managed in a `finally` block for resilience against fetch failures.
