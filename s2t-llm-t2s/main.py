"""End-to-end voice assistant:

1. Listen on the microphone
2. Transcribe speech to text (STT)
3. Send text to local Ollama LLM
4. Speak the LLM reply using the robot TTS/motor system
"""

from __future__ import annotations

import sys
from pathlib import Path

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


from robot_speech import RobotSpeaker  # type: ignore  # from t2s1/robot_speech.py


class LlamaServerClient:
    """Minimal client for local llama.cpp llama-server completion API."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8080",
        timeout: float = 60.0,
    ) -> None:
        # llama-server runs as a systemd service listening on this port.
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def chat(self, prompt: str, history=None):
        """Yield text chunks from llama-server /completion endpoint.

        Currently returns a single chunk (non-streaming response)
        to match the generator interface used in main()."""
        import requests  # local import to avoid circular issues

        payload = {
            "prompt": prompt,
            "n_predict": 256,
        }
        url = f"{self.base_url}/completion"
        resp = requests.post(url, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        content = data.get("content")
        if not isinstance(content, str):
            raise RuntimeError(f"Unexpected response from llama-server: {data}")
        # Yield a single chunk for compatibility with the streaming loop in main().
        yield content


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

            try:
                for chunk in client.chat(prompt=text, history=None):
                    print(chunk, end="", flush=True)
                    reply_chunks.append(chunk)
            except requests.exceptions.ReadTimeout:
                print("\nTimed out waiting for LLM reply; it may still be loading or is too slow. Please try again or use a smaller model.")
                continue
            except requests.exceptions.RequestException as e:
                print(f"\nHTTP error while talking to LLM: {e}")
                continue

            print()  # newline after streamed text
            reply = "".join(reply_chunks)

            # Speak full reply once streaming is finished
            print("Speaking reply...")
            robot.speak(reply)

    finally:
        robot.cleanup()


if __name__ == "__main__":
    main()
