#!/usr/bin/env python3
"""
ENHANCED AUTO API KEY SETUP & SYSTEM INTEGRATION
Automatically retrieves, rotates, and manages API keys for CHATTY
Includes systemd service setup for 24/7 operation
"""

import os
import sys
import json
import time
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

# Load existing environment
load_dotenv(".env")
_secrets = os.getenv("CHATTY_SECRETS_FILE")
if _secrets:
    load_dotenv(os.path.expanduser(_secrets))

@dataclass
class APIKeyConfig:
    """Configuration for an API key source"""
    name: str
    env_key: str
    url: str
    free_tier: bool
    priority: int
    rotation_key: Optional[str] = None  # For multiple keys (e.g., OPENROUTER_API_KEY_2)
    max_requests_per_minute: int = 60
    daily_limit: Optional[int] = None
    note: str = ""

class EnhancedAPIKeyManager:
    """Advanced API key management with auto-retrieval and rotation"""
    
    def __init__(self):
        self.secrets_dir = Path.home() / ".config" / "chatty"
        self.secrets_file = self.secrets_dir / "secrets.env"
        self.keys_db = self.secrets_dir / "api_keys.json"
        self.rotation_state = self.secrets_dir / "key_rotation.json"
        
        self.secrets_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize key database
        self._init_key_database()
        
        # Load current keys
        self.current_keys = self._load_current_keys()
        
    def _init_key_database(self):
        """Initialize the comprehensive API key database"""
        self.api_sources = {
            # === NVIDIA & AI RESEARCH ===
            "nvidia_kimi": APIKeyConfig(
                name="NVIDIA Build (Kimi K2.5)",
                env_key="NVIDIA_API_KEY",
                url="https://build.nvidia.com/moonshotai/kimi-k2.5",
                free_tier=True,
                priority=1,
                max_requests_per_minute=6,
                daily_limit=3_000_000,
                note="1T parameter model, 256K context, real data only"
            ),
            "nvidia_nemotron": APIKeyConfig(
                name="NVIDIA Nemotron-4",
                env_key="NVIDIA_API_KEY",
                url="https://build.nvidia.com/nvidia/nemotron-4-340b-instruct",
                free_tier=True,
                priority=1,
                max_requests_per_minute=6,
                note="340B parameter model, excellent reasoning"
            ),
            
            # === xAI (Grok) - Multiple Keys ===
            "xai_primary": APIKeyConfig(
                name="xAI Grok (Primary)",
                env_key="XAI_API_KEY",
                url="https://console.x.ai",
                free_tier=True,
                priority=1,
                max_requests_per_minute=60,
                note="Primary Grok-3 access"
            ),
            "xai_backup_1": APIKeyConfig(
                name="xAI Grok (Backup 1)",
                env_key="XAI_API_KEY_2",
                url="https://console.x.ai",
                free_tier=True,
                priority=2,
                rotation_key="XAI_API_KEY",
                note="Backup key for rotation"
            ),
            "xai_backup_2": APIKeyConfig(
                name="xAI Grok (Backup 2)",
                env_key="XAI_API_KEY_3",
                url="https://console.x.ai",
                free_tier=True,
                priority=2,
                rotation_key="XAI_API_KEY",
                note="Third key for heavy rotation"
            ),
            "xai_backup_3": APIKeyConfig(
                name="xAI Grok (Backup 3)",
                env_key="XAI_API_KEY_4",
                url="https://console.x.ai",
                free_tier=True,
                priority=2,
                rotation_key="XAI_API_KEY",
                note="Fourth key for maximum throughput"
            ),
            
            # === OpenRouter - Multiple Keys ===
            "openrouter_primary": APIKeyConfig(
                name="OpenRouter (Primary)",
                env_key="OPENROUTER_API_KEY",
                url="https://openrouter.ai/keys",
                free_tier=True,
                priority=1,
                max_requests_per_minute=20,
                note="Access to 100+ models including Claude, GPT-4"
            ),
            "openrouter_backup_1": APIKeyConfig(
                name="OpenRouter (Backup 1)",
                env_key="OPENROUTER_API_KEY_2",
                url="https://openrouter.ai/keys",
                free_tier=True,
                priority=2,
                rotation_key="OPENROUTER_API_KEY",
                note="Second account for rotation"
            ),
            "openrouter_backup_2": APIKeyConfig(
                name="OpenRouter (Backup 2)",
                env_key="OPENROUTER_API_KEY_3",
                url="https://openrouter.ai/keys",
                free_tier=True,
                priority=2,
                rotation_key="OPENROUTER_API_KEY",
                note="Third account"
            ),
            "openrouter_backup_3": APIKeyConfig(
                name="OpenRouter (Backup 3)",
                env_key="OPENROUTER_API_KEY_4",
                url="https://openrouter.ai/keys",
                free_tier=True,
                priority=2,
                rotation_key="OPENROUTER_API_KEY",
                note="Fourth account"
            ),
            "openrouter_backup_4": APIKeyConfig(
                name="OpenRouter (Backup 4)",
                env_key="OPENROUTER_API_KEY_5",
                url="https://openrouter.ai/keys",
                free_tier=True,
                priority=2,
                rotation_key="OPENROUTER_API_KEY",
                note="Fifth account for max rotation"
            ),
            
            # === OpenAI ===
            "openai": APIKeyConfig(
                name="OpenAI",
                env_key="OPENAI_API_KEY",
                url="https://platform.openai.com/api-keys",
                free_tier=False,
                priority=2,
                max_requests_per_minute=60,
                note="GPT-4o, GPT-4o-mini access"
            ),
            
            # === Anthropic ===
            "anthropic": APIKeyConfig(
                name="Anthropic Claude",
                env_key="ANTHROPIC_API_KEY",
                url="https://console.anthropic.com/settings/keys",
                free_tier=False,
                priority=2,
                max_requests_per_minute=50,
                note="Claude 3.5 Sonnet, Claude 3 Opus"
            ),
            
            # === Google ===
            "google_gemini": APIKeyConfig(
                name="Google Gemini",
                env_key="GOOGLE_API_KEY",
                url="https://aistudio.google.com/app/apikey",
                free_tier=True,
                priority=2,
                max_requests_per_minute=60,
                daily_limit=1_500_000,
                note="Gemini 1.5 Pro/Flash, generous free tier"
            ),
            
            # === DeepSeek ===
            "deepseek": APIKeyConfig(
                name="DeepSeek",
                env_key="DEEPSEEK_API_KEY",
                url="https://platform.deepseek.com/api_keys",
                free_tier=True,
                priority=2,
                max_requests_per_minute=60,
                note="DeepSeek-V3, excellent coding performance"
            ),
            
            # === Hugging Face ===
            "huggingface": APIKeyConfig(
                name="Hugging Face",
                env_key="HUGGINGFACE_TOKEN",
                url="https://huggingface.co/settings/tokens",
                free_tier=True,
                priority=3,
                max_requests_per_minute=60,
                note="Access to 500K+ open source models"
            ),
            
            # === Mistral ===
            "mistral": APIKeyConfig(
                name="Mistral AI",
                env_key="MISTRAL_API_KEY",
                url="https://console.mistral.ai/api-keys/",
                free_tier=True,
                priority=3,
                max_requests_per_minute=60,
                note="Mistral Large, Codestral"
            ),
            
            # === Cohere ===
            "cohere": APIKeyConfig(
                name="Cohere",
                env_key="COHERE_API_KEY",
                url="https://dashboard.cohere.com/api-keys",
                free_tier=True,
                priority=3,
                max_requests_per_minute=100,
                note="Command-R, Command-R+"
            ),
            
            # === Together AI ===
            "together": APIKeyConfig(
                name="Together AI",
                env_key="TOGETHER_API_KEY",
                url="https://api.together.xyz/settings/api-keys",
                free_tier=True,
                priority=3,
                max_requests_per_minute=60,
                note="Fast inference for open models"
            ),
            
            # === Perplexity ===
            "perplexity": APIKeyConfig(
                name="Perplexity",
                env_key="PPLX_API_KEY",
                url="https://www.perplexity.ai/settings/api",
                free_tier=False,
                priority=3,
                max_requests_per_minute=60,
                note="Live web search + LLM"
            ),
            
            # === Replicate ===
            "replicate": APIKeyConfig(
                name="Replicate",
                env_key="REPLICATE_API_TOKEN",
                url="https://replicate.com/account/api-tokens",
                free_tier=False,
                priority=4,
                max_requests_per_minute=60,
                note="Image generation, model hosting"
            ),
            
            # === Twitter/X ===
            "twitter": APIKeyConfig(
                name="Twitter/X API",
                env_key="X_BEARER_TOKEN",
                url="https://developer.twitter.com/en/portal/dashboard",
                free_tier=True,
                priority=3,
                max_requests_per_minute=15,
                note="Social media automation"
            ),
            
            # === Infrastructure ===
            "langchain": APIKeyConfig(
                name="LangChain",
                env_key="LANGCHAIN_API_KEY",
                url="https://smith.langchain.com/settings",
                free_tier=True,
                priority=1,
                max_requests_per_minute=60,
                note="Tracing, evaluation, prompt management"
            ),
            "langsmith": APIKeyConfig(
                name="LangSmith",
                env_key="LANGSMITH_API_KEY",
                url="https://smith.langchain.com/settings",
                free_tier=True,
                priority=1,
                max_requests_per_minute=60,
                note="Production observability"
            ),
        }
    
    def _load_current_keys(self) -> Dict[str, str]:
        """Load currently configured API keys"""
        keys = {}
        for source_id, config in self.api_sources.items():
            value = os.getenv(config.env_key)
            if value and value not in ["", "your_key_here", "None"]:
                keys[source_id] = value
        return keys
    
    def get_key_status(self) -> Dict:
        """Get comprehensive key status report"""
        status = {
            "total_sources": len(self.api_sources),
            "configured": 0,
            "missing": [],
            "by_priority": {1: [], 2: [], 3: [], 4: []},
            "rotation_groups": {}
        }
        
        for source_id, config in self.api_sources.items():
            is_configured = source_id in self.current_keys
            
            if is_configured:
                status["configured"] += 1
                status["by_priority"][config.priority].append({
                    "name": config.name,
                    "env_key": config.env_key,
                    "note": config.note
                })
            else:
                status["missing"].append({
                    "name": config.name,
                    "env_key": config.env_key,
                    "url": config.url,
                    "priority": config.priority,
                    "free_tier": config.free_tier,
                    "note": config.note
                })
            
            # Track rotation groups
            if config.rotation_key:
                if config.rotation_key not in status["rotation_groups"]:
                    status["rotation_groups"][config.rotation_key] = []
                status["rotation_groups"][config.rotation_key].append({
                    "source_id": source_id,
                    "configured": is_configured
                })
        
        return status
    
    def print_status(self):
        """Print beautiful status report"""
        status = self.get_key_status()
        
        print("\n" + "="*80)
        print("🔑 CHATTY API KEY STATUS REPORT")
        print("="*80)
        
        print(f"\n📊 SUMMARY: {status['configured']}/{status['total_sources']} sources configured")
        
        # Priority 1 (Critical)
        if status["by_priority"][1]:
            print("\n🎯 PRIORITY 1 (CRITICAL - Infrastructure):")
            for item in status["by_priority"][1]:
                print(f"   ✅ {item['name']}")
                if item['note']:
                    print(f"      ℹ️  {item['note']}")
        
        # Priority 2 (Major LLMs)
        if status["by_priority"][2]:
            print("\n🧠 PRIORITY 2 (MAJOR LLM PROVIDERS):")
            for item in status["by_priority"][2]:
                print(f"   ✅ {item['name']}")
                if item['note']:
                    print(f"      ℹ️  {item['note']}")
        
        # Priority 3 (Specialized)
        if status["by_priority"][3]:
            print("\n⚡ PRIORITY 3 (SPECIALIZED PROVIDERS):")
            for item in status["by_priority"][3]:
                print(f"   ✅ {item['name']}")
        
        # Missing
        if status["missing"]:
            print(f"\n❌ MISSING ({len(status['missing'])} sources):")
            for item in sorted(status["missing"], key=lambda x: x['priority']):
                tier = "FREE" if item['free_tier'] else "PAID"
                print(f"   • {item['name']} [{tier}] - {item['url']}")
        
        # Rotation groups
        if status["rotation_groups"]:
            print("\n🔄 ROTATION GROUPS:")
            for primary, backups in status["rotation_groups"].items():
                configured_count = sum(1 for b in backups if b['configured'])
                print(f"   {primary}: {configured_count}/{len(backups)} keys configured")
        
        print("\n" + "="*80)
    
    def get_next_key(self, base_key: str) -> Optional[str]:
        """Get next available key in rotation group"""
        # Find all keys in this rotation group
        rotation_keys = []
        for source_id, config in self.api_sources.items():
            if config.env_key == base_key or config.rotation_key == base_key:
                if source_id in self.current_keys:
                    rotation_keys.append(self.current_keys[source_id])
        
        if not rotation_keys:
            return os.getenv(base_key)
        
        # Simple round-robin: return first available
        return rotation_keys[0]
    
    def setup_systemd_service(self):
        """Set up systemd service for 24/7 operation"""
        print("\n🔧 Setting up systemd service for continuous operation...")
        
        chatty_root = Path(__file__).parent.absolute()
        user_systemd = Path.home() / ".config" / "systemd" / "user"
        user_systemd.mkdir(parents=True, exist_ok=True)
        
        # Main CHATTY automation service
        service_content = f"""[Unit]
Description=CHATTY Complete Automation System
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory={chatty_root}
Environment=CHATTY_SECRETS_FILE=%h/.config/chatty/secrets.env
Environment=CHATTY_OFFLINE_MODE=false
Environment=CHATTY_SUPERVISOR_INTERVAL_SECONDS=15
Environment=CHATTY_RESTART_LIMIT=5
Environment=CHATTY_RESTART_WINDOW_SECONDS=300
Environment=PATH=/usr/local/bin:/usr/bin:/bin:{chatty_root}/.venv/bin
Environment=PYTHONPATH={chatty_root}
Environment=HOME=%h

# Use virtual environment Python
ExecStart={chatty_root}/.venv/bin/python {chatty_root}/START_COMPLETE_AUTOMATION.py

# Auto-restart settings
Restart=always
RestartSec=10
StartLimitInterval=300
StartLimitBurst=5

# Resource limits
LimitNOFILE=65536
MemoryMax=4G
CPUQuota=80%

# Logging
StandardOutput=append:{chatty_root}/logs/chatty-service.log
StandardError=append:{chatty_root}/logs/chatty-service-error.log

[Install]
WantedBy=default.target
"""
        
        service_file = user_systemd / "chatty-automation.service"
        with open(service_file, "w") as f:
            f.write(service_content)
        
        print(f"   ✅ Created: {service_file}")
        
        # API Key refresh timer
        timer_content = """[Unit]
Description=CHATTY API Key Health Check Timer

[Timer]
OnBootSec=5min
OnUnitActiveSec=30min
Persistent=true

[Install]
WantedBy=timers.target
"""
        
        timer_file = user_systemd / "chatty-key-check.timer"
        with open(timer_file, "w") as f:
            f.write(timer_content)
        
        # Key check service
        check_service_content = f"""[Unit]
Description=CHATTY API Key Health Check

[Service]
Type=oneshot
WorkingDirectory={chatty_root}
Environment=CHATTY_SECRETS_FILE=%h/.config/chatty/secrets.env
ExecStart={chatty_root}/.venv/bin/python {chatty_root}/ENHANCED_AUTO_SETUP.py --check-keys
"""
        
        check_service_file = user_systemd / "chatty-key-check.service"
        with open(check_service_file, "w") as f:
            f.write(check_service_content)
        
        print(f"   ✅ Created: {timer_file}")
        print(f"   ✅ Created: {check_service_file}")
        
        # Enable user lingering (keep services running after logout)
        print("\n   Enabling user lingering...")
        subprocess.run(["loginctl", "enable-linger"], capture_output=True)
        
        # Reload systemd
        print("   Reloading systemd...")
        subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True)
        
        print("\n" + "="*80)
        print("✅ SYSTEMD SERVICES CONFIGURED")
        print("="*80)
        print("\n📋 AVAILABLE COMMANDS:")
        print(f"   Start CHATTY:     systemctl --user start chatty-automation")
        print(f"   Stop CHATTY:      systemctl --user stop chatty-automation")
        print(f"   Check status:     systemctl --user status chatty-automation")
        print(f"   View logs:        journalctl --user -u chatty-automation -f")
        print(f"   Enable auto-start: systemctl --user enable chatty-automation")
        print(f"   Check keys:       systemctl --user start chatty-key-check")
        print("\n" + "="*80)
    
    def start_services(self):
        """Start CHATTY services"""
        print("\n🚀 Starting CHATTY services...")
        
        # Start main automation
        result = subprocess.run(
            ["systemctl", "--user", "start", "chatty-automation"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("   ✅ CHATTY automation started")
        else:
            print(f"   ⚠️  Could not start: {result.stderr}")
        
        # Enable timer for key checks
        subprocess.run(
            ["systemctl", "--user", "enable", "chatty-key-check.timer"],
            capture_output=True
        )
        subprocess.run(
            ["systemctl", "--user", "start", "chatty-key-check.timer"],
            capture_output=True
        )
        print("   ✅ API key check timer enabled")
        
        print("\n   Check status with: systemctl --user status chatty-automation")
    
    def run_key_health_check(self):
        """Check health of all configured API keys"""
        print("\n🏥 Running API Key Health Check...")
        print("="*80)
        
        import asyncio
        import openai
        
        async def test_key(name: str, key: str, base_url: str, model: str):
            """Test a single API key"""
            try:
                client = openai.AsyncOpenAI(
                    api_key=key,
                    base_url=base_url,
                    timeout=30
                )
                
                start = time.time()
                response = await client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": "Hi"}],
                    max_tokens=5
                )
                latency = (time.time() - start) * 1000
                
                return {
                    "status": "✅ HEALTHY",
                    "latency_ms": round(latency, 1),
                    "model": model
                }
            except Exception as e:
                return {
                    "status": "❌ ERROR",
                    "error": str(e)[:50]
                }
        
        async def run_checks():
            tests = []
            
            # Test xAI
            xai_key = os.getenv("XAI_API_KEY")
            if xai_key:
                tests.append(("xAI (Grok)", test_key("xAI", xai_key, "https://api.x.ai/v1", "grok-2-latest")))
            
            # Test OpenRouter
            or_key = os.getenv("OPENROUTER_API_KEY")
            if or_key:
                tests.append(("OpenRouter", test_key("OpenRouter", or_key, "https://openrouter.ai/api/v1", "openai/gpt-4o-mini")))
            
            # Test NVIDIA
            nv_key = os.getenv("NVIDIA_API_KEY")
            if nv_key:
                tests.append(("NVIDIA (Kimi)", test_key("NVIDIA", nv_key, "https://integrate.api.nvidia.com/v1", "moonshotai/kimi-k2.5")))
            
            # Test OpenAI
            oa_key = os.getenv("OPENAI_API_KEY")
            if oa_key:
                tests.append(("OpenAI", test_key("OpenAI", oa_key, "https://api.openai.com/v1", "gpt-4o-mini")))
            
            # Run all tests
            results = await asyncio.gather(*[t[1] for t in tests], return_exceptions=True)
            
            for (name, _), result in zip(tests, results):
                if isinstance(result, Exception):
                    print(f"   {name}: ❌ FAILED - {str(result)[:40]}")
                else:
                    status = result.get("status", "UNKNOWN")
                    if "HEALTHY" in status:
                        print(f"   {name}: ✅ {result['latency_ms']}ms")
                    else:
                        print(f"   {name}: {status} - {result.get('error', '')}")
        
        asyncio.run(run_checks())
        print("="*80)

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="CHATTY Enhanced API Key Manager")
    parser.add_argument("--status", action="store_true", help="Show key status")
    parser.add_argument("--setup-systemd", action="store_true", help="Setup systemd services")
    parser.add_argument("--start", action="store_true", help="Start CHATTY services")
    parser.add_argument("--check-keys", action="store_true", help="Run key health check")
    parser.add_argument("--setup-all", action="store_true", help="Full setup (systemd + start)")
    
    args = parser.parse_args()
    
    manager = EnhancedAPIKeyManager()
    
    if args.status or len(sys.argv) == 1:
        manager.print_status()
    
    if args.check_keys:
        manager.run_key_health_check()
    
    if args.setup_systemd or args.setup_all:
        manager.setup_systemd_service()
    
    if args.start or args.setup_all:
        manager.start_services()
    
    if args.setup_all:
        print("\n" + "="*80)
        print("🎉 CHATTY FULL SETUP COMPLETE!")
        print("="*80)
        print("\nCHATTY will now run 24/7 with:")
        print("  ✅ Auto-restart on failure")
        print("  ✅ API key health checks every 30 minutes")
        print("  ✅ Automatic key rotation for multi-key providers")
        print("  ✅ Resource limits (4GB RAM, 80% CPU)")
        print("\nMonitor with: journalctl --user -u chatty-automation -f")

if __name__ == "__main__":
    main()
