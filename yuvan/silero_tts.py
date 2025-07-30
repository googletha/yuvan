"""
Silero TTS System for Yuvan
Real-time text-to-speech using Silero with asyncio support
"""

import asyncio
import torch
import torchaudio
import tempfile
import os
import threading
import queue
from typing import Optional, Callable
import numpy as np

class SileroTTS:
    def __init__(self, device: str = "cpu", language: str = "en", speaker: str = "en_0"):
        """
        Initialize Silero TTS
        
        Args:
            device: Device to use ('cpu' or 'cuda')
            language: Language code ('en', 'de', 'es', 'fr', 'it', 'pl', 'pt', 'tr', 'ru')
            speaker: Speaker ID (e.g., 'en_0', 'en_1', etc.)
        """
        self.device = device
        self.language = language
        self.speaker = speaker
        self.model = None
        self.sample_rate = 24000
        self.is_initialized = False
        self.audio_queue = asyncio.Queue()
        self.is_speaking = False
        self.stop_speaking = False
        
        # Initialize in a separate thread to avoid blocking
        self.init_thread = threading.Thread(target=self._initialize_model, daemon=True)
        self.init_thread.start()
    
    def _initialize_model(self):
        """Initialize the Silero model (blocking)"""
        try:
            # Load Silero TTS model
            self.model, _ = torch.hub.load(
                repo_or_dir='snakers4/silero-models',
                model='silero_tts',
                language=self.language,
                speaker=self.speaker
            )
            self.model.to(self.device)
            self.is_initialized = True
            print(f"✅ Silero TTS initialized successfully! (Language: {self.language}, Speaker: {self.speaker})")
        except Exception as e:
            print(f"❌ Failed to initialize Silero TTS: {e}")
            self.is_initialized = False
    
    async def wait_for_initialization(self, timeout: float = 30.0):
        """Wait for model initialization to complete"""
        start_time = asyncio.get_event_loop().time()
        while not self.is_initialized:
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError("Silero TTS initialization timed out")
            await asyncio.sleep(0.1)
    
    async def synthesize_speech(self, text: str) -> Optional[str]:
        """
        Synthesize speech from text asynchronously
        
        Args:
            text: Text to synthesize
            
        Returns:
            Path to generated audio file or None if failed
        """
        if not text or not text.strip():
            return None
        
        # Wait for initialization if needed
        if not self.is_initialized:
            await self.wait_for_initialization()
        
        try:
            # Run synthesis in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            audio_path = await loop.run_in_executor(
                None, self._synthesize_speech_sync, text
            )
            return audio_path
        except Exception as e:
            print(f"Error in speech synthesis: {e}")
            return None
    
    def _synthesize_speech_sync(self, text: str) -> Optional[str]:
        """Synchronous speech synthesis (runs in thread pool)"""
        try:
            # Generate audio
            audio = self.model.apply_tts(
                text=text,
                speaker=self.speaker,
                sample_rate=self.sample_rate
            )
            
            # Convert to numpy array
            audio_np = audio.numpy()
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(
                suffix='.wav', 
                delete=False,
                dir=tempfile.gettempdir()
            )
            
            # Save audio
            torchaudio.save(
                temp_file.name,
                torch.tensor(audio_np).unsqueeze(0),
                self.sample_rate
            )
            
            return temp_file.name
            
        except Exception as e:
            print(f"Error in synchronous speech synthesis: {e}")
            return None
    
    async def speak_text(self, text: str, callback: Optional[Callable] = None):
        """
        Speak text asynchronously
        
        Args:
            text: Text to speak
            callback: Optional callback function to call when done
        """
        if not text or not text.strip():
            return
        
        # Add to audio queue
        await self.audio_queue.put((text, callback))
        
        # Start audio processing if not already running
        if not self.is_speaking:
            asyncio.create_task(self._process_audio_queue())
    
    async def _process_audio_queue(self):
        """Process audio queue asynchronously"""
        self.is_speaking = True
        
        try:
            while not self.audio_queue.empty() and not self.stop_speaking:
                text, callback = await self.audio_queue.get()
                
                if self.stop_speaking:
                    break
                
                # Synthesize speech
                audio_path = await self.synthesize_speech(text)
                
                if audio_path and os.path.exists(audio_path):
                    # Play audio asynchronously
                    await self._play_audio_async(audio_path)
                    
                    # Clean up
                    try:
                        os.remove(audio_path)
                    except:
                        pass
                    
                    # Call callback if provided
                    if callback:
                        try:
                            callback()
                        except:
                            pass
                else:
                    print(f"Failed to synthesize speech for: {text[:50]}...")
                
                # Mark task as done
                self.audio_queue.task_done()
                
        except Exception as e:
            print(f"Error in audio queue processing: {e}")
        finally:
            self.is_speaking = False
    
    async def _play_audio_async(self, audio_path: str):
        """Play audio file asynchronously"""
        try:
            # Use pygame for audio playback in a separate thread
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._play_audio_sync, audio_path)
        except Exception as e:
            print(f"Error playing audio: {e}")
    
    def _play_audio_sync(self, audio_path: str):
        """Synchronous audio playback (runs in thread pool)"""
        try:
            import pygame
            pygame.mixer.init(frequency=24000, size=-16, channels=1, buffer=512)
            pygame.mixer.music.load(audio_path)
            pygame.mixer.music.play()
            
            # Wait for audio to finish
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)
                
        except Exception as e:
            print(f"Error in synchronous audio playback: {e}")
    
    async def stop_speaking_async(self):
        """Stop speaking asynchronously"""
        self.stop_speaking = True
        # Clear the queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
                self.audio_queue.task_done()
            except asyncio.QueueEmpty:
                break
    
    def cleanup(self):
        """Clean up resources"""
        self.stop_speaking = True
        if hasattr(self, 'model') and self.model is not None:
            del self.model
            self.model = None

# Global Silero TTS instance
silero_tts = None

async def get_silero_tts() -> SileroTTS:
    """Get the global Silero TTS instance"""
    global silero_tts
    if silero_tts is None:
        silero_tts = SileroTTS(language="en", speaker="en_0")
        # Wait for initialization
        await silero_tts.wait_for_initialization()
    return silero_tts

async def speak_text_async(text: str, callback: Optional[Callable] = None):
    """
    Convenience function to speak text asynchronously
    
    Args:
        text: Text to speak
        callback: Optional callback function
    """
    tts = await get_silero_tts()
    await tts.speak_text(text, callback)

async def stop_speaking_async():
    """Stop speaking asynchronously"""
    global silero_tts
    if silero_tts:
        await silero_tts.stop_speaking_async()

def cleanup_silero_tts():
    """Clean up Silero TTS resources"""
    global silero_tts
    if silero_tts:
        silero_tts.cleanup()
        silero_tts = None 