# chatty

> **Auto marketing app** — autonomous AI marketing automation system.
> **Status: NEEDS-HOST** — server-side app; requires a host with Docker and ~20+ API keys. **Not** a static site / PWA; GitHub Pages does not apply.

## What this is

Chatty is a 24/7 autonomous AI marketing agent: it plans, generates, and publishes
marketing content, manages leads, routes work across AI providers, and exposes a
web dashboard. The codebase is a hybrid:

- **Python backend** — Flask + FastAPI + SQLAlchemy + ChromaDB (RAG memory), ~166 `.py` files.
- **Next.js 16 dashboard** — React 19 ops UI (`app/`, `package.json`, `leads_dashboard.html`).
- **Docker** — `Dockerfile` + `docker-compose.yml` (ports 8000/5000), health check on `/health`.
- **Deploy automation** — `.github/workflows/deploy.yml` (Oracle Cloud over SSH, or Railway with a token), plus `deploy-oracle-cloud.sh`, `deploy-railway.sh`, `deploy-render.sh`, `cloud-init.sh`.

## Branch map (read this first!)

| Branch | Content |
|--------|---------|
| `secure-key-setup` ← **default** | X (Twitter) credential setup only: `configure_x_keys.py`, `publish_approved_x.py`, agent-instruction files. No app code. |
| `main` | The full application (1,719 files, ~19 MB). This README describes `main`. |
| `feat/adaptive-orchestration-router` | `main` + `ADAPTIVE_ORCHESTRATION_ROUTER.py` (1,723 files). |
| `design/portable-orchestration-20261003` | Design doc only: `docs/superpowers/specs/2026-10-03-portable-orchestration-design.md`. |

## What exists (verified 2026-10-08, wave-2 factory audit)

- Orchestration: `CHATTY_MASTER_ORCHESTRATOR_v2.py`, `UNIFIED_AI_ORCHESTRATION.py`, `CHATTY_MODEL_ROUTER.py`, agent fleet/A2A protocol modules.
- Automation: `AUTOMATED_CUSTOMER_ACQUISITION.py`, `AUTOMATED_REVENUE_ENGINE.py`, `AUTOMATION_API_SERVER.py`, `AUTOMATE_EVERYTHING.sh` one-click setup.
- Dashboard/UI: Next.js app + `leads_dashboard.html`, API route `app/api/[...path]/route.ts`.
- Memory/RAG: ChromaDB-backed `CHATTY_RAG.py`, `AGENT_MEMORY_SYSTEM.py`.
- Docs: 39 markdown files, incl. `AUTOMATION_INDEX.md`, `DEPLOYMENT_SUMMARY.md`, `CHATTY_ASSISTANT_README.md`.
- Container + compose + CI deploy workflow.

## Promised vs. verified vs. missing

- **Claimed by docs** (`AUTOMATION_INDEX.md`, `DEPLOYMENT_SUMMARY.md`): "fully configured and running", "10/10 components operational", 13/24 API keys configured at some point.
  → **Not independently verified** in this audit. No live instance was found or exercised. Treat operational claims as aspirational until a deploy proves them.
- **Required to run**: 20+ env vars (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`, `XAI_API_KEY`, `NVIDIA_API_KEY`, `GOOGLE_API_KEY`, `HUGGINGFACE_TOKEN`, `COHERE_API_KEY`, `BRAVE_API_KEY`, `YOUTUBE_API_KEY`, `STRIPE_SECRET_KEY`, X/Twitter keys, `NARCOGUARD_URL`, `CHATTY_SECRETS_FILE`, …), a Python 3.11 runtime with native deps (ffmpeg, OpenCV libs, libpq), Postgres/ChromaDB storage.
- **Missing / not verified**: automated tests, CI beyond the deploy workflow, lockfile pinning for the full Python dep tree, production secret management.

## Deployment

- **Vercel: BLOCKED** — do not attempt (org policy). `.vercelignore` exists for historical reasons only.
- **Supported paths**: Docker on any VPS (`cloud-init.sh`), Oracle Cloud free tier (`deploy-oracle-cloud.sh`), Railway (`deploy-railway.sh`), Render (`deploy-render.sh`). All require secrets/env setup first.
- **GitHub Pages: N/A** — server-dependent app, nothing static to serve.

## Known issues found in audit

- Committed junk inflating the repo (~14 MB): `get-pip.py` (2.2 MB), `python3` and `python_launcher` binaries (5.9 MB each), `tmp/` artifacts (PDFs, scraped HTML). Recommend a cleanup wave — **not deleted yet** (pending reference check).
- Default branch `secure-key-setup` does not contain the app; newcomers land on the utility branch. Consider making `main` default or adding a pointer README to the default branch.
- Two utility scripts on the default branch publish to X from `~/.config/chatty/secrets.env`; they are manual, human-confirmed tools, not part of the running service.

## Quick sanity commands

```bash
git checkout main
python3 -m venv venv && pip install -r requirements.txt   # backend deps
python3 check_automation_status.py                        # what is configured
docker compose up --build                                 # full stack
```
