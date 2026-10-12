# Feature: Opportunity Finder (coding jobs + Cortese Digital prospects)

_Plan per `piv-plan-implementation`. Approved by Stephen 2026-10-10 with the defaults in "Decisions"._

## User stories
- As Stephen, I want a daily, ranked digest of US-remote Python / TypeScript / AI-automation jobs and contracts, so I can apply quickly.
- As Cortese Digital, I want a nationwide, scored (A/B/C) list of phone-dependent businesses (dental, med spa, home services, law firms, auto repair) plus reviewable first-touch email drafts, so I can run compliant outreach for missed-call recovery.

## Feature metadata
- **Type:** New capability, plus startup clean-up.
- **Complexity:** Medium-High.
- **Systems:** `START_COMPLETE_AUTOMATION.py`, `AUTOMATION_API_SERVER.py`, the new `opportunities/` package, `leads_dashboard.html`.

## Decisions (approved defaults)
1. Job targeting: Python, TypeScript, AI automation; contract or full-time; US-remote (US or worldwide-remote). Configurable via env.
2. Prospects: all five verticals across the top 100 US metros (by population). Google Places spend capped at **$50/month** (`OPP_PLACES_MONTHLY_BUDGET_USD`), enforced with a persisted monthly usage counter.
3. Delivery:
   - A daily digest goes to Stephen only (`OPP_DIGEST_TO`), via Resend. Without a key it is written to a file.
   - Prospect emails are **drafts only**. There is no send path for prospects in code.
   - No automated calls or texts.
4. Legacy NarcoGuard, YouTube and X loops stay in the codebase but are **off by default** (feature flags).
5. New work lives in an isolated `opportunities/` package with its own unit tests. The legacy single-file engines are left alone.

## Out of scope
- Rewriting git history or the legacy engines.
- Fixing `backend/server.py`'s pre-existing circular import (it is not on the opportunity path).
- Upwork (needs an approved API app).
- LinkedIn/Indeed scraping (ToS).
- Yelp (no free tier).
- Changing the default branch or archiving repos.

## Step 1: clean startup
- `chatty_paths.py` (CHATTY_HOME). Replace `/home/coden809/...` literals in code and scripts.
- `SELF_IMPROVING_AGENTS.py`: when no LLM is configured, disable the agents instead of letting CrewAI demand `OPENAI_API_KEY`.
- `START_COMPLETE_AUTOMATION.py`: `sys.exit(1)` when init fails. Feature flags via `chatty_flags.py`. Register the `opportunity_finder` task.
- `pytest.ini`: unit test paths plus `asyncio_mode=auto`. Fix the TokenspinBridge test, stale acquisition tests, and the `sys.exit` in `test_nvidia_real.py`.
- Make `backend/requirements.txt` compatible with the root requirements (single venv).
- Replace the leaked `nvapi-` key in `API_KEYS_GUIDE.md` with a placeholder. **The key must still be rotated: history is not rewritten.**

## Step 2: job finder (`opportunities/jobs`)
- **Sources:**
  - Remotive (keyless; 24h-delayed; attribution + link back)
  - RemoteOK (keyless; followed link + "Remote OK" credit)
  - Himalayas (keyless)
  - HN "Who is hiring" (Algolia API, keyless)
  - Greenhouse / Lever / Ashby public boards (keyless; curated company list)
  - Adzuna (`ADZUNA_APP_ID`/`ADZUNA_APP_KEY`)
  - USAJOBS (`USAJOBS_API_KEY` + `USAJOBS_EMAIL`)
- Every source is an isolated adapter returning normalized `Job`. A missing key means skip with a clear log line; a network error means log and continue.
- Pipeline: dedupe (url, then company + title), US-remote eligibility filter, score 0–100 with reasons, SQLite store (`OPP_DB_PATH`).
- Surfaces: API `/api/opportunities/*`, dashboard tab `/opportunities`, daily digest (text + HTML, source credited on every job).

## Step 3: Cortese prospect finder (`opportunities/prospects`)
- **Google Places (New) Text Search** (`GOOGLE_PLACES_API_KEY`):
  - field-masked;
  - budget guard checked before every call;
  - metro × vertical rotation cursor so successive runs cover the country;
  - Places-derived fields purged after 30 days (only `place_id` is kept), per Maps ToS.
- **NPI Registry** (keyless): dental + med-spa-adjacent organizations by metro.
- **Website signals:** robots.txt respected, identifying user agent, 1 request per host. Detects online booking, chat/text widgets, and 24/7 or after-hours lines.
- **Score A/B/C** with reasons. CSV export.
- **Drafts:** an LLM (OpenRouter/xAI, if configured) writes them, with a deterministic template as fallback. Stored with status `draft` and written to `generated_content/opportunities/drafts/`. Includes CAN-SPAM placeholders (sender address, opt-out).

## Validation
- `pytest -q` (all unit tests offline, using fixtures; no live calls).
- `python -m opportunities jobs --dry-run`: live keyless sources must return real jobs.
- `python -m opportunities prospects --dry-run --metros 2`: NPI returns real businesses; Places is skipped without a key.
- `python -m uvicorn AUTOMATION_API_SERVER:app`: `/api/opportunities/jobs` returns 200.
- `npm run build` still passes.
