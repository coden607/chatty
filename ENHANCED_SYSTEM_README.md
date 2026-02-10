# Enhanced Chatty Multi-Agent Automation System

🚀 **A fully automated, self-healing, self-learning multi-agent system with YouTube transcription capabilities, token optimization, and open-source tool integrations.**

## 🌟 Key Features

### 🤖 Multi-Agent Architecture
- **5+ Specialized Agents**: System Optimizer, YouTube Learner, Self Healer, Guardrail, Token Optimizer
- **Collaborative Intelligence**: Agents work together on complex tasks
- **Dynamic Load Balancing**: Intelligent task distribution across agents
- **Real-time Communication**: Token-efficient agent-to-agent messaging

### 🎥 YouTube Learning System
- **Automatic Transcription**: Extract and process YouTube video transcripts
- **Knowledge Integration**: Convert video insights into actionable system improvements
- **Continuous Learning**: Agents learn from relevant content 24/7
- **Content Generation**: Automatically create blog posts, social media, and implementation guides

### 🔧 Self-Healing Capabilities
- **Health Monitoring**: Real-time system health checks (memory, disk, API connectivity)
- **Auto-Recovery**: Automatic fixes for common issues
- **Predictive Maintenance**: Identify and resolve problems before they impact performance
- **Graceful Degradation**: System continues operating even with component failures

### 💰 Token Optimization
- **Semantic Compression**: Reduce token usage by 30% while preserving context
- **Cost Estimation**: Real-time token cost tracking
- **Smart Routing**: Route tasks to most cost-effective LLM providers
- **Context Management**: Efficient context passing between agents

### 🛡️ Guardrails & Safety
- **Hallucination Detection**: Identify and flag potential AI hallucinations
- **Content Validation**: Safety checks for all generated content
- **Accuracy Verification**: Fact-checking and validation systems
- **Ethical Compliance**: Ensure all outputs meet safety standards

### 🔗 Open-Source Integrations
- **OpenCLAW**: Advanced automation workflows
- **Agent Zero**: Agent orchestration and scaling
- **N8N**: Visual workflow automation
- **Pydantic AI**: Structured AI responses
- **ChromaDB/FAISS**: Vector database storage
- **Prefect/Dagster**: Workflow orchestration
- **Transformers/LangChain**: AI model integrations

### 📱 Multi-Agent Chat Interface
- **Real-time Chat**: Web-based interface to chat with multiple agents simultaneously
- **Context Awareness**: Agents maintain conversation context
- **Specialized Responses**: Each agent provides domain-specific insights
- **Token Usage Tracking**: Real-time cost monitoring

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                Enhanced Chatty System                       │
├─────────────────────────────────────────────────────────────┤
│  🤖 Multi-Agent Chat Interface (FastAPI + WebSocket)      │
├─────────────────────────────────────────────────────────────┤
│  🔄 Token Optimization Layer                               │
├─────────────────────────────────────────────────────────────┤
│  🤖 Enhanced Multi-Agent System                           │
│  ├── System Optimizer    ├── YouTube Learner               │
│  ├── Self Healer          ├── Guardrail                     │
│  └── Token Optimizer      └── [Additional Agents]           │
├─────────────────────────────────────────────────────────────┤
│  🔗 Open-Source Integration Layer                          │
│  ├── OpenCLAW ├── Agent Zero ├── N8N ├── Pydantic AI      │
│  ├── ChromaDB ├── FAISS ├── Prefect ├── Dagster           │
│  └── Transformers ├── LangChain                            │
├─────────────────────────────────────────────────────────────┤
│  🎥 YouTube Learning System                                │
│  ├── Transcript Extraction ├── Content Analysis            │
│  ├── Insight Extraction └── Knowledge Integration          │
├─────────────────────────────────────────────────────────────┤
│  🔧 Self-Healing Engine                                    │
│  ├── Health Monitoring ├── Auto-Recovery                   │
│  └── Predictive Maintenance                                │
├─────────────────────────────────────────────────────────────┤
│  🛡️ Guardrail System                                       │
│  ├── Hallucination Detection ├── Content Validation         │
│  └── Safety Checks                                         │
├─────────────────────────────────────────────────────────────┤
│  📊 Existing Chatty Automation (Revenue + Acquisition)     │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- 8GB+ RAM recommended
- Internet connection for YouTube/API access

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd chatty
```

2. **Install dependencies**
```bash
# Core dependencies
pip3 install fastapi uvicorn websockets pydantic python-multipart

# AI/ML dependencies
pip3 install sentence-transformers transformers langchain

# YouTube transcription
pip3 install youtube-transcript-api

# Vector databases
pip3 install chromadb faiss-cpu

# Workflow engines (optional)
pip3 install prefect dagster n8n

# Open-source tools (optional)
pip3 install openclaw agent-zero pydantic-ai

# System monitoring
pip3 install psutil
```

3. **Set up environment variables**
```bash
# Create .env file
cp .env.example .env

# Edit .env with your API keys
nano .env
```

4. **Run the system**
```bash
# Using the enhanced launcher
./launch_enhanced_chatty.sh

# Or directly with Python
python3 ENHANCED_START_COMPLETE_AUTOMATION.py

# Chat interface only
python3 ENHANCED_START_COMPLETE_AUTOMATION.py --mode chat-only --port 8000
```

5. **Access the interface**
- **Chat Interface**: http://localhost:8000
- **System Status**: http://localhost:8000/api/system/metrics
- **Agent Status**: http://localhost:8000/api/agents/status

## 📖 Usage Guide

### Multi-Agent Chat

1. **Open the chat interface** at http://localhost:8000
2. **Type your message** - all active agents will respond
3. **Review specialized insights** from each agent
4. **Monitor token usage** in real-time

**Example Chat:**
```
You: "How can we improve system performance?"

🔧 System Optimizer: "I recommend optimizing the database queries and implementing caching...
🎥 YouTube Learner: "I found 3 relevant videos about performance optimization...
🔨 Self Healer: "System health is at 92%. No immediate performance issues detected...
🛡️ Guardrail: "Performance optimization recommendations are safe and validated...
💰 Token Optimizer: "This conversation used 156 tokens. I can optimize by 25%..."
```

### YouTube Learning

1. **Provide video URL** to the YouTube Learner agent
2. **Automatic transcription** and analysis
3. **Knowledge integration** into the system
4. **Content generation** based on insights

```python
# Programmatic YouTube learning
from ENHANCED_MULTI_AGENT_SYSTEM import EnhancedMultiAgentSystem

system = EnhancedMultiAgentSystem()
await system.initialize()

result = await system.youtube_learner.learn_from_video(
    video_url="https://youtube.com/watch?v=example",
    learning_goals=["automation", "ai", "optimization"]
)
```

### Self-Healing

The system automatically:
- Monitors memory usage, disk space, API connectivity
- Triggers healing actions when health drops below 80%
- Logs all recovery actions
- Maintains system uptime

### Token Optimization

- **Automatic compression** of large messages
- **Cost estimation** before processing
- **Provider rotation** for best rates
- **Context preservation** during optimization

## 🔧 Configuration

### Environment Variables

```bash
# API Keys (choose one or more)
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
XAI_API_KEY=your_xai_key
OPENROUTER_API_KEY=your_openrouter_key

# System Configuration
CHATTY_OFFLINE_MODE=false
CHATTY_SUPERVISOR_INTERVAL_SECONDS=15
CHATTY_REVENUE_SCHEDULER_INTERVAL_SECONDS=900

# Enhanced System Settings
ENHANCED_SYSTEM_LOG_LEVEL=INFO
TOKEN_OPTIMIZATION_ENABLED=true
YOUTUBE_LEARNING_ENABLED=true
SELF_HEALING_ENABLED=true
GUARDRAIL_ENABLED=true

# Integration Settings
OPENCLAW_ENABLED=true
AGENT_ZERO_ENABLED=true
N8N_ENABLED=true
CHROMADB_ENABLED=true
```

### Agent Configuration

Each agent can be configured via `PydanticAgentConfig`:

```python
from ENHANCED_MULTI_AGENT_SYSTEM import PydanticAgentConfig, AgentRole

config = PydanticAgentConfig(
    agent_id="custom_agent",
    role=AgentRole.SYSTEM_OPTIMIZER,
    capabilities=["custom_capability"],
    llm_provider="openai",
    model_name="gpt-4",
    max_tokens=4000,
    temperature=0.7,
    memory_enabled=True,
    learning_enabled=True,
    auto_healing=True,
    token_optimization=True
)
```

## 📊 Monitoring & Metrics

### System Metrics
- **Active Agents**: Number of running agents
- **System Health**: Overall system health percentage
- **Token Usage**: Total tokens consumed and costs
- **Task Processing**: Success/failure rates
- **Integration Status**: Status of all open-source integrations

### API Endpoints

```bash
# System status
GET /api/system/metrics

# Agent status
GET /api/agents/status

# Create chat session
POST /api/session/create

# Send message
POST /api/chat/message

# Integration status
GET /api/integrations/status
```

### Logs

- **Main Log**: `logs/enhanced_automation.log`
- **Agent Log**: `logs/enhanced_agents.log`
- **Chat Log**: `logs/chat_interface.log`
- **YouTube Learning**: `logs/youtube_learning.log`

## 🔄 Integration with Existing System

The enhanced system is designed to work alongside your existing Chatty automation:

1. **Preserves existing functionality** - Revenue engine, customer acquisition, etc.
2. **Adds new capabilities** - Multi-agent chat, YouTube learning, self-healing
3. **Shared resources** - Uses existing databases, APIs, and configurations
4. **Gradual migration** - Can enable/disable features independently

## 🛠️ Development

### Adding New Agents

```python
from ENHANCED_MULTI_AGENT_SYSTEM import EnhancedAgent, PydanticAgentConfig, AgentRole

# Create custom agent
class CustomAgent(EnhancedAgent):
    async def _handle_custom_task(self, message):
        # Custom logic here
        return "Custom response"

# Register agent
config = PydanticAgentConfig(
    agent_id="custom_agent",
    role=AgentRole.SYSTEM_OPTIMIZER,
    capabilities=["custom_capability"]
)

agent = CustomAgent(config, communication_hub)
system.agents["custom_agent"] = agent
```

### Adding New Integrations

```python
from OPEN_SOURCE_INTEGRATIONS import UnifiedIntegrationInterface

class CustomIntegration:
    async def execute_task(self, task_config):
        # Custom integration logic
        return {"result": "Custom task completed"}

# Register integration
interface.integration_manager.integrations["custom"] = CustomIntegration()
```

### Testing

```bash
# Run tests
python3 -m pytest tests/

# Test specific components
python3 ENHANCED_MULTI_AGENT_SYSTEM.py --test
python3 OPEN_SOURCE_INTEGRATIONS.py --test
```

## 🚨 Troubleshooting

### Common Issues

1. **Memory Issues**
   - Increase system RAM
   - Enable token optimization
   - Reduce agent count

2. **API Rate Limits**
   - Configure multiple API keys
   - Enable provider rotation
   - Use token optimization

3. **YouTube Transcription Failures**
   - Check video availability
   - Verify transcript language support
   - Use fallback transcription service

4. **Integration Failures**
   - Verify tool installation
   - Check configuration
   - Review logs for specific errors

### Debug Mode

```bash
# Enable debug logging
python3 ENHANCED_START_COMPLETE_AUTOMATION.py --debug

# Check component status
python3 ENHANCED_START_COMPLETE_AUTOMATION.py --mode status
```

## 📈 Performance Optimization

### Token Optimization
- Enable semantic compression
- Use context caching
- Optimize prompt engineering

### System Performance
- Monitor resource usage
- Scale agent count based on load
- Use load balancing

### Cost Management
- Track token usage
- Rotate between providers
- Optimize for cost vs. quality

## 🔮 Future Roadmap

### v2.0 Features
- [ ] Voice chat interface
- [ ] Mobile app
- [ ] Advanced analytics dashboard
- [ ] Custom agent marketplace
- [ ] Multi-language support

### v3.0 Features
- [ ] Distributed agent deployment
- [ ] Advanced AI model fine-tuning
- [ ] Real-time video processing
- [ ] Blockchain integration
- [ ] Edge computing support

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new features
4. Submit pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Open-source community for amazing tools
- YouTube for transcript API
- AI providers for powerful models
- Contributors and testers

## 📞 Support

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Documentation**: Wiki
- **Community**: Discord/Slack

---

**🚀 Enhanced Chatty: Where multiple AI minds collaborate for automation excellence!**
