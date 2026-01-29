#!/usr/bin/env python3
import asyncio
import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from VIRAL_GROWTH_ENGINE import ViralGrowthEngine
from AUTOMATED_REVENUE_ENGINE import revenue_engine

async def main():
    print("🚀 Initiating NarcoGuard Showcase Thread...")
    viral = ViralGrowthEngine(revenue_engine)
    
    # Force a hero story generation with 'show off the app' context
    system_prompt = "You are a master storyteller and social media growth hacker."
    user_prompt = """
    Create a 6-tweet showcase thread for NarcoGuard.
    Focus on: 'The App meets The Watch'.
    
    Story beats:
    1. Hook: 80 lives saved starts with 80 watches.
    2. The Tech: How the NG2 watch monitors vitals in silence.
    3. The Software: Showcase the live app demo (https://v0-narcoguard-pwa-build.vercel.app).
    4. The Mission: 80 units for Broome County.
    5. The Community: Why this matters now.
    6. Call to Action: Donate for the first 80: https://gofund.me/9acf270ea
    
    Include screenshot descriptions and emojis.
    """
    
    print("🤖 Generating with AI (or fallback)...")
    content = revenue_engine.generate_ai_content(system_prompt, user_prompt)
    
    print("\n" + "="*60)
    print("🧵 SHOWCASE THREAD GENERATED")
    print("="*60)
    print(content)
    print("="*60 + "\n")
    
    # Save to viral content
    timestamp = Path("generated_content/viral") / f"showcase_thread_{os.getpid()}.md"
    timestamp.write_text(content)
    print(f"✅ Saved to {timestamp}")

if __name__ == "__main__":
    asyncio.run(main())
