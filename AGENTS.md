# Agent instructions
## Shared agent skills
Canonical skill library: https://github.com/coden607/skills

For every coding/agent session in this repository:
1. Treat the canonical skill library as the complete shared skill set; do not maintain a hand-picked subset here.
2. Before planning or editing, make the library available locally (reuse/sync an existing clone when possible) and inspect the skills relevant to the task.
3. Follow the selected skill's SKILL.md/instructions together with this repository's existing rules. Repository-specific safety/product rules win on conflict.
4. Choose skills by task; do not execute every skill blindly. Use orchestration/routing skills when they can select a smaller, cheaper, more appropriate workflow.
5. Keep the library reusable across Codex/ChatGPT, Claude Code, Gemini CLI, Kimi, Copilot, OpenClaw, Chatty, and other coding agents. Do not make project behavior depend on one model vendor.
6. Never copy secrets into prompts, skill files, commits, logs, or external services.
7. If the canonical library changes, prefer syncing it rather than creating divergent local copies.
