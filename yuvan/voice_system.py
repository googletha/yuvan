"""
Yuvan Voice System using Gradio Client
Converts Yuvan's text responses to audio using the provided model
"""

import os
import tempfile
import time
from gradio_client import Client
import pygame
import threading
from typing import Optional

class YuvanVoice:
    def __init__(self, hf_token: str = None):
        """
        Initialize Yuvan's voice system
        
        Args:
            hf_token: Hugging Face token for accessing the private space
        """
        # Import configuration
        import yuvan_config
        voice_config = yuvan_config.get_voice_config()
        
        self.hf_token = hf_token or voice_config["hf_token"]
        self.model_url = voice_config["model_url"]
        self.voice_preset = voice_config["voice_preset"]
        self.template_name = voice_config["template_name"]
        self.system_prompt = voice_config["system_prompt"]
        self.max_completion_tokens = voice_config["max_completion_tokens"]
        self.temperature = voice_config["temperature"]
        self.top_p = voice_config["top_p"]
        self.top_k = voice_config["top_k"]
        self.ras_win_len = voice_config["ras_win_len"]
        self.ras_win_max_num_repeat = voice_config["ras_win_max_num_repeat"]
        self.async_playback = voice_config["async_playback"]
        self.fallback_to_text = voice_config["fallback_to_text"]
        
        self.client = None
        self.is_initialized = False
        self.is_speaking = False
        self.audio_queue = []
        self.audio_thread = None
        
        # Initialize pygame mixer for audio playback
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.audio_available = True
        except Exception as e:
            print(f"Warning: Audio system not available: {e}")
            self.audio_available = False
    
    def initialize_client(self):
        """Initialize the Gradio client"""
        try:
            self.client = Client(self.model_url, hf_token=self.hf_token)
            self.is_initialized = True
            print("✅ Voice system initialized successfully!")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize voice system: {e}")
            self.is_initialized = False
            return False
    
    def text_to_speech(self, text: str, system_prompt: str = None) -> Optional[str]:
        """
        Convert text to speech using the Higgs Audio v2 model
        
        Args:
            text: The text to convert to speech
            system_prompt: System prompt for the model (uses default if None)
            
        Returns:
            Path to the generated audio file or None if failed
        """
        if not self.is_initialized:
            if not self.initialize_client():
                return None
        
        # Use default system prompt if none provided
        if system_prompt is None:
            system_prompt = self.system_prompt
        
        try:
            # First, apply the template to get the proper system prompt
            template_result = self.client.predict(
                template_name=self.template_name,
                api_name="/apply_template"
            )
            
            # The template result contains [system_prompt, input_text, html, voice_preset, ras_win_len]
            # We can use the returned system prompt or our custom one
            if template_result and len(template_result) >= 1:
                # Use the template's system prompt as base and append our custom prompt
                template_system_prompt = template_result[0]
                combined_system_prompt = f"{template_system_prompt}\n\n{system_prompt}"
            else:
                combined_system_prompt = system_prompt
            
            # Call the generate_speech API
            result = self.client.predict(
                text=text,
                voice_preset=self.voice_preset,
                reference_audio=None,
                reference_text=None,
                max_completion_tokens=self.max_completion_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                top_k=self.top_k,
                system_prompt=combined_system_prompt,
                stop_strings={"headers":["stops"],"data":[["<|end_of_text|>"],["<|eot_id|>"]],"metadata":None},
                ras_win_len=self.ras_win_len,
                ras_win_max_num_repeat=self.ras_win_max_num_repeat,
                api_name="/generate_speech"
            )
            
            # The result is a tuple [model_response, audio_file_path]
            if result and len(result) >= 2:
                audio_file_path = result[1]
                if audio_file_path and os.path.exists(audio_file_path):
                    return audio_file_path
                else:
                    print(f"Warning: No audio file generated for text: {text[:50]}...")
                    return None
            else:
                print(f"Warning: Unexpected result format: {result}")
                return None
                
        except Exception as e:
            print(f"Error in text-to-speech: {e}")
            return None
    
    def play_audio(self, audio_file_path: str):
        """Play audio file using pygame"""
        if not self.audio_available:
            print("Audio playback not available")
            return
        
        try:
            # Load and play the audio
            pygame.mixer.music.load(audio_file_path)
            pygame.mixer.music.play()
            
            # Wait for audio to finish
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
                
        except Exception as e:
            print(f"Error playing audio: {e}")
    
    def speak(self, text: str, system_prompt: str = None):
        """
        Convert text to speech and play it
        
        Args:
            text: The text to speak
            system_prompt: System prompt for the model (uses default if None)
        """
        if not text or not text.strip():
            return
        
        # Generate audio
        audio_file = self.text_to_speech(text, system_prompt)
        
        if audio_file:
            # Play the audio
            self.play_audio(audio_file)
            
            # Clean up the temporary file
            try:
                os.remove(audio_file)
            except:
                pass  # Ignore cleanup errors
        elif self.fallback_to_text:
            # Fallback to text output if voice fails
            print(f"Yuvan says: {text}")
    
    def speak_async(self, text: str, system_prompt: str = None):
        """
        Convert text to speech and play it asynchronously (non-blocking)
        
        Args:
            text: The text to speak
            system_prompt: System prompt for the model (uses default if None)
        """
        if not text or not text.strip():
            return
        
        # Start audio generation and playback in a separate thread
        thread = threading.Thread(
            target=self.speak,
            args=(text, system_prompt),
            daemon=True
        )
        thread.start()
    
    def stop_speaking(self):
        """Stop any currently playing audio"""
        if self.audio_available:
            try:
                pygame.mixer.music.stop()
            except:
                pass
    
    def cleanup(self):
        """Clean up resources"""
        self.stop_speaking()
        if self.audio_available:
            pygame.mixer.quit()

# Global voice instance
voice_system = None

def get_voice_system() -> YuvanVoice:
    """Get the global voice system instance"""
    global voice_system
    if voice_system is None:
        voice_system = YuvanVoice()
    return voice_system

def speak_text(text: str, async_play: bool = True):
    """
    Convenience function to speak text
    
    Args:
        text: The text to speak
        async_play: Whether to play audio asynchronously
    """
    voice = get_voice_system()
    
    if async_play:
        voice.speak_async(text)
    else:
        voice.speak(text)

def stop_voice():
    """Stop any currently playing voice"""
    voice = get_voice_system()
    voice.stop_speaking()

def cleanup_voice():
    """Clean up voice system resources"""
    global voice_system
    if voice_system:
        voice_system.cleanup()
        voice_system = None 