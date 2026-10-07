# chatty — branch note

**You are on `secure-key-setup`** (the default branch). This branch holds only two
manual utility scripts for the official X/Twitter account:

- `configure_x_keys.py` — interactively stores X API credentials in `~/.config/chatty/secrets.env` (mode 600, values hidden).
- `publish_approved_x.py` — publishes **one** pre-approved NarcoGuard awareness post to X after you type `PUBLISH` in a real terminal.

**The actual Chatty application lives on the `main` branch** (1,719 files: Python
backend + Next.js dashboard + Docker). See the full README there:
https://github.com/coden607/chatty/tree/main

- These scripts need: Python 3, `tweepy>=4.14,<5`, and the 5 X credentials.
- They are standalone tools — not part of the running Chatty service.
- Vercel is **blocked** (org policy); do not attempt deployments there.
