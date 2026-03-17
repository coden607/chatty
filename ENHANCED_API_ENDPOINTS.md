# CHATTY Enhanced API Endpoints

## Model Router
- `POST /api/v1/generate` - Generate content with auto-failover
- `GET /api/v1/models/health` - Get model health status
- `GET /api/v1/models/providers` - List available providers

## Unified Intelligence
- `POST /api/v1/intelligence/analyze` - Analyze code/content
- `POST /api/v1/intelligence/learn` - Learn from file
- `GET /api/v1/intelligence/status` - Get system status

## Real Data
- `GET /api/v1/data/revenue` - Get real revenue data
- `GET /api/v1/data/transactions` - Get real transactions
- `GET /api/v1/data/leads` - Get real leads data

## Agent Management
- `POST /api/v1/agents/fleet/deploy` - Deploy Agent Zero fleet
- `POST /api/v1/agents/task/submit` - Submit Archon2 task
- `GET /api/v1/agents/status` - Get agent hierarchy status

## System Health
- `GET /api/v1/health` - Overall system health
- `GET /api/v1/health/diagnostics` - Full diagnostics
- `GET /api/v1/health/validation` - Validation report
