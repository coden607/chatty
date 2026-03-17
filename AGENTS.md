# AGENTS.md - CHATTY Complete Automation System

## Project Overview

**CHATTY** is a fully autonomous, self-improving AI automation system designed for complete business automation including revenue generation, customer acquisition, investor relations, and multi-agent orchestration.

**Core Philosophy**: Real data only, no simulations. Automatic failover between AI providers. Continuous self-improvement through learning systems.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CHATTY MASTER ORCHESTRATOR                         │
│                    (START_COMPLETE_AUTOMATION.py)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │  Revenue Engine │  │   Acquisition   │  │  Investor Work  │             │
│  │  (AUTOMATED_    │  │   Engine        │  │  Flows          │             │
│  │   REVENUE_)     │  │  (AUTOMATED_    │  │  (INVESTOR_)    │             │
│  │                 │  │   CUSTOMER_)    │  │                 │             │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘             │
│           │                    │                    │                       │
│  ┌────────▼────────┐  ┌────────▼────────┐  ┌────────▼────────┐             │
│  │  Stripe         │  │  Lead Gen       │  │  Data Room      │             │
│  │  SendGrid       │  │  Social Auto    │  │  Outreach       │             │
│  │  AI Content     │  │  SEO Auto       │  │  CRM            │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
├─────────────────────────────────────────────────────────────────────────────┤
│                        AI AGENT ORCHESTRATION LAYER                          │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐       │
│  │ Self-Improving│ │   Archon2    │ │ Agent Zero   │ │    BMAD      │       │
│  │   Agents     │ │Orchestration │ │   Fleet      │ │  Modeling    │       │
│  │ (SELF_)      │ │  (ARCHON2_)  │ │(AGENT_ZERO_) │ │  (BMAD_)     │       │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘       │
├─────────────────────────────────────────────────────────────────────────────┤
│                      INTELLIGENCE & CHUNKING LAYER                           │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐       │
│  │   OpenClaw   │ │   Docling    │ │  DeepCode    │ │ Multi-LLM    │       │
│  │   Learning   │ │   Chunker    │ │   Analysis   │ │   Router     │       │
│  │ (openclaw_)  │ │ (dockling_)  │ │  (enhanced_) │ │ (MODEL_)     │       │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘       │
├─────────────────────────────────────────────────────────────────────────────┤
│                         API & CONTROL LAYER                                  │
│                    (AUTOMATION_API_SERVER.py)                               │
│  REST API │ WebSocket │ Status Dashboard │ n8n Integration │ CLI Interface │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Components

### Core Entry Points

| File | Purpose | Entry Command |
|------|---------|---------------|
| `START_COMPLETE_AUTOMATION.py` | Main orchestrator - starts all systems | `./python3 START_COMPLETE_AUTOMATION.py` |
| `launch_chatty.sh` | One-click launcher script | `./launch_chatty.sh` |
| `AUTOMATION_API_SERVER.py` | FastAPI control & monitoring API | `./python3 -m uvicorn AUTOMATION_API_SERVER:app --host 0.0.0.0 --port 8000` |
| `ACTION_CENTER.py` | Action history and prompt management | `./python3 ACTION_CENTER.py` |

### Engine Components

| Engine | File | Description |
|--------|------|-------------|
| **Revenue Engine** | `AUTOMATED_REVENUE_ENGINE.py` | Stripe integration, AI content generation, pricing optimization |
| **Acquisition Engine** | `AUTOMATED_CUSTOMER_ACQUISITION.py` | Lead generation, social automation, SEO, viral growth |
| **Self-Improving Agents** | `SELF_IMPROVING_AGENTS.py` | LangChain/CrewAI agent orchestration with auto-improvement |
| **Investor Workflows** | `INVESTOR_WORKFLOWS.py` | Fundraising automation, data room, outreach tracking |

### Advanced Intelligence Systems

| System | File | Purpose |
|--------|------|---------|
| **OpenClaw** | `openclaw_integration.py` | Autonomous learning, file chunking, context management |
| **OpenClaw Enhanced** | `openclaw_enhanced_integration.py` | Extended OpenClaw with multi-LLM orchestration |
| **Archon2** | `ARCHON2_ORCHESTRATION.py` | Hierarchical agent orchestration (4-level hierarchy) |
| **Agent Zero** | `AGENT_ZERO_FLEET.py` | Fleet-based agent coordination with zero-shot learning |
| **BMAD** | `BMAD_MODELING.py` | Behavioral Modeling for Agent Dynamics |
| **Enhanced BMAD** | `enhanced_bmad_agent.py` | AI-powered code analysis, security scanning, auto-fixes |
| **Docling Chunker** | `dockling_chunker.py` | Semantic file chunking with AST analysis |
| **Debugging System** | `AUTOMATED_DEBUGGING_SYSTEM.py` | Automated error detection, log analysis, auto-fixing |

### Multi-LLM & Model Failover

| Component | File | Description |
|-----------|------|-------------|
| **Model Router** | `CHATTY_MODEL_ROUTER.py` (NEW) | Unified LLM failover system - auto-hands off between providers |
| **AI Marketplace** | `ai_model_marketplace.py` | Model selection and routing based on task type |

**Failover Priority**:
1. xAI (Grok-3) - Primary brain
2. OpenRouter (Claude 3.5/GPT-4) - Secondary
3. Cohere Command-R - Tertiary
4. Local Ollama models - Fallback

### Unified AI Orchestration (NEW)

| Component | File | Description |
|-----------|------|-------------|
| **Unified Orchestrator** | `UNIFIED_AI_ORCHESTRATION.py` | Master orchestration integrating all AI frameworks |
| **Complete Integration** | `INTEGRATE_ALL_AI_SYSTEMS.py` | High-level API for all AI capabilities |

**Features**:
- **Intelligent Task Routing**: Automatically routes tasks to the optimal framework
- **Automatic LLM Failover**: Seamlessly switches between AI providers
- **Unified Interface**: Single API for all AI operations
- **Performance Tracking**: Monitors and optimizes framework selection
- **Demo Mode**: Works without API keys for testing

**Supported Frameworks**:
| Framework | Strengths | Best For |
|-----------|-----------|----------|
| **OpenClaw** | File chunking, self-repair, code analysis | Code generation, debugging |
| **LangChain** | Chains, tools, memory, flexibility | Research, flexible workflows |
| **CrewAI** | Multi-agent collaboration, role-playing | Content creation, complex workflows |
| **Pydantic AI** | Type-safe, structured outputs, validation | Data analysis, integrations |
| **Archon2** | Hierarchical orchestration, strategic planning | Strategic planning, coordination |

**Quick Start**:
```python
from UNIFIED_AI_ORCHESTRATION import execute_ai_task, quick_code_generation

# Execute any AI task
result = await execute_ai_task(
    name="Generate API",
    description="Create a REST API client",
    task_type="code_generation"
)

# Quick helpers
code = await quick_code_generation("Create a rate limiter", "python")
content = await quick_content_creation("AI in Business", "blog")
analysis = await quick_data_analysis(sales_data, "Find trends")
strategy = await quick_strategic_planning("Q4 growth plan")
```

### NVIDIA Build + Kimi K2.5 Real Data System (NEW)

| Component | File | Description |
|-----------|------|-------------|
| **Real Data Orchestrator** | `NVIDIA_REAL_AI_ORCHESTRATION.py` | **REAL DATA ONLY** - Uses NVIDIA Build API with Kimi K2.5 |
| **Setup Guide** | `SETUP_NVIDIA_KIMI.md` | Configuration guide for NVIDIA Build |
| **Test Script** | `test_nvidia_real.py` | Validates real API connection |

**⚠️ REAL DATA ONLY - NO SIMULATIONS**:
- ✅ Uses **NVIDIA Build API** (free tier available)
- ✅ **Kimi K2.5** - 1T parameter multimodal model
- ✅ **Real API calls** - No demo mode, no fallbacks
- ✅ **Fails fast** if API unavailable

**Setup**:
```bash
# 1. Get free API key at https://build.nvidia.com/moonshotai/kimi-k2.5
# 2. Set environment variable
export NVIDIA_API_KEY='nvapi-your-key-here'

# 3. Test
python3 test_nvidia_real.py
```

**Usage**:
```python
from NVIDIA_REAL_AI_ORCHESTRATION import (
    get_orchestrator, 
    UnifiedTask, 
    TaskType
)

orchestrator = await get_orchestrator()

# Test connection
status = await orchestrator.test_api_connection()
# Returns: {'status': 'connected', 'model': 'kimi-k2.5', 'latency_ms': 850}

# Execute with real data
result = await orchestrator.execute_task(
    UnifiedTask(
        name="Generate Code",
        description="Create a Python API client",
        task_type=TaskType.CODE_GENERATION
    )
)
# Returns actual API response with real generated code
```

**Kimi K2.5 Specifications**:
| Feature | Value |
|---------|-------|
| Parameters | 1 Trillion (32B active) |
| Context Window | 256,000 tokens |
| Architecture | MoE (Mixture of Experts) |
| Vision | Yes (images + video) |
| Tool Calling | Yes |
| Free Tier | 6 RPM, 3M tokens/day |

**API Endpoint**:
```
URL: https://integrate.api.nvidia.com/v1/chat/completions
Model: moonshotai/kimi-k2.5
```

### Data Integrations

| Integration | File | Real APIs Used |
|-------------|------|----------------|
| **Stripe** | `REAL_DATA_INTEGRATIONS.py` | Live balance, transactions, customers |
| **SendGrid** | `REAL_DATA_INTEGRATIONS.py` | Live email campaigns, analytics |
| **Twitter/X** | `TWITTER_AUTOMATION.py` | Live posting, engagement tracking |
| **Real Data Integrations** | `REAL_DATA_INTEGRATIONS.py` | Central hub for all real data connections |

### Learning Systems

| System | File | Description |
|--------|------|-------------|
| **YouTube Learner** | `REAL_YOUTUBE_LEARNER.py`, `COLE_MEDIN_LEARNER.py` | Extract insights from YouTube videos |
| **Transcriber Learner** | `REAL_TRANSCRIBER_LEARNER.py` | Transcribe and learn from audio/video |
| **Cole Medin Scanner** | `REAL_COLE_MEDIN_SCANNER.py` | Specialized scanner for Cole Medin content |
| **Implement Insights** | `IMPLEMENT_LEARNED_INSIGHTS.py` | Apply learned knowledge to codebase |

### n8n Workflow Integration

| Component | Location | Description |
|-----------|----------|-------------|
| **n8n Workflows** | `n8n_workflows/` | 1000+ workflow files for automation |
| **Autonomous API App** | `autonomous_api_app_development_workflow_n8n.json` | n8n workflow for API development |
| **Advanced DB Integration** | `advanced_database_integration_workflow_n8n.json` | n8n database workflows |

---

## Directory Structure

```
/home/coden809/Projects/chatty/
├── Core Automation
│   ├── START_COMPLETE_AUTOMATION.py      # Main entry point
│   ├── ENHANCED_START_COMPLETE_AUTOMATION.py  # Enhanced version
│   └── LAUNCH_AUTONOMOUS_SYSTEM.py       # Alternative launcher
│
├── Engines
│   ├── AUTOMATED_REVENUE_ENGINE.py       # Revenue generation
│   ├── AUTOMATED_CUSTOMER_ACQUISITION.py # Lead/customer acquisition
│   ├── SELF_IMPROVING_AGENTS.py          # AI agent orchestration
│   └── INVESTOR_WORKFLOWS.py             # Fundraising automation
│
├── Intelligence Systems
│   ├── UNIFIED_AI_ORCHESTRATION.py       # Master AI orchestration (NEW)
│   ├── INTEGRATE_ALL_AI_SYSTEMS.py       # Complete AI integration (NEW)
│   ├── openclaw_integration.py           # OpenClaw learning
│   ├── openclaw_enhanced_integration.py  # Enhanced OpenClaw
│   ├── ARCHON2_ORCHESTRATION.py          # Hierarchical orchestration
│   ├── AGENT_ZERO_FLEET.py               # Fleet management
│   ├── BMAD_MODELING.py                  # Behavioral modeling
│   ├── enhanced_bmad_agent.py            # AI code analysis
│   └── dockling_chunker.py               # Semantic chunking
│
├── API & Control
│   ├── AUTOMATION_API_SERVER.py          # FastAPI server
│   ├── CHATTY_UNIFIED_CHAT.py            # Chat interface
│   ├── CHATTY_CHAT.py                    # Alternative chat
│   └── backend_api.py                    # Backend API stub
│
├── Data & Integrations
│   ├── REAL_DATA_INTEGRATIONS.py         # Real data connections
│   ├── REAL_PAYMENT_PROCESSING.py        # Payment integrations
│   ├── REAL_SOCIAL_MEDIA_INTEGRATION.py  # Social media APIs
│   └── TRANSCRIPTAPI_INTEGRATION.py      # Transcription APIs
│
├── Learning Systems
│   ├── REAL_YOUTUBE_LEARNER.py
│   ├── COLE_MEDIN_LEARNER.py
│   ├── REAL_COLE_MEDIN_SCANNER.py
│   └── IMPLEMENT_LEARNED_INSIGHTS.py
│
├── Debugging & Quality
│   ├── AUTOMATED_DEBUGGING_SYSTEM.py     # Auto-debugging
│   ├── ROBUSTNESS_SYSTEM.py              # Error handling
│   └── FINAL_SYSTEM_VERIFICATION.py      # System validation
│
├── Utilities
│   ├── ACTION_CENTER.py                  # Action management
│   ├── CONTEXT_WINDOW_MANAGER.py         # Context optimization
│   ├── AGENT_MEMORY_SYSTEM.py            # Agent memory
│   └── transparency_log.py               # Audit logging
│
├── Generated Content
│   └── generated_content/                # Output artifacts
│       ├── earnings_status.md
│       ├── action_feed.md
│       ├── action_history.jsonl
│       └── investor/                     # Investor materials
│
├── n8n Workflows
│   └── n8n_workflows/                    # 1000+ workflow files
│
├── Config & Keys
│   ├── .env                              # Environment variables
│   ├── requirements.txt                  # Python dependencies
│   └── ~/.config/chatty/secrets.env      # Secure secrets (outside repo)
│
└── Logs & Data
    ├── logs/                             # Runtime logs
    ├── leads.json                        # Lead database
    └── chatty_memory.json                # System memory
```

---

## Agent Rules & Conventions

### Critical Rules

1. **Real Data Only**: Never use simulated/mock data unless explicitly in test mode
2. **Auto-Failover**: All LLM calls must use the Model Router for automatic provider failover
3. **No Hallucination**: All outputs must be grounded in actual system state
4. **Graceful Degradation**: Systems must continue operating with reduced functionality when APIs fail
5. **Audit Everything**: All actions are logged via `transparency_log.py`

### Code Style

- Use `./python3` for running scripts (matches repo-bundled Python binary)
- Prefer async/await for all I/O operations
- Use Pydantic models for all data structures
- Keep logging format: `timestamp - emoji - message`
- ASCII-only unless file already contains Unicode

### Environment Variables

```bash
# Required for full functionality
STRIPE_SECRET_KEY=sk_live_...
SENDGRID_API_KEY=SG...
XAI_API_KEY=xai-...
OPENROUTER_API_KEY=sk-or-v1-...
TWITTER_API_KEY=...

# Optional but recommended
CHATTY_SECRETS_FILE=~/.config/chatty/secrets.env
CHATTY_OFFLINE_MODE=false
CHATTY_SUPERVISOR_INTERVAL_SECONDS=15
```

---

## Workflows

### Starting the Full System

```bash
# Method 1: Direct Python
./python3 START_COMPLETE_AUTOMATION.py

# Method 2: Launcher script
./launch_chatty.sh

# Method 3: API server mode
./python3 -m uvicorn AUTOMATION_API_SERVER:app --host 0.0.0.0 --port 8000
```

### Action Center

```bash
./python3 ACTION_CENTER.py
```

Outputs:
- `generated_content/earnings_status.md` - Current snapshot
- `generated_content/action_feed.md` - Current actions + history
- `generated_content/action_history.jsonl` - Full history log
- `generated_content/action_requests.json` - Queued actions

### Model Failover Test

```bash
./python3 -c "from CHATTY_MODEL_ROUTER import router; print(router.health_check())"
```

### File Chunking with Docling

```python
from dockling_chunker import DocklingChunker

chunker = DocklingChunker()
chunks = chunker.dockling_chunk_file("path/to/file.py", strategy='auto')
```

### Agent Zero Fleet Deployment

```python
from AGENT_ZERO_FLEET import AgentZeroFleet

fleet = AgentZeroFleet()
result = await fleet.deploy_fleet({
    'agent_types': ['worker', 'coordinator', 'specialist'],
    'coordination_protocol': 'zero_shot'
})
```

---

## Integration Points

### Adding New AI Provider

1. Add provider config to `CHATTY_MODEL_ROUTER.py`
2. Implement provider class with `generate()` method
3. Add to failover chain in priority order
4. Update health check

### Adding New Revenue Stream

1. Create stream class in `AUTOMATED_REVENUE_ENGINE.py`
2. Implement `initialize()` and `run()` methods
3. Register in revenue streams dict
4. Add to transparency logging

### Adding New n8n Workflow

1. Create workflow JSON in `n8n_workflows/`
2. Register in `AUTOMATION_API_SERVER.py` workflows list
3. Add trigger endpoint if needed

---

## Guardrails & Safety

### Hallucination Prevention

1. **Source Verification**: All claims must reference actual data sources
2. **Confidence Scoring**: All AI outputs include confidence scores
3. **Human-in-the-Loop**: Critical actions require approval
4. **Ground Truth Checking**: Regular validation against real data

### API Safety

1. **Rate Limiting**: Built-in rate limit tracking per service
2. **Circuit Breakers**: Automatic disable on repeated failures
3. **Budget Controls**: Daily spend limits enforced
4. **Graceful Degradation**: Falls back to cached/local data

### Data Safety

1. **No PII in Logs**: Personal data is redacted
2. **Secrets Outside Repo**: All keys in `~/.config/chatty/`
3. **Audit Trail**: Complete action history in `transparency_log.py`

---

## Testing

```bash
# Run all tests
./python3 -m pytest

# Test specific component
./python3 -m pytest test_system_integration.py

# Test model router
./python3 CHATTY_MODEL_ROUTER.py --test

# Test real data integrations
./python3 REAL_DATA_INTEGRATIONS.py --test
```

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Model API errors | Check `CHATTY_MODEL_ROUTER.py` health, auto-failover should engage |
| Missing API keys | Run `./python3 auto_setup_api_keys.py` |
| Import errors | Ensure virtualenv activated: `source .venv/bin/activate` |
| Database locked | Remove `chatty.db` and restart |
| Port in use | Kill existing process: `pkill -f uvicorn` |

### Debug Mode

```bash
export DEBUG=true
export CHATTY_OFFLINE_MODE=true
./python3 START_COMPLETE_AUTOMATION.py
```

---

## Version History

- **v1.0**: Initial CHATTY system
- **v1.5**: Added OpenClaw integration
- **v2.0**: Added Archon2, Agent Zero, BMAD
- **v2.5**: Added Docling chunking, DeepCode analysis
- **v3.0**: Unified Model Router with auto-failover
- **v3.5**: Real data only mandate, guardrails implementation

---

## Contributing

1. All changes must pass `./python3 FINAL_SYSTEM_VERIFICATION.py`
2. Update AGENTS.md with any new components
3. Add transparency logging for all actions
4. Test model failover when adding AI features
5. Ensure real data paths (no mocks in production)

---

## License

Proprietary - All rights reserved.

---

## Contact

For issues or questions, check logs in `logs/` directory or run `./python3 check_automation_status.py`.
