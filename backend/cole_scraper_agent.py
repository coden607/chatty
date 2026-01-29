#!/usr/bin/env python3
"""
CHATTY Cole Medin Scraper Agent
Specialized agent for comprehensive YouTube channel analysis and autonomous system upgrade
"""

import os
import re
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import concurrent.futures

import requests
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp
from sentence_transformers import SentenceTransformer
import networkx as nx
from sklearn.cluster import KMeans
import numpy as np

from server import db, Agent, Task, logger
from youtube_agent import YouTubeTranscriptionAgent, ToolDownloaderAgent, KnowledgeSynthesizerAgent
from learning_system import memory_system, adaptive_learning
from agent_factory import agent_factory
from code_executor import code_executor

class ColeMedinScraperAgent:
    """Specialized agent for scraping and learning from Cole Medin's YouTube channel"""

    def __init__(self):
        self.youtube_agent = YouTubeTranscriptionAgent()
        self.tool_downloader = ToolDownloaderAgent()
        self.knowledge_synthesizer = KnowledgeSynthesizerAgent()

        # Cole Medin's channel specifics
        self.channel_id = "UCGq-a57w-aPwyCMZgDQA8Dw"  # Cole Medin's channel
        self.channel_handle = "@ColeMedin"  # Alternative identifier

        # Analysis results
        self.channel_analysis = {}
        self.extracted_knowledge = {}
        self.discovered_tools = []
        self.learned_techniques = []
        self.upgrade_recommendations = []

        # Progress tracking
        self.scraping_progress = {
            'videos_found': 0,
            'videos_processed': 0,
            'tools_discovered': 0,
            'knowledge_extracted': 0,
            'upgrades_applied': 0
        }

    def create_scraper_agent(self) -> Dict[str, Any]:
        """Create a specialized agent for Cole Medin channel scraping"""
        agent_config = {
            'name': 'ColeMedinScraperAgent',
            'description': 'Specialized agent for scraping and learning from Cole Medin\'s YouTube channel to autonomously upgrade the CHATTY system',
            'capabilities': [
                'youtube_scraping',
                'content_analysis',
                'knowledge_extraction',
                'tool_discovery',
                'system_upgrade',
                'autonomous_learning'
            ],
            'tools': [
                'youtube_transcript_api',
                'yt_dlp',
                'sentence_transformers',
                'requests',
                'beautifulsoup4'
            ],
            'config': {
                'channel_id': self.channel_id,
                'max_videos_per_batch': 10,
                'analysis_depth': 'comprehensive',
                'autonomous_upgrades': True,
                'learning_objectives': [
                    'extract_technical_knowledge',
                    'discover_tools_and_software',
                    'learn_programming_techniques',
                    'understand_ai_methodologies',
                    'identify_system_architectures'
                ]
            },
            'autonomy_level': 'autonomous'
        }

        return agent_config

    def scrape_entire_channel(self) -> Dict[str, Any]:
        """Scrape and analyze the entire Cole Medin YouTube channel"""
        logger.info("Starting comprehensive Cole Medin channel scraping")

        try:
            # Step 1: Get all video IDs from the channel
            video_ids = self._get_all_channel_videos()
            self.scraping_progress['videos_found'] = len(video_ids)

            logger.info(f"Found {len(video_ids)} videos in Cole Medin channel")

            # Step 2: Process videos in batches
            batch_size = 10
            all_analyses = []

            for i in range(0, len(video_ids), batch_size):
                batch = video_ids[i:i + batch_size]
                batch_analyses = self._process_video_batch(batch)
                all_analyses.extend(batch_analyses)

                self.scraping_progress['videos_processed'] += len(batch)
                logger.info(f"Processed {self.scraping_progress['videos_processed']}/{len(video_ids)} videos")

                # Brief pause to be respectful to YouTube API
                time.sleep(2)

            # Step 3: Synthesize all knowledge
            synthesized_knowledge = self._synthesize_channel_knowledge(all_analyses)

            # Step 4: Extract upgrade recommendations
            upgrade_plan = self._create_upgrade_plan(synthesized_knowledge)

            # Step 5: Execute autonomous upgrades
            upgrade_results = self._execute_autonomous_upgrades(upgrade_plan)

            return {
                'success': True,
                'videos_processed': len(all_analyses),
                'knowledge_extracted': synthesized_knowledge,
                'upgrade_plan': upgrade_plan,
                'upgrade_results': upgrade_results,
                'progress': self.scraping_progress
            }

        except Exception as e:
            logger.error("Channel scraping failed", error=str(e))
            return {
                'success': False,
                'error': str(e),
                'progress': self.scraping_progress
            }

    def _get_all_channel_videos(self) -> List[str]:
        """Get all video IDs from Cole Medin's channel"""
        video_ids = []

        try:
            # Use yt-dlp to get channel videos
            ydl_opts = {
                'quiet': True,
                'extract_flat': True,
                'force_generic_extractor': False,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Try multiple channel URL formats
                channel_urls = [
                    f"https://www.youtube.com/channel/{self.channel_id}",
                    f"https://www.youtube.com/{self.channel_handle}",
                    f"https://www.youtube.com/c/ColeMedin"
                ]

                for url in channel_urls:
                    try:
                        result = ydl.extract_info(url, download=False)
                        if 'entries' in result:
                            for entry in result['entries']:
                                if entry.get('id'):
                                    video_ids.append(entry['id'])
                            break
                    except Exception as e:
                        logger.warning(f"Failed to extract from {url}", error=str(e))
                        continue

            # Remove duplicates
            video_ids = list(set(video_ids))

        except Exception as e:
            logger.error("Failed to get channel videos", error=str(e))

        return video_ids

    def _process_video_batch(self, video_ids: List[str]) -> List[Dict[str, Any]]:
        """Process a batch of videos for analysis"""
        analyses = []

        # Use thread pool for parallel processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_to_video = {
                executor.submit(self._analyze_single_video, video_id): video_id
                for video_id in video_ids
            }

            for future in concurrent.futures.as_completed(future_to_video):
                video_id = future_to_video[future]
                try:
                    analysis = future.result()
                    if analysis:
                        analyses.append(analysis)
                except Exception as e:
                    logger.error(f"Failed to analyze video {video_id}", error=str(e))

        return analyses

    def _analyze_single_video(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Analyze a single video comprehensively"""
        try:
            # Get transcript
            transcript = self.youtube_agent.get_transcript(video_id)
            if 'error' in transcript:
                logger.warning(f"No transcript available for video {video_id}")
                return None

            # Analyze content
            content_analysis = self.youtube_agent.analyze_content(transcript)

            # Enhanced analysis for Cole Medin specific content
            cole_specific_analysis = self._analyze_cole_medin_content(transcript, content_analysis)

            # Store in learning system
            memory_system.store_experience('cole_scraper_agent', {
                'type': 'video_analysis',
                'content': {
                    'video_id': video_id,
                    'transcript_length': len(transcript.get('full_text', '')),
                    'topics': content_analysis.get('topics', []),
                    'tools_mentioned': content_analysis.get('mentioned_tools', [])
                },
                'tags': ['cole_medin', 'video_analysis', 'knowledge_extraction']
            })

            return {
                'video_id': video_id,
                'transcript': transcript,
                'content_analysis': content_analysis,
                'cole_specific_analysis': cole_specific_analysis,
                'processed_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Video analysis failed for {video_id}", error=str(e))
            return None

    def _analyze_cole_medin_content(self, transcript: Dict[str, Any], content_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Perform Cole Medin specific content analysis"""
        text = transcript.get('full_text', '')

        # Cole Medin specific patterns
        analysis = {
            'technical_concepts': [],
            'tools_and_software': [],
            'programming_languages': [],
            'ai_techniques': [],
            'system_architectures': [],
            'business_insights': [],
            'educational_value': 0
        }

        # Extract technical concepts
        tech_patterns = [
            r'\b(AI|artificial intelligence|machine learning|deep learning|neural network)\b',
            r'\b(blockchain|cryptocurrency|web3|defi|smart contract)\b',
            r'\b(devops|docker|kubernetes|cloud|aws|azure|gcp)\b',
            r'\b(react|vue|angular|node|python|rust|golang|typescript)\b',
            r'\b(api|microservice|serverless|lambda|function)\b'
        ]

        for pattern in tech_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            analysis['technical_concepts'].extend(matches)

        # Identify tools and software (building on existing analysis)
        tool_indicators = [
            r'\b(install|download|use|get)\s+(\w+(?:\s+\w+)*?)(?:\s+(?:from|via|using|with)\s+(\w+))?',
            r'\b(\w+(?:\s+\w+)*?)\s+(?:library|framework|tool|software|app|platform)\b',
            r'\b(GPT|ChatGPT|Claude|Bard|Midjourney|DALL-E|Stable Diffusion)\b',
            r'\b(VSCode|Vim|Emacs|PyCharm|WebStorm|IntelliJ)\b'
        ]

        for pattern in tool_indicators:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    tool = ' '.join([m for m in match if m])
                else:
                    tool = match
                if tool and len(tool) > 2:
                    analysis['tools_and_software'].append(tool.strip())

        # Programming languages mentioned
        languages = ['Python', 'JavaScript', 'TypeScript', 'Go', 'Rust', 'Java', 'C++', 'C#', 'PHP', 'Ruby']
        for lang in languages:
            if re.search(r'\b' + re.escape(lang) + r'\b', text, re.IGNORECASE):
                analysis['programming_languages'].append(lang)

        # AI techniques and methodologies
        ai_techniques = [
            'prompt engineering', 'fine-tuning', 'transfer learning', 'reinforcement learning',
            'supervised learning', 'unsupervised learning', 'computer vision', 'nlp',
            'natural language processing', 'generative ai', 'large language model'
        ]
        for technique in ai_techniques:
            if technique.lower() in text.lower():
                analysis['ai_techniques'].append(technique)

        # Assess educational value
        educational_indicators = [
            'tutorial', 'guide', 'how to', 'learn', 'understand', 'explained',
            'step by step', 'beginner', 'advanced', 'tips', 'tricks'
        ]
        analysis['educational_value'] = sum(1 for indicator in educational_indicators
                                          if indicator in text.lower())

        # Remove duplicates
        for key in analysis:
            if isinstance(analysis[key], list):
                analysis[key] = list(set(analysis[key]))

        return analysis

    def _synthesize_channel_knowledge(self, video_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Synthesize knowledge from all video analyses"""
        logger.info("Synthesizing knowledge from channel analysis")

        # Aggregate all findings
        all_technical_concepts = []
        all_tools = []
        all_languages = []
        all_ai_techniques = []
        all_architectures = []

        for analysis in video_analyses:
            cole_analysis = analysis.get('cole_specific_analysis', {})

            all_technical_concepts.extend(cole_analysis.get('technical_concepts', []))
            all_tools.extend(cole_analysis.get('tools_and_software', []))
            all_languages.extend(cole_analysis.get('programming_languages', []))
            all_ai_techniques.extend(cole_analysis.get('ai_techniques', []))

        # Create knowledge graph
        knowledge_graph = self._build_knowledge_graph(video_analyses)

        # Identify key themes and patterns
        themes = self._identify_key_themes(video_analyses)

        # Generate learning path
        learning_path = self._create_learning_path(themes, all_tools, all_languages)

        synthesized = {
            'total_videos_analyzed': len(video_analyses),
            'technical_concepts': list(set(all_technical_concepts)),
            'tools_discovered': list(set(all_tools)),
            'programming_languages': list(set(all_languages)),
            'ai_techniques': list(set(all_ai_techniques)),
            'key_themes': themes,
            'knowledge_graph': knowledge_graph,
            'recommended_learning_path': learning_path,
            'educational_value_assessment': self._assess_educational_value(video_analyses)
        }

        self.extracted_knowledge = synthesized
        return synthesized

    def _build_knowledge_graph(self, video_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build a knowledge graph from video content"""
        graph = nx.DiGraph()

        # Add nodes for concepts, tools, and techniques
        for analysis in video_analyses:
            cole_analysis = analysis.get('cole_specific_analysis', {})

            # Add concept nodes
            for concept in cole_analysis.get('technical_concepts', []):
                graph.add_node(concept, type='concept')

            # Add tool nodes
            for tool in cole_analysis.get('tools_and_software', []):
                graph.add_node(tool, type='tool')

            # Add technique nodes
            for technique in cole_analysis.get('ai_techniques', []):
                graph.add_node(technique, type='technique')

        # Add edges based on co-occurrence in videos
        # This is a simplified implementation - could be enhanced
        concepts = [n for n in graph.nodes() if graph.nodes[n].get('type') == 'concept']
        tools = [n for n in graph.nodes() if graph.nodes[n].get('type') == 'tool']

        # Connect concepts to tools they enable
        for concept in concepts:
            for tool in tools:
                if concept.lower() in tool.lower() or tool.lower() in concept.lower():
                    graph.add_edge(concept, tool, relationship='enables')

        return {
            'nodes': list(graph.nodes()),
            'edges': list(graph.edges(data=True)),
            'node_types': dict(graph.nodes(data='type'))
        }

    def _identify_key_themes(self, video_analyses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify key themes across all videos"""
        theme_clusters = defaultdict(int)

        for analysis in video_analyses:
            content_analysis = analysis.get('content_analysis', {})
            topics = content_analysis.get('topics', [])

            for topic in topics:
                theme_clusters[topic] += 1

        # Sort by frequency
        sorted_themes = sorted(theme_clusters.items(), key=lambda x: x[1], reverse=True)

        themes = []
        for theme, count in sorted_themes[:10]:  # Top 10 themes
            themes.append({
                'theme': theme,
                'frequency': count,
                'percentage': count / len(video_analyses) * 100
            })

        return themes

    def _create_learning_path(self, themes: List[Dict[str, Any]], tools: List[str], languages: List[str]) -> List[Dict[str, Any]]:
        """Create a recommended learning path based on extracted knowledge"""

        # Define learning progression
        learning_stages = [
            {
                'stage': 'foundation',
                'focus': 'Programming Fundamentals',
                'languages': ['Python', 'JavaScript'],
                'concepts': ['variables', 'functions', 'loops', 'data structures']
            },
            {
                'stage': 'intermediate',
                'focus': 'Web Development & APIs',
                'languages': ['JavaScript', 'TypeScript', 'Python'],
                'concepts': ['APIs', 'databases', 'web frameworks']
            },
            {
                'stage': 'advanced',
                'focus': 'AI & Machine Learning',
                'languages': ['Python', 'JavaScript'],
                'concepts': ['machine learning', 'neural networks', 'prompt engineering']
            },
            {
                'stage': 'expert',
                'focus': 'System Architecture & Scaling',
                'languages': ['Go', 'Rust', 'Python'],
                'concepts': ['microservices', 'cloud architecture', 'performance optimization']
            }
        ]

        # Customize based on Cole's content
        for stage in learning_stages:
            # Add tools relevant to this stage
            stage_tools = [tool for tool in tools if self._tool_matches_stage(tool, stage)]
            stage['recommended_tools'] = stage_tools[:5]  # Top 5 tools per stage

            # Add relevant themes
            stage_themes = [theme for theme in themes if self._theme_matches_stage(theme['theme'], stage)]
            stage['related_themes'] = stage_themes[:3]

        return learning_stages

    def _tool_matches_stage(self, tool: str, stage: Dict[str, Any]) -> bool:
        """Check if a tool is relevant to a learning stage"""
        tool_lower = tool.lower()
        stage_focus = stage['focus'].lower()

        # Simple matching - could be enhanced with ML
        if 'foundation' in stage['stage']:
            return any(keyword in tool_lower for keyword in ['python', 'javascript', 'vscode', 'git'])
        elif 'intermediate' in stage['stage']:
            return any(keyword in tool_lower for keyword in ['react', 'node', 'api', 'database'])
        elif 'advanced' in stage['stage']:
            return any(keyword in tool_lower for keyword in ['ai', 'ml', 'gpt', 'tensorflow'])
        elif 'expert' in stage['stage']:
            return any(keyword in tool_lower for keyword in ['docker', 'kubernetes', 'aws', 'architecture'])

        return False

    def _theme_matches_stage(self, theme: str, stage: Dict[str, Any]) -> bool:
        """Check if a theme matches a learning stage"""
        theme_lower = theme.lower()
        stage_concepts = [concept.lower() for concept in stage.get('concepts', [])]

        return any(concept in theme_lower for concept in stage_concepts)

    def _assess_educational_value(self, video_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess the overall educational value of the channel"""
        total_educational_value = 0
        video_count = len(video_analyses)

        for analysis in video_analyses:
            cole_analysis = analysis.get('cole_specific_analysis', {})
            total_educational_value += cole_analysis.get('educational_value', 0)

        avg_educational_value = total_educational_value / video_count if video_count > 0 else 0

        return {
            'total_videos': video_count,
            'average_educational_value': avg_educational_value,
            'total_educational_score': total_educational_value,
            'assessment': 'high' if avg_educational_value > 5 else 'medium' if avg_educational_value > 2 else 'low'
        }

    def _create_upgrade_plan(self, synthesized_knowledge: Dict[str, Any]) -> Dict[str, Any]:
        """Create a comprehensive upgrade plan based on learned knowledge"""
        logger.info("Creating autonomous upgrade plan")

        upgrade_plan = {
            'tools_to_install': [],
            'agents_to_create': [],
            'capabilities_to_add': [],
            'system_improvements': [],
            'new_functionality': []
        }

        # 1. Tools to install
        discovered_tools = synthesized_knowledge.get('tools_discovered', [])
        for tool in discovered_tools:
            if tool in self.tool_downloader.tool_database:
                upgrade_plan['tools_to_install'].append({
                    'name': tool,
                    'category': self.tool_downloader.tool_database[tool].get('category'),
                    'reason': 'Discovered in Cole Medin content'
                })

        # 2. Agents to create based on themes
        themes = synthesized_knowledge.get('key_themes', [])
        for theme_data in themes[:5]:  # Top 5 themes
            theme = theme_data['theme']
            agent_config = self._create_agent_for_theme(theme, synthesized_knowledge)
            if agent_config:
                upgrade_plan['agents_to_create'].append(agent_config)

        # 3. Capabilities to add
        ai_techniques = synthesized_knowledge.get('ai_techniques', [])
        for technique in ai_techniques:
            upgrade_plan['capabilities_to_add'].append({
                'capability': technique,
                'implementation': 'integrate_into_existing_agents',
                'priority': 'high'
            })

        # 4. System improvements
        upgrade_plan['system_improvements'] = [
            'enhance_learning_system_with_cole_knowledge',
            'improve_ai_model_integration',
            'add_autonomous_research_capabilities',
            'implement_advanced_prompt_engineering'
        ]

        # 5. New functionality
        upgrade_plan['new_functionality'] = [
            'youtube_channel_monitoring',
            'content_based_agent_creation',
            'autonomous_skill_acquisition',
            'knowledge_graph_expansion'
        ]

        self.upgrade_recommendations = upgrade_plan
        return upgrade_plan

    def _create_agent_for_theme(self, theme: str, knowledge: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create an agent configuration for a specific theme"""

        theme_agents = {
            'programming': {
                'name': 'CodeMasterAgent',
                'capabilities': ['code_generation', 'debugging', 'code_review'],
                'specialization': 'programming_assistance'
            },
            'web development': {
                'name': 'WebDevAgent',
                'capabilities': ['web_development', 'api_design', 'frontend_backend_integration'],
                'specialization': 'web_development'
            },
            'data science': {
                'name': 'DataScienceAgent',
                'capabilities': ['data_analysis', 'visualization', 'machine_learning'],
                'specialization': 'data_science'
            },
            'artificial intelligence': {
                'name': 'AIAgent',
                'capabilities': ['ai_integration', 'prompt_engineering', 'model_fine_tuning'],
                'specialization': 'ai_assistance'
            }
        }

        # Find matching agent
        for key, agent_config in theme_agents.items():
            if key.lower() in theme.lower():
                # Enhance with learned tools
                relevant_tools = [tool for tool in knowledge.get('tools_discovered', [])
                                if self._tool_matches_theme(tool, key)]
                agent_config['tools'] = relevant_tools[:5]
                return agent_config

        return None

    def _tool_matches_theme(self, tool: str, theme: str) -> bool:
        """Check if a tool matches a theme"""
        tool_lower = tool.lower()
        theme_lower = theme.lower()

        theme_keywords = {
            'programming': ['python', 'javascript', 'vscode', 'git', 'docker'],
            'web development': ['react', 'node', 'api', 'html', 'css'],
            'data science': ['pandas', 'numpy', 'jupyter', 'matplotlib'],
            'artificial intelligence': ['gpt', 'claude', 'ai', 'ml', 'neural']
        }

        keywords = theme_keywords.get(theme_lower, [])
        return any(keyword in tool_lower for keyword in keywords)

    def _execute_autonomous_upgrades(self, upgrade_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the autonomous upgrade plan"""
        logger.info("Executing autonomous upgrades")

        upgrade_results = {
            'tools_installed': [],
            'agents_created': [],
            'capabilities_added': [],
            'improvements_made': [],
            'errors': []
        }

        # 1. Install tools
        tools_to_install = upgrade_plan.get('tools_to_install', [])
        for tool_info in tools_to_install:
            try:
                result = self.tool_downloader.download_and_install(tool_info['name'])
                if result.get('success'):
                    upgrade_results['tools_installed'].append(tool_info['name'])
                    self.scraping_progress['tools_discovered'] += 1
                else:
                    upgrade_results['errors'].append(f"Failed to install {tool_info['name']}: {result.get('error')}")
            except Exception as e:
                upgrade_results['errors'].append(f"Tool installation error for {tool_info['name']}: {str(e)}")

        # 2. Create agents
        agents_to_create = upgrade_plan.get('agents_to_create', [])
        for agent_config in agents_to_create:
            try:
                # Use agent factory to create the agent
                full_config = agent_factory.create_agent_from_description(
                    f"Create an agent specialized in {agent_config.get('specialization', 'general tasks')}",
                    'system',  # System user
                    agent_config.get('specialization')
                )

                # Override with specific config
                full_config.update(agent_config)

                # Create agent in database
                agent = Agent(
                    name=full_config['name'],
                    description=full_config.get('description', ''),
                    capabilities=full_config.get('capabilities', []),
                    tools=full_config.get('tools', []),
                    config=full_config.get('config', {}),
                    autonomy_level=full_config.get('autonomy_level', 'supervised'),
                    user_id='system'  # System-generated agent
                )

                with db.session.begin():
                    db.session.add(agent)

                upgrade_results['agents_created'].append(full_config['name'])
                logger.info("Created specialized agent", agent_name=full_config['name'])

            except Exception as e:
                upgrade_results['errors'].append(f"Agent creation error for {agent_config.get('name')}: {str(e)}")

        # 3. Log improvements made
        upgrade_results['improvements_made'] = upgrade_plan.get('system_improvements', [])

        # 4. Store upgrade results in learning system
        memory_system.store_experience('cole_scraper_agent', {
            'type': 'system_upgrade',
            'content': upgrade_results,
            'outcome': 'success' if not upgrade_results['errors'] else 'partial_success',
            'tags': ['system_upgrade', 'autonomous_improvement', 'cole_medin_inspired']
        })

        self.scraping_progress['upgrades_applied'] = len(upgrade_results['tools_installed']) + len(upgrade_results['agents_created'])

        return upgrade_results

# Global instance
cole_scraper = ColeMedinScraperAgent()
