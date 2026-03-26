#!/usr/bin/env python3
"""
CHATTY JARVIS Voice Module
==========================
Voice recognition and text-to-speech for JARVIS
Makes JARVIS truly like Iron Man's JARVIS - you can talk to it!

Features:
- Voice command recognition (speech-to-text)
- JARVIS voice responses (text-to-speech)
- Wake word detection ("Hey JARVIS")
- Voice-activated commands
"""

import os
import asyncio
import threading
import queue
from pathlib import Path
from typing import Optional, Callable, List
from dataclasses import dataclass


@dataclass
class VoiceConfig:
    """Voice configuration"""
    wake_word: str = "hey jarvis"
    language: str = "en-US"
    speech_rate: int = 175  # Words per minute
    voice_id: Optional[str] = None  # System-specific voice ID
    silence_timeout: float = 3.0  # Seconds of silence before processing


class JarvisVoice:
    """JARVIS Voice System - Speech recognition and synthesis"""
    
    def __init__(self, config: VoiceConfig = None):
        self.config = config or VoiceConfig()
        self.is_listening = False
        self.is_speaking = False
        self.audio_queue = queue.Queue()
        self.recognizer = None
        self.microphone = None
        self.tts_engine = None
        self._initialized = False
        
        # Callbacks
        self.on_wake_word: Optional[Callable] = None
        self.on_command: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
    
    def initialize(self) -> bool:
        """Initialize voice systems"""
        try:
            # Try speech_recognition for input
            try:
                import speech_recognition as sr
                self.recognizer = sr.Recognizer()
                self.microphone = sr.Microphone()
                
                # Calibrate for ambient noise
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                print("🎤 Speech recognition initialized")
            except ImportError:
                print("⚠️  speech_recognition not available (pip install SpeechRecognition)")
                print("   Voice input disabled")
            
            # Try pyttsx3 for output
            try:
                import pyttsx3
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty('rate', self.config.speech_rate)
                
                # List available voices
                voices = self.tts_engine.getProperty('voices')
                if voices:
                    # Try to find a male voice (JARVIS-like)
                    for voice in voices:
                        if 'male' in voice.name.lower() or 'david' in voice.name.lower():
                            self.tts_engine.setProperty('voice', voice.id)
                            break
                
                print("🔊 Text-to-speech initialized")
            except ImportError:
                print("⚠️  pyttsx3 not available (pip install pyttsx3)")
                print("   Voice output disabled")
            
            self._initialized = True
            return True
            
        except Exception as e:
            print(f"❌ Voice initialization error: {e}")
            return False
    
    def speak(self, text: str, block: bool = False):
        """Speak text using TTS"""
        if not self.tts_engine:
            print(f"🔊 (TTS disabled) {text}")
            return
        
        self.is_speaking = True
        
        def _speak():
            try:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            except Exception as e:
                print(f"TTS error: {e}")
            finally:
                self.is_speaking = False
        
        if block:
            _speak()
        else:
            threading.Thread(target=_speak, daemon=True).start()
    
    def listen_once(self, timeout: float = 5.0) -> Optional[str]:
        """Listen for one command"""
        if not self.recognizer or not self.microphone:
            print("🎤 Voice recognition not available")
            return None
        
        try:
            with self.microphone as source:
                print("🎤 Listening...")
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
            
            print("🧠 Processing speech...")
            text = self.recognizer.recognize_google(audio, language=self.config.language)
            print(f"📝 Heard: {text}")
            return text
            
        except Exception as e:
            print(f"Listening error: {e}")
            return None
    
    def listen_for_wake_word(self) -> bool:
        """Listen for wake word, return True if detected"""
        text = self.listen_once(timeout=3.0)
        if text:
            return self.config.wake_word.lower() in text.lower()
        return False
    
    def start_listening_loop(self):
        """Start continuous listening in background thread"""
        if not self.recognizer:
            print("Cannot start listening - recognizer not available")
            return
        
        self.is_listening = True
        
        def listen_loop():
            while self.is_listening:
                try:
                    # Listen for wake word
                    if self.listen_for_wake_word():
                        if self.on_wake_word:
                            self.on_wake_word()
                        
                        # Greet and listen for command
                        self.speak("Yes, sir?")
                        
                        command = self.listen_once(timeout=10.0)
                        if command:
                            if self.on_command:
                                self.on_command(command)
                    
                    asyncio.sleep(0.1)
                    
                except Exception as e:
                    if self.on_error:
                        self.on_error(str(e))
        
        threading.Thread(target=listen_loop, daemon=True).start()
        print(f"🎤 Listening for wake word: '{self.config.wake_word}'")
    
    def stop_listening(self):
        """Stop listening"""
        self.is_listening = False
        print("🛑 Voice listening stopped")


class JarvisVoiceCommands:
    """Predefined voice commands for JARVIS"""
    
    def __init__(self, jarvis_assistant):
        self.jarvis = jarvis_assistant
        self.commands = {
            "status": self._cmd_status,
            "help": self._cmd_help,
            "code": self._cmd_code,
            "analyze": self._cmd_analyze,
            "stop": self._cmd_stop,
            "exit": self._cmd_exit,
            "quit": self._cmd_exit,
        }
    
    async def process_voice_command(self, text: str) -> str:
        """Process a voice command"""
        text_lower = text.lower()
        
        # Find matching command
        for cmd, handler in self.commands.items():
            if cmd in text_lower:
                return await handler(text)
        
        # Default: treat as chat
        return await self.jarvis._generate_response(text)
    
    async def _cmd_status(self, text: str) -> str:
        """Handle status command"""
        return "All systems are operational, sir."
    
    async def _cmd_help(self, text: str) -> str:
        """Handle help command"""
        return "I can help you with coding, file operations, system management, and general questions. Just ask."
    
    async def _cmd_code(self, text: str) -> str:
        """Handle code command"""
        # Extract what to code
        parts = text.replace("code", "").strip()
        if parts:
            return await self.jarvis._generate_code(parts)
        return "What would you like me to code, sir?"
    
    async def _cmd_analyze(self, text: str) -> str:
        """Handle analyze command"""
        return "Analysis mode activated. What would you like me to analyze?"
    
    async def _cmd_stop(self, text: str) -> str:
        """Handle stop command"""
        return "Stopping current operations."
    
    async def _cmd_exit(self, text: str) -> str:
        """Handle exit command"""
        return "Goodbye, sir. JARVIS standing by."


# Voice-enabled JARVIS wrapper

class JarvisWithVoice:
    """JARVIS with voice capabilities"""
    
    def __init__(self, jarvis_assistant):
        self.jarvis = jarvis_assistant
        self.voice = JarvisVoice()
        self.voice_commands = JarvisVoiceCommands(jarvis_assistant)
        self.voice_enabled = False
    
    def enable_voice(self) -> bool:
        """Enable voice mode"""
        if self.voice.initialize():
            self.voice_enabled = True
            
            # Set up callbacks
            self.voice.on_wake_word = self._on_wake
            self.voice.on_command = self._on_command
            
            # Start listening
            self.voice.start_listening_loop()
            
            # Greeting
            self.voice.speak("JARVIS online and ready, sir.")
            
            return True
        return False
    
    def disable_voice(self):
        """Disable voice mode"""
        self.voice_enabled = False
        self.voice.stop_listening()
    
    def _on_wake(self):
        """Called when wake word detected"""
        print("🎤 Wake word detected!")
    
    def _on_command(self, command: str):
        """Called when command received"""
        asyncio.create_task(self._process_voice_command(command))
    
    async def _process_voice_command(self, command: str):
        """Process voice command and speak response"""
        try:
            response = await self.voice_commands.process_voice_command(command)
            print(f"🤖 JARVIS: {response}")
            
            if self.voice_enabled:
                self.voice.speak(response[:200])  # Limit response length for TTS
        except Exception as e:
            print(f"Error processing voice command: {e}")
    
    def speak(self, text: str):
        """Speak text"""
        if self.voice_enabled and self.voice.tts_engine:
            self.voice.speak(text)
        else:
            print(f"🔊 {text}")


# Simple voice test

if __name__ == "__main__":
    print("Testing JARVIS Voice Module")
    print("=" * 40)
    
    voice = JarvisVoice()
    
    if voice.initialize():
        print("\nTesting text-to-speech...")
        voice.speak("JARVIS online and ready, sir.", block=True)
        
        print("\nTesting speech recognition...")
        print("Say something:")
        result = voice.listen_once(timeout=5.0)
        
        if result:
            print(f"Recognized: {result}")
            voice.speak(f"I heard: {result}", block=True)
        else:
            print("No speech detected")
    else:
        print("Voice initialization failed")
