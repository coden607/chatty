# CHATTY JARVIS - Your Personal AI Assistant

**Just A Rather Very Intelligent System**

Like JARVIS from Iron Man, but for your codebase and systems. A unified AI assistant that combines the best of Claude Code, Kimi CLI, and OpenClaw - working 24/7 autonomously or interactively at your command.

---

## What is JARVIS?

JARVIS is the ultimate evolution of CHATTY - a personal AI assistant that:

- 💻 **Writes and edits code** like Claude Code
- 🎯 **Executes commands** like Kimi CLI  
- 📁 **Learns from files** with OpenClaw chunking
- 🤖 **Manages AI agents** via Agent Zero fleet
- 🏛️ **Orchestrates hierarchies** with Archon2
- 🧠 **Self-repairs** when things break
- 🎙️ **Speaks and listens** (optional voice mode)
- 🔄 **Works 24/7** alongside continuous mode

---

## Quick Start

### Start JARVIS Interactive Mode
```bash
./chatty-jarvis
# or
./chattyctl jarvis
# or
./jarvis
```

### One-Shot Tasks
```bash
# Ask JARVIS anything
./chattyctl jarvis-task "Create a Python REST API"

# Generate code
./chattyctl jarvis-code "Create a fibonacci function"

# Learn from a file
./chattyctl jarvis-file ./myscript.py
```

---

## JARVIS Commands

Once in JARVIS interactive mode, you can use these commands:

### 📁 File Operations (Like Claude Code)
```
/file <path>       - Load and analyze a file
/learn <path>      - Deep learn from file with chunking
/cd <dir>          - Change working directory  
/ls [dir]          - List directory contents
/cat <file>        - Display file contents
/exec <command>    - Execute shell command
```

### 💻 Development
```
/code <task>       - Generate code
/analyze <file>    - Analyze code/file
/search <query>    - Search in loaded files
```

### 🤖 AI Systems
```
/agents            - Show Agent Zero fleet status
/archon            - Show Archon2 orchestration
/task <desc>       - Create task for agent fleet
/repair            - Run self-repair diagnostics
```

### 🧠 Memory & Status
```
/status            - Show comprehensive system status
/memory            - Show memory/context info
/keys              - Show API key status
/clear             - Clear chat history
```

### ⚙️  Settings
```
/voice             - Toggle voice mode (if available)
/autonomous        - Toggle autonomous monitoring
/help              - Show all commands
/exit, /quit       - Exit JARVIS
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      JARVIS INTERFACE                        │
│              (Interactive Chat / Voice / CLI)               │
├─────────────────────────────────────────────────────────────┤
│                    JARVIS CORE                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │
│  │ File Ops    │ │ Code Gen    │ │ System Control      │   │
│  │ (Claude)    │ │ (Multi-LLM) │ │ (Continuous Mode)   │   │
│  └─────────────┘ └─────────────┘ └─────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                   AI SYSTEMS INTEGRATION                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │OpenClaw  │ │Agent Zero│ │ Archon2  │ │NVIDIA Nemoclaw│   │
│  │Chunking  │ │Fleet     │ │Hierarchy │ │Kimi K2.5      │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                   MODEL ROUTER                               │
│        (Auto-failover: NVIDIA → OpenRouter → xAI)           │
└─────────────────────────────────────────────────────────────┘
```

---

## Features

### 1. File Learning (OpenClaw Integration)
```bash
# JARVIS can deeply learn from any file
/learn ./my_project.py

# Or naturally ask
"Please read and analyze the main.py file"
```

JARVIS will:
- Chunk the file semantically
- Store in memory
- Create embeddings for search
- Answer questions about the file

### 2. Code Generation
```bash
# Ask naturally
"Create a Python function to parse JSON with error handling"

# Or use command
/code "Create a REST API with Flask"
```

### 3. System Integration
```bash
# Check all CHATTY systems
/status

# View Agent Zero fleet
/agents

# Check Archon2 orchestration
/archon
```

### 4. Continuous Mode Bridge
JARVIS connects to the 24/7 continuous automation:
- View real-time metrics
- Dispatch tasks to agents
- Control continuous mode
- Receive alerts

### 5. Voice Mode (Optional)
```bash
/voice  # Toggle voice mode
```

With voice enabled:
- Say "Hey JARVIS" to wake
- Speak commands naturally
- JARVIS responds verbally

Requires: `pip install SpeechRecognition pyttsx3`

---

## Files Created

| File | Purpose |
|------|---------|
| `CHATTY_JARVIS.py` | Main JARVIS assistant (38KB) |
| `CHATTY_JARVIS_INTEGRATION.py` | Continuous mode bridge |
| `CHATTY_JARVIS_VOICE.py` | Voice recognition/synthesis |
| `chatty-jarvis` | Launcher script |
| `jarvis` | Shortcut symlink |

---

## Usage Examples

### Example 1: Code Review
```
💬 [chatty]> /file ./main.py
🤖 JARVIS: 📁 **main.py**

This is a Python web application using Flask. It contains:
- Route definitions
- Database models
- Authentication logic

_File loaded into context. You can now ask questions about it._

💬 [chatty]> What's the authentication flow?
🤖 JARVIS: The authentication flow in main.py works as follows:
1. User submits credentials via /login endpoint
2. Password is hashed using bcrypt
3. Session token is generated and stored
4. User is redirected to dashboard
```

### Example 2: Generate Code
```
💬 [chatty]> /code "Create a decorator for logging function calls"
🤖 JARVIS: Here's a Python decorator for logging function calls:

```python
import functools
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def log_calls(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        logger.info(f"Calling {func.__name__} at {start_time}")
        
        try:
            result = func(*args, **kwargs)
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            logger.info(f"{func.__name__} completed in {duration:.3f}s")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} failed: {e}")
            raise
    
    return wrapper

# Example usage
@log_calls
def my_function():
    pass
```

💾 Save to file? (y/n): y
Filename: log_decorator.py
✅ Saved to /home/user/projects/chatty/log_decorator.py
```

### Example 3: System Control
```
💬 [chatty]> /status
📊 JARVIS SYSTEM STATUS
══════════════════════════════════════════════════════════

🖥️  Working Directory: /home/user/projects/chatty
💾 Memory: 45 messages, 3 files loaded

📡 AI Providers: 6/8 active
   🟢 nvidia
   🟢 openrouter
   🟢 xai
   🟢 openai
   🟢 anthropic
   🟢 cohere

🔧 Components:
   🟢 Ready: File Chunker
   🟢 Ready: Self-Repair
   🟢 Ready: Agent Zero
   🟢 Ready: Archon2
   🟢 Ready: NVIDIA Nemoclaw
```

---

## Integration with Continuous Mode

JARVIS works alongside the 24/7 continuous automation:

```python
# In your code
from CHATTY_JARVIS_INTEGRATION import get_jarvis_integration

integration = await get_jarvis_integration()

# Check continuous mode status
status = await integration.get_comprehensive_status()

# Control continuous mode
result = await integration.control_continuous_mode("start")  # or "stop"

# Dispatch to agents
result = await integration.bridge.dispatch_to_agents({
    "type": "analyze_code",
    "file_path": "/path/to/file.py"
})
```

---

## Configuration

JARVIS uses your existing `.env` file with all API keys:
- `NVIDIA_API_KEY` - Primary (Kimi K2.5)
- `OPENROUTER_API_KEY` - Secondary
- `XAI_API_KEY` - Tertiary
- `OPENAI_API_KEY` - Backup

No additional configuration needed!

---

## Tips

1. **Natural Language**: JARVIS understands natural requests like "read the config file" or "analyze this code"

2. **File Context**: Once you `/learn` a file, JARVIS remembers it for the session

3. **Tab Completion**: Press TAB for command completion in interactive mode

4. **History**: Use up/down arrows to access previous commands

5. **Session Persistence**: Chat history is saved between sessions

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Model Router not initialized" | Check API keys in `.env` |
| "Voice not available" | Install: `pip install SpeechRecognition pyttsx3` |
| Commands not recognized | Make sure you're using `/` prefix for commands |
| File not found | Check path is relative to current directory |

---

## Next Steps

1. **Try JARVIS**: `./chatty-jarvis`
2. **Learn your codebase**: `/learn ./your_project`
3. **Generate code**: `/code "Create a web scraper"`
4. **Check systems**: `/status`

---

**Welcome to the future of AI assistance. JARVIS is ready, sir.** 🤖
