#!/usr/bin/env python3
"""
CHATTY Continuous Learning System
Advanced memory management, knowledge retention, and adaptive learning capabilities
"""

import os
import json
import time
import uuid
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, deque
import threading
import numpy as np

import redis
from sentence_transformers import SentenceTransformer
import networkx as nx
from sklearn.cluster import DBSCAN
from sqlalchemy import and_, or_, func

from server import db, Agent, Task, Execution, logger

class MemorySystem:
    """Advanced memory management with multiple storage layers"""

    def __init__(self):
        self.redis_client = redis.Redis.from_url(os.environ.get('REDIS_URL', 'redis://localhost:6379'))
        self.embedding_model = None
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        except:
            logger.warning("Sentence transformer not available, embeddings disabled")

        # Memory layers
        self.short_term_memory = deque(maxlen=1000)  # Recent events
        self.working_memory = {}  # Active context
        self.long_term_memory = {}  # Persistent knowledge
        self.episodic_memory = []  # Experience sequences

        # Knowledge graph for relationships
        self.knowledge_graph = nx.DiGraph()

        # Learning parameters
        self.learning_rate = 0.1
        self.forgetfulness_rate = 0.01
        self.consolidation_threshold = 0.7

        # Start background consolidation
        self.consolidation_thread = threading.Thread(target=self._consolidate_memories_loop, daemon=True)
        self.consolidation_thread.start()

    def store_experience(self, agent_id: str, experience: Dict[str, Any]) -> str:
        """Store an agent experience with metadata"""
        experience_id = str(uuid.uuid4())

        # Enrich experience with metadata
        enriched_experience = {
            'id': experience_id,
            'agent_id': agent_id,
            'timestamp': datetime.utcnow().isoformat(),
            'type': experience.get('type', 'general'),
            'content': experience,
            'importance': self._calculate_importance(experience),
            'embedding': self._generate_embedding(experience) if self.embedding_model else None,
            'tags': experience.get('tags', []),
            'context': experience.get('context', {})
        }

        # Store in different memory layers
        self.short_term_memory.append(enriched_experience)

        # Store in Redis with TTL based on importance
        ttl = self._calculate_ttl(enriched_experience['importance'])
        self.redis_client.setex(
            f"experience:{experience_id}",
            ttl,
            json.dumps(enriched_experience)
        )

        # Add to working memory if highly relevant
        if enriched_experience['importance'] > 0.7:
            self.working_memory[experience_id] = enriched_experience

        # Update knowledge graph
        self._update_knowledge_graph(enriched_experience)

        logger.info("Experience stored", experience_id=experience_id, agent_id=agent_id, importance=enriched_experience['importance'])
        return experience_id

    def retrieve_relevant_memories(self, agent_id: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve memories relevant to a query using semantic search"""
        query_embedding = self._generate_embedding({'text': query}) if self.embedding_model else None

        candidates = []

        # Search short-term memory
        for experience in self.short_term_memory:
            if experience['agent_id'] == agent_id:
                similarity = self._calculate_similarity(query_embedding, experience.get('embedding'))
                if similarity > 0.3:
                    candidates.append((experience, similarity))

        # Search working memory
        for exp_id, experience in self.working_memory.items():
            if experience['agent_id'] == agent_id:
                similarity = self._calculate_similarity(query_embedding, experience.get('embedding'))
                if similarity > 0.3:
                    candidates.append((experience, similarity))

        # Search Redis for recent experiences
        redis_keys = self.redis_client.keys(f"experience:*")
        for key in redis_keys[:100]:  # Limit for performance
            try:
                data = self.redis_client.get(key)
                if data:
                    experience = json.loads(data)
                    if experience['agent_id'] == agent_id:
                        similarity = self._calculate_similarity(query_embedding, experience.get('embedding'))
                        if similarity > 0.3:
                            candidates.append((experience, similarity))
            except:
                continue

        # Sort by similarity and recency
        candidates.sort(key=lambda x: (x[1], x[0]['timestamp']), reverse=True)

        return [exp for exp, sim in candidates[:limit]]

    def consolidate_knowledge(self, agent_id: str) -> Dict[str, Any]:
        """Consolidate short-term memories into long-term knowledge"""
        # Get recent experiences for this agent
        recent_experiences = [
            exp for exp in self.short_term_memory
            if exp['agent_id'] == agent_id and exp['importance'] > self.consolidation_threshold
        ]

        if len(recent_experiences) < 3:
            return {'consolidated': 0, 'patterns': []}

        # Extract patterns using clustering
        patterns = self._extract_patterns(recent_experiences)

        # Store consolidated knowledge
        for pattern in patterns:
            pattern_id = str(uuid.uuid4())
            consolidated = {
                'id': pattern_id,
                'agent_id': agent_id,
                'type': 'consolidated_pattern',
                'pattern': pattern,
                'experiences': [exp['id'] for exp in pattern['experiences']],
                'created_at': datetime.utcnow().isoformat(),
                'confidence': pattern['confidence']
            }

            # Store in long-term memory
            self.long_term_memory[pattern_id] = consolidated

            # Store in database
            with db.session.begin():
                agent = db.session.query(Agent).get(agent_id)
                if agent:
                    if 'consolidated_knowledge' not in agent.memory:
                        agent.memory['consolidated_knowledge'] = []
                    agent.memory['consolidated_knowledge'].append(consolidated)
                    db.session.commit()

        return {
            'consolidated': len(patterns),
            'patterns': patterns
        }

    def learn_from_feedback(self, agent_id: str, experience_id: str, feedback: Dict[str, Any]):
        """Learn from user/agent feedback to improve performance"""
        # Retrieve the experience
        experience_data = self.redis_client.get(f"experience:{experience_id}")
        if not experience_data:
            return

        experience = json.loads(experience_data)

        # Update importance based on feedback
        feedback_score = feedback.get('score', 0.5)
        experience['importance'] = (experience['importance'] + feedback_score) / 2
        experience['feedback'] = feedback

        # Update in Redis
        ttl = self._calculate_ttl(experience['importance'])
        self.redis_client.setex(f"experience:{experience_id}", ttl, json.dumps(experience))

        # Update agent learning metrics
        with db.session.begin():
            agent = db.session.query(Agent).get(agent_id)
            if agent:
                if 'learning_metrics' not in agent.memory:
                    agent.memory['learning_metrics'] = {
                        'total_feedback': 0,
                        'positive_feedback': 0,
                        'average_score': 0,
                        'learning_trends': []
                    }

                metrics = agent.memory['learning_metrics']
                metrics['total_feedback'] += 1
                if feedback_score > 0.7:
                    metrics['positive_feedback'] += 1
                metrics['average_score'] = (metrics['average_score'] + feedback_score) / 2

                # Store learning trend
                metrics['learning_trends'].append({
                    'timestamp': datetime.utcnow().isoformat(),
                    'score': feedback_score,
                    'experience_type': experience['type']
                })

                # Keep only last 100 trends
                metrics['learning_trends'] = metrics['learning_trends'][-100:]

                agent.memory['learning_metrics'] = metrics
                db.session.commit()

        logger.info("Feedback processed", agent_id=agent_id, experience_id=experience_id, feedback_score=feedback_score)

    def predict_success_probability(self, agent_id: str, task_description: str) -> float:
        """Predict success probability for a task based on past experiences"""
        # Retrieve similar past experiences
        similar_experiences = self.retrieve_relevant_memories(agent_id, task_description, limit=20)

        if not similar_experiences:
            return 0.5  # Default confidence

        # Calculate success rate from similar experiences
        success_count = 0
        total_count = 0

        for exp in similar_experiences:
            if 'outcome' in exp['content']:
                total_count += 1
                if exp['content']['outcome'] == 'success':
                    success_count += 1

        if total_count == 0:
            return 0.5

        # Weight by recency and similarity
        success_rate = success_count / total_count

        # Adjust based on agent learning metrics
        with db.session.begin():
            agent = db.session.query(Agent).get(agent_id)
            if agent and 'learning_metrics' in agent.memory:
                avg_score = agent.memory['learning_metrics'].get('average_score', 0.5)
                success_rate = (success_rate + avg_score) / 2

        return min(success_rate, 0.95)  # Cap at 95%

    def _calculate_importance(self, experience: Dict[str, Any]) -> float:
        """Calculate importance score for an experience"""
        importance = 0.5  # Base importance

        # Increase for successful outcomes
        if experience.get('outcome') == 'success':
            importance += 0.2
        elif experience.get('outcome') == 'failure':
            importance += 0.1  # Learn from failures too

        # Increase for novel experiences
        if experience.get('type') == 'new_skill_learned':
            importance += 0.3

        # Increase for user feedback
        if 'user_feedback' in experience:
            feedback_score = experience['user_feedback'].get('rating', 0.5)
            importance += feedback_score * 0.2

        # Increase for complex tasks
        if experience.get('complexity', 'medium') == 'high':
            importance += 0.1

        return min(importance, 1.0)

    def _generate_embedding(self, content: Dict[str, Any]) -> Optional[List[float]]:
        """Generate semantic embedding for content"""
        if not self.embedding_model:
            return None

        # Extract text for embedding
        text_parts = []
        if 'text' in content:
            text_parts.append(content['text'])
        if 'description' in content:
            text_parts.append(content['description'])
        if 'tags' in content:
            text_parts.extend(content['tags'])

        text = ' '.join(text_parts)
        if not text.strip():
            return None

        try:
            embedding = self.embedding_model.encode(text, convert_to_list=True)
            return embedding
        except Exception as e:
            logger.warning("Embedding generation failed", error=str(e))
            return None

    def _calculate_similarity(self, embedding1: Optional[List[float]], embedding2: Optional[List[float]]) -> float:
        """Calculate cosine similarity between embeddings"""
        if not embedding1 or not embedding2:
            return 0.0

        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)

            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            return dot_product / (norm1 * norm2)
        except Exception as e:
            logger.warning("Similarity calculation failed", error=str(e))
            return 0.0

    def _calculate_ttl(self, importance: float) -> int:
        """Calculate TTL in seconds based on importance"""
        # Higher importance = longer retention
        base_ttl = 3600  # 1 hour
        max_ttl = 2592000  # 30 days

        ttl = base_ttl * (1 + importance * 10)  # Scale TTL with importance
        return min(int(ttl), max_ttl)

    def _update_knowledge_graph(self, experience: Dict[str, Any]):
        """Update the knowledge graph with new relationships"""
        exp_id = experience['id']

        # Add node for experience
        self.knowledge_graph.add_node(exp_id, **experience)

        # Find related experiences and add edges
        if experience.get('embedding'):
            for other_id, other_exp in self.working_memory.items():
                if other_id != exp_id and other_exp.get('embedding'):
                    similarity = self._calculate_similarity(
                        experience['embedding'],
                        other_exp['embedding']
                    )
                    if similarity > 0.7:  # Strong relationship
                        self.knowledge_graph.add_edge(exp_id, other_id, weight=similarity)

    def _extract_patterns(self, experiences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract patterns from experiences using clustering"""
        if not experiences or not self.embedding_model:
            return []

        # Prepare embeddings for clustering
        embeddings = []
        valid_experiences = []

        for exp in experiences:
            if exp.get('embedding'):
                embeddings.append(exp['embedding'])
                valid_experiences.append(exp)

        if len(embeddings) < 3:
            return []

        # Perform clustering
        embeddings_array = np.array(embeddings)
        clustering = DBSCAN(eps=0.5, min_samples=2).fit(embeddings_array)

        # Group experiences by cluster
        clusters = defaultdict(list)
        for i, label in enumerate(clustering.labels_):
            if label != -1:  # Ignore noise
                clusters[label].append(valid_experiences[i])

        # Extract patterns from clusters
        patterns = []
        for cluster_exps in clusters.values():
            if len(cluster_exps) >= 2:
                # Calculate common characteristics
                types = [exp['type'] for exp in cluster_exps]
                outcomes = [exp['content'].get('outcome') for exp in cluster_exps]

                pattern = {
                    'experiences': cluster_exps,
                    'common_type': max(set(types), key=types.count) if types else 'mixed',
                    'success_rate': outcomes.count('success') / len(outcomes) if outcomes else 0,
                    'avg_importance': sum(exp['importance'] for exp in cluster_exps) / len(cluster_exps),
                    'confidence': len(cluster_exps) / len(experiences),
                    'description': self._describe_pattern(cluster_exps)
                }
                patterns.append(pattern)

        return patterns

    def _describe_pattern(self, experiences: List[Dict[str, Any]]) -> str:
        """Generate a description for a pattern"""
        if not experiences:
            return "Empty pattern"

        types = [exp['type'] for exp in experiences]
        most_common_type = max(set(types), key=types.count)

        outcomes = [exp['content'].get('outcome', 'unknown') for exp in experiences]
        success_rate = outcomes.count('success') / len(outcomes)

        return f"Pattern of {len(experiences)} {most_common_type} experiences with {success_rate:.1%} success rate"

    def _consolidate_memories_loop(self):
        """Background thread for memory consolidation"""
        while True:
            try:
                # Get all active agents
                with db.session.begin():
                    agents = db.session.query(Agent).filter(Agent.status == 'active').all()

                for agent in agents:
                    self.consolidate_knowledge(agent.id)

                # Sleep for consolidation interval
                time.sleep(3600)  # Consolidate every hour

            except Exception as e:
                logger.error("Memory consolidation failed", error=str(e))
                time.sleep(300)  # Wait 5 minutes on error

class AdaptiveLearningSystem:
    """System for adaptive learning and behavior optimization"""

    def __init__(self, memory_system: MemorySystem):
        self.memory_system = memory_system
        self.performance_history = defaultdict(list)
        self.learning_strategies = {}
        self.adaptation_rules = self._load_adaptation_rules()

    def adapt_agent_behavior(self, agent_id: str, task_result: Dict[str, Any]):
        """Adapt agent behavior based on task performance"""
        # Store the experience
        experience_id = self.memory_system.store_experience(agent_id, {
            'type': 'task_execution',
            'content': task_result,
            'outcome': task_result.get('success', False) and 'success' or 'failure',
            'tags': ['adaptation', task_result.get('task_type', 'general')]
        })

        # Update performance history
        self.performance_history[agent_id].append({
            'timestamp': datetime.utcnow(),
            'task_type': task_result.get('task_type'),
            'success': task_result.get('success', False),
            'duration': task_result.get('duration', 0),
            'experience_id': experience_id
        })

        # Keep only recent history
        self.performance_history[agent_id] = self.performance_history[agent_id][-100:]

        # Apply adaptation rules
        adaptations = self._apply_adaptation_rules(agent_id, task_result)

        # Update agent configuration if needed
        if adaptations:
            self._update_agent_config(agent_id, adaptations)

        return adaptations

    def optimize_task_assignment(self, task: Dict[str, Any], available_agents: List[str]) -> str:
        """Optimize task assignment based on agent performance history"""
        if not available_agents:
            return available_agents[0] if available_agents else None

        best_agent = None
        best_score = -1

        for agent_id in available_agents:
            score = self._calculate_agent_fitness(agent_id, task)

            if score > best_score:
                best_score = score
                best_agent = agent_id

        return best_agent

    def generate_learning_recommendations(self, agent_id: str) -> List[Dict[str, Any]]:
        """Generate learning recommendations for an agent"""
        recommendations = []

        # Analyze performance history
        history = self.performance_history.get(agent_id, [])
        if len(history) < 5:
            return recommendations

        # Identify weak areas
        task_types = defaultdict(list)
        for entry in history[-20:]:  # Last 20 tasks
            task_types[entry['task_type']].append(entry['success'])

        weak_areas = []
        for task_type, successes in task_types.items():
            success_rate = sum(successes) / len(successes)
            if success_rate < 0.7 and len(successes) >= 3:
                weak_areas.append({
                    'task_type': task_type,
                    'success_rate': success_rate,
                    'sample_size': len(successes)
                })

        # Generate recommendations
        for weak_area in weak_areas:
            recommendations.append({
                'type': 'skill_improvement',
                'area': weak_area['task_type'],
                'current_performance': weak_area['success_rate'],
                'recommendation': f"Focus on improving {weak_area['task_type']} skills",
                'suggested_actions': [
                    f"Review successful {weak_area['task_type']} executions",
                    f"Study best practices for {weak_area['task_type']}",
                    f"Practice with similar tasks under supervision"
                ]
            })

        # Check for learning opportunities
        if len(history) >= 10:
            recent_success_rate = sum(1 for h in history[-10:] if h['success']) / 10
            if recent_success_rate > 0.8:
                recommendations.append({
                    'type': 'expansion',
                    'recommendation': "Consider taking on more complex tasks",
                    'reason': "Agent showing strong recent performance"
                })

        return recommendations

    def _load_adaptation_rules(self) -> List[Dict[str, Any]]:
        """Load adaptation rules for behavior optimization"""
        return [
            {
                'condition': lambda result: result.get('success') == False and 'timeout' in str(result.get('error', '')),
                'adaptation': {'increase_timeout': True, 'max_timeout': 300},
                'description': 'Increase timeout for timeout errors'
            },
            {
                'condition': lambda result: result.get('success') == False and 'memory' in str(result.get('error', '')),
                'adaptation': {'reduce_concurrency': True},
                'description': 'Reduce concurrency for memory issues'
            },
            {
                'condition': lambda result: result.get('duration', 0) > 300,  # 5 minutes
                'adaptation': {'optimize_performance': True},
                'description': 'Optimize for long-running tasks'
            },
            {
                'condition': lambda result: result.get('retry_count', 0) > 2,
                'adaptation': {'implement_retry_logic': True},
                'description': 'Improve retry logic for failing tasks'
            }
        ]

    def _apply_adaptation_rules(self, agent_id: str, task_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply adaptation rules based on task result"""
        adaptations = []

        for rule in self.adaptation_rules:
            if rule['condition'](task_result):
                adaptations.append({
                    'rule': rule['description'],
                    'adaptation': rule['adaptation'],
                    'triggered_by': {
                        'success': task_result.get('success'),
                        'error': task_result.get('error'),
                        'duration': task_result.get('duration')
                    }
                })

        return adaptations

    def _update_agent_config(self, agent_id: str, adaptations: List[Dict[str, Any]]):
        """Update agent configuration based on adaptations"""
        with db.session.begin():
            agent = db.session.query(Agent).get(agent_id)
            if not agent:
                return

            config_updates = {}

            for adaptation in adaptations:
                adapt_config = adaptation['adaptation']

                if 'increase_timeout' in adapt_config:
                    current_timeout = agent.config.get('timeout', 60)
                    new_timeout = min(current_timeout * 1.5, adapt_config.get('max_timeout', 300))
                    config_updates['timeout'] = new_timeout

                if 'reduce_concurrency' in adapt_config:
                    current_concurrency = agent.config.get('max_concurrency', 5)
                    config_updates['max_concurrency'] = max(current_concurrency - 1, 1)

                if 'optimize_performance' in adapt_config:
                    config_updates['performance_mode'] = 'optimized'

                if 'implement_retry_logic' in adapt_config:
                    config_updates['retry_enabled'] = True
                    config_updates['max_retries'] = agent.config.get('max_retries', 3) + 1

            if config_updates:
                agent.config.update(config_updates)
                agent.updated_at = datetime.utcnow()

                logger.info("Agent configuration updated", agent_id=agent_id, updates=config_updates)
                db.session.commit()

    def _calculate_agent_fitness(self, agent_id: str, task: Dict[str, Any]) -> float:
        """Calculate how well an agent fits a task"""
        base_score = 0.5

        # Check capability match
        task_type = task.get('task_type', 'general')
        with db.session.begin():
            agent = db.session.query(Agent).get(agent_id)
            if agent and task_type in agent.capabilities:
                base_score += 0.3

        # Check performance history
        history = self.performance_history.get(agent_id, [])
        if history:
            # Recent performance for this task type
            recent_tasks = [h for h in history[-10:] if h['task_type'] == task_type]
            if recent_tasks:
                success_rate = sum(1 for h in recent_tasks if h['success']) / len(recent_tasks)
                base_score += (success_rate - 0.5) * 0.4  # Scale around 0.5

        # Check current workload (simplified)
        # In production, this would check active tasks

        return max(0.0, min(1.0, base_score))

# Global instances
memory_system = MemorySystem()
adaptive_learning = AdaptiveLearningSystem(memory_system)
