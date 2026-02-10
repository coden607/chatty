#!/usr/bin/env python3
"""
DEPRECATED — use FIXED_YOUTUBE_LEARNER.py and COLE_MEDIN_CHANNEL_LEARNER.py instead.

FULLY FUNCTIONAL YouTube Learning System
Real transcription, real AI analysis, real code modification
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

# Real YouTube libraries
try:
    from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, VideoUnavailable
    from youtube_transcript_api.formatters import TextFormatter
    YOUTUBE_API_AVAILABLE = True
except ImportError:
    YOUTUBE_API_AVAILABLE = False
    print("❌ Install youtube-transcript-api: pip install youtube-transcript-api")

# Real AI
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("❌ Install openai: pip install openai")

# Web scraping for metadata
try:
    import requests
    from bs4 import BeautifulSoup
    WEB_SCRAPING_AVAILABLE = True
except ImportError:
    WEB_SCRAPING_AVAILABLE = False
    print("❌ Install requests and beautifulsoup4: pip install requests beautifulsoup4")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FunctionalYouTubeLearner:
    """Actually functional YouTube learning system"""
    
    def __init__(self):
        self.learning_database = {}
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.codebase_path = Path('.')
        
        # Topics that matter for Chatty
        self.relevant_keywords = [
            'multi-agent', 'automation', 'ai agent', 'llm', 'token optimization',
            'self-healing', 'autonomous', 'crew ai', 'langchain', 'n8n',
            'workflow', 'api integration', 'system architecture', 'microservices'
        ]
        
        logger.info("🚀 Functional YouTube Learner initialized")
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check if all dependencies are available"""
        missing = []
        if not YOUTUBE_API_AVAILABLE:
            missing.append("youtube-transcript-api")
        if not OPENAI_AVAILABLE:
            missing.append("openai")
        if not WEB_SCRAPING_AVAILABLE:
            missing.append("requests/beautifulsoup4")
        
        if missing:
            logger.warning(f"⚠️ Missing dependencies: {missing}")
            logger.info("Install with: pip install " + " ".join(missing))
        else:
            logger.info("✅ All dependencies available")
    
    async def learn_from_video(self, video_url: str) -> Dict[str, Any]:
        """Learn from YouTube video - ACTUALLY WORKS"""
        try:
            logger.info(f"🎥 Processing video: {video_url}")
            
            # Step 1: Extract video ID
            video_id = self._extract_video_id(video_url)
            if not video_id:
                return {"error": "Invalid YouTube URL", "success": False}
            
            # Step 2: Get REAL transcript
            transcript = await self._get_transcript(video_id)
            if not transcript:
                return {"error": "No transcript available", "success": False}
            
            # Step 3: Get video metadata
            metadata = await self._get_metadata(video_id)
            
            # Step 4: Analyze with REAL AI
            analysis = await self._analyze_with_ai(transcript, metadata)
            
            # Step 5: Extract actionable insights
            insights = await self._extract_insights(transcript, analysis)
            
            # Step 6: Apply code improvements
            code_changes = await self._apply_code_improvements(insights)
            
            # Store results
            learning_result = {
                "success": True,
                "video_id": video_id,
                "url": video_url,
                "metadata": metadata,
                "transcript_length": len(transcript),
                "analysis": analysis,
                "insights": insights,
                "code_changes_applied": code_changes,
                "timestamp": datetime.now().isoformat()
            }
            
            self.learning_database[video_id] = learning_result
            
            logger.info(f"✅ Learning complete: {len(code_changes)} code changes applied")
            return learning_result
            
        except Exception as e:
            logger.error(f"❌ Learning failed: {e}")
            return {"error": str(e), "success": False}
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL"""
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
        """Get REAL YouTube transcript"""
        if not YOUTUBE_API_AVAILABLE:
            logger.error("❌ YouTube transcript API not available")
            return None
        
        try:
            # Create API instance
            ytt_api = YouTubeTranscriptApi()
            
            # Get available transcripts
            transcript_list = ytt_api.list(video_id)
            
            # Try English first
            try:
                transcript = transcript_list.find_transcript(['en'])
                transcript_data = transcript.fetch()
            except NoTranscriptFound:
                # Get any available transcript
                transcript = list(transcript_list)[0]
                transcript_data = transcript.fetch()
            
            # Format to plain text
            formatter = TextFormatter()
            formatted_transcript = formatter.format_transcript(transcript_data)
            
            logger.info(f"✅ Transcript extracted: {len(formatted_transcript)} chars")
            return formatted_transcript
            
        except VideoUnavailable:
            logger.error("❌ Video not available")
            return None
        except Exception as e:
            logger.error(f"❌ Transcript extraction failed: {e}")
            return None
    
    async def _get_metadata(self, video_id: str) -> Dict[str, Any]:
        """Get video metadata using web scraping"""
        metadata = {
            "video_id": video_id,
            "title": "",
            "channel": "",
            "description": "",
            "view_count": 0,
            "length": 0
        }
        
        if not WEB_SCRAPING_AVAILABLE:
            logger.warning("⚠️ Web scraping not available, using basic metadata")
            return metadata
        
        try:
            # Fetch video page
            url = f"https://www.youtube.com/watch?v={video_id}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract title
                title_tag = soup.find('title')
                if title_tag:
                    metadata['title'] = title_tag.text.replace(' - YouTube', '')
                
                # Extract channel name
                channel_tag = soup.find('link', {'itemprop': 'name'})
                if channel_tag:
                    metadata['channel'] = channel_tag.get('content', '')
                
                # Extract description
                desc_tag = soup.find('meta', {'property': 'og:description'})
                if desc_tag:
                    metadata['description'] = desc_tag.get('content', '')[:500]
                
                logger.info(f"✅ Metadata extracted: {metadata['title']}")
            
        except Exception as e:
            logger.warning(f"⚠️ Metadata extraction failed: {e}")
        
        return metadata
    
    async def _analyze_with_ai(self, transcript: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze transcript with REAL AI"""
        if not OPENAI_AVAILABLE or not self.api_key:
            logger.warning("⚠️ OpenAI not available, using keyword analysis")
            return self._keyword_analysis(transcript)
        
        try:
            client = openai.OpenAI(api_key=self.api_key)
            
            # Create focused prompt
            prompt = f"""
            Analyze this YouTube video content for improving the Chatty automation system:
            
            Title: {metadata.get('title', '')}
            Channel: {metadata.get('channel', '')}
            
            Transcript: {transcript[:2000]}...
            
            Focus on:
            1. Code improvements for multi-agent systems
            2. New automation techniques
            3. Performance optimizations
            4. Integration patterns
            5. System architecture improvements
            
            Return JSON format:
            {{
                "relevance_score": 0.0-1.0,
                "key_topics": ["topic1", "topic2"],
                "code_improvements": ["improvement1", "improvement2"],
                "new_techniques": ["technique1", "technique2"],
                "actionable_insights": ["insight1", "insight2"]
            }}
            """
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.3
            )
            
            analysis_text = response.choices[0].message.content
            
            # Parse JSON response
            try:
                analysis = json.loads(analysis_text)
                logger.info(f"✅ AI analysis completed")
                return analysis
            except json.JSONDecodeError:
                logger.warning("⚠️ Failed to parse AI response")
                return self._keyword_analysis(transcript)
                
        except Exception as e:
            logger.error(f"❌ AI analysis failed: {e}")
            return self._keyword_analysis(transcript)
    
    def _keyword_analysis(self, transcript: str) -> Dict[str, Any]:
        """Fallback keyword-based analysis"""
        text_lower = transcript.lower()
        
        found_topics = []
        improvements = []
        techniques = []
        insights = []
        
        for keyword in self.relevant_keywords:
            if keyword in text_lower:
                found_topics.append(keyword)
                
                if 'agent' in keyword:
                    improvements.append(f"Implement {keyword} architecture")
                elif 'optimization' in keyword:
                    improvements.append(f"Apply {keyword} techniques")
                elif 'workflow' in keyword:
                    improvements.append(f"Integrate {keyword} automation")
                elif 'integration' in keyword:
                    techniques.append(f"Use {keyword} patterns")
                else:
                    insights.append(f"Consider {keyword} for system improvement")
        
        return {
            "relevance_score": min(len(found_topics) * 0.15, 1.0),
            "key_topics": found_topics,
            "code_improvements": improvements,
            "new_techniques": techniques,
            "actionable_insights": insights
        }
    
    async def _extract_insights(self, transcript: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract actionable insights from analysis"""
        insights = []
        
        # Process AI insights
        for insight in analysis.get('actionable_insights', []):
            insights.append({
                "type": "insight",
                "content": insight,
                "source": "ai_analysis",
                "priority": "medium",
                "timestamp": datetime.now().isoformat()
            })
        
        # Process code improvements
        for improvement in analysis.get('code_improvements', []):
            insights.append({
                "type": "code_improvement",
                "content": improvement,
                "source": "ai_analysis",
                "priority": "high",
                "timestamp": datetime.now().isoformat()
            })
        
        return insights
    
    async def _apply_code_improvements(self, insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Actually apply code improvements to files"""
        applied_changes = []
        
        for insight in insights:
            if insight['type'] == 'code_improvement' and insight['priority'] == 'high':
                try:
                    # Generate actual code change
                    code_change = await self._generate_code_change(insight['content'])
                    
                    if code_change:
                        # Apply the change
                        success = await self._apply_change_to_file(code_change)
                        
                        applied_changes.append({
                            "insight": insight['content'],
                            "file": code_change['file'],
                            "change_type": code_change['type'],
                            "success": success,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        if success:
                            logger.info(f"✅ Applied code change: {code_change['file']}")
                        else:
                            logger.warning(f"⚠️ Failed to apply: {code_change['file']}")
                
                except Exception as e:
                    logger.error(f"❌ Code improvement failed: {e}")
                    applied_changes.append({
                        "insight": insight['content'],
                        "success": False,
                        "error": str(e)
                    })
        
        return applied_changes
    
    async def _generate_code_change(self, improvement_description: str) -> Optional[Dict[str, Any]]:
        """Generate actual code change based on improvement"""
        if not OPENAI_AVAILABLE or not self.api_key:
            # Fallback to simple code generation
            return self._simple_code_generation(improvement_description)
        
        try:
            client = openai.OpenAI(api_key=self.api_key)
            
            prompt = f"""
            Generate a specific code improvement for the Chatty automation system.
            
            Improvement needed: {improvement_description}
            
            Available files to modify:
            - ENHANCED_MULTI_AGENT_SYSTEM.py (main system)
            - CONTEXT_WINDOW_MANAGER.py (context management)
            - REAL_YOUTUBE_LEARNER.py (learning system)
            
            Return JSON:
            {{
                "file": "filename.py",
                "type": "add_function|modify_function|add_class|add_import",
                "code": "actual Python code",
                "description": "what this does"
            }}
            """
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600,
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            logger.error(f"❌ Code generation failed: {e}")
            return self._simple_code_generation(improvement_description)
    
    def _simple_code_generation(self, improvement: str) -> Optional[Dict[str, Any]]:
        """Simple fallback code generation"""
        # Map improvements to basic code changes
        improvement_lower = improvement.lower()
        
        if 'agent' in improvement_lower and 'communication' in improvement_lower:
            return {
                "file": "ENHANCED_MULTI_AGENT_SYSTEM.py",
                "type": "add_function",
                "code": """
async def enhanced_agent_communication(self, message: str, agents: List[str]) -> Dict[str, Any]:
    \"\"\"Enhanced communication between agents\"\"\"
    results = {}
    for agent_id in agents:
        if agent_id in self.agents:
            results[agent_id] = await self.agents[agent_id].process_message(message)
    return results
""",
                "description": "Add enhanced agent communication"
            }
        
        elif 'optimization' in improvement_lower:
            return {
                "file": "ENHANCED_MULTI_AGENT_SYSTEM.py",
                "type": "add_function",
                "code": """
def optimize_system_performance(self) -> Dict[str, Any]:
    \"\"\"Optimize system performance\"\"\"
    optimizations = {
        "memory_usage": self._optimize_memory(),
        "token_usage": self._optimize_tokens(),
        "agent_efficiency": self._optimize_agents()
    }
    return optimizations
""",
                "description": "Add system performance optimization"
            }
        
        return None
    
    async def _apply_change_to_file(self, code_change: Dict[str, Any]) -> bool:
        """Apply code change to actual file"""
        try:
            file_path = self.codebase_path / code_change['file']
            
            if not file_path.exists():
                logger.warning(f"⚠️ File not found: {file_path}")
                return False
            
            # Read current content
            current_content = file_path.read_text()
            
            # Apply change based on type
            if code_change['type'] == 'add_function':
                # Add function to end of file
                new_content = current_content + "\n\n" + code_change['code']
            elif code_change['type'] == 'add_import':
                # Add import at top
                lines = current_content.split('\n')
                import_index = 0
                for i, line in enumerate(lines):
                    if line.startswith('import') or line.startswith('from'):
                        import_index = i + 1
                lines.insert(import_index, code_change['code'])
                new_content = '\n'.join(lines)
            else:
                # Default: append
                new_content = current_content + "\n\n" + code_change['code']
            
            # Write back
            file_path.write_text(new_content)
            
            logger.info(f"✅ Code change applied to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to apply code change: {e}")
            return False
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """Get comprehensive learning statistics"""
        if not self.learning_database:
            return {
                "videos_processed": 0,
                "total_code_changes": 0,
                "last_learning": None,
                "topics_covered": []
            }
        
        total_changes = sum(
            len(video.get('code_changes_applied', [])) 
            for video in self.learning_database.values()
        )
        
        all_topics = []
        for video in self.learning_database.values():
            all_topics.extend(video.get('analysis', {}).get('key_topics', []))
        
        return {
            "videos_processed": len(self.learning_database),
            "total_code_changes": total_changes,
            "last_learning": max(
                video['timestamp'] 
                for video in self.learning_database.values()
            ),
            "topics_covered": list(set(all_topics)),
            "recent_videos": [
                {
                    "video_id": video_id,
                    "title": video['metadata'].get('title', ''),
                    "changes": len(video.get('code_changes_applied', []))
                }
                for video_id, video in list(self.learning_database.items())[-5:]
            ]
        }

# ============================================================================
# DEMONSTRATION
# ============================================================================

async def main():
    """Demonstrate the functional YouTube learner"""
    print("🚀 Functional YouTube Learning System")
    print("=" * 50)
    
    learner = FunctionalYouTubeLearner()
    
    # Test with a real video about AI/automation
    test_videos = [
        "https://www.youtube.com/watch?v=jkrO6OyfGnM",  # AI agents
        "https://www.youtube.com/watch?v=si8z_jk7g5c",  # Automation
        "https://www.youtube.com/watch?v=wH7vqrz8oOs"   # Multi-agent systems
    ]
    
    for video_url in test_videos[:1]:  # Test one video
        print(f"\n🎥 Processing: {video_url}")
        result = await learner.learn_from_video(video_url)
        
        if result.get('success'):
            print(f"✅ Learning successful!")
            print(f"📊 Analysis: {result['analysis']}")
            print(f"🔧 Code changes: {len(result['code_changes_applied'])}")
        else:
            print(f"❌ Learning failed: {result.get('error')}")
    
    # Show stats
    stats = learner.get_learning_stats()
    print(f"\n📈 Learning Stats:")
    print(json.dumps(stats, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
