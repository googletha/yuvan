"""
Streaming Text-to-Speech System for Yuvan AI Assistant
Implements real-time TTS that starts speaking while generating response
"""

import asyncio
import threading
import queue
import time
from typing import Optional, Callable, Generator, List
from dataclasses import dataclass
from datetime import datetime
import re
import io
import json

# TTS libraries
import torch
import torchaudio
from scipy.io import wavfile
import numpy as np

# Silero TTS
from silero_tts import SileroTTS

# PyAudio for real-time audio playback
import pyaudio

@dataclass
class TTSChunk:
    """Represents a chunk of text to be converted to speech"""
    text: str
    priority: int
    timestamp: datetime
    chunk_id: str

class StreamingTTS:
    """Advanced streaming TTS system with real-time audio generation and playback"""
    
    def __init__(self, 
                 model_name: str = 'silero_tts',
                 language: str = 'en',
                 speaker: str = 'v3_en',
                 sample_rate: int = 48000,
                 device: str = 'cpu'):
        
        self.model_name = model_name
        self.language = language
        self.speaker = speaker
        self.sample_rate = sample_rate
        self.device = device
        
        # Audio settings
        self.chunk_size = 1024
        self.format = pyaudio.paFloat32
        self.channels = 1
        
        # Initialize PyAudio
        self.audio = pyaudio.PyAudio()
        self.audio_stream = None
        
        # Text processing queues
        self.text_queue = queue.Queue()
        self.audio_queue = queue.Queue()
        
        # Control flags
        self.is_streaming = False
        self.is_speaking = False
        self.should_stop = False
        
        # Threading
        self.text_processor_thread = None
        self.audio_player_thread = None
        
        # TTS model
        self.tts_model = None
        self._initialize_tts_model()
        
        # Text processing settings
        self.sentence_endings = ['.', '!', '?', '\n']
        self.pause_patterns = [',', ';', ':', '--', '...']
        self.min_chunk_length = 10
        self.max_chunk_length = 200
        
        # Statistics
        self.stats = {
            'chunks_processed': 0,
            'total_audio_time': 0,
            'processing_time': 0,
            'started_at': None
        }
    
    def _initialize_tts_model(self):
        """Initialize the TTS model"""
        try:
            if self.model_name == 'silero_tts':
                # Use Silero TTS
                torch.set_grad_enabled(False)
                
                # Load model
                model, example_text = torch.hub.load(
                    repo_or_dir='snakers4/silero-tts',
                    model='silero_tts',
                    language=self.language,
                    speaker=self.speaker
                )
                
                model.to(self.device)
                self.tts_model = model
                
                print(f"Silero TTS model loaded: {self.speaker}")
                
        except Exception as e:
            print(f"Error initializing TTS model: {e}")
            self.tts_model = None
    
    def start_streaming(self):
        """Start the streaming TTS system"""
        if self.is_streaming:
            return
        
        self.is_streaming = True
        self.should_stop = False
        self.stats['started_at'] = datetime.now()
        
        # Initialize audio stream
        self._init_audio_stream()
        
        # Start worker threads
        self.text_processor_thread = threading.Thread(target=self._text_processor_worker, daemon=True)
        self.audio_player_thread = threading.Thread(target=self._audio_player_worker, daemon=True)
        
        self.text_processor_thread.start()
        self.audio_player_thread.start()
        
        print("Streaming TTS started")
    
    def stop_streaming(self):
        """Stop the streaming TTS system"""
        if not self.is_streaming:
            return
        
        self.should_stop = True
        self.is_streaming = False
        self.is_speaking = False
        
        # Clear queues
        while not self.text_queue.empty():
            try:
                self.text_queue.get_nowait()
            except queue.Empty:
                break
        
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break
        
        # Close audio stream
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
            self.audio_stream = None
        
        print("Streaming TTS stopped")
    
    def _init_audio_stream(self):
        """Initialize PyAudio stream for real-time playback"""
        try:
            self.audio_stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                output=True,
                frames_per_buffer=self.chunk_size
            )
        except Exception as e:
            print(f"Error initializing audio stream: {e}")
            self.audio_stream = None
    
    def add_text(self, text: str, priority: int = 1):
        """Add text to the processing queue"""
        if not text or not text.strip():
            return
        
        # Split text into chunks for better streaming
        chunks = self._split_text_into_chunks(text)
        
        for i, chunk in enumerate(chunks):
            if chunk.strip():
                tts_chunk = TTSChunk(
                    text=chunk.strip(),
                    priority=priority,
                    timestamp=datetime.now(),
                    chunk_id=f"{int(time.time())}_{i}"
                )
                self.text_queue.put(tts_chunk)
    
    def add_text_stream(self, text_generator: Generator[str, None, None]):
        """Add text from a generator (for streaming responses)"""
        accumulated_text = ""
        
        for text_chunk in text_generator:
            accumulated_text += text_chunk
            
            # Check if we have a complete sentence or enough text
            if self._should_process_accumulated_text(accumulated_text):
                # Find the best split point
                split_point = self._find_split_point(accumulated_text)
                
                if split_point > 0:
                    text_to_process = accumulated_text[:split_point]
                    accumulated_text = accumulated_text[split_point:].strip()
                    
                    self.add_text(text_to_process)
        
        # Process any remaining text
        if accumulated_text.strip():
            self.add_text(accumulated_text)
    
    def _split_text_into_chunks(self, text: str) -> List[str]:
        """Split text into appropriate chunks for TTS"""
        chunks = []
        
        # First, split by sentences
        sentences = self._split_by_sentences(text)
        
        current_chunk = ""
        for sentence in sentences:
            # If adding this sentence would make the chunk too long, save current chunk
            if len(current_chunk + sentence) > self.max_chunk_length and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        # Add the last chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _split_by_sentences(self, text: str) -> List[str]:
        """Split text by sentences"""
        # Use regex to split by sentence endings
        sentence_pattern = r'[.!?]+(?:\s+|$)'
        sentences = re.split(sentence_pattern, text)
        
        # Filter out empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def _should_process_accumulated_text(self, text: str) -> bool:
        """Check if accumulated text should be processed"""
        # Check for sentence endings
        for ending in self.sentence_endings:
            if ending in text:
                return True
        
        # Check length
        if len(text) >= self.max_chunk_length:
            return True
        
        # Check for pause patterns
        for pattern in self.pause_patterns:
            if pattern in text and len(text) >= self.min_chunk_length:
                return True
        
        return False
    
    def _find_split_point(self, text: str) -> int:
        """Find the best point to split accumulated text"""
        # Look for sentence endings first
        for ending in self.sentence_endings:
            pos = text.rfind(ending)
            if pos > self.min_chunk_length:
                return pos + 1
        
        # Look for pause patterns
        for pattern in self.pause_patterns:
            pos = text.rfind(pattern)
            if pos > self.min_chunk_length:
                return pos + len(pattern)
        
        # If text is too long, split at word boundary
        if len(text) > self.max_chunk_length:
            pos = text.rfind(' ', 0, self.max_chunk_length)
            if pos > self.min_chunk_length:
                return pos + 1
        
        return 0
    
    def _text_processor_worker(self):
        """Worker thread for processing text to audio"""
        while self.is_streaming and not self.should_stop:
            try:
                # Get text chunk from queue
                chunk = self.text_queue.get(timeout=0.1)
                
                # Generate audio
                start_time = time.time()
                audio_data = self._generate_audio(chunk.text)
                processing_time = time.time() - start_time
                
                if audio_data is not None:
                    # Add to audio queue
                    self.audio_queue.put({
                        'audio': audio_data,
                        'chunk_id': chunk.chunk_id,
                        'text': chunk.text,
                        'processing_time': processing_time
                    })
                    
                    # Update statistics
                    self.stats['chunks_processed'] += 1
                    self.stats['processing_time'] += processing_time
                
                self.text_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in text processor: {e}")
                continue
    
    def _audio_player_worker(self):
        """Worker thread for playing audio"""
        while self.is_streaming and not self.should_stop:
            try:
                # Get audio from queue
                audio_item = self.audio_queue.get(timeout=0.1)
                
                # Play audio
                self._play_audio(audio_item['audio'])
                
                # Update statistics
                audio_duration = len(audio_item['audio']) / self.sample_rate
                self.stats['total_audio_time'] += audio_duration
                
                self.audio_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in audio player: {e}")
                continue
    
    def _generate_audio(self, text: str) -> Optional[np.ndarray]:
        """Generate audio from text using TTS model"""
        if not self.tts_model:
            return None
        
        try:
            # Clean text
            text = self._clean_text_for_tts(text)
            
            if not text.strip():
                return None
            
            # Generate audio using Silero TTS
            audio = self.tts_model.apply_tts(
                text=text,
                speaker=self.speaker,
                sample_rate=self.sample_rate
            )
            
            # Convert to numpy array
            if isinstance(audio, torch.Tensor):
                audio_np = audio.cpu().numpy()
            else:
                audio_np = np.array(audio)
            
            # Ensure correct data type for PyAudio
            audio_np = audio_np.astype(np.float32)
            
            return audio_np
            
        except Exception as e:
            print(f"Error generating audio: {e}")
            return None
    
    def _clean_text_for_tts(self, text: str) -> str:
        """Clean text for better TTS output"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove markdown formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # Italic
        text = re.sub(r'`(.*?)`', r'\1', text)        # Code
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)  # Links
        
        # Replace common abbreviations
        text = re.sub(r'\bDr\.', 'Doctor', text)
        text = re.sub(r'\bMr\.', 'Mister', text)
        text = re.sub(r'\bMrs\.', 'Missus', text)
        text = re.sub(r'\bMs\.', 'Miss', text)
        text = re.sub(r'\betc\.', 'etcetera', text)
        text = re.sub(r'\be\.g\.', 'for example', text)
        text = re.sub(r'\bi\.e\.', 'that is', text)
        
        # Handle numbers and special characters
        text = re.sub(r'\$(\d+)', r'\1 dollars', text)
        text = re.sub(r'(\d+)%', r'\1 percent', text)
        
        return text
    
    def _play_audio(self, audio_data: np.ndarray):
        """Play audio data through PyAudio stream"""
        if not self.audio_stream or audio_data is None:
            return
        
        try:
            self.is_speaking = True
            
            # Convert to bytes for PyAudio
            audio_bytes = audio_data.tobytes()
            
            # Play in chunks
            chunk_size = self.chunk_size * 4  # 4 bytes per float32
            
            for i in range(0, len(audio_bytes), chunk_size):
                if self.should_stop:
                    break
                
                chunk = audio_bytes[i:i + chunk_size]
                self.audio_stream.write(chunk)
            
            self.is_speaking = False
            
        except Exception as e:
            print(f"Error playing audio: {e}")
            self.is_speaking = False
    
    def wait_until_finished(self, timeout: Optional[float] = None):
        """Wait until all queued text has been spoken"""
        start_time = time.time()
        
        while (self.text_queue.qsize() > 0 or 
               self.audio_queue.qsize() > 0 or 
               self.is_speaking):
            
            if timeout and (time.time() - start_time) > timeout:
                break
            
            time.sleep(0.1)
    
    def clear_queue(self):
        """Clear all pending text and audio"""
        while not self.text_queue.empty():
            try:
                self.text_queue.get_nowait()
            except queue.Empty:
                break
        
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break
    
    def get_queue_status(self) -> dict:
        """Get current queue status"""
        return {
            'text_queue_size': self.text_queue.qsize(),
            'audio_queue_size': self.audio_queue.qsize(),
            'is_streaming': self.is_streaming,
            'is_speaking': self.is_speaking
        }
    
    def get_statistics(self) -> dict:
        """Get TTS statistics"""
        current_stats = self.stats.copy()
        
        if current_stats['started_at']:
            running_time = (datetime.now() - current_stats['started_at']).total_seconds()
            current_stats['running_time'] = running_time
            
            if current_stats['chunks_processed'] > 0:
                current_stats['avg_processing_time'] = (
                    current_stats['processing_time'] / current_stats['chunks_processed']
                )
        
        current_stats.update(self.get_queue_status())
        
        return current_stats
    
    def set_speaker(self, speaker: str):
        """Change TTS speaker"""
        self.speaker = speaker
        # Reinitialize model with new speaker
        self._initialize_tts_model()
    
    def set_speed(self, speed: float):
        """Set speech speed (1.0 = normal, 0.5 = half speed, 2.0 = double speed)"""
        # This would require model-specific implementation
        pass
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.stop_streaming()
        
        if self.audio_stream:
            self.audio_stream.close()
        
        if self.audio:
            self.audio.terminate()

# Async wrapper for integration with async code
class AsyncStreamingTTS:
    """Async wrapper for StreamingTTS"""
    
    def __init__(self, *args, **kwargs):
        self.tts = StreamingTTS(*args, **kwargs)
        self.loop = None
    
    async def start_streaming(self):
        """Start streaming in async context"""
        self.loop = asyncio.get_running_loop()
        await self.loop.run_in_executor(None, self.tts.start_streaming)
    
    async def stop_streaming(self):
        """Stop streaming in async context"""
        await self.loop.run_in_executor(None, self.tts.stop_streaming)
    
    async def add_text(self, text: str, priority: int = 1):
        """Add text in async context"""
        await self.loop.run_in_executor(None, self.tts.add_text, text, priority)
    
    async def wait_until_finished(self, timeout: Optional[float] = None):
        """Wait until finished in async context"""
        await self.loop.run_in_executor(None, self.tts.wait_until_finished, timeout)
    
    def __getattr__(self, name):
        """Delegate other methods to the sync TTS instance"""
        return getattr(self.tts, name)

# Integration function for Yuvan
def create_streaming_response_with_tts(response_generator: Generator[str, None, None],
                                     tts_system: StreamingTTS) -> Generator[str, None, None]:
    """Create a response generator that feeds TTS while yielding text"""
    
    # Start TTS if not already started
    if not tts_system.is_streaming:
        tts_system.start_streaming()
    
    # Process the response stream
    accumulated_text = ""
    
    for chunk in response_generator:
        accumulated_text += chunk
        yield chunk
        
        # Add to TTS if we have enough text
        if len(accumulated_text) >= 50:  # Minimum chunk size
            # Find a good split point
            split_point = tts_system._find_split_point(accumulated_text)
            
            if split_point > 0:
                text_to_speak = accumulated_text[:split_point]
                accumulated_text = accumulated_text[split_point:].strip()
                
                tts_system.add_text(text_to_speak)
    
    # Add any remaining text
    if accumulated_text.strip():
        tts_system.add_text(accumulated_text)