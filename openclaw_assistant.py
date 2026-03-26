#!/usr/bin/env python3
"""
OPENCLAW INTERACTIVE ASSISTANT
Your AI companion that can handle anything - code, analysis, automation, and more.

Usage:
    ./openclaw                    # Start interactive chat
    ./openclaw --task "..."       # One-shot task
    ./openclaw --code "..."       # Code generation mode
    ./openclaw --status           # Show system status
"""

import os
import sys
import asyncio
import json
import readline
import atexit
import aiohttp
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

# Load environment
load_dotenv()
_secrets = os.getenv("CHATTY_SECRETS_FILE")
if _secrets:
    load_dotenv(os.path.expanduser(_secrets))

sys.path.insert(0, str(Path(__file__).parent))

@dataclass
class ChatMessage:
    role: str
    content: str
    timestamp: str
    metadata: Optional[Dict] = None


class OpenClawAssistant:
    """Interactive OpenClaw Assistant with direct API integration"""
    
    def __init__(self):
        self.history: List[ChatMessage] = []
        self.history_file = Path.home() / ".openclaw_history"
        self.session_file = Path.home() / ".openclaw_session"
        self.context_window = 30
        
        # API configurations
        self.api_configs = {
            "nvidia": {
                "url": "https://integrate.api.nvidia.com/v1/chat/completions",
                "key": os.getenv("NVIDIA_API_KEY"),
                "model": "moonshotai/kimi-k2.5",
                "headers": lambda key: {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
            },
            "openai": {
                "url": "https://api.openai.com/v1/chat/completions",
                "key": os.getenv("OPENAI_API_KEY"),
                "model": "gpt-4o-mini",
                "headers": lambda key: {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
            },
            "xai": {
                "url": "https://api.x.ai/v1/chat/completions",
                "key": os.getenv("XAI_API_KEY"),
                "model": "grok-3",
                "headers": lambda key: {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
            },
            "openrouter": {
                "url": "https://openrouter.ai/api/v1/chat/completions",
                "key": os.getenv("OPENROUTER_API_KEY"),
                "model": "meta-llama/llama-3.2-3b-instruct:free",
                "headers": lambda key: {
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://chatty.ai",
                    "X-Title": "OpenClaw Assistant"
                }
            }
        }
        
        # Systems (lazy loaded)
        self._file_chunker = None
        self._memory_system = None
        
        # Load history
        self._load_history()
        self._setup_readline()
        
        # Stats
        self.stats = {
            "messages_exchanged": 0,
            "files_chunked": [],
            "tasks_completed": 0,
            "session_start": datetime.now().isoformat()
        }
    
    def _setup_readline(self):
        """Setup command history and tab completion"""
        if self.history_file.exists():
            try:
                readline.read_history_file(str(self.history_file))
            except Exception:
                pass
        atexit.register(self._save_history)
        
        commands = [
            "/help", "/status", "/clear", "/exit", "/quit",
            "/code", "/analyze", "/chunk", "/debug",
            "/memory", "/models", "/task", "/file", "/reset"
        ]
        readline.set_completer(lambda text, state: 
            ([c for c in commands if c.startswith(text)] + [None])[state])
        readline.parse_and_bind("tab: complete")
    
    def _load_history(self):
        """Load chat history"""
        if self.session_file.exists():
            try:
                with open(self.session_file) as f:
                    data = json.load(f)
                    self.history = [ChatMessage(**m) for m in data.get("messages", [])]
            except Exception:
                pass
    
    def _save_history(self):
        """Save command history"""
        try:
            readline.write_history_file(str(self.history_file))
        except Exception:
            pass
    
    def _save_session(self):
        """Save chat session"""
        try:
            with open(self.session_file, 'w') as f:
                json.dump({
                    "messages": [asdict(m) for m in self.history[-self.context_window:]],
                    "stats": self.stats,
                    "last_updated": datetime.now().isoformat()
                }, f, indent=2, default=str)
        except Exception as e:
            print(f"⚠️  Could not save session: {e}")
    
    @property
    def file_chunker(self):
        """Lazy load file chunker"""
        if self._file_chunker is None:
            try:
                from openclaw_integration import FileChunker
                self._file_chunker = FileChunker()
            except Exception as e:
                print(f"⚠️  File Chunker error: {e}")
        return self._file_chunker
    
    async def call_llm(self, prompt: str, system_prompt: str = "", max_tokens: int = 2000, temperature: float = 0.7) -> Dict[str, Any]:
        """Call LLM with automatic provider failover"""
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": "placeholder",
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        # Try providers in order of preference
        provider_order = ["xai", "openai", "openrouter", "nvidia"]
        
        async with aiohttp.ClientSession() as session:
            for provider_name in provider_order:
                config = self.api_configs.get(provider_name)
                if not config or not config["key"]:
                    continue
                
                try:
                    payload["model"] = config["model"]
                    headers = config["headers"](config["key"])
                    
                    timeout = aiohttp.ClientTimeout(total=60)
                    
                    async with session.post(
                        config["url"],
                        headers=headers,
                        json=payload,
                        timeout=timeout
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                            return {
                                "success": True,
                                "content": content,
                                "provider": provider_name,
                                "model": config["model"]
                            }
                        else:
                            error_text = await response.text()
                            print(f"  ⚠️  {provider_name} failed: HTTP {response.status}")
                            
                except asyncio.TimeoutError:
                    print(f"  ⚠️  {provider_name} timed out")
                except Exception as e:
                    print(f"  ⚠️  {provider_name} error: {str(e)[:50]}")
        
        return {"success": False, "error": "All providers failed", "content": ""}
    
    async def initialize(self):
        """Initialize the assistant"""
        print("🔧 Initializing OpenClaw Assistant...")
        print()
        
        # Check API keys
        available = [name for name, config in self.api_configs.items() if config["key"]]
        if available:
            print(f"   ✅ API Keys: {', '.join(available)}")
        else:
            print("   ⚠️  No API keys found. Set them in .env file.")
        
        print()
        print("🚀 OpenClaw Assistant ready!")
        print("   Type /help for commands or just start chatting.")
        print()
    
    def print_banner(self):
        """Print welcome banner"""
        print("""
╔═══════════════════════════════════════════════════════════════════════╗
║                    🔧 OPENCLAW INTERACTIVE ASSISTANT                   ║
║                        Your AI Companion                              ║
╠═══════════════════════════════════════════════════════════════════════╣
║  Capabilities:                                                        ║
║    💻 Code generation, analysis & debugging                          ║
║    📁 File chunking & semantic understanding                         ║
║    🧠 Multi-LLM routing (Grok, Claude, GPT-4, Kimi K2.5)             ║
║    🎯 Autonomous task execution                                      ║
╚═══════════════════════════════════════════════════════════════════════╝
        """)
    
    async def chat_loop(self):
        """Main chat loop"""
        self.print_banner()
        await self.initialize()
        
        while True:
            try:
                user_input = input("\n💬 You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.startswith("/"):
                    if await self._handle_command(user_input):
                        continue
                
                self.history.append(ChatMessage(
                    role="user",
                    content=user_input,
                    timestamp=datetime.now().isoformat()
                ))
                
                response = await self._generate_response(user_input)
                
                self.history.append(ChatMessage(
                    role="assistant",
                    content=response,
                    timestamp=datetime.now().isoformat()
                ))
                
                print(f"\n🤖 OpenClaw: {response}")
                
                self._save_session()
                self.stats["messages_exchanged"] += 2
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except EOFError:
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
    
    async def _handle_command(self, command: str) -> bool:
        """Handle slash commands"""
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if cmd in ["/exit", "/quit"]:
            print("\n👋 Goodbye!")
            sys.exit(0)
        
        elif cmd == "/help":
            print("""
📋 Available Commands:
  /help              Show this help
  /status            Show system status
  /clear             Clear chat history
  /exit, /quit       Exit the assistant

💻 Development:
  /code <desc>       Generate code
  /analyze <file>    Analyze a code file
  /debug <desc>      Debug an issue
  /chunk <file>      Chunk and analyze a file

🧠 AI Systems:
  /memory            Show memory info
  /models            Show available AI models
  /task <desc>       Create autonomous task

📁 File Operations:
  /file <path>       Load file into context
            """)
        
        elif cmd == "/status":
            await self._show_status()
        
        elif cmd == "/clear":
            self.history = []
            print("✅ Chat history cleared")
        
        elif cmd == "/memory":
            print(f"🧠 Memory:")
            print(f"   Messages in session: {len(self.history)}")
            print(f"   Context window: {self.context_window}")
            print(f"   Files chunked: {len(self.stats['files_chunked'])}")
            print(f"   Tasks completed: {self.stats['tasks_completed']}")
        
        elif cmd == "/models":
            await self._show_models()
        
        elif cmd == "/code":
            if args:
                response = await self._generate_code(args)
                print(f"\n🤖 OpenClaw:\n{response}")
            else:
                print("Usage: /code <description of what to generate>")
        
        elif cmd == "/analyze":
            if args:
                await self._analyze_file(args)
            else:
                print("Usage: /analyze <file_path>")
        
        elif cmd == "/chunk":
            if args:
                await self._chunk_file(args)
            else:
                print("Usage: /chunk <file_path>")
        
        elif cmd == "/debug":
            if args:
                response = await self._debug_issue(args)
                print(f"\n🤖 OpenClaw:\n{response}")
            else:
                print("Usage: /debug <description of the issue>")
        
        elif cmd == "/task":
            if args:
                await self._create_task(args)
            else:
                print("Usage: /task <task description>")
        
        elif cmd == "/file":
            if args:
                await self._load_file(args)
            else:
                print("Usage: /file <file_path>")
        
        elif cmd == "/reset":
            self.history = []
            self.stats = {
                "messages_exchanged": 0,
                "files_chunked": [],
                "tasks_completed": 0,
                "session_start": datetime.now().isoformat()
            }
            print("✅ Session reset")
        
        else:
            print(f"❓ Unknown command: {cmd}. Type /help for available commands.")
        
        return True
    
    async def _show_status(self):
        """Show comprehensive system status"""
        print("\n📊 OPENCLAW SYSTEM STATUS")
        print("=" * 60)
        
        # API Keys
        print("\n🔑 API Keys:")
        for name, config in self.api_configs.items():
            key = config["key"]
            status = "✅" if key else "❌"
            masked = f"{key[:8]}...{key[-4:]}" if key and len(key) > 12 else ("set" if key else "not set")
            print(f"   {status} {name}: {masked}")
        
        # Session stats
        print(f"\n📈 Session Stats:")
        print(f"   Messages exchanged: {self.stats['messages_exchanged']}")
        print(f"   Files chunked: {len(self.stats['files_chunked'])}")
        print(f"   Tasks completed: {self.stats['tasks_completed']}")
        
        print("\n" + "=" * 60)
    
    async def _show_models(self):
        """Show available AI models"""
        print("\n🧠 Available AI Models:")
        print("=" * 60)
        
        models = {
            "NVIDIA (Free)": "moonshotai/kimi-k2.5 (1T params, 256K context)",
            "xAI Grok": "grok-3",
            "OpenAI": "gpt-4o-mini",
            "OpenRouter": "meta-llama/llama-3.2-3b-instruct (free)",
        }
        
        for provider, model in models.items():
            config = self.api_configs.get(provider.lower().split()[0])
            status = "✅" if config and config["key"] else "❌"
            print(f"   {status} {provider}: {model}")
        
        print("\n" + "=" * 60)
        print("Models are selected automatically with failover.")
    
    async def _generate_response(self, user_input: str) -> str:
        """Generate AI response"""
        # Build context from history
        context = ""
        if len(self.history) > 1:
            recent = self.history[-10:-1]
            context = "\n".join([
                f"{'User' if m.role == 'user' else 'Assistant'}: {m.content[:200]}"
                for m in recent
            ])
        
        # Determine task type for system prompt
        input_lower = user_input.lower()
        code_keywords = ["code", "function", "class", "script", "python", "javascript", "api", "write a program"]
        debug_keywords = ["debug", "fix", "error", "bug", "exception", "traceback", "not working"]
        
        if any(kw in input_lower for kw in code_keywords):
            system_prompt = "You are an expert programmer. Provide clear, well-commented code with explanations."
        elif any(kw in input_lower for kw in debug_keywords):
            system_prompt = "You are a debugging expert. Help identify issues and provide solutions."
        else:
            system_prompt = "You are OpenClaw, a helpful AI assistant. Be concise and helpful."
        
        if context:
            system_prompt += f"\n\nPrevious context:\n{context}"
        
        print("🤔 Thinking...", end="\r")
        
        result = await self.call_llm(
            prompt=user_input,
            system_prompt=system_prompt,
            max_tokens=2000,
            temperature=0.7
        )
        
        print(" " * 20, end="\r")
        
        if result["success"]:
            return result["content"]
        else:
            return f"⚠️ Sorry, I couldn't generate a response. {result.get('error', 'Unknown error')}"
    
    async def _generate_code(self, description: str) -> str:
        """Generate code with proper formatting"""
        print("💻 Generating code...", end="\r")
        
        result = await self.call_llm(
            prompt=f"Generate code for: {description}",
            system_prompt="""You are an expert code generator. Generate clean, production-ready code with:
- Clear comments explaining key logic
- Error handling where appropriate
- Type hints (for Python)
- Best practices for the language
- Brief explanation of how to use the code

Provide the code in a markdown code block with the appropriate language tag.""",
            max_tokens=3000,
            temperature=0.3
        )
        
        print(" " * 25, end="\r")
        
        if result["success"]:
            self.stats["tasks_completed"] += 1
            return result["content"]
        else:
            return f"⚠️ Could not generate code. {result.get('error', 'Unknown error')}"
    
    async def _analyze_file(self, file_path: str):
        """Analyze a file using OpenClaw chunking"""
        path = Path(file_path).expanduser()
        
        if not path.exists():
            print(f"❌ File not found: {file_path}")
            return
        
        chunker = self.file_chunker
        if not chunker:
            # Fallback: just read the file
            try:
                content = path.read_text(encoding='utf-8', errors='ignore')
                print(f"📁 Analyzing {path.name} ({len(content)} chars)...")
                
                print("🧠 Generating AI analysis...")
                result = await self.call_llm(
                    prompt=f"Analyze this code/file:\n\n```\n{content[:3000]}\n```",
                    system_prompt="""Analyze the provided code/file. Provide:
1. Brief summary of what it does
2. Key components/functions
3. Potential issues or improvements
4. Overall quality assessment

Be concise but thorough.""",
                    max_tokens=1500,
                    temperature=0.3
                )
                
                if result["success"]:
                    print(f"\n🤖 Analysis:\n{result['content']}")
                else:
                    print(f"⚠️ Analysis failed: {result.get('error', 'Unknown')}")
            except Exception as e:
                print(f"❌ Error reading file: {e}")
            return
        
        print(f"📁 Analyzing {path.name}...")
        
        try:
            chunks = chunker.chunk_file(str(path))
            
            if not chunks:
                print("❌ Could not chunk file")
                return
            
            self.stats["files_chunked"].append(str(path))
            
            print(f"✅ File chunked into {len(chunks)} semantic sections")
            print(f"\n📊 Analysis:")
            print(f"   Total chunks: {len(chunks)}")
            print(f"   File type: {path.suffix}")
            
            for i, chunk in enumerate(chunks[:3]):
                print(f"\n   Chunk {i+1}:")
                print(f"      Lines: {chunk.get('start_line', '?')} - {chunk.get('end_line', '?')}")
                content_preview = chunk.get('content', '')[:100].replace('\n', ' ')
                print(f"      Preview: {content_preview}...")
            
            if len(chunks) > 3:
                print(f"\n   ... and {len(chunks) - 3} more chunks")
            
            # Generate AI analysis
            print("\n🧠 Generating AI analysis...")
            combined = "\n\n".join([
                f"=== Section {i+1} ===\n{c['content'][:500]}"
                for i, c in enumerate(chunks[:5])
            ])
            
            result = await self.call_llm(
                prompt=f"Analyze this code/file:\n\n{combined}",
                system_prompt="""Analyze the provided code/file. Provide:
1. Brief summary of what it does
2. Key components/functions
3. Potential issues or improvements
4. Overall quality assessment

Be concise but thorough.""",
                max_tokens=1500,
                temperature=0.3
            )
            
            if result["success"]:
                print(f"\n🤖 Analysis:\n{result['content']}")
            else:
                print(f"⚠️ Analysis failed: {result.get('error', 'Unknown')}")
                
        except Exception as e:
            print(f"❌ Error analyzing file: {e}")
    
    async def _chunk_file(self, file_path: str):
        """Chunk a file and show detailed output"""
        path = Path(file_path).expanduser()
        
        if not path.exists():
            print(f"❌ File not found: {file_path}")
            return
        
        chunker = self.file_chunker
        if not chunker:
            print("⚠️ File Chunker not available")
            return
        
        print(f"🔧 Chunking {path.name}...")
        
        try:
            chunks = chunker.chunk_file(str(path))
            
            if chunks:
                self.stats["files_chunked"].append(str(path))
                print(f"✅ Created {len(chunks)} chunks")
                
                for i, chunk in enumerate(chunks[:10]):
                    print(f"\n   Chunk {i+1}:")
                    print(f"      Type: {chunk.get('type', 'unknown')}")
                    print(f"      Lines: {chunk.get('start_line', '?')} - {chunk.get('end_line', '?')}")
                    print(f"      Size: {len(chunk.get('content', ''))} chars")
                
                if len(chunks) > 10:
                    print(f"\n   ... and {len(chunks) - 10} more chunks")
            else:
                print("❌ No chunks created")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def _debug_issue(self, description: str) -> str:
        """Debug an issue"""
        print("🔍 Debugging...", end="\r")
        
        result = await self.call_llm(
            prompt=f"Debug this issue:\n{description}",
            system_prompt="""You are a debugging expert. Help identify and fix the issue:
1. Identify the root cause
2. Provide a solution
3. Show example fix if applicable
4. Suggest preventive measures

Be thorough and practical.""",
            max_tokens=2000,
            temperature=0.3
        )
        
        print(" " * 15, end="\r")
        
        if result["success"]:
            self.stats["tasks_completed"] += 1
            return result["content"]
        else:
            return f"⚠️ Could not analyze. {result.get('error', 'Unknown error')}"
    
    async def _create_task(self, description: str):
        """Create an autonomous task"""
        print(f"📋 Task: {description}")
        print("   This would be dispatched to the agent fleet for execution.")
        print("   Use /code or regular chat for immediate results.")
        self.stats["tasks_completed"] += 1
    
    async def _load_file(self, file_path: str):
        """Load file content into conversation context"""
        path = Path(file_path).expanduser()
        
        if not path.exists():
            print(f"❌ File not found: {file_path}")
            return
        
        try:
            content = path.read_text(encoding='utf-8', errors='ignore')
            
            self.history.append(ChatMessage(
                role="system",
                content=f"File loaded: {path.name}\n```\n{content[:2000]}\n```",
                timestamp=datetime.now().isoformat()
            ))
            
            print(f"✅ Loaded {path.name} ({len(content)} chars)")
            print(f"   First 2000 characters added to context")
            
        except Exception as e:
            print(f"❌ Error loading file: {e}")
    
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
    
    parser = argparse.ArgumentParser(description="OpenClaw Interactive Assistant")
    parser.add_argument("--task", type=str, help="One-shot task to execute")
    parser.add_argument("--code", action="store_true", help="Code generation mode")
    parser.add_argument("--status", action="store_true", help="Show status and exit")
    
    args = parser.parse_args()
    
    assistant = OpenClawAssistant()
    
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
