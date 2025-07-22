import pyttsx3
import speech_recognition as sr
from yuvan.task_handler import TaskHandler

# Initialize the text-to-speech engine
engine = pyttsx3.init()

def speak(text):
    """Converts text to speech."""
    engine.say(text)
    engine.runAndWait()

def listen():
    """Listens for voice input and converts it to text."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.pause_threshold = 1
        audio = r.listen(source)

    try:
        print("Recognizing...")
        query = r.recognize_google(audio, language='en-in')
        print(f"You said: {query}\n")
    except Exception as e:
        print("Say that again please...")
        return "None"
    return query

def main():
    """Main function for the Yuvan AI assistant."""
    task_handler = TaskHandler()
    print("Yuvan AI Operational Assistant")
    speak("Yuvan AI Operational Assistant")
    print("Choose your input method: (1) Text or (2) Voice")
    speak("Choose your input method: 1 for Text or 2 for Voice")
    
    choice = input("Enter choice (1/2): ")

    if choice == '1':
        print("Text mode selected.")
        speak("Text mode selected.")
    elif choice == '2':
        print("Voice mode selected.")
        speak("Voice mode selected.")
    else:
        print("Invalid choice. Defaulting to text mode.")
        speak("Invalid choice. Defaulting to text mode.")
        choice = '1'


    while True:
        try:
            if choice == '1':
                user_input = input("You: ")
            else:
                user_input = listen().lower()
            
            if 'exit' in user_input:
                speak("Goodbye!")
                break
            
            # Process the command using the TaskHandler
            response = task_handler.process_command(user_input)
            print(f"Yuvan: {response}")
            speak(response)

        except KeyboardInterrupt:
            speak("Goodbye!")
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            break

if __name__ == "__main__":
    main() 