#!/usr/bin/env python3
"""
WHISPER_TRANSCRIBER.py - Fully offline YouTube/audio transcription

Pipeline:
  1. yt-dlp downloads audio (m4a/mp3) from YouTube URL
  2. openai-whisper (local model, no API) transcribes to text
  3. Result fed into YOUTUBE_LIVE_LEARNER's RAG pipeline

Whisper model sizes (all free, local):
  tiny   ~39M  - fast, lower accuracy
  base   ~74M  - good balance (default)
  small  ~244M - better accuracy
  medium ~769M - high accuracy
  large  ~1.5G - best accuracy (slow)
"""

import asyncio
import hashlib
import json
import logging
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
CACHE_DIR = Path("generated_content/whisper_cache")


# ─────────────────────────────────────────────────────────────
# Dependency checks
# ─────────────────────────────────────────────────────────────

try:
    import whisper as openai_whisper
    WHISPER_OK = True
except ImportError:
    WHISPER_OK = False
    logger.info("Whisper not installed: pip install openai-whisper")

try:
    import yt_dlp
    YT_DLP_OK = True
except ImportError:
    YT_DLP_OK = False


# ─────────────────────────────────────────────────────────────

@dataclass
class TranscriptionResult:
    video_id: str
    video_url: str
    text: str
    language: str
    segments: List[Dict[str, Any]] = field(default_factory=list)
    duration: float = 0.0
    model_used: str = ""
    method: str = "whisper"
    transcribed_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class WhisperTranscriber:
    """
    Local Whisper-based transcription for YouTube videos.
    Downloads audio with yt-dlp, transcribes locally — no API keys needed.
    """

    def __init__(self, model_size: str = WHISPER_MODEL):
        self.model_size = model_size
        self._model = None       # lazy-load (large download on first use)
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _load_model(self):
        if not WHISPER_OK:
            raise RuntimeError("openai-whisper not installed: pip install openai-whisper")
        if self._model is None:
            logger.info(f"🎤 Loading Whisper model '{self.model_size}' (first load may download)...")
            self._model = openai_whisper.load_model(self.model_size)
            logger.info(f"✅ Whisper '{self.model_size}' ready")
        return self._model

    def _cache_key(self, video_id: str) -> Path:
        return CACHE_DIR / f"{video_id}_{self.model_size}.json"

    def _load_cache(self, video_id: str) -> Optional[TranscriptionResult]:
        path = self._cache_key(video_id)
        if path.exists():
            try:
                data = json.loads(path.read_text())
                logger.info(f"📦 Cache hit for {video_id}")
                return TranscriptionResult(**data)
            except Exception:
                pass
        return None

    def _save_cache(self, result: TranscriptionResult):
        path = self._cache_key(result.video_id)
        try:
            path.write_text(json.dumps({
                "video_id":       result.video_id,
                "video_url":      result.video_url,
                "text":           result.text,
                "language":       result.language,
                "segments":       result.segments[:50],  # cap size
                "duration":       result.duration,
                "model_used":     result.model_used,
                "method":         result.method,
                "transcribed_at": result.transcribed_at,
            }))
        except Exception as e:
            logger.warning(f"Cache write failed: {e}")

    async def transcribe_url(self, url: str, video_id: str,
                              force: bool = False) -> TranscriptionResult:
        """
        Download audio from URL and transcribe with local Whisper.
        Cached by video_id + model_size.
        """
        # Check cache
        if not force:
            cached = self._load_cache(video_id)
            if cached:
                return cached

        if not YT_DLP_OK:
            raise RuntimeError("yt-dlp required: pip install yt-dlp")

        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = await self._download_audio(url, tmpdir)
            if not audio_path:
                raise RuntimeError(f"Failed to download audio for {url}")

            result = await self._transcribe_file(audio_path, url, video_id)
            self._save_cache(result)
            return result

    async def transcribe_file(self, audio_path: str, video_id: str = "",
                               video_url: str = "") -> TranscriptionResult:
        """Transcribe a local audio/video file directly."""
        cached = self._load_cache(video_id) if video_id else None
        if cached:
            return cached
        result = await self._transcribe_file(audio_path, video_url, video_id)
        if video_id:
            self._save_cache(result)
        return result

    async def _download_audio(self, url: str, tmpdir: str) -> Optional[str]:
        """Download best audio from YouTube URL using yt-dlp."""
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": f"{tmpdir}/%(id)s.%(ext)s",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "128",
            }],
            "quiet": True,
            "no_warnings": True,
        }
        try:
            loop = asyncio.get_event_loop()
            audio_files: List[str] = []

            def _download():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                found = list(Path(tmpdir).glob("*.mp3"))
                if not found:
                    found = list(Path(tmpdir).glob("*.m4a"))
                    if not found:
                        found = list(Path(tmpdir).glob("*"))
                audio_files.extend(str(f) for f in found[:1])

            await loop.run_in_executor(None, _download)
            return audio_files[0] if audio_files else None

        except Exception as e:
            logger.error(f"Audio download failed for {url}: {e}")
            return None

    async def _transcribe_file(self, audio_path: str, video_url: str,
                                video_id: str) -> TranscriptionResult:
        """Run Whisper transcription in a thread pool (CPU-bound)."""
        loop = asyncio.get_event_loop()

        def _run_whisper():
            model = self._load_model()
            logger.info(f"🎤 Transcribing {audio_path} with Whisper {self.model_size}...")
            result = model.transcribe(
                audio_path,
                fp16=False,        # CPU-safe
                verbose=False,
                word_timestamps=False,
            )
            return result

        try:
            whisper_result = await loop.run_in_executor(None, _run_whisper)
            text      = whisper_result.get("text", "").strip()
            language  = whisper_result.get("language", "en")
            segments  = [
                {"start": s["start"], "end": s["end"], "text": s["text"]}
                for s in whisper_result.get("segments", [])[:100]
            ]
            duration  = segments[-1]["end"] if segments else 0.0

            logger.info(f"✅ Whisper transcribed {len(text)} chars, lang={language}")

            return TranscriptionResult(
                video_id=video_id or hashlib.md5(video_url.encode()).hexdigest()[:8],
                video_url=video_url,
                text=text,
                language=language,
                segments=segments,
                duration=duration,
                model_used=f"whisper-{self.model_size}",
            )
        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
            raise

    def status(self) -> Dict[str, Any]:
        return {
            "whisper_ok":    WHISPER_OK,
            "yt_dlp_ok":     YT_DLP_OK,
            "model":         self.model_size,
            "model_loaded":  self._model is not None,
            "cache_entries": len(list(CACHE_DIR.glob("*.json"))),
        }


# ── Module singleton ───────────────────────────────────────────
_transcriber: Optional[WhisperTranscriber] = None

def get_transcriber(model_size: str = WHISPER_MODEL) -> WhisperTranscriber:
    global _transcriber
    if _transcriber is None:
        _transcriber = WhisperTranscriber(model_size)
    return _transcriber


# ── Patch YOUTUBE_LIVE_LEARNER to use Whisper as fallback ─────

def patch_youtube_learner():
    """
    Monkey-patch YOUTUBE_LIVE_LEARNER.TranscriptFetcher to use
    Whisper when youtube-transcript-api has no captions.
    """
    try:
        import YOUTUBE_LIVE_LEARNER as yll
        original_get_transcript = yll.TranscriptFetcher.get_transcript.__func__

        @staticmethod
        async def get_transcript_with_whisper(video_id: str):
            # Try original method first (fast, no download)
            text, lang, duration = await original_get_transcript(video_id)
            if text and len(text) > 100:
                return text, lang, duration

            # Fallback to Whisper
            logger.info(f"📡 Transcript API failed for {video_id}, trying Whisper...")
            try:
                transcriber = get_transcriber()
                url = f"https://www.youtube.com/watch?v={video_id}"
                result = await transcriber.transcribe_url(url, video_id)
                if result.text:
                    return result.text, result.language, result.duration
            except Exception as e:
                logger.warning(f"Whisper fallback failed: {e}")

            return None, "unknown", 0.0

        yll.TranscriptFetcher.get_transcript = get_transcript_with_whisper
        logger.info("✅ Whisper fallback patched into YOUTUBE_LIVE_LEARNER")
    except Exception as e:
        logger.warning(f"Could not patch YouTube learner: {e}")


if __name__ == "__main__":
    async def demo():
        t = WhisperTranscriber("tiny")   # tiny = fast for demo
        print("Status:", t.status())

        if not WHISPER_OK:
            print("Install whisper: pip install openai-whisper")
            return
        if not YT_DLP_OK:
            print("Install yt-dlp: pip install yt-dlp")
            return

        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        print(f"Transcribing {url}...")
        result = await t.transcribe_url(url, "dQw4w9WgXcQ")
        print(f"Text ({len(result.text)} chars): {result.text[:300]}...")
        print(f"Language: {result.language}, Duration: {result.duration:.1f}s")

    asyncio.run(demo())
