#!/usr/bin/env python3
"""
Cole Medin Channel Learning System
Learns from Cole Medin's YouTube channel and applies advanced AI techniques to Chatty
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

# YouTube API
try:
    from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, VideoUnavailable
    from youtube_transcript_api.formatters import TextFormatter
    YOUTUBE_API_AVAILABLE = True
except ImportError:
    YOUTUBE_API_AVAILABLE = False

# AI for analysis
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Web scraping
try:
    import requests
    from bs4 import BeautifulSoup
    WEB_SCRAPING_AVAILABLE = True
except ImportError:
    WEB_SCRAPING_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ColeMedinChannelLearner:
    """Specialized learner for Cole Medin's channel content"""
    
    def __init__(self):
        self.channel_id = "UCZ92LYsgE9p2pZtF6LZ8B2A"  # Cole Medin's channel ID
        self.learning_database = {}
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.codebase_path = Path('.')
        
        # Cole Medin's specific expertise areas
        self.cole_topics = [
            "agent zero", "archon 2", "bmad", "autonomous agents",
            "multi-agent systems", "ai orchestration", "agent coordination",
            "advanced ai", "agent frameworks", "intelligent automation",
            "agent communication", "distributed ai", "agent swarms"
        ]
        
        # Techniques Cole Medin specializes in
        self.cole_techniques = [
            "agent fleet management", "zero-shot coordination", 
            "emergent behavior", "agent communication protocols",
            "distributed decision making", "agent specialization",
            "real-time agent orchestration", "agent learning loops"
        ]
        
        logger.info("🧠 Cole Medin Channel Learner initialized")
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check dependencies"""
        missing = []
        if not YOUTUBE_API_AVAILABLE:
            missing.append("youtube-transcript-api")
        if not OPENAI_AVAILABLE:
            missing.append("openai")
        if not WEB_SCRAPING_AVAILABLE:
            missing.append("requests/beautifulsoup4")
        
        if missing:
            logger.warning(f"⚠️ Missing: {missing}")
        else:
            logger.info("✅ All dependencies available")
    
    async def learn_from_cole_medin_video(self, video_url: str) -> Dict[str, Any]:
        """Learn from Cole Medin video with specialized analysis"""
        try:
            logger.info(f"🧠 Learning from Cole Medin: {video_url}")
            
            # Extract video ID
            video_id = self._extract_video_id(video_url)
            if not video_id:
                return {"error": "Invalid URL", "success": False}
            
            # Get transcript
            transcript = await self._get_transcript(video_id)
            if not transcript:
                return {"error": "No transcript", "success": False}
            
            # Get metadata
            metadata = await self._get_metadata(video_id)
            
            # Specialized Cole Medin analysis
            cole_analysis = await self._analyze_cole_content(transcript, metadata)
            
            # Extract agent techniques
            agent_techniques = await self._extract_agent_techniques(transcript, cole_analysis)
            
            # Generate Chatty improvements based on Cole's methods
            chatty_improvements = await self._generate_chatty_improvements(agent_techniques)
            
            # Apply improvements to codebase
            applied_changes = await self._apply_cole_inspired_changes(chatty_improvements)
            
            result = {
                "success": True,
                "video_id": video_id,
                "url": video_url,
                "metadata": metadata,
                "cole_analysis": cole_analysis,
                "agent_techniques": agent_techniques,
                "chatty_improvements": chatty_improvements,
                "applied_changes": applied_changes,
                "timestamp": datetime.now().isoformat()
            }
            
            self.learning_database[video_id] = result
            logger.info(f"✅ Cole Medin learning complete: {len(applied_changes)} improvements applied")
            return result
            
        except Exception as e:
            logger.error(f"❌ Cole Medin learning failed: {e}")
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
            
            logger.info(f"✅ Transcript extracted: {len(formatted_transcript)} chars")
            return formatted_transcript
            
        except Exception as e:
            logger.error(f"❌ Transcript failed: {e}")
            return None
    
    async def _get_metadata(self, video_id: str) -> Dict[str, Any]:
        """Get video metadata"""
        metadata = {
            "video_id": video_id,
            "title": "",
            "channel": "Cole Medin",
            "description": "",
            "upload_date": ""
        }
        
        if WEB_SCRAPING_AVAILABLE:
            try:
                url = f"https://www.youtube.com/watch?v={video_id}"
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    title_tag = soup.find('title')
                    if title_tag:
                        metadata['title'] = title_tag.text.replace(' - YouTube', '')
                    
                    desc_tag = soup.find('meta', {'property': 'og:description'})
                    if desc_tag:
                        metadata['description'] = desc_tag.get('content', '')[:500]
                
            except Exception as e:
                logger.warning(f"⚠️ Metadata extraction failed: {e}")
        
        return metadata
    
    async def _analyze_cole_content(self, transcript: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Specialized analysis for Cole Medin's content"""
        if not OPENAI_AVAILABLE or not self.api_key:
            return self._cole_keyword_analysis(transcript)
        
        try:
            client = openai.OpenAI(api_key=self.api_key)
            
            prompt = f"""
            Analyze this Cole Medin video content for advanced AI agent techniques:
            
            Title: {metadata.get('title', '')}
            
            Transcript: {transcript[:2500]}...
            
            Focus on Cole Medin's expertise:
            - Agent Zero and Archon 2 implementations
            - BMAD agent behavioral modeling
            - Autonomous agent orchestration
            - Agent communication protocols
            - Distributed AI systems
            - Real-time agent coordination
            - Agent fleet management
            - Emergent agent behaviors
            
            Return JSON:
            {{
                "cole_relevance_score": 0.0-1.0,
                "agent_frameworks_mentioned": ["agent zero", "archon 2", "bmad"],
                "key_techniques": ["technique1", "technique2"],
                "implementation_patterns": ["pattern1", "pattern2"],
                "advanced_concepts": ["concept1", "concept2"],
                "chatty_applications": ["application1", "application2"]
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
            return self._cole_keyword_analysis(transcript)
    
    def _cole_keyword_analysis(self, transcript: str) -> Dict[str, Any]:
        """Fallback keyword analysis for Cole's content"""
        text_lower = transcript.lower()
        
        frameworks_found = []
        techniques_found = []
        concepts_found = []
        
        # Check for Cole's specific frameworks
        for framework in ["agent zero", "archon 2", "bmad", "agent fleet"]:
            if framework in text_lower:
                frameworks_found.append(framework)
        
        # Check for techniques
        for technique in self.cole_techniques:
            if technique in text_lower:
                techniques_found.append(technique)
        
        # Check for concepts
        for concept in ["autonomous", "orchestration", "coordination", "emergent", "distributed"]:
            if concept in text_lower:
                concepts_found.append(concept)
        
        return {
            "cole_relevance_score": min((len(frameworks_found) + len(techniques_found)) * 0.2, 1.0),
            "agent_frameworks_mentioned": frameworks_found,
            "key_techniques": techniques_found,
            "implementation_patterns": [f"Implement {tech}" for tech in techniques_found[:3]],
            "advanced_concepts": concepts_found,
            "chatty_applications": [f"Apply {concept} to Chatty" for concept in concepts_found[:3]]
        }
    
    async def _extract_agent_techniques(self, transcript: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract specific agent techniques from analysis"""
        techniques = []
        
        for technique in analysis.get('key_techniques', []):
            techniques.append({
                "type": "agent_technique",
                "name": technique,
                "source": "cole_medin",
                "priority": "high",
                "description": f"Cole Medin's {technique} approach",
                "timestamp": datetime.now().isoformat()
            })
        
        for framework in analysis.get('agent_frameworks_mentioned', []):
            techniques.append({
                "type": "agent_framework",
                "name": framework,
                "source": "cole_medin",
                "priority": "high",
                "description": f"Cole Medin's {framework} framework",
                "timestamp": datetime.now().isoformat()
            })
        
        return techniques
    
    async def _generate_chatty_improvements(self, techniques: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate specific Chatty improvements based on Cole's techniques"""
        improvements = []
        
        for technique in techniques:
            if technique['type'] == 'agent_framework':
                improvement = await self._generate_framework_improvement(technique)
            elif technique['type'] == 'agent_technique':
                improvement = await self._generate_technique_improvement(technique)
            
            if improvement:
                improvements.append(improvement)
        
        return improvements
    
    async def _generate_framework_improvement(self, framework: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate improvement for agent framework"""
        framework_name = framework['name'].lower()
        
        if 'agent zero' in framework_name:
            return {
                "type": "framework_integration",
                "name": "Agent Zero Integration",
                "description": "Integrate Agent Zero fleet management into Chatty",
                "file": "AGENT_ZERO_INTEGRATION.py",
                "code": self._generate_agent_zero_code(),
                "priority": "high"
            }
        elif 'archon 2' in framework_name:
            return {
                "type": "framework_integration",
                "name": "Archon 2 Integration",
                "description": "Add Archon 2 agent orchestration capabilities",
                "file": "ARCHON2_INTEGRATION.py",
                "code": self._generate_archon2_code(),
                "priority": "high"
            }
        elif 'bmad' in framework_name:
            return {
                "type": "framework_integration",
                "name": "BMAD Integration",
                "description": "Integrate BMAD behavioral modeling for agents",
                "file": "BMAD_INTEGRATION.py",
                "code": self._generate_bmad_code(),
                "priority": "medium"
            }
        
        return None
    
    async def _generate_technique_improvement(self, technique: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate improvement for agent technique"""
        technique_name = technique['name'].lower()
        
        if 'fleet' in technique_name:
            return {
                "type": "technique_implementation",
                "name": "Agent Fleet Management",
                "description": "Implement Cole Medin's agent fleet coordination",
                "file": "ENHANCED_MULTI_AGENT_SYSTEM.py",
                "code": self._generate_fleet_code(),
                "priority": "high"
            }
        elif 'communication' in technique_name:
            return {
                "type": "technique_implementation",
                "name": "Enhanced Agent Communication",
                "description": "Add Cole Medin's agent communication protocols",
                "file": "ENHANCED_MULTI_AGENT_SYSTEM.py",
                "code": self._generate_communication_code(),
                "priority": "medium"
            }
        
        return None
    
    def _generate_agent_zero_code(self) -> str:
        """Generate Agent Zero integration code"""
        return '''
# Agent Zero Integration - Inspired by Cole Medin
class AgentZeroFleet:
    """Agent Zero fleet management system"""
    
    def __init__(self):
        self.agents = {}
        self.fleet_coordinator = None
        
    async def deploy_fleet(self, fleet_config: dict) -> dict:
        """Deploy agent fleet using Agent Zero patterns"""
        fleet_id = f"agent_zero_fleet_{int(time.time())}"
        
        # Initialize fleet coordinator
        self.fleet_coordinator = FleetCoordinator(fleet_id)
        
        # Deploy specialized agents
        agents = []
        for agent_type in fleet_config.get('agent_types', ['worker', 'coordinator', 'specialist']):
            agent = await self._create_agent_zero_agent(agent_type, fleet_id)
            agents.append(agent)
            self.agents[agent.id] = agent
        
        return {"fleet_id": fleet_id, "agents": len(agents)}
    
    async def _create_agent_zero_agent(self, agent_type: str, fleet_id: str):
        """Create Agent Zero style agent"""
        return AgentZeroAgent(
            id=f"{fleet_id}_{agent_type}_{int(time.time())}",
            type=agent_type,
            capabilities=self._get_agent_capabilities(agent_type)
        )
'''
    
    def _generate_archon2_code(self) -> str:
        """Generate Archon 2 integration code"""
        return '''
# Archon 2 Integration - Inspired by Cole Medin
class Archon2Orchestrator:
    """Archon 2 agent orchestration system"""
    
    def __init__(self):
        self.orchestrator = None
        self.agent_hierarchy = {}
        
    async def initialize_archon2(self) -> dict:
        """Initialize Archon 2 orchestrator"""
        self.orchestrator = Archon2Core()
        
        # Setup agent hierarchy
        await self._setup_agent_hierarchy()
        
        return {"status": "initialized", "hierarchy_levels": len(self.agent_hierarchy)}
    
    async def _setup_agent_hierarchy(self):
        """Setup Cole Medin's agent hierarchy pattern"""
        self.agent_hierarchy = {
            "level_1": "master_coordinators",
            "level_2": "domain_specialists", 
            "level_3": "task_executors",
            "level_4": "utility_agents"
        }
'''
    
    def _generate_bmad_code(self) -> str:
        """Generate BMAD integration code"""
        return '''
# BMAD Integration - Inspired by Cole Medin
class BMADBehavioralModel:
    """BMAD (Behavioral Modeling Agent Dynamics) system"""
    
    def __init__(self):
        self.behavioral_models = {}
        self.agent_behaviors = {}
        
    async def model_agent_behavior(self, agent_id: str, behavior_data: dict) -> dict:
        """Model agent behavior using BMAD principles"""
        model = BMADModel(agent_id)
        
        # Analyze behavioral patterns
        patterns = await self._analyze_behavioral_patterns(behavior_data)
        
        # Create behavioral model
        behavioral_model = {
            "agent_id": agent_id,
            "patterns": patterns,
            "predictions": await self._predict_behaviors(patterns),
            "optimizations": await self._generate_optimizations(patterns)
        }
        
        self.behavioral_models[agent_id] = behavioral_model
        return behavioral_model
'''
    
    def _generate_fleet_code(self) -> str:
        """Generate fleet management code"""
        return '''
    async def manage_agent_fleet(self, fleet_id: str, task: dict) -> dict:
        """Manage agent fleet using Cole Medin's coordination patterns"""
        fleet = self.fleets.get(fleet_id)
        if not fleet:
            return {"error": "Fleet not found"}
        
        # Distribute task across fleet
        task_distribution = await self._distribute_task(fleet, task)
        
        # Coordinate execution
        results = await self._coordinate_fleet_execution(fleet, task_distribution)
        
        return {"fleet_id": fleet_id, "results": results, "coordination_time": time.time()}
'''
    
    def _generate_communication_code(self) -> str:
        """Generate enhanced communication code"""
        return '''
    async def enhanced_agent_communication(self, message: str, target_agents: list) -> dict:
        """Enhanced communication using Cole Medin's protocols"""
        communication_protocol = CommunicationProtocol("cole_medin_style")
        
        # Route message through specialized channels
        routed_messages = await communication_protocol.route_message(message, target_agents)
        
        # Collect responses
        responses = {}
        for agent_id, routed_msg in routed_messages.items():
            if agent_id in self.agents:
                responses[agent_id] = await self.agents[agent_id].process_cole_protocol_message(routed_msg)
        
        return {"message": message, "responses": responses, "protocol": "cole_medin"}
'''
    
    async def _apply_cole_inspired_changes(self, improvements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply Cole Medin inspired changes to codebase"""
        applied = []
        
        for improvement in improvements:
            try:
                file_path = self.codebase_path / improvement['file']
                
                # Read existing content or create new file
                if file_path.exists():
                    content = file_path.read_text()
                else:
                    content = f"# {improvement['name']}\n# Inspired by Cole Medin\n\n"
                
                # Add the improvement
                new_content = content + "\n\n" + improvement['code']
                
                # Write back
                file_path.write_text(new_content)
                
                applied.append({
                    "improvement": improvement['name'],
                    "file": improvement['file'],
                    "success": True,
                    "timestamp": datetime.now().isoformat()
                })
                
                logger.info(f"✅ Applied Cole Medin improvement: {improvement['name']}")
                
            except Exception as e:
                logger.error(f"❌ Failed to apply {improvement['name']}: {e}")
                applied.append({
                    "improvement": improvement['name'],
                    "success": False,
                    "error": str(e)
                })
        
        return applied
    
    def get_cole_learning_stats(self) -> Dict[str, Any]:
        """Get Cole Medin learning statistics"""
        if not self.learning_database:
            return {
                "cole_videos_processed": 0,
                "frameworks_integrated": [],
                "techniques_applied": 0,
                "total_improvements": 0
            }
        
        all_frameworks = []
        total_improvements = 0
        
        for video in self.learning_database.values():
            all_frameworks.extend(video.get('cole_analysis', {}).get('agent_frameworks_mentioned', []))
            total_improvements += len(video.get('applied_changes', []))
        
        return {
            "cole_videos_processed": len(self.learning_database),
            "frameworks_integrated": list(set(all_frameworks)),
            "techniques_applied": total_improvements,
            "total_improvements": total_improvements,
            "recent_videos": [
                {
                    "video_id": video_id,
                    "title": video['metadata'].get('title', ''),
                    "frameworks": video['cole_analysis'].get('agent_frameworks_mentioned', []),
                    "improvements": len(video['applied_changes'])
                }
                for video_id, video in list(self.learning_database.items())[-3:]
            ]
        }

# ============================================================================
# COLE MEDIN CHANNEL SCANNER
# ============================================================================

async def scan_cole_medin_channel():
    """Scan Cole Medin's channel for relevant videos"""
    # In production, would use YouTube Data API to get channel videos
    # For now, return some known Cole Medin video URLs
    cole_videos = [
        "https://www.youtube.com/watch?v=example1",  # Agent Zero tutorial
        "https://www.youtube.com/watch?v=example2",  # Archon 2 demonstration
        "https://www.youtube.com/watch?v=example3",  # BMAD behavioral modeling
    ]
    
    return cole_videos

# ============================================================================
# MAIN DEMONSTRATION
# ============================================================================

async def main():
    """Demonstrate Cole Medin learning"""
    print("🧠 Cole Medin Channel Learning System")
    print("=" * 50)
    
    learner = ColeMedinChannelLearner()
    
    # Get Cole Medin videos
    videos = await scan_cole_medin_channel()
    print(f"📺 Found {len(videos)} Cole Medin videos")
    
    # Process first video (example)
    if videos:
        print(f"\n🎥 Learning from: {videos[0]}")
        result = await learner.learn_from_cole_medin_video(videos[0])
        
        if result.get('success'):
            print("✅ Learning successful!")
            print(f"🎯 Cole's relevance: {result['cole_analysis'].get('cole_relevance_score', 0)}")
            print(f"🔧 Frameworks found: {result['cole_analysis'].get('agent_frameworks_mentioned', [])}")
            print(f"💡 Improvements applied: {len(result['applied_changes'])}")
        else:
            print(f"❌ Learning failed: {result.get('error')}")
    
    # Show stats
    stats = learner.get_cole_learning_stats()
    print(f"\n📊 Cole Medin Learning Stats:")
    print(json.dumps(stats, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
