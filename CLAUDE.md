# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Chatty is a multi-agent AI automation platform for business operations: revenue generation, customer acquisition, content creation, and investor workflows. Built with Python, FastAPI, Flask, and multiple AI/ML frameworks (Anthropic, OpenAI, LangChain, CrewAI, Pydantic AI).

## Commands

### Run the full automation system
```bash
python3 START_COMPLETE_AUTOMATION.py
# Or use the launcher:
./launch_chatty.sh
```

### Run the FastAPI control/monitoring API
```bash
python3 -m uvicorn AUTOMATION_API_SERVER:app --host 0.0.0.0 --port 8000
```

### Run the Flask backend
```bash
python3 backend/server.py
```

### Install dependencies
```bash
pip install -r requirements.txt          # Main system
pip install -r backend/requirements.txt  # Backend services
```

### Run tests
```bash
python3 -m pytest
python3 run_integration_tests.py         # Integration tests
```

### Check system status
```bash
python3 verify_system.py
python3 ACTION_CENTER.py                 # Generates status reports in generated_content/
```

## Architecture

### Entry Points
- **`START_COMPLETE_AUTOMATION.py`** - Primary orchestrator that coordinates all automation engines in an async event loop with graceful shutdown
- **`AUTOMATION_API_SERVER.py`** - FastAPI API for monitoring and controlling the system (port 8000)
- **`backend/server.py`** - Flask + SQLAlchemy backend with user management, agent lifecycle, task orchestration (port 8181 in Docker, default Flask port locally)

### Core Engines (wired into `START_COMPLETE_AUTOMATION.py`)
- `AUTOMATED_REVENUE_ENGINE.py` - Revenue generation (Stripe, grants)
- `AUTOMATED_CUSTOMER_ACQUISITION.py` - Lead generation and scoring
- `SELF_IMPROVING_AGENTS.py` - Multi-agent AI orchestration
- `INVESTOR_WORKFLOWS.py` - Investor tracking, outreach, data room
- `TWITTER_AUTOMATION.py` - Social media automation
- `VIRAL_GROWTH_ENGINE.py` - Content virality

### Specialized Agent Systems
- `chatty_conversational_interface.py` - Multi-agent chat interface
- `YOUTUBE_LEARNING_INTEGRATION.py` / `COLE_MEDIN_LEARNER.py` - Video transcript learning
- `SKILL_BASED_ARCHITECTURE.py` - Task-to-agent routing
- `ROBUSTNESS_SYSTEM.py` - Hallucination detection and validation
- `pydantic_n8n_engine.py` - N8N workflow generation

### Data Layer
- PostgreSQL (primary DB via SQLAlchemy ORM)
- Redis (caching, task queues via Celery)
- ChromaDB / FAISS (vector embeddings, stored in `chroma_db/`)
- JSON files for config and intermediate outputs (`leads.json`, `grant_catalog.json`)

### Key Directories
- `logs/` - Runtime logs (notably `logs/complete_automation.log`)
- `generated_content/` - Output artifacts (grant proposals, investor updates, SEO reports, viral content)
- `n8n_workflows/` - Auto-generated N8N workflow JSON files
- `backend/` - Flask server, agent factory, learning system, code executor, security, observability
- `templates/` - HTML templates (landing page)
- `pwa/` - Progressive Web App manifest and service worker

## Development Guidelines

- **Large single-file systems**: Favor small, localized edits. Most engines are self-contained in single large files.
- **New modules**: Wire them into `START_COMPLETE_AUTOMATION.py` and update system status reporting.
- **Async loops**: Preserve graceful shutdown (`stop()` paths) when editing async code.
- **API schemas**: When modifying API schemas, update corresponding status models in `AUTOMATION_API_SERVER.py`.
- **Avoid live integrations**: Do not invoke live integrations (social, payment, email, ads) unless explicitly requested; mock or stub in tests.
- **Logging format**: Keep consistent with existing files (timestamped, emoji markers are used).
- **Don't modify data dirs**: Do not delete or alter `logs/`, `chroma_db/`, or `generated_content/` unless asked.

## Secrets Management

Secrets are stored outside the repo at `~/.config/chatty/secrets.env` (set via `CHATTY_SECRETS_FILE` env var). Required API keys include: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `XAI_API_KEY`, `OPENROUTER_API_KEY`, `STRIPE_SECRET_KEY`, `SENDGRID_API_KEY`, `TWITTER_API_KEY`/`TWITTER_API_SECRET`. Run `python3 auto_setup_api_keys.py` for guided key setup.
