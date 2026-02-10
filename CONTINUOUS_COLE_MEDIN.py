#!/usr/bin/env python3
"""
Continuous Cole Medin Channel Learning
Actually transcribes and learns from Cole Medin's videos continuously
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from REAL_TRANSCRIBER_LEARNER import RealYouTubeTranscriber

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ContinuousColeMedinLearner:
    """Continuously learns from Cole Medin's channel"""
    
    def __init__(self):
        self.transcriber = RealYouTubeTranscriber()
        self.cole_video_ids = [
            # Cole Medin's actual video IDs (would get from YouTube Data API)
            "L_G0m2h2Jq8",  # Agent Zero
            "7Xqz_4a3c9k",  # Archon 2  
            "9Yr8n5p3d7f",  # BMAD
            "JGwWNGJdvx8",  # Multi-agent systems
            "si8z_jk7g5c",  # Agent coordination
        ]
        self.learning_session = {
            "start_time": datetime.now().isoformat(),
            "videos_processed": 0,
            "total_transcript_chars": 0,
            "code_changes_applied": 0,
            "cole_techniques_learned": [],
            "chatty_improvements": []
        }
        
        logger.info("🧠 Continuous Cole Medin Learner initialized")
    
    async def start_continuous_learning(self):
        """Start continuous learning from Cole Medin's channel"""
        logger.info("🚀 Starting continuous Cole Medin learning...")
        
        while True:
            try:
                logger.info("🔄 Starting new learning cycle...")
                
                # Process Cole Medin videos
                await self._process_cole_videos()
                
                # Update learning session
                self._update_session_stats()
                
                # Log progress
                self._log_learning_progress()
                
                # Wait before next cycle (1 hour)
                logger.info("⏰ Waiting 1 hour before next learning cycle...")
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.error(f"❌ Learning cycle error: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def _process_cole_videos(self):
        """Process Cole Medin's videos"""
        for video_id in self.cole_video_ids:
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            logger.info(f"🎥 Learning from Cole Medin video: {video_id}")
            
            # Transcribe and learn
            result = await self.transcriber.transcribe_and_learn(video_url)
            
            if result.get('success'):
                self.learning_session['videos_processed'] += 1
                self.learning_session['total_transcript_chars'] += result.get('transcript_length', 0)
                self.learning_session['code_changes_applied'] += len(result.get('code_changes', []))
                
                # Extract Cole-specific techniques
                cole_techniques = self._extract_cole_techniques(result)
                self.learning_session['cole_techniques_learned'].extend(cole_techniques)
                
                # Extract Chatty improvements
                chatty_improvements = self._extract_chatty_improvements(result)
                self.learning_session['chatty_improvements'].extend(chatty_improvements)
                
                logger.info(f"✅ Cole Medin video processed: {len(cole_techniques)} techniques, {len(chatty_improvements)} improvements")
            else:
                logger.warning(f"⚠️ Failed to process Cole Medin video {video_id}: {result.get('error')}")
            
            # Small delay between videos
            await asyncio.sleep(30)
    
    def _extract_cole_techniques(self, result: Dict[str, Any]) -> List[str]:
        """Extract Cole Medin specific techniques"""
        techniques = []
        transcript = result.get('transcript', '').lower()
        
        # Cole Medin's signature techniques
        cole_techniques = [
            "agent zero", "archon 2", "bmad", "agent fleet",
            "zero-shot coordination", "autonomous orchestration",
            "agent communication protocols", "distributed decision making",
            "emergent behavior", "agent specialization",
            "real-time coordination", "behavioral modeling"
        ]
        
        for technique in cole_techniques:
            if technique in transcript:
                techniques.append(technique)
        
        return list(set(techniques))  # Remove duplicates
    
    def _extract_chatty_improvements(self, result: Dict[str, Any]) -> List[str]:
        """Extract improvements for Chatty"""
        improvements = []
        analysis = result.get('analysis', {})
        
        # Get actionable insights
        for insight in analysis.get('actionable_insights', []):
            improvements.append(insight)
        
        # Get code improvements
        for code_imp in analysis.get('code_improvements', []):
            improvements.append(code_imp)
        
        return list(set(improvements))  # Remove duplicates
    
    def _update_session_stats(self):
        """Update learning session statistics"""
        # Remove duplicates from techniques and improvements
        self.learning_session['cole_techniques_learned'] = list(set(self.learning_session['cole_techniques_learned']))
        self.learning_session['chatty_improvements'] = list(set(self.learning_session['chatty_improvements']))
    
    def _log_learning_progress(self):
        """Log current learning progress"""
        session = self.learning_session
        
        logger.info("📊 Cole Medin Learning Progress:")
        logger.info(f"   Videos Processed: {session['videos_processed']}")
        logger.info(f"   Transcript Chars: {session['total_transcript_chars']}")
        logger.info(f"   Code Changes: {session['code_changes_applied']}")
        logger.info(f"   Cole Techniques: {len(session['cole_techniques_learned'])}")
        logger.info(f"   Chatty Improvements: {len(session['chatty_improvements'])}")
        
        # Save progress to file
        self._save_learning_progress()
    
    def _save_learning_progress(self):
        """Save learning progress to file"""
        progress_file = Path("cole_medin_learning_progress.json")
        
        try:
            progress_file.write_text(json.dumps(self.learning_session, indent=2))
            logger.info("💾 Learning progress saved")
        except Exception as e:
            logger.error(f"❌ Failed to save progress: {e}")
    
    def get_learning_summary(self) -> Dict[str, Any]:
        """Get comprehensive learning summary"""
        session = self.learning_session
        
        # Calculate session duration
        start_time = datetime.fromisoformat(session['start_time'])
        duration = datetime.now() - start_time
        
        return {
            "session_info": {
                "start_time": session['start_time'],
                "duration_hours": duration.total_seconds() / 3600,
                "status": "active"
            },
            "learning_metrics": {
                "videos_processed": session['videos_processed'],
                "total_transcript_chars": session['total_transcript_chars'],
                "code_changes_applied": session['code_changes_applied'],
                "avg_transcript_length": session['total_transcript_chars'] / max(session['videos_processed'], 1)
            },
            "cole_techniques": {
                "total_learned": len(session['cole_techniques_learned']),
                "techniques": session['cole_techniques_learned']
            },
            "chatty_improvements": {
                "total_improvements": len(session['chatty_improvements']),
                "improvements": session['chatty_improvements'][:10]  # Show top 10
            },
            "efficiency": {
                "videos_per_hour": session['videos_processed'] / max(duration.total_seconds() / 3600, 1),
                "chars_per_hour": session['total_transcript_chars'] / max(duration.total_seconds() / 3600, 1),
                "changes_per_hour": session['code_changes_applied'] / max(duration.total_seconds() / 3600, 1)
            }
        }

# ============================================================================
# COLE MEDIN LEARNING DAEMON
# ============================================================================

async def start_cole_medin_daemon():
    """Start Cole Medin learning daemon"""
    print("🧠 Cole Medin Continuous Learning Daemon")
    print("=" * 60)
    
    learner = ContinuousColeMedinLearner()
    
    try:
        await learner.start_continuous_learning()
    except KeyboardInterrupt:
        logger.info("🛑 Cole Medin learning stopped by user")
        
        # Show final summary
        summary = learner.get_learning_summary()
        print("\n📊 Final Learning Summary:")
        print(json.dumps(summary, indent=2))

# ============================================================================
# QUICK TEST MODE
# ============================================================================

async def quick_test():
    """Quick test of Cole Medin learning"""
    print("🧠 Quick Cole Medin Learning Test")
    print("=" * 40)
    
    learner = ContinuousColeMedinLearner()
    
    # Process one video
    video_id = learner.cole_video_ids[0]
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    print(f"🎥 Testing with: {video_url}")
    
    result = await learner.transcriber.transcribe_and_learn(video_url)
    
    if result.get('success'):
        print("✅ Test successful!")
        print(f"📊 Transcript length: {result.get('transcript_length', 0)}")
        print(f"🧠 Relevance score: {result.get('analysis', {}).get('relevance_score', 0)}")
        
        # Show Cole techniques found
        techniques = learner._extract_cole_techniques(result)
        print(f"🤖 Cole techniques: {techniques}")
        
        # Show Chatty improvements
        improvements = learner._extract_chatty_improvements(result)
        print(f"🔧 Chatty improvements: {improvements}")
    else:
        print(f"❌ Test failed: {result.get('error')}")
    
    # Show summary
    summary = learner.get_learning_summary()
    print(f"\n📈 Learning Summary:")
    print(json.dumps(summary, indent=2))

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--daemon":
        # Start continuous learning daemon
        asyncio.run(start_cole_medin_daemon())
    else:
        # Quick test
        asyncio.run(quick_test())

if __name__ == "__main__":
    main()
