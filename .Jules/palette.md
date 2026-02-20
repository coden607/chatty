## 2026-01-31 - [Dashboard Accessibility & Interactivity]
**Learning:** Interactive dashboards in this repo often use simple HTML/JS without formal frameworks, making accessibility labels and ARIA roles critical for screen reader compatibility as they are easily missed. Additionally, adding simple utility features like "Copy to Clipboard" significantly improves user efficiency in data-heavy interfaces.
**Action:** Always check for `placeholder`-only inputs and modal containers that lack standard ARIA dialog roles. Implement visual feedback (e.g., "Copied!" state) for all clipboard interactions to ensure the user is aware of the successful action.

## 2026-02-05 - [Interactive Dashboard Polish]
**Learning:** For multi-panel dashboards, a delegated 'Enter' key listener targeting the panel's primary button significantly reduces friction for power users. Additionally, providing 'Refreshing...' state on the primary refresh button prevents redundant clicks and confirms the system is active.
**Action:** Implement delegated 'Enter' key handlers in complex command interfaces and always disable/label-swap async trigger buttons during network requests using a `finally` block for resilience.

## 2026-02-12 - [Robust Clipboard Feedback]
**Learning:** Simple clipboard feedback (label swap) can become stuck if the user clicks the button multiple times within the timeout window, as the 'original text' might be captured as the feedback state ('Copied!').
**Action:** Use a persistent `_originalText` property on the button element to store the label during the first click and ensure it is only cleared after the timeout reverts the text. This prevents state-sticking during rapid interactions.
