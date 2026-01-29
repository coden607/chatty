# AGENTS.md

Project: CHATTY complete automation system (Python + FastAPI + async engines).

## Repo map (high-signal)
- `START_COMPLETE_AUTOMATION.py`: primary entrypoint for the full automation loop.
- `AUTOMATED_REVENUE_ENGINE.py`: revenue engine implementation.
- `AUTOMATED_CUSTOMER_ACQUISITION.py`: acquisition engine implementation.
- `SELF_IMPROVING_AGENTS.py`: AI agent orchestration.
- `AUTOMATION_API_SERVER.py`: FastAPI control/monitoring API (run via Uvicorn).
- `launch_chatty.sh`: one-click launcher for the full system.
- `logs/`: runtime logs (notably `logs/complete_automation.log`).
- `chroma_db/`: local vector store data.
- `generated_content/`: content outputs and artifacts.
- `templates/`, `backend/`: supporting UI/API assets.

## Agent rules (project-specific)
- Prefer `./python3` for running scripts to match the repo-bundled Python binary.
- Avoid invoking live integrations (social, payment, email, ads) unless explicitly requested; mock or stub in tests.
- Do not delete or alter `logs/`, `chroma_db/`, or `generated_content/` unless the user asks.
- Keep logging format consistent with existing files (timestamped, emoji markers are expected).
- Keep edits ASCII-only unless the target file already uses Unicode (many runtime logs do).

## Common workflows
### Secrets workflow (local secure file)
- Store secrets outside the repo (recommended path: `~/.config/chatty/secrets.env`).
- Set `CHATTY_SECRETS_FILE` to that path or rely on the default if it exists.
- Use `.env.example` for sharing config structure without secrets.

### Action center (history + prompts)
```
./python3 ACTION_CENTER.py
```
Outputs:
- `generated_content/earnings_status.md` (current snapshot)
- `generated_content/action_feed.md` (current actions + recent history)
- `generated_content/action_history.jsonl` (full history log)
- `generated_content/action_requests.json` (queued actions)

### Run full automation loop
```
./python3 START_COMPLETE_AUTOMATION.py
```
Or use the launcher:
```
./launch_chatty.sh
```

### Run API server
```
./python3 -m uvicorn AUTOMATION_API_SERVER:app --host 0.0.0.0 --port 8000
```

### Run tests
```
./python3 -m pytest
```

## Investor workflows
### Investor data room refresh (weekly)
- Metrics snapshot: MRR, CAC, LTV, active customers, churn, runway.
- Product updates: shipping log with measurable outcomes.
- Risk register: top 3 risks with mitigation updates.
- Shareable artifacts: 1-page brief, deck PDF, demo video link.

### Outreach pipeline (daily)
- Target list: 10 new investors matching stage/vertical.
- Personalization: 2-sentence thesis + traction proof.
- Touch cadence: Day 0 intro, Day 3 follow-up, Day 7 value update.
- CRM logging: track status, last touch, next action date.

### Fundraising narrative loop (biweekly)
- Update pitch with new traction and customer proof.
- Validate assumptions with 3 customer interviews.
- Rehearse demo flow and objection handling.

### Investor update automation (system)
- Weekly update written to `generated_content/investor/weekly_update_YYYYMMDD.md`.
- Narrative refresh written to `generated_content/investor/narrative_update_YYYYMMDD.md`.
- Outreach cadence logged to `generated_content/investor/outreach_log.csv`.
- Metrics snapshot saved to `generated_content/investor/metrics_snapshot.json`.

## Development guidelines
- Favor small, localized edits; this repo has large single-file systems.
- If adding new modules, wire them into `START_COMPLETE_AUTOMATION.py` and update system status reporting.
- If editing async loops, ensure graceful shutdown (`stop()` paths) remains intact.
- When touching API schemas, update the corresponding status models in `AUTOMATION_API_SERVER.py`.
