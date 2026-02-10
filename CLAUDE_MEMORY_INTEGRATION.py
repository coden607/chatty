#!/usr/bin/env python3
"""
Claude Memory Integration for Chatty
Persistent memory system with context management and learning
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
import hashlib

# Vector storage for semantic memory
try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

# Text embeddings for semantic search
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

# Async operations
try:
    import aiofiles
    AIOFILES_AVAILABLE = True
except ImportError:
    AIOFILES_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class MemoryItem:
    """Individual memory item"""
    id: str
    content: str
    timestamp: datetime
    importance: float  # 0.0 to 1.0
    tags: Set[str] = field(default_factory=set)
    embedding: Optional[List[float]] = None
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    context: Optional[str] = None
    source: str = "chatty"

@dataclass
class MemoryConfig:
    """Memory system configuration"""
    max_memories: int = 10000
    importance_threshold: float = 0.3
    semantic_threshold: float = 0.8
    retention_days: int = 90
    auto_cleanup: bool = True
    enable_semantic_search: bool = True

class ClaudeMemorySystem:
    """Claude-inspired memory system for Chatty"""
    
    def __init__(self, config: Optional[MemoryConfig] = None):
        self.config = config or MemoryConfig()
        self.memories: Dict[str, MemoryItem] = {}
        self.memory_file = Path("chatty_memory.json")
        self.vector_db = None
        self.embedding_model = None
        
        # Memory statistics
        self.stats = {
            "total_memories": 0,
            "memories_today": 0,
            "avg_importance": 0.0,
            "last_cleanup": None,
            "semantic_searches": 0
        }
        
        logger.info("🧠 Claude Memory System initialized for Chatty")
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize memory components"""
        # Load existing memories
        self._load_memories()
        
        # Initialize semantic search if available
        if self.config.enable_semantic_search:
            self._init_semantic_search()
        
        logger.info(f"✅ Memory system ready: {len(self.memories)} memories loaded")
    
    def _init_semantic_search(self):
        """Initialize semantic search capabilities"""
        try:
            # Initialize embedding model
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("✅ Sentence transformers loaded")
            
            # Initialize vector database
            if CHROMADB_AVAILABLE:
                self.vector_db = chromadb.Client()
                self.collection = self.vector_db.create_collection("chatty_memories")
                logger.info("✅ ChromaDB vector store initialized")
            else:
                logger.warning("⚠️ ChromaDB not available, semantic search limited")
                
        except Exception as e:
            logger.warning(f"⚠️ Semantic search initialization failed: {e}")
            self.config.enable_semantic_search = False
    
    async def add_memory(self, content: str, importance: float = 0.5, tags: Set[str] = None, 
                        context: str = None, source: str = "chatty") -> str:
        """Add a new memory item"""
        try:
            # Generate unique ID
            memory_id = self._generate_memory_id(content)
            
            # Create memory item
            memory = MemoryItem(
                id=memory_id,
                content=content,
                timestamp=datetime.now(),
                importance=min(max(importance, 0.0), 1.0),
                tags=tags or set(),
                context=context,
                source=source
            )
            
            # Generate embedding if semantic search enabled
            if self.config.enable_semantic_search and self.embedding_model:
                memory.embedding = self.embedding_model.encode(content).tolist()
            
            # Store memory
            self.memories[memory_id] = memory
            
            # Add to vector database
            if self.config.enable_semantic_search and hasattr(self, 'collection'):
                await self._add_to_vector_db(memory)
            
            # Update statistics
            self._update_stats()
            
            # Auto cleanup if needed
            if self.config.auto_cleanup and len(self.memories) > self.config.max_memories:
                await self._cleanup_memories()
            
            logger.info(f"✅ Memory added: {memory_id[:8]}... (importance: {importance})")
            return memory_id
            
        except Exception as e:
            logger.error(f"❌ Failed to add memory: {e}")
            return ""
    
    def _generate_memory_id(self, content: str) -> str:
        """Generate unique memory ID"""
        timestamp = datetime.now().isoformat()
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"mem_{timestamp}_{content_hash}"
    
    async def _add_to_vector_db(self, memory: MemoryItem):
        """Add memory to vector database"""
        try:
            if memory.embedding and hasattr(self, 'collection'):
                self.collection.add(
                    ids=[memory.id],
                    embeddings=[memory.embedding],
                    documents=[memory.content],
                    metadatas=[{
                        "timestamp": memory.timestamp.isoformat(),
                        "importance": memory.importance,
                        "tags": list(memory.tags),
                        "source": memory.source
                    }]
                )
        except Exception as e:
            logger.warning(f"⚠️ Failed to add to vector DB: {e}")
    
    async def search_memories(self, query: str, limit: int = 10, 
                            semantic: bool = True, tags: Set[str] = None) -> List[MemoryItem]:
        """Search memories"""
        try:
            results = []
            
            if semantic and self.config.enable_semantic_search and self.embedding_model:
                # Semantic search
                results = await self._semantic_search(query, limit)
                self.stats["semantic_searches"] += 1
            else:
                # Keyword search
                results = self._keyword_search(query, limit, tags)
            
            # Update access counts
            for memory in results:
                memory.access_count += 1
                memory.last_accessed = datetime.now()
            
            logger.info(f"🔍 Memory search: {len(results)} results for '{query[:30]}...'")
            return results
            
        except Exception as e:
            logger.error(f"❌ Memory search failed: {e}")
            return []
    
    async def _semantic_search(self, query: str, limit: int) -> List[MemoryItem]:
        """Perform semantic search"""
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Search vector database
            if hasattr(self, 'collection'):
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=limit
                )
                
                # Convert to MemoryItem objects
                memory_items = []
                for i, memory_id in enumerate(results['ids'][0]):
                    if memory_id in self.memories:
                        memory_items.append(self.memories[memory_id])
                
                return memory_items
            else:
                # Fallback to keyword search
                return self._keyword_search(query, limit)
                
        except Exception as e:
            logger.warning(f"⚠️ Semantic search failed: {e}")
            return self._keyword_search(query, limit)
    
    def _keyword_search(self, query: str, limit: int, tags: Set[str] = None) -> List[MemoryItem]:
        """Perform keyword search"""
        query_lower = query.lower()
        results = []
        
        for memory in self.memories.values():
            # Check content match
            content_match = query_lower in memory.content.lower()
            
            # Check tag match
            tag_match = not tags or tags.intersection(memory.tags)
            
            # Check importance threshold
            importance_ok = memory.importance >= self.config.importance_threshold
            
            if content_match and tag_match and importance_ok:
                results.append(memory)
        
        # Sort by importance and recency
        results.sort(key=lambda m: (m.importance, m.timestamp), reverse=True)
        
        return results[:limit]
    
    async def get_recent_memories(self, hours: int = 24, limit: int = 20) -> List[MemoryItem]:
        """Get recent memories"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_memories = [
            memory for memory in self.memories.values()
            if memory.timestamp > cutoff_time
        ]
        
        # Sort by timestamp
        recent_memories.sort(key=lambda m: m.timestamp, reverse=True)
        
        return recent_memories[:limit]
    
    async def get_important_memories(self, min_importance: float = 0.7, limit: int = 20) -> List[MemoryItem]:
        """Get important memories"""
        important_memories = [
            memory for memory in self.memories.values()
            if memory.importance >= min_importance
        ]
        
        # Sort by importance
        important_memories.sort(key=lambda m: m.importance, reverse=True)
        
        return important_memories[:limit]
    
    async def update_memory_importance(self, memory_id: str, new_importance: float) -> bool:
        """Update memory importance"""
        try:
            if memory_id in self.memories:
                old_importance = self.memories[memory_id].importance
                self.memories[memory_id].importance = min(max(new_importance, 0.0), 1.0)
                
                logger.info(f"📊 Memory importance updated: {memory_id[:8]}... {old_importance} → {new_importance}")
                return True
            else:
                logger.warning(f"⚠️ Memory not found: {memory_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to update memory importance: {e}")
            return False
    
    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory"""
        try:
            if memory_id in self.memories:
                # Remove from memories
                del self.memories[memory_id]
                
                # Remove from vector database
                if hasattr(self, 'collection'):
                    try:
                        self.collection.delete(ids=[memory_id])
                    except:
                        pass  # Vector DB deletion is optional
                
                logger.info(f"🗑️ Memory deleted: {memory_id[:8]}...")
                return True
            else:
                logger.warning(f"⚠️ Memory not found: {memory_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to delete memory: {e}")
            return False
    
    async def _cleanup_memories(self):
        """Cleanup old and low-importance memories"""
        try:
            cutoff_time = datetime.now() - timedelta(days=self.config.retention_days)
            
            # Find memories to delete
            to_delete = []
            for memory_id, memory in self.memories.items():
                should_delete = (
                    memory.timestamp < cutoff_time or
                    memory.importance < self.config.importance_threshold
                )
                if should_delete:
                    to_delete.append(memory_id)
            
            # Delete memories
            for memory_id in to_delete:
                await self.delete_memory(memory_id)
            
            self.stats["last_cleanup"] = datetime.now().isoformat()
            logger.info(f"🧹 Cleanup completed: {len(to_delete)} memories removed")
            
        except Exception as e:
            logger.error(f"❌ Memory cleanup failed: {e}")
    
    def _update_stats(self):
        """Update memory statistics"""
        self.stats["total_memories"] = len(self.memories)
        
        # Count today's memories
        today = datetime.now().date()
        today_memories = [
            memory for memory in self.memories.values()
            if memory.timestamp.date() == today
        ]
        self.stats["memories_today"] = len(today_memories)
        
        # Calculate average importance
        if self.memories:
            avg_importance = sum(m.importance for m in self.memories.values()) / len(self.memories)
            self.stats["avg_importance"] = avg_importance
    
    def _load_memories(self):
        """Load memories from file"""
        try:
            if self.memory_file.exists():
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Convert to MemoryItem objects
                for memory_data in data.get('memories', []):
                    memory = MemoryItem(
                        id=memory_data['id'],
                        content=memory_data['content'],
                        timestamp=datetime.fromisoformat(memory_data['timestamp']),
                        importance=memory_data['importance'],
                        tags=set(memory_data.get('tags', [])),
                        access_count=memory_data.get('access_count', 0),
                        last_accessed=datetime.fromisoformat(memory_data['last_accessed']) if memory_data.get('last_accessed') else None,
                        context=memory_data.get('context'),
                        source=memory_data.get('source', 'chatty')
                    )
                    self.memories[memory.id] = memory
                
                logger.info(f"✅ Loaded {len(self.memories)} memories from file")
                
        except Exception as e:
            logger.warning(f"⚠️ Failed to load memories: {e}")
    
    async def save_memories(self):
        """Save memories to file"""
        try:
            # Convert to serializable format
            memories_data = []
            for memory in self.memories.values():
                memory_dict = {
                    'id': memory.id,
                    'content': memory.content,
                    'timestamp': memory.timestamp.isoformat(),
                    'importance': memory.importance,
                    'tags': list(memory.tags),
                    'access_count': memory.access_count,
                    'last_accessed': memory.last_accessed.isoformat() if memory.last_accessed else None,
                    'context': memory.context,
                    'source': memory.source
                }
                memories_data.append(memory_dict)
            
            # Save to file
            data = {
                'memories': memories_data,
                'stats': self.stats,
                'config': {
                    'max_memories': self.config.max_memories,
                    'importance_threshold': self.config.importance_threshold,
                    'retention_days': self.config.retention_days
                },
                'last_saved': datetime.now().isoformat()
            }
            
            if AIOFILES_AVAILABLE:
                async with aiofiles.open(self.memory_file, 'w', encoding='utf-8') as f:
                    await f.write(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                with open(self.memory_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Saved {len(self.memories)} memories to file")
            
        except Exception as e:
            logger.error(f"❌ Failed to save memories: {e}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        self._update_stats()
        
        # Additional statistics
        if self.memories:
            most_accessed = max(self.memories.values(), key=lambda m: m.access_count)
            most_important = max(self.memories.values(), key=lambda m: m.importance)
            
            self.stats.update({
                "most_accessed_memory": most_accessed.id[:8] + "...",
                "most_important_memory": most_important.id[:8] + "...",
                "total_accesses": sum(m.access_count for m in self.memories.values()),
                "unique_tags": len(set().union(*[m.tags for m in self.memories.values()]))
            })
        
        return self.stats.copy()

# ============================================================================
# CHATTY MEMORY INTEGRATION
# ============================================================================

class ChattyMemoryIntegration:
    """Integrates Claude Memory System with Chatty"""
    
    def __init__(self):
        self.memory_system = ClaudeMemorySystem()
        self.learning_enabled = True
        
        logger.info("🧠 Chatty Memory Integration initialized")
    
    async def learn_from_interaction(self, interaction: Dict[str, Any]) -> str:
        """Learn from user interaction"""
        try:
            # Extract key information
            user_input = interaction.get('user_input', '')
            chatty_response = interaction.get('chatty_response', '')
            context = interaction.get('context', '')
            
            # Create memory content
            memory_content = f"User: {user_input}\nChatty: {chatty_response}"
            if context:
                memory_content = f"Context: {context}\n{memory_content}"
            
            # Calculate importance based on interaction
            importance = self._calculate_interaction_importance(interaction)
            
            # Extract tags
            tags = self._extract_interaction_tags(interaction)
            
            # Add to memory
            memory_id = await self.memory_system.add_memory(
                content=memory_content,
                importance=importance,
                tags=tags,
                context=context,
                source="user_interaction"
            )
            
            logger.info(f"🧠 Learned from interaction: {memory_id[:8]}...")
            return memory_id
            
        except Exception as e:
            logger.error(f"❌ Failed to learn from interaction: {e}")
            return ""
    
    def _calculate_interaction_importance(self, interaction: Dict[str, Any]) -> float:
        """Calculate importance score for interaction"""
        importance = 0.5  # Base importance
        
        user_input = interaction.get('user_input', '').lower()
        chatty_response = interaction.get('chatty_response', '').lower()
        
        # Increase importance for certain patterns
        if any(keyword in user_input for keyword in ['important', 'remember', 'note', 'critical']):
            importance += 0.2
        
        if any(keyword in user_input for keyword in ['error', 'fix', 'problem', 'issue']):
            importance += 0.15
        
        if len(user_input) > 100:  # Longer interactions
            importance += 0.1
        
        if any(keyword in chatty_response for keyword in ['solution', 'fixed', 'resolved', 'success']):
            importance += 0.15
        
        return min(importance, 1.0)
    
    def _extract_interaction_tags(self, interaction: Dict[str, Any]) -> Set[str]:
        """Extract tags from interaction"""
        tags = set()
        
        user_input = interaction.get('user_input', '').lower()
        chatty_response = interaction.get('chatty_response', '').lower()
        
        # Common tags
        if 'error' in user_input or 'error' in chatty_response:
            tags.add('error')
        
        if 'fix' in user_input or 'fixed' in chatty_response:
            tags.add('solution')
        
        if 'automation' in user_input or 'automation' in chatty_response:
            tags.add('automation')
        
        if 'agent' in user_input or 'agent' in chatty_response:
            tags.add('agent')
        
        if 'cole medin' in user_input or 'cole medin' in chatty_response:
            tags.add('cole_medin')
        
        return tags
    
    async def recall_relevant_memories(self, query: str, context: str = "") -> List[Dict[str, Any]]:
        """Recall memories relevant to current context"""
        try:
            # Search memories
            memories = await self.memory_system.search_memories(query, limit=5)
            
            # Format for use
            relevant_memories = []
            for memory in memories:
                relevant_memories.append({
                    'content': memory.content,
                    'importance': memory.importance,
                    'timestamp': memory.timestamp.isoformat(),
                    'tags': list(memory.tags),
                    'source': memory.source
                })
            
            logger.info(f"🧠 Recalled {len(relevant_memories)} relevant memories")
            return relevant_memories
            
        except Exception as e:
            logger.error(f"❌ Failed to recall memories: {e}")
            return []
    
    async def get_memory_summary(self) -> Dict[str, Any]:
        """Get memory system summary"""
        stats = self.memory_system.get_memory_stats()
        
        # Get recent memories
        recent_memories = await self.memory_system.get_recent_memories(hours=24, limit=5)
        
        # Get important memories
        important_memories = await self.memory_system.get_important_memories(limit=5)
        
        return {
            'stats': stats,
            'recent_memories': [
                {
                    'id': m.id[:8] + '...',
                    'content': m.content[:100] + '...',
                    'importance': m.importance,
                    'timestamp': m.timestamp.isoformat()
                }
                for m in recent_memories
            ],
            'important_memories': [
                {
                    'id': m.id[:8] + '...',
                    'content': m.content[:100] + '...',
                    'importance': m.importance,
                    'tags': list(m.tags)
                }
                for m in important_memories
            ]
        }

# ============================================================================
# DEMONSTRATION
# ============================================================================

async def demonstrate_claude_memory():
    """Demonstrate Claude Memory System"""
    print("🧠 Claude Memory System for Chatty")
    print("=" * 50)
    
    # Initialize memory integration
    chatty_memory = ChattyMemoryIntegration()
    
    # Add some sample memories
    print("📝 Adding sample memories...")
    
    sample_interactions = [
        {
            'user_input': 'How do I fix the agent communication error?',
            'chatty_response': 'You need to update the communication protocol in the ENHANCED_MULTI_AGENT_SYSTEM.py file',
            'context': 'debugging'
        },
        {
            'user_input': 'Cole Medin mentioned Agent Zero fleet management',
            'chatty_response': 'I should integrate Agent Zero techniques into Chatty for better coordination',
            'context': 'learning'
        },
        {
            'user_input': 'The YouTube transcription is not working',
            'chatty_response': 'Use TranscriptAPI.com for reliable transcription service',
            'context': 'troubleshooting'
        }
    ]
    
    memory_ids = []
    for interaction in sample_interactions:
        memory_id = await chatty_memory.learn_from_interaction(interaction)
        if memory_id:
            memory_ids.append(memory_id)
    
    print(f"✅ Added {len(memory_ids)} memories")
    
    # Search memories
    print("\n🔍 Searching memories...")
    search_results = await chatty_memory.recall_relevant_memories("agent communication")
    
    for result in search_results:
        print(f"📄 {result['content'][:80]}... (importance: {result['importance']})")
    
    # Get memory summary
    print("\n📊 Memory Summary:")
    summary = await chatty_memory.get_memory_summary()
    print(f"Total memories: {summary['stats']['total_memories']}")
    print(f"Memories today: {summary['stats']['memories_today']}")
    print(f"Average importance: {summary['stats']['avg_importance']:.2f}")
    
    # Save memories
    await chatty_memory.memory_system.save_memories()
    print("\n💾 Memories saved to chatty_memory.json")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    asyncio.run(demonstrate_claude_memory())
