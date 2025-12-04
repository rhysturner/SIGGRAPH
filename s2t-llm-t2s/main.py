"""End-to-end voice assistant:

1. Listen on the microphone
2. Transcribe speech to text (STT)
3. Send text to local Ollama LLM
4. Speak the LLM reply using the robot TTS/motor system
"""

from __future__ import annotations

import sys
from pathlib import Path

import speech_recognition as sr


# --- Wire up local subprojects on sys.path ---
BASE_DIR = Path(__file__).resolve().parent

S2T_DIR = BASE_DIR / "s2t1"
LLM_DIR = BASE_DIR / "llm-app"
T2S_DIR = BASE_DIR / "t2s1"

for p in (S2T_DIR, LLM_DIR, T2S_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


from app import OllamaClient  # type: ignore  # from llm-app/app.py
from robot_speech import RobotSpeaker  # type: ignore  # from t2s1/robot_speech.py


def listen_once(recognizer: sr.Recognizer) -> str | None:
    """Capture a single utterance from the default microphone and return text.

    Returns None if recognition fails.
    """

    with sr.Microphone() as source:
        print("Calibrating for ambient noise... please stay quiet.")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Calibration complete. Start speaking.\n")

        print("Listening...")
        audio = recognizer.listen(source)
        print("Recognizing...")

    try:
        text = recognizer.recognize_google(audio)
        print(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        print("Sorry, I could not understand the audio.")
        return None
    except sr.RequestError as e:  # network / API error
        print(f"Could not request results from the speech service: {e}")
        return None


def main() -> None:
    recognizer = sr.Recognizer()

    # Motors disabled by default for desktop development; set True on Pi.
    robot = RobotSpeaker(motor_enabled=False)
    client = OllamaClient()  # uses default base_url/model from llm-app

    try:
        while True:
            try:
                inp = input("Press Enter to speak, or type 'quit' to exit: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting.")
                break

            if inp.lower() == "quit":
                break

            text = listen_once(recognizer)
            if not text:
                continue

            # Send to LLM and stream the reply to the console
            print("Sending to LLM (streaming)...")
            reply_chunks: list[str] = []

            for chunk in client.chat(prompt=text, history=None):
                print(chunk, end="", flush=True)
                reply_chunks.append(chunk)

            print()  # newline after streamed text
            reply = "".join(reply_chunks)

            # Speak full reply once streaming is finished
            print("Speaking reply...")
            robot.speak(reply)

    finally:
        robot.cleanup()


if __name__ == "__main__":
    main()
