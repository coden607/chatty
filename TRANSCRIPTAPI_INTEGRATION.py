#!/usr/bin/env python3
"""
TranscriptAPI Integration - Best YouTube Transcription Service
Reliable API that actually works for YouTube transcription
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# HTTP requests
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

# AI for analysis
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TranscriptAPIIntegration:
    """Integration with TranscriptAPI.com - the best YouTube transcription service"""
    
    def __init__(self):
        self.api_key = os.getenv('TRANSCRIPTAPI_KEY')
        self.base_url = "https://api.transcriptapi.com"
        self.openai_key = os.getenv('OPENAI_API_KEY')
        
        # Statistics
        self.transcription_stats = {
            "videos_processed": 0,
            "total_chars": 0,
            "success_rate": 0.0,
            "last_transcription": None
        }
        
        logger.info("🎯 TranscriptAPI Integration initialized")
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check required dependencies"""
        available = []
        missing = []
        
        if AIOHTTP_AVAILABLE:
            available.append("aiohttp")
        else:
            missing.append("aiohttp")
        
        if OPENAI_AVAILABLE:
            available.append("openai")
        else:
            missing.append("openai")
        
        logger.info(f"✅ Available: {available}")
        if missing:
            logger.warning(f"⚠️ Missing: {missing}")
            logger.info("Install: pip install " + " ".join(missing))
    
    async def transcribe_youtube_video(self, video_url: str) -> Dict[str, Any]:
        """Transcribe YouTube video using TranscriptAPI"""
        try:
            logger.info(f"🎯 Transcribing with TranscriptAPI: {video_url}")
            
            # Extract video ID
            video_id = self._extract_video_id(video_url)
            if not video_id:
                return {"error": "Invalid YouTube URL", "success": False}
            
            # Get transcript via TranscriptAPI
            transcript_data = await self._get_transcript_from_api(video_id)
            
            if not transcript_data:
                return {"error": "Failed to get transcript", "success": False}
            
            # Get video metadata
            metadata = await self._get_video_metadata(video_id)
            
            # Analyze with AI
            analysis = await self._analyze_transcript(transcript_data, metadata)
            
            # Update stats
            self._update_stats(len(transcript_data), True)
            
            result = {
                "success": True,
                "video_id": video_id,
                "url": video_url,
                "metadata": metadata,
                "transcript": transcript_data,
                "transcript_length": len(transcript_data),
                "analysis": analysis,
                "timestamp": datetime.now().isoformat(),
                "service": "transcriptapi.com"
            }
            
            logger.info(f"✅ TranscriptAPI success: {len(transcript_data)} chars")
            return result
            
        except Exception as e:
            logger.error(f"❌ TranscriptAPI failed: {e}")
            self._update_stats(0, False)
            return {"error": str(e), "success": False}
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID"""
        import re
        
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/)([^&\n?#]+)',
            r'youtube\.com/embed/([^?&\n]+)',
            r'youtube\.com/v/([^?&\n]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                video_id = match.group(1)
                if len(video_id) == 11:
                    return video_id
        return None
    
    async def _get_transcript_from_api(self, video_id: str) -> Optional[str]:
        """Get transcript from TranscriptAPI"""
        if not self.api_key:
            logger.warning("⚠️ TRANSCRIPTAPI_KEY not set")
            return None
        
        if not AIOHTTP_AVAILABLE:
            logger.error("❌ aiohttp not available")
            return None
        
        try:
            # TranscriptAPI endpoint
            url = f"{self.base_url}/transcript"
            
            headers = {
                'x-api-key': self.api_key,
                'Content-Type': 'application/json'
            }
            
            data = {
                'video_id': video_id,
                'lang': 'en'  # Default to English
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        if result.get('success'):
                            transcript = result.get('data', {}).get('transcript', '')
                            logger.info(f"✅ TranscriptAPI transcript received: {len(transcript)} chars")
                            return transcript
                        else:
                            error_msg = result.get('error', 'Unknown error')
                            logger.error(f"❌ TranscriptAPI error: {error_msg}")
                            return None
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ TranscriptAPI HTTP error: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"❌ TranscriptAPI request failed: {e}")
            return None
    
    async def _get_video_metadata(self, video_id: str) -> Dict[str, Any]:
        """Get video metadata"""
        # For now, return basic metadata
        # In production, could use YouTube Data API or TranscriptAPI metadata endpoint
        
        return {
            "video_id": video_id,
            "title": f"Video {video_id}",
            "channel": "Unknown",
            "description": "YouTube video",
            "duration": 0,
            "upload_date": datetime.now().isoformat()
        }
    
    async def _analyze_transcript(self, transcript: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze transcript with AI"""
        if not OPENAI_AVAILABLE or not self.openai_key:
            return self._basic_analysis(transcript)
        
        try:
            client = openai.OpenAI(api_key=self.openai_key)
            
            prompt = f"""
            Analyze this YouTube video transcript for automation and AI insights:
            
            Title: {metadata.get('title', '')}
            
            Transcript: {transcript[:2000]}...
            
            Focus on:
            1. Multi-agent systems and coordination
            2. Automation techniques and workflows
            3. AI agent architectures
            4. Performance optimizations
            5. Code improvements and best practices
            
            Return JSON:
            {{
                "relevance_score": 0.0-1.0,
                "key_topics": ["topic1", "topic2"],
                "automation_techniques": ["technique1", "technique2"],
                "code_improvements": ["improvement1", "improvement2"],
                "actionable_insights": ["insight1", "insight2"],
                "cole_medin_techniques": ["technique1", "technique2"]
            }}
            """
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.3
            )
            
            analysis_text = response.choices[0].message.content
            return json.loads(analysis_text)
            
        except Exception as e:
            logger.error(f"❌ AI analysis failed: {e}")
            return self._basic_analysis(transcript)
    
    def _basic_analysis(self, transcript: str) -> Dict[str, Any]:
        """Basic keyword analysis"""
        text_lower = transcript.lower()
        
        # Keywords for different categories
        keywords = {
            "multi-agent": ["agent", "multi-agent", "coordination", "orchestration"],
            "automation": ["automation", "workflow", "automate", "script"],
            "ai": ["artificial intelligence", "machine learning", "neural", "model"],
            "performance": ["optimize", "performance", "speed", "efficiency"],
            "cole_medin": ["agent zero", "archon 2", "bmad", "fleet"]
        }
        
        found_topics = []
        techniques = []
        improvements = []
        cole_techniques = []
        
        for category, words in keywords.items():
            if any(word in text_lower for word in words):
                found_topics.append(category)
                
                if category == "multi-agent":
                    techniques.extend(["agent coordination", "multi-agent workflows"])
                    improvements.extend(["implement agent communication", "add fleet management"])
                elif category == "automation":
                    techniques.extend(["workflow automation", "process optimization"])
                    improvements.extend(["automate repetitive tasks", "create workflow engine"])
                elif category == "cole_medin":
                    cole_techniques.extend(["agent zero", "archon 2", "bmad"])
                    improvements.extend(["integrate cole medin techniques", "implement agent frameworks"])
        
        return {
            "relevance_score": min(len(found_topics) * 0.2, 1.0),
            "key_topics": found_topics,
            "automation_techniques": techniques,
            "code_improvements": improvements,
            "actionable_insights": [f"Consider {topic} for Chatty" for topic in found_topics],
            "cole_medin_techniques": cole_techniques
        }
    
    def _update_stats(self, char_count: int, success: bool):
        """Update transcription statistics"""
        self.transcription_stats["videos_processed"] += 1
        self.transcription_stats["total_chars"] += char_count
        self.transcription_stats["last_transcription"] = datetime.now().isoformat()
        
        # Calculate success rate
        if success:
            successful = self.transcription_stats.get("successful_transcriptions", 0) + 1
        else:
            successful = self.transcription_stats.get("successful_transcriptions", 0)
        
        self.transcription_stats["successful_transcriptions"] = successful
        self.transcription_stats["success_rate"] = successful / self.transcription_stats["videos_processed"]
    
    async def batch_transcribe(self, video_urls: List[str]) -> List[Dict[str, Any]]:
        """Transcribe multiple videos"""
        logger.info(f"🎯 Batch transcribing {len(video_urls)} videos")
        
        results = []
        for i, url in enumerate(video_urls):
            logger.info(f"🎥 Processing video {i+1}/{len(video_urls)}")
            
            result = await self.transcribe_youtube_video(url)
            results.append(result)
            
            # Small delay between requests
            await asyncio.sleep(1)
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get transcription statistics"""
        return self.transcription_stats.copy()

# ============================================================================
# TRANSCRIPTAPI DEMONSTRATION
# ============================================================================

async def demonstrate_transcriptapi():
    """Demonstrate TranscriptAPI integration"""
    print("🎯 TranscriptAPI.com Integration - Best YouTube Transcription")
    print("=" * 70)
    
    # Check for API key
    api_key = os.getenv('TRANSCRIPTAPI_KEY')
    if not api_key:
        print("❌ TRANSCRIPTAPI_KEY not set!")
        print("📝 Get your free API key at: https://transcriptapi.com/signup")
        print("🔧 Set it with: export TRANSCRIPTAPI_KEY=your_key_here")
        return
    
    transcriber = TranscriptAPIIntegration()
    
    # Test videos
    test_videos = [
        "https://www.youtube.com/watch?v=JGwWNGJdvx8",  # Tech video
        "https://www.youtube.com/watch?v=wH7vqrz8oOs",  # Another video
        "https://www.youtube.com/watch?v=si8z_jk7g5c"   # Third video
    ]
    
    print(f"🎥 Testing with {len(test_videos)} videos...")
    
    # Process videos
    results = await transcriber.batch_transcribe(test_videos)
    
    # Display results
    successful = [r for r in results if r.get('success')]
    failed = [r for r in results if not r.get('success')]
    
    print(f"\n📊 Results:")
    print(f"✅ Successful: {len(successful)}")
    print(f"❌ Failed: {len(failed)}")
    print(f"📈 Success Rate: {len(successful)/len(results)*100:.1f}%")
    
    if successful:
        total_chars = sum(r.get('transcript_length', 0) for r in successful)
        print(f"📝 Total Chars: {total_chars}")
        print(f"📊 Avg Chars: {total_chars/len(successful):.0f}")
        
        # Show analysis from first successful result
        first_result = successful[0]
        analysis = first_result.get('analysis', {})
        
        print(f"\n🧠 Analysis from first successful video:")
        print(f"Relevance Score: {analysis.get('relevance_score', 0)}")
        print(f"Key Topics: {analysis.get('key_topics', [])}")
        print(f"Cole Medin Techniques: {analysis.get('cole_medin_techniques', [])}")
        print(f"Code Improvements: {analysis.get('code_improvements', [])}")
    
    # Show stats
    stats = transcriber.get_stats()
    print(f"\n📈 Transcription Stats:")
    print(json.dumps(stats, indent=2))

# ============================================================================
# SETUP INSTRUCTIONS
# ============================================================================

def setup_instructions():
    """Show setup instructions"""
    print("🎯 TranscriptAPI.com Setup Instructions")
    print("=" * 50)
    print()
    print("1. 📝 Get FREE API Key:")
    print("   Go to: https://transcriptapi.com/signup")
    print("   Get 100 free credits to start")
    print()
    print("2. 🔧 Set Environment Variable:")
    print("   export TRANSCRIPTAPI_KEY=your_key_here")
    print("   Or add to .env file")
    print()
    print("3. 🤖 Optional: Set OpenAI Key:")
    print("   export OPENAI_API_KEY=your_openai_key")
    print("   For better transcript analysis")
    print()
    print("4. 🚀 Run the System:")
    print("   python3 TRANSCRIPTAPI_INTEGRATION.py")
    print()
    print("🎯 Benefits of TranscriptAPI.com:")
    print("   ✅ Reliable transcription (500K+ transcripts daily)")
    print("   ✅ No YouTube blocks or rate limits")
    print("   ✅ REST API + MCP for ChatGPT/Claude")
    print("   ✅ Channel browsing and playlist support")
    print("   ✅ 100 free credits to start")
    print("   ✅ Professional API with documentation")

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--setup":
        setup_instructions()
    else:
        asyncio.run(demonstrate_transcriptapi())

if __name__ == "__main__":
    main()
