#!/usr/bin/env python3
"""
CHATTY_RAG.py - Unified RAG system

Combines:
  - Docling-style chunking (from dockling_chunker.py) for files
  - YouTube transcript chunks (from YOUTUBE_LIVE_LEARNER.py)
  - Web scraped content (from FREE_WEB_SCRAPER.py)
  - ChromaDB persistent storage
  - Semantic search with sentence-transformers
  - Context compression for LLM prompts

This is the single entry point for all retrieval-augmented generation.
"""

import asyncio
import hashlib
import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Dependencies
# ─────────────────────────────────────────────────────────────

try:
    import chromadb
    CHROMA_OK = True
except ImportError:
    CHROMA_OK = False

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_OK = True
except ImportError:
    EMBEDDINGS_OK = False

# ─────────────────────────────────────────────────────────────
# Data models
# ─────────────────────────────────────────────────────────────

@dataclass
class RAGDocument:
    id: str
    content: str
    source: str                          # "file" | "youtube" | "web" | "memory"
    source_path: str = ""                # file path, URL, video ID
    title: str = ""
    chunk_index: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    added_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

@dataclass
class RAGResult:
    content: str
    source: str
    source_path: str
    title: str
    relevance: float
    chunk_index: int


# ─────────────────────────────────────────────────────────────
# Vector store wrapper
# ─────────────────────────────────────────────────────────────

class ChattyVectorStore:
    """Multi-collection ChromaDB store for all RAG content."""

    PERSIST_DIR = "chroma_db"
    COLLECTIONS = {
        "files":   "chatty_files",
        "youtube": "youtube_learnings",    # shared with YOUTUBE_LIVE_LEARNER
        "web":     "chatty_web",
        "memory":  "chatty_memory",
    }

    def __init__(self):
        self._client: Optional[Any] = None
        self._cols: Dict[str, Any] = {}
        self._embedder: Optional[Any] = None
        self._fallback_store: List[Dict] = []   # in-memory when ChromaDB unavailable
        self._init()

    def _init(self):
        if CHROMA_OK:
            try:
                self._client = chromadb.PersistentClient(path=self.PERSIST_DIR)
                for key, name in self.COLLECTIONS.items():
                    self._cols[key] = self._client.get_or_create_collection(
                        name=name,
                        metadata={"hnsw:space": "cosine"},
                    )
                logger.info("✅ ChromaDB multi-collection store ready")
            except Exception as e:
                logger.warning(f"ChromaDB failed: {e}. Using in-memory fallback.")

        if EMBEDDINGS_OK:
            try:
                self._embedder = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("✅ Sentence embedder loaded")
            except Exception as e:
                logger.warning(f"Embedder failed: {e}")

    def _embed(self, texts: List[str]) -> Optional[List[List[float]]]:
        if self._embedder:
            try:
                return self._embedder.encode(texts, show_progress_bar=False).tolist()
            except Exception:
                pass
        return None

    def _cosine(self, a: List[float], b: List[float]) -> float:
        try:
            import numpy as np
            va, vb = np.array(a), np.array(b)
            denom = np.linalg.norm(va) * np.linalg.norm(vb)
            return float(np.dot(va, vb) / denom) if denom > 0 else 0.0
        except ImportError:
            # Pure python fallback
            dot = sum(x * y for x, y in zip(a, b))
            mag_a = sum(x ** 2 for x in a) ** 0.5
            mag_b = sum(x ** 2 for x in b) ** 0.5
            return dot / (mag_a * mag_b) if mag_a and mag_b else 0.0

    def store(self, docs: List[RAGDocument], collection: str = "files"):
        col = self._cols.get(collection)
        if col and docs:
            texts = [d.content for d in docs]
            embeddings = self._embed(texts)
            ids = [d.id for d in docs]
            metas = [
                {
                    "source":      d.source,
                    "source_path": d.source_path[:500],
                    "title":       d.title[:200],
                    "chunk_index": d.chunk_index,
                    "added_at":    d.added_at,
                    **{k: str(v)[:200] for k, v in d.metadata.items()},
                }
                for d in docs
            ]
            try:
                if embeddings:
                    col.upsert(ids=ids, documents=texts, metadatas=metas,
                               embeddings=embeddings)
                else:
                    col.upsert(ids=ids, documents=texts, metadatas=metas)
                logger.debug(f"Stored {len(docs)} docs in '{collection}'")
            except Exception as e:
                logger.error(f"Store error: {e}")
        else:
            # Fallback in-memory
            for doc in docs:
                embedding = self._embed([doc.content])
                self._fallback_store.append({
                    "id": doc.id, "content": doc.content,
                    "source": doc.source, "source_path": doc.source_path,
                    "title": doc.title, "chunk_index": doc.chunk_index,
                    "embedding": embedding[0] if embedding else None,
                })

    def search(
        self,
        query: str,
        n_results: int = 5,
        collections: Optional[List[str]] = None,
        min_relevance: float = 0.3,
    ) -> List[RAGResult]:
        collections = collections or list(self.COLLECTIONS.keys())
        query_emb = self._embed([query])
        all_results: List[RAGResult] = []

        # Search ChromaDB collections
        for col_key in collections:
            col = self._cols.get(col_key)
            if not col:
                continue
            try:
                count = col.count()
                if count == 0:
                    continue
                kwargs: Dict[str, Any] = dict(
                    n_results=min(n_results, count),
                    include=["documents", "metadatas", "distances"],
                )
                if query_emb:
                    kwargs["query_embeddings"] = query_emb
                else:
                    kwargs["query_texts"] = [query]

                res = col.query(**kwargs)
                for i, doc in enumerate(res["documents"][0]):
                    meta = res["metadatas"][0][i]
                    dist = res["distances"][0][i]
                    relevance = round(1.0 - dist, 3)
                    if relevance >= min_relevance:
                        all_results.append(RAGResult(
                            content=doc,
                            source=meta.get("source", col_key),
                            source_path=meta.get("source_path", ""),
                            title=meta.get("title", ""),
                            relevance=relevance,
                            chunk_index=int(meta.get("chunk_index", 0)),
                        ))
            except Exception as e:
                logger.debug(f"Search error in {col_key}: {e}")

        # Fallback in-memory search
        if not all_results and self._fallback_store and query_emb:
            for item in self._fallback_store:
                if item.get("embedding"):
                    sim = self._cosine(query_emb[0], item["embedding"])
                    if sim >= min_relevance:
                        all_results.append(RAGResult(
                            content=item["content"],
                            source=item["source"],
                            source_path=item["source_path"],
                            title=item["title"],
                            relevance=round(sim, 3),
                            chunk_index=item["chunk_index"],
                        ))

        # Sort by relevance, deduplicate
        all_results.sort(key=lambda x: x.relevance, reverse=True)
        seen = set()
        unique = []
        for r in all_results:
            key = hashlib.md5(r.content[:100].encode()).hexdigest()
            if key not in seen:
                seen.add(key)
                unique.append(r)

        return unique[:n_results]

    def count(self, collection: str = "files") -> int:
        col = self._cols.get(collection)
        if col:
            try:
                return col.count()
            except Exception:
                pass
        return len(self._fallback_store)

    def total_count(self) -> Dict[str, int]:
        return {key: self.count(key) for key in self.COLLECTIONS}


# ─────────────────────────────────────────────────────────────
# Document ingestion
# ─────────────────────────────────────────────────────────────

class DocumentIngester:
    """Ingest files into the RAG store using dockling_chunker."""

    def __init__(self, store: ChattyVectorStore):
        self.store = store
        self._chunker: Optional[Any] = None
        try:
            from dockling_chunker import DocklingChunker
            self._chunker = DocklingChunker()
        except Exception:
            pass

    def _simple_chunk(self, text: str, chunk_size: int = 800,
                      overlap: int = 80) -> List[str]:
        """Sentence-boundary chunker when dockling not available."""
        sentences = re.split(r"(?<=[.!?\n])\s+", text)
        chunks, current, cur_len = [], [], 0
        for sent in sentences:
            if cur_len + len(sent) > chunk_size and current:
                chunks.append(" ".join(current))
                overlap_words = " ".join(current).split()[-overlap:]
                current = [" ".join(overlap_words)]
                cur_len = len(current[0])
            current.append(sent)
            cur_len += len(sent)
        if current:
            chunks.append(" ".join(current))
        return chunks

    def ingest_file(self, path: Union[str, Path]) -> int:
        """Ingest a single file. Returns number of chunks stored."""
        path = Path(path)
        if not path.exists():
            logger.warning(f"File not found: {path}")
            return 0

        text = path.read_text(encoding="utf-8", errors="replace")
        chunks_text: List[str] = []

        if self._chunker:
            try:
                raw_chunks = self._chunker.chunk_file(str(path))
                chunks_text = [c.get("content", "") for c in raw_chunks if c.get("content")]
            except Exception as e:
                logger.debug(f"Dockling chunker failed: {e}")

        if not chunks_text:
            chunks_text = self._simple_chunk(text)

        docs = [
            RAGDocument(
                id=hashlib.md5(f"{path}_{i}_{chunk[:30]}".encode()).hexdigest(),
                content=chunk,
                source="file",
                source_path=str(path),
                title=path.name,
                chunk_index=i,
                metadata={"extension": path.suffix, "size": path.stat().st_size},
            )
            for i, chunk in enumerate(chunks_text)
            if chunk.strip()
        ]

        self.store.store(docs, collection="files")
        logger.info(f"📄 Ingested {path.name}: {len(docs)} chunks")
        return len(docs)

    def ingest_directory(self, directory: Union[str, Path],
                         extensions: Optional[List[str]] = None,
                         recursive: bool = True) -> int:
        """Ingest all matching files in a directory."""
        directory = Path(directory)
        extensions = extensions or [".py", ".md", ".txt", ".json", ".yaml", ".rst"]
        pattern = "**/*" if recursive else "*"
        total = 0
        for file_path in directory.glob(pattern):
            if file_path.is_file() and file_path.suffix in extensions:
                try:
                    total += self.ingest_file(file_path)
                except Exception as e:
                    logger.warning(f"Failed to ingest {file_path}: {e}")
        logger.info(f"📁 Directory ingest complete: {total} total chunks")
        return total

    def ingest_text(self, text: str, source_path: str = "manual",
                    title: str = "", collection: str = "memory") -> int:
        """Ingest arbitrary text (e.g., scraped web content)."""
        chunks_text = self._simple_chunk(text)
        docs = [
            RAGDocument(
                id=hashlib.md5(f"{source_path}_{i}_{chunk[:30]}".encode()).hexdigest(),
                content=chunk,
                source=collection,
                source_path=source_path,
                title=title or source_path[:80],
                chunk_index=i,
            )
            for i, chunk in enumerate(chunks_text)
            if chunk.strip()
        ]
        self.store.store(docs, collection=collection)
        return len(docs)


# ─────────────────────────────────────────────────────────────
# RAG engine
# ─────────────────────────────────────────────────────────────

class ChattyRAG:
    """
    Unified RAG engine. Handles ingestion, retrieval, and
    context building for LLM prompts.
    """

    def __init__(self, router=None):
        self.store    = ChattyVectorStore()
        self.ingester = DocumentIngester(self.store)
        self.router   = router

    # ── Ingestion shortcuts ────────────────────────────────────

    def ingest_file(self, path: Union[str, Path]) -> int:
        return self.ingester.ingest_file(path)

    def ingest_directory(self, path: Union[str, Path], **kwargs) -> int:
        return self.ingester.ingest_directory(path, **kwargs)

    def ingest_text(self, text: str, **kwargs) -> int:
        return self.ingester.ingest_text(text, **kwargs)

    async def ingest_web(self, url: str) -> int:
        """Scrape a URL and ingest into web collection."""
        try:
            from FREE_WEB_SCRAPER import get_scraper
            scraper = get_scraper()
            page = await scraper.scrape(url)
            if page.success and page.text:
                return self.ingester.ingest_text(
                    page.text, source_path=url, title=page.title,
                    collection="web"
                )
        except Exception as e:
            logger.warning(f"Web ingest failed for {url}: {e}")
        return 0

    async def ingest_youtube(self, url: str) -> int:
        """Learn from a YouTube video and ensure it's in the store."""
        try:
            from YOUTUBE_LIVE_LEARNER import get_learner
            learner = get_learner(router=self.router)
            learning = await learner.learn_from_video(url)
            return len(learning.chunks)
        except Exception as e:
            logger.warning(f"YouTube ingest failed for {url}: {e}")
        return 0

    # ── Retrieval ──────────────────────────────────────────────

    def search(
        self,
        query: str,
        n_results: int = 5,
        collections: Optional[List[str]] = None,
        min_relevance: float = 0.25,
    ) -> List[RAGResult]:
        return self.store.search(query, n_results=n_results,
                                 collections=collections,
                                 min_relevance=min_relevance)

    def build_context(
        self,
        query: str,
        n_results: int = 5,
        max_context_chars: int = 4000,
        collections: Optional[List[str]] = None,
    ) -> Tuple[str, List[RAGResult]]:
        """
        Build a context block for LLM prompts.
        Returns (context_str, results_used).
        """
        results = self.search(query, n_results=n_results, collections=collections)
        if not results:
            return "", []

        lines = ["RELEVANT CONTEXT:"]
        total_chars = 0
        used = []
        for r in results:
            source_label = f"[{r.source.upper()} | {r.title or r.source_path}]"
            entry = f"{source_label}\n{r.content}\n"
            if total_chars + len(entry) > max_context_chars:
                break
            lines.append(entry)
            total_chars += len(entry)
            used.append(r)

        return "\n".join(lines), used

    # ── RAG-augmented generation ───────────────────────────────

    async def generate_with_rag(
        self,
        question: str,
        system_prompt: str = "",
        n_results: int = 5,
        max_tokens: int = 1024,
        collections: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve relevant context, then generate an answer.
        """
        context, results = self.build_context(question, n_results=n_results,
                                               collections=collections)
        has_context = bool(results)

        system = system_prompt or (
            "You are a knowledgeable assistant with access to retrieved context. "
            "Answer using the context when relevant. Cite sources. "
            "If context is insufficient, answer from general knowledge."
        )

        user = f"{context}\n\nQuestion: {question}" if context else question

        if self.router:
            from FREE_LLM_ROUTER import TaskType
            result = await self.router.generate(system, user, max_tokens=max_tokens,
                                                 task_type=TaskType.ANALYSIS)
            answer = result.get("text", "")
        else:
            answer = f"[No LLM router available]\nContext found: {has_context}\n{context[:500]}"

        return {
            "answer": answer,
            "context_used": has_context,
            "sources": [
                {"title": r.title, "source": r.source,
                 "path": r.source_path, "relevance": r.relevance}
                for r in results
            ],
            "total_docs": sum(self.store.total_count().values()),
        }

    def status(self) -> Dict[str, Any]:
        counts = self.store.total_count()
        return {
            "chromadb": CHROMA_OK,
            "embeddings": EMBEDDINGS_OK,
            "collections": counts,
            "total_chunks": sum(counts.values()),
        }


# ── Module singleton ───────────────────────────────────────────
_rag: Optional[ChattyRAG] = None

def get_rag(router=None) -> ChattyRAG:
    global _rag
    if _rag is None:
        _rag = ChattyRAG(router=router)
    return _rag


if __name__ == "__main__":
    async def demo():
        from FREE_LLM_ROUTER import get_router
        router = get_router()
        rag = ChattyRAG(router=router)

        print("Status:", json.dumps(rag.status(), indent=2))

        # Ingest this file itself
        rag.ingest_file(__file__)

        result = await rag.generate_with_rag(
            "What does CHATTY_RAG.py do?",
            n_results=3,
        )
        print(f"\nAnswer: {result['answer'][:500]}")
        print(f"Sources: {result['sources']}")

    import json
    asyncio.run(demo())
