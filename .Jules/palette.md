# Palette's Journal - UX & Accessibility Learnings

## 2026-02-24 - Consistent Copy Feedback Pattern
**Learning:** Providing consistent, localized visual feedback for clipboard actions (changing button text to "Copied!" and color to success green) significantly improves user confidence in the interaction without requiring disruptive toast notifications.
**Action:** Use a unified `copyToClipboard` utility that captures and restores original button styles (color, border) to ensure visual consistency after the feedback state resets.
