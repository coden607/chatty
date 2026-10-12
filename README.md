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
- **Missing / not verified**: broad automated test coverage (unit tests now cover `opportunities/` and startup hygiene), CI beyond the deploy workflow, lockfile pinning for the full Python dep tree, production secret management.

## Deployment

- **Vercel: BLOCKED** — do not attempt (org policy). `.vercelignore` exists for historical reasons only.
- **Supported paths**: Docker on any VPS (`cloud-init.sh`), Oracle Cloud free tier (`deploy-oracle-cloud.sh`), Railway (`deploy-railway.sh`), Render (`deploy-render.sh`). All require secrets/env setup first.
- **GitHub Pages: N/A** — server-dependent app, nothing static to serve.

## Known issues found in audit

- Committed junk inflating the repo (~14 MB): `get-pip.py` (2.2 MB), `python3` and `python_launcher` binaries (5.9 MB each), `tmp/` artifacts (PDFs, scraped HTML). Recommend a cleanup wave — **not deleted yet** (pending reference check).
- Default branch `secure-key-setup` does not contain the app; newcomers land on the utility branch. Consider making `main` default or adding a pointer README to the default branch.
- Two utility scripts on the default branch publish to X from `~/.config/chatty/secrets.env`; they are manual, human-confirmed tools, not part of the running service.

## Opportunity finder: coding jobs + Cortese Digital prospects

The `opportunities/` package finds (a) US-remote Python / TypeScript / AI-automation jobs and contracts for Stephen, and (b) phone-dependent US businesses for Cortese Digital's missed-call recovery offer. It runs on its own (CLI) or inside the orchestrator (`opportunity_finder` task: jobs daily, prospects weekly, digest daily). **Every source is optional.** A missing key skips that source with a clear log line.

| Area | Keyless (works out of the box) | Needs a key |
|---|---|---|
| Jobs | Remotive, Remote OK, Himalayas, HN "Who is hiring" (Algolia API), Greenhouse / Lever / Ashby public boards | Adzuna (`ADZUNA_APP_ID`, `ADZUNA_APP_KEY`), USAJOBS (`USAJOBS_API_KEY`, `USAJOBS_EMAIL`) |
| Prospects | NPI Registry (dental, dermatology/aesthetics orgs) | Google Places API (New) (`GOOGLE_PLACES_API_KEY`), budget-capped |
| Email drafts | Deterministic template | AI drafts with `OPENROUTER_API_KEY` or `XAI_API_KEY` |
| Daily digest | Saved to `generated_content/opportunities/digests/` | Emailed to `OPP_DIGEST_TO` **only** via `RESEND_API_KEY` + `OPP_DIGEST_FROM` |

```bash
python -m opportunities status                         # what's configured (no secrets shown)
python -m opportunities jobs --dry-run --keyless       # live keyless job search, prints top matches
python -m opportunities jobs                           # fetch + score + store
python -m opportunities prospects --metros 5           # NPI (+ Places if keyed), score A/B/C, CSV, drafts
python -m opportunities export --grade A               # CSV of stored prospects
python -m opportunities digest --preview               # see today's digest without sending
```

Dashboard tab: run `uvicorn AUTOMATION_API_SERVER:app` and open `/opportunities`. API: `/api/opportunities/{jobs,prospects,prospects.csv,drafts,status}`. The "Opportunities" button is also on `/dashboard`.

**How jobs are matched:** listings are deduplicated by company+title and URL, filtered to remote roles open to US-based workers, and scored 0-100. The score covers role fit, keyword and stack matches, remote/US eligibility, contract or full-time, salary floor (`OPP_MIN_SALARY_USD`), freshness, and deal-breakers such as clearance-required. Tune it with `OPP_*` variables (see `.env.example`).

**How prospects are graded:** businesses come from Google Places Text Search (verticals × top-100 metros, rotating cursor) and the NPI Registry. Each gets a homepage check (robots.txt respected, one page, identifying User-Agent) for online booking, chat/text-back widgets and after-hours lines, plus hours (closed weekends / closes by 6pm) and review count. The result is **A ≥ 65, B ≥ 40, C otherwise**. NPI-only records have no website or hours, so they stay at C until enriched.

**Guardrails (by design):**
- Google Places spend is capped at `OPP_PLACES_MONTHLY_BUDGET_USD` (default **$50/month**). Usage is counted before each call and persisted per month. Non-`place_id` Places content is purged after 30 days (Maps ToS).
- Prospect emails are **drafts only** (SQLite + `generated_content/opportunities/drafts/*.md`). No code path sends email to prospects. Recipient emails are not scraped or guessed. **No automated calls or texts.** Drafts include a CAN-SPAM opt-out and your postal address (`CORTESE_POSTAL_ADDRESS`).
- Job sources' terms are respected: Remotive/Remote OK/USAJOBS listings are credited and link back to the source, Remotive is called once per run (24h-delayed feed), and no LinkedIn/Indeed/Upwork scraping is done.

## Startup flags

Legacy loops are **off by default**: `CHATTY_ENABLE_NARCOGUARD` (investor/funding/viral), `CHATTY_ENABLE_YOUTUBE` (YouTube learners), `CHATTY_ENABLE_X` (X posting). `CHATTY_ENABLE_OPPORTUNITIES` defaults on. Paths resolve from `CHATTY_HOME` (default: the repo). The self-improving agents disable themselves when no LLM key is configured, and `START_COMPLETE_AUTOMATION.py` exits non-zero if initialization fails.

## Quick sanity commands

```bash
git checkout main
python3 -m venv venv && pip install -r requirements.txt -r backend/requirements.txt   # one venv for both
python3 -m pytest -q                                      # unit tests (offline)
python3 check_automation_status.py                        # what is configured
docker compose up --build                                 # full stack
```
