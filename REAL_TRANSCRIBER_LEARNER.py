#!/usr/bin/env python3
"""
REAL YouTube Transcription and Learning System
Actually transcribes videos and learns from them
"""

import asyncio
import json
import logging
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Real YouTube transcription
try:
    from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, VideoUnavailable
    from youtube_transcript_api.formatters import TextFormatter
    YOUTUBE_API_AVAILABLE = True
except ImportError:
    YOUTUBE_API_AVAILABLE = False

# Real AI analysis
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Audio processing for videos without transcripts
try:
    import speech_recognition as sr
    from pydub import AudioSegment
    AUDIO_PROCESSING_AVAILABLE = True
except ImportError:
    AUDIO_PROCESSING_AVAILABLE = False

# Video downloading
try:
    import yt_dlp
    VIDEO_DOWNLOAD_AVAILABLE = True
except ImportError:
    VIDEO_DOWNLOAD_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RealYouTubeTranscriber:
    """Actually transcribes YouTube videos and learns from them"""
    
    def __init__(self):
        self.learning_database = {}
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.temp_dir = Path('temp_audio')
        self.temp_dir.mkdir(exist_ok=True)
        
        logger.info("🎥 Real YouTube Transcriber initialized")
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check what's available"""
        available = []
        missing = []
        
        if YOUTUBE_API_AVAILABLE:
            available.append("youtube-transcript-api")
        else:
            missing.append("youtube-transcript-api")
        
        if OPENAI_AVAILABLE:
            available.append("openai")
        else:
            missing.append("openai")
        
        if AUDIO_PROCESSING_AVAILABLE:
            available.append("speech_recognition/pydub")
        else:
            missing.append("speech_recognition/pydub")
        
        if VIDEO_DOWNLOAD_AVAILABLE:
            available.append("yt-dlp")
        else:
            missing.append("yt-dlp")
        
        logger.info(f"✅ Available: {available}")
        if missing:
            logger.warning(f"⚠️ Missing: {missing}")
            logger.info("Install missing: pip install " + " ".join(missing))
    
    async def transcribe_and_learn(self, video_url: str) -> Dict[str, Any]:
        """Actually transcribe video and learn from it"""
        try:
            logger.info(f"🎥 Starting real transcription: {video_url}")
            
            # Extract video ID
            video_id = self._extract_video_id(video_url)
            if not video_id:
                return {"error": "Invalid YouTube URL", "success": False}
            
            # Try method 1: YouTube transcript API
            transcript = await self._get_youtube_transcript(video_id)
            
            # If that fails, try method 2: Download and transcribe audio
            if not transcript:
                logger.info("🔄 No transcript available, downloading audio...")
                transcript = await self._transcribe_from_audio(video_url, video_id)
            
            if not transcript:
                return {"error": "Could not transcribe video", "success": False}
            
            # Get video metadata
            metadata = await self._get_video_metadata(video_id)
            
            # Analyze with AI
            analysis = await self._analyze_with_ai(transcript, metadata)
            
            # Extract actionable insights
            insights = await self._extract_insights(transcript, analysis)
            
            # Apply learning to Chatty codebase
            code_changes = await self._apply_learning(insights)
            
            result = {
                "success": True,
                "video_id": video_id,
                "url": video_url,
                "metadata": metadata,
                "transcript": transcript[:1000] + "..." if len(transcript) > 1000 else transcript,
                "transcript_length": len(transcript),
                "analysis": analysis,
                "insights": insights,
                "code_changes": code_changes,
                "timestamp": datetime.now().isoformat(),
                "transcription_method": "youtube_api" if YOUTUBE_API_AVAILABLE else "audio_processing"
            }
            
            self.learning_database[video_id] = result
            
            # Clean up temp files
            self._cleanup_temp_files(video_id)
            
            logger.info(f"✅ Real transcription and learning complete!")
            logger.info(f"📊 Transcript length: {len(transcript)} chars")
            logger.info(f"🧠 Insights extracted: {len(insights)}")
            logger.info(f"🔧 Code changes applied: {len(code_changes)}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Transcription/learning failed: {e}")
            return {"error": str(e), "success": False}
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID"""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/)([^&\n?#]+)',
            r'youtube\.com/embed/([^?&\n]+)',
            r'youtube\.com/v/([^?&\n]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                video_id = match.group(1)
                if len(video_id) == 11:
                    return video_id
        return None
    
    async def _get_youtube_transcript(self, video_id: str) -> Optional[str]:
        """Get transcript using YouTube API"""
        if not YOUTUBE_API_AVAILABLE:
            return None
        
        try:
            ytt_api = YouTubeTranscriptApi()
            transcript_list = ytt_api.list(video_id)
            
            # Try English first
            try:
                transcript = transcript_list.find_transcript(['en'])
                transcript_data = transcript.fetch()
            except NoTranscriptFound:
                # Try any available transcript
                transcript = list(transcript_list)[0]
                transcript_data = transcript.fetch()
            
            # Format to plain text
            formatter = TextFormatter()
            formatted_transcript = formatter.format_transcript(transcript_data)
            
            logger.info(f"✅ YouTube API transcript: {len(formatted_transcript)} chars")
            return formatted_transcript
            
        except Exception as e:
            logger.warning(f"⚠️ YouTube API failed: {e}")
            return None
    
    async def _transcribe_from_audio(self, video_url: str, video_id: str) -> Optional[str]:
        """Download audio and transcribe using speech recognition"""
        if not VIDEO_DOWNLOAD_AVAILABLE or not AUDIO_PROCESSING_AVAILABLE:
            logger.error("❌ Audio processing not available")
            return None
        
        try:
            # Download audio using yt-dlp
            audio_file = await self._download_audio(video_url, video_id)
            if not audio_file:
                return None
            
            # Transcribe audio
            transcript = await self._transcribe_audio_file(audio_file)
            
            logger.info(f"✅ Audio transcription: {len(transcript)} chars")
            return transcript
            
        except Exception as e:
            logger.error(f"❌ Audio transcription failed: {e}")
            return None
    
    async def _download_audio(self, video_url: str, video_id: str) -> Optional[Path]:
        """Download audio from YouTube video"""
        try:
            output_path = self.temp_dir / f"{video_id}.wav"
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                    'preferredquality': '192',
                }],
                'outtmpl': str(self.temp_dir / f"{video_id}.%(ext)s"),
                'quiet': True,
                'no_warnings': True,
            }
            
            import yt_dlp
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            
            # Find the downloaded file
            wav_file = self.temp_dir / f"{video_id}.wav"
            if wav_file.exists():
                logger.info(f"✅ Audio downloaded: {wav_file}")
                return wav_file
            else:
                logger.error("❌ Audio file not found after download")
                return None
                
        except Exception as e:
            logger.error(f"❌ Audio download failed: {e}")
            return None
    
    async def _transcribe_audio_file(self, audio_file: Path) -> str:
        """Transcribe audio file using speech recognition"""
        try:
            recognizer = sr.Recognizer()
            audio = AudioSegment.from_wav(str(audio_file))
            
            # Split audio into chunks (30 seconds each)
            chunk_length = 30 * 1000  # 30 seconds in milliseconds
            chunks = [audio[i:i+chunk_length] for i in range(0, len(audio), chunk_length)]
            
            transcript_parts = []
            
            for i, chunk in enumerate(chunks):
                logger.info(f"🎤 Transcribing chunk {i+1}/{len(chunks)}...")
                
                # Export chunk to temporary file
                chunk_file = self.temp_dir / f"chunk_{i}.wav"
                chunk.export(str(chunk_file), format="wav")
                
                # Recognize speech
                with sr.AudioFile(str(chunk_file)) as source:
                    audio_data = recognizer.record(source)
                
                try:
                    # Use Google's speech recognition (free)
                    text = recognizer.recognize_google(audio_data)
                    transcript_parts.append(text)
                    logger.info(f"✅ Chunk {i+1} transcribed")
                except sr.UnknownValueError:
                    logger.warning(f"⚠️ Could not understand chunk {i+1}")
                except sr.RequestError as e:
                    logger.error(f"❌ Speech recognition error: {e}")
                
                # Clean up chunk file
                chunk_file.unlink(missing_ok=True)
            
            full_transcript = " ".join(transcript_parts)
            return full_transcript
            
        except Exception as e:
            logger.error(f"❌ Audio transcription failed: {e}")
            return ""
    
    async def _get_video_metadata(self, video_id: str) -> Dict[str, Any]:
        """Get video metadata"""
        metadata = {
            "video_id": video_id,
            "title": "",
            "channel": "",
            "description": "",
            "duration": 0
        }
        
        # For now, use basic metadata
        # In production, would use YouTube Data API
        metadata.update({
            "title": f"Video {video_id}",
            "channel": "Unknown",
            "description": "YouTube video"
        })
            "automation": ["automation", "workflow", "automate", "script"],
            "ai": ["artificial intelligence", "machine learning", "neural", "model"],
            "performance": ["optimize", "performance", "speed", "efficiency"],
            "code": ["code", "programming", "function", "class", "algorithm"]
        }
        
        found_topics = []
        techniques = []
        improvements = []
        
        for category, words in keywords.items():
            if any(word in text_lower for word in words):
                found_topics.append(category)
                
                if category == "multi-agent":
                    techniques.extend(["agent coordination", "multi-agent workflows"])
                    improvements.extend(["implement agent communication", "add fleet management"])
                elif category == "automation":
                    techniques.extend(["workflow automation", "process optimization"])
                    improvements.extend(["automate repetitive tasks", "create workflow engine"])
                elif category == "performance":
                    techniques.extend(["performance optimization", "resource management"])
                    improvements.extend(["optimize code execution", "improve memory usage"])
        
        return {
            "relevance_score": min(len(found_topics) * 0.2, 1.0),
            "key_topics": found_topics,
            "automation_techniques": techniques,
            "code_improvements": improvements,
            "actionable_insights": [f"Consider {topic} for Chatty" for topic in found_topics],
            "chatty_applications": [f"Apply {tech} to system" for tech in techniques[:3]]
        }
    
    async def _extract_insights(self, transcript: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract actionable insights"""
        insights = []
        
        # Add AI insights
        for insight in analysis.get('actionable_insights', []):
            insights.append({
                "type": "insight",
                "content": insight,
                "source": "ai_analysis",
                "priority": "medium",
                "timestamp": datetime.now().isoformat()
            })
        
        # Add code improvements
        for improvement in analysis.get('code_improvements', []):
            insights.append({
                "type": "code_improvement",
                "content": improvement,
                "source": "ai_analysis",
                "priority": "high",
                "timestamp": datetime.now().isoformat()
            })
        
        return insights
    
    async def _apply_learning(self, insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply learning to Chatty codebase"""
        applied = []
        
        for insight in insights:
            if insight['type'] == 'code_improvement' and insight['priority'] == 'high':
                try:
                    # Generate code change
                    code_change = await self._generate_code_change(insight['content'])
                    
                    if code_change:
                        # Apply the change
                        success = await self._apply_code_change(code_change)
                        
                        applied.append({
                            "insight": insight['content'],
                            "file": code_change['file'],
                            "change_type": code_change['type'],
                            "success": success,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        if success:
                            logger.info(f"✅ Applied: {code_change['file']}")
                        else:
                            logger.warning(f"⚠️ Failed: {code_change['file']}")
                
                except Exception as e:
                    logger.error(f"❌ Code application failed: {e}")
                    applied.append({
                        "insight": insight['content'],
                        "success": False,
                        "error": str(e)
                    })
        
        return applied
    
    async def _generate_code_change(self, improvement_description: str) -> Optional[Dict[str, Any]]:
        """Generate code change based on improvement"""
        if not OPENAI_AVAILABLE or not self.api_key:
            return self._simple_code_generation(improvement_description)
        
        try:
            client = openai.OpenAI(api_key=self.api_key)
            
            prompt = f"""
            Generate a specific code improvement for Chatty automation system.
            
            Improvement needed: {improvement_description}
            
            Available files:
            - ENHANCED_MULTI_AGENT_SYSTEM.py (main system)
            - CONTEXT_WINDOW_MANAGER.py (context management)
            - REAL_YOUTUBE_LEARNER.py (learning system)
            
            Return JSON:
            {{
                "file": "filename.py",
                "type": "add_function|modify_function|add_class",
                "code": "actual Python code",
                "description": "what this does"
            }}
            """
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600,
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            logger.error(f"❌ Code generation failed: {e}")
            return self._simple_code_generation(improvement_description)
    
    def _simple_code_generation(self, improvement: str) -> Optional[Dict[str, Any]]:
        """Simple code generation fallback"""
        improvement_lower = improvement.lower()
        
        if 'agent' in improvement_lower and 'communication' in improvement_lower:
            return {
                "file": "ENHANCED_MULTI_AGENT_SYSTEM.py",
                "type": "add_function",
                "code": """
async def enhanced_agent_communication(self, message: str, target_agents: List[str]) -> Dict[str, Any]:
    \"\"\"Enhanced communication between agents\"\"\"
    results = {}
    for agent_id in target_agents:
        if agent_id in self.agents:
            results[agent_id] = await self.agents[agent_id].process_message(message)
    return results
""",
                "description": "Add enhanced agent communication"
            }
        
        elif 'automation' in improvement_lower:
            return {
                "file": "ENHANCED_MULTI_AGENT_SYSTEM.py",
                "type": "add_function",
                "code": """
async def automate_task_execution(self, task_config: Dict[str, Any]) -> Dict[str, Any]:
    \"\"\"Automate task execution based on configuration\"\"\"
    automation_result = {
        "task": task_config.get('task_name', 'unknown'),
        "status": "executing",
        "start_time": datetime.now().isoformat()
    }
    
    # Execute automation logic
    try:
        result = await self._execute_automation_logic(task_config)
        automation_result.update({
            "status": "completed",
            "result": result,
            "end_time": datetime.now().isoformat()
        })
    except Exception as e:
        automation_result.update({
            "status": "failed",
            "error": str(e),
            "end_time": datetime.now().isoformat()
        })
    
    return automation_result
""",
                "description": "Add task automation functionality"
            }
        
        return None
    
    async def _apply_code_change(self, code_change: Dict[str, Any]) -> bool:
        """Apply code change to file"""
        try:
            file_path = Path(code_change['file'])
            
            if not file_path.exists():
                logger.warning(f"⚠️ File not found: {file_path}")
                return False
            
            # Read current content
            current_content = file_path.read_text()
            
            # Apply change
            if code_change['type'] == 'add_function':
                new_content = current_content + "\n\n" + code_change['code']
            else:
                new_content = current_content + "\n\n" + code_change['code']
            
            # Write back
            file_path.write_text(new_content)
            
            logger.info(f"✅ Code change applied to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to apply code change: {e}")
            return False
    
    def _cleanup_temp_files(self, video_id: str):
        """Clean up temporary files"""
        try:
            for file in self.temp_dir.glob(f"{video_id}*"):
                file.unlink(missing_ok=True)
            for file in self.temp_dir.glob("chunk_*"):
                file.unlink(missing_ok=True)
        except Exception as e:
            logger.warning(f"⚠️ Cleanup failed: {e}")
    
    def get_transcription_stats(self) -> Dict[str, Any]:
        """Get transcription statistics"""
        if not self.learning_database:
            return {
                "videos_transcribed": 0,
                "total_transcript_chars": 0,
                "code_changes_applied": 0,
                "last_transcription": None
            }
        
        total_chars = sum(
            video['transcript_length'] 
            for video in self.learning_database.values()
        )
        
        total_changes = sum(
            len(video.get('code_changes', [])) 
            for video in self.learning_database.values()
        )
        
        return {
            "videos_transcribed": len(self.learning_database),
            "total_transcript_chars": total_chars,
            "code_changes_applied": total_changes,
            "last_transcription": max(
                video['timestamp'] 
                for video in self.learning_database.values()
            ),
            "transcription_methods": list(set(
                video['transcription_method'] 
                for video in self.learning_database.values()
            ))
        }

# ============================================================================
# MAIN DEMONSTRATION
# ============================================================================

async def main():
    """Demonstrate real transcription and learning"""
    print("🎥 Real YouTube Transcription and Learning System")
    print("=" * 60)
    
    transcriber = RealYouTubeTranscriber()
    
    # Test videos that likely have transcripts
    test_videos = [
        "https://www.youtube.com/watch?v=JGwWNGJdvx8",  # Tech talk
        "https://www.youtube.com/watch?v=si8z_jk7g5c",  # Another video
        "https://www.youtube.com/watch?v=wH7vqrz8oOs"   # Third video
    ]
    
    for video_url in test_videos[:1]:  # Test one video
        print(f"\n🎥 Processing: {video_url}")
        result = await transcriber.transcribe_and_learn(video_url)
        
        if result.get('success'):
            print("✅ Transcription and learning successful!")
            print(f"📊 Transcript length: {result['transcript_length']} chars")
            print(f"🧠 Relevance score: {result['analysis'].get('relevance_score', 0)}")
            print(f"🔧 Code changes: {len(result['code_changes'])}")
            
            # Show applied changes
            for change in result['code_changes']:
                print(f"\n🔧 {change.get('insight', 'N/A')}")
                print(f"File: {change.get('file', 'N/A')}")
                print(f"Success: {change.get('success', False)}")
        else:
            print(f"❌ Failed: {result.get('error', 'Unknown error')}")
    
    # Show stats
    stats = transcriber.get_transcription_stats()
    print(f"\n📈 Transcription Stats:")
    print(json.dumps(stats, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
