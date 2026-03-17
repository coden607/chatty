#!/usr/bin/env python3
"""
YOUTUBE_LIVE_LEARNER.py - Real-time YouTube learning with RAG integration

Features:
  - Extracts transcripts via youtube-transcript-api (no API key needed)
  - Falls back to yt-dlp + Whisper for videos without captions
  - Chunks transcripts with semantic boundaries
  - Embeds and stores in ChromaDB for RAG
  - On-the-fly learning: new videos immediately searchable
  - Supports playlists and batch processing
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
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Dependency checks
# ─────────────────────────────────────────────────────────────

try:
    from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, VideoUnavailable
    TRANSCRIPT_API_OK = True
except ImportError:
    TRANSCRIPT_API_OK = False
    logger.warning("youtube-transcript-api not installed: pip install youtube-transcript-api")

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

try:
    import yt_dlp
    YT_DLP_OK = True
except ImportError:
    YT_DLP_OK = False

# ─────────────────────────────────────────────────────────────
# Data models
# ─────────────────────────────────────────────────────────────

@dataclass
class TranscriptChunk:
    id: str
    video_id: str
    video_title: str
    video_url: str
    text: str
    start_time: float       # seconds
    end_time: float
    chunk_index: int
    embedding: Optional[List[float]] = None

@dataclass
class VideoLearning:
    video_id: str
    video_url: str
    title: str
    transcript: str
    chunks: List[TranscriptChunk] = field(default_factory=list)
    insights: Dict[str, Any] = field(default_factory=dict)
    processed_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    duration_seconds: float = 0.0
    language: str = "en"

# ─────────────────────────────────────────────────────────────
# ChromaDB store
# ─────────────────────────────────────────────────────────────

class YouTubeVectorStore:
    """Persistent ChromaDB collection for YouTube learnings."""

    COLLECTION = "youtube_learnings"
    PERSIST_DIR = "chroma_db"

    def __init__(self):
        self._client: Optional[Any] = None
        self._collection: Optional[Any] = None
        self._embedder: Optional[Any] = None
        self._init()

    def _init(self):
        if CHROMA_OK:
            try:
                self._client = chromadb.PersistentClient(path=self.PERSIST_DIR)
                self._collection = self._client.get_or_create_collection(
                    name=self.COLLECTION,
                    metadata={"hnsw:space": "cosine"},
                )
                logger.info(f"✅ ChromaDB ready: {self._collection.count()} existing chunks")
            except Exception as e:
                logger.warning(f"ChromaDB init failed: {e}")

        if EMBEDDINGS_OK:
            try:
                self._embedder = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception as e:
                logger.warning(f"Embedder init failed: {e}")

    def _embed(self, texts: List[str]) -> Optional[List[List[float]]]:
        if self._embedder:
            try:
                return self._embedder.encode(texts, show_progress_bar=False).tolist()
            except Exception:
                pass
        return None

    def store_chunks(self, chunks: List[TranscriptChunk]):
        if not self._collection:
            return
        if not chunks:
            return

        texts = [c.text for c in chunks]
        embeddings = self._embed(texts)

        ids = [c.id for c in chunks]
        metas = [
            {
                "video_id":    c.video_id,
                "video_title": c.video_title[:200],
                "video_url":   c.video_url,
                "start_time":  c.start_time,
                "end_time":    c.end_time,
                "chunk_index": c.chunk_index,
            }
            for c in chunks
        ]

        try:
            if embeddings:
                self._collection.upsert(ids=ids, documents=texts,
                                        metadatas=metas, embeddings=embeddings)
            else:
                self._collection.upsert(ids=ids, documents=texts, metadatas=metas)
            logger.info(f"💾 Stored {len(chunks)} chunks in ChromaDB")
        except Exception as e:
            logger.error(f"ChromaDB store error: {e}")

    def search(self, query: str, n_results: int = 5,
               video_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Semantic search over all stored YouTube content."""
        if not self._collection:
            return []
        try:
            where = {"video_id": video_id} if video_id else None
            query_embeddings = self._embed([query])
            kwargs = dict(
                query_texts=[query],
                n_results=min(n_results, max(1, self._collection.count())),
                include=["documents", "metadatas", "distances"],
            )
            if query_embeddings:
                kwargs["query_embeddings"] = query_embeddings
                del kwargs["query_texts"]
            if where:
                kwargs["where"] = where

            results = self._collection.query(**kwargs)
            out = []
            for i, doc in enumerate(results["documents"][0]):
                meta = results["metadatas"][0][i]
                dist = results["distances"][0][i]
                out.append({
                    "text": doc,
                    "video_title": meta.get("video_title", ""),
                    "video_url":   meta.get("video_url", ""),
                    "start_time":  meta.get("start_time", 0),
                    "relevance":   round(1 - dist, 3),
                })
            return out
        except Exception as e:
            logger.error(f"ChromaDB search error: {e}")
            return []

    @property
    def count(self) -> int:
        if self._collection:
            try:
                return self._collection.count()
            except Exception:
                pass
        return 0


# ─────────────────────────────────────────────────────────────
# Transcript fetcher
# ─────────────────────────────────────────────────────────────

class TranscriptFetcher:
    """Fetch YouTube transcripts with multiple fallback strategies."""

    @staticmethod
    def extract_video_id(url: str) -> Optional[str]:
        patterns = [
            r"(?:v=|youtu\.be/|embed/|shorts/)([a-zA-Z0-9_-]{11})",
            r"^([a-zA-Z0-9_-]{11})$",
        ]
        for p in patterns:
            m = re.search(p, url)
            if m:
                return m.group(1)
        return None

    @staticmethod
    async def get_transcript(video_id: str) -> Tuple[Optional[str], str, float]:
        """
        Returns (transcript_text, language, duration_seconds).
        Tries: transcript API → yt-dlp auto-captions
        """
        # Strategy 1: youtube-transcript-api
        if TRANSCRIPT_API_OK:
            try:
                # Try English first, then any available
                try:
                    entries = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
                    lang = "en"
                except Exception:
                    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                    transcript = transcript_list.find_transcript(
                        transcript_list._manually_created_transcripts.keys()
                        or transcript_list._generated_transcripts.keys()
                    )
                    entries = transcript.fetch()
                    lang = transcript.language_code

                text_parts = [e.get("text", "") if isinstance(e, dict) else e.text
                               for e in entries]
                full_text = " ".join(text_parts)
                duration  = max((e.get("start", 0) + e.get("duration", 0)
                                  if isinstance(e, dict) else e.start + e.duration)
                                 for e in entries) if entries else 0
                logger.info(f"✅ Transcript via API: {len(full_text)} chars, lang={lang}")
                return full_text, lang, duration

            except (NoTranscriptFound, VideoUnavailable) as e:
                logger.debug(f"No transcript: {e}")
            except Exception as e:
                logger.debug(f"Transcript API error: {e}")

        # Strategy 2: yt-dlp auto-captions (for videos without manual captions)
        if YT_DLP_OK:
            try:
                import tempfile
                with tempfile.TemporaryDirectory() as tmpdir:
                    ydl_opts = {
                        "writeautomaticsub": True,
                        "writesubtitles": True,
                        "subtitlesformat": "vtt",
                        "subtitleslangs": ["en", "en-US"],
                        "skip_download": True,
                        "outtmpl": f"{tmpdir}/%(id)s.%(ext)s",
                        "quiet": True,
                    }
                    url = f"https://www.youtube.com/watch?v={video_id}"
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=True)
                        duration = info.get("duration", 0)

                    # Find VTT file
                    for vtt_path in Path(tmpdir).glob("*.vtt"):
                        vtt_text = vtt_path.read_text(encoding="utf-8")
                        # Strip VTT markup
                        clean = re.sub(r"<[^>]+>", "", vtt_text)
                        clean = re.sub(r"^\d{2}:\d{2}:\d{2}.*$", "", clean, flags=re.M)
                        clean = re.sub(r"^WEBVTT.*$", "", clean, flags=re.M)
                        clean = re.sub(r"\n{3,}", "\n\n", clean).strip()
                        if len(clean) > 100:
                            logger.info(f"✅ Transcript via yt-dlp: {len(clean)} chars")
                            return clean, "en", float(duration)

            except Exception as e:
                logger.debug(f"yt-dlp caption extraction failed: {e}")

        return None, "unknown", 0.0

    @staticmethod
    async def get_video_info(video_id: str) -> Dict[str, Any]:
        """Get title and metadata for a video."""
        if YT_DLP_OK:
            try:
                url = f"https://www.youtube.com/watch?v={video_id}"
                with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
                    info = ydl.extract_info(url, download=False)
                    return {
                        "title":    info.get("title", f"Video {video_id}"),
                        "channel":  info.get("uploader", ""),
                        "duration": info.get("duration", 0),
                        "views":    info.get("view_count", 0),
                        "tags":     info.get("tags", [])[:10],
                    }
            except Exception:
                pass
        return {"title": f"Video {video_id}"}


# ─────────────────────────────────────────────────────────────
# Transcript chunker
# ─────────────────────────────────────────────────────────────

class TranscriptChunker:
    """
    Chunk transcripts semantically:
      - Paragraph boundaries (double newlines / topic shifts)
      - Sentence boundaries within size limits
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap    = overlap

    def chunk(self, text: str, video_id: str, video_title: str,
              video_url: str) -> List[TranscriptChunk]:
        """Split transcript into overlapping chunks with metadata."""
        # Split on sentence boundaries
        sentences = re.split(r"(?<=[.!?])\s+", text)
        chunks: List[TranscriptChunk] = []
        current: List[str] = []
        current_len = 0
        chunk_idx = 0

        for sent in sentences:
            sent_len = len(sent)
            if current_len + sent_len > self.chunk_size and current:
                chunk_text = " ".join(current)
                chunk_id = hashlib.md5(
                    f"{video_id}_{chunk_idx}_{chunk_text[:50]}".encode()
                ).hexdigest()
                chunks.append(TranscriptChunk(
                    id=chunk_id,
                    video_id=video_id,
                    video_title=video_title,
                    video_url=video_url,
                    text=chunk_text,
                    start_time=chunk_idx * 30.0,   # rough estimate
                    end_time=(chunk_idx + 1) * 30.0,
                    chunk_index=chunk_idx,
                ))
                chunk_idx += 1
                # Overlap: keep last N words
                overlap_words = " ".join(current).split()[-self.overlap:]
                current = [" ".join(overlap_words)]
                current_len = len(current[0])

            current.append(sent)
            current_len += sent_len

        # Last chunk
        if current:
            chunk_text = " ".join(current)
            chunk_id = hashlib.md5(
                f"{video_id}_{chunk_idx}_{chunk_text[:50]}".encode()
            ).hexdigest()
            chunks.append(TranscriptChunk(
                id=chunk_id,
                video_id=video_id,
                video_title=video_title,
                video_url=video_url,
                text=chunk_text,
                start_time=chunk_idx * 30.0,
                end_time=(chunk_idx + 1) * 30.0,
                chunk_index=chunk_idx,
            ))

        return chunks


# ─────────────────────────────────────────────────────────────
# Main learner
# ─────────────────────────────────────────────────────────────

class YouTubeLiveLearner:
    """
    End-to-end YouTube learning system.
    Process a video → transcript → chunks → embed → ChromaDB → query ready.
    """

    LEARNINGS_FILE = Path("generated_content/youtube_learnings.json")

    def __init__(self, router=None):
        self.router   = router
        self.store    = YouTubeVectorStore()
        self.chunker  = TranscriptChunker(chunk_size=600, overlap=60)
        self.fetcher  = TranscriptFetcher()
        self._processed: Dict[str, VideoLearning] = {}
        self._load_existing()

    def _load_existing(self):
        if self.LEARNINGS_FILE.exists():
            try:
                data = json.loads(self.LEARNINGS_FILE.read_text())
                logger.info(f"📚 Loaded {len(data)} existing video learnings")
            except Exception:
                pass

    # ── Process a single video ─────────────────────────────────

    async def learn_from_video(self, url: str, force: bool = False) -> VideoLearning:
        """
        Full pipeline: URL → transcript → chunks → RAG store → insights.
        Returns VideoLearning with all extracted knowledge.
        """
        video_id = TranscriptFetcher.extract_video_id(url)
        if not video_id:
            raise ValueError(f"Cannot extract video ID from: {url}")

        if video_id in self._processed and not force:
            logger.info(f"📖 Already processed: {video_id}")
            return self._processed[video_id]

        logger.info(f"🎬 Learning from: {url}")

        # Get metadata
        info = await TranscriptFetcher.get_video_info(video_id)
        title = info.get("title", f"Video {video_id}")

        # Get transcript
        transcript, lang, duration = await TranscriptFetcher.get_transcript(video_id)
        if not transcript:
            raise RuntimeError(f"No transcript available for {video_id}")

        logger.info(f"📝 Transcript: {len(transcript)} chars, lang={lang}")

        # Chunk
        chunks = self.chunker.chunk(transcript, video_id, title, url)
        logger.info(f"🔪 Created {len(chunks)} chunks")

        # Store in ChromaDB
        self.store.store_chunks(chunks)

        # Extract insights
        insights = await self._extract_insights(transcript[:4000], title)

        learning = VideoLearning(
            video_id=video_id,
            video_url=url,
            title=title,
            transcript=transcript,
            chunks=chunks,
            insights=insights,
            duration_seconds=duration,
            language=lang,
        )
        self._processed[video_id] = learning
        self._save_learning(learning)

        logger.info(f"✅ Learned from '{title}': {len(chunks)} chunks, "
                    f"{len(insights)} insight categories")
        return learning

    async def _extract_insights(self, transcript_sample: str, title: str) -> Dict[str, Any]:
        """Use LLM to extract structured insights from transcript."""
        system = """Extract structured insights from a video transcript.
Return JSON with keys:
  - key_topics: list of main topics (max 8)
  - actionable_tips: list of concrete tips/steps (max 10)
  - code_concepts: programming concepts mentioned (if any)
  - tools_mentioned: tools, libraries, frameworks mentioned
  - summary: 2-3 sentence summary
Output ONLY valid JSON."""

        user = f"Video: {title}\n\nTranscript sample:\n{transcript_sample}"

        if self.router:
            from FREE_LLM_ROUTER import TaskType
            result = await self.router.generate(system, user, max_tokens=800,
                                                 task_type=TaskType.ANALYSIS)
            text = result.get("text", "")
            try:
                m = re.search(r"\{.*\}", text, re.DOTALL)
                if m:
                    return json.loads(m.group())
            except Exception:
                pass
            return {"summary": text[:500], "key_topics": [], "actionable_tips": []}

        # Basic keyword fallback
        words = transcript_sample.lower().split()
        return {
            "summary": f"Video about: {title}",
            "key_topics": list(set(w for w in words if len(w) > 5))[:8],
            "actionable_tips": [],
            "tools_mentioned": [],
        }

    # ── Batch processing ───────────────────────────────────────

    async def learn_from_playlist(self, playlist_url: str) -> List[VideoLearning]:
        """Extract all videos from a playlist and learn from each."""
        if not YT_DLP_OK:
            raise RuntimeError("yt-dlp required for playlist: pip install yt-dlp")

        logger.info(f"📋 Fetching playlist: {playlist_url}")
        video_urls = []
        with yt_dlp.YoutubeDL({"quiet": True, "extract_flat": True}) as ydl:
            info = ydl.extract_info(playlist_url, download=False)
            for entry in info.get("entries", []):
                vid_id = entry.get("id") or entry.get("url", "")
                if vid_id:
                    video_urls.append(f"https://www.youtube.com/watch?v={vid_id}")

        logger.info(f"🎬 Processing {len(video_urls)} videos from playlist")
        results = []
        for url in video_urls:
            try:
                learning = await self.learn_from_video(url)
                results.append(learning)
                await asyncio.sleep(1)  # polite delay
            except Exception as e:
                logger.warning(f"Failed to learn from {url}: {e}")
        return results

    # ── RAG query ──────────────────────────────────────────────

    async def query(self, question: str, n_results: int = 5,
                    generate_answer: bool = True) -> Dict[str, Any]:
        """
        Query the YouTube knowledge base and optionally generate an answer.
        """
        # Semantic search
        chunks = self.store.search(question, n_results=n_results)

        if not chunks:
            return {
                "answer": "No relevant YouTube content found.",
                "sources": [],
                "total_chunks_searched": self.store.count,
            }

        context = "\n\n---\n\n".join(
            f"[{c['video_title']}] {c['text']}" for c in chunks
        )

        answer = ""
        if generate_answer and self.router:
            system = (
                "You are a knowledgeable assistant. Answer the question using ONLY "
                "the provided context from YouTube videos. Cite the video titles. "
                "If the context doesn't contain the answer, say so clearly."
            )
            user = f"Question: {question}\n\nContext from videos:\n{context}"
            from FREE_LLM_ROUTER import TaskType
            result = await self.router.generate(system, user, max_tokens=600,
                                                 task_type=TaskType.ANALYSIS)
            answer = result.get("text", "")

        return {
            "answer": answer or context[:1000],
            "sources": [
                {
                    "title": c["video_title"],
                    "url":   c["video_url"],
                    "text":  c["text"][:300],
                    "relevance": c["relevance"],
                }
                for c in chunks
            ],
            "total_chunks_searched": self.store.count,
        }

    # ── Continuous learning ────────────────────────────────────

    async def start_continuous_learning(
        self,
        video_urls: List[str],
        interval_minutes: int = 60,
    ):
        """
        Continuously re-check a list of videos for new content.
        (Also supports new URLs added to a JSON watch list.)
        """
        watch_list_path = Path("generated_content/youtube_watch_list.json")
        watch_list_path.parent.mkdir(exist_ok=True)

        while True:
            # Merge with any URLs added to watch list
            if watch_list_path.exists():
                try:
                    extra = json.loads(watch_list_path.read_text())
                    video_urls = list(dict.fromkeys(video_urls + extra))
                except Exception:
                    pass

            for url in video_urls:
                try:
                    await self.learn_from_video(url)
                except Exception as e:
                    logger.warning(f"Continuous learning error for {url}: {e}")
                await asyncio.sleep(2)

            logger.info(f"⏰ Next YouTube learning cycle in {interval_minutes}m")
            await asyncio.sleep(interval_minutes * 60)

    # ── Persistence ────────────────────────────────────────────

    def _save_learning(self, learning: VideoLearning):
        self.LEARNINGS_FILE.parent.mkdir(exist_ok=True)
        existing: List[Dict] = []
        if self.LEARNINGS_FILE.exists():
            try:
                existing = json.loads(self.LEARNINGS_FILE.read_text())
            except Exception:
                pass

        # Replace or append
        existing = [e for e in existing if e.get("video_id") != learning.video_id]
        existing.append({
            "video_id":  learning.video_id,
            "video_url": learning.video_url,
            "title":     learning.title,
            "insights":  learning.insights,
            "chunks":    len(learning.chunks),
            "language":  learning.language,
            "processed_at": learning.processed_at,
        })
        self.LEARNINGS_FILE.write_text(json.dumps(existing, indent=2))

    def add_to_watch_list(self, url: str):
        """Add a URL to the persistent watch list."""
        path = Path("generated_content/youtube_watch_list.json")
        path.parent.mkdir(exist_ok=True)
        current = []
        if path.exists():
            try:
                current = json.loads(path.read_text())
            except Exception:
                pass
        if url not in current:
            current.append(url)
            path.write_text(json.dumps(current, indent=2))
            logger.info(f"📌 Added to watch list: {url}")

    def status(self) -> Dict[str, Any]:
        return {
            "videos_processed": len(self._processed),
            "chunks_in_store":  self.store.count,
            "chromadb_ok":      CHROMA_OK,
            "embeddings_ok":    EMBEDDINGS_OK,
            "transcript_api":   TRANSCRIPT_API_OK,
            "yt_dlp_ok":        YT_DLP_OK,
        }


# ── Module singleton ───────────────────────────────────────────
_learner: Optional[YouTubeLiveLearner] = None

def get_learner(router=None) -> YouTubeLiveLearner:
    global _learner
    if _learner is None:
        _learner = YouTubeLiveLearner(router=router)
    return _learner


if __name__ == "__main__":
    async def demo():
        from FREE_LLM_ROUTER import get_router
        router = get_router()
        learner = YouTubeLiveLearner(router=router)

        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        print(f"Status: {learner.status()}")

        try:
            learning = await learner.learn_from_video(url)
            print(f"\n✅ Learned: {learning.title}")
            print(f"   Chunks: {len(learning.chunks)}")
            print(f"   Insights: {learning.insights.get('summary', '')[:200]}")

            result = await learner.query("What is this video about?")
            print(f"\n🔍 Query result: {result['answer'][:300]}")
        except Exception as e:
            print(f"Error: {e}")

    asyncio.run(demo())
