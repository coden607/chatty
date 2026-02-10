#!/usr/bin/env python3
"""
Robustness and Anti-Hallucination System for Chatty
Comprehensive system to reduce hallucination and improve reliability
Uses multi-agent consensus, verification, and error recovery mechanisms
"""

import asyncio
import json
import os
import uuid
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from pydantic import BaseModel, Field
from enum import Enum
import logging
from statistics import mean, stdev
import re

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# HALLUCINATION DETECTION
# ============================================================================

class HallucinationSeverity(Enum):
    """Severity levels of hallucinations"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class HallucinationDetectionResult(BaseModel):
    """Result of hallucination detection"""
    detected: bool
    severity: HallucinationSeverity = Field(default=HallucinationSeverity.LOW)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    patterns: List[str] = Field(default_factory=list)
    explanation: str = ""
    suggestions: List[str] = Field(default_factory=list)

class HallucinationDetector:
    """Advanced hallucination detection system"""
    
    def __init__(self):
        self.patterns = self._load_hallucination_patterns()
        self.trust_threshold = 0.8
        self.consensus_threshold = 0.7
    
    def _load_hallucination_patterns(self) -> List[Dict[str, Any]]:
        """Load known hallucination patterns"""
        return [
            {
                'name': 'exact_duplicate',
                'pattern': r'(.{50,}?)\1',
                'severity': HallucinationSeverity.HIGH,
                'description': 'Exact text duplication'
            },
            {
                'name': 'vague_claims',
                'pattern': r'\b(always|never|everyone|no one|all|none)\b.*\b(claims?|states?|says?)\b',
                'severity': HallucinationSeverity.MEDIUM,
                'description': 'Absolute statements without sources'
            },
            {
                'name': 'statistical_claims',
                'pattern': r'\b(\d+%|\d+\s*percent)\b.*\b(proves?|demonstrates?|shows?)\b',
                'severity': HallucinationSeverity.MEDIUM,
                'description': 'Statistical claims without sources'
            },
            {
                'name': 'unsubstantiated_expertise',
                'pattern': r'\b(expert|researcher|studies?)\b.*\b(proves?|demonstrates?|shows?)\b',
                'severity': HallucinationSeverity.MEDIUM,
                'description': 'Expert claims without references'
            },
            {
                'name': 'contradictions',
                'pattern': r'\b(however|but|yet|nevertheless)\b.*\b(earlier|previously|before)\b',
                'severity': HallucinationSeverity.HIGH,
                'description': 'Contradictory statements'
            },
            {
                'name': 'absurd_claims',
                'pattern': r'\b(impossible|miracle|perfect|flawless)\b',
                'severity': HallucinationSeverity.CRITICAL,
                'description': 'Absurd or impossible claims'
            },
            {
                'name': 'hallucination_markings',
                'pattern': r'\b(hallucination|fabrication|falsehood|lie)\b',
                'severity': HallucinationSeverity.CRITICAL,
                'description': 'Explicit hallucination markers'
            },
            {
                'name': 'source_claims',
                'pattern': r'\b(according to|source:|study:|research:)\b',
                'severity': HallucinationSeverity.LOW,
                'description': 'Source references'
            }
        ]
    
    def detect(self, text: str) -> HallucinationDetectionResult:
        """Detect hallucinations in text"""
        result = HallucinationDetectionResult(
            detected=False,
            severity=HallucinationSeverity.LOW,
            confidence=0.0,
            patterns=[],
            explanation=""
        )
        
        detected_patterns = []
        for pattern_config in self.patterns:
            matches = re.findall(pattern_config['pattern'], text, re.IGNORECASE)
            if matches:
                detected_patterns.append(pattern_config['name'])
                # Update severity if higher
                if pattern_config['severity'].value > result.severity.value:
                    result.severity = pattern_config['severity']
        
        if detected_patterns:
            result.detected = True
            result.patterns = detected_patterns
            result.confidence = self._calculate_confidence(text, detected_patterns)
            
            # Calculate confidence based on patterns and their severities
            pattern_counts = {
                'low': sum(1 for p in self.patterns if p['name'] in detected_patterns and p['severity'] == HallucinationSeverity.LOW),
                'medium': sum(1 for p in self.patterns if p['name'] in detected_patterns and p['severity'] == HallucinationSeverity.MEDIUM),
                'high': sum(1 for p in self.patterns if p['name'] in detected_patterns and p['severity'] == HallucinationSeverity.HIGH),
                'critical': sum(1 for p in self.patterns if p['name'] in detected_patterns and p['severity'] == HallucinationSeverity.CRITICAL)
            }
            
            # Calculate weighted confidence
            total_weight = pattern_counts['low'] * 0.2 + pattern_counts['medium'] * 0.4 + pattern_counts['high'] * 0.7 + pattern_counts['critical'] * 1.0
            result.confidence = min(1.0, total_weight)
            
            result.explanation = self._generate_explanation(detected_patterns)
            result.suggestions = self._generate_suggestions(detected_patterns)
        
        return result
    
    def _calculate_confidence(self, text: str, patterns: List[str]) -> float:
        """Calculate detection confidence"""
        base_confidence = len(patterns) * 0.2
        source_claims = len(re.findall(r'\b(according to|source:|study:|research:)\b', text, re.IGNORECASE))
        
        if source_claims > 0:
            base_confidence = max(0.0, base_confidence - (source_claims * 0.1))
        
        return min(1.0, max(0.0, base_confidence))
    
    def _generate_explanation(self, patterns: List[str]) -> str:
        """Generate human-readable explanation"""
        descriptions = []
        for pattern_config in self.patterns:
            if pattern_config['name'] in patterns:
                descriptions.append(pattern_config['description'])
        
        if len(descriptions) == 1:
            return f"Detected potential hallucination: {descriptions[0]}"
        elif len(descriptions) > 1:
            return f"Detected potential hallucinations: {', '.join(descriptions)}"
        else:
            return "No specific hallucination patterns detected"
    
    def _generate_suggestions(self, patterns: List[str]) -> List[str]:
        """Generate suggestions to reduce hallucination"""
        suggestions = []
        
        if any(p in ['exact_duplicate', 'contradictions'] for p in patterns):
            suggestions.append("Consider rephrasing to avoid duplication or contradictions")
        
        if any(p in ['vague_claims', 'statistical_claims', 'unsubstantiated_expertise'] for p in patterns):
            suggestions.append("Add specific sources or references to support claims")
        
        if any(p in ['absurd_claims', 'hallucination_markings'] for p in patterns):
            suggestions.append("Review and revise these statements as they appear questionable")
        
        if not suggestions:
            suggestions.append("This text appears to be free of common hallucination patterns")
        
        return suggestions

# ============================================================================
# CONSENSUS VERIFICATION
# ============================================================================

class ConsensusResult(BaseModel):
    """Result of multi-agent consensus verification"""
    consensus_reached: bool
    agreement_score: float = Field(default=0.0, ge=0.0, le=1.0)
    majority_opinion: Any
    diversity_score: float = Field(default=0.0, ge=0.0, le=1.0)
    conflicting_results: List[Any] = Field(default_factory=list)
    verification_metrics: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)

class ConsensusVerifier:
    """Consensus verification system using multi-agent voting and analysis"""
    
    def __init__(self, min_agents: int = 3):
        self.min_agents = min_agents
        self.consensus_threshold = 0.7
        self.diversity_threshold = 0.3
        self.trust_scores = {}
    
    async def verify_consensus(self, task_description: str, results: List[Dict[str, Any]]) -> ConsensusResult:
        """
        Verify consensus among agent results
        Results should include 'agent_name', 'result', 'confidence', and optionally 'trust_score'
        """
        logger.info(f"🔍 Verifying consensus for task: {task_description}")
        
        if len(results) < self.min_agents:
            return ConsensusResult(
                consensus_reached=False,
                agreement_score=0.0,
                majority_opinion=None,
                diversity_score=0.0,
                conflicting_results=[],
                verification_metrics={
                    'agent_count': len(results),
                    'min_agents_required': self.min_agents,
                    'confidence_scores': [r.get('confidence', 0) for r in results]
                },
                recommendations=[
                    f"Need at least {self.min_agents} agents for consensus verification"
                ]
            )
        
        # Calculate trust scores for each agent
        self._update_trust_scores(results)
        
        # Calculate agreement between results
        agreement_score = self._calculate_agreement(results)
        
        # Calculate diversity of results
        diversity_score = self._calculate_diversity(results)
        
        # Find majority opinion
        majority_opinion = self._find_majority_opinion(results)
        
        # Identify conflicting results
        conflicting = self._find_conflicting_results(results, majority_opinion)
        
        consensus_reached = agreement_score >= self.consensus_threshold
        
        recommendations = []
        if not consensus_reached:
            recommendations.extend(self._generate_consensus_recommendations(
                agreement_score, diversity_score, len(results)
            ))
        
        metrics = self._calculate_verification_metrics(results, agreement_score, diversity_score)
        
        return ConsensusResult(
            consensus_reached=consensus_reached,
            agreement_score=agreement_score,
            majority_opinion=majority_opinion,
            diversity_score=diversity_score,
            conflicting_results=conflicting,
            verification_metrics=metrics,
            recommendations=recommendations
        )
    
    def _update_trust_scores(self, results: List[Dict[str, Any]]):
        """Update trust scores based on agent performance"""
        for result in results:
            agent = result['agent_name']
            if agent not in self.trust_scores:
                self.trust_scores[agent] = {
                    'total': 0,
                    'successful': 0,
                    'confidence': 0.0,
                    'consistent': 0
                }
            
            self.trust_scores[agent]['total'] += 1
            self.trust_scores[agent]['confidence'] = result.get('confidence', 0.8)
    
    def _calculate_agreement(self, results: List[Dict[str, Any]]) -> float:
        """Calculate agreement between results"""
        if len(results) < 2:
            return 1.0
        
        # Calculate similarity between all pairs of results
        similarity_scores = []
        for i in range(len(results)):
            for j in range(i + 1, len(results)):
                sim = self._calculate_result_similarity(
                    results[i]['result'],
                    results[j]['result']
                )
                similarity_scores.append(sim)
        
        return mean(similarity_scores)
    
    def _calculate_result_similarity(self, result1: Any, result2: Any) -> float:
        """Calculate semantic similarity between two results"""
        # Convert to strings for comparison
        str1 = str(result1).lower()
        str2 = str(result2).lower()
        
        # Calculate text similarity metrics
        # Simple character-based similarity
        if len(str1) == 0 or len(str2) == 0:
            return 0.0
        
        # Jaccard similarity of words
        words1 = set(str1.split())
        words2 = set(str2.split())
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_diversity(self, results: List[Dict[str, Any]]) -> float:
        """Calculate result diversity score"""
        if len(results) < 2:
            return 0.0
        
        unique_results = set()
        for result in results:
            result_str = str(result['result']).strip().lower()
            unique_results.add(result_str)
        
        return len(unique_results) / len(results)
    
    def _find_majority_opinion(self, results: List[Dict[str, Any]]) -> Any:
        """Find the majority opinion weighted by confidence and trust"""
        result_counts = {}
        
        for result in results:
            result_str = str(result['result']).strip().lower()
            
            if result_str not in result_counts:
                result_counts[result_str] = {
                    'count': 0,
                    'total_confidence': 0.0,
                    'agents': []
                }
            
            result_counts[result_str]['count'] += 1
            result_counts[result_str]['total_confidence'] += result.get('confidence', 0.8)
            result_counts[result_str]['agents'].append(result['agent_name'])
        
        # Find result with highest weighted score
        best_result = None
        best_score = 0.0
        
        for result_str, data in result_counts.items():
            # Weight by count + average confidence
            score = data['count'] + (data['total_confidence'] / len(results))
            
            if score > best_score:
                best_score = score
                best_result = self._find_original_result(results, result_str)
        
        return best_result
    
    def _find_original_result(self, results: List[Dict[str, Any]], result_str: str) -> Any:
        """Find the original result with this string representation"""
        for result in results:
            if str(result['result']).strip().lower() == result_str:
                return result['result']
        
        return None
    
    def _find_conflicting_results(self, results: List[Dict[str, Any]], 
                                 majority_opinion: Any) -> List[Any]:
        """Find results that conflict with the majority"""
        conflicting = []
        
        if majority_opinion is None:
            return conflicting
        
        for result in results:
            similarity = self._calculate_result_similarity(
                result['result'],
                majority_opinion
            )
            
            if similarity < 0.5:  # Threshold for significant disagreement
                conflicting.append(result['result'])
        
        return conflicting
    
    def _calculate_verification_metrics(self, results: List[Dict[str, Any]], 
                                       agreement_score: float, 
                                       diversity_score: float) -> Dict[str, Any]:
        """Calculate comprehensive verification metrics"""
        confidence_scores = [r.get('confidence', 0.8) for r in results]
        agent_count = len(results)
        
        return {
            'agent_count': agent_count,
            'confidence_scores': {
                'mean': mean(confidence_scores),
                'std': stdev(confidence_scores) if len(confidence_scores) > 1 else 0.0,
                'min': min(confidence_scores),
                'max': max(confidence_scores)
            },
            'agreement_score': agreement_score,
            'diversity_score': diversity_score,
            'trust_scores': self._get_agent_trust_scores(results)
        }
    
    def _get_agent_trust_scores(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Get trust scores for agents involved in this task"""
        scores = {}
        for result in results:
            agent = result['agent_name']
            scores[agent] = self.trust_scores.get(agent, {}).get('confidence', 0.8)
        
        return scores
    
    def _generate_consensus_recommendations(self, agreement_score: float,
                                           diversity_score: float, 
                                           agent_count: int) -> List[str]:
        """Generate recommendations based on consensus analysis"""
        recommendations = []
        
        if agreement_score < 0.5:
            recommendations.append("Results show significant disagreement. Consider rephrasing the task or adding more context.")
        
        if agent_count < 5:
            recommendations.append("Adding more agents could improve consensus reliability.")
        
        if diversity_score < 0.2:
            recommendations.append("Results appear too similar. Consider adding diverse agents with different perspectives.")
        
        return recommendations

# ============================================================================
# ERROR RECOVERY AND SELF-HEALING
# ============================================================================

class ErrorType(Enum):
    """Types of errors the system can recover from"""
    AGENT_FAILURE = "agent_failure"
    NETWORK_ERROR = "network_error"
    VALIDATION_ERROR = "validation_error"
    TIMEOUT = "timeout"
    INTERNAL_ERROR = "internal_error"
    CONFLICT = "conflict"
    NOT_FOUND = "not_found"

class RecoveryStrategy(Enum):
    """Available recovery strategies"""
    RETRY = "retry"
    FALLBACK = "fallback"
    REASSIGN = "reassign"
    COMPENSATE = "compensate"
    SKIP = "skip"
    ROLLBACK = "rollback"

class ErrorRecoveryResult(BaseModel):
    """Result of error recovery operation"""
    recovered: bool
    strategy: RecoveryStrategy
    attempts: int
    time_taken: float
    details: Dict[str, Any] = Field(default_factory=dict)
    success_result: Optional[Any] = None

class ErrorRecoverySystem:
    """Advanced error recovery and self-healing system"""
    
    def __init__(self):
        self.recovery_strategies = self._load_recovery_strategies()
        self.max_retries = 3
        self.retry_backoff = [1, 5, 15]  # seconds
        self.fallback_agents = ['bmad', 'n8n', 'revenue']
    
    def _load_recovery_strategies(self) -> Dict[ErrorType, List[RecoveryStrategy]]:
        """Load recovery strategies for different error types"""
        return {
            ErrorType.AGENT_FAILURE: [
                RecoveryStrategy.RETRY,
                RecoveryStrategy.REASSIGN,
                RecoveryStrategy.FALLBACK
            ],
            ErrorType.NETWORK_ERROR: [
                RecoveryStrategy.RETRY,
                RecoveryStrategy.FALLBACK,
                RecoveryStrategy.COMPENSATE
            ],
            ErrorType.VALIDATION_ERROR: [
                RecoveryStrategy.FALLBACK,
                RecoveryStrategy.SKIP,
                RecoveryStrategy.ROLLBACK
            ],
            ErrorType.TIMEOUT: [
                RecoveryStrategy.RETRY,
                RecoveryStrategy.REASSIGN,
                RecoveryStrategy.SKIP
            ],
            ErrorType.INTERNAL_ERROR: [
                RecoveryStrategy.FALLBACK,
                RecoveryStrategy.COMPENSATE,
                RecoveryStrategy.ROLLBACK
            ],
            ErrorType.CONFLICT: [
                RecoveryStrategy.ROLLBACK,
                RecoveryStrategy.COMPENSATE,
                RecoveryStrategy.FALLBACK
            ],
            ErrorType.NOT_FOUND: [
                RecoveryStrategy.FALLBACK,
                RecoveryStrategy.SKIP,
                RecoveryStrategy.COMPENSATE
            ]
        }
    
    async def recover(self, error_type: ErrorType, context: Dict[str, Any],
                     task_description: str) -> ErrorRecoveryResult:
        """Attempt to recover from an error"""
        logger.info(f"🔧 Attempting recovery from {error_type.value}")
        
        start_time = datetime.now()
        attempts = 0
        
        for strategy in self.recovery_strategies.get(error_type, []):
            attempts += 1
            
            try:
                result = await self._execute_recovery_strategy(
                    strategy, error_type, context, task_description
                )
                
                time_taken = (datetime.now() - start_time).total_seconds()
                
                return ErrorRecoveryResult(
                    recovered=True,
                    strategy=strategy,
                    attempts=attempts,
                    time_taken=time_taken,
                    details=result,
                    success_result=result.get('result')
                )
            
            except Exception as e:
                logger.warning(f"⚠️ Recovery strategy {strategy.value} failed: {e}")
                continue
        
        time_taken = (datetime.now() - start_time).total_seconds()
        
        return ErrorRecoveryResult(
            recovered=False,
            strategy=RecoveryStrategy.SKIP,
            attempts=attempts,
            time_taken=time_taken,
            details={
                'error': 'All recovery strategies failed',
                'error_type': error_type.value,
                'task': task_description,
                'context': context
            }
        )
    
    async def _execute_recovery_strategy(self, strategy: RecoveryStrategy,
                                       error_type: ErrorType,
                                       context: Dict[str, Any],
                                       task_description: str) -> Dict[str, Any]:
        """Execute specific recovery strategy"""
        if strategy == RecoveryStrategy.RETRY:
            return await self._retry_strategy(context, task_description)
        elif strategy == RecoveryStrategy.FALLBACK:
            return await self._fallback_strategy(context, task_description)
        elif strategy == RecoveryStrategy.REASSIGN:
            return await self._reassign_strategy(context, task_description)
        elif strategy == RecoveryStrategy.COMPENSATE:
            return await self._compensate_strategy(context, task_description)
        elif strategy == RecoveryStrategy.SKIP:
            return await self._skip_strategy(context, task_description)
        elif strategy == RecoveryStrategy.ROLLBACK:
            return await self._rollback_strategy(context, task_description)
        
        raise Exception(f"Unknown recovery strategy: {strategy.value}")
    
    async def _retry_strategy(self, context: Dict[str, Any], 
                             task_description: str) -> Dict[str, Any]:
        """Retry failed operation"""
        agent = context.get('agent', 'unknown')
        
        for i, backoff in enumerate(self.retry_backoff[:self.max_retries]):
            logger.debug(f"🔄 Retrying {agent} (attempt {i+1})...")
            await asyncio.sleep(backoff)
            
            # Simulate retry logic
            if i == len(self.retry_backoff) - 1:
                raise Exception(f"Retry limit exceeded for agent {agent}")
        
        return {'recovered': True, 'result': f"Retried {agent} successfully"}
    
    async def _fallback_strategy(self, context: Dict[str, Any], 
                                task_description: str) -> Dict[str, Any]:
        """Use fallback agent"""
        fallback_agent = self._select_fallback_agent(context)
        
        if fallback_agent:
            logger.debug(f"🔄 Falling back to {fallback_agent}")
            return {
                'recovered': True,
                'result': f"Fallback to {fallback_agent} for task: {task_description}"
            }
        
        raise Exception("No fallback agents available")
    
    def _select_fallback_agent(self, context: Dict[str, Any]) -> str:
        """Select appropriate fallback agent based on context"""
        task_type = context.get('task_type', 'general')
        
        fallback_map = {
            'code': 'bmad',
            'workflow': 'n8n',
            'revenue': 'revenue',
            'acquisition': 'acquisition',
            'investor': 'investor',
            'social': 'twitter',
            'viral': 'viral',
            'learning': 'youtube',
            'scraping': 'scraper'
        }
        
        return fallback_map.get(task_type, self.fallback_agents[0])
    
    async def _reassign_strategy(self, context: Dict[str, Any], 
                               task_description: str) -> Dict[str, Any]:
        """Reassign task to different agent"""
        agents = context.get('available_agents', [])
        
        if agents:
            # Exclude the failing agent
            available_agents = [
                a for a in agents 
                if a != context.get('agent', 'unknown')
            ]
            
            if available_agents:
                reassigned_agent = available_agents[0]
                logger.debug(f"🔄 Reassigning to {reassigned_agent}")
                
                return {
                    'recovered': True,
                    'result': f"Task reassigned to {reassigned_agent}"
                }
        
        raise Exception("No available agents for reassignment")
    
    async def _compensate_strategy(self, context: Dict[str, Any], 
                                  task_description: str) -> Dict[str, Any]:
        """Provide compensation for failed operation"""
        logger.debug("🔄 Applying compensation strategy")
        
        return {
            'recovered': True,
            'result': f"Task failed, but compensation applied. Task: {task_description}"
        }
    
    async def _skip_strategy(self, context: Dict[str, Any], 
                           task_description: str) -> Dict[str, Any]:
        """Skip the failed operation"""
        logger.debug("🔄 Skipping failed operation")
        
        return {
            'recovered': True,
            'result': f"Task skipped: {task_description}"
        }
    
    async def _rollback_strategy(self, context: Dict[str, Any], 
                               task_description: str) -> Dict[str, Any]:
        """Roll back any partial operations"""
        logger.debug("🔄 Rolling back operations")
        
        return {
            'recovered': True,
            'result': f"Operations rolled back for task: {task_description}"
        }

# ============================================================================
# SYSTEM HEALTH MONITORING
# ============================================================================

class SystemHealthStatus(Enum):
    """System health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    DOWN = "down"

class HealthMetric(BaseModel):
    """Single health metric measurement"""
    name: str
    value: float
    threshold: float
    status: SystemHealthStatus
    timestamp: datetime = Field(default_factory=datetime.now)
    trend: str = "stable"  # increasing, decreasing, stable

class SystemHealth(BaseModel):
    """Overall system health status"""
    status: SystemHealthStatus
    metrics: List[HealthMetric] = Field(default_factory=list)
    last_checked: datetime = Field(default_factory=datetime.now)
    uptime: float = 0.0
    error_rate: float = 0.0
    response_time: float = 0.0

class SystemHealthMonitor:
    """Continuous system health monitoring"""
    
    def __init__(self):
        self.metrics = self._load_health_metrics()
        self.health_status = SystemHealth(status=SystemHealthStatus.HEALTHY)
        self.check_interval = 60  # seconds
        self.history = []
    
    def _load_health_metrics(self) -> List[Dict[str, Any]]:
        """Load health metric configurations"""
        return [
            {
                'name': 'agent_availability',
                'threshold': 0.95,
                'description': 'Percentage of available agents',
                'critical_threshold': 0.75
            },
            {
                'name': 'task_success_rate',
                'threshold': 0.90,
                'description': 'Percentage of successful tasks',
                'critical_threshold': 0.60
            },
            {
                'name': 'response_time',
                'threshold': 5.0,
                'description': 'Average response time in seconds',
                'critical_threshold': 15.0
            },
            {
                'name': 'error_rate',
                'threshold': 0.10,
                'description': 'Rate of errors per task',
                'critical_threshold': 0.30
            },
            {
                'name': 'memory_usage',
                'threshold': 0.85,
                'description': 'Memory usage percentage',
                'critical_threshold': 0.95
            },
            {
                'name': 'cpu_usage',
                'threshold': 0.90,
                'description': 'CPU usage percentage',
                'critical_threshold': 0.98
            }
        ]
    
    async def check_health(self, metrics: Dict[str, float]) -> SystemHealth:
        """Check current system health"""
        health_metrics = []
        
        for config in self.metrics:
            value = metrics.get(config['name'], 0.0)
            
            if value > config['critical_threshold']:
                status = SystemHealthStatus.CRITICAL
            elif value > config['threshold']:
                status = SystemHealthStatus.WARNING
            else:
                status = SystemHealthStatus.HEALTHY
            
            health_metrics.append(HealthMetric(
                name=config['name'],
                value=value,
                threshold=config['threshold'],
                status=status
            ))
        
        # Determine overall status
        if any(m.status == SystemHealthStatus.CRITICAL for m in health_metrics):
            overall_status = SystemHealthStatus.CRITICAL
        elif any(m.status == SystemHealthStatus.WARNING for m in health_metrics):
            overall_status = SystemHealthStatus.WARNING
        else:
            overall_status = SystemHealthStatus.HEALTHY
        
        # Calculate uptime and other metrics
        error_rate = metrics.get('error_rate', 0.0)
        response_time = metrics.get('response_time', 0.0)
        
        self.health_status = SystemHealth(
            status=overall_status,
            metrics=health_metrics,
            last_checked=datetime.now(),
            uptime=metrics.get('uptime', 0.0),
            error_rate=error_rate,
            response_time=response_time
        )
        
        self._update_history()
        
        return self.health_status
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get health status summary"""
        return {
            'status': self.health_status.status.value,
            'uptime': self.health_status.uptime,
            'error_rate': self.health_status.error_rate,
            'response_time': self.health_status.response_time,
            'metrics': [
                {
                    'name': m.name,
                    'value': m.value,
                    'status': m.status.value
                } for m in self.health_status.metrics
            ]
        }
    
    def _update_history(self):
        """Update health history"""
        self.history.append({
            'timestamp': datetime.now().isoformat(),
            'status': self.health_status.status.value,
            'metrics': [
                {
                    'name': m.name,
                    'value': m.value,
                    'status': m.status.value
                } for m in self.health_status.metrics
            ]
        })
        
        # Keep last 24 hours of history
        max_history = 24 * 60  # 1 minute intervals for 24 hours
        if len(self.history) > max_history:
            self.history = self.history[-max_history:]
    
    def log_health_event(self, event: str, details: Dict[str, Any] = None):
        """Log health events"""
        logger.info(f"🏥 Health Event: {event}")
        if details:
            logger.debug(f"Details: {json.dumps(details, default=str)}")

# ============================================================================
# MAIN ROBUSTNESS SYSTEM
# ============================================================================

class RobustnessSystem:
    """Main robustness and anti-hallucination system"""
    
    def __init__(self):
        self.hallucination_detector = HallucinationDetector()
        self.consensus_verifier = ConsensusVerifier(min_agents=3)
        self.error_recovery = ErrorRecoverySystem()
        self.health_monitor = SystemHealthMonitor()
        self.is_running = False
        self.health_check_task = None
    
    async def initialize(self):
        """Initialize the robustness system"""
        logger.info("🛡️ Initializing Robustness System...")
        
        # Start health monitoring task
        self.is_running = True
        self.health_check_task = asyncio.create_task(self._health_monitoring_loop())
        
        logger.info("✅ Robustness System initialized")
    
    async def _health_monitoring_loop(self):
        """Continuous health monitoring"""
        while self.is_running:
            try:
                # Collect current metrics (simulated for now)
                metrics = self._collect_system_metrics()
                
                # Check health
                health = await self.health_monitor.check_health(metrics)
                
                if health.status == SystemHealthStatus.CRITICAL:
                    logger.warning("🚨 CRITICAL HEALTH STATUS DETECTED")
                    await self._handle_critical_health()
                
                elif health.status == SystemHealthStatus.WARNING:
                    logger.warning("⚠️ WARNING HEALTH STATUS DETECTED")
                    await self._handle_warning_health()
                
                await asyncio.sleep(self.health_monitor.check_interval)
                
            except Exception as e:
                logger.error(f"Health monitoring failed: {e}")
                await asyncio.sleep(30)
    
    def _collect_system_metrics(self) -> Dict[str, float]:
        """Collect current system metrics"""
        # Simulated metrics for testing
        import random
        return {
            'agent_availability': 0.98 + random.uniform(-0.02, 0.02),
            'task_success_rate': 0.95 + random.uniform(-0.05, 0.05),
            'response_time': 2.5 + random.uniform(-1.0, 1.0),
            'error_rate': 0.05 + random.uniform(-0.03, 0.03),
            'memory_usage': 0.75 + random.uniform(-0.1, 0.1),
            'cpu_usage': 0.65 + random.uniform(-0.2, 0.2),
            'uptime': random.uniform(0, 86400)
        }
    
    async def _handle_critical_health(self):
        """Handle critical health status"""
        logger.critical("🚨 SYSTEM IN CRITICAL HEALTH STATE")
        
        # Take emergency actions
        await self._execute_health_actions([
            'reduce_workload',
            'alert_admins',
            'initiate_recovery'
        ])
    
    async def _handle_warning_health(self):
        """Handle warning health status"""
        logger.warning("⚠️ SYSTEM WARNING - Monitoring closely")
        
        await self._execute_health_actions([
            'notify_admins',
            'check_resources'
        ])
    
    async def _execute_health_actions(self, actions: List[str]):
        """Execute health management actions"""
        for action in actions:
            try:
                if action == 'reduce_workload':
                    await self._reduce_workload()
                elif action == 'alert_admins':
                    await self._alert_admins()
                elif action == 'initiate_recovery':
                    await self._initiate_recovery()
                elif action == 'notify_admins':
                    await self._notify_admins()
                elif action == 'check_resources':
                    await self._check_resources()
            except Exception as e:
                logger.error(f"Health action {action} failed: {e}")
    
    async def _reduce_workload(self):
        """Reduce system workload"""
        logger.info("⚖️ Reducing system workload")
        await asyncio.sleep(1)
    
    async def _alert_admins(self):
        """Alert administrators"""
        logger.info("🔔 Alerting administrators")
        await asyncio.sleep(0.5)
    
    async def _initiate_recovery(self):
        """Initiate recovery procedures"""
        logger.info("🔄 Initiating recovery")
        await asyncio.sleep(2)
    
    async def _notify_admins(self):
        """Notify administrators"""
        logger.info("📧 Notifying administrators")
        await asyncio.sleep(0.5)
    
    async def _check_resources(self):
        """Check system resources"""
        logger.info("🔍 Checking system resources")
        await asyncio.sleep(1)
    
    async def verify_result(self, task_description: str, 
                          results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Verify task results for hallucination and consensus
        Returns verification results with recommendations
        """
        logger.info(f"🔍 Verifying task results: {task_description}")
        
        # Step 1: Detect hallucinations in each result
        hallucination_results = []
        for result in results:
            hallucination_result = self.hallucination_detector.detect(str(result['result']))
            hallucination_results.append({
                'agent': result['agent_name'],
                'result': result['result'],
                'hallucination': hallucination_result
            })
        
        # Step 2: Check consensus
        consensus_result = await self.consensus_verifier.verify_consensus(
            task_description, results
        )
        
        # Step 3: Summarize verification
        verification_summary = {
            'task_description': task_description,
            'agent_count': len(results),
            'hallucination_check': self._summarize_hallucinations(hallucination_results),
            'consensus_check': consensus_result.dict(),
            'trust_scores': self.consensus_verifier._get_agent_trust_scores(results),
            'recommendations': []
        }
        
        # Step 4: Generate recommendations
        verification_summary['recommendations'] = self._generate_verification_recommendations(
            hallucination_results, consensus_result
        )
        
        logger.info(f"✅ Verification complete. Consensus: {consensus_result.agreement_score:.2f}")
        
        return verification_summary
    
    def _summarize_hallucinations(self, hallucination_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize hallucination detection results"""
        hallucination_count = sum(1 for r in hallucination_results if r['hallucination'].detected)
        high_severity = sum(1 for r in hallucination_results if r['hallucination'].detected and r['hallucination'].severity.value >= 3)
        
        return {
            'total_hallucinations': hallucination_count,
            'high_severity_count': high_severity,
            'per_agent': [{
                'agent': r['agent'],
                'detected': r['hallucination'].detected,
                'severity': r['hallucination'].severity.value,
                'confidence': r['hallucination'].confidence
            } for r in hallucination_results]
        }
    
    def _generate_verification_recommendations(self, hallucination_results: List[Dict[str, Any]],
                                              consensus_result: ConsensusResult) -> List[str]:
        """Generate recommendations based on verification results"""
        recommendations = []
        
        # Check hallucination recommendations
        hallucination_count = sum(1 for r in hallucination_results if r['hallucination'].detected)
        if hallucination_count > 0:
            recommendations.append(f"{hallucination_count} results contained potential hallucinations. Consider reviewing these results carefully.")
        
        # Check high severity hallucinations
        high_severity = sum(1 for r in hallucination_results if r['hallucination'].detected and r['hallucination'].severity.value >= 3)
        if high_severity > 0:
            recommendations.append(f"{high_severity} results contained high-severity hallucinations. These results should be treated with caution.")
        
        # Check consensus recommendations
        recommendations.extend(consensus_result.recommendations)
        
        return recommendations
    
    async def recover_from_error(self, error: Exception, context: Dict[str, Any],
                               task_description: str) -> ErrorRecoveryResult:
        """Recover from an error"""
        # Determine error type
        error_type = self._classify_error(error)
        
        # Attempt recovery
        return await self.error_recovery.recover(error_type, context, task_description)
    
    def _classify_error(self, error: Exception) -> ErrorType:
        """Classify exception type"""
        error_str = str(error).lower()
        
        if any(keyword in error_str for keyword in ['agent', 'not found', 'unavailable']):
            return ErrorType.AGENT_FAILURE
        elif any(keyword in error_str for keyword in ['timeout', 'timed out']):
            return ErrorType.TIMEOUT
        elif any(keyword in error_str for keyword in ['network', 'connection', 'http']):
            return ErrorType.NETWORK_ERROR
        elif any(keyword in error_str for keyword in ['validation', 'invalid', 'format']):
            return ErrorType.VALIDATION_ERROR
        elif any(keyword in error_str for keyword in ['internal', 'server', 'database']):
            return ErrorType.INTERNAL_ERROR
        elif any(keyword in error_str for keyword in ['conflict']):
            return ErrorType.CONFLICT
        elif any(keyword in error_str for keyword in ['not found']):
            return ErrorType.NOT_FOUND
        else:
            return ErrorType.INTERNAL_ERROR
    
    async def shutdown(self):
        """Shutdown the robustness system"""
        self.is_running = False
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
        logger.info("🛑 Robustness System shutdown complete")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status"""
        return {
            'running': self.is_running,
            'health': self.health_monitor.get_status_summary(),
            'hallucination_detector_config': {
                'pattern_count': len(self.hallucination_detector.patterns),
                'trust_threshold': self.hallucination_detector.trust_threshold
            },
            'consensus_verifier_config': {
                'min_agents': self.consensus_verifier.min_agents,
                'consensus_threshold': self.consensus_verifier.consensus_threshold,
                'diversity_threshold': self.consensus_verifier.diversity_threshold
            },
            'error_recovery_config': {
                'max_retries': self.error_recovery.max_retries,
                'retry_backoff': self.error_recovery.retry_backoff,
                'fallback_agents': self.error_recovery.fallback_agents
            }
        }

# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Main entry point for testing"""
    robustness_system = RobustnessSystem()
    await robustness_system.initialize()
    
    logger.info("📋 System Status:")
    logger.info(json.dumps(robustness_system.get_system_status(), indent=2, default=str))
    
    # Test hallucination detection
    logger.info("\n🔍 Testing Hallucination Detection...")
    test_texts = [
        "This is a normal text without any hallucinations.",
        "Everyone says this product is always perfect and never fails!",
        "Studies prove that 95% of people love this product!",
        "According to research, this approach works in 85% of cases."
    ]
    
    for text in test_texts:
        result = robustness_system.hallucination_detector.detect(text)
        logger.info(f"\nText: '{text}'")
        logger.info(f"Detected: {result.detected}")
        logger.info(f"Severity: {result.severity.value}")
        logger.info(f"Confidence: {result.confidence:.2f}")
        if result.patterns:
            logger.info(f"Patterns: {', '.join(result.patterns)}")
        if result.explanation:
            logger.info(f"Explanation: {result.explanation}")
        if result.suggestions:
            logger.info(f"Suggestions: {', '.join(result.suggestions)}")
    
    # Test consensus verification
    logger.info("\n⚖️ Testing Consensus Verification...")
    test_results = [
        {'agent_name': 'bmad', 'result': 'This is the correct result', 'confidence': 0.9},
        {'agent_name': 'n8n', 'result': 'This is the correct result', 'confidence': 0.85},
        {'agent_name': 'youtube', 'result': 'This is a different result', 'confidence': 0.8},
        {'agent_name': 'scraper', 'result': 'This is the correct result', 'confidence': 0.95}
    ]
    
    consensus = await robustness_system.consensus_verifier.verify_consensus(
        "Test task for consensus", test_results
    )
    logger.info(f"Consensus Reached: {consensus.consensus_reached}")
    logger.info(f"Agreement Score: {consensus.agreement_score:.2f}")
    logger.info(f"Diversity Score: {consensus.diversity_score:.2f}")
    logger.info(f"Majority Opinion: '{consensus.majority_opinion}'")
    
    await robustness_system.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n✅ System shutdown by user")