# NVIDIA Build + Kimi K2.5 Real Data Setup Guide

## Overview

This guide configures CHATTY to use **NVIDIA Build API** with **Kimi K2.5** for all AI operations. 

**Key Features:**
- ✅ **REAL DATA ONLY** - No simulations, no demo mode
- ✅ **FREE TIER** - NVIDIA offers free API access for prototyping
- ✅ **Kimi K2.5** - State-of-the-art multimodal model (1T parameters, 256K context)
- ✅ **Automatic Failover** - Between available NVIDIA endpoints

## Quick Start

### 1. Get Your Free NVIDIA API Key

1. Visit: https://build.nvidia.com/moonshotai/kimi-k2.5
2. Sign in with your NVIDIA Developer account (free to create)
3. Click "Get API Key"
4. Copy your API key

### 2. Set Environment Variable

```bash
# Linux/macOS
export NVIDIA_API_KEY='nvapi-your-actual-key-here'

# Add to your ~/.bashrc or ~/.zshrc for persistence
echo 'export NVIDIA_API_KEY="nvapi-your-key"' >> ~/.bashrc
```

### 3. Test the Connection

```bash
cd /home/coden809/Projects/chatty
source .venv/bin/activate
python3 NVIDIA_REAL_AI_ORCHESTRATION.py
```

## API Details

### NVIDIA Build Endpoint
```
URL: https://integrate.api.nvidia.com/v1/chat/completions
Model: moonshotai/kimi-k2.5
```

### Kimi K2.5 Specifications
| Feature | Value |
|---------|-------|
| Parameters | 1 Trillion (32B active) |
| Architecture | MoE (Mixture of Experts) |
| Context Window | 256,000 tokens |
| Vision Support | Yes (images + video) |
| Tool Calling | Yes |
| Thinking Mode | Yes |

### Free Tier Limits
- **Rate Limit**: 6 requests per minute (RPM)
- **Daily Limit**: 3,000,000 tokens per day
- **Concurrent**: Limited (varies by load)

## Usage Examples

### Basic Task Execution

```python
import asyncio
from NVIDIA_REAL_AI_ORCHESTRATION import (
    get_orchestrator, 
    UnifiedTask, 
    TaskType
)

async def main():
    orchestrator = await get_orchestrator()
    
    # Test API connection
    status = await orchestrator.test_api_connection()
    print(f"API Status: {status}")
    
    # Execute a task
    result = await orchestrator.execute_task(
        UnifiedTask(
            name="Generate Code",
            description="Create a Python class for API authentication",
            task_type=TaskType.CODE_GENERATION
        )
    )
    
    print(f"Status: {result.status}")
    print(f"Output: {result.output}")
    print(f"Tokens used: {result.tokens_used}")

asyncio.run(main())
```

### Code Generation

```python
from NVIDIA_REAL_AI_ORCHESTRATION import execute_ai_task, TaskType

result = await execute_ai_task(
    name="Generate API Client",
    description="Create a Python HTTP client with retry logic",
    task_type=TaskType.CODE_GENERATION,
    context={"language": "python"}
)

print(result.output['code'])
```

### Data Analysis

```python
result = await execute_ai_task(
    name="Analyze Sales",
    description="Analyze Q4 sales data for trends",
    task_type=TaskType.DATA_ANALYSIS,
    inputs={
        "data": [
            {"month": "Oct", "sales": 15000},
            {"month": "Nov", "sales": 18000},
            {"month": "Dec", "sales": 22000}
        ]
    }
)

print(result.output['analysis'])
```

### Content Creation

```python
result = await execute_ai_task(
    name="Blog Post",
    description="Write a blog post about AI automation",
    task_type=TaskType.CONTENT_CREATION,
    inputs={"platform": "blog", "tone": "professional"}
)

print(result.output['content'])
```

## Framework Routing

The system automatically routes tasks to the optimal framework:

| Task Type | Framework | Best For |
|-----------|-----------|----------|
| `code_generation` | OpenClaw | Writing code |
| `debugging` | OpenClaw | Fixing bugs |
| `data_analysis` | Pydantic | Structured analysis |
| `research` | LangChain | Information gathering |
| `content_creation` | CrewAI | Multi-agent writing |
| `strategic_planning` | Archon2 | Hierarchical planning |

All frameworks use **Kimi K2.5 via NVIDIA API** for actual AI operations.

## Available Models on NVIDIA Build

NVIDIA Build offers several free models:

1. **moonshotai/kimi-k2.5** (Recommended)
   - Best overall performance
   - Multimodal (text + vision)
   - Agentic capabilities

2. **meta/llama-3.3-70b-instruct**
   - Alternative option
   - Good for simpler tasks

3. **mistralai/mixtral-8x22b-instruct-v0.1**
   - Mixture of Experts
   - Efficient inference

To use a different model, modify `NVIDIA_REAL_AI_ORCHESTRATION.py`:
```python
MODEL_NAME = "meta/llama-3.3-70b-instruct"  # Change this
```

## Error Handling

The system raises `RealDataError` if:
- API key is not configured
- API returns an error
- Rate limits exceeded
- Network issues

Example error handling:
```python
from NVIDIA_REAL_AI_ORCHESTRATION import RealDataError

try:
    result = await orchestrator.execute_task(task)
except RealDataError as e:
    print(f"API Error: {e}")
    # Handle appropriately
```

## Monitoring

Track your API usage:

```python
# Get health status
health = orchestrator.get_health()
print(f"API Requests: {health.api_status['total_requests']}")
print(f"Tokens Used: {health.api_status['total_tokens']}")
```

## Integration with Existing CHATTY

To integrate with the main CHATTY system:

```python
# In your main CHATTY code
from NVIDIA_REAL_AI_ORCHESTRATION import get_orchestrator

async def initialize_chatty():
    # Initialize NVIDIA-based orchestrator
    ai_orchestrator = await get_orchestrator()
    
    # Use for all AI operations
    result = await ai_orchestrator.execute_task(...)
```

## Troubleshooting

### "NVIDIA_API_KEY environment variable not set"
```bash
export NVIDIA_API_KEY='nvapi-your-key-here'
```

### "429 Too Many Requests"
- You've hit the rate limit (6 RPM)
- Wait 10 seconds and retry
- Consider adding delays between requests

### "402 Payment Required"
- Daily token limit (3M) exceeded
- Wait for next day or upgrade plan

### Connection Timeout
- Check internet connection
- NVIDIA API may be temporarily unavailable
- Retry with exponential backoff

## Best Practices

1. **Set API Key Early**: Configure before importing
2. **Handle Rate Limits**: Add delays between requests
3. **Cache Results**: Store responses to avoid duplicate API calls
4. **Monitor Usage**: Track token consumption
5. **Error Handling**: Always catch `RealDataError`

## Resources

- **NVIDIA Build**: https://build.nvidia.com
- **Kimi K2.5 Model Card**: https://build.nvidia.com/moonshotai/kimi-k2.5/modelcard
- **NVIDIA Developer Program**: https://developer.nvidia.com
- **Kimi Documentation**: https://platform.moonshot.ai

## Support

For issues:
1. Check API key is set correctly
2. Verify NVIDIA Build status
3. Check rate limits
4. Review error messages carefully

---

**Note**: This system requires a valid NVIDIA API key and active internet connection. All operations make REAL API calls to NVIDIA's servers.
