import speech_recognition as sr


def main() -> None:
    recognizer = sr.Recognizer()

    # Use the default system microphone as the audio source
    with sr.Microphone() as source:
        print("Calibrating for ambient noise... please stay quiet.")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Calibration complete. Start speaking. Press Ctrl+C to stop.\n")

        while True:
            try:
                print("Listening...")
                audio = recognizer.listen(source)
                print("Recognizing...")

                # Uses Google's free Web Speech API
                text = recognizer.recognize_google(audio)
                print(f"You said: {text}")

            except sr.UnknownValueError:
                print("Sorry, I could not understand the audio.")
            except sr.RequestError as e:
                print(f"Could not request results from the speech service: {e}")
            except KeyboardInterrupt:
                print("\nStopping.")
                break


if __name__ == "__main__":
    main()
