#!/usr/bin/env python3
"""
Fixed YouTube Learner with OpenRouter Integration
"""

import asyncio
import json
import logging
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# YouTube API
try:
    from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, VideoUnavailable
    from youtube_transcript_api.formatters import TextFormatter
    YOUTUBE_API_AVAILABLE = True
except ImportError:
    YOUTUBE_API_AVAILABLE = False

# AI analysis
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FixedYouTubeLearner:
    """Fixed YouTube learner with OpenRouter support"""

    def __init__(self, revenue_engine=None):
        self.learning_database = {}
        self.revenue_engine = revenue_engine
        self.openrouter_key = os.getenv('OPENROUTER_API_KEY')
        self.openai_key = os.getenv('OPENAI_API_KEY')
        self.learnings_path = Path("generated_content") / "youtube_learnings.json"
        self.learnings_path.parent.mkdir(parents=True, exist_ok=True)
        self.is_running = False

        logger.info("🎥 Fixed YouTube Learner initialized")
        logger.info(f"🔑 OpenRouter: {'Available' if self.openrouter_key else 'Not set'}")
        logger.info(f"🔑 OpenAI: {'Available' if self.openai_key else 'Not set'}")
    
    async def transcribe_and_learn(self, video_url: str) -> Dict[str, Any]:
        """Transcribe and learn from YouTube video"""
        try:
            logger.info(f"🎥 Processing: {video_url}")
            
            # Extract video ID
            video_id = self._extract_video_id(video_url)
            if not video_id:
                return {"error": "Invalid URL", "success": False}
            
            # Get transcript
            transcript = await self._get_transcript(video_id)
            if not transcript:
                return {"error": "No transcript", "success": False}
            
            # Get metadata
            metadata = {"video_id": video_id, "title": f"Video {video_id}"}
            
            # Analyze with AI
            analysis = await self._analyze_with_ai(transcript, metadata)
            
            # Extract insights
            insights = await self._extract_insights(analysis)
            
            result = {
                "success": True,
                "video_id": video_id,
                "url": video_url,
                "metadata": metadata,
                "transcript_length": len(transcript),
                "analysis": analysis,
                "insights": insights,
                "timestamp": datetime.now().isoformat()
            }

            self._save_learning(result)
            logger.info(f"✅ Learning complete: {len(insights)} insights")
            return result
            
        except Exception as e:
            logger.error(f"❌ Learning failed: {e}")
            return {"error": str(e), "success": False}
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID"""
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
    
    async def _get_transcript(self, video_id: str) -> Optional[str]:
        """Get YouTube transcript"""
        if not YOUTUBE_API_AVAILABLE:
            return None
        
        try:
            ytt_api = YouTubeTranscriptApi()
            transcript_list = ytt_api.list(video_id)
            
            # Try English first
            try:
                transcript = transcript_list.find_transcript(['en'])
                transcript_data = transcript.fetch()
            except NoTranscriptFound:
                transcript = list(transcript_list)[0]
                transcript_data = transcript.fetch()
            
            formatter = TextFormatter()
            formatted_transcript = formatter.format_transcript(transcript_data)
            
            logger.info(f"✅ Transcript: {len(formatted_transcript)} chars")
            return formatted_transcript
            
        except Exception as e:
            logger.error(f"❌ Transcript failed: {e}")
            return None
    
    async def _analyze_with_ai(self, transcript: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze transcript with AI — delegates to revenue engine when available"""
        if self.revenue_engine:
            return await self._analyze_with_revenue_engine(transcript, metadata)
        if self.openrouter_key:
            return await self._analyze_with_openrouter(transcript, metadata)
        elif self.openai_key:
            return await self._analyze_with_openai(transcript, metadata)
        else:
            return self._basic_analysis(transcript)

    async def _analyze_with_revenue_engine(self, transcript: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze using the shared revenue engine LLM rotation"""
        try:
            system_prompt = "You are an expert AI automation analyst. Return ONLY valid JSON."
            user_prompt = (
                f"Analyze this YouTube video transcript for automation insights.\n\n"
                f"Title: {metadata.get('title', '')}\n\n"
                f"Transcript (first 3000 chars):\n{transcript[:3000]}\n\n"
                "Return JSON with exactly these keys:\n"
                '{"relevance_score": <0-1>, "key_topics": [...], '
                '"automation_techniques": [...], "code_improvements": [...], '
                '"actionable_insights": [...]}'
            )
            raw = await self.revenue_engine.generate_ai_content(system_prompt, user_prompt, max_tokens=500)
            parsed = self._parse_json_response(raw)
            if parsed:
                return parsed
            return self._basic_analysis(transcript)
        except Exception as e:
            logger.error(f"Revenue engine analysis failed: {e}")
            return self._basic_analysis(transcript)
    
    async def _analyze_with_openrouter(self, transcript: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze with OpenRouter"""
        try:
            client = openai.OpenAI(
                api_key=self.openrouter_key,
                base_url='https://openrouter.ai/api/v1'
            )
            
            prompt = f"""
            Analyze this YouTube video transcript for automation insights:
            
            Title: {metadata.get('title', '')}
            
            Transcript: {transcript[:2000]}...
            
            Return JSON:
            {{
                "relevance_score": 0.8,
                "key_topics": ["automation", "ai"],
                "automation_techniques": ["workflow automation"],
                "code_improvements": ["implement message passing"],
                "actionable_insights": ["use event-driven architecture"]
            }}
            """
            
            response = client.chat.completions.create(
                model='anthropic/claude-3-haiku',
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.3
            )
            
            analysis_text = response.choices[0].message.content
            logger.info(f"🔍 OpenRouter raw response: {analysis_text[:200]}...")

            parsed = self._parse_json_response(analysis_text)
            if parsed:
                logger.info("✅ OpenRouter analysis completed")
                return parsed
            return self._basic_analysis(transcript)
                
        except Exception as e:
            logger.error(f"❌ OpenRouter analysis failed: {e}")
            return self._basic_analysis(transcript)
    
    async def _analyze_with_openai(self, transcript: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze with OpenAI"""
        try:
            client = openai.OpenAI(api_key=self.openai_key)
            
            prompt = f"""
            Analyze this YouTube video transcript for automation insights:
            
            Title: {metadata.get('title', '')}
            
            Transcript: {transcript[:2000]}...
            
            Return JSON:
            {{
                "relevance_score": 0.8,
                "key_topics": ["automation", "ai"],
                "automation_techniques": ["workflow automation"],
                "code_improvements": ["implement message passing"],
                "actionable_insights": ["use event-driven architecture"]
            }}
            """
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.3
            )
            
            analysis_text = response.choices[0].message.content

            parsed = self._parse_json_response(analysis_text)
            if parsed:
                logger.info("✅ OpenAI analysis completed")
                return parsed
            return self._basic_analysis(transcript)
                
        except Exception as e:
            logger.error(f"❌ OpenAI analysis failed: {e}")
            return self._basic_analysis(transcript)
    
    def _basic_analysis(self, transcript: str) -> Dict[str, Any]:
        """Basic keyword analysis"""
        text_lower = transcript.lower()
        
        keywords = {
            "automation": ["automation", "workflow", "automate", "script"],
            "ai": ["artificial intelligence", "machine learning", "neural", "model"],
            "multi-agent": ["agent", "multi-agent", "coordination", "orchestration"],
            "performance": ["optimize", "performance", "speed", "efficiency"],
            "code": ["code", "programming", "function", "class", "algorithm"]
        }
        
        found_topics = []
        techniques = []
        improvements = []
        
        for category, words in keywords.items():
            if any(word in text_lower for word in words):
                found_topics.append(category)
                
                if category == "automation":
                    techniques.extend(["workflow automation", "process optimization"])
                    improvements.extend(["automate repetitive tasks", "create workflow engine"])
                elif category == "multi-agent":
                    techniques.extend(["agent coordination", "multi-agent workflows"])
                    improvements.extend(["implement agent communication", "add fleet management"])
                elif category == "performance":
                    techniques.extend(["performance optimization", "resource management"])
                    improvements.extend(["optimize code execution", "improve memory usage"])
        
        return {
            "relevance_score": min(len(found_topics) * 0.2, 1.0),
            "key_topics": found_topics,
            "automation_techniques": techniques,
            "code_improvements": improvements,
            "actionable_insights": [f"Consider {topic} for Chatty" for topic in found_topics]
        }
    
    def _parse_json_response(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from an LLM response that may contain markdown fences."""
        if not text:
            return None
        # Strip markdown code fences
        cleaned = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`")
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
        # Fallback: find first { ... } block
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                pass
        logger.warning(f"Could not parse JSON from LLM response: {text[:120]}...")
        return None

    def _save_learning(self, result: Dict[str, Any]):
        """Persist a learning result to generated_content/youtube_learnings.json"""
        try:
            existing: List[Dict[str, Any]] = []
            if self.learnings_path.exists():
                try:
                    existing = json.loads(self.learnings_path.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, ValueError):
                    existing = []
            # Avoid duplicates by video_id
            video_id = result.get("video_id")
            existing = [e for e in existing if e.get("video_id") != video_id]
            existing.append(result)
            self.learnings_path.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to save learning: {e}")

    async def start_continuous_learning(self, video_urls: Optional[List[str]] = None, interval_minutes: int = 60):
        """Process a list of video URLs on a repeating schedule."""
        self.is_running = True
        urls = video_urls or []
        if not urls:
            logger.warning("No video URLs provided for continuous learning")
            return
        logger.info(f"🎥 Starting continuous learning: {len(urls)} videos, interval {interval_minutes}m")
        while self.is_running:
            for url in urls:
                if not self.is_running:
                    break
                await self.transcribe_and_learn(url)
                await asyncio.sleep(5)
            if self.is_running:
                await asyncio.sleep(interval_minutes * 60)

    async def stop(self):
        self.is_running = False

    async def _extract_insights(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract actionable insights"""
        insights = []
        
        # Add AI insights
        for insight in analysis.get('actionable_insights', []):
            insights.append({
                "type": "insight",
                "content": insight,
                "source": "ai_analysis",
                "priority": "medium",
                "timestamp": datetime.now().isoformat()
            })
        
        # Add code improvements
        for improvement in analysis.get('code_improvements', []):
            insights.append({
                "type": "code_improvement",
                "content": improvement,
                "source": "ai_analysis",
                "priority": "high",
                "timestamp": datetime.now().isoformat()
            })
        
        return insights

# ============================================================================
# TEST THE FIXED SYSTEM
# ============================================================================

async def test_fixed_learner():
    """Test the fixed YouTube learner"""
    print("🎥 Testing Fixed YouTube Learner")
    print("=" * 40)
    
    learner = FixedYouTubeLearner()
    
    # Test video
    test_video = "https://www.youtube.com/watch?v=JGwWNGJdvx8"
    
    print(f"🎥 Processing: {test_video}")
    
    result = await learner.transcribe_and_learn(test_video)
    
    if result.get('success'):
        print("✅ Learning successful!")
        print(f"📊 Transcript length: {result['transcript_length']}")
        print(f"🧠 Relevance score: {result['analysis'].get('relevance_score', 0)}")
        print(f"🔑 Key topics: {result['analysis'].get('key_topics', [])}")
        print(f"🤖 Techniques: {result['analysis'].get('automation_techniques', [])}")
        print(f"💡 Insights: {len(result['insights'])}")
        
        # Show insights
        for insight in result['insights']:
            print(f"   - {insight['content']}")
    else:
        print(f"❌ Learning failed: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(test_fixed_learner())
