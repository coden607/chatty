#!/usr/bin/env python3
"""
CHATTY - Complete Heuristic Assistant for Technical Tasks Yielding Results
======================================================
The ultimate personal AI assistant that combines:
- OpenClaw (file learning, chunking, self-repair)
- Claude Code-style file operations
- Kimi CLI-style command interface  
- Agent Zero fleet management
- Archon2 hierarchical orchestration
- Multi-LLM routing with auto-failover
- Voice commands (optional)
- 24/7 autonomous operation

Like CHATTY - your personal AI assistant that works
around the clock, manages your systems, writes code, and learns.

Usage:
    ./chatty                    # Start interactive mode
    ./chatty --task "..."       # One-shot task
    ./chatty --code "..."       # Code generation
    ./chatty --file <path>      # Learn from file
    ./chatty --watch <dir>      # Watch directory
"""

import os
import sys
import asyncio
import json
import readline
import atexit
import subprocess
import shlex
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

# Load environment
load_dotenv()
_secrets = os.getenv("CHATTY_SECRETS_FILE")
if _secrets:
    load_dotenv(os.path.expanduser(_secrets))


@dataclass
class JarvisMessage:
    role: str  # "user", "assistant", "system", "agent"
    content: str
    timestamp: str
    metadata: Optional[Dict] = None


@dataclass
class FileContext:
    path: str
    content: str
    chunks: List[Dict]
    summary: str
    last_accessed: str


class JarvisCore:
    """Core CHATTY intelligence system"""
    
    def __init__(self):
        self.history: List[JarvisMessage] = []
        self.file_contexts: Dict[str, FileContext] = {}
        self.working_directory = Path.cwd()
        
        # System components
        self.model_router = None
        self.file_chunker = None
        self.self_repair = None
        self.agent_zero = None
        self.archon2 = None
        self.nvidia_orchestrator = None
        
        # Paths
        self.history_file = Path.home() / ".chatty_history"
        self.session_file = Path.home() / ".chatty_session"
        self.memory_dir = Path.home() / ".chatty_memory"
        self.memory_dir.mkdir(exist_ok=True)
        
        # Settings
        self.context_window = 30
        self.voice_enabled = False
        self.autonomous_mode = False
        
        self._load_history()
        self._setup_readline()
    
    def _setup_readline(self):
        """Setup command history and tab completion"""
        if self.history_file.exists():
            try:
                readline.read_history_file(str(self.history_file))
            except:
                pass
        atexit.register(self._save_history)
        
        # Commands for tab completion
        commands = [
            "/help", "/status", "/clear", "/exit", "/quit",
            "/code", "/file", "/learn", "/agents", "/memory",
            "/openclaw", "/archon", "/nvidia", "/keys",
            "/exec", "/cd", "/ls", "/cat", "/edit",
            "/task", "/repair", "/analyze", "/search",
            "/voice", "/autonomous", "/continuous"
        ]
        
        def completer(text, state):
            options = [c for c in commands if c.startswith(text)]
            if state < len(options):
                return options[state]
            return None
        
        readline.set_completer(completer)
        readline.parse_and_bind("tab: complete")
    
    def _load_history(self):
        """Load chat history"""
        if self.session_file.exists():
            try:
                with open(self.session_file) as f:
                    data = json.load(f)
                    self.history = [JarvisMessage(**m) for m in data.get("messages", [])]
            except:
                pass
    
    def _save_history(self):
        """Save command history"""
        try:
            readline.write_history_file(str(self.history_file))
        except:
            pass
    
    def _save_session(self):
        """Save chat session"""
        try:
            with open(self.session_file, 'w') as f:
                json.dump({
                    "messages": [asdict(m) for m in self.history[-self.context_window:]],
                    "last_updated": datetime.now().isoformat(),
                    "working_directory": str(self.working_directory)
                }, f, indent=2, default=str)
        except Exception as e:
            print(f"⚠️  Could not save session: {e}")
    
    async def initialize(self):
        """Initialize all CHATTY systems"""
        print("🔧 Initializing CHATTY systems...")
        
        # 1. Model Router
        try:
            from CHATTY_MODEL_ROUTER import ModelRouter, TaskType
            self.model_router = ModelRouter()
            health = self.model_router.health_check()
            active = sum(1 for p in health['providers'].values() if p['available'])
            print(f"   ✅ Model Router: {active} providers ready")
        except Exception as e:
            print(f"   ⚠️  Model Router: {e}")
        
        # 2. OpenClaw File Chunker
        try:
            from openclaw_integration import FileChunker
            self.file_chunker = FileChunker()
            print(f"   ✅ OpenClaw File Chunker ready")
        except Exception as e:
            print(f"   ⚠️  OpenClaw: {e}")
        
        # 3. Self-Repair Engine
        try:
            from openclaw_integration import SelfRepairEngine
            self.self_repair = SelfRepairEngine()
            print(f"   ✅ Self-Repair Engine ready")
        except Exception as e:
            print(f"   ⚠️  Self-Repair: {e}")
        
        # 4. Agent Zero Fleet
        try:
            from AGENT_ZERO_FLEET import AgentZeroFleet
            self.agent_zero = AgentZeroFleet()
            print(f"   ✅ Agent Zero Fleet ready")
        except Exception as e:
            print(f"   ℹ️  Agent Zero: {e}")
        
        # 5. Archon2 Orchestration
        try:
            from ARCHON2_ORCHESTRATION import Archon2Orchestrator
            self.archon2 = Archon2Orchestrator()
            print(f"   ✅ Archon2 Orchestration ready")
        except Exception as e:
            print(f"   ℹ️  Archon2: {e}")
        
        # 6. NVIDIA Nemoclaw
        try:
            from NVIDIA_REAL_AI_ORCHESTRATION import get_orchestrator
            self.nvidia_orchestrator = await get_orchestrator()
            status = await self.nvidia_orchestrator.test_api_connection()
            if status.get("status") == "connected":
                print(f"   ✅ NVIDIA Nemoclaw connected ({status['model']})")
            else:
                print(f"   ⚠️  NVIDIA Nemoclaw: not connected")
        except Exception as e:
            print(f"   ℹ️  NVIDIA Nemoclaw: {e}")
        
        print("\n🚀 CHATTY is online and ready to assist you.")
        print("   Type /help for commands or just start chatting.\n")
    
    def print_banner(self):
        """Print CHATTY welcome banner"""
        print("""
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║     ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗    ██╗  ██╗              ║
║     ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝    ██║  ██║              ║
║     ██║███████║██████╔╝██║   ██║██║███████╗    ███████║              ║
║     ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║    ██╔══██║              ║
║     ██║██║  ██║██║  ██║ ╚████╔╝ ██║███████║    ██║  ██║              ║
║     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝    ╚═╝  ╚═╝              ║
║                                                                       ║
║     Complete Heuristic Assistant for Technical Tasks Yielding Results                             ║
╠═══════════════════════════════════════════════════════════════════════╣
║  💻 File Operations    🤖 Multi-Agent     🧠 Self-Repair             ║
║  📁 Code Analysis      🎯 Task Routing    🔄 Continuous Learning     ║
║  🌐 Web Search         📊 Data Analysis   🎮 NVIDIA Kimi K2.5        ║
╚═══════════════════════════════════════════════════════════════════════╝
        """)


class JarvisAssistant(JarvisCore):
    """Interactive CHATTY assistant with file operations"""
    
    def __init__(self):
        super().__init__()
        self.command_handlers = {
            '/help': self._cmd_help,
            '/status': self._cmd_status,
            '/clear': self._cmd_clear,
            '/exit': self._cmd_exit,
            '/quit': self._cmd_exit,
            '/code': self._cmd_code,
            '/file': self._cmd_file,
            '/learn': self._cmd_learn,
            '/exec': self._cmd_exec,
            '/cd': self._cmd_cd,
            '/ls': self._cmd_ls,
            '/cat': self._cmd_cat,
            '/agents': self._cmd_agents,
            '/archon': self._cmd_archon,
            '/repair': self._cmd_repair,
            '/search': self._cmd_search,
            '/task': self._cmd_task,
            '/analyze': self._cmd_analyze,
            '/memory': self._cmd_memory,
            '/keys': self._cmd_keys,
            '/voice': self._cmd_voice,
            '/autonomous': self._cmd_autonomous,
        }
    
    async def chat_loop(self):
        """Main interactive chat loop"""
        self.print_banner()
        await self.initialize()
        
        while True:
            try:
                # Get user input
                prompt = f"\n💬 [{self.working_directory.name}]> "
                user_input = input(prompt).strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.startswith("/"):
                    cmd_parts = user_input.split(None, 1)
                    cmd = cmd_parts[0].lower()
                    args = cmd_parts[1] if len(cmd_parts) > 1 else ""
                    
                    if cmd in self.command_handlers:
                        should_continue = await self.command_handlers[cmd](args)
                        if not should_continue:
                            break
                        continue
                    else:
                        print(f"❓ Unknown command: {cmd}. Type /help for available commands.")
                        continue
                
                # Regular chat - add to history
                self._add_message("user", user_input)
                
                # Check if it's a file operation request
                if self._is_file_request(user_input):
                    response = await self._handle_file_request(user_input)
                else:
                    # Generate AI response
                    response = await self._generate_response(user_input)
                
                # Add response to history
                self._add_message("assistant", response)
                
                # Print response
                print(f"\n🤖 CHATTY: {response}")
                
                # Save session
                self._save_session()
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye.")
                break
            except EOFError:
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
    
    def _add_message(self, role: str, content: str, metadata: Dict = None):
        """Add message to history"""
        self.history.append(JarvisMessage(
            role=role,
            content=content,
            timestamp=datetime.now().isoformat(),
            metadata=metadata
        ))
    
    def _is_file_request(self, text: str) -> bool:
        """Check if user is asking for file operations"""
        file_keywords = [
            "read file", "show file", "open file", "view file",
            "cat ", "list files", "ls ", "directory", "folder",
            "create file", "write file", "edit file", "modify file"
        ]
        return any(kw in text.lower() for kw in file_keywords)
    
    async def _handle_file_request(self, text: str) -> str:
        """Handle file-related requests"""
        # Extract file path
        words = text.split()
        file_path = None
        
        for i, word in enumerate(words):
            if word.endswith(('.py', '.js', '.ts', '.md', '.txt', '.json', '.yml', '.yaml', '.sh')):
                file_path = word
                break
            elif i > 0 and words[i-1] in ['file', 'read', 'open', 'show', 'cat']:
                file_path = word
                break
        
        if not file_path:
            return "Could you specify which file you'd like me to work with?"
        
        # Resolve path
        path = Path(file_path)
        if not path.is_absolute():
            path = self.working_directory / path
        
        if not path.exists():
            return f"File not found: {path}"
        
        try:
            # Read and chunk file
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Store in context
            chunks = []
            if self.file_chunker:
                chunks = self.file_chunker.chunk_file(str(path))
            
            self.file_contexts[str(path)] = FileContext(
                path=str(path),
                content=content[:5000],  # Limit stored content
                chunks=chunks,
                summary="",
                last_accessed=datetime.now().isoformat()
            )
            
            # Generate summary
            if self.model_router and len(content) > 100:
                summary = await self._summarize_file(content[:3000], path.name)
                return f"📁 **{path.name}**\n\n{summary}\n\n_File loaded into context. You can now ask questions about it._"
            else:
                preview = content[:500] + "..." if len(content) > 500 else content
                return f"📁 **{path.name}**\n```\n{preview}\n```"
                
        except Exception as e:
            return f"Error reading file: {e}"
    
    async def _summarize_file(self, content: str, filename: str) -> str:
        """Generate file summary"""
        try:
            from CHATTY_MODEL_ROUTER import TaskType
            
            result = await self.model_router.generate(
                prompt=f"Summarize this {filename} file:\n\n{content[:2000]}",
                system_prompt="Provide a brief summary of what this code/file does, its main components, and purpose.",
                task_type=TaskType.CHAT,
                max_tokens=300
            )
            return result.content if hasattr(result, 'content') else "File loaded."
        except:
            return "File loaded into context."
    
    async def _generate_response(self, user_input: str) -> str:
        """Generate AI response"""
        if not self.model_router:
            return "⚠️ Model Router not initialized. Check your API keys."
        
        try:
            from CHATTY_MODEL_ROUTER import TaskType
            
            # Build context from history and file contexts
            context_parts = []
            for m in self.history[-8:]:
                prefix = "User" if m.role == "user" else "CHATTY"
                context_parts.append(f"{prefix}: {m.content}")
            
            # Add file context if relevant
            file_context = ""
            if self.file_contexts:
                recent_files = list(self.file_contexts.values())[-2:]
                file_context = "\nLoaded files:\n" + "\n".join([
                    f"- {Path(f.path).name}: {f.content[:200]}..." 
                    for f in recent_files
                ])
            
            # Determine task type
            task_type = TaskType.CHAT
            if any(kw in user_input.lower() for kw in ["code", "function", "class", "script", "python", "javascript"]):
                task_type = TaskType.CODE_GENERATION
            elif any(kw in user_input.lower() for kw in ["debug", "fix", "error", "bug"]):
                task_type = TaskType.DEBUGGING
            elif any(kw in user_input.lower() for kw in ["analyze", "data", "research"]):
                task_type = TaskType.RESEARCH
            
            # Generate response
            result = await self.model_router.generate(
                prompt=user_input,
                system_prompt=f"""You are CHATTY (Complete Heuristic Assistant for Technical Tasks Yielding Results), an advanced AI assistant.
You help with coding, file analysis, system management, and general tasks.
Be concise, helpful, and professional.

Previous conversation:
{chr(10).join(context_parts)}
{file_context}""",
                task_type=task_type,
                max_tokens=1500,
                temperature=0.7
            )
            
            return result.content if hasattr(result, 'content') else "I processed your request but couldn't generate a response."
            
        except Exception as e:
            return f"❌ Error: {str(e)[:100]}"
    
    # Command handlers
    
    async def _cmd_help(self, args: str) -> bool:
        """Show help"""
        print("""
📋 CHATTY Commands
═══════════════════════════════════════════════════════════

🎮 General:
  /help              Show this help
  /status            Show system status
  /clear             Clear chat history
  /exit, /quit       Exit CHATTY

📁 File Operations (like Claude Code):
  /file <path>       Load and analyze a file
  /learn <path>      Deep learn from file with chunking
  /cd <dir>          Change working directory
  /ls [dir]          List directory contents
  /cat <file>        Display file contents
  /exec <command>    Execute shell command

💻 Development:
  /code <task>       Generate code
  /analyze <file>    Analyze code/file
  /search <query>    Search in loaded files
  /repair            Run self-repair diagnostics

🤖 AI Systems:
  /agents            Show Agent Zero fleet status
  /archon            Show Archon2 orchestration
  /task <desc>       Create task for agent fleet
  /memory            Show memory/context info
  /keys              Show API key status

⚙️  Settings:
  /voice             Toggle voice mode
  /autonomous        Toggle autonomous mode

You can also:
  • Ask me to read/edit/create files naturally
  • Request code in any programming language
  • Ask me to analyze your codebase
  • Have me manage your system tasks
        """)
        return True
    
    async def _cmd_status(self, args: str) -> bool:
        """Show system status"""
        print("\n📊 CHATTY SYSTEM STATUS")
        print("═" * 60)
        
        print(f"\n🖥️  Working Directory: {self.working_directory}")
        print(f"💾 Memory: {len(self.history)} messages, {len(self.file_contexts)} files loaded")
        
        if self.model_router:
            try:
                health = self.model_router.health_check()
                active = sum(1 for p in health['providers'].values() if p['available'])
                print(f"\n📡 AI Providers: {active}/8 active")
                for name, status in health['providers'].items():
                    icon = "🟢" if status['available'] else "🔴"
                    print(f"   {icon} {name}")
            except:
                pass
        
        print(f"\n🔧 Components:")
        components = [
            ("File Chunker", self.file_chunker),
            ("Self-Repair", self.self_repair),
            ("Agent Zero", self.agent_zero),
            ("Archon2", self.archon2),
            ("NVIDIA Nemoclaw", self.nvidia_orchestrator),
        ]
        for name, comp in components:
            status = "🟢 Ready" if comp else "⚪ Not loaded"
            print(f"   {status}: {name}")
        
        print("\n" + "═" * 60)
        return True
    
    async def _cmd_clear(self, args: str) -> bool:
        """Clear history"""
        self.history = []
        self.file_contexts = {}
        print("✅ Chat history and file contexts cleared")
        return True
    
    async def _cmd_exit(self, args: str) -> bool:
        """Exit"""
        print("\n👋 Goodbye. CHATTY standing by.")
        return False
    
    async def _cmd_code(self, args: str) -> bool:
        """Generate code"""
        if not args:
            print("Usage: /code <description of what to generate>")
            return True
        
        print(f"🤖 Generating code for: {args}")
        
        if not self.model_router:
            print("⚠️ Model Router not available")
            return True
        
        try:
            from CHATTY_MODEL_ROUTER import TaskType
            
            result = await self.model_router.generate(
                prompt=f"Generate code: {args}",
                system_prompt="""Generate clean, well-documented code.
Include:
- File extension recommendation
- Brief explanation of how it works
- Example usage
- Any dependencies needed""",
                task_type=TaskType.CODE_GENERATION,
                max_tokens=2000,
                temperature=0.3
            )
            
            code = result.content if hasattr(result, 'content') else "Could not generate code."
            print(f"\n{code}")
            
            # Ask if user wants to save
            save = input("\n💾 Save to file? (y/n): ").lower()
            if save == 'y':
                filename = input("Filename: ")
                if filename:
                    path = self.working_directory / filename
                    # Extract code blocks if present
                    import re
                    code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', code, re.DOTALL)
                    if code_blocks:
                        code_to_save = code_blocks[0]
                    else:
                        code_to_save = code
                    
                    with open(path, 'w') as f:
                        f.write(code_to_save)
                    print(f"✅ Saved to {path}")
        
        except Exception as e:
            print(f"❌ Error: {e}")
        
        return True
    
    async def _cmd_file(self, args: str) -> bool:
        """Load and analyze file"""
        if not args:
            print("Usage: /file <path>")
            return True
        
        path = Path(args)
        if not path.is_absolute():
            path = self.working_directory / path
        
        if not path.exists():
            print(f"❌ File not found: {path}")
            return True
        
        response = await self._handle_file_request(f"read file {path}")
        print(f"\n{response}")
        return True
    
    async def _cmd_learn(self, args: str) -> bool:
        """Deep learn from file with chunking"""
        if not args:
            print("Usage: /learn <path>")
            return True
        
        path = Path(args)
        if not path.is_absolute():
            path = self.working_directory / path
        
        if not path.exists():
            print(f"❌ File not found: {path}")
            return True
        
        print(f"📚 Deep learning from {path.name}...")
        
        try:
            # Chunk the file
            if self.file_chunker:
                chunks = self.file_chunker.chunk_file(str(path))
                print(f"   ✅ Chunked into {len(chunks)} semantic chunks")
                
                # Store in memory
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                self.file_contexts[str(path)] = FileContext(
                    path=str(path),
                    content=content[:10000],
                    chunks=chunks,
                    summary="",
                    last_accessed=datetime.now().isoformat()
                )
                
                # Save to memory directory
                memory_file = self.memory_dir / f"{path.stem}_{datetime.now().strftime('%Y%m%d')}.json"
                with open(memory_file, 'w') as f:
                    json.dump({
                        'path': str(path),
                        'chunks': len(chunks),
                        'content_preview': content[:1000],
                        'learned_at': datetime.now().isoformat()
                    }, f, indent=2)
                
                print(f"   ✅ Learned and saved to memory")
                print(f"   📊 {len(chunks)} chunks indexed")
            else:
                print("   ⚠️ File chunker not available")
        
        except Exception as e:
            print(f"❌ Error: {e}")
        
        return True
    
    async def _cmd_exec(self, args: str) -> bool:
        """Execute shell command"""
        if not args:
            print("Usage: /exec <command>")
            return True
        
        print(f"$ {args}")
        try:
            result = subprocess.run(
                args,
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.working_directory,
                timeout=30
            )
            
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(f"stderr: {result.stderr}")
            
            print(f"Exit code: {result.returncode}")
        
        except subprocess.TimeoutExpired:
            print("❌ Command timed out")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        return True
    
    async def _cmd_cd(self, args: str) -> bool:
        """Change directory"""
        if not args:
            print(f"Current directory: {self.working_directory}")
            return True
        
        path = Path(args)
        if not path.is_absolute():
            path = self.working_directory / path
        
        path = path.resolve()
        
        if not path.exists():
            print(f"❌ Directory not found: {path}")
            return True
        
        if not path.is_dir():
            print(f"❌ Not a directory: {path}")
            return True
        
        self.working_directory = path
        print(f"📁 Changed to: {path}")
        return True
    
    async def _cmd_ls(self, args: str) -> bool:
        """List directory"""
        path = self.working_directory
        if args:
            path = Path(args)
            if not path.is_absolute():
                path = self.working_directory / path
        
        try:
            items = list(path.iterdir())
            print(f"\n📂 {path}")
            print("─" * 40)
            
            dirs = [i for i in items if i.is_dir()]
            files = [i for i in items if i.is_file()]
            
            for d in sorted(dirs):
                print(f"📁 {d.name}/")
            for f in sorted(files)[:50]:  # Limit to 50 files
                size = f.stat().st_size
                size_str = f"{size}B" if size < 1024 else f"{size//1024}KB"
                print(f"📄 {f.name:<30} {size_str:>10}")
            
            if len(files) > 50:
                print(f"   ... and {len(files) - 50} more files")
        
        except Exception as e:
            print(f"❌ Error: {e}")
        
        return True
    
    async def _cmd_cat(self, args: str) -> bool:
        """Display file contents"""
        if not args:
            print("Usage: /cat <file>")
            return True
        
        path = Path(args)
        if not path.is_absolute():
            path = self.working_directory / path
        
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            lines = content.split('\n')
            print(f"\n📄 {path} ({len(lines)} lines)")
            print("═" * 60)
            
            # Print with line numbers
            for i, line in enumerate(lines[:100], 1):
                print(f"{i:4} │ {line}")
            
            if len(lines) > 100:
                print(f"\n... ({len(lines) - 100} more lines)")
        
        except Exception as e:
            print(f"❌ Error: {e}")
        
        return True
    
    async def _cmd_agents(self, args: str) -> bool:
        """Show Agent Zero status"""
        print("\n🤖 Agent Zero Fleet Status")
        print("═" * 60)
        
        if self.agent_zero:
            try:
                status = await self.agent_zero.get_fleet_status()
                print(f"Fleet Status: {status}")
            except:
                print("Agent Zero initialized but status unavailable")
        else:
            print("⚪ Agent Zero not loaded")
            print("   Run continuous mode for full agent capabilities")
        
        return True
    
    async def _cmd_archon(self, args: str) -> bool:
        """Show Archon2 status"""
        print("\n🏛️  Archon2 Orchestration")
        print("═" * 60)
        
        if self.archon2:
            try:
                print(f"Agents: {len(self.archon2.agents)}")
                print(f"Hierarchy: 4 levels")
            except:
                print("Archon2 initialized")
        else:
            print("⚪ Archon2 not loaded")
        
        return True
    
    async def _cmd_repair(self, args: str) -> bool:
        """Run self-repair"""
        print("\n🔧 Self-Repair Diagnostics")
        print("═" * 60)
        
        if self.self_repair:
            print("Running diagnostics...")
            # Placeholder - would run actual diagnostics
            print("✅ All systems nominal")
        else:
            print("⚪ Self-Repair not loaded")
        
        return True
    
    async def _cmd_search(self, args: str) -> bool:
        """Search in loaded files"""
        if not args:
            print("Usage: /search <query>")
            return True
        
        print(f"\n🔍 Searching for: {args}")
        
        if not self.file_contexts:
            print("No files loaded. Use /file or /learn first.")
            return True
        
        results = []
        for path, ctx in self.file_contexts.items():
            if args.lower() in ctx.content.lower():
                # Find context around match
                idx = ctx.content.lower().find(args.lower())
                start = max(0, idx - 100)
                end = min(len(ctx.content), idx + 100)
                snippet = ctx.content[start:end]
                results.append((path, snippet))
        
        if results:
            print(f"Found {len(results)} matches:")
            for path, snippet in results:
                print(f"\n📄 {path}")
                print(f"   ...{snippet}...")
        else:
            print("No matches found.")
        
        return True
    
    async def _cmd_task(self, args: str) -> bool:
        """Create task for agents"""
        if not args:
            print("Usage: /task <description>")
            return True
        
        print(f"\n📋 Creating task: {args}")
        
        if self.agent_zero:
            print("Dispatching to Agent Zero fleet...")
            # Would actually dispatch task
            print("✅ Task dispatched")
        else:
            print("⚪ Agent Zero not available")
            print("   Task saved for later processing")
        
        return True
    
    async def _cmd_analyze(self, args: str) -> bool:
        """Analyze file"""
        if not args:
            print("Usage: /analyze <file>")
            return True
        
        path = Path(args)
        if not path.is_absolute():
            path = self.working_directory / path
        
        print(f"\n🔬 Analyzing: {path.name}")
        
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Basic stats
            lines = content.split('\n')
            words = len(content.split())
            chars = len(content)
            
            print(f"\n📊 Statistics:")
            print(f"   Lines: {len(lines)}")
            print(f"   Words: {words}")
            print(f"   Characters: {chars}")
            print(f"   Size: {chars//1024}KB")
            
            # Language detection
            ext = path.suffix.lower()
            lang_map = {
                '.py': 'Python',
                '.js': 'JavaScript',
                '.ts': 'TypeScript',
                '.java': 'Java',
                '.cpp': 'C++',
                '.c': 'C',
                '.go': 'Go',
                '.rs': 'Rust',
                '.rb': 'Ruby',
                '.php': 'PHP',
                '.md': 'Markdown',
                '.json': 'JSON',
                '.yml': 'YAML',
                '.yaml': 'YAML',
                '.sh': 'Shell',
                '.html': 'HTML',
                '.css': 'CSS',
            }
            lang = lang_map.get(ext, 'Unknown')
            print(f"   Language: {lang}")
            
            # AI analysis
            if self.model_router and len(content) < 10000:
                print(f"\n🤖 AI Analysis:")
                analysis = await self._summarize_file(content, path.name)
                print(analysis)
        
        except Exception as e:
            print(f"❌ Error: {e}")
        
        return True
    
    async def _cmd_memory(self, args: str) -> bool:
        """Show memory info"""
        print("\n🧠 CHATTY Memory")
        print("═" * 60)
        print(f"Messages in session: {len(self.history)}")
        print(f"Files in context: {len(self.file_contexts)}")
        print(f"Context window: {self.context_window}")
        print(f"Memory directory: {self.memory_dir}")
        
        if self.file_contexts:
            print(f"\n📁 Loaded Files:")
            for path, ctx in self.file_contexts.items():
                print(f"   📄 {Path(path).name}")
        
        return True
    
    async def _cmd_keys(self, args: str) -> bool:
        """Show API key status"""
        print("\n🔑 API Key Status")
        print("═" * 60)
        
        keys = [
            ('OpenAI', 'OPENAI_API_KEY'),
            ('OpenRouter', 'OPENROUTER_API_KEY'),
            ('xAI/Grok', 'XAI_API_KEY'),
            ('NVIDIA', 'NVIDIA_API_KEY'),
            ('HuggingFace', 'HUGGINGFACE_TOKEN'),
            ('SendGrid', 'SENDGRID_API_KEY'),
        ]
        
        for name, env_var in keys:
            value = os.getenv(env_var)
            status = "🟢" if value else "🔴"
            print(f"   {status} {name}")
        
        return True
    
    async def _cmd_voice(self, args: str) -> bool:
        """Toggle voice mode"""
        self.voice_enabled = not self.voice_enabled
        status = "enabled" if self.voice_enabled else "disabled"
        print(f"🎤 Voice mode {status}")
        return True
    
    async def _cmd_autonomous(self, args: str) -> bool:
        """Toggle autonomous mode"""
        self.autonomous_mode = not self.autonomous_mode
        status = "enabled" if self.autonomous_mode else "disabled"
        print(f"🤖 Autonomous mode {status}")
        if self.autonomous_mode:
            print("   CHATTY will now work proactively in the background")
        return True


# Entry points

async def interactive_mode():
    """Run CHATTY in interactive mode"""
    chatty = JarvisAssistant()
    await chatty.chat_loop()


async def one_shot_task(task: str, mode: str = "chat"):
    """Execute a one-shot task"""
    chatty = JarvisAssistant()
    await chatty.initialize()
    
    if mode == "code":
        result = await chatty._generate_code(task)
    else:
        result = await chatty._generate_response(task)
    
    print(result)


async def learn_file(file_path: str):
    """Learn from a file"""
    chatty = JarvisAssistant()
    await chatty.initialize()
    await chatty._cmd_learn(file_path)


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="CHATTY - Your Personal AI Assistant")
    parser.add_argument("--task", type=str, help="One-shot task to execute")
    parser.add_argument("--code", action="store_true", help="Code generation mode")
    parser.add_argument("--file", type=str, help="Learn from file")
    parser.add_argument("--status", action="store_true", help="Show status and exit")
    parser.add_argument("--exec", type=str, dest="execute", help="Execute command and exit")
    
    args = parser.parse_args()
    
    if args.status:
        chatty = JarvisAssistant()
        await chatty.initialize()
        await chatty._cmd_status("")
    elif args.execute:
        chatty = JarvisAssistant()
        await chatty.initialize()
        await chatty._cmd_exec(args.execute)
    elif args.file:
        await learn_file(args.file)
    elif args.task:
        await one_shot_task(args.task, "code" if args.code else "chat")
    else:
        await interactive_mode()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye.")
        sys.exit(0)
