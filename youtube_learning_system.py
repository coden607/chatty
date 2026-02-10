#!/usr/bin/env python3
"""
DEPRECATED — use FIXED_YOUTUBE_LEARNER.py and COLE_MEDIN_CHANNEL_LEARNER.py instead.

YouTube Learning System
AI-powered video analysis and learning with transcript extraction and knowledge integration
"""

import os
import json
import time
import asyncio
import logging
import re
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
from collections import defaultdict
import concurrent.futures

import requests
from pydantic import BaseModel, Field, validator
from sentence_transformers import SentenceTransformer
import networkx as nx
import numpy as np
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

from server import db, Agent, Task, logger
from learning_system import memory_system, adaptive_learning
from openclaw_integration import MultiLLMRouter

class VideoMetadata(BaseModel):
    """Pydantic model for video metadata"""
    video_id: str
    title: str
    channel: str
    duration: int
    publish_date: Optional[datetime] = None
    description: str = ""
    tags: List[str] = Field(default_factory=list)
    view_count: int = 0
    like_count: int = 0
    category: str = ""
    
    @validator('video_id')
    def validate_video_id(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]{11}$', v):
            raise ValueError('Invalid YouTube video ID format')
        return v

class TranscriptSegment(BaseModel):
    """Pydantic model for transcript segments"""
    start: float
    duration: float
    text: str
    speaker: Optional[str] = None
    
    @validator('start', 'duration')
    def validate_time(cls, v):
        if v < 0:
            raise ValueError('Time values must be non-negative')
        return v

class LearningInsight(BaseModel):
    """Pydantic model for learning insights"""
    insight_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str  # 'concept', 'fact', 'procedure', 'example'
    content: str
    confidence: float = Field(ge=0.0, le=1.0)
    relevance_score: float = Field(ge=0.0, le=1.0)
    keywords: List[str] = Field(default_factory=list)
    related_insights: List[str] = Field(default_factory=list)
    timestamp: Optional[float] = None

class KnowledgeIntegration(BaseModel):
    """Pydantic model for knowledge integration"""
    integration_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_video: str
    integration_type: str  # 'content_generation', 'system_improvement', 'feature_idea'
    content: str
    implementation_priority: str  # 'low', 'medium', 'high', 'critical'
    estimated_effort: str  # 'small', 'medium', 'large'
    potential_impact: str  # 'low', 'medium', 'high'
    status: str = 'pending'  # 'pending', 'implemented', 'rejected'

class YouTubeLearningSystem:
    """AI-powered YouTube learning and analysis system"""
    
    def __init__(self):
        self.name = "YouTube Learning System"
        self.capabilities = [
            'transcript_extraction', 'content_analysis', 'insight_extraction',
            'knowledge_integration', 'automatic_content_generation'
        ]
        
        # AI components
        self.transcript_extractor = TranscriptExtractor()
        self.content_analyzer = ContentAnalyzer()
        self.insight_extractor = InsightExtractor()
        self.knowledge_integrator = KnowledgeIntegrator()
        
        # Learning and memory
        self.learned_videos = {}
        self.knowledge_base = {}
        self.content_library = {}
        
        # Configuration
        self.max_video_duration = 3600  # 1 hour
        self.min_confidence_threshold = 0.7
        self.learning_enabled = True
        
        # AI models
        self.embeddings_model = None
        self._init_embeddings_model()
    
    def _init_embeddings_model(self):
        """Initialize sentence embeddings model"""
        try:
            self.embeddings_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✅ Sentence embeddings model loaded")
        except Exception as e:
            logger.warning(f"⚠️ Failed to load embeddings model: {str(e)}")
    
    async def learn_from_video(self, video_url: str, learning_goals: List[str] = None) -> Dict[str, Any]:
        """Complete learning pipeline from YouTube video"""
        try:
            logger.info(f"🎥 YouTube Learning: Starting analysis of {video_url}")
            
            # Extract video ID
            video_id = self._extract_video_id(video_url)
            if not video_id:
                raise ValueError("Invalid YouTube URL")
            
            # Get video metadata
            metadata = await self._get_video_metadata(video_id)
            
            # Extract transcript
            transcript = await self.transcript_extractor.extract_transcript(video_id)
            
            # Analyze content
            analysis = await self.content_analyzer.analyze_content(transcript, metadata, learning_goals)
            
            # Extract insights
            insights = await self.insight_extractor.extract_insights(transcript, analysis, learning_goals)
            
            # Integrate knowledge
            integrations = await self.knowledge_integrator.integrate_knowledge(
                video_id, insights, metadata, learning_goals
            )
            
            # Generate content
            content = await self._generate_content_from_learning(video_id, insights, integrations)
            
            # Store learning results
            learning_result = {
                'video_id': video_id,
                'metadata': metadata.dict(),
                'transcript_summary': analysis.get('summary', ''),
                'insights': [insight.dict() for insight in insights],
                'integrations': [integration.dict() for integration in integrations],
                'generated_content': content,
                'timestamp': datetime.utcnow().isoformat(),
                'learning_goals': learning_goals or []
            }
            
            self.learned_videos[video_id] = learning_result
            
            logger.info(f"✅ YouTube Learning: Completed analysis of {metadata.title}")
            return learning_result
            
        except Exception as e:
            logger.error(f"❌ YouTube Learning: Failed to analyze {video_url}: {str(e)}")
            return {'error': str(e), 'video_url': video_url}
    
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
    
    async def _get_video_metadata(self, video_id: str) -> VideoMetadata:
        """Get video metadata using YouTube Data API or web scraping"""
        try:
            # This would integrate with YouTube Data API
            # For now, return mock metadata
            metadata = VideoMetadata(
                video_id=video_id,
                title="Sample Video Title",
                channel="Sample Channel",
                duration=600,  # 10 minutes
                description="Sample video description",
                tags=["sample", "video", "learning"],
                view_count=1000,
                like_count=100,
                category="Education"
            )
            return metadata
            
        except Exception as e:
            logger.warning(f"Failed to get metadata for {video_id}: {str(e)}")
            return VideoMetadata(video_id=video_id, title="Unknown Video", channel="Unknown", duration=0)
    
    async def _generate_content_from_learning(self, video_id: str, insights: List[LearningInsight], 
                                            integrations: List[KnowledgeIntegration]) -> Dict[str, Any]:
        """Generate content based on learned insights"""
        try:
            # Generate blog post
            blog_content = await self._generate_blog_post(video_id, insights, integrations)
            
            # Generate social media content
            social_content = await self._generate_social_content(video_id, insights, integrations)
            
            # Generate implementation guide
            implementation_guide = await self._generate_implementation_guide(video_id, insights, integrations)
            
            return {
                'blog_post': blog_content,
                'social_content': social_content,
                'implementation_guide': implementation_guide,
                'content_summary': f"Generated {len(insights)} insights and {len(integrations)} integrations"
            }
            
        except Exception as e:
            logger.error(f"Content generation failed: {str(e)}")
            return {'error': str(e)}
    
    async def _generate_blog_post(self, video_id: str, insights: List[LearningInsight], 
                                integrations: List[KnowledgeIntegration]) -> str:
        """Generate blog post from learned content"""
        try:
            # Use AI to generate blog post
            prompt = f"""
            Generate a comprehensive blog post based on these learning insights:
            
            Video ID: {video_id}
            Insights: {[insight.content for insight in insights[:5]]}
            Integrations: {[integration.content for integration in integrations[:3]]}
            
            The blog post should be:
            - Informative and engaging
            - Include practical examples
            - Have a clear structure with introduction, body, and conclusion
            - Include actionable insights
            - Be optimized for SEO
            """
            
            ai_task = {
                'description': 'Generate blog post from learning insights',
                'prompt': prompt,
                'max_tokens': 2000
            }
            
            result = self.knowledge_integrator.multi_llm_router.route_task(ai_task)
            return result.get('content', '')
            
        except Exception as e:
            logger.error(f"Blog post generation failed: {str(e)}")
            return f"Error generating blog post: {str(e)}"
    
    async def _generate_social_content(self, video_id: str, insights: List[LearningInsight], 
                                     integrations: List[KnowledgeIntegration]) -> Dict[str, Any]:
        """Generate social media content from learned insights"""
        try:
            # Generate Twitter thread
            twitter_thread = await self._generate_twitter_thread(video_id, insights)
            
            # Generate LinkedIn post
            linkedin_post = await self._generate_linkedin_post(video_id, insights, integrations)
            
            # Generate Instagram caption
            instagram_caption = await self._generate_instagram_caption(video_id, insights)
            
            return {
                'twitter_thread': twitter_thread,
                'linkedin_post': linkedin_post,
                'instagram_caption': instagram_caption
            }
            
        except Exception as e:
            logger.error(f"Social content generation failed: {str(e)}")
            return {'error': str(e)}
    
    async def _generate_twitter_thread(self, video_id: str, insights: List[LearningInsight]) -> str:
        """Generate Twitter thread from insights"""
        try:
            prompt = f"""
            Generate a viral Twitter thread based on these insights from video {video_id}:
            
            Insights: {[insight.content for insight in insights[:3]]}
            
            The thread should:
            - Be 5-7 tweets long
            - Each tweet should be under 280 characters
            - Be engaging and shareable
            - Include relevant hashtags
            - Have a clear narrative flow
            """
            
            ai_task = {
                'description': 'Generate Twitter thread from insights',
                'prompt': prompt,
                'max_tokens': 1000
            }
            
            result = self.knowledge_integrator.multi_llm_router.route_task(ai_task)
            return result.get('content', '')
            
        except Exception as e:
            return f"Error generating Twitter thread: {str(e)}"
    
    async def _generate_linkedin_post(self, video_id: str, insights: List[LearningInsight], 
                                    integrations: List[KnowledgeIntegration]) -> str:
        """Generate LinkedIn post from insights"""
        try:
            prompt = f"""
            Generate a professional LinkedIn post based on these insights from video {video_id}:
            
            Insights: {[insight.content for insight in insights[:3]]}
            Integrations: {[integration.content for integration in integrations[:2]]}
            
            The post should:
            - Be professional and insightful
            - Include industry-relevant keywords
            - Be 3-4 paragraphs long
            - Include a call to action
            - Be optimized for professional networking
            """
            
            ai_task = {
                'description': 'Generate LinkedIn post from insights',
                'prompt': prompt,
                'max_tokens': 1500
            }
            
            result = self.knowledge_integrator.multi_llm_router.route_task(ai_task)
            return result.get('content', '')
            
        except Exception as e:
            return f"Error generating LinkedIn post: {str(e)}"
    
    async def _generate_instagram_caption(self, video_id: str, insights: List[LearningInsight]) -> str:
        """Generate Instagram caption from insights"""
        try:
            prompt = f"""
            Generate an engaging Instagram caption based on these insights from video {video_id}:
            
            Insights: {[insight.content for insight in insights[:2]]}
            
            The caption should:
            - Be concise and engaging
            - Include relevant emojis
            - Include 5-10 relevant hashtags
            - Be inspirational or educational
            - Encourage engagement
            """
            
            ai_task = {
                'description': 'Generate Instagram caption from insights',
                'prompt': prompt,
                'max_tokens': 500
            }
            
            result = self.knowledge_integrator.multi_llm_router.route_task(ai_task)
            return result.get('content', '')
            
        except Exception as e:
            return f"Error generating Instagram caption: {str(e)}"
    
    async def _generate_implementation_guide(self, video_id: str, insights: List[LearningInsight], 
                                           integrations: List[KnowledgeIntegration]) -> str:
        """Generate implementation guide from insights"""
        try:
            prompt = f"""
            Generate a practical implementation guide based on these insights from video {video_id}:
            
            Insights: {[insight.content for insight in insights[:5]]}
            Integrations: {[integration.content for integration in integrations[:3]]}
            
            The guide should:
            - Be step-by-step and actionable
            - Include practical examples
            - Be organized in clear sections
            - Include success metrics
            - Be suitable for immediate implementation
            """
            
            ai_task = {
                'description': 'Generate implementation guide from insights',
                'prompt': prompt,
                'max_tokens': 2500
            }
            
            result = self.knowledge_integrator.multi_llm_router.route_task(ai_task)
            return result.get('content', '')
            
        except Exception as e:
            return f"Error generating implementation guide: {str(e)}"

class TranscriptExtractor:
    """Extract and process YouTube transcripts"""
    
    def __init__(self):
        self.formatter = TextFormatter()
    
    async def extract_transcript(self, video_id: str) -> List[TranscriptSegment]:
        """Extract transcript from YouTube video"""
        try:
            # Get available transcripts
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # Get English transcript (or first available)
            transcript = None
            try:
                transcript = transcript_list.find_transcript(['en'])
            except:
                # Fall back to first available transcript
                transcript = list(transcript_list)[0]
            
            # Fetch transcript data
            transcript_data = transcript.fetch()
            
            # Convert to TranscriptSegment objects
            segments = []
            for segment in transcript_data:
                segments.append(TranscriptSegment(
                    start=segment['start'],
                    duration=segment['duration'],
                    text=segment['text']
                ))
            
            logger.info(f"✅ Transcript extracted: {len(segments)} segments")
            return segments
            
        except Exception as e:
            logger.error(f"❌ Transcript extraction failed: {str(e)}")
            return []
    
    def get_full_transcript_text(self, segments: List[TranscriptSegment]) -> str:
        """Get full transcript as text"""
        return ' '.join(segment.text for segment in segments)
    
    def get_transcript_summary(self, segments: List[TranscriptSegment], max_length: int = 1000) -> str:
        """Get summary of transcript"""
        full_text = self.get_full_transcript_text(segments)
        
        # Simple summarization (could be enhanced with AI)
        if len(full_text) <= max_length:
            return full_text
        
        # Truncate and add ellipsis
        return full_text[:max_length] + "..."

class ContentAnalyzer:
    """Analyze video content and extract key information"""
    
    def __init__(self):
        self.multi_llm_router = MultiLLMRouter()
    
    async def analyze_content(self, transcript: List[TranscriptSegment], 
                            metadata: VideoMetadata, 
                            learning_goals: List[str] = None) -> Dict[str, Any]:
        """Analyze video content for key insights"""
        try:
            # Get full transcript text
            full_text = TranscriptExtractor().get_full_transcript_text(transcript)
            
            # Analyze content using AI
            analysis_task = {
                'description': 'Analyze video content for key insights',
                'prompt': f"""
                Analyze this video transcript and extract key information:
                
                Video Title: {metadata.title}
                Channel: {metadata.channel}
                Duration: {metadata.duration} seconds
                
                Transcript: {full_text[:5000]}...
                
                Learning Goals: {learning_goals or 'General learning'}
                
                Please provide:
                1. Main topics covered
                2. Key concepts and ideas
                3. Important facts and statistics
                4. Practical applications
                5. Overall summary
                """,
                'max_tokens': 1500
            }
            
            result = self.multi_llm_router.route_task(analysis_task)
            
            return {
                'summary': result.get('content', ''),
                'topics': self._extract_topics(full_text),
                'concepts': self._extract_concepts(full_text),
                'facts': self._extract_facts(full_text),
                'applications': self._extract_applications(full_text),
                'analysis_confidence': 0.8  # Mock confidence score
            }
            
        except Exception as e:
            logger.error(f"Content analysis failed: {str(e)}")
            return {'error': str(e)}
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract main topics from text"""
        # Simple topic extraction (could be enhanced with NLP)
        topics = []
        
        # Look for common topic indicators
        topic_patterns = [
            r'\b(?:topic|subject|theme)\b.*?(\w+)',
            r'\b(?:discuss|talk about|cover)\b.*?(\w+)',
            r'\b(?:about|regarding|concerning)\b.*?(\w+)'
        ]
        
        for pattern in topic_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            topics.extend(matches)
        
        return list(set(topics))[:10]  # Return top 10 unique topics
    
    def _extract_concepts(self, text: str) -> List[str]:
        """Extract key concepts from text"""
        concepts = []
        
        # Look for concept indicators
        concept_patterns = [
            r'\b(?:concept|idea|principle)\b.*?(\w+)',
            r'\b(?:theory|framework|model)\b.*?(\w+)',
            r'\b(?:method|approach|technique)\b.*?(\w+)'
        ]
        
        for pattern in concept_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            concepts.extend(matches)
        
        return list(set(concepts))[:10]
    
    def _extract_facts(self, text: str) -> List[str]:
        """Extract factual information from text"""
        facts = []
        
        # Look for fact indicators
        fact_patterns = [
            r'\b(?:fact|statistic|data|number)\b.*?(\d+[\w\s]+)',
            r'\b(?:research|study|survey)\b.*?(\w+)',
            r'\b(?:percent|percentage|rate)\b.*?(\d+%)'
        ]
        
        for pattern in fact_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            facts.extend(matches)
        
        return list(set(facts))[:10]
    
    def _extract_applications(self, text: str) -> List[str]:
        """Extract practical applications from text"""
        applications = []
        
        # Look for application indicators
        application_patterns = [
            r'\b(?:apply|use|implement)\b.*?(\w+)',
            r'\b(?:example|case study|real world)\b.*?(\w+)',
            r'\b(?:benefit|advantage|value)\b.*?(\w+)'
        ]
        
        for pattern in application_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            applications.extend(matches)
        
        return list(set(applications))[:10]

class InsightExtractor:
    """Extract meaningful insights from analyzed content"""
    
    def __init__(self):
        self.multi_llm_router = MultiLLMRouter()
    
    async def extract_insights(self, transcript: List[TranscriptSegment], 
                             analysis: Dict[str, Any], 
                             learning_goals: List[str] = None) -> List[LearningInsight]:
        """Extract meaningful insights from content analysis"""
        try:
            insights = []
            
            # Generate insights using AI
            insight_task = {
                'description': 'Extract meaningful insights from content',
                'prompt': f"""
                Based on this content analysis, extract meaningful insights:
                
                Analysis: {json.dumps(analysis, indent=2)}
                Learning Goals: {learning_goals or 'General learning'}
                
                Please provide insights that are:
                - Actionable and practical
                - Relevant to the learning goals
                - Supported by the content
                - Novel and insightful
                
                Format each insight with:
                - Type (concept, fact, procedure, example)
                - Content (the actual insight)
                - Confidence (0.0-1.0)
                - Relevance score (0.0-1.0)
                - Keywords
                """,
                'max_tokens': 2000
            }
            
            result = self.multi_llm_router.route_task(insight_task)
            
            # Parse insights from AI response
            insights_text = result.get('content', '')
            parsed_insights = self._parse_insights_from_text(insights_text)
            
            return parsed_insights
            
        except Exception as e:
            logger.error(f"Insight extraction failed: {str(e)}")
            return []
    
    def _parse_insights_from_text(self, text: str) -> List[LearningInsight]:
        """Parse insights from AI-generated text"""
        insights = []
        
        # Simple parsing (could be enhanced with proper NLP)
        insight_blocks = re.findall(r'Insight \d+:(.*?)(?=Insight \d+|$)', text, re.DOTALL)
        
        for i, block in enumerate(insight_blocks):
            try:
                # Extract components from block
                insight_type = self._extract_field(block, 'Type:', 'concept')
                content = self._extract_field(block, 'Content:', '')
                confidence = float(self._extract_field(block, 'Confidence:', '0.5'))
                relevance = float(self._extract_field(block, 'Relevance:', '0.5'))
                keywords = self._extract_keywords(block)
                
                if content and confidence >= 0.5:
                    insights.append(LearningInsight(
                        type=insight_type,
                        content=content,
                        confidence=confidence,
                        relevance_score=relevance,
                        keywords=keywords
                    ))
            except Exception:
                continue
        
        return insights
    
    def _extract_field(self, text: str, field_name: str, default: str) -> str:
        """Extract a field from text"""
        pattern = rf'{field_name}\s*([^:\n]+)'
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else default
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        # Simple keyword extraction
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [word for word in words if len(word) > 3]
        return list(set(keywords))[:10]

class KnowledgeIntegrator:
    """Integrate learned knowledge into the system"""
    
    def __init__(self):
        self.multi_llm_router = MultiLLMRouter()
        self.knowledge_graph = nx.DiGraph()
        self.integration_history = []
    
    async def integrate_knowledge(self, video_id: str, insights: List[LearningInsight], 
                                metadata: VideoMetadata, 
                                learning_goals: List[str] = None) -> List[KnowledgeIntegration]:
        """Integrate learned insights into the system"""
        try:
            integrations = []
            
            for insight in insights:
                # Generate integration suggestions
                integration_task = {
                    'description': 'Generate knowledge integration suggestions',
                    'prompt': f"""
                    How can this insight be integrated into a business automation system?
                    
                    Video ID: {video_id}
                    Insight: {insight.content}
                    Type: {insight.type}
                    Confidence: {insight.confidence}
                    Relevance: {insight.relevance_score}
                    Keywords: {insight.keywords}
                    Learning Goals: {learning_goals or 'General learning'}
                    
                    Please suggest specific ways to integrate this knowledge:
                    1. Content generation opportunities
                    2. System improvements
                    3. New feature ideas
                    4. Process optimizations
                    
                    For each suggestion, provide:
                    - Integration type
                    - Content/description
                    - Implementation priority
                    - Estimated effort
                    - Potential impact
                    """,
                    'max_tokens': 1500
                }
                
                result = self.multi_llm_router.route_task(integration_task)
                
                # Parse integration suggestions
                integration_suggestions = self._parse_integration_suggestions(
                    result.get('content', ''), video_id, insight
                )
                
                integrations.extend(integration_suggestions)
            
            # Build knowledge graph
            self._build_knowledge_graph(video_id, insights, integrations)
            
            # Store integration history
            self.integration_history.append({
                'video_id': video_id,
                'insights_count': len(insights),
                'integrations_count': len(integrations),
                'timestamp': datetime.utcnow().isoformat()
            })
            
            logger.info(f"✅ Knowledge integration complete: {len(integrations)} integrations created")
            return integrations
            
        except Exception as e:
            logger.error(f"Knowledge integration failed: {str(e)}")
            return []
    
    def _parse_integration_suggestions(self, text: str, video_id: str, insight: LearningInsight) -> List[KnowledgeIntegration]:
        """Parse integration suggestions from AI response"""
        integrations = []
        
        # Simple parsing (could be enhanced with proper NLP)
        suggestion_blocks = re.findall(r'Suggestion \d+:(.*?)(?=Suggestion \d+|$)', text, re.DOTALL)
        
        for i, block in enumerate(suggestion_blocks):
            try:
                integration_type = self._extract_field(block, 'Integration Type:', 'content_generation')
                content = self._extract_field(block, 'Content:', '')
                priority = self._extract_field(block, 'Priority:', 'medium')
                effort = self._extract_field(block, 'Effort:', 'medium')
                impact = self._extract_field(block, 'Impact:', 'medium')
                
                if content:
                    integrations.append(KnowledgeIntegration(
                        source_video=video_id,
                        integration_type=integration_type,
                        content=content,
                        implementation_priority=priority,
                        estimated_effort=effort,
                        potential_impact=impact
                    ))
            except Exception:
                continue
        
        return integrations
    
    def _extract_field(self, text: str, field_name: str, default: str) -> str:
        """Extract a field from text"""
        pattern = rf'{field_name}\s*([^:\n]+)'
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else default
    
    def _build_knowledge_graph(self, video_id: str, insights: List[LearningInsight], 
                             integrations: List[KnowledgeIntegration]):
        """Build knowledge graph from insights and integrations"""
        # Add video node
        self.knowledge_graph.add_node(video_id, type='video', title=f"Video: {video_id}")
        
        # Add insight nodes and edges
        for insight in insights:
            insight_id = insight.insight_id
            self.knowledge_graph.add_node(insight_id, type='insight', content=insight.content)
            self.knowledge_graph.add_edge(video_id, insight_id, relationship='contains_insight')
            
            # Add keyword nodes
            for keyword in insight.keywords:
                keyword_id = f"keyword_{keyword}"
                self.knowledge_graph.add_node(keyword_id, type='keyword', keyword=keyword)
                self.knowledge_graph.add_edge(insight_id, keyword_id, relationship='has_keyword')
        
        # Add integration nodes and edges
        for integration in integrations:
            integration_id = integration.integration_id
            self.knowledge_graph.add_node(integration_id, type='integration', content=integration.content)
            
            # Connect to relevant insights
            for insight in insights:
                if any(keyword in integration.content.lower() for keyword in insight.keywords):
                    self.knowledge_graph.add_edge(insight.insight_id, integration_id, relationship='enables_integration')

class AdvancedWebsiteScraper:
    """Advanced website scraper with semantic analysis"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.semantic_analyzer = SemanticAnalyzer()
    
    async def scrape_and_analyze(self, url: str, content_types: List[str] = None) -> Dict[str, Any]:
        """Scrape website and perform semantic analysis"""
        try:
            logger.info(f"🌐 Advanced Scraper: Analyzing {url}")
            
            # Fetch content
            response = await asyncio.to_thread(self.session.get, url, timeout=30)
            response.raise_for_status()
            
            # Parse content
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract content
            content = self._extract_content(soup)
            
            # Perform semantic analysis
            analysis = await self.semantic_analyzer.analyze_content(content, url)
            
            # Categorize content
            categories = await self._categorize_content(content, analysis)
            
            # Extract actionable insights
            insights = await self._extract_insights(content, analysis)
            
            result = {
                'url': url,
                'content': content,
                'analysis': analysis,
                'categories': categories,
                'insights': insights,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info(f"✅ Website scraping complete: {len(content.get('text', ''))} characters analyzed")
            return result
            
        except Exception as e:
            logger.error(f"❌ Website scraping failed: {str(e)}")
            return {'error': str(e), 'url': url}
    
    def _extract_content(self, soup) -> Dict[str, Any]:
        """Extract different types of content from HTML"""
        content = {
            'title': soup.title.string if soup.title else '',
            'text': '',
            'links': [],
            'images': [],
            'headings': [],
            'metadata': {}
        }
        
        # Extract text content
        for element in soup.find_all(['p', 'div', 'span']):
            if element.get_text().strip():
                content['text'] += element.get_text().strip() + ' '
        
        # Extract links
        for link in soup.find_all('a', href=True):
            content['links'].append({
                'url': link['href'],
                'text': link.get_text().strip(),
                'title': link.get('title', '')
            })
        
        # Extract images
        for img in soup.find_all('img'):
            content['images'].append({
                'src': img.get('src', ''),
                'alt': img.get('alt', ''),
                'title': img.get('title', '')
            })
        
        # Extract headings
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            content['headings'].append({
                'level': heading.name,
                'text': heading.get_text().strip()
            })
        
        # Extract metadata
        for meta in soup.find_all('meta'):
            if meta.get('name'):
                content['metadata'][meta['name']] = meta.get('content', '')
        
        return content
    
    async def _categorize_content(self, content: Dict[str, Any], analysis: Dict[str, Any]) -> List[str]:
        """Categorize content based on analysis"""
        categories = []
        
        # Analyze content for categories
        text = content.get('text', '').lower()
        
        category_keywords = {
            'technology': ['ai', 'machine learning', 'automation', 'software', 'programming'],
            'business': ['business', 'startup', 'entrepreneur', 'marketing', 'sales'],
            'education': ['learn', 'tutorial', 'guide', 'course', 'education'],
            'health': ['health', 'medical', 'fitness', 'wellness', 'medicine'],
            'finance': ['finance', 'money', 'investment', 'crypto', 'stock'],
            'lifestyle': ['lifestyle', 'travel', 'food', 'fashion', 'entertainment']
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in text for keyword in keywords):
                categories.append(category)
        
        return categories
    
    async def _extract_insights(self, content: Dict[str, Any], analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract actionable insights from content"""
        insights = []
        
        # Use AI to extract insights
        prompt = f"""
        Extract actionable insights from this website content:
        
        Content: {content.get('text', '')[:2000]}...
        Analysis: {json.dumps(analysis, indent=2)}
        
        Please provide insights that are:
        - Actionable and practical
        - Relevant to business automation
        - Supported by the content
        - Novel and valuable
        """
        
        ai_task = {
            'description': 'Extract insights from website content',
            'prompt': prompt,
            'max_tokens': 1000
        }
        
        result = self.semantic_analyzer.multi_llm_router.route_task(ai_task)
        
        # Parse insights
        insights_text = result.get('content', '')
        parsed_insights = self._parse_insights_from_text(insights_text)
        
        return parsed_insights
    
    def _parse_insights_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Parse insights from AI response"""
        insights = []
        
        # Simple parsing
        insight_blocks = re.findall(r'Insight \d+:(.*?)(?=Insight \d+|$)', text, re.DOTALL)
        
        for block in insight_blocks:
            try:
                content = self._extract_field(block, 'Content:', '')
                if content:
                    insights.append({
                        'content': content,
                        'type': self._extract_field(block, 'Type:', 'general'),
                        'confidence': float(self._extract_field(block, 'Confidence:', '0.5'))
                    })
            except Exception:
                continue
        
        return insights
    
    def _extract_field(self, text: str, field_name: str, default: str) -> str:
        """Extract a field from text"""
        pattern = rf'{field_name}\s*([^:\n]+)'
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else default

class SemanticAnalyzer:
    """Semantic analysis for content understanding"""
    
    def __init__(self):
        self.multi_llm_router = MultiLLMRouter()
        self.embeddings_model = None
        self._init_embeddings_model()
    
    def _init_embeddings_model(self):
        """Initialize embeddings model"""
        try:
            self.embeddings_model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            logger.warning(f"Failed to load embeddings model: {str(e)}")
    
    async def analyze_content(self, content: Dict[str, Any], url: str) -> Dict[str, Any]:
        """Perform semantic analysis on content"""
        try:
            text = content.get('text', '')
            
            # Analyze content using AI
            analysis_task = {
                'description': 'Perform semantic analysis on content',
                'prompt': f"""
                Perform semantic analysis on this content:
                
                URL: {url}
                Content: {text[:3000]}...
                
                Please analyze:
                1. Main topics and themes
                2. Sentiment and tone
                3. Key entities and concepts
                4. Content quality and structure
                5. Potential applications
                """,
                'max_tokens': 1500
            }
            
            result = self.multi_llm_router.route_task(analysis_task)
            
            return {
                'semantic_analysis': result.get('content', ''),
                'topics': self._extract_topics(text),
                'sentiment': self._analyze_sentiment(text),
                'entities': self._extract_entities(text),
                'quality_score': self._calculate_quality_score(text)
            }
            
        except Exception as e:
            logger.error(f"Semantic analysis failed: {str(e)}")
            return {'error': str(e)}
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract topics using simple keyword analysis"""
        topics = []
        
        topic_keywords = [
            'ai', 'machine learning', 'automation', 'business', 'technology',
            'health', 'finance', 'education', 'marketing', 'startup'
        ]
        
        text_lower = text.lower()
        for keyword in topic_keywords:
            if keyword in text_lower:
                topics.append(keyword)
        
        return list(set(topics))
    
    def _analyze_sentiment(self, text: str) -> str:
        """Analyze sentiment of text"""
        # Simple sentiment analysis (could be enhanced with proper NLP)
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'disappointing']
        
        positive_count = sum(1 for word in positive_words if word in text.lower())
        negative_count = sum(1 for word in negative_words if word in text.lower())
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract named entities"""
        # Simple entity extraction (could be enhanced with NLP)
        entities = []
        
        # Look for potential entities
        entity_patterns = [
            r'\b[A-Z][a-zA-Z]+\s+[A-Z][a-zA-Z]+\b',  # Person names
            r'\b[A-Z][a-zA-Z]+\b',  # Company names
            r'\b[A-Z]{2,}\b'  # Acronyms
        ]
        
        for pattern in entity_patterns:
            matches = re.findall(pattern, text)
            entities.extend(matches)
        
        return list(set(entities))[:10]
    
    def _calculate_quality_score(self, text: str) -> float:
        """Calculate content quality score"""
        if not text:
            return 0.0
        
        # Simple quality metrics
        length_score = min(len(text) / 1000, 1.0)  # Length up to 1000 chars
        word_count = len(text.split())
        readability_score = 1.0 if word_count > 100 else 0.5  # Minimum word count
        
        # Overall quality
        quality_score = (length_score + readability_score) / 2
        return quality_score

# Global instances
youtube_learning_system = YouTubeLearningSystem()
advanced_scraper = AdvancedWebsiteScraper()

async def main():
    """Test the YouTube learning system"""
    logger.info("🎥 Testing YouTube Learning System")
    
    # Test with a sample video
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll (example)
    learning_goals = ["AI automation", "business optimization", "content generation"]
    
    result = await youtube_learning_system.learn_from_video(test_url, learning_goals)
    print(f"Learning complete: {result.get('transcript_summary', 'No summary')}")

if __name__ == "__main__":
    asyncio.run(main())