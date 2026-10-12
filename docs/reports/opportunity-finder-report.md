# Implementation Report: Opportunity Finder
**Plan**: `docs/plans/opportunity-finder.md`   **Branch**: `feat/opportunity-finder`   **Status**: COMPLETE

## Summary
CHATTY now starts cleanly on a fresh machine with no keys, and has a new `opportunities/` package with two finders:
- a nationwide **US-remote coding-job finder** (7 sources: 5 keyless, 2 keyed), with dedupe, scoring, storage, a dashboard tab and a daily digest to Stephen only;
- a **Cortese Digital prospect finder** (Google Places with a $50/month guard, plus the keyless NPI Registry), with website signals, A/B/C grading, CSV export and AI/template email **drafts that are never sent**.

## Tasks completed
**Step 1: clean startup**
- `chatty_paths.py` (CREATE). `/home/coden809` literals removed from 10 Python files and 3 shell scripts (UPDATE).
- `SELF_IMPROVING_AGENTS.py`: agents disable themselves when no LLM is configured, instead of CrewAI raising `OPENAI_API_KEY is required` (UPDATE).
- `START_COMPLETE_AUTOMATION.py`: `sys.exit(1)` when init fails; flags gate the NarcoGuard (investor/GoFundMe/viral), YouTube and X loops, all off by default; new `opportunity_finder` task (UPDATE).
- `chatty_flags.py` (CREATE).
- `pytest.ini` (CREATE).
- Test fixes (UPDATE): `test_adaptive_orchestration_router.py` (TokenspinBridge import), `test_system_integration.py` (stale tests replaced with a no-fabrication test), `test_nvidia_real.py` (skip instead of `sys.exit` under pytest).
- `backend/requirements.txt`: made compatible with the root requirements, so one venv works (UPDATE).
- `API_KEYS_GUIDE.md`: leaked `nvapi-` key replaced with a placeholder (UPDATE).

**Step 2: jobs**
- Sources: `opportunities/jobs/sources/{remotive,remoteok,himalayas,hn,ats,adzuna,usajobs}.py`.
- Pipeline: `jobs/scoring.py`, `jobs/finder.py`.
- Supporting modules: `store.py` (SQLite), `digest.py`, `api.py`, `dashboard.html`, `scheduler.py`, `__main__.py` (CLI), `readiness.py`.

**Step 3: prospects**
- Data: `opportunities/prospects/{metros,verticals}.py`.
- Sources and enrichment: `places.py`, `npi.py`, `website.py`.
- Grading and output: `scoring.py`, `drafts.py`, `export.py`, `finder.py`.

**Wiring and docs**
- `AUTOMATION_API_SERVER.py` includes the router (optional import). `leads_dashboard.html` gets an "Opportunities" button.
- `.env.example` (CREATE; un-ignored in `.gitignore`), README section, CLAUDE.md note.

## Tests added
- `tests/test_opportunities_jobs.py` (11)
- `tests/test_opportunities_prospects.py` (12)
- `tests/test_startup_flags.py` (5)
- Fixtures in `tests/fixtures/opportunities/`.

All tests run offline (sources are monkeypatched).

## Validation
- `pytest -q`: **68 passed**. Before: collection crashed with an INTERNALERROR from `test_nvidia_real.py`.
- Mutation check: flipping the X flag's default to on makes `test_legacy_loops_off_by_default` fail. The checker can fail.
- `ruff check --select E9,F` on new code: clean.
- `python -m opportunities jobs --keyless` (live): 3,335 raw → 3,018 unique → ~250 matched, from Remotive, Remote OK, Himalayas, HN, Greenhouse/Lever/Ashby. Adzuna/USAJOBS log `skipped: missing …`.
- `python -m opportunities prospects --metros 3` (live): NPI returned 300 organizations, 278 unique. Places logs `skipped: missing GOOGLE_PLACES_API_KEY`. CSV and drafts were written.
- `START_COMPLETE_AUTOMATION.py` with **no keys at all**: boots to "COMPLETE AUTOMATION SYSTEM RUNNING" and the opportunity loop fetches jobs. Zero YouTube/yt-dlp log spam (was hundreds of 429s).
- `uvicorn AUTOMATION_API_SERVER:app`: `/opportunities`, `/api/opportunities/{jobs,prospects,prospects.csv,drafts,status}` all return 200.
- `npm run build`: passes.

## Deviations (intentional)
- **`backend/server.py` still fails to boot** with a pre-existing circular import (`learning_system` imports models from `server` before they are defined). Its dependency conflict is fixed, but the import cycle is out of scope and not on the opportunity path.
- **NPI-only prospects grade C.** NPI has no website, hours or reviews, so there is nothing to score. A/B grades need Places data (`GOOGLE_PLACES_API_KEY`).
- **The dashboard tab is served by the FastAPI server** (`/opportunities`). The Next.js `/api/[...path]` in-memory routes were not extended.
- **The leaked NVIDIA key remains in git history** (no history rewrite, per instructions). **It must be rotated.**
