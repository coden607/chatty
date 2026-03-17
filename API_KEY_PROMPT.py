#!/usr/bin/env python3
"""
CHATTY API Key Configuration Prompt
Interactive setup for all required and optional API keys
"""

import os
import json
from pathlib import Path
from datetime import datetime

# Configuration file
CONFIG_FILE = Path("~/.config/chatty/api_keys_config.json").expanduser()
ENV_FILE = Path(".env")

def load_existing_keys():
    """Load existing API keys from environment"""
    keys = {}
    
    # Required for full operation
    keys["STRIPE_SECRET_KEY"] = os.getenv("STRIPE_SECRET_KEY", "")
    keys["STRIPE_PUBLISHABLE_KEY"] = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    
    # AI Providers
    keys["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")
    keys["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY", "")
    keys["XAI_API_KEY"] = os.getenv("XAI_API_KEY", "")
    keys["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY", "")
    keys["NVIDIA_API_KEY"] = os.getenv("NVIDIA_API_KEY", "")
    
    # Communication
    keys["SENDGRID_API_KEY"] = os.getenv("SENDGRID_API_KEY", "")
    keys["TWILIO_ACCOUNT_SID"] = os.getenv("TWILIO_ACCOUNT_SID", "")
    keys["TWILIO_AUTH_TOKEN"] = os.getenv("TWILIO_AUTH_TOKEN", "")
    
    # Social Media
    keys["X_BEARER_TOKEN"] = os.getenv("X_BEARER_TOKEN", "")
    keys["X_CONSUMER_KEY"] = os.getenv("X_CONSUMER_KEY", "")
    keys["X_CONSUMER_SECRET"] = os.getenv("X_CONSUMER_SECRET", "")
    keys["X_ACCESS_TOKEN"] = os.getenv("X_ACCESS_TOKEN", "")
    keys["X_ACCESS_SECRET"] = os.getenv("X_ACCESS_SECRET", "")
    keys["LINKEDIN_CLIENT_ID"] = os.getenv("LINKEDIN_CLIENT_ID", "")
    keys["LINKEDIN_CLIENT_SECRET"] = os.getenv("LINKEDIN_CLIENT_SECRET", "")
    
    # Search & Data
    keys["BRAVE_API_KEY"] = os.getenv("BRAVE_API_KEY", "")
    keys["SERP_API_KEY"] = os.getenv("SERP_API_KEY", "")
    keys["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY", "")
    
    # Development
    keys["GITHUB_TOKEN"] = os.getenv("GITHUB_TOKEN", "")
    keys["HUGGINGFACE_TOKEN"] = os.getenv("HUGGINGFACE_TOKEN", "")
    keys["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY", "")
    
    return keys


def prompt_for_keys():
    """Interactive prompt for API keys"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║              🔑 CHATTY API Key Configuration                                 ║
║                                                                              ║
║   Configure your API keys to unlock full system capabilities                 ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
    
    keys = load_existing_keys()
    new_keys = {}
    
    # Helper function for prompts
    def ask(key, description, required=False, example="", current_value=""):
        prefix = "🔴 REQUIRED" if required else "🟢 Optional"
        current = f" [Current: {current_value[:20]}...]" if current_value else ""
        
        print(f"\n{prefix}: {key}")
        print(f"   {description}")
        if example:
            print(f"   Example: {example}")
        if current:
            print(f"   {current}")
        
        value = input(f"   Enter value (press Enter to {'keep current' if current_value else 'skip'}): ").strip()
        
        if value:
            return value
        return current_value if current_value else None
    
    print("\n" + "="*80)
    print("SECTION 1: PAYMENT PROCESSING (Required for revenue)")
    print("="*80)
    
    new_keys["STRIPE_SECRET_KEY"] = ask(
        "STRIPE_SECRET_KEY",
        "Stripe secret key for payment processing",
        required=True,
        example="sk_live_...",
        current_value=keys.get("STRIPE_SECRET_KEY", "")
    )
    
    new_keys["STRIPE_PUBLISHABLE_KEY"] = ask(
        "STRIPE_PUBLISHABLE_KEY",
        "Stripe publishable key for frontend",
        required=True,
        example="pk_live_...",
        current_value=keys.get("STRIPE_PUBLISHABLE_KEY", "")
    )
    
    print("\n" + "="*80)
    print("SECTION 2: AI PROVIDERS (At least 2 recommended for failover)")
    print("="*80)
    
    new_keys["OPENAI_API_KEY"] = ask(
        "OPENAI_API_KEY",
        "OpenAI API key for GPT-4, GPT-3.5",
        required=False,
        example="sk-proj-...",
        current_value=keys.get("OPENAI_API_KEY", "")
    )
    
    new_keys["ANTHROPIC_API_KEY"] = ask(
        "ANTHROPIC_API_KEY",
        "Anthropic API key for Claude 3.5 Sonnet/Opus",
        required=False,
        example="sk-ant-...",
        current_value=keys.get("ANTHROPIC_API_KEY", "")
    )
    
    new_keys["XAI_API_KEY"] = ask(
        "XAI_API_KEY",
        "xAI API key for Grok-3 (already configured!)",
        required=False,
        example="xai-...",
        current_value=keys.get("XAI_API_KEY", "")
    )
    
    new_keys["GOOGLE_API_KEY"] = ask(
        "GOOGLE_API_KEY",
        "Google AI API key for Gemini models",
        required=False,
        example="AIza...",
        current_value=keys.get("GOOGLE_API_KEY", "")
    )
    
    new_keys["NVIDIA_API_KEY"] = ask(
        "NVIDIA_API_KEY",
        "NVIDIA Build API key for Kimi K2.5 (already configured!)",
        required=False,
        example="nvapi-...",
        current_value=keys.get("NVIDIA_API_KEY", "")
    )
    
    print("\n" + "="*80)
    print("SECTION 3: EMAIL & COMMUNICATION")
    print("="*80)
    
    new_keys["SENDGRID_API_KEY"] = ask(
        "SENDGRID_API_KEY",
        "SendGrid API key for email automation (already configured!)",
        required=False,
        example="SG.xxx",
        current_value=keys.get("SENDGRID_API_KEY", "")
    )
    
    new_keys["TWILIO_ACCOUNT_SID"] = ask(
        "TWILIO_ACCOUNT_SID",
        "Twilio Account SID for SMS",
        required=False,
        example="AC...",
        current_value=keys.get("TWILIO_ACCOUNT_SID", "")
    )
    
    new_keys["TWILIO_AUTH_TOKEN"] = ask(
        "TWILIO_AUTH_TOKEN",
        "Twilio Auth Token",
        required=False,
        example="xxx...",
        current_value=keys.get("TWILIO_AUTH_TOKEN", "")
    )
    
    print("\n" + "="*80)
    print("SECTION 4: SOCIAL MEDIA AUTOMATION")
    print("="*80)
    
    new_keys["X_BEARER_TOKEN"] = ask(
        "X_BEARER_TOKEN",
        "Twitter/X Bearer Token",
        required=False,
        example="AAAA...",
        current_value=keys.get("X_BEARER_TOKEN", "")
    )
    
    new_keys["X_CONSUMER_KEY"] = ask(
        "X_CONSUMER_KEY",
        "Twitter/X Consumer Key (API Key)",
        required=False,
        example="xxx...",
        current_value=keys.get("X_CONSUMER_KEY", "")
    )
    
    new_keys["X_CONSUMER_SECRET"] = ask(
        "X_CONSUMER_SECRET",
        "Twitter/X Consumer Secret",
        required=False,
        example="xxx...",
        current_value=keys.get("X_CONSUMER_SECRET", "")
    )
    
    new_keys["X_ACCESS_TOKEN"] = ask(
        "X_ACCESS_TOKEN",
        "Twitter/X Access Token",
        required=False,
        example="xxx...",
        current_value=keys.get("X_ACCESS_TOKEN", "")
    )
    
    new_keys["X_ACCESS_SECRET"] = ask(
        "X_ACCESS_SECRET",
        "Twitter/X Access Token Secret",
        required=False,
        example="xxx...",
        current_value=keys.get("X_ACCESS_SECRET", "")
    )
    
    new_keys["LINKEDIN_CLIENT_ID"] = ask(
        "LINKEDIN_CLIENT_ID",
        "LinkedIn Client ID for B2B outreach",
        required=False,
        example="xxx...",
        current_value=keys.get("LINKEDIN_CLIENT_ID", "")
    )
    
    new_keys["LINKEDIN_CLIENT_SECRET"] = ask(
        "LINKEDIN_CLIENT_SECRET",
        "LinkedIn Client Secret",
        required=False,
        example="xxx...",
        current_value=keys.get("LINKEDIN_CLIENT_SECRET", "")
    )
    
    print("\n" + "="*80)
    print("SECTION 5: SEARCH & RESEARCH (For MCP tools)")
    print("="*80)
    
    new_keys["BRAVE_API_KEY"] = ask(
        "BRAVE_API_KEY",
        "Brave Search API key for web search MCP tool",
        required=False,
        example="BSA...",
        current_value=keys.get("BRAVE_API_KEY", "")
    )
    
    new_keys["SERP_API_KEY"] = ask(
        "SERP_API_KEY",
        "SerpAPI key for Google search results",
        required=False,
        example="xxx...",
        current_value=keys.get("SERP_API_KEY", "")
    )
    
    new_keys["TAVILY_API_KEY"] = ask(
        "TAVILY_API_KEY",
        "Tavily API key for AI search",
        required=False,
        example="tvly-...",
        current_value=keys.get("TAVILY_API_KEY", "")
    )
    
    print("\n" + "="*80)
    print("SECTION 6: DEVELOPMENT & INTEGRATION")
    print("="*80)
    
    new_keys["GITHUB_TOKEN"] = ask(
        "GITHUB_TOKEN",
        "GitHub Personal Access Token for MCP git operations",
        required=False,
        example="ghp_...",
        current_value=keys.get("GITHUB_TOKEN", "")
    )
    
    new_keys["HUGGINGFACE_TOKEN"] = ask(
        "HUGGINGFACE_TOKEN",
        "HuggingFace token for model access (already configured!)",
        required=False,
        example="hf_...",
        current_value=keys.get("HUGGINGFACE_TOKEN", "")
    )
    
    new_keys["LANGCHAIN_API_KEY"] = ask(
        "LANGCHAIN_API_KEY",
        "LangSmith API key for observability",
        required=False,
        example="lsv2_...",
        current_value=keys.get("LANGCHAIN_API_KEY", "")
    )
    
    return {k: v for k, v in new_keys.items() if v is not None}


def save_keys(keys):
    """Save keys to .env file"""
    print("\n💾 Saving configuration...")
    
    # Read existing .env
    env_content = ""
    if ENV_FILE.exists():
        env_content = ENV_FILE.read_text()
    
    # Update or add keys
    for key, value in keys.items():
        pattern = f"{key}=.*"
        import re
        if re.search(f"^{pattern}$", env_content, re.MULTILINE):
            # Update existing
            env_content = re.sub(
                f"^{key}=.*$",
                f"{key}={value}",
                env_content,
                flags=re.MULTILINE
            )
        else:
            # Add new
            env_content += f"\n{key}={value}"
    
    # Save
    ENV_FILE.write_text(env_content)
    
    # Also save to secrets file
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps({
        "keys_configured": list(keys.keys()),
        "updated_at": datetime.now().isoformat()
    }, indent=2))
    
    print(f"✅ Configuration saved to {ENV_FILE}")
    print(f"✅ Key registry saved to {CONFIG_FILE}")


def print_summary(keys):
    """Print configuration summary"""
    print("\n" + "="*80)
    print("CONFIGURATION SUMMARY")
    print("="*80)
    
    categories = {
        "Payment Processing": ["STRIPE_SECRET_KEY", "STRIPE_PUBLISHABLE_KEY"],
        "AI Providers": ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "XAI_API_KEY", "GOOGLE_API_KEY", "NVIDIA_API_KEY"],
        "Communication": ["SENDGRID_API_KEY", "TWILIO_ACCOUNT_SID"],
        "Social Media": ["X_BEARER_TOKEN", "LINKEDIN_CLIENT_ID"],
        "Search & Research": ["BRAVE_API_KEY", "SERP_API_KEY", "TAVILY_API_KEY"],
        "Development": ["GITHUB_TOKEN", "HUGGINGFACE_TOKEN", "LANGCHAIN_API_KEY"]
    }
    
    for category, key_list in categories.items():
        print(f"\n{category}:")
        for key in key_list:
            configured = "✅" if key in keys and keys[key] else "❌"
            print(f"  {configured} {key}")
    
    print("\n" + "="*80)
    print("NEXT STEPS:")
    print("="*80)
    print("1. Restart the CHATTY automation system:")
    print("   ./launch_chatty.sh")
    print("\n2. Verify all integrations are working:")
    print("   python3 check_automation_status.py")
    print("\n3. Check API status dashboard:")
    print("   http://localhost:8080/api/status")


def main():
    """Main entry point"""
    try:
        keys = prompt_for_keys()
        
        if keys:
            save_keys(keys)
            print_summary(keys)
        else:
            print("\n⚠️ No keys were entered. Existing configuration unchanged.")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Configuration cancelled.")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
