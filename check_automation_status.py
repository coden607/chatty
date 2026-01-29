#!/usr/bin/env python3
"""
AUTOMATION STATUS CHECKER
Quick check to see what's configured and what's running
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import subprocess

def check_status():
    """Check automation status"""
    
    print("\n" + "="*80)
    print("🔍 CHATTY AUTOMATION STATUS CHECK")
    print("="*80)
    
    # Check secrets file
    secrets_file = Path.home() / ".config/chatty/secrets.env"
    print("\n📁 Configuration Files:")
    if secrets_file.exists():
        print(f"   ✅ Secrets file exists: {secrets_file}")
        load_dotenv(secrets_file)
    else:
        print(f"   ❌ Secrets file missing: {secrets_file}")
        print("   Run: python3 auto_setup_api_keys.py")
    
    # Check API keys
    print("\n🔑 API Keys Status:")
    keys = {
        # Priority 1
        "LANGCHAIN_API_KEY": "LangChain",
        "CREWAI_API_KEY": "CrewAI",
        "N8N_API_KEY": "n8n",
        
        # Priority 2
        "OPENAI_API_KEY": "OpenAI",
        "GOOGLE_API_KEY": "Google Gemini",
        "DEEPSEEK_API_KEY": "DeepSeek",
        "ANTHROPIC_API_KEY": "Anthropic",
        
        # Priority 3
        "OPENROUTER_API_KEY": "OpenRouter",
        "XAI_API_KEY": "xAI (Grok)",
        "HUGGINGFACE_TOKEN": "Hugging Face",
        
        # Priority 4
        "MISTRAL_API_KEY": "Mistral AI",
        "PPLX_API_KEY": "Perplexity",
        "TOGETHER_API_KEY": "Together AI",
        "REPLICATE_API_TOKEN": "Replicate",
        "COHERE_API_KEY": "Cohere",
        "X_BEARER_TOKEN": "Twitter/X"
    }
    
    configured = 0
    for key, name in keys.items():
        value = os.getenv(key)
        if value and len(value) > 10 and value != "your_key_here":
            print(f"   ✅ {name:<15}")
            configured += 1
        else:
            print(f"   ❌ {name:<15}")
    
    print(f"\n   📊 {configured}/{len(keys)} keys configured")
    
    # Fallback Chain Status
    print("\n🛡️ AI Fallback Chain Status:")
    chain = [
        ("1. xAI", os.getenv("XAI_API_KEY")),
        ("2. OpenRouter", os.getenv("OPENROUTER_API_KEY")),
        ("3. OpenAI", os.getenv("OPENAI_API_KEY")),
        ("4. Anthropic", os.getenv("ANTHROPIC_API_KEY")),
        ("5. Google", os.getenv("GOOGLE_API_KEY")),
        ("6. DeepSeek", os.getenv("DEEPSEEK_API_KEY")),
        ("7. Mistral", os.getenv("MISTRAL_API_KEY")),
        ("8. Cohere", os.getenv("COHERE_API_KEY"))
    ]
    
    active_links = 0
    for name, key in chain:
        status = "🟢 Active" if key and len(key) > 5 else "⚪ Skiped (Missing Key)"
        if "Active" in status:
            active_links += 1
        print(f"   {name:<15} : {status}")
    
    if active_links == 0:
        print("   ⚠️  CRITICAL: No AI providers configured. Automation will fail.")
    elif active_links < 3:
        print("   ⚠️  Warning: Low redundancy. Add more keys for better stability.")
    else:
        print(f"   ✅ Robust redundancy: {active_links} active fallback layers")

    # Check running processes
    print("\n🚀 Running Processes:")
    try:
        # Check for Ollama (Local AI)
        result = subprocess.run(
            ["pgrep", "-f", "ollama"],
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            print(f"   ✅ Ollama (Local AI) running (PID: {result.stdout.strip().split()[0]})")
        else:
            print("   ❌ Ollama not running (Optional local AI)")
            
        # Check for automation
        result = subprocess.run(
            ["pgrep", "-f", "START_COMPLETE_AUTOMATION"],
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            print(f"   ✅ Automation running (PID: {result.stdout.strip()})")
        else:
            print("   ❌ Automation not running")
            print("   Start with: python3 START_COMPLETE_AUTOMATION.py")
        
        # Check for API server
        result = subprocess.run(
            ["pgrep", "-f", "AUTOMATION_API_SERVER"],
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            print(f"   ✅ API server running (PID: {result.stdout.strip()})")
        else:
            print("   ❌ API server not running")
            print("   Start with: python3 AUTOMATION_API_SERVER.py")
    except Exception as e:
        print(f"   ⚠️  Could not check processes: {e}")
    
    # Check generated content
    print("\n📄 Generated Content:")
    content_dir = Path("/home/coden809/CHATTY/generated_content")
    if content_dir.exists():
        files = list(content_dir.glob("**/*"))
        file_count = len([f for f in files if f.is_file()])
        print(f"   ✅ Content directory exists")
        print(f"   📊 {file_count} files generated")
    else:
        print("   ⚠️  No content generated yet")
    
    # Check logs
    print("\n📋 Logs:")
    log_dir = Path("/home/coden809/CHATTY/logs")
    if log_dir.exists():
        log_files = list(log_dir.glob("*.log"))
        if log_files:
            latest_log = max(log_files, key=lambda p: p.stat().st_mtime)
            size_kb = latest_log.stat().st_size / 1024
            print(f"   ✅ Latest log: {latest_log.name} ({size_kb:.1f} KB)")
        else:
            print("   ⚠️  No log files yet")
    else:
        print("   ⚠️  Log directory not found")
    
    # Summary
    print("\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80)
    
    if configured >= 3:
        print("\n✅ System is configured and ready!")
        print("\n🚀 To start automation:")
        print("   ./AUTOMATE_EVERYTHING.sh")
        print("   OR")
        print("   python3 START_COMPLETE_AUTOMATION.py")
    elif configured > 0:
        print("\n⚠️  Partial configuration")
        print(f"   {configured}/{len(keys)} API keys configured")
        print("\n🔑 To complete setup:")
        print("   python3 auto_setup_api_keys.py")
    else:
        print("\n❌ Not configured yet")
        print("\n🚀 To get started:")
        print("   ./AUTOMATE_EVERYTHING.sh")
        print("   OR")
        print("   python3 ONE_CLICK_SETUP.py")
    
    print("\n" + "="*80)
    print("💡 Quick Commands:")
    print("="*80)
    print("   Setup:    ./AUTOMATE_EVERYTHING.sh")
    print("   Status:   python3 check_automation_status.py")
    print("   Logs:     tail -f logs/automation.log")
    print("   Stop:     pkill -f START_COMPLETE_AUTOMATION")
    print("="*80 + "\n")


if __name__ == "__main__":
    try:
        check_status()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
