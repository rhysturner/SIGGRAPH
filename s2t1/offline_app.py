import os
import tempfile

import speech_recognition as sr
import whisper


def _audio_to_temp_wav(audio: sr.AudioData) -> str:
    """Save SpeechRecognition AudioData to a temporary WAV file and return its path."""
    wav_bytes = audio.get_wav_data()
    fd, path = tempfile.mkstemp(suffix=".wav")
    with os.fdopen(fd, "wb") as f:
        f.write(wav_bytes)
    return path


def main() -> None:
    # Load Whisper model (change to "base", "medium", "large" if you want)
    print("Loading Whisper model (this may take a moment the first time)...")
    model = whisper.load_model("small")

    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("Calibrating for ambient noise... please stay quiet.")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Calibration complete. Start speaking. Press Ctrl+C to stop.\n")

        while True:
            try:
                print("Listening...")
                audio = recognizer.listen(source)
                print("Transcribing locally with Whisper...")

                temp_wav = _audio_to_temp_wav(audio)
                try:
                    result = model.transcribe(temp_wav, language="en")
                    text = result.get("text", "").strip()
                    if text:
                        print(f"You said (offline): {text}")
                    else:
                        print("No speech detected.")
                finally:
                    if os.path.exists(temp_wav):
                        os.remove(temp_wav)

            except KeyboardInterrupt:
                print("\nStopping.")
                break
            except Exception as e:
                print(f"Error during transcription: {e}")


if __name__ == "__main__":
    main()
