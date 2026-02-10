#!/usr/bin/env python3
"""
Cole Medin Channel Continuous Learner
Actually learns from Cole Medin's YouTube channel
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from FIXED_YOUTUBE_LEARNER import FixedYouTubeLearner

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ColeMedinChannelLearner:
    """Continuous learner for Cole Medin's channel"""
    
    def __init__(self):
        self.learner = FixedYouTubeLearner()
        
        # Real working videos (use the one we know works + other potential ones)
        self.cole_medin_videos = [
            "https://www.youtube.com/watch?v=JGwWNGJdvx8",  # This one works (we tested it)
            "https://www.youtube.com/watch?v=si8z_jk7g5c",  # Try another
            "https://www.youtube.com/watch?v=wH7vqrz8oOs",  # And another
            # In production, would get actual Cole Medin videos from his channel
            # https://www.youtube.com/@ColeMedin
        ]
        
        # Learning statistics
        self.learning_stats = {
            "videos_processed": 0,
            "successful_learnings": 0,
            "cole_techniques_found": [],
            "total_insights": 0,
            "start_time": datetime.now().isoformat(),
            "last_learning": None
        }
        
        logger.info("🧠 Cole Medin Channel Learner initialized")
        logger.info(f"📺 Found {len(self.cole_medin_videos)} Cole Medin videos")
    
    async def start_continuous_learning(self, interval_minutes: int = 30):
        """Start continuous learning from Cole Medin's channel"""
        logger.info(f"🚀 Starting continuous Cole Medin learning (every {interval_minutes} minutes)")
        
        while True:
            try:
                logger.info(f"🔄 Starting Cole Medin learning cycle...")
                
                # Process all videos
                await self._process_all_videos()
                
                # Update statistics
                self._update_stats()
                
                # Log progress
                self._log_progress()
                
                # Save learning results
                await self._save_learning_results()
                
                # Wait for next cycle
                logger.info(f"⏰ Waiting {interval_minutes} minutes before next cycle...")
                await asyncio.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                logger.info("🛑 Cole Medin learning stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Learning cycle error: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def _process_all_videos(self):
        """Process all Cole Medin videos"""
        for i, video_url in enumerate(self.cole_medin_videos):
            logger.info(f"🎥 Processing Cole Medin video {i+1}/{len(self.cole_medin_videos)}: {video_url}")
            
            try:
                # Learn from video
                result = await self.learner.transcribe_and_learn(video_url)
                
                if result.get('success'):
                    self.learning_stats["successful_learnings"] += 1
                    
                    # Extract Cole-specific techniques
                    cole_techniques = self._extract_cole_techniques(result)
                    self.learning_stats["cole_techniques_found"].extend(cole_techniques)
                    
                    # Count insights
                    insights_count = len(result.get('insights', []))
                    self.learning_stats["total_insights"] += insights_count
                    
                    logger.info(f"✅ Video {i+1} successful: {insights_count} insights, {len(cole_techniques)} Cole techniques")
                    
                    # Save individual video result
                    await self._save_video_result(video_url, result)
                    
                else:
                    logger.warning(f"⚠️ Video {i+1} failed: {result.get('error')}")
                
                self.learning_stats["videos_processed"] += 1
                self.learning_stats["last_learning"] = datetime.now().isoformat()
                
                # Small delay between videos
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"❌ Error processing video {i+1}: {e}")
    
    def _extract_cole_techniques(self, result: Dict[str, Any]) -> List[str]:
        """Extract Cole Medin specific techniques"""
        techniques = []
        
        # Get transcript and analysis
        transcript = result.get('transcript', '')
        analysis = result.get('analysis', {})
        
        # Cole Medin's signature techniques
        cole_techniques = [
            "agent zero", "archon 2", "bmad", "agent fleet",
            "zero-shot coordination", "autonomous orchestration",
            "agent communication protocols", "distributed decision making",
            "emergent behavior", "agent specialization",
            "real-time coordination", "behavioral modeling",
            "fleet management", "agent coordination"
        ]
        
        transcript_lower = transcript.lower()
        
        for technique in cole_techniques:
            if technique in transcript_lower:
                techniques.append(technique)
        
        # Also check analysis for relevant topics
        key_topics = analysis.get('key_topics', [])
        for topic in key_topics:
            if any(keyword in topic.lower() for keyword in ['agent', 'coordination', 'fleet', 'orchestration']):
                techniques.append(topic)
        
        # Remove duplicates
        techniques = list(set(techniques))
        
        return techniques
    
    def _update_stats(self):
        """Update learning statistics"""
        # Remove duplicates from techniques
        self.learning_stats["cole_techniques_found"] = list(set(self.learning_stats["cole_techniques_found"]))
    
    def _log_progress(self):
        """Log learning progress"""
        stats = self.learning_stats
        
        logger.info("📊 Cole Medin Learning Progress:")
        logger.info(f"   Videos Processed: {stats['videos_processed']}")
        logger.info(f"   Successful Learnings: {stats['successful_learnings']}")
        logger.info(f"   Total Insights: {stats['total_insights']}")
        logger.info(f"   Cole Techniques Found: {len(stats['cole_techniques_found'])}")
        
        if stats['cole_techniques_found']:
            logger.info(f"   Techniques: {', '.join(stats['cole_techniques_found'][:5])}")
    
    async def _save_video_result(self, video_url: str, result: Dict[str, Any]):
        """Save individual video learning result via the shared learner's persistence"""
        try:
            # Enrich with Cole-specific metadata
            result["cole_techniques"] = self._extract_cole_techniques(result)
            # Persist through the canonical learner storage
            self.learner._save_learning(result)
        except Exception as e:
            logger.error(f"❌ Failed to save video result: {e}")
    
    async def _save_learning_results(self):
        """Save overall learning results"""
        try:
            results_file = Path("generated_content") / "cole_medin_channel_learning.json"
            results_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Update duration
            start_time = datetime.fromisoformat(self.learning_stats["start_time"])
            duration = datetime.now() - start_time
            
            save_data = {
                "learning_session": {
                    "start_time": self.learning_stats["start_time"],
                    "duration_hours": duration.total_seconds() / 3600,
                    "status": "active"
                },
                "statistics": self.learning_stats,
                "cole_techniques_mastered": self.learning_stats["cole_techniques_found"],
                "last_updated": datetime.now().isoformat()
            }
            
            results_file.write_text(json.dumps(save_data, indent=2, ensure_ascii=False))
            logger.info("💾 Learning results saved")
            
        except Exception as e:
            logger.error(f"❌ Failed to save learning results: {e}")
    
    def get_learning_summary(self) -> Dict[str, Any]:
        """Get comprehensive learning summary"""
        stats = self.learning_stats
        
        # Calculate success rate
        success_rate = 0.0
        if stats["videos_processed"] > 0:
            success_rate = stats["successful_learnings"] / stats["videos_processed"] * 100
        
        # Calculate duration
        start_time = datetime.fromisoformat(stats["start_time"])
        duration = datetime.now() - start_time
        
        return {
            "session_info": {
                "start_time": stats["start_time"],
                "duration_hours": duration.total_seconds() / 3600,
                "status": "active"
            },
            "learning_metrics": {
                "videos_processed": stats["videos_processed"],
                "successful_learnings": stats["successful_learnings"],
                "success_rate_percent": success_rate,
                "total_insights": stats["total_insights"],
                "cole_techniques_found": len(stats["cole_techniques_found"])
            },
            "cole_techniques": {
                "total_found": len(stats["cole_techniques_found"]),
                "techniques": stats["cole_techniques_found"]
            },
            "efficiency": {
                "videos_per_hour": stats["videos_processed"] / max(duration.total_seconds() / 3600, 1),
                "insights_per_video": stats["total_insights"] / max(stats["successful_learnings"], 1)
            }
        }

# ============================================================================
# START COLE MEDIN LEARNING
# ============================================================================

async def start_cole_medin_learning():
    """Start learning from Cole Medin's channel"""
    print("🧠 Starting Cole Medin Channel Learning")
    print("=" * 50)
    
    learner = ColeMedinChannelLearner()
    
    try:
        # Start continuous learning (every 30 minutes)
        await learner.start_continuous_learning(interval_minutes=30)
        
    except KeyboardInterrupt:
        logger.info("🛑 Learning stopped by user")
        
        # Show final summary
        summary = learner.get_learning_summary()
        print("\n📊 Final Cole Medin Learning Summary:")
        print(json.dumps(summary, indent=2))

# ============================================================================
# QUICK TEST MODE
# ============================================================================

async def test_cole_medin_learning():
    """Quick test of Cole Medin learning"""
    print("🧠 Testing Cole Medin Channel Learning")
    print("=" * 40)
    
    learner = ColeMedinChannelLearner()
    
    # Process first few videos
    test_videos = learner.cole_medin_videos[:3]
    
    for i, video_url in enumerate(test_videos):
        print(f"\n🎥 Testing video {i+1}: {video_url}")
        
        result = await learner.learner.transcribe_and_learn(video_url)
        
        if result.get('success'):
            techniques = learner._extract_cole_techniques(result)
            insights_count = len(result.get('insights', []))
            
            print(f"✅ Success: {insights_count} insights, {len(techniques)} Cole techniques")
            print(f"🧠 Relevance: {result['analysis'].get('relevance_score', 0)}")
            print(f"🔑 Topics: {result['analysis'].get('key_topics', [])}")
            
            if techniques:
                print(f"🤖 Cole Techniques: {techniques}")
        else:
            print(f"❌ Failed: {result.get('error')}")
    
    # Show summary
    summary = learner.get_learning_summary()
    print(f"\n📈 Test Summary:")
    print(json.dumps(summary, indent=2))

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        # Continuous learning mode
        asyncio.run(start_cole_medin_learning())
    elif len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Test mode
        asyncio.run(test_cole_medin_learning())
    else:
        # Default to continuous learning
        asyncio.run(start_cole_medin_learning())

if __name__ == "__main__":
    main()
