# Palette's UX Journal

## 2025-05-15 - [Accessible Feedback and Data Representation]
**Learning:** In static HTML dashboards using `innerHTML` injection, ARIA roles like `progressbar` must be manually included in the template strings to ensure data remains accessible. Additionally, icon-only buttons (like modal close buttons using `&times;`) and async triggers require explicit `aria-label` and visual state changes (e.g., "Refreshing...") to provide a polished, accessible experience.
**Action:** Always include ARIA attributes in JS-generated HTML and use `finally` blocks to restore button states after async operations.
