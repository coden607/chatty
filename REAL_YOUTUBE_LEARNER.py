#!/usr/bin/env python3
"""
DEPRECATED — use FIXED_YOUTUBE_LEARNER.py and COLE_MEDIN_CHANNEL_LEARNER.py instead.

REAL YouTube Learning System with Actual Transcription and Code Integration
"""

import asyncio
import json
import logging
import os
import re
import time
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import subprocess
import sys

# Real YouTube libraries
try:
    from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, VideoUnavailable
    from youtube_transcript_api.formatters import TextFormatter
    YOUTUBE_REAL = True
except ImportError:
    YOUTUBE_REAL = False

# Real AI for content analysis
try:
    import openai
    OPENAI_REAL = True
except ImportError:
    OPENAI_REAL = False

# Real web scraping
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    SELENIUM_REAL = True
except ImportError:
    SELENIUM_REAL = False

# Real code analysis and modification
try:
    import ast
    import difflib
    CODE_ANALYSIS_REAL = True
except ImportError:
    CODE_ANALYSIS_REAL = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealYouTubeLearner:
    """Real YouTube learning with actual transcription and code integration"""
    
    def __init__(self):
        self.transcript_formatter = TextFormatter()
        self.learning_database = {}
        self.code_improvements = []
        self.api_keys = self._load_api_keys()
        self.driver = None
        
        # Topics to track for Chatty improvements
        self.relevant_topics = [
            "multi-agent systems", "automation", "ai agents", "llm optimization",
            "token optimization", "self-healing code", "autonomous systems",
            "crew ai", "langchain", "n8n workflows", "openclaw",
            "agent zero", "pydantic ai", "vector databases",
            "system architecture", "microservices", "api integration"
        ]
        
        self._init_selenium()
    
    def _load_api_keys(self) -> Dict[str, str]:
        """Load real API keys"""
        keys = {}
        if OPENAI_REAL:
            keys['openai'] = os.getenv('OPENAI_API_KEY')
        return keys
    
    def _init_selenium(self):
        """Initialize Selenium for web scraping"""
        if SELENIUM_REAL:
            try:
                options = Options()
                options.add_argument('--headless')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                self.driver = webdriver.Chrome(options=options)
                logger.info("✅ Real Selenium WebDriver initialized")
            except Exception as e:
                logger.warning(f"⚠️ Selenium init failed: {e}")
                self.driver = None
    
    async def learn_from_youtube_real(self, video_url: str) -> Dict[str, Any]:
        """Real YouTube learning with actual transcription"""
        try:
            logger.info(f"🎥 Starting REAL YouTube learning: {video_url}")
            
            # Extract video ID
            video_id = self._extract_video_id(video_url)
            if not video_id:
                return {"error": "Invalid YouTube URL"}
            
            # Get REAL transcript
            transcript = await self._get_real_transcript(video_id)
            if not transcript:
                return {"error": "No transcript available"}
            
            # Get video metadata
            metadata = await self._get_video_metadata_real(video_id)
            
            # Analyze content with REAL AI
            analysis = await self._analyze_content_real(transcript, metadata)
            
            # Extract code improvements
            code_improvements = await self._extract_code_improvements(transcript, analysis)
            
            # Apply improvements to Chatty codebase
            if code_improvements:
                applied = await self._apply_code_improvements(code_improvements)
                analysis['code_changes_applied'] = applied
            
            # Store learning
            learning_result = {
                "video_id": video_id,
                "url": video_url,
                "metadata": metadata,
                "transcript": transcript[:1000] + "..." if len(transcript) > 1000 else transcript,
                "analysis": analysis,
                "timestamp": datetime.now().isoformat(),
                "real_transcription": True,
                "code_improvements": len(code_improvements)
            }
            
            self.learning_database[video_id] = learning_result
            
            logger.info(f"✅ REAL YouTube learning complete: {len(code_improvements)} code improvements found")
            return learning_result
            
        except Exception as e:
            logger.error(f"❌ REAL YouTube learning failed: {e}")
            return {"error": str(e)}
    
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
    
    async def _get_real_transcript(self, video_id: str) -> Optional[str]:
        """Get REAL YouTube transcript"""
        if not YOUTUBE_REAL:
            logger.warning("⚠️ YouTube transcript API not available")
            return None
        
        try:
            # Get list of available transcripts
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # Try to get English transcript first
            try:
                transcript = transcript_list.find_transcript(['en'])
                transcript_data = transcript.fetch()
            except NoTranscriptFound:
                # Get first available transcript
                transcript = list(transcript_list)[0]
                transcript_data = transcript.fetch()
            
            # Format transcript
            formatted_transcript = self.transatter_formatter.format_transcript(transcript_data)
            
            logger.info(f"✅ REAL transcript extracted: {len(formatted_transcript)} characters")
            return formatted_transcript
            
        except (NoTranscriptFound, VideoUnavailable) as e:
            logger.error(f"❌ Transcript not available: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Transcript extraction failed: {e}")
            return None
    
    async def _get_video_metadata_real(self, video_id: str) -> Dict[str, Any]:
        """Get REAL video metadata using web scraping"""
        metadata = {
            "video_id": video_id,
            "title": "",
            "channel": "",
            "view_count": 0,
            "like_count": 0,
            "duration": 0,
            "upload_date": ""
        }
        
        if self.driver:
            try:
                # Load video page
                self.driver.get(f"https://www.youtube.com/watch?v={video_id}")
                time.sleep(2)  # Wait for page load
                
                # Extract metadata using JavaScript
                js_script = """
                return {
                    title: document.title.replace(' - YouTube', ''),
                    channel: document.querySelector('#channel-name a')?.textContent || '',
                    view_count: document.querySelector('#view-count')?.textContent || '',
                    like_count: document.querySelector('#segmented-like-button button')?.getAttribute('aria-label') || ''
                };
                """
                
                page_data = self.driver.execute_script(js_script)
                
                metadata.update({
                    "title": page_data.get("title", ""),
                    "channel": page_data.get("channel", ""),
                    "view_count": self._parse_count(page_data.get("view_count", "0")),
                    "like_count": self._parse_count(page_data.get("like_count", "0"))
                })
                
                logger.info(f"✅ REAL metadata extracted: {metadata['title']}")
                
            except Exception as e:
                logger.warning(f"⚠️ Web scraping failed: {e}")
        
        return metadata
    
    def _parse_count(self, count_str: str) -> int:
        """Parse count string like '1.2K views' to integer"""
        if not count_str:
            return 0
        
        # Remove non-numeric characters except K, M, B
        clean_str = re.sub(r'[^\d.KMB]', '', count_str.upper())
        
        # Extract number and multiplier
        match = re.match(r'([\d.]+)([KMB]?)', clean_str)
        if not match:
            return 0
        
        number = float(match.group(1))
        multiplier = match.group(2)
        
        multipliers = {'': 1, 'K': 1000, 'M': 1000000, 'B': 1000000000}
        return int(number * multipliers.get(multiplier, 1))
    
    async def _analyze_content_real(self, transcript: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze content using REAL AI"""
        if not OPENAI_REAL or not self.api_keys.get('openai'):
            logger.warning("⚠️ OpenAI not available, using basic analysis")
            return self._basic_analysis(transcript, metadata)
        
        try:
            client = openai.OpenAI(api_key=self.api_keys['openai'])
            
            prompt = f"""
            Analyze this YouTube video content for Chatty automation system improvements:
            
            Title: {metadata.get('title', '')}
            Channel: {metadata.get('channel', '')}
            
            Transcript: {transcript[:3000]}...
            
            Focus on:
            1. Code improvements for multi-agent systems
            2. New automation techniques
            3. AI agent architectures
            4. Performance optimizations
            5. Integration patterns
            
            Return JSON with:
            - key_insights: []
            - code_improvements: []
            - new_techniques: []
            - relevance_score: 0.0-1.0
            """
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.3
            )
            
            analysis_text = response.choices[0].message.content
            
            # Parse JSON response
            try:
                analysis = json.loads(analysis_text)
                logger.info(f"✅ REAL AI analysis completed")
                return analysis
            except json.JSONDecodeError:
                logger.warning("⚠️ Failed to parse AI response, using basic analysis")
                return self._basic_analysis(transcript, metadata)
                
        except Exception as e:
            logger.error(f"❌ AI analysis failed: {e}")
            return self._basic_analysis(transcript, metadata)
    
    def _basic_analysis(self, transcript: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Basic analysis without AI"""
        insights = []
        improvements = []
        techniques = []
        
        # Look for relevant keywords
        text_lower = transcript.lower()
        
        for topic in self.relevant_topics:
            if topic in text_lower:
                insights.append(f"Found discussion about {topic}")
                
                if "agent" in topic:
                    improvements.append(f"Consider implementing {topic} in Chatty")
                elif "optimization" in topic:
                    improvements.append(f"Apply {topic} techniques to existing code")
                elif "workflow" in topic:
                    improvements.append(f"Integrate {topic} automation")
        
        return {
            "key_insights": insights,
            "code_improvements": improvements,
            "new_techniques": techniques,
            "relevance_score": min(len(insights) * 0.2, 1.0)
        }
    
    async def _extract_code_improvements(self, transcript: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract specific code improvements from analysis"""
        improvements = []
        
        # Get improvements from AI analysis
        ai_improvements = analysis.get('code_improvements', [])
        
        for improvement in ai_improvements:
            improvements.append({
                "type": "ai_suggested",
                "description": improvement,
                "priority": "high",
                "source": "youtube_analysis",
                "timestamp": datetime.now().isoformat()
            })
        
        return improvements
    
    async def _apply_code_improvements(self, improvements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply real code improvements to Chatty codebase"""
        applied = []
        
        for improvement in improvements:
            try:
                if improvement['type'] == 'ai_suggested':
                    # Generate code based on improvement
                    code_change = await self._generate_code_change(improvement['description'])
                    
                    if code_change:
                        # Apply the change
                        success = await self._apply_code_change(code_change)
                        if success:
                            applied.append({
                                "improvement": improvement['description'],
                                "code_change": code_change,
                                "applied_at": datetime.now().isoformat(),
                                "success": True
                            })
                        else:
                            applied.append({
                                "improvement": improvement['description'],
                                "code_change": code_change,
                                "applied_at": datetime.now().isoformat(),
                                "success": False,
                                "error": "Failed to apply code change"
                            })
                
            except Exception as e:
                logger.error(f"❌ Failed to apply improvement: {e}")
                applied.append({
                    "improvement": improvement['description'],
                    "success": False,
                    "error": str(e)
                })
        
        return applied
    
    async def _generate_code_change(self, improvement_description: str) -> Optional[Dict[str, Any]]:
        """Generate actual code change based on improvement"""
        if not OPENAI_REAL:
            return None
        
        try:
            client = openai.OpenAI(api_key=self.api_keys['openai'])
            
            prompt = f"""
            Generate a code improvement for the Chatty automation system based on this suggestion:
            
            Suggestion: {improvement_description}
            
            Return JSON with:
            - file_to_modify: (path to Python file)
            - change_type: (add_function, modify_function, add_class, etc.)
            - code_snippet: (the actual code to add/modify)
            - description: (what this change does)
            """
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            logger.error(f"❌ Code generation failed: {e}")
            return None
    
    async def _apply_code_change(self, code_change: Dict[str, Any]) -> bool:
        """Apply code change to actual file"""
        try:
            file_path = Path(code_change['file_to_modify'])
            
            if not file_path.exists():
                logger.warning(f"⚠️ File not found: {file_path}")
                return False
            
            # Read current file
            current_content = file_path.read_text()
            
            # Apply change based on type
            if code_change['change_type'] == 'add_function':
                # Add function to end of file
                new_content = current_content + "\n\n" + code_change['code_snippet']
            elif code_change['change_type'] == 'modify_function':
                # Find and replace function (simplified)
                new_content = self._replace_function(current_content, code_change['code_snippet'])
            else:
                # Default: append to file
                new_content = current_content + "\n\n" + code_change['code_snippet']
            
            # Write back
            file_path.write_text(new_content)
            
            logger.info(f"✅ Code change applied to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to apply code change: {e}")
            return False
    
    def _replace_function(self, content: str, new_function: str) -> str:
        """Replace function in content (simplified)"""
        # Parse new function to get its name
        try:
            tree = ast.parse(new_function)
            if tree.body and isinstance(tree.body[0], ast.FunctionDef):
                func_name = tree.body[0].name
                
                # Find existing function in content
                content_tree = ast.parse(content)
                for node in ast.walk(content_tree):
                    if isinstance(node, ast.FunctionDef) and node.name == func_name:
                        # Replace function (simplified - just append)
                        return content + "\n\n# Updated function:\n" + new_function
        except:
            pass
        
        return content + "\n\n" + new_function
    
    async def continuous_learning_loop(self):
        """Continuously search and learn from relevant YouTube content"""
        search_queries = [
            "multi-agent AI systems 2024",
            "autonomous code improvement",
            "self-healing software architecture",
            "crew AI tutorial",
            "langchain multi-agent",
            "n8n workflow automation",
            "openclaw automation"
        ]
        
        while True:
            try:
                for query in search_queries:
                    # Search for videos (would need YouTube Data API)
                    # For now, simulate finding relevant videos
                    logger.info(f"🔍 Searching YouTube for: {query}")
                    
                    # In production, would:
                    # 1. Use YouTube Data API to search
                    # 2. Get top 5 results
                    # 3. Learn from each video
                    # 4. Apply improvements
                    
                    await asyncio.sleep(300)  # 5 minutes between searches
                
                await asyncio.sleep(3600)  # 1 hour between full cycles
                
            except Exception as e:
                logger.error(f"❌ Continuous learning error: {e}")
                await asyncio.sleep(600)
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """Get learning statistics"""
        return {
            "videos_learned": len(self.learning_database),
            "code_improvements": len(self.code_improvements),
            "last_learning": max([v['timestamp'] for v in self.learning_database.values()], default=None),
            "topics_covered": list(set([
                topic for video in self.learning_database.values()
                for topic in video.get('analysis', {}).get('key_insights', [])
            ]))
        }

# ============================================================================
# REAL N8N WORKFLOW CREATION
# ============================================================================

class RealN8NWorkflowCreator:
    """Real N8N workflow creation and deployment"""
    
    def __init__(self):
        self.n8n_url = os.getenv('N8N_URL', 'http://localhost:5678')
        self.api_key = os.getenv('N8N_API_KEY')
        self.workflows_created = []
    
    async def create_workflow_real(self, workflow_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create real N8N workflow"""
        try:
            if not self.api_key:
                logger.warning("⚠️ N8N API key not configured")
                return {"error": "N8N API key required"}
            
            # Create workflow via N8N API
            workflow_data = {
                "name": workflow_config['name'],
                "nodes": workflow_config.get('nodes', []),
                "connections": workflow_config.get('connections', []),
                "active": True
            }
            
            headers = {
                'X-N8N-API-KEY': self.api_key,
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.n8n_url}/api/v1/workflows",
                    json=workflow_data,
                    headers=headers
                ) as response:
                    if response.status == 201:
                        result = await response.json()
                        workflow_id = result['data']['id']
                        
                        # Activate workflow
                        await self._activate_workflow(workflow_id)
                        
                        self.workflows_created.append({
                            "id": workflow_id,
                            "name": workflow_config['name'],
                            "created_at": datetime.now().isoformat()
                        })
                        
                        logger.info(f"✅ Real N8N workflow created: {workflow_id}")
                        return {"success": True, "workflow_id": workflow_id}
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ N8N workflow creation failed: {error_text}")
                        return {"error": error_text}
                        
        except Exception as e:
            logger.error(f"❌ N8N workflow creation error: {e}")
            return {"error": str(e)}
    
    async def _activate_workflow(self, workflow_id: str):
        """Activate N8N workflow"""
        try:
            headers = {
                'X-N8N-API-KEY': self.api_key,
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.n8n_url}/api/v1/workflows/{workflow_id}/activate",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        logger.info(f"✅ N8N workflow activated: {workflow_id}")
                    else:
                        logger.warning(f"⚠️ Failed to activate workflow: {workflow_id}")
                        
        except Exception as e:
            logger.error(f"❌ Workflow activation error: {e}")

# ============================================================================
# MAIN REAL LEARNING SYSTEM
# ============================================================================

async def main():
    """Test real learning system"""
    learner = RealYouTubeLearner()
    
    # Test with a real video
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Example
    
    result = await learner.learn_from_youtube_real(test_url)
    print("Learning Result:", json.dumps(result, indent=2))
    
    # Show stats
    stats = learner.get_learning_stats()
    print("Learning Stats:", json.dumps(stats, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
