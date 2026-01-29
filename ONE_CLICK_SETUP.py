#!/usr/bin/env python3
"""
ONE-CLICK COMPLETE AUTOMATION SETUP
Just press ENTER to get everything automated
"""

import os
import sys
import time
import subprocess
import webbrowser
from pathlib import Path
from dotenv import load_dotenv

class OneClickSetup:
    """Complete automation setup with one click"""
    
    def __init__(self):
        self.chatty_dir = Path("/home/coden809/CHATTY")
        self.secrets_file = Path.home() / ".config/chatty/secrets.env"
        
    def run(self):
        """Run complete setup"""
        self.show_banner()
        
        print("\n🎯 This will set up COMPLETE AUTOMATION for Chatty")
        print("\n✨ What will be automated:")
        print("   • AI-powered content generation")
        print("   • Grant proposal writing and submission")
        print("   • Lead acquisition and conversion")
        print("   • Social media posting")
        print("   • Revenue generation")
        print("   • Customer acquisition")
        
        print("\n⏱️  Setup time: ~5 minutes")
        print("\n" + "="*80)
        print("Press ENTER to begin, or Ctrl+C to cancel")
        print("="*80)
        
        input()
        
        # Step 1: Check system
        self.check_system()
        
        # Step 1.5: Check Ollama
        self.check_ollama()
        
        # Step 2: Setup API keys
        self.setup_api_keys()
        
        # Step 3: Verify configuration
        self.verify_config()
        
        # Step 4: Launch automation
        self.launch_automation()
        
        self.show_completion()
    
    def show_banner(self):
        """Show welcome banner"""
        print("\n" + "="*80)
        print("🚀 CHATTY - ONE-CLICK AUTOMATION SETUP")
        print("="*80)
    
    def check_system(self):
        """Check system requirements"""
        print("\n[1/4] 🔍 Checking system...")
        
        # Check Python
        python_version = sys.version_info
        if python_version.major >= 3 and python_version.minor >= 8:
            print("   ✅ Python version OK")
        else:
            print("   ⚠️  Python 3.8+ recommended")
        
        # Check required files
        required_files = [
            "AUTOMATED_REVENUE_ENGINE.py",
            "AUTOMATED_CUSTOMER_ACQUISITION.py",
            "START_COMPLETE_AUTOMATION.py"
        ]
        
        for file in required_files:
            if (self.chatty_dir / file).exists():
                print(f"   ✅ {file}")
            else:
                print(f"   ❌ {file} missing")
        
        # Install dependencies
        print("\n   📦 Installing dependencies...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-q", "-r", "requirements.txt"],
                cwd=self.chatty_dir,
                check=False,
                capture_output=True
            )
            print("   ✅ Dependencies installed")
        except Exception as e:
            print(f"   ⚠️  Could not install dependencies: {e}")
        
        input("\n   Press ENTER to continue...")

    def check_ollama(self):
        """Check and install Ollama"""
        print("\n[One-Click] 🦙 Checking Ollama (Local AI)...")
        
        # Check if Ollama is installed
        ollama_path = subprocess.run(["which", "ollama"], capture_output=True).stdout.strip()
        
        if ollama_path:
            print("   ✅ Ollama is installed")
            # Check if running
            is_running = subprocess.run(["pgrep", "-f", "ollama"], capture_output=True).stdout.strip()
            if is_running:
                print("   ✅ Ollama is running")
            else:
                print("   ⚠️  Ollama is installed but not running")
                print("   🚀 Starting Ollama...")
                subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(2)
                print("   ✅ Ollama started")
        else:
            print("   ❌ Ollama is NOT installed")
            print("   Ollama allows you to run AI models locally for free.")
            choice = input("   Install Ollama now? (y/N): ").strip().lower()
            
            if choice == 'y':
                print("   ⬇️  Installing Ollama...")
                try:
                    subprocess.run("curl -fsSL https://ollama.com/install.sh | sh", shell=True, check=True)
                    print("   ✅ Ollama installed successfully")
                    print("   🚀 Starting Ollama...")
                    subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    time.sleep(2)
                except Exception as e:
                    print(f"   ❌ Error installing Ollama: {e}")
            else:
                print("   ⏭️  Skipping Ollama")
    
    def setup_api_keys(self):
        """Setup API keys automatically"""
        print("\n[2/4] 🔑 Setting up API keys...")
        
        # Load existing keys
        if self.secrets_file.exists():
            load_dotenv(self.secrets_file)
        
        # Check which keys are needed
        key_status = {
            # Priority 1
            "LANGCHAIN_API_KEY": ("LangChain", "https://smith.langchain.com/settings"),
            "CREWAI_API_KEY": ("CrewAI", "https://app.crewai.com/settings/api-keys"),
            "N8N_API_KEY": ("n8n", "https://app.n8n.cloud/settings/api"),
            
            # Priority 2
            "OPENAI_API_KEY": ("OpenAI", "https://platform.openai.com/api-keys"),
            "GOOGLE_API_KEY": ("Google Gemini", "https://aistudio.google.com/app/apikey"),
            "DEEPSEEK_API_KEY": ("DeepSeek", "https://platform.deepseek.com/api_keys"),
            "ANTHROPIC_API_KEY": ("Anthropic", "https://console.anthropic.com/settings/keys"),
            
            # Priority 3
            "OPENROUTER_API_KEY": ("OpenRouter", "https://openrouter.ai/keys"),
            "XAI_API_KEY": ("xAI (Grok)", "https://console.x.ai/"),
            "HUGGINGFACE_TOKEN": ("Hugging Face", "https://huggingface.co/settings/tokens"),
            
            # Priority 4
            "MISTRAL_API_KEY": ("Mistral AI", "https://console.mistral.ai/api-keys/"),
            "PPLX_API_KEY": ("Perplexity", "https://www.perplexity.ai/settings/api"),
            "TOGETHER_API_KEY": ("Together AI", "https://api.together.xyz/settings/api-keys"),
            "REPLICATE_API_TOKEN": ("Replicate", "https://replicate.com/account/api-tokens"),
            "COHERE_API_KEY": ("Cohere", "https://dashboard.cohere.com/api-keys"),
            "X_BEARER_TOKEN": ("Twitter/X", "https://developer.twitter.com/en/portal/dashboard"),
        }
        
        missing_keys = []
        for key, (name, url) in key_status.items():
            value = os.getenv(key)
            if value and len(value) > 10 and value != "your_key_here":
                print(f"   ✅ {name}: Configured")
            else:
                print(f"   ❌ {name}: Missing")
                missing_keys.append((key, name, url))
        
        if not missing_keys:
            print("\n   ✅ All API keys configured!")
            input("\n   Press ENTER to continue...")
            return
        
        print(f"\n   📋 Need to configure {len(missing_keys)} API keys")
        print("\n   Options:")
        print("   1. Auto-open signup pages and paste keys (RECOMMENDED)")
        print("   2. Skip for now (limited functionality)")
        
        choice = input("\n   Choose (1-2) [1]: ").strip() or "1"
        
        if choice == "1":
            self.auto_get_keys(missing_keys)
        else:
            print("\n   ⏭️  Skipping API key setup")
            print("   ⚠️  Some features will be limited")
        
        input("\n   Press ENTER to continue...")
    
    def auto_get_keys(self, missing_keys):
        """Automatically guide through getting API keys"""
        print("\n   🌐 Opening API key pages...")
        
        for i, (key_name, service_name, url) in enumerate(missing_keys, 1):
            print(f"\n   {'='*70}")
            print(f"   [{i}/{len(missing_keys)}] {service_name}")
            print(f"   {'='*70}")
            
            # Service-specific instructions
            instructions = {
                # P1
                "LANGCHAIN_API_KEY": ["1. Sign in", "2. Settings → API Keys", "3. Create key"],
                "CREWAI_API_KEY": ["1. Sign in", "2. Generate New Key"],
                "N8N_API_KEY": ["1. Sign in", "2. Settings → API", "3. Create key"],
                
                # P2
                "OPENAI_API_KEY": ["1. Sign in", "2. Create new secret key", "3. Copy key"],
                "GOOGLE_API_KEY": ["1. Sign in with Google", "2. Create API key", "3. Copy key"],
                "DEEPSEEK_API_KEY": ["1. Sign in", "2. Create API Key"],
                "ANTHROPIC_API_KEY": ["1. Sign in", "2. Create Key"],
                
                # P3
                "OPENROUTER_API_KEY": ["1. Sign in", "2. Create Key"],
                "XAI_API_KEY": ["1. Sign in with X", "2. Create API Key"],
                "HUGGINGFACE_TOKEN": ["1. New token", "2. Select 'Read'", "3. Copy token"],
                
                # P4
                "MISTRAL_API_KEY": ["1. Sign in", "2. Create new key"],
                "PPLX_API_KEY": ["1. Sign in", "2. Generate API Key"],
                "TOGETHER_API_KEY": ["1. Sign in", "2. Copy default key"],
                "REPLICATE_API_TOKEN": ["1. Sign in", "2. Copy API token"],
                "COHERE_API_KEY": ["1. Sign in", "2. Create API Key"],
                "X_BEARER_TOKEN": ["1. Developer Portal", "2. Generate Bearer Token"]
            }
            
            print(f"\n   📖 Instructions:")
            for instruction in instructions.get(key_name, ["Follow the on-screen instructions"]):
                print(f"      {instruction}")
            
            print(f"\n   Press ENTER to open {service_name} in browser...")
            input()
            
            webbrowser.open(url)
            print(f"   ✅ Opened {url}")
            
            print(f"\n   After you get your API key, paste it here:")
            print(f"   (or press ENTER to skip)")
            api_key = input(f"\n   {key_name}: ").strip()
            
            if api_key:
                self.save_key(key_name, api_key)
                print(f"   ✅ Saved {service_name} key!")
            else:
                print(f"   ⏭️  Skipped {service_name}")
    
    def save_key(self, key_name, key_value):
        """Save API key to secrets file"""
        self.secrets_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Read existing content
        if self.secrets_file.exists():
            with open(self.secrets_file, 'r') as f:
                lines = f.readlines()
        else:
            lines = ["# CHATTY API Keys\n", "# Auto-generated by ONE_CLICK_SETUP.py\n\n"]
        
        # Update or add key
        key_found = False
        for i, line in enumerate(lines):
            if line.startswith(f"{key_name}="):
                lines[i] = f"{key_name}={key_value}\n"
                key_found = True
                break
        
        if not key_found:
            lines.append(f"{key_name}={key_value}\n")
        
        # Write back
        with open(self.secrets_file, 'w') as f:
            f.writelines(lines)
    
    def verify_config(self):
        """Verify configuration"""
        print("\n[3/4] ✅ Verifying configuration...")
        
        # Reload environment
        load_dotenv(self.secrets_file, override=True)
        
        # Check critical components
        checks = {
            "Secrets file": self.secrets_file.exists(),
            "Revenue engine": (self.chatty_dir / "AUTOMATED_REVENUE_ENGINE.py").exists(),
            "Customer acquisition": (self.chatty_dir / "AUTOMATED_CUSTOMER_ACQUISITION.py").exists(),
            "Automation launcher": (self.chatty_dir / "START_COMPLETE_AUTOMATION.py").exists(),
        }
        
        all_ok = True
        for check, status in checks.items():
            if status:
                print(f"   ✅ {check}")
            else:
                print(f"   ❌ {check}")
                all_ok = False
        
        if all_ok:
            print("\n   ✅ Configuration verified!")
        else:
            print("\n   ⚠️  Some components missing")
        
        input("\n   Press ENTER to continue...")
    
    def launch_automation(self):
        """Launch the automation system"""
        print("\n[4/4] 🚀 Launching automation...")
        
        print("\n   Starting automation system...")
        print("   This will run in the background and:")
        print("   • Generate content automatically")
        print("   • Find and convert leads")
        print("   • Write grant proposals")
        print("   • Post to social media")
        print("   • Generate revenue 24/7")
        
        print("\n   Press ENTER to launch automation...")
        input()
        
        # Launch the automation
        try:
            print("\n   🚀 Starting automation...")
            subprocess.Popen(
                [sys.executable, "START_COMPLETE_AUTOMATION.py"],
                cwd=self.chatty_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            print("   ✅ Automation started!")
            
            # Also start the API server
            print("\n   🌐 Starting API server...")
            subprocess.Popen(
                [sys.executable, "AUTOMATION_API_SERVER.py"],
                cwd=self.chatty_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            print("   ✅ API server started!")
            
        except Exception as e:
            print(f"   ❌ Error launching automation: {e}")
            print("   You can manually start it with:")
            print(f"   cd {self.chatty_dir}")
            print("   python3 START_COMPLETE_AUTOMATION.py")
    
    def show_completion(self):
        """Show completion message"""
        print("\n" + "="*80)
        print("🎉 SETUP COMPLETE!")
        print("="*80)
        
        print("\n✅ Your automation is now running!")
        
        print("\n📊 Monitor your automation:")
        print("   • Dashboard: http://localhost:5000")
        print("   • Leads: http://localhost:5000/leads")
        print("   • Status: Check generated_content/earnings_status.md")
        
        print("\n📁 Generated content location:")
        print(f"   {self.chatty_dir / 'generated_content'}")
        
        print("\n🔄 The system will now:")
        print("   • Run continuously in the background")
        print("   • Generate content every hour")
        print("   • Find and convert leads daily")
        print("   • Submit grant proposals automatically")
        print("   • Post to social media on schedule")
        
        print("\n💡 Useful commands:")
        print("   • Check status: cat generated_content/earnings_status.md")
        print("   • View logs: tail -f logs/automation.log")
        print("   • Stop automation: pkill -f START_COMPLETE_AUTOMATION")
        
        print("\n" + "="*80)
        print("Press ENTER to finish")
        print("="*80)
        input()


def main():
    """Main execution"""
    setup = OneClickSetup()
    setup.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        print("\nPlease report this issue or try manual setup")
        sys.exit(1)
