#!/usr/bin/env python3
"""
Cole Medin Channel Learner

Continuously learns from Cole Medin's YouTube channel using the
production-grade YouTubeLiveLearner with ChromaDB RAG storage.

Cole Medin: https://www.youtube.com/@ColeMedin
  - Agentic AI, AI Agents, LangGraph, CrewAI, n8n, Pydantic AI, etc.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# Cole Medin's YouTube channel and confirmed video IDs
COLE_MEDIN_CHANNEL_URL = "https://www.youtube.com/@ColeMedin/videos"
COLE_MEDIN_CHANNEL_ID  = "UCz7MolJa20jJWqNMHo3grKg"
COLE_MEDIN_PLAYLIST_URL = (
    "https://www.youtube.com/playlist?list="
    "PLtK_vZNfkRxhFPIzTzNjZ00S4u7OAjqNQ"   # 'All Videos' playlist
)

# Seed videos to bootstrap learning while channel discovery runs
COLE_MEDIN_SEED_VIDEOS: List[str] = [
    "https://www.youtube.com/watch?v=JGwWNGJdvx8",  # Agentic AI
    "https://www.youtube.com/watch?v=si8z_jk7g5c",
    "https://www.youtube.com/watch?v=wH7vqrz8oOs",
    "https://www.youtube.com/watch?v=9YL3QRXEXDY",  # n8n + Claude
    "https://www.youtube.com/watch?v=BPunMV4LScQ",  # LangGraph agents
    "https://www.youtube.com/watch?v=rv2fqxFX0Rg",  # Pydantic AI
    "https://www.youtube.com/watch?v=qO5PFbX6kgg",  # CrewAI
]


class ColeMedinChannelLearner:
    """
    Continuously learns from Cole Medin's YouTube channel.

    Uses YouTubeLiveLearner for:
      - Real transcript extraction (youtube-transcript-api + yt-dlp fallback)
      - Semantic chunking and ChromaDB vector storage
      - RAG-powered insight extraction
      - Continuous watch-list polling
    """

    RESULTS_FILE = Path("generated_content/cole_medin_learnings.json")

    def __init__(self, router=None):
        from YOUTUBE_LIVE_LEARNER import get_learner
        self.learner = get_learner(router=router)
        self.router = router

        self.stats: Dict[str, Any] = {
            "videos_processed": 0,
            "successful_learnings": 0,
            "failed_videos": [],
            "total_chunks": 0,
            "techniques_found": [],
            "start_time": datetime.utcnow().isoformat(),
            "last_learning": None,
        }
        logger.info("Cole Medin Channel Learner ready")

    # ── Channel discovery ──────────────────────────────────────

    async def discover_channel_videos(self, max_videos: int = 50) -> List[str]:
        """
        Discover video URLs from Cole Medin's channel via yt-dlp.
        Returns a list of video URLs sorted newest-first.
        """
        try:
            import yt_dlp
            ydl_opts = {
                "quiet": True,
                "extract_flat": True,
                "playlistend": max_videos,
            }
            urls: List[str] = []
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(COLE_MEDIN_CHANNEL_URL, download=False)
                for entry in info.get("entries", []) or []:
                    vid_id = entry.get("id") or ""
                    if vid_id:
                        urls.append(f"https://www.youtube.com/watch?v={vid_id}")
            logger.info(f"Discovered {len(urls)} videos from Cole Medin's channel")
            return urls
        except Exception as e:
            logger.warning(f"Channel discovery failed ({e}), using seed list")
            return COLE_MEDIN_SEED_VIDEOS.copy()

    # ── Core learning loop ─────────────────────────────────────

    async def learn_latest(self, max_videos: int = 20) -> Dict[str, Any]:
        """
        Discover and process the latest videos from the channel.
        Returns a summary of what was learned.
        """
        logger.info("Starting Cole Medin learning cycle")
        video_urls = await self.discover_channel_videos(max_videos)

        # Add to the learner's persistent watch list
        for url in video_urls:
            self.learner.add_to_watch_list(url)

        successes, failures = 0, []
        for url in video_urls:
            try:
                learning = await self.learner.learn_from_video(url)
                self.stats["videos_processed"] += 1
                self.stats["successful_learnings"] += 1
                self.stats["total_chunks"] += len(learning.chunks)
                self.stats["last_learning"] = datetime.utcnow().isoformat()

                # Collect AI/agent technique keywords
                topics = learning.insights.get("key_topics", [])
                for t in topics:
                    if t not in self.stats["techniques_found"]:
                        self.stats["techniques_found"].append(t)

                successes += 1
                logger.info(f"Learned: '{learning.title}' ({len(learning.chunks)} chunks)")
                await asyncio.sleep(1)   # polite delay between requests

            except Exception as e:
                failures.append({"url": url, "error": str(e)})
                logger.warning(f"Skipped {url}: {e}")

        self.stats["failed_videos"] = failures[-20:]  # keep last 20 failures
        self._save_results()

        summary = {
            "cycle_videos": len(video_urls),
            "newly_learned": successes,
            "failures": len(failures),
            "total_chunks_in_store": self.learner.store.count,
            "techniques_found": self.stats["techniques_found"][:20],
        }
        logger.info(
            f"Cole Medin cycle complete: {successes}/{len(video_urls)} videos, "
            f"{self.learner.store.count} total chunks in store"
        )
        return summary

    async def start_continuous_learning(self, interval_minutes: int = 60):
        """
        Continuously re-check Cole Medin's channel for new videos.
        Also bootstraps with seed videos on first run.
        """
        # First: bootstrap from seed list immediately
        for url in COLE_MEDIN_SEED_VIDEOS:
            self.learner.add_to_watch_list(url)
            try:
                await self.learner.learn_from_video(url)
                await asyncio.sleep(1)
            except Exception as e:
                logger.debug(f"Seed video {url}: {e}")

        logger.info(
            f"Cole Medin continuous learning started "
            f"(refresh every {interval_minutes}m)"
        )

        while True:
            try:
                await self.learn_latest(max_videos=30)
            except Exception as e:
                logger.error(f"Learning cycle error: {e}")

            await asyncio.sleep(interval_minutes * 60)

    # ── RAG query ──────────────────────────────────────────────

    async def query(self, question: str) -> Dict[str, Any]:
        """Query the Cole Medin knowledge base."""
        return await self.learner.query(question)

    # ── Persistence ────────────────────────────────────────────

    def _save_results(self):
        self.RESULTS_FILE.parent.mkdir(exist_ok=True)
        self.RESULTS_FILE.write_text(
            json.dumps({
                "stats": self.stats,
                "learner_status": self.learner.status(),
                "updated_at": datetime.utcnow().isoformat(),
            }, indent=2)
        )

    def status(self) -> Dict[str, Any]:
        return {
            **self.stats,
            "learner_status": self.learner.status(),
        }


# ── Module singleton ───────────────────────────────────────────
_instance: Optional[ColeMedinChannelLearner] = None

def get_cole_medin_learner(router=None) -> ColeMedinChannelLearner:
    global _instance
    if _instance is None:
        _instance = ColeMedinChannelLearner(router=router)
    return _instance


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s - %(levelname)s - %(message)s")

    async def demo():
        from FREE_LLM_ROUTER import get_router
        router = get_router()
        learner = ColeMedinChannelLearner(router=router)
        print("Status:", learner.status())

        # Learn from one seed video
        try:
            result = await learner.learner.learn_from_video(COLE_MEDIN_SEED_VIDEOS[0])
            print(f"\nLearned: {result.title}")
            print(f"Chunks: {len(result.chunks)}")
            print(f"Summary: {result.insights.get('summary', '')[:300]}")

            qa = await learner.query("What AI agent frameworks does Cole Medin recommend?")
            print(f"\nQ&A Answer: {qa.get('answer', '')[:300]}")
        except Exception as e:
            print(f"Error: {e}")

    asyncio.run(demo())
