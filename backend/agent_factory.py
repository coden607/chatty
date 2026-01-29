#!/usr/bin/env python3
"""
CHATTY Advanced Agent Factory
Dynamic agent creation with capability discovery, specialization, and intelligent configuration
"""

import os
import re
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

import requests
from sentence_transformers import SentenceTransformer
import networkx as nx
from sklearn.cluster import KMeans
import numpy as np

from server import db, Agent, logger
from youtube_agent import tool_downloader

class AgentCapabilityAnalyzer:
    """Analyzes and discovers agent capabilities from natural language descriptions"""

    def __init__(self):
        self.embeddings_model = None
        try:
            self.embeddings_model = SentenceTransformer('all-MiniLM-L6-v2')
        except:
            logger.warning("Sentence transformer not available for capability analysis")

        # Predefined capability templates
        self.capability_templates = self._load_capability_templates()

        # Domain expertise patterns
        self.domain_patterns = self._load_domain_patterns()

    def _load_capability_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load predefined capability templates"""
        return {
            'voice_assistant': {
                'capabilities': ['voice_interaction', 'natural_language_processing', 'home_automation'],
                'tools': ['speech_recognition', 'text_to_speech', 'home_control_api'],
                'config': {
                    'voice_engine': 'default',
                    'wake_word': 'hey chatty',
                    'response_timeout': 30
                },
                'autonomy_level': 'semi_autonomous',
                'description': 'Voice-controlled assistant for smart home and information tasks'
            },
            'workflow_automator': {
                'capabilities': ['process_automation', 'api_integration', 'data_processing'],
                'tools': ['workflow_engine', 'api_client', 'data_transformer'],
                'config': {
                    'max_concurrent_workflows': 5,
                    'timeout_minutes': 60,
                    'retry_attempts': 3
                },
                'autonomy_level': 'autonomous',
                'description': 'Business process automation and workflow management'
            },
            'creative_writer': {
                'capabilities': ['content_generation', 'text_analysis', 'creative_assistance'],
                'tools': ['language_model', 'text_analyzer', 'content_optimizer'],
                'config': {
                    'writing_style': 'professional',
                    'content_types': ['blog', 'article', 'social_media'],
                    'quality_threshold': 0.8
                },
                'autonomy_level': 'semi_autonomous',
                'description': 'Creative writing and content generation assistant'
            },
            'data_analyst': {
                'capabilities': ['data_analysis', 'visualization', 'statistical_modeling'],
                'tools': ['data_processor', 'chart_generator', 'statistical_analyzer'],
                'config': {
                    'supported_formats': ['csv', 'json', 'excel', 'database'],
                    'visualization_types': ['bar', 'line', 'pie', 'scatter'],
                    'confidence_interval': 0.95
                },
                'autonomy_level': 'semi_autonomous',
                'description': 'Data analysis and visualization specialist'
            },
            'research_assistant': {
                'capabilities': ['information_retrieval', 'source_verification', 'knowledge_synthesis'],
                'tools': ['web_search', 'document_analyzer', 'citation_manager'],
                'config': {
                    'search_depth': 3,
                    'reliability_threshold': 0.7,
                    'max_sources': 10
                },
                'autonomy_level': 'autonomous',
                'description': 'Research and information gathering specialist'
            },
            'code_developer': {
                'capabilities': ['code_generation', 'debugging', 'code_review'],
                'tools': ['code_generator', 'debugger', 'linter'],
                'config': {
                    'supported_languages': ['python', 'javascript', 'java', 'cpp'],
                    'code_style': 'pep8',
                    'testing_required': True
                },
                'autonomy_level': 'semi_autonomous',
                'description': 'Software development and code assistance'
            },
            'system_administrator': {
                'capabilities': ['system_monitoring', 'resource_management', 'security_monitoring'],
                'tools': ['system_monitor', 'resource_allocator', 'security_scanner'],
                'config': {
                    'monitoring_interval': 60,
                    'alert_thresholds': {'cpu': 80, 'memory': 85, 'disk': 90},
                    'auto_remediation': False
                },
                'autonomy_level': 'autonomous',
                'description': 'System administration and monitoring'
            }
        }

    def _load_domain_patterns(self) -> Dict[str, List[str]]:
        """Load domain-specific patterns for capability detection"""
        return {
            'voice': [
                r'\b(voice|speech|talk|say|listen|hear|call|dial)\b',
                r'\b(smart home|home automation|lights|thermostat|security)\b',
                r'\b(siri|alexa|google assistant|phone|mobile)\b'
            ],
            'workflow': [
                r'\b(workflow|process|automation|business|task)\b',
                r'\b(api|integration|webhook|trigger|action)\b',
                r'\b(schedule|calendar|reminder|notification)\b'
            ],
            'creative': [
                r'\b(write|content|blog|article|story|creative)\b',
                r'\b(marketing|social media|advertising|brand)\b',
                r'\b(edit|proofread|grammar|style)\b'
            ],
            'data': [
                r'\b(data|analytics|chart|graph|visualization)\b',
                r'\b(statistics|machine learning|ai|model)\b',
                r'\b(database|sql|query|report)\b'
            ],
            'research': [
                r'\b(research|study|investigate|explore|discover)\b',
                r'\b(information|knowledge|facts|sources|references)\b',
                r'\b(search|find|lookup|verify)\b'
            ],
            'code': [
                r'\b(code|program|develop|software|application)\b',
                r'\b(debug|fix|error|bug|test|deploy)\b',
                r'\b(python|javascript|java|cpp|web|mobile)\b'
            ],
            'system': [
                r'\b(system|server|infrastructure|cloud|deployment)\b',
                r'\b(monitor|alert|security|backup|performance)\b',
                r'\b(linux|windows|docker|kubernetes|aws)\b'
            ]
        }

    def analyze_description(self, description: str) -> Dict[str, Any]:
        """Analyze agent description and extract capabilities"""
        try:
            # Clean and normalize description
            description = description.lower().strip()

            # Calculate domain scores
            domain_scores = self._calculate_domain_scores(description)

            # Determine primary and secondary domains
            primary_domain = max(domain_scores.items(), key=lambda x: x[1])
            secondary_domains = sorted(
                [(d, s) for d, s in domain_scores.items() if d != primary_domain[0]],
                key=lambda x: x[1],
                reverse=True
            )[:2]

            # Generate agent configuration
            agent_config = self._generate_agent_config(
                primary_domain[0],
                [d for d, s in secondary_domains],
                description
            )

            # Enhance with AI analysis if available
            ai_enhancement = self._enhance_with_ai(description, agent_config)

            return {
                'primary_domain': primary_domain[0],
                'domain_scores': domain_scores,
                'secondary_domains': [d for d, s in secondary_domains],
                'capabilities': agent_config.get('capabilities', []),
                'tools': agent_config.get('tools', []),
                'config': agent_config.get('config', {}),
                'autonomy_level': agent_config.get('autonomy_level', 'supervised'),
                'complexity_score': self._calculate_complexity(description),
                'specialization_level': self._calculate_specialization(domain_scores),
                'ai_enhancement': ai_enhancement
            }

        except Exception as e:
            logger.error("Agent description analysis failed", error=str(e))
            return self._fallback_analysis(description)

    def _calculate_domain_scores(self, description: str) -> Dict[str, float]:
        """Calculate relevance scores for each domain"""
        scores = {}

        for domain, patterns in self.domain_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, description, re.IGNORECASE))
                score += matches

            # Normalize score
            scores[domain] = min(score / len(patterns), 1.0)

        return scores

    def _generate_agent_config(self, primary_domain: str, secondary_domains: List[str],
                             description: str) -> Dict[str, Any]:
        """Generate agent configuration based on domain analysis"""
        # Start with primary domain template
        if primary_domain in self.capability_templates:
            config = self.capability_templates[primary_domain].copy()
        else:
            config = self.capability_templates['voice_assistant'].copy()

        # Enhance with secondary domains
        for secondary_domain in secondary_domains:
            if secondary_domain in self.capability_templates:
                secondary_config = self.capability_templates[secondary_domain]

                # Merge capabilities (avoid duplicates)
                config['capabilities'].extend([
                    cap for cap in secondary_config['capabilities']
                    if cap not in config['capabilities']
                ])

                # Merge tools
                config['tools'].extend([
                    tool for tool in secondary_config['tools']
                    if tool not in config['tools']
                ])

                # Merge config (secondary overrides primary for conflicts)
                config['config'].update(secondary_config['config'])

        # Adjust autonomy based on description complexity
        if 'complex' in description or 'advanced' in description:
            config['autonomy_level'] = 'autonomous'
        elif 'simple' in description or 'basic' in description:
            config['autonomy_level'] = 'supervised'

        return config

    def _enhance_with_ai(self, description: str, current_config: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance agent configuration using AI analysis"""
        try:
            ollama_url = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')

            prompt = f"""
            Analyze this agent description and suggest enhancements:

            Description: {description}

            Current configuration:
            - Capabilities: {current_config.get('capabilities', [])}
            - Tools: {current_config.get('tools', [])}
            - Autonomy: {current_config.get('autonomy_level', 'supervised')}

            Suggest:
            1. Additional capabilities (max 3)
            2. Additional tools needed (max 3)
            3. Configuration improvements
            4. Autonomy level recommendation

            Return as JSON with keys: additional_capabilities, additional_tools, config_improvements, autonomy_recommendation
            """

            response = requests.post(f"{ollama_url}/api/generate", json={
                'model': 'llama2',
                'prompt': prompt,
                'format': 'json',
                'stream': False
            }, timeout=30)

            if response.status_code == 200:
                result = response.json()
                return {
                    'additional_capabilities': result.get('additional_capabilities', []),
                    'additional_tools': result.get('additional_tools', []),
                    'config_improvements': result.get('config_improvements', {}),
                    'autonomy_recommendation': result.get('autonomy_recommendation', current_config.get('autonomy_level'))
                }

        except Exception as e:
            logger.warning("AI enhancement failed", error=str(e))

        return {}

    def _calculate_complexity(self, description: str) -> float:
        """Calculate description complexity score"""
        words = description.split()
        sentences = re.split(r'[.!?]+', description)

        # Factors: length, vocabulary diversity, technical terms
        length_score = min(len(words) / 50, 1.0)
        sentence_score = min(len(sentences) / 5, 1.0)

        # Technical term detection
        technical_terms = [
            'api', 'database', 'algorithm', 'framework', 'library', 'protocol',
            'architecture', 'infrastructure', 'deployment', 'integration'
        ]
        tech_score = sum(1 for term in technical_terms if term in description.lower())
        tech_score = min(tech_score / 5, 1.0)

        return (length_score + sentence_score + tech_score) / 3

    def _calculate_specialization(self, domain_scores: Dict[str, float]) -> str:
        """Calculate specialization level based on domain focus"""
        max_score = max(domain_scores.values())

        if max_score > 0.8:
            return 'highly_specialized'
        elif max_score > 0.6:
            return 'moderately_specialized'
        elif max_score > 0.4:
            return 'generalist'
        else:
            return 'unspecialized'

    def _fallback_analysis(self, description: str) -> Dict[str, Any]:
        """Fallback analysis when main analysis fails"""
        return {
            'primary_domain': 'general',
            'domain_scores': {},
            'secondary_domains': [],
            'capabilities': ['general_assistance'],
            'tools': [],
            'config': {},
            'autonomy_level': 'supervised',
            'complexity_score': 0.5,
            'specialization_level': 'generalist',
            'ai_enhancement': {}
        }

class AgentSpecializer:
    """Specializes agents based on their intended use cases and performance history"""

    def __init__(self):
        self.specialization_patterns = self._load_specialization_patterns()

    def _load_specialization_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load specialization patterns for different use cases"""
        return {
            'customer_support': {
                'capabilities': ['customer_interaction', 'issue_resolution', 'knowledge_base_access'],
                'tools': ['ticketing_system', 'knowledge_search', 'sentiment_analyzer'],
                'config': {
                    'response_time_target': 60,  # seconds
                    'escalation_threshold': 0.3,  # low confidence
                    'max_conversation_turns': 10
                }
            },
            'content_moderation': {
                'capabilities': ['content_analysis', 'policy_enforcement', 'risk_assessment'],
                'tools': ['content_classifier', 'sentiment_analyzer', 'policy_checker'],
                'config': {
                    'confidence_threshold': 0.85,
                    'auto_action_enabled': False,
                    'human_review_queue': True
                }
            },
            'data_pipeline': {
                'capabilities': ['data_ingestion', 'transformation', 'validation'],
                'tools': ['etl_processor', 'data_validator', 'monitoring_system'],
                'config': {
                    'batch_size': 1000,
                    'error_tolerance': 0.05,
                    'retry_attempts': 3
                }
            }
        }

    def specialize_agent(self, agent_analysis: Dict[str, Any], use_case: Optional[str] = None) -> Dict[str, Any]:
        """Specialize agent based on analysis and use case"""
        specialized_config = agent_analysis.copy()

        # Apply use case specialization if specified
        if use_case and use_case in self.specialization_patterns:
            pattern = self.specialization_patterns[use_case]

            # Merge capabilities
            specialized_config['capabilities'].extend([
                cap for cap in pattern['capabilities']
                if cap not in specialized_config['capabilities']
            ])

            # Merge tools
            specialized_config['tools'].extend([
                tool for tool in pattern['tools']
                if tool not in specialized_config['tools']
            ])

            # Update config
            specialized_config['config'].update(pattern['config'])
            specialized_config['specialization'] = use_case

        # Apply performance-based specialization
        performance_specialization = self._apply_performance_specialization(specialized_config)
        specialized_config.update(performance_specialization)

        return specialized_config

    def _apply_performance_specialization(self, agent_config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply specialization based on expected performance characteristics"""
        enhancements = {}

        # High autonomy agents get more sophisticated tools
        if agent_config.get('autonomy_level') == 'autonomous':
            enhancements['advanced_tools'] = ['performance_monitor', 'auto_optimizer']
            enhancements['config'] = enhancements.get('config', {})
            enhancements['config']['self_learning_enabled'] = True

        # Complex agents get debugging capabilities
        if agent_config.get('complexity_score', 0) > 0.7:
            enhancements['capabilities'] = enhancements.get('capabilities', [])
            enhancements['capabilities'].append('self_diagnosis')

        return enhancements

class AgentFactory:
    """Main factory for creating specialized agents"""

    def __init__(self):
        self.analyzer = AgentCapabilityAnalyzer()
        self.specializer = AgentSpecializer()
        self.tool_discovery = tool_downloader

    def create_agent_from_description(self, description: str, user_id: str,
                                    specialization: Optional[str] = None) -> Dict[str, Any]:
        """Create a complete agent configuration from natural language description"""
        try:
            # Analyze the description
            analysis = self.analyzer.analyze_description(description)

            # Apply specialization
            specialized_config = self.specializer.specialize_agent(analysis, specialization)

            # Discover required tools
            required_tools = self._discover_required_tools(specialized_config)

            # Generate final agent configuration
            agent_config = self._generate_final_config(specialized_config, required_tools, description)

            # Create agent name if not specified
            if 'name' not in agent_config:
                agent_config['name'] = self._generate_agent_name(analysis, specialization)

            # Validate configuration
            validation_result = self._validate_agent_config(agent_config)
            agent_config['validation'] = validation_result

            logger.info("Agent configuration created",
                       primary_domain=analysis.get('primary_domain'),
                       capabilities=len(agent_config.get('capabilities', [])),
                       tools=len(agent_config.get('tools', [])))

            return agent_config

        except Exception as e:
            logger.error("Agent creation failed", error=str(e))
            return self._create_fallback_agent(description)

    def _discover_required_tools(self, agent_config: Dict[str, Any]) -> List[str]:
        """Discover tools required for the agent configuration"""
        required_tools = set(agent_config.get('tools', []))

        # Map capabilities to tools
        capability_tool_mapping = {
            'voice_interaction': ['speech_recognition', 'text_to_speech'],
            'data_analysis': ['pandas', 'numpy', 'matplotlib'],
            'web_development': ['node', 'react', 'vscode'],
            'machine_learning': ['tensorflow', 'scikit-learn'],
            'api_integration': ['requests', 'flask'],
            'database': ['postgresql', 'redis'],
            'containerization': ['docker', 'kubernetes']
        }

        for capability in agent_config.get('capabilities', []):
            if capability in capability_tool_mapping:
                required_tools.update(capability_tool_mapping[capability])

        # Filter to known tools
        known_tools = []
        for tool in required_tools:
            if tool in self.tool_discovery.tool_database:
                known_tools.append(tool)

        return known_tools

    def _generate_final_config(self, analysis: Dict[str, Any], tools: List[str],
                             description: str) -> Dict[str, Any]:
        """Generate the final agent configuration"""
        config = {
            'name': analysis.get('name', f"Agent-{uuid.uuid4().hex[:8]}"),
            'description': description,
            'capabilities': analysis.get('capabilities', []),
            'tools': tools,
            'config': analysis.get('config', {}),
            'autonomy_level': analysis.get('autonomy_level', 'supervised'),
            'metadata': {
                'primary_domain': analysis.get('primary_domain'),
                'complexity_score': analysis.get('complexity_score', 0),
                'specialization_level': analysis.get('specialization_level', 'generalist'),
                'created_at': datetime.utcnow().isoformat(),
                'version': '2.0'
            }
        }

        # Add AI enhancements
        ai_enhancement = analysis.get('ai_enhancement', {})
        if ai_enhancement:
            config['capabilities'].extend(ai_enhancement.get('additional_capabilities', []))
            config['tools'].extend(ai_enhancement.get('additional_tools', []))
            config['config'].update(ai_enhancement.get('config_improvements', {}))
            if ai_enhancement.get('autonomy_recommendation'):
                config['autonomy_level'] = ai_enhancement['autonomy_recommendation']

        # Remove duplicates
        config['capabilities'] = list(set(config['capabilities']))
        config['tools'] = list(set(config['tools']))

        return config

    def _generate_agent_name(self, analysis: Dict[str, Any], specialization: Optional[str]) -> str:
        """Generate a meaningful agent name"""
        primary_domain = analysis.get('primary_domain', 'general')

        # Domain-based prefixes
        prefixes = {
            'voice': 'Voice',
            'workflow': 'Workflow',
            'creative': 'Creative',
            'data': 'Data',
            'research': 'Research',
            'code': 'Code',
            'system': 'System'
        }

        prefix = prefixes.get(primary_domain, 'Agent')

        # Add specialization if provided
        if specialization:
            prefix = f"{specialization.title()} {prefix}"

        # Add uniqueness
        unique_id = uuid.uuid4().hex[:4]

        return f"{prefix}Agent-{unique_id}"

    def _validate_agent_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate agent configuration"""
        issues = []

        # Check required fields
        required_fields = ['name', 'capabilities', 'autonomy_level']
        for field in required_fields:
            if field not in config:
                issues.append(f"Missing required field: {field}")

        # Validate capabilities
        if 'capabilities' in config and not config['capabilities']:
            issues.append("Agent must have at least one capability")

        # Validate autonomy level
        valid_autonomy_levels = ['supervised', 'semi_autonomous', 'autonomous']
        if config.get('autonomy_level') not in valid_autonomy_levels:
            issues.append(f"Invalid autonomy level. Must be one of: {valid_autonomy_levels}")

        # Check tool availability
        available_tools = set(self.tool_discovery.tool_database.keys())
        for tool in config.get('tools', []):
            if tool not in available_tools:
                issues.append(f"Tool not available: {tool}")

        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': []
        }

    def _create_fallback_agent(self, description: str) -> Dict[str, Any]:
        """Create a basic fallback agent when creation fails"""
        return {
            'name': f"FallbackAgent-{uuid.uuid4().hex[:8]}",
            'description': description,
            'capabilities': ['general_assistance'],
            'tools': [],
            'config': {},
            'autonomy_level': 'supervised',
            'metadata': {
                'fallback': True,
                'error': 'Agent creation failed, using fallback configuration'
            },
            'validation': {
                'valid': True,
                'issues': [],
                'warnings': ['This is a fallback configuration']
            }
        }

# Global instance
agent_factory = AgentFactory()
