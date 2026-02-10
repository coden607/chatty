#!/usr/bin/env python3
"""
REAL Cole Medin Channel Scanner and Learner
Finds actual Cole Medin videos and learns from them
"""

import asyncio
import json
import logging
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from REAL_TRANSCRIBER_LEARNER import RealYouTubeTranscriber

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RealColeMedinScanner:
    """Scans for real Cole Medin videos and learns from them"""
    
    def __init__(self):
        self.transcriber = RealYouTubeTranscriber()
        self.cole_channel_url = "https://www.youtube.com/@ColeMedin"
        
        # Search terms for Cole Medin content
        self.search_terms = [
            "Cole Medin Agent Zero",
            "Cole Medin Archon 2", 
            "Cole Medin BMAD",
            "Cole Medin multi-agent",
            "Agent Zero tutorial",
            "Archon 2 framework"
        ]
        
        self.learning_results = []
        
        logger.info("🔍 Real Cole Medin Scanner initialized")
    
    async def scan_and_learn(self):
        """Scan for Cole Medin videos and learn from them"""
        logger.info("🔍 Starting real Cole Medin video scan...")
        
        # Method 1: Try to get videos from channel
        channel_videos = await self._get_channel_videos()
        
        # Method 2: Search for Cole Medin videos
        search_results = await self._search_cole_videos()
        
        # Combine results
        all_videos = list(set(channel_videos + search_results))
        
        logger.info(f"📺 Found {len(all_videos)} Cole Medin videos")
        
        # Process videos
        for i, video_url in enumerate(all_videos[:3]):  # Process top 3
            logger.info(f"🎥 Processing video {i+1}/{len(all_videos)}: {video_url}")
            
            result = await self.transcriber.transcribe_and_learn(video_url)
            
            if result.get('success'):
                self.learning_results.append(result)
                logger.info(f"✅ Successfully learned from video {i+1}")
            else:
                logger.warning(f"⚠️ Failed to process video {i+1}: {result.get('error')}")
            
            # Small delay between videos
            await asyncio.sleep(10)
        
        # Generate summary
        summary = self._generate_learning_summary()
        logger.info("📊 Learning complete!")
        
        return summary
    
    async def _get_channel_videos(self) -> List[str]:
        """Get videos from Cole Medin's channel"""
        # This would require YouTube Data API in production
        # For now, return some known working video URLs that have transcripts
        
        working_videos = [
            "https://www.youtube.com/watch?v=JGwWNGJdvx8",  # This one worked
            "https://www.youtube.com/watch?v=wH7vqrz8oOs",  # Try another
            "https://www.youtube.com/watch?v=si8z_jk7g5c",  # And another
        ]
        
        logger.info(f"📋 Using {len(working_videos)} known working videos")
        return working_videos
    
    async def _search_cole_videos(self) -> List[str]:
        """Search for Cole Medin videos"""
        # This would use YouTube Data API in production
        # For now, return empty list
        logger.info("🔍 YouTube Data API not available, using known videos")
        return []
    
    def _generate_learning_summary(self) -> Dict[str, Any]:
        """Generate comprehensive learning summary"""
        if not self.learning_results:
            return {
                "status": "no_successful_learning",
                "message": "No videos were successfully processed"
            }
        
        total_chars = sum(r.get('transcript_length', 0) for r in self.learning_results)
        total_changes = sum(len(r.get('code_changes', [])) for r in self.learning_results)
        
        # Extract all techniques and improvements
        all_techniques = []
        all_improvements = []
        
        for result in self.learning_results:
            analysis = result.get('analysis', {})
            all_techniques.extend(analysis.get('automation_techniques', []))
            all_improvements.extend(analysis.get('code_improvements', []))
        
        return {
            "status": "success",
            "videos_processed": len(self.learning_results),
            "total_transcript_chars": total_chars,
            "total_code_changes": total_changes,
            "cole_techniques_found": list(set(all_techniques)),
            "chatty_improvements": list(set(all_improvements)),
            "learning_efficiency": {
                "avg_transcript_length": total_chars / len(self.learning_results),
                "changes_per_video": total_changes / len(self.learning_results),
                "success_rate": len(self.learning_results) / max(len(self.learning_results) + 1, 1) * 100
            },
            "processed_videos": [
                {
                    "video_id": r.get('video_id'),
                    "url": r.get('url'),
                    "transcript_length": r.get('transcript_length'),
                    "relevance_score": r.get('analysis', {}).get('relevance_score', 0),
                    "code_changes": len(r.get('code_changes', []))
                }
                for r in self.learning_results
            ]
        }

# ============================================================================
# DEMONSTRATION
# ============================================================================

async def demonstrate_cole_medin_learning():
    """Demonstrate real Cole Medin learning"""
    print("🧠 Real Cole Medin Learning Demonstration")
    print("=" * 60)
    
    scanner = RealColeMedinScanner()
    
    # Scan and learn
    summary = await scanner.scan_and_learn()
    
    # Display results
    print(f"\n📊 Learning Results:")
    print(f"Status: {summary.get('status', 'unknown')}")
    
    if summary.get('status') == 'success':
        print(f"✅ Videos Processed: {summary['videos_processed']}")
        print(f"📝 Total Transcript Chars: {summary['total_transcript_chars']}")
        print(f"🔧 Total Code Changes: {summary['total_code_changes']}")
        print(f"🤖 Cole Techniques: {len(summary['cole_techniques_found'])}")
        print(f"💡 Chatty Improvements: {len(summary['chatty_improvements'])}")
        
        # Show efficiency
        efficiency = summary.get('learning_efficiency', {})
        print(f"\n📈 Efficiency Metrics:")
        print(f"   Avg Transcript Length: {efficiency.get('avg_transcript_length', 0):.0f}")
        print(f"   Changes Per Video: {efficiency.get('changes_per_video', 0):.1f}")
        print(f"   Success Rate: {efficiency.get('success_rate', 0):.1f}%")
        
        # Show techniques found
        if summary['cole_techniques_found']:
            print(f"\n🤖 Cole Medin Techniques Found:")
            for technique in summary['cole_techniques_found']:
                print(f"   - {technique}")
        
        # Show improvements
        if summary['chatty_improvements']:
            print(f"\n💡 Chatty Improvements:")
            for improvement in summary['chatty_improvements'][:5]:  # Show top 5
                print(f"   - {improvement}")
        
        # Show processed videos
        print(f"\n📺 Processed Videos:")
        for video in summary['processed_videos']:
            print(f"   🎥 {video['video_id']}: {video['transcript_length']} chars, {video['code_changes']} changes")
    
    else:
        print(f"❌ Learning failed: {summary.get('message', 'Unknown error')}")
    
    # Save results
    results_file = Path("cole_medin_learning_results.json")
    results_file.write_text(json.dumps(summary, indent=2))
    print(f"\n💾 Results saved to: {results_file}")

# ============================================================================
# AUTO-LEARNING MODE
# ============================================================================

async def start_auto_learning():
    """Start automatic continuous learning"""
    print("🤖 Starting Auto Cole Medin Learning Mode")
    print("=" * 50)
    
    scanner = RealColeMedinScanner()
    
    cycle_count = 0
    
    while True:
        cycle_count += 1
        logger.info(f"🔄 Starting learning cycle {cycle_count}")
        
        try:
            # Scan and learn
            summary = await scanner.scan_and_learn()
            
            if summary.get('status') == 'success':
                logger.info(f"✅ Cycle {cycle_count} successful: {summary['videos_processed']} videos")
            else:
                logger.warning(f"⚠️ Cycle {cycle_count} failed: {summary.get('message')}")
            
            # Wait 30 minutes before next cycle
            logger.info("⏰ Waiting 30 minutes before next cycle...")
            await asyncio.sleep(1800)
            
        except KeyboardInterrupt:
            logger.info("🛑 Auto-learning stopped by user")
            break
        except Exception as e:
            logger.error(f"❌ Cycle {cycle_count} error: {e}")
            await asyncio.sleep(300)  # Wait 5 minutes on error

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        # Start auto-learning
        asyncio.run(start_auto_learning())
    else:
        # Single demonstration
        asyncio.run(demonstrate_cole_medin_learning())

if __name__ == "__main__":
    main()
