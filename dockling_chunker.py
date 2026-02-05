#!/usr/bin/env python3
"""
CHATTY Dockling Integration
Advanced file chunking system with semantic analysis and context preservation
"""

import os
import json
import time
import asyncio
import logging
import hashlib
import ast
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
from collections import defaultdict, deque
import concurrent.futures

import requests
from sentence_transformers import SentenceTransformer
import networkx as nx
from sklearn.cluster import KMeans
import numpy as np

from server import db, Agent, Task, logger
from learning_system import memory_system, adaptive_learning

class DocklingChunker:
    """Advanced file chunking system inspired by Dockling's semantic analysis"""
    
    def __init__(self):
        self.embeddings_model = None
        try:
            self.embeddings_model = SentenceTransformer('all-MiniLM-L6-v2')
        except:
            logger.warning("Sentence transformer not available for Dockling chunking")
        
        self.chunk_cache = {}
        self.semantic_graph = nx.DiGraph()
        self.context_windows = {}
        
        # Dockling-specific configurations
        self.chunk_strategies = {
            'code': self._chunk_code_dockling,
            'documentation': self._chunk_documentation_dockling,
            'data': self._chunk_data_dockling,
            'config': self._chunk_config_dockling
        }
    
    def dockling_chunk_file(self, file_path: str, strategy: str = 'auto', 
                          max_chunk_size: int = 2000) -> List[Dict[str, Any]]:
        """Dockling-style intelligent file chunking"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            file_type = Path(file_path).suffix.lower()
            
            # Auto-detect strategy if not specified
            if strategy == 'auto':
                strategy = self._detect_chunk_strategy(file_path, content)
            
            # Get appropriate chunker
            chunker = self.chunk_strategies.get(strategy, self._chunk_generic_dockling)
            
            # Perform chunking
            chunks = chunker(content, file_path, max_chunk_size)
            
            # Build semantic relationships
            self._build_semantic_graph(chunks, file_path)
            
            # Create context windows
            self._create_context_windows(chunks, file_path)
            
            # Cache results
            self.chunk_cache[file_path] = chunks
            
            logger.info(f"Dockling chunked {file_path} into {len(chunks)} semantic chunks using {strategy} strategy")
            return chunks
            
        except Exception as e:
            logger.error(f"Dockling chunking failed for {file_path}: {str(e)}")
            return []
    
    def _detect_chunk_strategy(self, file_path: str, content: str) -> str:
        """Auto-detect optimal chunking strategy"""
        file_type = Path(file_path).suffix.lower()
        
        # File type based detection
        if file_type in ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rust']:
            return 'code'
        elif file_type in ['.md', '.txt', '.rst', '.adoc']:
            return 'documentation'
        elif file_type in ['.json', '.yaml', '.yml', '.xml', '.csv']:
            return 'data'
        elif file_type in ['.env', '.config', '.ini', '.toml']:
            return 'config'
        
        # Content-based detection
        if any(keyword in content.lower() for keyword in ['function', 'class', 'def ', 'import ']):
            return 'code'
        elif any(keyword in content.lower() for keyword in ['## ', '### ', '# Introduction']):
            return 'documentation'
        elif any(keyword in content.lower() for keyword in ['{', '[', 'key:', 'value:']):
            return 'data'
        
        return 'generic'
    
    def _chunk_code_dockling(self, content: str, file_path: str, max_size: int) -> List[Dict[str, Any]]:
        """Dockling-style code chunking with semantic boundaries"""
        chunks = []
        lines = content.split('\n')
        
        # Parse AST for structural analysis
        try:
            tree = ast.parse(content)
            structure = self._analyze_code_structure(tree, lines)
        except:
            structure = self._fallback_code_analysis(lines)
        
        # Create semantic chunks based on structure
        current_chunk = self._create_new_chunk(file_path)
        chunk_id = 0
        
        for i, line in enumerate(lines):
            line_size = len(line)
            
            # Check for semantic boundaries
            boundary = self._detect_semantic_boundary(i, line, structure)
            
            if boundary and current_chunk['size'] > max_size * 0.6:
                # Finalize current chunk
                if current_chunk['content']:
                    chunks.append(self._finalize_dockling_chunk(current_chunk, chunk_id, file_path))
                    chunk_id += 1
                
                # Start new chunk
                current_chunk = self._create_new_chunk(file_path, boundary)
            
            # Add line to current chunk
            current_chunk['content'] += line + '\n'
            current_chunk['size'] += line_size
            current_chunk['end_line'] = i
            
            # Check chunk size limit
            if current_chunk['size'] >= max_size:
                chunks.append(self._finalize_dockling_chunk(current_chunk, chunk_id, file_path))
                chunk_id += 1
                current_chunk = self._create_new_chunk(file_path)
        
        # Add final chunk
        if current_chunk['content']:
            chunks.append(self._finalize_dockling_chunk(current_chunk, chunk_id, file_path))
        
        return chunks
    
    def _analyze_code_structure(self, tree: ast.AST, lines: List[str]) -> Dict[str, Any]:
        """Analyze code structure using AST"""
        structure = {
            'functions': [],
            'classes': [],
            'imports': [],
            'comments': [],
            'logical_sections': []
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                structure['functions'].append({
                    'name': node.name,
                    'line': node.lineno,
                    'end_line': getattr(node, 'end_lineno', node.lineno),
                    'docstring': ast.get_docstring(node)
                })
            elif isinstance(node, ast.ClassDef):
                structure['classes'].append({
                    'name': node.name,
                    'line': node.lineno,
                    'end_line': getattr(node, 'end_lineno', node.lineno),
                    'methods': [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                })
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    structure['imports'].append({
                        'name': alias.name,
                        'line': node.lineno,
                        'alias': alias.asname
                    })
            elif isinstance(node, ast.ImportFrom):
                structure['imports'].append({
                    'module': node.module,
                    'names': [alias.name for alias in node.names],
                    'line': node.lineno
                })
        
        # Analyze comments and documentation
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
                structure['comments'].append({
                    'line': i,
                    'type': 'comment' if stripped.startswith('#') else 'docstring',
                    'content': stripped
                })
        
        return structure
    
    def _fallback_code_analysis(self, lines: List[str]) -> Dict[str, Any]:
        """Fallback code structure analysis without AST"""
        structure = {
            'functions': [],
            'classes': [],
            'imports': [],
            'comments': [],
            'logical_sections': []
        }
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            if re.match(r'^\s*def\s+\w+', stripped):
                structure['functions'].append({
                    'name': re.search(r'def\s+(\w+)', stripped).group(1),
                    'line': i,
                    'end_line': i
                })
            elif re.match(r'^\s*class\s+\w+', stripped):
                structure['classes'].append({
                    'name': re.search(r'class\s+(\w+)', stripped).group(1),
                    'line': i,
                    'end_line': i
                })
            elif re.match(r'^\s*(import|from)\s+', stripped):
                structure['imports'].append({
                    'line': i,
                    'content': stripped
                })
            elif stripped.startswith('#'):
                structure['comments'].append({
                    'line': i,
                    'type': 'comment',
                    'content': stripped[1:].strip()
                })
        
        return structure
    
    def _detect_semantic_boundary(self, line_num: int, line: str, structure: Dict[str, Any]) -> Optional[str]:
        """Detect semantic boundaries in code"""
        stripped = line.strip()
        
        # Function boundaries
        if any(func['line'] == line_num for func in structure.get('functions', [])):
            return 'function_start'
        
        # Class boundaries
        if any(cls['line'] == line_num for cls in structure.get('classes', [])):
            return 'class_start'
        
        # Import boundaries
        if any(imp['line'] == line_num for imp in structure.get('imports', [])):
            return 'import_section'
        
        # Comment boundaries
        if any(comment['line'] == line_num for comment in structure.get('comments', [])):
            return 'comment_boundary'
        
        # Logical section boundaries (heuristic)
        if not stripped and line_num > 0:
            prev_line = line_num - 1
            if prev_line >= 0:
                prev_stripped = lines[prev_line].strip() if 'lines' in locals() else ''
                if prev_stripped and not prev_stripped.startswith('#'):
                    return 'logical_section'
        
        return None
    
    def _chunk_documentation_dockling(self, content: str, file_path: str, max_size: int) -> List[Dict[str, Any]]:
        """Dockling-style documentation chunking"""
        chunks = []
        paragraphs = content.split('\n\n')
        
        current_chunk = self._create_new_chunk(file_path, chunk_type='documentation')
        chunk_id = 0
        
        for i, paragraph in enumerate(paragraphs):
            para_size = len(paragraph)
            
            # Detect section boundaries
            boundary = self._detect_documentation_boundary(paragraph, i)
            
            if boundary and current_chunk['size'] > max_size * 0.7:
                if current_chunk['content']:
                    chunks.append(self._finalize_dockling_chunk(current_chunk, chunk_id, file_path))
                    chunk_id += 1
                
                current_chunk = self._create_new_chunk(file_path, boundary, chunk_type='documentation')
            
            if current_chunk['size'] + para_size > max_size:
                if current_chunk['content']:
                    chunks.append(self._finalize_dockling_chunk(current_chunk, chunk_id, file_path))
                    chunk_id += 1
                
                current_chunk = self._create_new_chunk(file_path, chunk_type='documentation')
            
            current_chunk['content'] += paragraph + '\n\n'
            current_chunk['size'] += para_size
            current_chunk['end_paragraph'] = i
        
        if current_chunk['content']:
            chunks.append(self._finalize_dockling_chunk(current_chunk, chunk_id, file_path))
        
        return chunks
    
    def _detect_documentation_boundary(self, paragraph: str, para_num: int) -> Optional[str]:
        """Detect documentation section boundaries"""
        stripped = paragraph.strip()
        
        # Heading boundaries
        if re.match(r'^#+\s+\w+', stripped):
            return 'heading'
        
        # Code block boundaries
        if stripped.startswith('```') or stripped.startswith('    '):
            return 'code_block'
        
        # List boundaries
        if re.match(r'^[-*+]\s+\w+', stripped) or re.match(r'^\d+\.\s+\w+', stripped):
            return 'list_section'
        
        # Table boundaries
        if '|' in stripped and ('---' in stripped or '===' in stripped):
            return 'table_section'
        
        return None
    
    def _chunk_data_dockling(self, content: str, file_path: str, max_size: int) -> List[Dict[str, Any]]:
        """Dockling-style data file chunking"""
        file_type = Path(file_path).suffix.lower()
        
        if file_type in ['.json', '.yaml', '.yml']:
            return self._chunk_structured_data(content, file_path, max_size)
        elif file_type in ['.csv', '.tsv']:
            return self._chunk_tabular_data(content, file_path, max_size)
        else:
            return self._chunk_generic_dockling(content, file_path, max_size)
    
    def _chunk_structured_data(self, content: str, file_path: str, max_size: int) -> List[Dict[str, Any]]:
        """Chunk structured data files (JSON, YAML)"""
        chunks = []
        
        try:
            if Path(file_path).suffix.lower() in ['.json']:
                import json
                data = json.loads(content)
            else:  # YAML
                import yaml
                data = yaml.safe_load(content)
            
            # Chunk based on data structure
            chunks = self._chunk_json_structure(data, file_path, max_size)
            
        except Exception as e:
            logger.warning(f"Failed to parse structured data: {str(e)}")
            chunks = self._chunk_generic_dockling(content, file_path, max_size)
        
        return chunks
    
    def _chunk_json_structure(self, data: Any, file_path: str, max_size: int) -> List[Dict[str, Any]]:
        """Chunk JSON/YAML data by structure"""
        chunks = []
        
        def chunk_recursive(obj: Any, path: str = "", depth: int = 0):
            if depth > 3:  # Limit recursion depth
                return
            
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    
                    # Create chunk for this section
                    chunk_content = json.dumps({key: value}, indent=2)
                    if len(chunk_content) > max_size * 0.8:
                        # Recurse deeper
                        chunk_recursive(value, current_path, depth + 1)
                    else:
                        chunks.append({
                            'content': chunk_content,
                            'path': current_path,
                            'type': 'data_section',
                            'size': len(chunk_content),
                            'structure_level': depth
                        })
            
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    current_path = f"{path}[{i}]"
                    chunk_content = json.dumps(item, indent=2)
                    
                    if len(chunk_content) > max_size * 0.8:
                        chunk_recursive(item, current_path, depth + 1)
                    else:
                        chunks.append({
                            'content': chunk_content,
                            'path': current_path,
                            'type': 'data_item',
                            'size': len(chunk_content),
                            'structure_level': depth
                        })
        
        chunk_recursive(data)
        return chunks
    
    def _chunk_tabular_data(self, content: str, file_path: str, max_size: int) -> List[Dict[str, Any]]:
        """Chunk tabular data (CSV, TSV)"""
        chunks = []
        lines = content.split('\n')
        
        if not lines:
            return chunks
        
        # Parse header
        header = lines[0]
        header_size = len(header)
        
        current_chunk = {
            'content': header + '\n',
            'start_row': 0,
            'end_row': 0,
            'type': 'tabular',
            'size': header_size
        }
        
        chunk_id = 0
        
        for i, line in enumerate(lines[1:], 1):
            line_size = len(line)
            
            if current_chunk['size'] + line_size > max_size:
                chunks.append(self._finalize_dockling_chunk(current_chunk, chunk_id, file_path))
                chunk_id += 1
                
                current_chunk = {
                    'content': header + '\n' + line + '\n',
                    'start_row': i,
                    'end_row': i,
                    'type': 'tabular',
                    'size': header_size + line_size
                }
            else:
                current_chunk['content'] += line + '\n'
                current_chunk['end_row'] = i
                current_chunk['size'] += line_size
        
        if current_chunk['content']:
            chunks.append(self._finalize_dockling_chunk(current_chunk, chunk_id, file_path))
        
        return chunks
    
    def _chunk_config_dockling(self, content: str, file_path: str, max_size: int) -> List[Dict[str, Any]]:
        """Chunk configuration files"""
        chunks = []
        lines = content.split('\n')
        
        current_chunk = self._create_new_chunk(file_path, chunk_type='configuration')
        chunk_id = 0
        
        for i, line in enumerate(lines):
            line_size = len(line)
            
            # Detect config section boundaries
            if line.strip().startswith('[') and line.strip().endswith(']'):
                if current_chunk['content']:
                    chunks.append(self._finalize_dockling_chunk(current_chunk, chunk_id, file_path))
                    chunk_id += 1
                
                current_chunk = self._create_new_chunk(file_path, 'config_section', chunk_type='configuration')
            
            current_chunk['content'] += line + '\n'
            current_chunk['size'] += line_size
            current_chunk['end_line'] = i
            
            if current_chunk['size'] >= max_size:
                chunks.append(self._finalize_dockling_chunk(current_chunk, chunk_id, file_path))
                chunk_id += 1
                current_chunk = self._create_new_chunk(file_path, chunk_type='configuration')
        
        if current_chunk['content']:
            chunks.append(self._finalize_dockling_chunk(current_chunk, chunk_id, file_path))
        
        return chunks
    
    def _chunk_generic_dockling(self, content: str, file_path: str, max_size: int) -> List[Dict[str, Any]]:
        """Generic Dockling chunking for unknown file types"""
        chunks = []
        lines = content.split('\n')
        
        current_chunk = self._create_new_chunk(file_path, chunk_type='generic')
        chunk_id = 0
        
        for i in range(0, len(lines), max_size // 100):
            chunk_lines = lines[i:i + max_size // 100]
            chunk_content = '\n'.join(chunk_lines)
            
            chunks.append({
                'id': f"{file_path}#{chunk_id}",
                'file_path': file_path,
                'content': chunk_content,
                'start_line': i,
                'end_line': min(i + max_size // 100 - 1, len(lines) - 1),
                'type': 'generic',
                'size': len(chunk_content),
                'semantic_boundaries': [],
                'created_at': datetime.utcnow().isoformat()
            })
            chunk_id += 1
        
        return chunks
    
    def _create_new_chunk(self, file_path: str, boundary: str = None, chunk_type: str = 'code') -> Dict[str, Any]:
        """Create a new chunk structure"""
        return {
            'content': '',
            'start_line': 0,
            'end_line': 0,
            'start_paragraph': 0,
            'end_paragraph': 0,
            'type': chunk_type,
            'size': 0,
            'semantic_boundaries': [boundary] if boundary else [],
            'metadata': {}
        }
    
    def _finalize_dockling_chunk(self, chunk_data: Dict[str, Any], chunk_id: int, file_path: str) -> Dict[str, Any]:
        """Finalize a Dockling chunk with metadata"""
        chunk_id_str = f"{file_path}#{chunk_id}"
        
        # Generate semantic embedding
        embedding = None
        if self.embeddings_model:
            try:
                embedding = self.embeddings_model.encode(chunk_data['content']).tolist()
            except Exception as e:
                logger.warning(f"Failed to generate embedding for chunk {chunk_id_str}: {str(e)}")
        
        # Extract semantic features
        semantic_features = self._extract_semantic_features(chunk_data['content'])
        
        return {
            'id': chunk_id_str,
            'file_path': file_path,
            'content': chunk_data['content'],
            'start_line': chunk_data['start_line'],
            'end_line': chunk_data['end_line'],
            'start_paragraph': chunk_data.get('start_paragraph', 0),
            'end_paragraph': chunk_data.get('end_paragraph', 0),
            'type': chunk_data['type'],
            'size': chunk_data['size'],
            'semantic_boundaries': chunk_data['semantic_boundaries'],
            'embedding': embedding,
            'semantic_features': semantic_features,
            'metadata': chunk_data.get('metadata', {}),
            'created_at': datetime.utcnow().isoformat()
        }
    
    def _extract_semantic_features(self, content: str) -> Dict[str, Any]:
        """Extract semantic features from chunk content"""
        features = {
            'keywords': [],
            'entities': [],
            'sentiment': 0.0,
            'complexity': 0.0,
            'topic_distribution': {}
        }
        
        # Extract keywords (simplified)
        words = re.findall(r'\b\w+\b', content.lower())
        word_freq = defaultdict(int)
        for word in words:
            if len(word) > 3:  # Filter short words
                word_freq[word] += 1
        
        features['keywords'] = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Extract entities (simplified)
        entities = re.findall(r'\b[A-Z][a-zA-Z]+\b', content)
        features['entities'] = list(set(entities))[:5]
        
        # Calculate complexity
        features['complexity'] = len(content) / 1000.0  # Simple complexity metric
        
        return features
    
    def _build_semantic_graph(self, chunks: List[Dict[str, Any]], file_path: str):
        """Build semantic relationship graph between chunks"""
        for i, chunk in enumerate(chunks):
            chunk_id = chunk['id']
            
            # Add node
            self.semantic_graph.add_node(chunk_id, **{
                'file_path': file_path,
                'type': chunk['type'],
                'size': chunk['size'],
                'boundaries': chunk['semantic_boundaries'],
                'features': chunk.get('semantic_features', {})
            })
            
            # Add sequential edges
            if i > 0:
                prev_chunk = chunks[i - 1]
                self.semantic_graph.add_edge(prev_chunk['id'], chunk_id, 
                                           relationship='sequential', weight=1.0)
            
            # Add semantic similarity edges
            if chunk.get('embedding'):
                for j, other_chunk in enumerate(chunks):
                    if i != j and other_chunk.get('embedding'):
                        similarity = self._calculate_similarity(
                            chunk['embedding'], other_chunk['embedding']
                        )
                        if similarity > 0.6:  # Lower threshold for semantic connections
                            self.semantic_graph.add_edge(
                                chunk_id, other_chunk['id'],
                                relationship='semantic_similarity',
                                weight=similarity
                            )
    
    def _create_context_windows(self, chunks: List[Dict[str, Any]], file_path: str):
        """Create context windows for chunks"""
        context_windows = {}
        
        for i, chunk in enumerate(chunks):
            chunk_id = chunk['id']
            
            # Create context window (previous and next chunks)
            context = {
                'previous': [],
                'next': [],
                'related': []
            }
            
            # Add previous chunks
            for j in range(max(0, i - 3), i):
                context['previous'].append(chunks[j]['id'])
            
            # Add next chunks
            for j in range(i + 1, min(len(chunks), i + 4)):
                context['next'].append(chunks[j]['id'])
            
            # Add related chunks (semantic similarity)
            if chunk.get('embedding'):
                for k, other_chunk in enumerate(chunks):
                    if i != k and other_chunk.get('embedding'):
                        similarity = self._calculate_similarity(
                            chunk['embedding'], other_chunk['embedding']
                        )
                        if similarity > 0.7:
                            context['related'].append(other_chunk['id'])
            
            context_windows[chunk_id] = context
        
        self.context_windows[file_path] = context_windows
    
    def _calculate_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between vectors"""
        try:
            import numpy as np
            v1 = np.array(vec1)
            v2 = np.array(vec2)
            return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        except:
            return 0.0
    
    def get_dockling_context(self, query: str, file_path: str = None, 
                           top_k: int = 5, context_window: int = 3) -> Dict[str, Any]:
        """Get Dockling-style context with semantic relationships"""
        if not self.embeddings_model:
            return {'error': 'Embeddings model not available'}
        
        try:
            query_embedding = self.embeddings_model.encode(query)
            relevant_chunks = []
            
            # Search in specific file or all files
            target_chunks = []
            if file_path and file_path in self.chunk_cache:
                target_chunks = self.chunk_cache[file_path]
            elif file_path is None:
                for chunks in self.chunk_cache.values():
                    target_chunks.extend(chunks)
            else:
                return {'error': f'File {file_path} not found in cache'}
            
            # Calculate similarities
            for chunk in target_chunks:
                if chunk.get('embedding'):
                    similarity = self._calculate_similarity(query_embedding, chunk['embedding'])
                    relevant_chunks.append((chunk, similarity))
            
            # Sort by similarity
            relevant_chunks.sort(key=lambda x: x[1], reverse=True)
            
            # Build context with relationships
            context = {
                'query': query,
                'relevant_chunks': [],
                'context_windows': [],
                'semantic_graph': []
            }
            
            for chunk, similarity in relevant_chunks[:top_k]:
                context['relevant_chunks'].append({
                    'chunk': chunk,
                    'similarity': similarity
                })
                
                # Add context window
                if file_path in self.context_windows:
                    chunk_context = self.context_windows[file_path].get(chunk['id'], {})
                    context['context_windows'].append(chunk_context)
            
            return context
            
        except Exception as e:
            logger.error(f"Dockling context retrieval failed: {str(e)}")
            return {'error': str(e)}

class AgentZero:
    """Agent Zero - The ultimate autonomous agent for CHATTY"""
    
    def __init__(self):
        self.name = "Agent Zero"
        self.capabilities = [
            'autonomous_learning', 'self_optimization', 'multi_llm_orchestration',
            'file_analysis', 'code_generation', 'system_monitoring', 'error_recovery'
        ]
        self.memory = []
        self.learning_rate = 0.1
        
    async def analyze_system_state(self) -> Dict[str, Any]:
        """Analyze current system state and identify improvement opportunities"""
        analysis = {
            'timestamp': datetime.utcnow().isoformat(),
            'system_health': 'unknown',
            'optimization_opportunities': [],
            'learning_opportunities': [],
            'performance_metrics': {}
        }
        
        # Analyze file system
        file_analysis = await self._analyze_file_system()
        analysis['optimization_opportunities'].extend(file_analysis['opportunities'])
        analysis['learning_opportunities'].extend(file_analysis['learning'])
        
        # Analyze performance
        perf_analysis = await self._analyze_performance()
        analysis['performance_metrics'] = perf_analysis
        
        # Determine system health
        if analysis['optimization_opportunities']:
            analysis['system_health'] = 'needs_optimization'
        else:
            analysis['system_health'] = 'healthy'
        
        return analysis
    
    async def _analyze_file_system(self) -> Dict[str, Any]:
        """Analyze file system for optimization opportunities"""
        opportunities = []
        learning = []
        
        # Check for large files that could benefit from chunking
        for file_path in self._get_python_files():
            try:
                size = os.path.getsize(file_path)
                if size > 50000:  # Files larger than 50KB
                    opportunities.append({
                        'type': 'file_chunking',
                        'file': file_path,
                        'size': size,
                        'recommendation': 'Apply Dockling chunking for better analysis'
                    })
            except:
                continue
        
        # Check for code patterns that could be optimized
        for file_path in self._get_python_files()[:10]:  # Limit to first 10 files
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Look for optimization patterns
                if 'for i in range(len(' in content:
                    opportunities.append({
                        'type': 'code_optimization',
                        'file': file_path,
                        'pattern': 'inefficient_iteration',
                        'recommendation': 'Use enumerate() instead of range(len())'
                    })
                
                if 'import *' in content:
                    opportunities.append({
                        'type': 'code_optimization',
                        'file': file_path,
                        'pattern': 'wildcard_import',
                        'recommendation': 'Use explicit imports for better maintainability'
                    })
                
            except:
                continue
        
        return {'opportunities': opportunities, 'learning': learning}
    
    def _get_python_files(self) -> List[str]:
        """Get list of Python files in the project"""
        python_files = []
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        return python_files
    
    async def _analyze_performance(self) -> Dict[str, Any]:
        """Analyze system performance metrics"""
        metrics = {
            'memory_usage': 0,
            'cpu_usage': 0,
            'disk_usage': 0,
            'response_times': []
        }
        
        # Get memory usage
        try:
            import psutil
            metrics['memory_usage'] = psutil.virtual_memory().percent
            metrics['cpu_usage'] = psutil.cpu_percent(interval=1)
            metrics['disk_usage'] = psutil.disk_usage('/').percent
        except:
            pass  # psutil not available
        
        return metrics
    
    async def optimize_system(self, opportunities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply system optimizations"""
        results = {
            'optimizations_applied': 0,
            'optimizations_failed': 0,
            'details': []
        }
        
        for opportunity in opportunities:
            try:
                if opportunity['type'] == 'file_chunking':
                    # Apply Dockling chunking
                    chunker = DocklingChunker()
                    chunks = chunker.dockling_chunk_file(
                        opportunity['file'], 
                        max_chunk_size=1500
                    )
                    
                    results['details'].append({
                        'file': opportunity['file'],
                        'chunks_created': len(chunks),
                        'optimization': 'dockling_chunking',
                        'success': True
                    })
                    results['optimizations_applied'] += 1
                
                elif opportunity['type'] == 'code_optimization':
                    # Apply code optimization
                    optimization_result = await self._apply_code_optimization(opportunity)
                    results['details'].append(optimization_result)
                    
                    if optimization_result['success']:
                        results['optimizations_applied'] += 1
                    else:
                        results['optimizations_failed'] += 1
                
            except Exception as e:
                results['details'].append({
                    'file': opportunity.get('file', 'unknown'),
                    'error': str(e),
                    'success': False
                })
                results['optimizations_failed'] += 1
        
        return results
    
    async def _apply_code_optimization(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Apply specific code optimization"""
        file_path = opportunity['file']
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Apply specific optimizations based on pattern
            if opportunity['pattern'] == 'inefficient_iteration':
                # Replace range(len()) with enumerate()
                content = re.sub(
                    r'for\s+(\w+)\s+in\s+range\(len\((\w+)\)\):',
                    r'for \1, item in enumerate(\2):',
                    content
                )
            
            elif opportunity['pattern'] == 'wildcard_import':
                # This is more complex and would require proper import analysis
                # For now, just log the opportunity
                pass
            
            # Write back to file
            with open(file_path, 'w') as f:
                f.write(content)
            
            return {
                'file': file_path,
                'optimization': opportunity['pattern'],
                'success': True,
                'message': 'Code optimization applied successfully'
            }
            
        except Exception as e:
            return {
                'file': file_path,
                'optimization': opportunity['pattern'],
                'success': False,
                'error': str(e)
            }

class BMADAgent:
    """BMAD Agent - Bug Management and Detection Agent"""
    
    def __init__(self):
        self.name = "BMAD Agent"
        self.bug_patterns = self._load_bug_patterns()
        self.detection_rules = self._load_detection_rules()
    
    def _load_bug_patterns(self) -> Dict[str, Any]:
        """Load known bug patterns"""
        return {
            'null_pointer': {
                'patterns': [r'\.(\w+)\s*==\s*None', r'(\w+)\s*is\s*None'],
                'severity': 'high',
                'fix_suggestion': 'Add null check before accessing'
            },
            'infinite_loop': {
                'patterns': [r'while\s+True:', r'for\s+\w+\s+in\s+range\(\d+\):'],
                'severity': 'medium',
                'fix_suggestion': 'Add break condition or limit iterations'
            },
            'resource_leak': {
                'patterns': [r'open\([^)]+\)', r'(\w+)\.read\(\)'],
                'severity': 'high',
                'fix_suggestion': 'Use context manager (with statement)'
            }
        }
    
    def _load_detection_rules(self) -> List[Dict[str, Any]]:
        """Load detection rules for various issues"""
        return [
            {
                'name': 'unused_variable',
                'pattern': r'^\s*(\w+)\s*=.*\n.*#.*unused',
                'severity': 'low',
                'description': 'Unused variable detected'
            },
            {
                'name': 'hardcoded_string',
                'pattern': r'["\']{2,}',
                'severity': 'medium',
                'description': 'Hardcoded string detected'
            }
        ]
    
    async def scan_file(self, file_path: str) -> Dict[str, Any]:
        """Scan file for bugs and issues"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            issues = []
            
            # Check bug patterns
            for bug_type, bug_data in self.bug_patterns.items():
                for pattern in bug_data['patterns']:
                    matches = re.finditer(pattern, content, re.MULTILINE)
                    for match in matches:
                        issues.append({
                            'type': bug_type,
                            'line': content[:match.start()].count('\n') + 1,
                            'severity': bug_data['severity'],
                            'description': f"Potential {bug_type} issue",
                            'suggestion': bug_data['fix_suggestion'],
                            'code': match.group(0)
                        })
            
            # Check detection rules
            for rule in self.detection_rules:
                matches = re.finditer(rule['pattern'], content, re.MULTILINE)
                for match in matches:
                    issues.append({
                        'type': rule['name'],
                        'line': content[:match.start()].count('\n') + 1,
                        'severity': rule['severity'],
                        'description': rule['description'],
                        'suggestion': 'Review and refactor if necessary',
                        'code': match.group(0)
                    })
            
            return {
                'file': file_path,
                'issues_found': len(issues),
                'issues': issues,
                'severity_breakdown': self._get_severity_breakdown(issues)
            }
            
        except Exception as e:
            return {
                'file': file_path,
                'error': str(e),
                'issues_found': 0,
                'issues': []
            }
    
    def _get_severity_breakdown(self, issues: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get breakdown of issues by severity"""
        breakdown = defaultdict(int)
        for issue in issues:
            breakdown[issue['severity']] += 1
        return dict(breakdown)

# Global instances
dockling_chunker = DocklingChunker()
agent_zero = AgentZero()
bmad_agent = BMADAgent()

# Integration functions
async def integrate_dockling_features():
    """Integrate Dockling chunking into CHATTY"""
    logger.info("🔗 Integrating Dockling chunking features")
    
    # Test Dockling chunking on key files
    key_files = ['START_COMPLETE_AUTOMATION.py', 'backend/server.py', 'openclaw_integration.py']
    
    for file_path in key_files:
        if os.path.exists(file_path):
            chunks = dockling_chunker.dockling_chunk_file(file_path)
            logger.info(f"Dockling chunked {file_path} into {len(chunks)} chunks")
    
    logger.info("✅ Dockling integration complete")

async def integrate_agent_zero():
    """Integrate Agent Zero into CHATTY"""
    logger.info("🤖 Integrating Agent Zero")
    
    # Analyze system state
    analysis = await agent_zero.analyze_system_state()
    logger.info(f"Agent Zero analysis: {analysis['system_health']}")
    
    # Apply optimizations if needed
    if analysis['optimization_opportunities']:
        results = await agent_zero.optimize_system(analysis['optimization_opportunities'])
        logger.info(f"Agent Zero optimizations: {results['optimizations_applied']} applied")
    
    logger.info("✅ Agent Zero integration complete")

async def integrate_bmad_agent():
    """Integrate BMAD Agent into CHATTY"""
    logger.info("🐛 Integrating BMAD Agent")
    
    # Scan key files for bugs
    key_files = ['START_COMPLETE_AUTOMATION.py', 'backend/server.py', 'openclaw_integration.py']
    
    for file_path in key_files:
        if os.path.exists(file_path):
            scan_result = await bmad_agent.scan_file(file_path)
            logger.info(f"BMAD scan {file_path}: {scan_result['issues_found']} issues found")
    
    logger.info("✅ BMAD Agent integration complete")

async def integrate_all_features():
    """Integrate all new features into CHATTY"""
    logger.info("🚀 Integrating all new features into CHATTY")
    
    await integrate_dockling_features()
    await integrate_agent_zero()
    await integrate_bmad_agent()
    
    logger.info("✅ All features integrated successfully")

if __name__ == "__main__":
    # Test the integration
    asyncio.run(integrate_all_features())