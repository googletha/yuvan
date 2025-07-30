import speech_recognition as sr
import time
import platform
import sys
import asyncio
from yuvan.task_handler import TaskHandler
from yuvan.silero_tts import speak_text_async, stop_speaking_async, cleanup_silero_tts

# Silero TTS integration
async def speak_async(text):
    """Speak text using Silero TTS asynchronously"""
    await speak_text_async(text)

def listen_for_wake_word(wake_word="yuvan"):
    """Continuously listens for the wake word and returns True if detected."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening for wake word...")
        r.pause_threshold = 0.5  # Reduced from 1 second
        audio = r.listen(source)
    try:
        query = r.recognize_google(audio, language='en-in').lower()
        print(f"Heard: {query}")
        if wake_word in query:
            return True
    except Exception:
        pass
    return False

def listen_command():
    """Listens for a command after the wake word is detected."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening for your command...")
        r.pause_threshold = 0.5  # Reduced from 1 second
        audio = r.listen(source)
    try:
        command = r.recognize_google(audio, language='en-in')
        print(f"You said: {command}\n")
        return command
    except Exception:
        print("Sorry, I didn't catch that.")
        return ""

def main():
    """Main function for the Yuvan AI assistant."""
    task_handler = TaskHandler()
    
    # Initialize voice system
    print("Initializing Yuvan's voice system...")
    
    greeting = "Hello! I'm Yuvan, your AI assistant. How can I help you today?"
    print(greeting)
    speak(greeting)
    print("Type your request or say 'Yuvan' to talk to me!")
    speak("Type your request or say Yuvan to talk to me!")

    while True:
        try:
            print("\nYou (type or say 'Yuvan'): ", end='', flush=True)
            
            # Simple input method - just wait for Enter key
            if platform.system() == "Windows":
                import msvcrt
                user_input = ""
                while True:
                    if msvcrt.kbhit():
                        char = msvcrt.getwche()
                        if char == '\r' or char == '\n':
                            break
                        user_input += char
                    time.sleep(0.01)
                print()  # for newline after input
            else:
                user_input = input().strip()
            
            # Process text input
            if user_input:
                if 'exit' in user_input.lower():
                    speak("Goodbye!")
                    print("Goodbye!")
                    break
                response = task_handler.process_command(user_input)
                print(f"Yuvan: {response}")
                # Removed speak(response) to avoid double output
            else:
                # If no text input, offer voice option
                print("No text entered. Say 'Yuvan' to use voice commands, or type your request.")
                if listen_for_wake_word():
                    speak("Yes? I'm listening.")
                    command = listen_command()
                    if command:
                        if 'exit' in command.lower():
                            speak("Goodbye!")
                            print("Goodbye!")
                            break
                        response = task_handler.process_command(command)
                        print(f"Yuvan: {response}")
                        # Removed speak(response) to avoid double output
                    
        except KeyboardInterrupt:
            speak("Goodbye!")
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            break
    
    # Cleanup voice system
    cleanup_voice()

if __name__ == "__main__":
    main() 