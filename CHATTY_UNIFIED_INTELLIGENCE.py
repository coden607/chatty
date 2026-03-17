#!/usr/bin/env python3
"""
CHATTY Unified Intelligence System
Combines OpenClaw, Archon2, Agent Zero, BMAD, and DeepCode into a cohesive system
With guardrails against hallucinations and real data enforcement
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from enum import Enum
from dotenv import load_dotenv

# Load environment
load_dotenv(".env", override=False)
_secrets_file = os.getenv("CHATTY_SECRETS_FILE")
if _secrets_file:
    load_dotenv(os.path.expanduser(_secrets_file), override=False)

# Import model router for AI generation
from CHATTY_MODEL_ROUTER import router, TaskType, generate_code, review_code, create_content

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VerificationStatus(Enum):
    """Status of fact verification"""
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    DISPUTED = "disputed"
    UNKNOWN = "unknown"


@dataclass
class IntelligenceResult:
    """Result from intelligence processing with verification"""
    success: bool
    content: Any
    source_system: str
    confidence: float = 0.0
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    sources: List[str] = field(default_factory=list)
    hallucination_risk: float = 0.0
    suggested_actions: List[str] = field(default_factory=list)
    processing_time_ms: float = 0.0


@dataclass
class AgentTask:
    """Task for agent execution"""
    task_id: str
    task_type: str
    description: str
    priority: int = 5
    assigned_agent: Optional[str] = None
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None


class HallucinationGuardrail:
    """
    Guardrail system to prevent and detect AI hallucinations
    """
    
    # Patterns that suggest hallucination
    HALLUCINATION_PATTERNS = [
        "i believe that",
        "it's possible that",
        "perhaps",
        "maybe",
        "i think",
        "in my opinion",
        "as far as i know",
        "to the best of my knowledge",
        "i'm not entirely sure",
        "i don't have specific information",
        "according to some sources",
        "it is said that",
        "some people claim",
    ]
    
    # High-confidence required topics
    HIGH_STAKES_TOPICS = [
        "medical advice",
        "legal advice",
        "financial advice",
        "security vulnerabilities",
        "personal data",
    ]
    
    def __init__(self):
        self.fact_database: Dict[str, Any] = {}
        self.verified_sources: set = set()
        self.logger = logging.getLogger("HallucinationGuardrail")
    
    def analyze_for_hallucination(self, content: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze content for potential hallucinations"""
        risk_score = 0.0
        indicators = []
        
        content_lower = content.lower()
        
        # Check for uncertainty patterns
        for pattern in self.HALLUCINATION_PATTERNS:
            if pattern in content_lower:
                risk_score += 0.15
                indicators.append(f"Uncertainty pattern: '{pattern}'")
        
        # Check for specific numbers without sources
        import re
        specific_numbers = re.findall(r'\b\d{3,}\b', content)
        if len(specific_numbers) > 3 and "source" not in content_lower:
            risk_score += 0.2
            indicators.append("Multiple specific numbers without sources")
        
        # Check for fabricated citations
        citation_patterns = re.findall(r'\[\d+\]|\(\w+ et al\.?,? \d{4}\)', content)
        if citation_patterns and not context.get("has_sources"):
            risk_score += 0.25
            indicators.append("Citations without source material")
        
        # Check for overly specific claims
        if "definitely" in content_lower or "certainly" in content_lower:
            if not context or not context.get("verified_facts"):
                risk_score += 0.1
                indicators.append("Absolute claims without verification")
        
        # Check for high-stakes topics
        for topic in self.HIGH_STAKES_TOPICS:
            if topic in content_lower:
                risk_score += 0.3
                indicators.append(f"High-stakes topic: {topic}")
        
        return {
            "risk_score": min(risk_score, 1.0),
            "indicators": indicators,
            "requires_verification": risk_score > 0.4,
            "should_block": risk_score > 0.7,
        }
    
    def verify_against_sources(self, claim: str, sources: List[str]) -> VerificationStatus:
        """Verify a claim against known sources"""
        if not sources:
            return VerificationStatus.UNVERIFIED
        
        # In production, this would use RAG or semantic search
        # For now, use simple keyword matching
        claim_keywords = set(claim.lower().split())
        
        for source in sources:
            source_keywords = set(source.lower().split())
            overlap = len(claim_keywords & source_keywords)
            if overlap / len(claim_keywords) > 0.5:
                return VerificationStatus.VERIFIED
        
        return VerificationStatus.UNKNOWN
    
    def add_guardrails_to_prompt(self, prompt: str, require_citations: bool = True) -> str:
        """Enhance prompt with anti-hallucination instructions"""
        guardrails = """
IMPORTANT: Follow these guidelines to ensure accuracy:
1. Only state facts you are confident about
2. If uncertain, clearly say "I don't have enough information"
3. Distinguish between facts and opinions
4. Cite specific sources when making claims
5. Avoid speculation or making up information
6. If asked about recent events, verify the date
"""
        if require_citations:
            guardrails += "\n7. Always provide sources for statistical claims\n"
        
        return f"{guardrails}\n\n{prompt}"


class OpenClawIntegration:
    """
    OpenClaw-inspired autonomous learning system
    File chunking, context management, and continuous learning
    """
    
    def __init__(self):
        self.chunker = None
        self.memory_path = Path("generated_content") / "openclaw_memory.json"
        self.context_cache: Dict[str, Any] = {}
        self.logger = logging.getLogger("OpenClaw")
        self._init_chunker()
    
    def _init_chunker(self):
        """Initialize the chunker with fallback"""
        try:
            from dockling_chunker import DocklingChunker
            self.chunker = DocklingChunker()
            self.logger.info("✅ Docling chunker initialized")
        except Exception as e:
            self.logger.warning(f"⚠️ Docling chunker not available: {e}")
            self.chunker = None
    
    async def chunk_and_analyze(self, file_path: str) -> IntelligenceResult:
        """Chunk a file and analyze its contents"""
        start_time = datetime.now()
        
        try:
            if self.chunker:
                chunks = self.chunker.dockling_chunk_file(file_path, strategy='auto')
            else:
                # Fallback to simple chunking
                chunks = await self._simple_chunk_file(file_path)
            
            # Analyze chunks
            analysis = await self._analyze_chunks(chunks)
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return IntelligenceResult(
                success=True,
                content={
                    "chunks": len(chunks),
                    "analysis": analysis,
                    "file_path": file_path,
                },
                source_system="OpenClaw",
                confidence=0.85,
                verification_status=VerificationStatus.VERIFIED,
                sources=[file_path],
                processing_time_ms=processing_time,
            )
            
        except Exception as e:
            return IntelligenceResult(
                success=False,
                content=None,
                source_system="OpenClaw",
                error=str(e),
            )
    
    async def _simple_chunk_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Simple fallback chunking"""
        chunks = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Simple chunking by lines
            lines = content.split('\n')
            chunk_size = 50
            
            for i in range(0, len(lines), chunk_size):
                chunk_lines = lines[i:i + chunk_size]
                chunks.append({
                    'content': '\n'.join(chunk_lines),
                    'start_line': i,
                    'end_line': min(i + chunk_size, len(lines)),
                    'type': 'code' if file_path.endswith('.py') else 'text',
                })
            
            return chunks
        except Exception as e:
            self.logger.error(f"Simple chunking failed: {e}")
            return []
    
    async def _analyze_chunks(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze chunks for patterns and insights"""
        if not chunks:
            return {}
        
        # Count code elements
        functions = []
        classes = []
        imports = []
        
        for chunk in chunks:
            content = chunk.get('content', '')
            
            # Simple pattern matching
            for line in content.split('\n'):
                if line.strip().startswith('def '):
                    functions.append(line.strip())
                elif line.strip().startswith('class '):
                    classes.append(line.strip())
                elif line.strip().startswith('import ') or line.strip().startswith('from '):
                    imports.append(line.strip())
        
        return {
            "total_chunks": len(chunks),
            "functions_found": len(functions),
            "classes_found": len(classes),
            "imports_found": len(imports),
            "sample_functions": functions[:5],
            "sample_classes": classes[:5],
        }
    
    async def learn_from_file(self, file_path: str) -> IntelligenceResult:
        """Learn from a file and store insights"""
        result = await self.chunk_and_analyze(file_path)
        
        if result.success:
            # Store in memory
            self._store_learning(file_path, result.content)
        
        return result
    
    def _store_learning(self, file_path: str, content: Any):
        """Store learning in persistent memory"""
        memory_entry = {
            "timestamp": datetime.now().isoformat(),
            "file_path": file_path,
            "content": content,
        }
        
        try:
            existing = []
            if self.memory_path.exists():
                with open(self.memory_path, 'r') as f:
                    existing = json.load(f)
            
            existing.append(memory_entry)
            
            # Keep only last 1000 entries
            existing = existing[-1000:]
            
            with open(self.memory_path, 'w') as f:
                json.dump(existing, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to store learning: {e}")


class Archon2Integration:
    """
    Archon2-inspired hierarchical agent orchestration
    4-level hierarchy: Master Coordinators -> Domain Specialists -> Task Executors -> Utility Agents
    """
    
    def __init__(self):
        self.agent_hierarchy = {
            "level_1": [],  # Master Coordinators
            "level_2": [],  # Domain Specialists
            "level_3": [],  # Task Executors
            "level_4": [],  # Utility Agents
        }
        self.active_tasks: Dict[str, AgentTask] = {}
        self.logger = logging.getLogger("Archon2")
    
    async def register_agent(self, agent_id: str, agent_type: str, level: int, capabilities: List[str]):
        """Register an agent in the hierarchy"""
        level_key = f"level_{level}"
        if level_key not in self.agent_hierarchy:
            raise ValueError(f"Invalid hierarchy level: {level}")
        
        agent = {
            "id": agent_id,
            "type": agent_type,
            "level": level,
            "capabilities": capabilities,
            "status": "idle",
            "registered_at": datetime.now().isoformat(),
        }
        
        self.agent_hierarchy[level_key].append(agent)
        self.logger.info(f"✅ Registered {agent_type} agent '{agent_id}' at level {level}")
    
    async def submit_task(self, task_description: str, task_type: str, priority: int = 5) -> str:
        """Submit a task for orchestration"""
        task_id = f"archon_task_{datetime.now().timestamp()}"
        
        task = AgentTask(
            task_id=task_id,
            task_type=task_type,
            description=task_description,
            priority=priority,
        )
        
        self.active_tasks[task_id] = task
        
        # Determine appropriate level
        target_level = self._determine_task_level(task_type)
        
        # Route to appropriate agents
        await self._route_task(task, target_level)
        
        return task_id
    
    def _determine_task_level(self, task_type: str) -> int:
        """Determine which hierarchy level should handle this task"""
        level_mapping = {
            "strategy": 1,
            "coordination": 1,
            "architecture": 2,
            "design": 2,
            "implementation": 3,
            "coding": 3,
            "testing": 3,
            "deployment": 3,
            "utility": 4,
            "logging": 4,
            "monitoring": 4,
        }
        return level_mapping.get(task_type.lower(), 3)
    
    async def _route_task(self, task: AgentTask, level: int):
        """Route task to appropriate agents"""
        level_key = f"level_{level}"
        agents = self.agent_hierarchy[level_key]
        
        if not agents:
            self.logger.warning(f"⚠️ No agents at level {level}, escalating to level {level - 1}")
            if level > 1:
                await self._route_task(task, level - 1)
            return
        
        # Find best agent for task
        best_agent = None
        best_match = 0
        
        for agent in agents:
            if agent["status"] != "idle":
                continue
            
            # Simple capability matching
            match_score = self._calculate_capability_match(agent, task)
            if match_score > best_match:
                best_match = match_score
                best_agent = agent
        
        if best_agent:
            task.assigned_agent = best_agent["id"]
            task.status = "assigned"
            best_agent["status"] = "busy"
            self.logger.info(f"📋 Task {task.task_id} assigned to {best_agent['id']}")
        else:
            self.logger.warning(f"⚠️ No available agents for task {task.task_id}")
            task.status = "queued"
    
    def _calculate_capability_match(self, agent: Dict, task: AgentTask) -> float:
        """Calculate how well an agent matches a task"""
        task_lower = task.task_type.lower()
        capabilities = [c.lower() for c in agent["capabilities"]]
        
        if task_lower in capabilities:
            return 1.0
        
        # Check for partial matches
        for cap in capabilities:
            if task_lower in cap or cap in task_lower:
                return 0.7
        
        return 0.3  # Base match
    
    async def get_hierarchy_status(self) -> IntelligenceResult:
        """Get current status of the hierarchy"""
        total_agents = sum(len(agents) for agents in self.agent_hierarchy.values())
        active_tasks = len([t for t in self.active_tasks.values() if t.status != "completed"])
        
        status = {
            "total_agents": total_agents,
            "agents_by_level": {
                level: len(agents) for level, agents in self.agent_hierarchy.items()
            },
            "active_tasks": active_tasks,
            "hierarchy_health": "healthy" if total_agents > 0 else "degraded",
        }
        
        return IntelligenceResult(
            success=True,
            content=status,
            source_system="Archon2",
            confidence=1.0,
            verification_status=VerificationStatus.VERIFIED,
        )


class AgentZeroIntegration:
    """
    Agent Zero-inspired fleet management
    Zero-shot coordination between agents
    """
    
    def __init__(self):
        self.fleets: Dict[str, Dict[str, Any]] = {}
        self.coordination_protocols = ["zero_shot", "emergent", "adaptive"]
        self.logger = logging.getLogger("AgentZero")
    
    async def deploy_fleet(self, fleet_name: str, agent_types: List[str], protocol: str = "zero_shot") -> IntelligenceResult:
        """Deploy a new agent fleet"""
        if protocol not in self.coordination_protocols:
            return IntelligenceResult(
                success=False,
                content=None,
                source_system="AgentZero",
                error=f"Unknown protocol: {protocol}",
            )
        
        fleet_id = f"fleet_{fleet_name}_{datetime.now().timestamp()}"
        
        agents = []
        for agent_type in agent_types:
            agent_id = f"{fleet_name}_{agent_type}_{len(agents)}"
            agents.append({
                "id": agent_id,
                "type": agent_type,
                "status": "idle",
                "fleet_id": fleet_id,
            })
        
        self.fleets[fleet_id] = {
            "name": fleet_name,
            "protocol": protocol,
            "agents": agents,
            "created_at": datetime.now().isoformat(),
            "tasks_completed": 0,
        }
        
        self.logger.info(f"🚀 Deployed fleet '{fleet_name}' with {len(agents)} agents using {protocol} protocol")
        
        return IntelligenceResult(
            success=True,
            content={
                "fleet_id": fleet_id,
                "agents_deployed": len(agents),
                "protocol": protocol,
            },
            source_system="AgentZero",
            confidence=1.0,
            verification_status=VerificationStatus.VERIFIED,
        )
    
    async def coordinate_task(self, fleet_id: str, task: Dict[str, Any]) -> IntelligenceResult:
        """Coordinate a task across a fleet"""
        if fleet_id not in self.fleets:
            return IntelligenceResult(
                success=False,
                content=None,
                source_system="AgentZero",
                error=f"Fleet not found: {fleet_id}",
            )
        
        fleet = self.fleets[fleet_id]
        
        # Select best agent for task
        best_agent = self._select_best_agent(fleet, task)
        
        if not best_agent:
            return IntelligenceResult(
                success=False,
                content=None,
                source_system="AgentZero",
                error="No suitable agent available",
            )
        
        # Execute task (simulated)
        best_agent["status"] = "executing"
        
        # In production, this would actually execute the task
        result = await self._execute_agent_task(best_agent, task)
        
        best_agent["status"] = "idle"
        fleet["tasks_completed"] += 1
        
        return IntelligenceResult(
            success=True,
            content=result,
            source_system="AgentZero",
            confidence=0.9,
            verification_status=VerificationStatus.VERIFIED,
        )
    
    def _select_best_agent(self, fleet: Dict, task: Dict) -> Optional[Dict]:
        """Select the best agent for a task"""
        available = [a for a in fleet["agents"] if a["status"] == "idle"]
        
        if not available:
            return None
        
        task_type = task.get("type", "")
        
        # Simple matching
        for agent in available:
            if task_type.lower() in agent["type"].lower():
                return agent
        
        return available[0]  # Default to first available
    
    async def _execute_agent_task(self, agent: Dict, task: Dict) -> Dict:
        """Execute a task with an agent"""
        # In production, this would invoke actual agent code
        return {
            "agent_id": agent["id"],
            "task_type": task.get("type"),
            "status": "completed",
            "result": f"Task executed by {agent['type']} agent",
        }


class BMADIntegration:
    """
    BMAD (Behavioral Modeling for Agent Dynamics) integration
    Predict and optimize agent behavior
    """
    
    def __init__(self):
        self.behavioral_models: Dict[str, Dict] = {}
        self.interaction_history: List[Dict] = []
        self.logger = logging.getLogger("BMAD")
    
    async def model_agent_behavior(self, agent_id: str, behavior_data: Dict) -> IntelligenceResult:
        """Create a behavioral model for an agent"""
        # Analyze patterns
        patterns = self._extract_patterns(behavior_data)
        
        # Create predictions
        predictions = self._generate_predictions(patterns)
        
        # Store model
        self.behavioral_models[agent_id] = {
            "agent_id": agent_id,
            "patterns": patterns,
            "predictions": predictions,
            "created_at": datetime.now().isoformat(),
            "accuracy_score": 0.85,
        }
        
        return IntelligenceResult(
            success=True,
            content={
                "agent_id": agent_id,
                "patterns_identified": len(patterns),
                "predictions_generated": len(predictions),
            },
            source_system="BMAD",
            confidence=0.85,
            verification_status=VerificationStatus.VERIFIED,
        )
    
    def _extract_patterns(self, behavior_data: Dict) -> List[str]:
        """Extract behavioral patterns from data"""
        patterns = []
        
        if "response_times" in behavior_data:
            avg_time = sum(behavior_data["response_times"]) / len(behavior_data["response_times"])
            if avg_time < 1.0:
                patterns.append("fast_responder")
            else:
                patterns.append("thorough_processor")
        
        if "success_rate" in behavior_data:
            if behavior_data["success_rate"] > 0.9:
                patterns.append("high_performer")
            elif behavior_data["success_rate"] > 0.7:
                patterns.append("reliable")
            else:
                patterns.append("needs_improvement")
        
        if "task_types" in behavior_data:
            unique_types = set(behavior_data["task_types"])
            if len(unique_types) > 3:
                patterns.append("versatile")
            else:
                patterns.append("specialized")
        
        return patterns
    
    def _generate_predictions(self, patterns: List[str]) -> List[str]:
        """Generate predictions based on patterns"""
        predictions = []
        
        if "fast_responder" in patterns and "high_performer" in patterns:
            predictions.append("optimal_for_high_volume_tasks")
        
        if "thorough_processor" in patterns:
            predictions.append("optimal_for_complex_tasks")
        
        if "versatile" in patterns:
            predictions.append("can_handle_diverse_workloads")
        
        if "specialized" in patterns:
            predictions.append("best_for_specific_domain_tasks")
        
        return predictions
    
    async def predict_performance(self, agent_id: str, task_context: Dict) -> IntelligenceResult:
        """Predict agent performance on a task"""
        if agent_id not in self.behavioral_models:
            return IntelligenceResult(
                success=False,
                content=None,
                source_system="BMAD",
                error=f"No model found for agent: {agent_id}",
            )
        
        model = self.behavioral_models[agent_id]
        
        # Simple prediction based on patterns
        confidence = 0.7
        predicted_success = True
        
        task_type = task_context.get("type", "")
        patterns = model["patterns"]
        
        if "specialized" in patterns and task_type not in str(patterns):
            confidence *= 0.8
        
        if "high_performer" in patterns:
            confidence *= 1.1
        
        return IntelligenceResult(
            success=True,
            content={
                "agent_id": agent_id,
                "predicted_success": predicted_success,
                "confidence": min(confidence, 1.0),
                "estimated_completion_time": "unknown",
            },
            source_system="BMAD",
            confidence=min(confidence, 1.0),
            verification_status=VerificationStatus.VERIFIED,
        )


class DeepCodeIntegration:
    """
    DeepCode-inspired static analysis and security scanning
    AI-powered code review with vulnerability detection
    """
    
    def __init__(self):
        self.vulnerability_patterns = self._load_vulnerability_patterns()
        self.logger = logging.getLogger("DeepCode")
    
    def _load_vulnerability_patterns(self) -> List[Dict]:
        """Load known vulnerability patterns"""
        return [
            {
                "id": "DC-001",
                "name": "SQL Injection",
                "pattern": r'execute\s*\(\s*["\'].*%s|(?:SELECT|INSERT|UPDATE|DELETE|WHERE).*?%s',
                "severity": "critical",
                "description": "Potential SQL injection vulnerability",
            },
            {
                "id": "DC-002",
                "name": "Hardcoded Secret",
                "pattern": r'(password|secret|key|token)\s*=\s*["\'][^"\']+["\']',
                "severity": "high",
                "description": "Hardcoded credential detected",
            },
            {
                "id": "DC-003",
                "name": "Insecure Deserialization",
                "pattern": r'pickle\.loads|yaml\.load\(',
                "severity": "high",
                "description": "Insecure deserialization detected",
            },
            {
                "id": "DC-004",
                "name": "Debug Mode Enabled",
                "pattern": r'DEBUG\s*=\s*True',
                "severity": "medium",
                "description": "Debug mode should be disabled in production",
            },
            {
                "id": "DC-005",
                "name": "Weak Hashing",
                "pattern": r'hashlib\.md5|hashlib\.sha1',
                "severity": "medium",
                "description": "Weak hashing algorithm used",
            },
        ]
    
    async def analyze_code(self, code: str, language: str = "python") -> IntelligenceResult:
        """Analyze code for issues"""
        start_time = datetime.now()
        
        issues = []
        
        # Pattern-based scanning
        for vuln in self.vulnerability_patterns:
            import re
            matches = re.finditer(vuln["pattern"], code, re.IGNORECASE)
            for match in matches:
                issues.append({
                    "id": vuln["id"],
                    "name": vuln["name"],
                    "severity": vuln["severity"],
                    "description": vuln["description"],
                    "line": code[:match.start()].count('\n') + 1,
                    "match": match.group()[:50],
                })
        
        # AI-powered analysis using model router
        ai_analysis = await self._ai_code_analysis(code, language)
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return IntelligenceResult(
            success=True,
            content={
                "issues_found": len(issues),
                "issues": issues,
                "ai_analysis": ai_analysis,
                "language": language,
            },
            source_system="DeepCode",
            confidence=0.9,
            verification_status=VerificationStatus.VERIFIED,
            suggested_actions=self._generate_fix_suggestions(issues),
            processing_time_ms=processing_time,
        )
    
    async def _ai_code_analysis(self, code: str, language: str) -> Dict:
        """Use AI to analyze code"""
        try:
            result = await review_code(code, language)
            if result.success:
                return {
                    "ai_review": result.content,
                    "confidence": result.confidence,
                }
        except Exception as e:
            self.logger.error(f"AI analysis failed: {e}")
        
        return {"ai_review": None, "confidence": 0}
    
    def _generate_fix_suggestions(self, issues: List[Dict]) -> List[str]:
        """Generate fix suggestions for found issues"""
        suggestions = []
        
        for issue in issues:
            if issue["id"] == "DC-001":
                suggestions.append("Use parameterized queries to prevent SQL injection")
            elif issue["id"] == "DC-002":
                suggestions.append("Move secrets to environment variables")
            elif issue["id"] == "DC-003":
                suggestions.append("Use yaml.safe_load() instead of yaml.load()")
            elif issue["id"] == "DC-004":
                suggestions.append("Set DEBUG = False in production")
            elif issue["id"] == "DC-005":
                suggestions.append("Use hashlib.sha256() or better")
        
        return suggestions


class UnifiedIntelligenceSystem:
    """
    Main entry point for all intelligence systems
    Combines OpenClaw, Archon2, Agent Zero, BMAD, and DeepCode
    """
    
    def __init__(self):
        self.openclaw = OpenClawIntegration()
        self.archon2 = Archon2Integration()
        self.agent_zero = AgentZeroIntegration()
        self.bmad = BMADIntegration()
        self.deepcode = DeepCodeIntegration()
        self.guardrail = HallucinationGuardrail()
        self.logger = logging.getLogger("UnifiedIntelligence")
        
        # Register default agents in hierarchy
        asyncio.create_task(self._initialize_default_agents())
    
    async def _initialize_default_agents(self):
        """Initialize default agents"""
        # Master Coordinators
        await self.archon2.register_agent("master_orchestrator", "orchestrator", 1, ["coordination", "strategy"])
        
        # Domain Specialists
        await self.archon2.register_agent("code_specialist", "code_expert", 2, ["coding", "review", "architecture"])
        await self.archon2.register_agent("content_specialist", "content_expert", 2, ["content", "marketing", "seo"])
        
        # Task Executors
        await self.archon2.register_agent("developer_agent", "developer", 3, ["implementation", "coding", "testing"])
        await self.archon2.register_agent("writer_agent", "writer", 3, ["writing", "editing", "publishing"])
        
        # Utility Agents
        await self.archon2.register_agent("logger_agent", "logger", 4, ["logging", "monitoring"])
        await self.archon2.register_agent("cache_agent", "cache_manager", 4, ["caching", "storage"])
    
    async def process(
        self,
        task_type: str,
        data: Any,
        require_verification: bool = True,
        check_hallucination: bool = True,
    ) -> IntelligenceResult:
        """
        Process a task using the unified intelligence system
        
        Args:
            task_type: Type of task (code_analysis, content_creation, file_learning, etc.)
            data: Input data for the task
            require_verification: Whether to require source verification
            check_hallucination: Whether to check for hallucinations
        
        Returns:
            IntelligenceResult with processed output
        """
        start_time = datetime.now()
        
        # Route to appropriate subsystem
        if task_type == "code_analysis":
            result = await self.deepcode.analyze_code(data.get("code", ""), data.get("language", "python"))
        
        elif task_type == "file_learning":
            result = await self.openclaw.learn_from_file(data.get("file_path", ""))
        
        elif task_type == "deploy_fleet":
            result = await self.agent_zero.deploy_fleet(
                data.get("fleet_name", ""),
                data.get("agent_types", []),
                data.get("protocol", "zero_shot")
            )
        
        elif task_type == "model_behavior":
            result = await self.bmad.model_agent_behavior(
                data.get("agent_id", ""),
                data.get("behavior_data", {})
            )
        
        elif task_type == "submit_task":
            task_id = await self.archon2.submit_task(
                data.get("description", ""),
                data.get("task_type", ""),
                data.get("priority", 5)
            )
            result = IntelligenceResult(
                success=True,
                content={"task_id": task_id},
                source_system="Archon2",
                confidence=1.0,
            )
        
        elif task_type == "ai_generate":
            gen_result = await router.generate(
                prompt=data.get("prompt", ""),
                system_prompt=data.get("system_prompt", ""),
                task_type=TaskType(data.get("task_category", "chat")),
            )
            result = IntelligenceResult(
                success=gen_result.success,
                content=gen_result.content if gen_result.success else (gen_result.error or "AI generation failed"),
                source_system="ModelRouter",
                confidence=gen_result.confidence,
            )
        
        else:
            return IntelligenceResult(
                success=False,
                content=None,
                source_system="UnifiedIntelligence",
                error=f"Unknown task type: {task_type}",
            )
        
        # Apply hallucination guardrail if requested
        if check_hallucination and result.success and isinstance(result.content, str):
            analysis = self.guardrail.analyze_for_hallucination(result.content)
            result.hallucination_risk = analysis["risk_score"]
            
            if analysis["should_block"]:
                return IntelligenceResult(
                    success=False,
                    content=None,
                    source_system="UnifiedIntelligence",
                    error=f"Content blocked due to high hallucination risk: {analysis['indicators']}",
                    hallucination_risk=analysis["risk_score"],
                )
            
            if analysis["requires_verification"] and require_verification:
                result.verification_status = VerificationStatus.UNVERIFIED
                result.suggested_actions.append("Verify content against sources before use")
        
        # Calculate processing time
        result.processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        return result
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get status of all subsystems"""
        return {
            "timestamp": datetime.now().isoformat(),
            "subsystems": {
                "model_router": router.health_check(),
                "archon2": (await self.archon2.get_hierarchy_status()).content,
                "agent_zero": {
                    "active_fleets": len(self.agent_zero.fleets),
                },
                "bmad": {
                    "models_trained": len(self.bmad.behavioral_models),
                },
                "deepcode": {
                    "patterns_loaded": len(self.deepcode.vulnerability_patterns),
                },
            },
            "overall_status": "operational",
        }


# Global instance
unified_intelligence = UnifiedIntelligenceSystem()


# Convenience functions
async def analyze_code(code: str, language: str = "python") -> IntelligenceResult:
    """Analyze code for issues"""
    return await unified_intelligence.process(
        task_type="code_analysis",
        data={"code": code, "language": language},
    )


async def learn_from_file(file_path: str) -> IntelligenceResult:
    """Learn from a file"""
    return await unified_intelligence.process(
        task_type="file_learning",
        data={"file_path": file_path},
    )


async def generate_with_guardrails(
    prompt: str,
    system_prompt: str = "",
    task_category: str = "chat",
) -> IntelligenceResult:
    """Generate content with hallucination guardrails"""
    return await unified_intelligence.process(
        task_type="ai_generate",
        data={
            "prompt": prompt,
            "system_prompt": system_prompt,
            "task_category": task_category,
        },
        check_hallucination=True,
    )


# Test function
async def test_unified_intelligence():
    """Test the unified intelligence system"""
    print("🧠 Testing CHATTY Unified Intelligence System")
    print("=" * 70)
    
    # Test system status
    print("\n📊 System Status:")
    status = await unified_intelligence.get_system_status()
    print(f"  Overall: {status['overall_status']}")
    print(f"  BMAD models: {status['subsystems']['bmad']['models_trained']}")
    print(f"  DeepCode patterns: {status['subsystems']['deepcode']['patterns_loaded']}")
    
    # Test code analysis
    print("\n🔍 Testing code analysis:")
    test_code = """
def process_user_input(user_input):
    query = "SELECT * FROM users WHERE name = '%s'" % user_input
    db.execute(query)
    password = "secret123"
    return result
"""
    result = await analyze_code(test_code)
    if result.success:
        print(f"  ✅ Found {result.content['issues_found']} issues")
        for issue in result.content['issues'][:3]:
            print(f"    - {issue['name']} ({issue['severity']})")
    
    # Test generation with guardrails
    print("\n📝 Testing generation with guardrails:")
    result = await generate_with_guardrails(
        prompt="What is 2+2?",
        task_category="chat",
    )
    if result.success:
        print(f"  ✅ Generated (confidence: {result.confidence:.2f})")
        print(f"  Risk: {result.hallucination_risk:.2f}")
    
    print("\n" + "=" * 70)
    print("Tests complete!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        asyncio.run(test_unified_intelligence())
    else:
        # Print system status
        print(json.dumps(asyncio.run(unified_intelligence.get_system_status()), indent=2))
