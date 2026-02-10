#!/usr/bin/env python3
"""
Chatty Agent Memory System
Uses ChromaDB to provide long-term memory and learning capabilities to AI agents.
Agents can store experiences, retrieve successful strategies, and avoid past mistakes.
"""

import os
import chromadb
from chromadb.config import Settings
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentMemory:
    """Long-term memory for AI agents using Vector Database"""
    
    def __init__(self, persistence_path="/home/coden809/CHATTY/chroma_db"):
        telemetry_disabled = os.getenv("CHATTY_DISABLE_TELEMETRY", "true").lower() in ("1", "true", "yes")
        settings = Settings(anonymized_telemetry=not telemetry_disabled)
        self.client = chromadb.PersistentClient(path=persistence_path, settings=settings)
        
        # Initialize collections for different types of memory
        self.strategies = self.client.get_or_create_collection("successful_strategies")
        self.content_performance = self.client.get_or_create_collection("content_performance")
        self.market_insights = self.client.get_or_create_collection("market_insights")
        self.failed_experiments = self.client.get_or_create_collection("failed_experiments")
        
        logger.info("🧠 Agent Memory System Initialized (ChromaDB)")

    def record_successful_strategy(self, agent_role: str, strategy: str, outcome: Dict[str, Any], impact_score: float):
        """Record a strategy that worked well"""
        try:
            timestamp = datetime.now().isoformat()
            
            # Create a rich text description for vector embedding
            document = f"{agent_role} used strategy: {strategy}. Outcome: {json.dumps(outcome)}. Impact: {impact_score}/10"
            
            self.strategies.add(
                documents=[document],
                metadatas=[{
                    "agent": agent_role,
                    "impact": impact_score,
                    "timestamp": timestamp,
                    "type": "success"
                }],
                ids=[f"strat_{timestamp}_{agent_role}"]
            )
            logger.info(f"🧠 Memory: Recorded successful strategy by {agent_role}")
            
        except Exception as e:
            logger.error(f"Failed to record strategy: {e}")

    def record_content_performance(self, content_type: str, topic: str, content_preview: str, metrics: Dict[str, Any]):
        """Record how a piece of content performed"""
        try:
            timestamp = datetime.now().isoformat()
            
            # Calculate an aggregate score (0-1) based on metrics
            score = self._calculate_performance_score(metrics)
            
            document = f"Type: {content_type}. Topic: {topic}. Content: {content_preview}. Metrics: {json.dumps(metrics)}"
            
            self.content_performance.add(
                documents=[document],
                metadatas=[{
                    "type": content_type,
                    "topic": topic,
                    "score": score,
                    "timestamp": timestamp
                }],
                ids=[f"cont_{timestamp}_{content_type}"]
            )
            logger.info(f"🧠 Memory: Recorded content performance (Score: {score:.2f})")
            
        except Exception as e:
            logger.error(f"Failed to record content performance: {e}")

    def record_failure(self, agent_role: str, action: str, error: str, lessons_learned: str):
        """Record a failure to avoid repeating it"""
        try:
            timestamp = datetime.now().isoformat()
            
            document = f"{agent_role} failed at {action}. Error: {error}. Lesson: {lessons_learned}"
            
            self.failed_experiments.add(
                documents=[document],
                metadatas=[{
                    "agent": agent_role,
                    "action": action,
                    "timestamp": timestamp,
                    "type": "failure"
                }],
                ids=[f"fail_{timestamp}_{agent_role}"]
            )
            logger.info(f"🧠 Memory: Recorded failure lesson for {agent_role}")
            
        except Exception as e:
            logger.error(f"Failed to record failure: {e}")

    def recall_winning_strategies(self, context: str, n_results: int = 3) -> List[str]:
        """Retrieve relevant successful strategies for a current problem"""
        try:
            results = self.strategies.query(
                query_texts=[context],
                n_results=n_results
            )
            
            if results and results['documents']:
                logger.info(f"💡 Memory: Recalled {len(results['documents'][0])} relevant strategies")
                return results['documents'][0]
            return []
            
        except Exception as e:
            logger.error(f"Failed to recall strategies: {e}")
            return []

    def recall_high_performing_content(self, topic: str, n_results: int = 3) -> List[str]:
        """Find past content about this topic that performed well"""
        try:
            results = self.content_performance.query(
                query_texts=[f"High performing content about {topic}"],
                where={"score": {"$gt": 0.7}}, # Only recall good stuff
                n_results=n_results
            )
            
            if results and results['documents']:
                return results['documents'][0]
            return []
            
        except Exception as e:
            logger.error(f"Failed to recall content: {e}")
            return []

    def check_for_past_failures(self, proposed_action: str) -> List[str]:
        """Check if this action has failed before"""
        try:
            results = self.failed_experiments.query(
                query_texts=[proposed_action],
                n_results=1
            )
            
            # Simple threshold check - if distance is close, it might be the same mistake
            if results and results['documents']:
                logger.warning(f"⚠️ Memory: Found similar past failure for '{proposed_action}'")
                return results['documents'][0]
            return []
            
        except Exception as e:
            logger.error(f"Failed to check failures: {e}")
            return []

    def _calculate_performance_score(self, metrics: Dict[str, Any]) -> float:
        """Normalize metrics to a 0-1 score"""
        # Simplified scoring logic
        views = metrics.get('views', 0)
        clicks = metrics.get('clicks', 0)
        conversions = metrics.get('conversions', 0)
        
        # Weighted score (example weights)
        raw_score = (views * 0.01) + (clicks * 0.1) + (conversions * 1.0)
        
        # Normalize (assuming 100 is a "great" raw score for this example)
        return min(raw_score / 100.0, 1.0)

# Global instance
agent_memory = AgentMemory()

if __name__ == "__main__":
    # Test the memory system
    print("🧠 Testing Agent Memory System...")
    
    # record a fake success
    agent_memory.record_successful_strategy(
        "Content Creator",
        "Use 'How-to' titles with numbers",
        {"ctr": 0.15, "leads": 25},
        0.85
    )
    
    # record a fake failure
    agent_memory.record_failure(
        "Ad Specialist",
        "Target generic 'business' keyword on LinkedIn",
        "Cost per click too high ($15)",
        "Too broad, need specific industry targeting"
    )
    
    # Recall
    print("\n🔍 Recalling strategies for 'blog titles':")
    strategies = agent_memory.recall_winning_strategies("blog post title optimization")
    for s in strategies:
        print(f" - {s}")
        
    print("\n✅ Memory check complete")
