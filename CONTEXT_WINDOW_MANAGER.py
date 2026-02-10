#!/usr/bin/env python3
"""
Context Window Management System
Monitors token usage and prepares concise handoffs to prevent errors
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

class ContextStatus(Enum):
    HEALTHY = "healthy"      # < 50% usage
    WARNING = "warning"      # 50-75% usage  
    CRITICAL = "critical"    # 75-90% usage
    EMERGENCY = "emergency"  # > 90% usage

@dataclass
class ContextSnapshot:
    """Snapshot of current context state"""
    timestamp: datetime = field(default_factory=datetime.now)
    total_tokens_used: int = 0
    max_context_window: int = 4096  # Default, can be adjusted per model
    usage_percentage: float = 0.0
    status: ContextStatus = ContextStatus.HEALTHY
    key_points: List[str] = field(default_factory=list)
    action_items: List[str] = field(default_factory=list)
    decisions_made: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)
    context_summary: str = ""

@dataclass
class HandoffPackage:
    """Concise handoff package for context continuation"""
    session_id: str
    handoff_timestamp: datetime = field(default_factory=datetime.now)
    original_context_tokens: int = 0
    compressed_tokens: int = 0
    compression_ratio: float = 0.0
    priority_level: int = 1  # 1=highest priority, 5=lowest
    
    # Core context elements
    project_goal: str = ""
    current_phase: str = ""
    key_decisions: List[str] = field(default_factory=list)
    immediate_actions: List[str] = field(default_factory=list)
    blockers_issues: List[str] = field(default_factory=list)
    
    # Technical details
    files_created: List[str] = field(default_factory=list)
    dependencies_needed: List[str] = field(default_factory=list)
    code_status: Dict[str, str] = field(default_factory=dict)
    
    # Next agent instructions
    next_agent_focus: str = ""
    continuation_plan: str = ""
    success_criteria: List[str] = field(default_factory=list)

class ContextWindowManager:
    """Manages context window usage and prepares handoffs"""
    
    def __init__(self, max_context_window: int = 4096, warning_threshold: float = 0.75):
        self.max_context_window = max_context_window
        self.warning_threshold = warning_threshold
        self.current_tokens = 0
        self.context_history = []
        self.snapshots = []
        self.handoff_packages = []
        
        # Context tracking
        self.key_points = []
        self.action_items = []
        self.decisions_made = []
        self.files_created = []
        self.issues_identified = []
        
        # Compression settings
        self.compression_model = None
        self._init_compression()
    
    def _init_compression(self):
        """Initialize text compression for context summarization"""
        try:
            from sentence_transformers import SentenceTransformer
            self.compression_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✅ Context compression model loaded")
        except ImportError:
            logger.warning("⚠️ Sentence transformers not available, using basic compression")
    
    def add_tokens(self, token_count: int, content_type: str = "general", content: str = ""):
        """Add tokens to current context and check thresholds"""
        self.current_tokens += token_count
        usage_percentage = self.current_tokens / self.max_context_window
        
        # Extract key information from content
        if content:
            self._extract_key_info(content, content_type)
        
        # Check if we need to prepare for handoff
        if usage_percentage >= self.warning_threshold:
            logger.warning(f"⚠️ Context window at {usage_percentage:.1%} - Preparing handoff")
            return self.prepare_handoff()
        
        return None
    
    def _extract_key_info(self, content: str, content_type: str):
        """Extract key information from content"""
        # Simple extraction - could be enhanced with NLP
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Extract action items
            if any(keyword in line.lower() for keyword in ['todo:', 'action:', 'implement:', 'create:']):
                self.action_items.append(line)
            
            # Extract decisions
            elif any(keyword in line.lower() for keyword in ['decided:', 'chose:', 'selected:', 'approved:']):
                self.decisions_made.append(line)
            
            # Extract key points
            elif any(keyword in line.lower() for keyword in ['important:', 'critical:', 'key:', 'note:']):
                self.key_points.append(line)
            
            # Extract file creation
            elif 'created:' in line.lower() or 'written:' in line.lower():
                self.files_created.append(line)
            
            # Extract issues
            elif any(keyword in line.lower() for keyword in ['issue:', 'problem:', 'error:', 'failed:']):
                self.issues_identified.append(line)
    
    def prepare_handoff(self) -> HandoffPackage:
        """Prepare concise handoff package"""
        logger.info("🔄 Preparing context handoff package...")
        
        # Create context snapshot
        snapshot = ContextSnapshot(
            total_tokens_used=self.current_tokens,
            max_context_window=self.max_context_window,
            usage_percentage=self.current_tokens / self.max_context_window,
            status=self._get_context_status(),
            key_points=self.key_points[-10:],  # Last 10 key points
            action_items=self.action_items[-5:],  # Last 5 action items
            decisions_made=self.decisions_made[-5:],  # Last 5 decisions
            context_summary=self._generate_context_summary()
        )
        
        # Create handoff package
        handoff = HandoffPackage(
            session_id=f"session_{int(time.time())}",
            original_context_tokens=self.current_tokens,
            priority_level=self._determine_priority(),
            
            # Core context
            project_goal=self._extract_project_goal(),
            current_phase=self._extract_current_phase(),
            key_decisions=self.decisions_made[-3:],
            immediate_actions=self.action_items[:3],  # Most urgent
            blockers_issues=self.issues_identified,
            
            # Technical details
            files_created=self.files_created,
            dependencies_needed=self._extract_dependencies(),
            code_status=self._extract_code_status(),
            
            # Next agent instructions
            next_agent_focus=self._determine_next_focus(),
            continuation_plan=self._create_continuation_plan(),
            success_criteria=self._extract_success_criteria()
        )
        
        # Compress the handoff
        compressed_handoff = self._compress_handoff(handoff)
        
        # Store and return
        self.snapshots.append(snapshot)
        self.handoff_packages.append(compressed_handoff)
        
        logger.info(f"✅ Handoff prepared: {compressed_handoff.compressed_tokens} tokens (compressed from {handoff.original_context_tokens})")
        
        return compressed_handoff
    
    def _get_context_status(self) -> ContextStatus:
        """Get current context status"""
        usage = self.current_tokens / self.max_context_window
        
        if usage < 0.5:
            return ContextStatus.HEALTHY
        elif usage < 0.75:
            return ContextStatus.WARNING
        elif usage < 0.9:
            return ContextStatus.CRITICAL
        else:
            return ContextStatus.EMERGENCY
    
    def _generate_context_summary(self) -> str:
        """Generate concise context summary"""
        summary_parts = []
        
        if self.project_goal := self._extract_project_goal():
            summary_parts.append(f"Goal: {self.project_goal}")
        
        if current_phase := self._extract_current_phase():
            summary_parts.append(f"Phase: {current_phase}")
        
        if self.action_items:
            summary_parts.append(f"Actions: {len(self.action_items)} pending")
        
        if self.issues_identified:
            summary_parts.append(f"Issues: {len(self.issues_identified)} identified")
        
        return " | ".join(summary_parts)
    
    def _extract_project_goal(self) -> str:
        """Extract main project goal from context"""
        # Look for goal-related statements
        for point in reversed(self.key_points):
            if any(keyword in point.lower() for keyword in ['goal:', 'objective:', 'aim:', 'purpose:']):
                return point.split(':', 1)[-1].strip()
        
        # Default based on recent context
        if self.files_created:
            return "Build enhanced multi-agent automation system"
        
        return "System development and enhancement"
    
    def _extract_current_phase(self) -> str:
        """Extract current project phase"""
        # Analyze recent actions to determine phase
        if any('create' in action.lower() for action in self.action_items[-3:]):
            return "Implementation"
        elif any('test' in action.lower() for action in self.action_items[-3:]):
            return "Testing"
        elif any('fix' in action.lower() for action in self.action_items[-3:]):
            return "Debugging"
        elif any('integrate' in action.lower() for action in self.action_items[-3:]):
            return "Integration"
        else:
            return "Development"
    
    def _determine_priority(self) -> int:
        """Determine handoff priority based on context"""
        if self.issues_identified:
            return 1  # High priority - issues to resolve
        elif self.action_items:
            return 2  # Medium priority - actions to complete
        elif self.decisions_made:
            return 3  # Lower priority - decisions made
        else:
            return 4  # Lowest priority - informational
    
    def _extract_dependencies(self) -> List[str]:
        """Extract dependencies from context"""
        dependencies = []
        
        for point in self.key_points:
            if any(keyword in point.lower() for keyword in ['install', 'import', 'require', 'dependency']):
                dependencies.append(point)
        
        return dependencies[-5:]  # Last 5 dependencies
    
    def _extract_code_status(self) -> Dict[str, str]:
        """Extract status of created code files"""
        status = {}
        
        for file_info in self.files_created:
            if '.py' in file_info:
                filename = file_info.split()[-1]
                status[filename] = "created"
        
        return status
    
    def _determine_next_focus(self) -> str:
        """Determine what the next agent should focus on"""
        if self.issues_identified:
            return "Resolve identified issues and blockers"
        elif self.action_items:
            return "Complete pending action items"
        elif self.files_created:
            return "Test and validate created components"
        else:
            return "Continue development based on current progress"
    
    def _create_continuation_plan(self) -> str:
        """Create concise continuation plan"""
        plan_parts = []
        
        if self.issues_identified:
            plan_parts.append(f"1. Fix {len(self.issues_identified)} critical issues")
        
        if self.action_items:
            plan_parts.append(f"2. Complete {len(self.action_items)} action items")
        
        if self.files_created:
            plan_parts.append(f"3. Test {len(self.files_created)} created files")
        
        plan_parts.append("4. Validate system integration")
        plan_parts.append("5. Prepare for next development phase")
        
        return " | ".join(plan_parts)
    
    def _extract_success_criteria(self) -> List[str]:
        """Extract success criteria from context"""
        criteria = []
        
        # Look for success-related statements
        for point in self.key_points:
            if any(keyword in point.lower() for keyword in ['success:', 'criteria:', 'requirement:', 'validate:']):
                criteria.append(point)
        
        # Default criteria
        if not criteria:
            criteria = [
                "All components integrate successfully",
                "System functions without errors",
                "Performance meets requirements"
            ]
        
        return criteria[:3]  # Top 3 criteria
    
    def _compress_handoff(self, handoff: HandoffPackage) -> HandoffPackage:
        """Compress handoff to reduce token usage"""
        original_tokens = self._estimate_tokens(handoff)
        
        # Simple compression - remove redundancy and be concise
        compressed = HandoffPackage(
            session_id=handoff.session_id,
            handoff_timestamp=handoff.handoff_timestamp,
            original_context_tokens=original_tokens,
            priority_level=handoff.priority_level,
            
            # Compressed content
            project_goal=handoff.project_goal[:100] if handoff.project_goal else "",
            current_phase=handoff.current_phase[:50] if handoff.current_phase else "",
            key_decisions=handoff.key_decisions[:2],
            immediate_actions=handoff.immediate_actions[:2],
            blockers_issues=handoff.blockers_issues[:3],
            files_created=handoff.files_created[:5],
            dependencies_needed=handoff.dependencies_needed[:3],
            code_status=dict(list(handoff.code_status.items())[:5]),
            next_agent_focus=handoff.next_agent_focus[:100] if handoff.next_agent_focus else "",
            continuation_plan=handoff.continuation_plan[:200] if handoff.continuation_plan else "",
            success_criteria=handoff.success_criteria[:2]
        )
        
        compressed_tokens = self._estimate_tokens(compressed)
        compressed.compressed_tokens = compressed_tokens
        compressed.compression_ratio = original_tokens / max(compressed_tokens, 1)
        
        return compressed
    
    def _estimate_tokens(self, obj: Any) -> int:
        """Estimate token count for object"""
        text = json.dumps(obj, separators=(',', ':'))
        return len(text) // 4  # Rough estimation
    
    def reset_context(self):
        """Reset context for fresh start"""
        self.current_tokens = 0
        self.key_points = []
        self.action_items = []
        self.decisions_made = []
        self.files_created = []
        self.issues_identified = []
        
        logger.info("🔄 Context window reset")
    
    def get_status_report(self) -> Dict[str, Any]:
        """Get comprehensive context status report"""
        return {
            "current_tokens": self.current_tokens,
            "max_tokens": self.max_context_window,
            "usage_percentage": self.current_tokens / self.max_context_window,
            "status": self._get_context_status().value,
            "key_points_count": len(self.key_points),
            "action_items_count": len(self.action_items),
            "decisions_made_count": len(self.decisions_made),
            "files_created_count": len(self.files_created),
            "issues_identified_count": len(self.issues_identified),
            "snapshots_count": len(self.snapshots),
            "handoffs_count": len(self.handoff_packages),
            "warning_threshold": self.warning_threshold
        }

# ============================================================================
# CONTEXT-AWARE AGENT DECORATOR
# ============================================================================

def context_aware(max_context: int = 4096, warning_threshold: float = 0.75):
    """Decorator to make agents context-aware"""
    def decorator(cls):
        original_init = cls.__init__
        
        def new_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            self.context_manager = ContextWindowManager(max_context, warning_threshold)
            
            # Wrap methods to track context
            for attr_name in dir(self):
                attr = getattr(self, attr_name)
                if callable(attr) and not attr_name.startswith('_'):
                    setattr(self, attr_name, self._wrap_method(attr))
        
        cls.__init__ = new_init
        
        def _wrap_method(self, method):
            def wrapped_method(*args, **kwargs):
                # Estimate tokens for this call
                estimated_tokens = len(str(args) + str(kwargs)) // 4
                
                # Check context before execution
                handoff = self.context_manager.add_tokens(
                    estimated_tokens, 
                    method.__name__,
                    str(args) + str(kwargs)
                )
                
                if handoff:
                    logger.warning(f"🔄 Context handoff needed before {method.__name__}")
                    # In production, would pass handoff to next agent/instance
                
                return method(*args, **kwargs)
            
            return wrapped_method
        
        cls._wrap_method = _wrap_method
        return cls
    
    return decorator

# ============================================================================
# GLOBAL CONTEXT MANAGER
# ============================================================================

# Global context manager instance
global_context_manager = ContextWindowManager()

def add_context(tokens: int, content_type: str = "general", content: str = "") -> Optional[HandoffPackage]:
    """Add tokens to global context and check for handoff"""
    return global_context_manager.add_tokens(tokens, content_type, content)

def get_context_status() -> Dict[str, Any]:
    """Get global context status"""
    return global_context_manager.get_status_report()

def prepare_handoff() -> HandoffPackage:
    """Manually prepare handoff"""
    return global_context_manager.prepare_handoff()

def reset_context():
    """Reset global context"""
    global_context_manager.reset_context()

# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Example usage
    manager = ContextWindowManager(max_context_window=1000, warning_threshold=0.75)
    
    # Simulate adding context
    manager.add_tokens(100, "goal", "Goal: Build enhanced multi-agent system")
    manager.add_tokens(200, "action", "Action: Create multi-agent communication system")
    manager.add_tokens(300, "decision", "Decision: Use FastAPI for web interface")
    manager.add_tokens(200, "file", "Created: ENHANCED_MULTI_AGENT_SYSTEM.py")
    
    # Check status
    status = manager.get_status_report()
    print("Context Status:", json.dumps(status, indent=2))
    
    # Trigger handoff if needed
    if status["usage_percentage"] >= 0.75:
        handoff = manager.prepare_handoff()
        print("Handoff Package:", json.dumps(handoff.__dict__, indent=2))
