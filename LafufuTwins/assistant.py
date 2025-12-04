"""
Virtual Assistant Module
Handles speech recognition, text-to-speech, and Ollama integration
"""

import sys
from typing import Optional

import ollama
import pyttsx3
import speech_recognition as sr


class VirtualAssistant:
    """Virtual Assistant that listens, processes, and responds using Ollama"""

    def __init__(self, model_name: str = "llama2"):
        """
        Initialize the virtual assistant

        Args:
            model_name: The Ollama model to use (default: llama2)
        """
        self.model_name = model_name
        self.recognizer = sr.Recognizer()
        self.tts_engine = pyttsx3.init()
        self.conversation_history = []

        # Configure TTS engine
        self.tts_engine.setProperty("rate", 150)  # Speed of speech
        self.tts_engine.setProperty("volume", 0.9)  # Volume (0.0 to 1.0)

        print(f"Virtual Assistant initialized with model: {model_name}")

    def listen(self) -> Optional[str]:
        """
        Listen to microphone input and convert speech to text

        Returns:
            Transcribed text or None if recognition failed
        """
        with sr.Microphone() as source:
            print("\n🎤 Listening... (speak now)")

            # Adjust for ambient noise
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)

            try:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                print("🔄 Processing speech...")

                # Use Google Speech Recognition (free)
                text = self.recognizer.recognize_google(audio)
                print(f"📝 You said: {text}")
                return text

            except sr.WaitTimeoutError:
                print("⏱️  No speech detected")
                return None
            except sr.UnknownValueError:
                print("❌ Could not understand audio")
                return None
            except sr.RequestError as e:
                print(f"❌ Speech recognition error: {e}")
                return None

    def speak(self, text: str):
        """
        Convert text to speech and play it

        Args:
            text: The text to speak
        """
        print(f"🤖 Assistant: {text}")
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()

    def get_ollama_response(self, prompt: str) -> str:
        """
        Get response from Ollama model

        Args:
            prompt: The user's input text

        Returns:
            The model's response
        """
        try:
            print(f"🧠 Thinking with {self.model_name}...")

            # Add user message to conversation history
            self.conversation_history.append({"role": "user", "content": prompt})

            # Get response from Ollama
            response = ollama.chat(
                model=self.model_name, messages=self.conversation_history
            )

            assistant_message = response["message"]["content"]

            # Add assistant response to conversation history
            self.conversation_history.append(
                {"role": "assistant", "content": assistant_message}
            )

            return assistant_message

        except ollama.ResponseError as e:
            error_msg = f"Ollama error: {e}"
            print(f"❌ {error_msg}")
            return "I'm sorry, I encountered an error processing your request."
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            print(f"❌ {error_msg}")
            return "I'm sorry, something went wrong."

    def process_command(self, text: str) -> bool:
        """
        Process special commands

        Args:
            text: The command text

        Returns:
            True if should continue, False if should exit
        """
        text_lower = text.lower()

        # Exit commands
        if any(cmd in text_lower for cmd in ["exit", "quit", "goodbye", "bye"]):
            self.speak("Goodbye! Have a great day!")
            return False

        # Clear history command
        if "clear history" in text_lower or "reset conversation" in text_lower:
            self.conversation_history = []
            self.speak("Conversation history cleared.")
            return True

        return True

    def run(self):
        """Main loop for the virtual assistant"""
        self.speak("Hello! I'm your virtual assistant. How can I help you today?")

        while True:
            try:
                # Listen for user input
                user_input = self.listen()

                if user_input is None:
                    continue

                # Process special commands
                if not self.process_command(user_input):
                    break

                # Get response from Ollama
                response = self.get_ollama_response(user_input)

                # Speak the response
                self.speak(response)

            except KeyboardInterrupt:
                print("\n\n👋 Interrupted by user")
                self.speak("Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error in main loop: {e}")
                continue


def test_microphone():
    """Test if microphone is working"""
    recognizer = sr.Recognizer()

    print("🎤 Testing microphone...")
    print("Available microphones:")
    for index, name in enumerate(sr.Microphone.list_microphone_names()):
        print(f"  {index}: {name}")

    try:
        with sr.Microphone() as source:
            print("\n✅ Microphone is working!")
            print(f"Default microphone: {source}")
            return True
    except Exception as e:
        print(f"\n❌ Microphone error: {e}")
        return False


def test_ollama_connection(model_name: str = "llama2"):
    """Test if Ollama is running and accessible"""
    print(f"🧠 Testing Ollama connection with model: {model_name}...")

    try:
        response = ollama.chat(
            model=model_name, messages=[{"role": "user", "content": "Say hello"}]
        )
        print("✅ Ollama is working!")
        print(f"Response: {response['message']['content']}")
        return True
    except ollama.ResponseError as e:
        print(f"❌ Ollama error: {e}")
        print("Make sure Ollama is running and the model is installed.")
        print(f"You can install the model with: ollama pull {model_name}")
        return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        print("Make sure Ollama is running (run 'ollama serve' in terminal)")
        return False
