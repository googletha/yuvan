"""
Enhanced Main Entry Point for Yuvan AI Assistant
Features: Memory, Autonomous Reasoning, Terminal Assistant, Document Processing,
Streaming TTS, File System Crawler, and App Launcher
"""

import speech_recognition as sr
import time
import platform
import sys
import asyncio
import signal
import atexit
from yuvan.enhanced_task_handler import create_enhanced_yuvan, EnhancedTaskHandler
from yuvan.voice_system import speak_text as speak, cleanup_voice

class EnhancedYuvanMain:
    """Enhanced Yuvan main application with all advanced features"""
    
    def __init__(self):
        self.task_handler: EnhancedTaskHandler = None
        self.running = True
        
        # Configuration
        self.enable_tts = True
        self.enable_voice_input = True
        self.enable_autonomous_mode = True
        
        # Setup cleanup handlers
        atexit.register(self.cleanup)
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\nReceived signal {signum}, shutting down gracefully...")
        self.running = False
        self.cleanup()
        sys.exit(0)
    
    def cleanup(self):
        """Cleanup all systems"""
        if self.task_handler:
            self.task_handler.cleanup()
        cleanup_voice()
        print("Yuvan shutdown complete.")
    
    def initialize(self):
        """Initialize enhanced Yuvan system"""
        print("=" * 60)
        print("🤖 YUVAN AI ASSISTANT - ENHANCED VERSION 🤖")
        print("=" * 60)
        print("Loading advanced capabilities...")
        print("• Memory System with Semantic Search")
        print("• Autonomous Reasoning (ReAct Framework)")
        print("• Terminal Assistant with Safe Command Execution")
        print("• Document Processing with OCR")
        print("• Streaming Text-to-Speech")
        print("• File System Crawler & Duplicate Finder")
        print("• Application Launcher & Manager")
        print("=" * 60)
        
        try:
            # Create enhanced task handler
            self.task_handler = create_enhanced_yuvan(
                enable_tts=self.enable_tts,
                scan_apps=True
            )
            
            # Show system status
            status = self.task_handler.get_system_status()
            print(f"\n✅ Yuvan Enhanced System Ready!")
            print(f"📊 Memory: {status['enhanced_features']['memory_system']['total_memories']} memories")
            print(f"🎤 Streaming TTS: {'Enabled' if status['enhanced_features']['streaming_tts']['enabled'] else 'Disabled'}")
            print(f"🧠 Autonomous Reasoning: {'Available' if status['enhanced_features']['reasoning_agent']['available'] else 'Unavailable'}")
            print(f"💻 Terminal Assistant: {'Available' if self.task_handler.terminal_assistant else 'Unavailable'}")
            print(f"📄 Document Processor: {'Available' if self.task_handler.document_processor else 'Unavailable'}")
            print(f"📁 File System Crawler: {'Available' if self.task_handler.fs_crawler else 'Unavailable'}")
            print(f"🚀 App Launcher: {'Available' if self.task_handler.app_launcher else 'Unavailable'}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error initializing Yuvan: {e}")
            return False
    
    def listen_for_wake_word(self, wake_word="yuvan"):
        """Continuously listens for the wake word and returns True if detected."""
        if not self.enable_voice_input:
            return False
        
        r = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                r.pause_threshold = 0.5
                audio = r.listen(source, timeout=1, phrase_time_limit=3)
            
            query = r.recognize_google(audio, language='en-in').lower()
            if wake_word in query:
                return True
        except (sr.UnknownValueError, sr.RequestError, sr.WaitTimeoutError):
            pass
        return False
    
    def listen_command(self):
        """Listens for a command after the wake word is detected."""
        if not self.enable_voice_input:
            return ""
        
        r = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                print("🎤 Listening for your command...")
                r.pause_threshold = 0.5
                audio = r.listen(source, timeout=10, phrase_time_limit=15)
            
            command = r.recognize_google(audio, language='en-in')
            print(f"👤 You said: {command}")
            return command
        except sr.UnknownValueError:
            print("❌ Sorry, I didn't catch that.")
            return ""
        except sr.RequestError as e:
            print(f"❌ Speech recognition error: {e}")
            return ""
        except sr.WaitTimeoutError:
            print("⏰ Listening timeout.")
            return ""
    
    def show_help(self):
        """Show help information"""
        help_text = """
🤖 YUVAN ENHANCED AI ASSISTANT - HELP
=====================================

BASIC COMMANDS:
• help - Show this help
• status - Show system status
• memory search <query> - Search memory
• save session - Save current session

AUTONOMOUS REASONING:
• "Yuvan, fix <problem>" - Autonomous problem solving
• "Yuvan, analyze <item>" - Autonomous analysis
• "analyze this <description>" - Deep analysis

DOCUMENT PROCESSING:
• "read <file.pdf>" - Process PDF document
• "process document <file>" - Process any supported document
• "ocr <file>" - Extract text using OCR

TERMINAL COMMANDS:
• "run <command>" - Execute terminal command safely
• "execute <command>" - Run system command

FILE SYSTEM:
• "scan <directory>" - Analyze directory
• "find duplicates in <path>" - Find duplicate files
• "find large files in <path>" - Find large files

APPLICATION MANAGEMENT:
• "launch <app>" - Launch application
• "open <app>" - Open application
• "close <app>" - Close application
• "list apps" - Show installed apps
• "running apps" - Show running processes

VOICE COMMANDS:
• Say "Yuvan" to activate voice mode
• Type commands or use voice input
• "exit" to quit

EXAMPLE COMMANDS:
• "Yuvan, analyze this Python file main.py"
• "read document.pdf"
• "run ls -la"
• "scan ~/Documents"
• "launch firefox"
• "memory search python projects"
=====================================
        """
        print(help_text)
    
    def run(self):
        """Main application loop"""
        if not self.initialize():
            print("❌ Failed to initialize Yuvan. Exiting.")
            return
        
        # Welcome message
        greeting = """
🎉 Welcome to Yuvan Enhanced AI Assistant! 
I now have deeper memory, autonomous reasoning, and many new capabilities.
Try saying "Yuvan, analyze this folder" or "help" for more commands.
        """
        print(greeting)
        
        # TTS greeting if enabled
        if self.task_handler.tts_enabled:
            self.task_handler.streaming_tts.add_text(
                "Hello! I'm Yuvan Enhanced. I now have advanced capabilities like autonomous reasoning, "
                "document processing, and file system analysis. How can I help you today?"
            )
        
        # Show quick start tips
        print("\n💡 QUICK START:")
        print("• Type commands directly or say 'Yuvan' for voice input")
        print("• Try: 'Yuvan, analyze this folder .' or 'help'")
        print("• Type 'exit' to quit")
        print("=" * 60)
        
        while self.running:
            try:
                print(f"\n{'🤖 Yuvan Enhanced' if self.task_handler.tts_enabled else '🤖 Yuvan'} > ", end='', flush=True)
                
                # Get user input (text or voice)
                user_input = input().strip()
                
                if not user_input:
                    # No text input, try voice
                    print("No text entered. Say 'Yuvan' to use voice commands...")
                    if self.listen_for_wake_word():
                        if self.task_handler.tts_enabled:
                            self.task_handler.streaming_tts.add_text("Yes? I'm listening.")
                        else:
                            speak("Yes? I'm listening.")
                        
                        command = self.listen_command()
                        if command:
                            user_input = command
                        else:
                            continue
                    else:
                        continue
                
                # Handle special commands
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("👋 Goodbye!")
                    if self.task_handler.tts_enabled:
                        self.task_handler.streaming_tts.add_text("Goodbye!")
                        self.task_handler.streaming_tts.wait_until_finished(timeout=3)
                    else:
                        speak("Goodbye!")
                    break
                
                elif user_input.lower() == 'help':
                    self.show_help()
                    continue
                
                elif user_input.lower() == 'status':
                    status = self.task_handler.get_system_status()
                    print(f"\n📊 YUVAN SYSTEM STATUS:")
                    print(f"Commands processed: {status['statistics']['commands_processed']}")
                    print(f"Autonomous sessions: {status['statistics']['autonomous_sessions']}")
                    print(f"Memory entries: {status['enhanced_features']['memory_system']['total_memories']}")
                    print(f"TTS enabled: {status['enhanced_features']['streaming_tts']['enabled']}")
                    continue
                
                elif user_input.lower().startswith('memory search '):
                    query = user_input[14:]  # Remove 'memory search '
                    results = self.task_handler.get_memory_search(query)
                    print(f"\n🧠 Memory search results for '{query}':")
                    for i, result in enumerate(results, 1):
                        print(f"{i}. {result}")
                    continue
                
                elif user_input.lower() == 'save session':
                    result = self.task_handler.save_session()
                    print(f"💾 {result}")
                    continue
                
                # Process command with enhanced handler
                print("🔄 Processing...")
                start_time = time.time()
                
                response = self.task_handler.process_command(user_input)
                
                processing_time = time.time() - start_time
                
                # Display response
                print(f"\n🤖 Yuvan: {response}")
                print(f"⏱️  Processed in {processing_time:.2f}s")
                
            except KeyboardInterrupt:
                print("\n\n👋 Interrupted by user. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ An error occurred: {e}")
                print("Yuvan is still running. Try another command.")
        
        self.running = False

def main():
    """Main entry point"""
    try:
        app = EnhancedYuvanMain()
        app.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()