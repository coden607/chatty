#!/usr/bin/env python3
"""
AUTOMATED API KEY SETUP
One-click setup for all API keys with browser automation
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Try to import selenium for browser automation
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

class AutoAPIKeySetup:
    """Automated API key retrieval and setup"""
    
    def __init__(self):
        self.secrets_file = Path.home() / ".config/chatty/secrets.env"
        self.secrets_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing secrets
        if self.secrets_file.exists():
            load_dotenv(self.secrets_file)
        
        self.api_services = {
            # === PRIORITY 1: INFRASTRUCTURE & TOOLS ===
            "LangChain": {
                "url": "https://smith.langchain.com/settings",
                "env_key": "LANGCHAIN_API_KEY",
                "instructions": "1. Sign in\n2. Go to Settings → API Keys\n3. Click 'Create API Key'\n4. Copy key (starts with 'lsv2_')",
                "free_tier": True,
                "priority": 1,
                "note": "Essential for AI tracing & debugging"
            },
            "CrewAI": {
                "url": "https://app.crewai.com/settings/api-keys",
                "env_key": "CREWAI_API_KEY",
                "instructions": "1. Sign in\n2. Click 'Generate New Key'\n3. Copy the key",
                "free_tier": True,
                "priority": 1,
                "note": "Required for multi-agent orchestration"
            },
            "n8n": {
                "url": "https://app.n8n.cloud/settings/api",
                "env_key": "N8N_API_KEY",
                "instructions": "1. Sign in\n2. Settings → API\n3. Create API Key\n4. Copy key",
                "free_tier": True,
                "priority": 1,
                "note": "Powerhouse for workflow automation"
            },

            # === PRIORITY 2: MAJOR LLM PROVIDERS ===
            "OpenAI": {
                "url": "https://platform.openai.com/api-keys",
                "env_key": "OPENAI_API_KEY",
                "instructions": "1. Sign in\n2. Click 'Create new secret key'\n3. Name it 'Auto'\n4. Copy the key (starts with 'sk-')",
                "free_tier": False,
                "priority": 2,
                "note": "Industry standard (GPT-4o)"
            },
            "Google Gemini": {
                "url": "https://aistudio.google.com/app/apikey",
                "env_key": "GOOGLE_API_KEY",
                "instructions": "1. Sign in with Google\n2. Click 'Create API key'\n3. Select project (or new)\n4. Copy key",
                "free_tier": True,
                "priority": 2,
                "note": "Generous free tier (Gemini 1.5)"
            },
            "DeepSeek": {
                "url": "https://platform.deepseek.com/api_keys",
                "env_key": "DEEPSEEK_API_KEY",
                "instructions": "1. Sign in\n2. Click 'Create API Key'\n3. Copy key",
                "free_tier": True,
                "priority": 2,
                "note": "Top tier coding performance (V3/R1)"
            },
            "Anthropic": {
                "url": "https://console.anthropic.com/settings/keys",
                "env_key": "ANTHROPIC_API_KEY",
                "instructions": "1. Sign in\n2. Click 'Create Key'\n3. Copy key (starts with 'sk-ant-')",
                "free_tier": False,
                "priority": 2,
                "note": "Best for complex reasoning (Claude 3.5)"
            },
            
            # === PRIORITY 3: AGGREGATORS & SPECIALIZED ===
            "OpenRouter": {
                "url": "https://openrouter.ai/keys",
                "env_key": "OPENROUTER_API_KEY",
                "instructions": "1. Sign in\n2. Create Key\n3. Copy key (starts with 'sk-or-v1-')",
                "free_tier": True,
                "free_credit": "$1",
                "priority": 3
            },
             "xAI (Grok)": {
                "url": "https://console.x.ai/",
                "env_key": "XAI_API_KEY",
                "instructions": "1. Sign in with X account\n2. API Keys → Create API Key\n3. Copy key",
                "free_tier": True,
                "priority": 3
            },
            "Hugging Face": {
                "url": "https://huggingface.co/settings/tokens",
                "env_key": "HUGGINGFACE_TOKEN",
                "instructions": "1. Sign in\n2. New token → Select 'Read'\n3. Copy key (starts with 'hf_')",
                "free_tier": True,
                "priority": 3
            },

            # === PRIORITY 4: OTHER POWERFUL MODELS ===
            "Mistral AI": {
                "url": "https://console.mistral.ai/api-keys/",
                "env_key": "MISTRAL_API_KEY",
                "instructions": "1. Sign in\n2. Click 'Create new key'\n3. Copy key",
                "free_tier": True,
                "priority": 4
            },
            "Perplexity": {
                "url": "https://www.perplexity.ai/settings/api",
                "env_key": "PPLX_API_KEY",
                "instructions": "1. Sign in\n2. Generate API Key\n3. Copy key (starts with 'pplx-')",
                "free_tier": False,
                "priority": 4,
                "note": "Excellent for live web search"
            },
            "Together AI": {
                "url": "https://api.together.xyz/settings/api-keys",
                "env_key": "TOGETHER_API_KEY",
                "instructions": "1. Sign in\n2. Copy the default API key",
                "free_tier": True,
                "priority": 4
            },
            "Replicate": {
                "url": "https://replicate.com/account/api-tokens",
                "env_key": "REPLICATE_API_TOKEN",
                "instructions": "1. Sign in with GitHub\n2. Copy the API token",
                "free_tier": False,
                "priority": 4,
                "note": "Best for image generation models"
            },
            "Cohere": {
                "url": "https://dashboard.cohere.com/api-keys",
                "env_key": "COHERE_API_KEY",
                "instructions": "1. Sign in\n2. Create API Key\n3. Copy key",
                "free_tier": True,
                "priority": 4
            },
            "Twitter/X": {
                "url": "https://developer.twitter.com/en/portal/dashboard",
                "env_key": "X_BEARER_TOKEN",
                "instructions": "1. Sign in\n2. Keys and tokens → Generate Bearer Token",
                "free_tier": True,
                "priority": 4
            }
        }
    
    def check_existing_keys(self):
        """Check which keys are already configured"""
        print("\n🔍 CHECKING EXISTING API KEYS")
        print("=" * 80)
        
        existing = []
        missing = []
        
        # Sort services by priority (1 = highest)
        sorted_services = sorted(
            self.api_services.items(),
            key=lambda x: (x[1].get('priority', 99), x[0])
        )
        
        for service, config in sorted_services:
            key = os.getenv(config['env_key'])
            note = f" ({config['note']})" if config.get('note') else ""
            
            if key and key != "your_key_here" and len(key) > 10:
                existing.append(service)
                print(f"✅ {service}: Configured{note}")
            else:
                missing.append(service)
                priority_marker = "🔴 PRIORITY" if config.get('priority', 99) == 1 else ""
                print(f"❌ {service}: Missing {priority_marker}{note}")
        
        print("=" * 80)
        return existing, missing
    
    def interactive_setup(self):
        """Interactive setup with browser automation"""
        print("\n🚀 AUTOMATED API KEY SETUP")
        print("=" * 80)
        print("This will help you get all necessary API keys automatically.")
        print("Press ENTER to continue, or Ctrl+C to cancel.")
        print("=" * 80)
        
        input()  # Wait for user to press Enter
        
        existing, missing = self.check_existing_keys()
        
        if not missing:
            print("\n✅ All API keys are already configured!")
            return
        
        print(f"\n📋 Need to configure {len(missing)} API keys")
        print("\nOptions:")
        print("1. Auto-open all signup pages (recommended)")
        print("2. Manual setup with guided instructions")
        print("3. Skip for now")
        
        choice = input("\nEnter choice (1-3) [1]: ").strip() or "1"
        
        if choice == "1":
            self.auto_open_pages(missing)
        elif choice == "2":
            self.manual_guided_setup(missing)
        else:
            print("\n⏭️  Skipping API key setup")
            return
    
    def auto_open_pages(self, missing_services):
        """Automatically open all API key pages in browser"""
        print("\n🌐 Opening API key pages in your browser...")
        print("=" * 80)
        
        import webbrowser
        
        # Sort by priority
        sorted_missing = sorted(
            missing_services,
            key=lambda s: (self.api_services[s].get('priority', 99), s)
        )
        
        for i, service in enumerate(sorted_missing, 1):
            config = self.api_services[service]
            
            print(f"\n📖 [{i}/{len(sorted_missing)}] {service}")
            
            if config.get('note'):
                print(f"   ℹ️  {config['note']}")
            
            print(f"   URL: {config['url']}")
            # Handle free tier display with proper string formatting
            if config.get('free_tier'):
                free_tier_text = "Yes"
                if config.get('free_credit'):
                    free_tier_text += f" ({config.get('free_credit', '')})"
            else:
                free_tier_text = "No"
            print(f"   Free tier: {free_tier_text}")
            print(f"\n   Instructions:")
            for line in config['instructions'].split('\n'):
                print(f"   {line}")
            
            print("\n   Press ENTER to open this page in your browser...")
            input()
            
            webbrowser.open(config['url'])
            print(f"   ✅ Opened {service} in browser")
            
            # Wait for user to get the key
            print(f"\n   After you get your API key, paste it here:")
            api_key = input(f"   {config['env_key']}: ").strip()
            
            if api_key:
                self.save_api_key(config['env_key'], api_key)
                print(f"   ✅ Saved {service} API key")
            else:
                print(f"   ⏭️  Skipped {service}")
        
        print("\n" + "=" * 80)
        print("✅ API KEY SETUP COMPLETE")
        print("=" * 80)
        
        # Verify all keys
        self.verify_saved_keys()
    
    def manual_guided_setup(self, missing_services):
        """Manual setup with detailed instructions"""
        print("\n📝 MANUAL SETUP GUIDE")
        print("=" * 80)
        
        for service in missing_services:
            config = self.api_services[service]
            print(f"\n{'='*80}")
            print(f"🔑 {service}")
            print(f"{'='*80}")
            print(f"\n1. Visit: {config['url']}")
            print(f"\n2. Follow these steps:")
            for line in config['instructions'].split('\n'):
                print(f"   {line}")
            print(f"\n3. Paste your API key below (or press ENTER to skip):")
            
            api_key = input(f"\n{config['env_key']}: ").strip()
            
            if api_key:
                self.save_api_key(config['env_key'], api_key)
                print(f"✅ Saved {service} API key")
            else:
                print(f"⏭️  Skipped {service}")
        
        print("\n" + "=" * 80)
        print("✅ MANUAL SETUP COMPLETE")
        print("=" * 80)
        
        self.verify_saved_keys()
    
    def save_api_key(self, key_name, key_value):
        """Save API key to secrets file"""
        # Read existing content
        if self.secrets_file.exists():
            # Create backup before modifying
            try:
                import subprocess
                subprocess.run(
                    [sys.executable, "secure_key_backup.py", "auto"],
                    cwd="/home/coden809/CHATTY",
                    capture_output=True,
                    timeout=5
                )
            except:
                pass  # Backup failed, but continue
            
            with open(self.secrets_file, 'r') as f:
                lines = f.readlines()
        else:
            lines = []
        
        # Check if key already exists
        key_exists = False
        for i, line in enumerate(lines):
            if line.startswith(f"{key_name}="):
                lines[i] = f"{key_name}={key_value}\n"
                key_exists = True
                break
        
        # Add key if it doesn't exist
        if not key_exists:
            # Add to appropriate section
            if not lines or lines[-1].strip():
                lines.append("\n")
            lines.append(f"# Added by auto_setup_api_keys.py on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            lines.append(f"{key_name}={key_value}\n")
        
        # Write back to file
        with open(self.secrets_file, 'w') as f:
            f.writelines(lines)
        
        # Set secure permissions (owner read/write only)
        os.chmod(self.secrets_file, 0o600)
    
    def verify_saved_keys(self):
        """Verify all saved keys"""
        print("\n🔍 VERIFYING SAVED KEYS")
        print("=" * 80)
        
        # Reload environment
        load_dotenv(self.secrets_file, override=True)
        
        configured = 0
        total = len(self.api_services)
        
        for service, config in self.api_services.items():
            key = os.getenv(config['env_key'])
            if key and key != "your_key_here" and len(key) > 10:
                print(f"✅ {service}: Configured")
                configured += 1
            else:
                print(f"❌ {service}: Not configured")
        
        print("=" * 80)
        print(f"\n📊 Configuration Status: {configured}/{total} keys configured")
        
        if configured == total:
            print("\n🎉 ALL API KEYS CONFIGURED!")
            print("\n🚀 You can now run the full automation:")
            print("   python3 START_COMPLETE_AUTOMATION.py")
        elif configured > 0:
            print("\n✅ Partial configuration complete")
            print("   You can run the automation with available keys")
            print("   Run this script again to add missing keys")
        else:
            print("\n⚠️  No keys configured yet")
            print("   Run this script again to configure keys")
    
    def quick_setup(self):
        """Quick setup - just press Enter to continue"""
        print("\n⚡ QUICK API KEY SETUP")
        print("=" * 80)
        print("This will guide you through getting all API keys.")
        print("Just press ENTER at each step to continue.")
        print("=" * 80)
        
        input("\nPress ENTER to start...")
        
        existing, missing = self.check_existing_keys()
        
        if not missing:
            print("\n✅ All API keys already configured!")
            input("\nPress ENTER to continue...")
            return
        
        print(f"\n📋 Setting up {len(missing)} API keys")
        input("\nPress ENTER to continue...")
        
        import webbrowser
        
        for i, service in enumerate(missing, 1):
            config = self.api_services[service]
            
            print(f"\n{'='*80}")
            print(f"[{i}/{len(missing)}] {service}")
            print(f"{'='*80}")
            
            if not config.get('free_tier'):
                print(f"⚠️  Note: {config.get('note', 'May require payment')}")
                skip = input("\nSkip this service? (y/N): ").strip().lower()
                if skip == 'y':
                    print(f"⏭️  Skipped {service}")
                    continue
            
            print(f"\nInstructions:")
            for line in config['instructions'].split('\n'):
                print(f"  {line}")
            
            print(f"\nPress ENTER to open {service} in your browser...")
            input()
            
            webbrowser.open(config['url'])
            print(f"✅ Opened {config['url']}")
            
            print(f"\nAfter getting your key, paste it below:")
            print(f"(or press ENTER to skip)")
            api_key = input(f"\n{config['env_key']}: ").strip()
            
            if api_key:
                self.save_api_key(config['env_key'], api_key)
                print(f"✅ Saved!")
            else:
                print(f"⏭️  Skipped")
        
        print("\n" + "=" * 80)
        print("✅ SETUP COMPLETE!")
        print("=" * 80)
        
        self.verify_saved_keys()
        
        input("\nPress ENTER to finish...")


def main():
    """Main execution"""
    setup = AutoAPIKeySetup()
    
    # Check if running in quick mode
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        setup.quick_setup()
    else:
        setup.interactive_setup()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
        sys.exit(0)
