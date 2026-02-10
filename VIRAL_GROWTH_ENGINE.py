#!/usr/bin/env python3
"""
VIRAL GROWTH ENGINE
Implements high-impact growth experiments for NarcoGuard.
"""

import os
import json
import logging
import asyncio
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class ViralGrowthEngine:
    def __init__(self, revenue_engine):
        self.revenue_engine = revenue_engine
        self.output_dir = Path("generated_content/viral")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.experiments_log = self.output_dir / "experiment_history.jsonl"
        self.offline_mode = os.getenv("CHATTY_OFFLINE_MODE", "false").lower() == "true"
        self.is_running = False
        self.status = "stopped"
        self.last_run = None
        self.last_error = None
        self.experiment_interval = int(os.getenv("CHATTY_VIRAL_INTERVAL_SECONDS", 60 * 60 * 12))

    async def run_hero_story_loop(self):
        """Generates a compelling 'Hero Story' thread for social media."""
        logger.info("🎬 Viral Growth: Running Hero Story Loop...")
        
        system_prompt = "You are a master storyteller and social media growth hacker."
        user_prompt = """
        Create a 5-tweet thread telling the story of NarcoGuard's impact.
        Focus on: 'The Guardian on the Wrist'. 
        
        Story beats:
        1. The problem of solitary overdose.
        2. The 'Wait, there's a better way' moment.
        3. Real-time demo: Watch the AI detect a crisis at https://v0-narcoguard-pwa-build.vercel.app
        4. The impact: Seconds saved, lives unified, families kept whole.
        5. Call to action: Help us put these on 80 more wrists: https://gofund.me/9acf270ea
        
        Include emojis and high-engagement hooks.
        """
        
        try:
            if self.offline_mode:
                raise RuntimeError("offline_mode_enabled")
            thread_content = await self.revenue_engine.generate_ai_content(system_prompt, user_prompt)
            if not thread_content:
                raise RuntimeError("empty_ai_response")
        except Exception as e:
            logger.warning(f"⚠️ Hero story AI generation failed, using offline template: {e}")
            thread_content = self._offline_hero_story()

        filename = self._write_output("hero_story_thread", thread_content)
        logger.info(f"✅ Hero Story Thread generated: {filename}")
        self._log_experiment("hero_story_loop", "success", {"file": str(filename)})
        return thread_content

    async def launch_ugc_challenge(self):
        """Drafts a campaign for User Generated Content (UGC)."""
        logger.info("🚀 Viral Growth: Drafting UGC Challenge...")
        
        system_prompt = "You are a viral marketing specialist."
        user_prompt = """
        Draft a plan for the #NarcoGuardChallenge.
        The goal is to get community members and first responders to share why 'Seconds Matter'.
        
        Include:
        1. Challenge Name & Tagline.
        2. 7 days of prompts.
        3. Incentive/Reward structure.
        4. Draft of the announcement post.
        """
        
        try:
            if self.offline_mode:
                raise RuntimeError("offline_mode_enabled")
            plan = await self.revenue_engine.generate_ai_content(system_prompt, user_prompt)
            if not plan:
                raise RuntimeError("empty_ai_response")
        except Exception as e:
            logger.warning(f"⚠️ UGC Challenge AI generation failed, using offline template: {e}")
            plan = self._offline_ugc_challenge()

        filename = self._write_output("ugc_challenge_plan", plan)
        logger.info(f"✅ UGC Challenge plan generated: {filename}")
        self._log_experiment("ugc_challenge", "success", {"file": str(filename)})
        return plan

    def _log_experiment(self, name, status, details):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "experiment": name,
            "status": status,
            "details": details
        }
        with open(self.experiments_log, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def _write_output(self, prefix, content):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = self.output_dir / f"{prefix}_{timestamp}.md"
        filename.write_text(content, encoding="utf-8")
        return filename

    def _offline_hero_story(self):
        """Deterministic offline template when LLMs are unavailable."""
        return "\n".join(
            [
                "1) Every day, someone overdoses alone. Minutes are lost. Families wait.",
                "2) We built NarcoGuard because there had to be a faster way than hope.",
                "3) See the live demo of our automated detection: https://v0-narcoguard-pwa-build.vercel.app",
                "4) Seconds saved turn into lives saved and families kept whole.",
                "5) Help put 80 more on wrists in Broome County: https://gofund.me/9acf270ea",
            ]
        )

    def _offline_ugc_challenge(self):
        """Deterministic offline template when LLMs are unavailable."""
        return "\n".join(
            [
                "#NarcoGuardChallenge: Seconds Matter",
                "",
                "Tagline: Share the moment you realized seconds can save a life.",
                "",
                "7-Day Prompt Plan:",
                "Day 1: Why seconds matter in your community.",
                "Day 2: A story of a life saved or a close call.",
                "Day 3: The one tool you wish every responder had.",
                "Day 4: How tech can bridge the response gap.",
                "Day 5: The person you dedicate this to.",
                "Day 6: What statewide coverage would change.",
                "Day 7: Call your community to action.",
                "",
                "Incentive: Feature stories + donated units to partner orgs.",
                "",
                "Announcement Draft:",
                "We’re launching the #NarcoGuardChallenge to spotlight why seconds matter.",
                "Share your story, tag us, and help bring lifesaving tech to more wrists.",
            ]
        )

    async def start(self):
        """Start scheduled viral growth experiments."""
        self.is_running = True
        self.status = "active"
        logger.info("🚀 Viral Growth Engine STARTED")
        while self.is_running:
            try:
                await self.run_hero_story_loop()
                await self.launch_ugc_challenge()
                self.last_run = datetime.now().isoformat()
                self.last_error = None
                await self._sleep_with_stop(self.experiment_interval)
            except Exception as e:
                self.last_error = str(e)
                logger.error(f"Viral growth cycle error: {e}")
                await self._sleep_with_stop(3600)

    async def stop(self):
        """Stop scheduled viral growth experiments."""
        self.is_running = False
        self.status = "stopped"
        logger.info("🛑 Viral Growth Engine STOPPED")

    async def _sleep_with_stop(self, duration_seconds: int):
        end_at = asyncio.get_event_loop().time() + duration_seconds
        while self.is_running and asyncio.get_event_loop().time() < end_at:
            remaining = end_at - asyncio.get_event_loop().time()
            await asyncio.sleep(min(5, max(0.0, remaining)))

    def get_status(self):
        return {
            "status": self.status,
            "active_experiments": ["hero_story_loop", "ugc_challenge"],
            "output_directory": str(self.output_dir),
            "offline_mode": self.offline_mode,
            "recent_outputs": self.list_outputs(limit=5),
            "last_run": self.last_run,
            "last_error": self.last_error,
        }

    def list_outputs(self, limit=10):
        outputs = []
        for path in sorted(self.output_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True):
            outputs.append(
                {
                    "file": str(path),
                    "name": path.name,
                    "modified_at": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
                }
            )
            if len(outputs) >= limit:
                break
        return outputs
