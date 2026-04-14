#!/usr/bin/env python3
"""
CHATTY INTERACTIVE ASSISTANT - Like Kimi Code / Claude Code
Chat with CHATTY in your terminal with full context awareness
Works alongside the 24/7 continuous automation mode

Usage:
    chatty-assistant          # Start interactive chat
    chatty-assistant --task "generate a python api"  # One-shot task
    chatty-assistant --code   # Code-focused mode
"""

import os
import sys
import asyncio
import json
import readline
import atexit
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

# Load environment
load_dotenv()
_secrets = os.getenv("CHATTY_SECRETS_FILE")
if _secrets:
    load_dotenv(os.path.expanduser(_secrets))

@dataclass
class ChatMessage:
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: str
    metadata: Optional[Dict] = None

class ChattyInteractiveAssistant:
    """Interactive terminal assistant like Kimi Code / Claude Code"""
    
    def __init__(self):
        self.history: List[ChatMessage] = []
        self.history_file = Path.home() / ".chatty_history"
        self.session_file = Path.home() / ".chatty_session"
        self.context_window = 20  # Keep last 20 messages
        
        # Initialize systems
        self.model_router = None
        self.continuous_connector = None
        self.memory_system = None
        
        # Load history
        self._load_history()
        
        # Setup readline
        self._setup_readline()
    
    def _setup_readline(self):
        """Setup command history and tab completion"""
        if self.history_file.exists():
            readline.read_history_file(str(self.history_file))
        atexit.register(self._save_history)
        
        # Tab completion for commands
        commands = [
            "/help", "/status", "/clear", "/exit", "/quit",
            "/code", "/task", "/agents", "/memory", "/youtube",
            "/openclaw", "/archon", "/nvidia", "/keys"
        ]
        readline.set_completer(lambda text, state: 
            ([c for c in commands if c.startswith(text)] + [None])[state])
        readline.parse_and_bind("tab: complete")
    
    def _load_history(self):
        """Load chat history from file"""
        if self.session_file.exists():
            try:
                with open(self.session_file) as f:
                    data = json.load(f)
                    self.history = [ChatMessage(**m) for m in data.get("messages", [])]
            except Exception:
                pass
    
    def _save_history(self):
        """Save command history"""
        readline.write_history_file(str(self.history_file))
    
    def _save_session(self):
        """Save chat session"""
        try:
            with open(self.session_file, 'w') as f:
                json.dump({
                    "messages": [asdict(m) for m in self.history[-self.context_window:]],
                    "last_updated": datetime.now().isoformat()
                }, f, indent=2, default=str)
        except Exception as e:
            print(f"⚠️  Could not save session: {e}")
    
    async def initialize(self):
        """Initialize all AI systems"""
        print("🔧 Initializing CHATTY Assistant...")
        
        # 1. Model Router with all providers
        try:
            from CHATTY_MODEL_ROUTER import ModelRouter, TaskType
            self.model_router = ModelRouter()
            health = self.model_router.health_check()
            active = sum(1 for p in health['providers'].values() if p['available'])
            print(f"   ✅ Model Router: {active} providers ready")
        except Exception as e:
            print(f"   ⚠️  Model Router: {e}")
        
        # 2. Connect to continuous mode if running
        try:
            metrics_file = Path(__file__).parent / "generated_content" / "continuous_metrics.json"
            if metrics_file.exists():
                with open(metrics_file) as f:
                    self.continuous_connector = json.load(f)
                print(f"   ✅ Connected to Continuous Mode (uptime data available)")
        except Exception as e:
            print(f"   ℹ️  Continuous Mode connector: {e}")
        
        # 3. Memory system
        try:
            from CLAUDE_MEMORY_INTEGRATION import ChattyMemoryIntegration
            self.memory_system = ChattyMemoryIntegration()
            print(f"   ✅ Memory system ready")
        except Exception as e:
            print(f"   ℹ️  Memory system: {e}")
        
        print("\n🚀 CHATTY Assistant ready!")
        print("   Type /help for commands or just start chatting.\n")
    
    def print_banner(self):
        """Print welcome banner"""
        print("""
╔═══════════════════════════════════════════════════════════════════╗
║                   🤖 CHATTY INTERACTIVE ASSISTANT                  ║
║              Like Kimi Code / Claude Code for CHATTY               ║
╠═══════════════════════════════════════════════════════════════════╣
║  Features: Code generation • Multi-agent • Real-time data          ║
║  Models: NVIDIA Kimi K2.5 • Grok-3 • Claude • GPT-4               ║
║  Systems: OpenClaw • Agent Zero • Archon2 • YouTube Learning      ║
╚═══════════════════════════════════════════════════════════════════╝
        """)
    
    async def chat_loop(self):
        """Main chat loop"""
        self.print_banner()
        await self.initialize()
        
        while True:
            try:
                # Get user input
                user_input = input("\n💬 You: ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.startswith("/"):
                    if await self._handle_command(user_input):
                        continue
                
                # Add to history
                self.history.append(ChatMessage(
                    role="user",
                    content=user_input,
                    timestamp=datetime.now().isoformat()
                ))
                
                # Generate response
                response = await self._generate_response(user_input)
                
                # Add response to history
                self.history.append(ChatMessage(
                    role="assistant",
                    content=response,
                    timestamp=datetime.now().isoformat()
                ))
                
                # Print response
                print(f"\n🤖 CHATTY: {response}")
                
                # Save session
                self._save_session()
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except EOFError:
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
    
    async def _handle_command(self, command: str) -> bool:
        """Handle slash commands. Returns True if handled."""
        cmd = command.lower().split()[0]
        args = command[len(cmd):].strip()
        
        if cmd in ["/exit", "/quit"]:
            print("\n👋 Goodbye!")
            sys.exit(0)
        
        elif cmd == "/help":
            print("""
📋 Available Commands:
  /help           Show this help
  /status         Show CHATTY system status
  /clear          Clear chat history
  /exit, /quit    Exit the assistant
  
🛠️  System Commands:
  /agents         Show Agent Zero fleet status
  /archon         Show Archon2 orchestration status
  /openclaw       Show OpenClaw learning status
  /nvidia         Show NVIDIA Nemoclaw status
  /keys           Show API key rotation status
  /memory         Show memory/context info
  /youtube        Show YouTube learning status
  
💻 Development:
  /code <task>    Focus on code generation
  /task <desc>    Create a task for agents
            """)
        
        elif cmd == "/status":
            await self._show_status()
        
        elif cmd == "/clear":
            self.history = []
            print("✅ Chat history cleared")
        
        elif cmd == "/agents":
            print("🤖 Agent Zero Fleet:")
            if self.continuous_connector:
                az = self.continuous_connector.get("components", {}).get("agent_zero", {})
                print(f"   Status: {'🟢 Running' if az.get('running') else '🔴 Not running'}")
                print(f"   Metrics: {az.get('metrics', {})}")
            else:
                print("   ℹ️  Connect to continuous mode for live data")
        
        elif cmd == "/archon":
            print("🏛️  Archon2 Orchestration:")
            if self.continuous_connector:
                ar = self.continuous_connector.get("components", {}).get("archon2", {})
                print(f"   Status: {'🟢 Running' if ar.get('running') else '🔴 Not running'}")
                print(f"   14 agents across 4 hierarchy levels")
        
        elif cmd == "/openclaw":
            print("🔧 OpenClaw:")
            if self.continuous_connector:
                oc = self.continuous_connector.get("components", {}).get("openclaw", {})
                print(f"   Status: {'🟢 Running' if oc.get('running') else '🔴 Not running'}")
                print(f"   Chunks learned: {oc.get('metrics', {}).get('chunks_learned', 0)}")
        
        elif cmd == "/nvidia":
            print("🎮 NVIDIA Nemoclaw:")
            if self.continuous_connector:
                nv = self.continuous_connector.get("components", {}).get("nvidia_nemoclaw", {})
                print(f"   Status: {'🟢 Running' if nv.get('running') else '🔴 Not running'}")
                metrics = nv.get("metrics", {})
                print(f"   Model: {metrics.get('model', 'N/A')}")
                print(f"   Latency: {metrics.get('latency_ms', 0):.0f}ms")
        
        elif cmd == "/keys":
            print("🔑 API Key Rotation:")
            if self.continuous_connector:
                rot = self.continuous_connector.get("key_rotation_index", 0)
                print(f"   Rotation cycles: {rot}")
                print(f"   OpenRouter: 5 keys rotating")
                print(f"   xAI: 4 keys rotating")
                print(f"   NVIDIA: 1 key (Kimi K2.5)")
        
        elif cmd == "/memory":
            print(f"🧠 Memory:")
            print(f"   Messages in session: {len(self.history)}")
            print(f"   Context window: {self.context_window}")
            print(f"   History file: {self.history_file}")
        
        elif cmd == "/code":
            if args:
                response = await self._generate_code(args)
                print(f"\n🤖 CHATTY:\n{response}")
            else:
                print("Usage: /code <description of what to generate>")
        
        elif cmd == "/task":
            if args:
                print(f"📋 Creating task: {args}")
                # Could dispatch to continuous mode
                print("   Task would be dispatched to Agent Zero fleet")
            else:
                print("Usage: /task <task description>")
        
        else:
            print(f"❓ Unknown command: {cmd}. Type /help for available commands.")
        
        return True
    
    async def _show_status(self):
        """Show comprehensive CHATTY status"""
        print("\n📊 CHATTY SYSTEM STATUS")
        print("=" * 60)
        
        # Model Router status
        if self.model_router:
            health = self.model_router.health_check()
            active = sum(1 for p in health['providers'].values() if p['available'])
            print(f"📡 Model Router: {active}/8 providers active")
        
        # Continuous mode status
        if self.continuous_connector:
            print(f"\n🔄 Continuous Mode:")
            print(f"   Last update: {self.continuous_connector.get('timestamp', 'N/A')}")
            print(f"   Key rotations: {self.continuous_connector.get('key_rotation_index', 0)}")
            
            print(f"\n   Components:")
            for name, comp in self.continuous_connector.get("components", {}).items():
                status = "🟢" if comp.get("running") else "⚪"
                print(f"   {status} {name}")
        
        print("\n" + "=" * 60)
    
    async def _generate_response(self, user_input: str) -> str:
        """Generate AI response using CHATTY systems"""
        if not self.model_router:
            return "⚠️ Model Router not initialized. Check your API keys."
        
        try:
            from CHATTY_MODEL_ROUTER import TaskType
            
            # Build context from history
            context = "\n".join([
                f"{'User' if m.role == 'user' else 'Assistant'}: {m.content}"
                for m in self.history[-6:]  # Last 6 messages for context
            ])
            
            # Determine task type
            task_type = TaskType.CHAT
            if any(kw in user_input.lower() for kw in ["code", "function", "class", "script", "python", "javascript"]):
                task_type = TaskType.CODE_GENERATION
            elif any(kw in user_input.lower() for kw in ["debug", "fix", "error", "bug"]):
                task_type = TaskType.DEBUGGING
            elif any(kw in user_input.lower() for kw in ["analyze", "data", "research"]):
                task_type = TaskType.RESEARCH
            
            # Generate using CHATTY Model Router
            result = await self.model_router.generate(
                prompt=user_input,
                system_prompt=f"""You are CHATTY, an advanced AI assistant with access to:
- OpenClaw (file chunking & self-repair)
- Agent Zero (fleet management)
- Archon2 (14-agent hierarchy)
- NVIDIA Nemoclaw (Kimi K2.5)
- YouTube Learning
- Multi-provider AI routing

Previous conversation context:
{context}

Respond helpfully and concisely.""",
                task_type=task_type,
                max_tokens=1000,
                temperature=0.7
            )
            
            return result.content if hasattr(result, 'content') and result.content else "I processed your request but couldn't generate a response. Try again?"
            
        except Exception as e:
            return f"❌ Error generating response: {str(e)[:100]}"
    
    async def _generate_code(self, description: str) -> str:
        """Generate code with proper formatting"""
        if not self.model_router:
            return "⚠️ Model Router not initialized."
        
        try:
            from CHATTY_MODEL_ROUTER import TaskType
            
            result = await self.model_router.generate(
                prompt=f"Generate code for: {description}",
                system_prompt="""You are a code generation expert. 
Generate clean, well-commented code.
Include file extension suggestions.
Explain key parts briefly.""",
                task_type=TaskType.CODE_GENERATION,
                max_tokens=2000,
                temperature=0.3
            )
            
            return result.content if hasattr(result, 'content') else "Could not generate code."
            
        except Exception as e:
            return f"❌ Error: {str(e)[:100]}"
    
    async def one_shot_task(self, task: str, mode: str = "chat"):
        """Execute a one-shot task and exit"""
        await self.initialize()
        
        if mode == "code":
            response = await self._generate_code(task)
        else:
            response = await self._generate_response(task)
        
        print(response)

async def main():
    """Entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="CHATTY Interactive Assistant")
    parser.add_argument("--task", type=str, help="One-shot task to execute")
    parser.add_argument("--code", action="store_true", help="Code generation mode")
    parser.add_argument("--status", action="store_true", help="Show status and exit")
    
    args = parser.parse_args()
    
    assistant = ChattyInteractiveAssistant()
    
    if args.status:
        await assistant.initialize()
        await assistant._show_status()
    elif args.task:
        await assistant.one_shot_task(args.task, "code" if args.code else "chat")
    else:
        await assistant.chat_loop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
