#!/usr/bin/env python3
"""
ULTIMATE CHATTY INTEGRATION
Combines YouTube Learning, Cole Medin Techniques, and Claude Memory
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import all our systems
from CLAUDE_MEMORY_INTEGRATION import ChattyMemoryIntegration
from REAL_TRANSCRIBER_LEARNER import RealYouTubeTranscriber
from TRANSCRIPTAPI_INTEGRATION import TranscriptAPIIntegration

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UltimateChattyIntegration:
    """Ultimate integration of all Chatty learning and memory systems"""
    
    def __init__(self):
        # Initialize all systems
        self.memory_system = ChattyMemoryIntegration()
        self.youtube_transcriber = RealYouTubeTranscriber()
        self.transcript_api = TranscriptAPIIntegration()
        
        # Learning configuration
        self.learning_config = {
            "auto_learn": True,
            "memory_importance_threshold": 0.4,
            "cole_medin_focus": True,
            "continuous_learning": True
        }
        
        # Statistics
        self.integration_stats = {
            "total_learnings": 0,
            "memories_created": 0,
            "cole_techniques_learned": 0,
            "youtube_videos_processed": 0,
            "last_learning_session": None
        }
        
        logger.info("🚀 Ultimate Chatty Integration initialized")
        logger.info("🧠 Memory System: Ready")
        logger.info("🎥 YouTube Transcription: Ready")
        logger.info("🎯 TranscriptAPI: Ready")
    
    async def learn_from_youtube_video(self, video_url: str, context: str = "general_learning") -> Dict[str, Any]:
        """Learn from YouTube video with full integration"""
        try:
            logger.info(f"🚀 Ultimate learning from: {video_url}")
            
            learning_session = {
                "video_url": video_url,
                "context": context,
                "start_time": datetime.now(),
                "memories_created": [],
                "techniques_learned": [],
                "success": False
            }
            
            # Step 1: Transcribe video (try TranscriptAPI first, then fallback)
            transcript_result = await self._transcribe_video(video_url)
            
            if not transcript_result.get('success'):
                logger.warning(f"⚠️ Transcription failed: {transcript_result.get('error')}")
                return {"error": "Transcription failed", "success": False}
            
            # Step 2: Analyze content
            analysis = transcript_result.get('analysis', {})
            transcript = transcript_result.get('transcript', '')
            
            # Step 3: Create memories from key insights
            await self._create_memories_from_transcript(transcript, analysis, video_url, learning_session)
            
            # Step 4: Focus on Cole Medin techniques if enabled
            if self.learning_config["cole_medin_focus"]:
                cole_techniques = await self._extract_cole_techniques(transcript, analysis)
                learning_session["techniques_learned"] = cole_techniques
                
                # Create special memories for Cole techniques
                for technique in cole_techniques:
                    await self._create_cole_technique_memory(technique, video_url, learning_session)
            
            # Step 5: Update statistics
            self._update_integration_stats(learning_session)
            
            # Step 6: Save everything
            await self._save_learning_session(learning_session)
            
            learning_session["success"] = True
            learning_session["end_time"] = datetime.now()
            learning_session["duration"] = (learning_session["end_time"] - learning_session["start_time"]).total_seconds()
            
            logger.info(f"✅ Ultimate learning complete: {len(learning_session['memories_created'])} memories, {len(learning_session['techniques_learned'])} techniques")
            
            return {
                "success": True,
                "learning_session": learning_session,
                "transcript_result": transcript_result
            }
            
        except Exception as e:
            logger.error(f"❌ Ultimate learning failed: {e}")
            return {"error": str(e), "success": False}
    
    async def _transcribe_video(self, video_url: str) -> Dict[str, Any]:
        """Transcribe video using best available method"""
        # Try TranscriptAPI first (most reliable)
        if os.getenv('TRANSCRIPTAPI_KEY'):
            logger.info("🎯 Using TranscriptAPI for transcription")
            result = await self.transcript_api.transcribe_youtube_video(video_url)
            if result.get('success'):
                return result
        
        # Fallback to YouTube transcriber
        logger.info("🎥 Using YouTube transcriber as fallback")
        result = await self.youtube_transcriber.transcribe_and_learn(video_url)
        
        return result
    
    async def _create_memories_from_transcript(self, transcript: str, analysis: Dict[str, Any], 
                                              video_url: str, learning_session: Dict[str, Any]):
        """Create memories from transcript insights"""
        try:
            # Memory 1: Video summary
            summary_memory = f"YouTube Video Learning\nURL: {video_url}\nSummary: {transcript[:200]}...\n\nKey Topics: {', '.join(analysis.get('key_topics', []))}"
            
            summary_id = await self.memory_system.memory_system.add_memory(
                content=summary_memory,
                importance=0.7,
                tags={'youtube', 'learning', 'video'},
                context=f"youtube_learning_{video_url}",
                source="youtube_transcript"
            )
            
            if summary_id:
                learning_session["memories_created"].append(summary_id)
            
            # Memory 2: Actionable insights
            for insight in analysis.get('actionable_insights', []):
                insight_memory = f"Learning Insight from {video_url}\nInsight: {insight}\nContext: YouTube learning"
                
                insight_id = await self.memory_system.memory_system.add_memory(
                    content=insight_memory,
                    importance=0.6,
                    tags={'insight', 'learning', 'actionable'},
                    context="youtube_insights",
                    source="youtube_analysis"
                )
                
                if insight_id:
                    learning_session["memories_created"].append(insight_id)
            
            # Memory 3: Code improvements
            for improvement in analysis.get('code_improvements', []):
                code_memory = f"Code Improvement Opportunity\nSource: {video_url}\nImprovement: {improvement}\nPriority: High"
                
                code_id = await self.memory_system.memory_system.add_memory(
                    content=code_memory,
                    importance=0.8,
                    tags={'code', 'improvement', 'automation'},
                    context="code_improvements",
                    source="youtube_analysis"
                )
                
                if code_id:
                    learning_session["memories_created"].append(code_id)
            
            logger.info(f"🧠 Created {len(learning_session['memories_created'])} memories from transcript")
            
        except Exception as e:
            logger.error(f"❌ Failed to create memories from transcript: {e}")
    
    async def _extract_cole_techniques(self, transcript: str, analysis: Dict[str, Any]) -> List[str]:
        """Extract Cole Medin specific techniques"""
        techniques = []
        transcript_lower = transcript.lower()
        
        # Cole Medin's signature techniques
        cole_techniques = [
            "agent zero", "archon 2", "bmad", "agent fleet",
            "zero-shot coordination", "autonomous orchestration",
            "agent communication protocols", "distributed decision making",
            "emergent behavior", "agent specialization",
            "real-time coordination", "behavioral modeling"
        ]
        
        for technique in cole_techniques:
            if technique in transcript_lower:
                techniques.append(technique)
        
        # Also check analysis for Cole techniques
        cole_from_analysis = analysis.get('cole_medin_techniques', [])
        techniques.extend(cole_from_analysis)
        
        # Remove duplicates
        techniques = list(set(techniques))
        
        logger.info(f"🤖 Found {len(techniques)} Cole Medin techniques")
        return techniques
    
    async def _create_cole_technique_memory(self, technique: str, video_url: str, learning_session: Dict[str, Any]):
        """Create special memory for Cole Medin technique"""
        try:
            technique_memory = f"Cole Medin Technique: {technique}\nSource: {video_url}\nPriority: Implement in Chatty\n\nAction: Research and integrate {technique} into Chatty's multi-agent system"
            
            technique_id = await self.memory_system.memory_system.add_memory(
                content=technique_memory,
                importance=0.9,  # High importance for Cole techniques
                tags={'cole_medin', technique.replace(' ', '_'), 'agent', 'technique'},
                context="cole_medin_learning",
                source="cole_medin_analysis"
            )
            
            if technique_id:
                learning_session["memories_created"].append(technique_id)
                self.integration_stats["cole_techniques_learned"] += 1
            
        except Exception as e:
            logger.error(f"❌ Failed to create Cole technique memory: {e}")
    
    def _update_integration_stats(self, learning_session: Dict[str, Any]):
        """Update integration statistics"""
        self.integration_stats["total_learnings"] += 1
        self.integration_stats["memories_created"] += len(learning_session["memories_created"])
        self.integration_stats["youtube_videos_processed"] += 1
        self.integration_stats["last_learning_session"] = datetime.now().isoformat()
    
    async def _save_learning_session(self, learning_session: Dict[str, Any]):
        """Save learning session to file"""
        try:
            # Convert datetime objects to ISO strings
            session_copy = learning_session.copy()
            if 'start_time' in session_copy:
                session_copy['start_time'] = session_copy['start_time'].isoformat()
            if 'end_time' in session_copy:
                session_copy['end_time'] = session_copy['end_time'].isoformat()
            
            # Save to learning history
            learning_file = Path("chatty_learning_history.json")
            
            if learning_file.exists():
                with open(learning_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            else:
                history = {"learning_sessions": [], "stats": {}}
            
            history["learning_sessions"].append(session_copy)
            history["stats"] = self.integration_stats
            history["last_updated"] = datetime.now().isoformat()
            
            with open(learning_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
            
            logger.info("💾 Learning session saved")
            
        except Exception as e:
            logger.error(f"❌ Failed to save learning session: {e}")
    
    async def recall_relevant_knowledge(self, query: str, context: str = "") -> Dict[str, Any]:
        """Recall relevant knowledge from all systems"""
        try:
            # Search memories
            memories = await self.memory_system.recall_relevant_memories(query, context)
            
            # Organize by type
            youtube_memories = [m for m in memories if 'youtube' in m.get('tags', [])]
            cole_memories = [m for m in memories if 'cole_medin' in m.get('tags', [])]
            code_memories = [m for m in memories if 'code' in m.get('tags', [])]
            
            result = {
                "query": query,
                "context": context,
                "total_memories": len(memories),
                "youtube_memories": youtube_memories,
                "cole_memories": cole_memories,
                "code_memories": code_memories,
                "all_memories": memories
            }
            
            logger.info(f"🧠 Recalled {len(memories)} relevant memories for query: {query[:30]}...")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to recall knowledge: {e}")
            return {"error": str(e), "total_memories": 0}
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            # Memory stats
            memory_summary = await self.memory_system.get_memory_summary()
            
            # YouTube transcriber stats
            youtube_stats = self.youtube_transcriber.get_transcription_stats()
            
            # TranscriptAPI stats
            transcriptapi_stats = self.transcript_api.get_stats()
            
            # Integration stats
            status = {
                "timestamp": datetime.now().isoformat(),
                "system_status": "active",
                "integration_stats": self.integration_stats,
                "memory_system": memory_summary,
                "youtube_transcriber": youtube_stats,
                "transcriptapi": transcriptapi_stats,
                "learning_config": self.learning_config
            }
            
            return status
            
        except Exception as e:
            logger.error(f"❌ Failed to get system status: {e}")
            return {"error": str(e), "system_status": "error"}
    
    async def start_continuous_learning(self, video_urls: List[str], interval_minutes: int = 60):
        """Start continuous learning from video list"""
        logger.info(f"🚀 Starting continuous learning: {len(video_urls)} videos, {interval_minutes}min interval")
        
        while True:
            try:
                for video_url in video_urls:
                    logger.info(f"🎥 Continuous learning: {video_url}")
                    
                    result = await self.learn_from_youtube_video(video_url, "continuous_learning")
                    
                    if result.get('success'):
                        logger.info(f"✅ Continuous learning successful for {video_url}")
                    else:
                        logger.warning(f"⚠️ Continuous learning failed: {result.get('error')}")
                    
                    # Small delay between videos
                    await asyncio.sleep(30)
                
                # Wait for next cycle
                logger.info(f"⏰ Continuous learning cycle complete, waiting {interval_minutes} minutes...")
                await asyncio.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                logger.info("🛑 Continuous learning stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Continuous learning error: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

# ============================================================================
# DEMONSTRATION
# ============================================================================

async def demonstrate_ultimate_integration():
    """Demonstrate ultimate integration"""
    print("🚀 Ultimate Chatty Integration Demonstration")
    print("=" * 60)
    
    # Initialize ultimate system
    ultimate = UltimateChattyIntegration()
    
    # Test video
    test_video = "https://www.youtube.com/watch?v=JGwWNGJdvx8"
    
    print(f"🎥 Learning from: {test_video}")
    
    # Learn from video
    result = await ultimate.learn_from_youtube_video(test_video, "demo")
    
    if result.get('success'):
        learning_session = result['learning_session']
        
        print(f"✅ Learning successful!")
        print(f"🧠 Memories created: {len(learning_session['memories_created'])}")
        print(f"🤖 Cole techniques: {len(learning_session['techniques_learned'])}")
        print(f"⏱️ Duration: {learning_session.get('duration', 0):.1f} seconds")
        
        # Show techniques found
        if learning_session['techniques_learned']:
            print(f"\n🤖 Cole Medin Techniques Found:")
            for technique in learning_session['techniques_learned']:
                print(f"   - {technique}")
    else:
        print(f"❌ Learning failed: {result.get('error')}")
    
    # Test knowledge recall
    print(f"\n🔍 Testing knowledge recall...")
    recall_result = await ultimate.recall_relevant_knowledge("agent communication")
    
    print(f"📊 Recall results: {recall_result['total_memories']} memories")
    print(f"   YouTube memories: {len(recall_result['youtube_memories'])}")
    print(f"   Cole Medin memories: {len(recall_result['cole_memories'])}")
    print(f"   Code memories: {len(recall_result['code_memories'])}")
    
    # Show system status
    print(f"\n📈 System Status:")
    status = await ultimate.get_system_status()
    
    print(f"📊 Total learnings: {status['integration_stats']['total_learnings']}")
    print(f"🧠 Total memories: {status['memory_system']['stats']['total_memories']}")
    print(f"🎥 YouTube videos: {status['integration_stats']['youtube_videos_processed']}")
    print(f"🤖 Cole techniques: {status['integration_stats']['cole_techniques_learned']}")

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        # Continuous learning mode
        videos = [
            "https://www.youtube.com/watch?v=JGwWNGJdvx8",
            "https://www.youtube.com/watch?v=wH7vqrz8oOs",
            "https://www.youtube.com/watch?v=si8z_jk7g5c"
        ]
        
        ultimate = UltimateChattyIntegration()
        asyncio.run(ultimate.start_continuous_learning(videos, interval_minutes=30))
    else:
        # Demonstration mode
        asyncio.run(demonstrate_ultimate_integration())

if __name__ == "__main__":
    main()
