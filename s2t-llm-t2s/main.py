"""End-to-end voice assistant:

1. Listen on the microphone
2. Transcribe speech to text (STT)
3. Send text to local Ollama LLM
4. Speak the LLM reply using the robot TTS/motor system
"""

from __future__ import annotations

import sys
import json
import re
from pathlib import Path
from typing import List

import requests
import speech_recognition as sr


# --- Wire up local subprojects on sys.path ---
BASE_DIR = Path(__file__).resolve().parent

S2T_DIR = BASE_DIR / "s2t1"
LLM_DIR = BASE_DIR / "llm-app"
T2S_DIR = BASE_DIR / "t2s1"

for p in (S2T_DIR, LLM_DIR, T2S_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


from app import OllamaClient, Message  # type: ignore  # from llm-app/app.py
from robot_speech import RobotSpeaker  # type: ignore  # from t2s1/robot_speech.py


def load_system_prompt(base_dir: Path) -> List[Message] | None:
    """Load a system prompt from `system_prompt.json` if present.

    Expected format:
        {"content": "You are a helpful assistant..."}
    or:
        {"role": "system", "content": "..."}
    """
    path = base_dir / "system_prompt.json"
    if not path.exists():
        return None

    try:
        with path.open("r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception as exc:  # noqa: BLE001
        print(f"Warning: could not load system_prompt.json: {exc}")
        return None

    if isinstance(raw, dict):
        content = raw.get("content")
        if not isinstance(content, str):
            print("Warning: system_prompt.json missing string 'content' field")
            return None
        role = raw.get("role") or "system"
        return [Message(role=role, content=content)]

    print("Warning: system_prompt.json must be a JSON object")
    return None


def strip_think_blocks(text: str) -> str:
    """Remove <think>...</think> or <thinking>...</thinking> sections from the model output."""
    # Handle both <think> and <thinking> tags just in case
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    text = re.sub(r"<thinking>.*?</thinking>", "", text, flags=re.DOTALL)
    return text.strip()


def listen_once(recognizer: sr.Recognizer) -> str | None:
    """Capture a single utterance from the default microphone and return text.

    Returns None if recognition fails.
    """

    with sr.Microphone() as source:
        print("Calibrating for ambient noise... please stay quiet.")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Calibration complete. Start speaking. You can talk for a while and pause briefly.\\n")

        # Be more tolerant of pauses so you don't get cut off too quickly
        recognizer.pause_threshold = 1.8  # seconds of silence before considering phrase complete
        recognizer.non_speaking_duration = 0.8

        print("Listening (up to ~20 seconds)...")
        audio = recognizer.listen(source, timeout=None, phrase_time_limit=20)
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
    robot = RobotSpeaker(motor_enabled=True)
    client = LlamaServerClient()  # uses local llama-server (GPU-accelerated) on port 8080

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

            for chunk in client.chat_stream(prompt=text, history=system_messages):
                reply_chunks.append(chunk)

            full_reply = "".join(reply_chunks)

            # Remove <think>/<thinking> sections for both display and speech
            cleaned_reply = strip_think_blocks(full_reply)

            print(cleaned_reply)
            print("Speaking reply...")
            robot.speak(cleaned_reply)

    finally:
        robot.cleanup()


if __name__ == "__main__":
    main()
