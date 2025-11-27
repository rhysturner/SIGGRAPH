# Microphone Speech-to-Text (Online & Offline)

This project contains two simple Python command-line apps that listen to your microphone and convert speech to text:

- `app.py` &mdash; **online** speech-to-text using Google Web Speech API (via `SpeechRecognition`).
- `offline_app.py` &mdash; **offline** speech-to-text using the **Whisper** model running locally.

Both apps:
- Use your system microphone as input.
- Calibrate for ambient noise.
- Continuously listen until you press `Ctrl+C`.

---

## 1. Prerequisites

- Python 3.8+ installed and available as `python` or `python3`.
- Internet connection (for:
  - Installing Python packages
  - Running the **online** `app.py` which calls Google Web Speech API.)
- A working microphone recognized by your OS.

### 1.1 Audio dependencies (PortAudio / PyAudio)

The apps use the `pyaudio` library, which depends on PortAudio.

**On macOS (Homebrew):**

```bash
brew install portaudio
```

If you use another OS, install PortAudio via your package manager, then install `pyaudio` via `pip`.

---

## 2. Setup

It is recommended to use a virtual environment so dependencies are isolated from your system Python.

From the project directory:

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
```

Then install dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This will install:
- `SpeechRecognition` &mdash; microphone handling + access to several STT backends.
- `pyaudio` &mdash; audio input from your microphone.
- `openai-whisper` &mdash; local Whisper speech-to-text model.

---

## 3. Online Speech-to-Text (`app.py`)

`app.py` uses Google’s free Web Speech API via the `SpeechRecognition` library. Audio is sent to Google’s servers for transcription.

### 3.1 Run the online app

From the project directory (with the virtual environment activated):

```bash
python app.py
```

### 3.2 What you should see

1. A message about **calibrating for ambient noise** (stay quiet for a second).
2. A loop of:
   - `Listening...`
   - `Recognizing...`
   - Then either:
     - `You said: <recognized text>`
     - or an error message like `Sorry, I could not understand the audio.`
3. Press `Ctrl+C` to stop the app.

### 3.3 Notes

- Requires an internet connection while running.
- Uses Google’s default free Web Speech API (no additional setup in this script).

---

## 4. Offline Speech-to-Text (`offline_app.py`)

`offline_app.py` uses the **Whisper** model running locally. Audio never leaves your machine during transcription.

### 4.1 First run (model download)

The first time you run the offline app, Whisper will download the selected model weights (by default: `small`). This may take some time depending on your connection.

### 4.2 Run the offline app

From the project directory (with the virtual environment activated):

```bash
python offline_app.py
```

### 4.3 What you should see

1. `Loading Whisper model (this may take a moment the first time)...`
2. Microphone calibration output.
3. Loop of:
   - `Listening...`
   - `Transcribing locally with Whisper...`
   - Then either:
     - `You said (offline): <recognized text>`
     - or `No speech detected.`
4. Press `Ctrl+C` to stop the app.

### 4.4 Changing the Whisper model size

In `offline_app.py` you’ll find this line:

```python
model = whisper.load_model("small")
```

You can change `"small"` to another model name:

- `"tiny"` &mdash; fastest, smallest, least accurate
- `"base"` &mdash; small and fairly fast
- `"small"` &mdash; default here (good balance for many cases)
- `"medium"` &mdash; more accurate, slower
- `"large"` &mdash; most accurate, largest and slowest

Larger models will:
- Use more RAM and disk space.
- Run slower, especially on CPU-only machines.

---

## 5. How It Works (High-Level)

### 5.1 Online (`app.py`)

1. `speech_recognition.Recognizer` handles microphone input and noise adjustment.
2. `speech_recognition.Microphone` opens the default system microphone.
3. `recognizer.listen(source)` records a chunk of audio.
4. `recognizer.recognize_google(audio)` sends the audio to Google and returns recognized text.

### 5.2 Offline (`offline_app.py`)

1. `speech_recognition` captures a short audio segment from the microphone.
2. The audio buffer is written to a temporary WAV file.
3. Whisper (`whisper.load_model(...).transcribe(...)`) loads the WAV file and returns a transcription.
4. The transcription text is printed, and the temporary file is deleted.

---

## 6. Common Issues & Troubleshooting

### 6.1 `pyaudio` installation errors

If you see errors installing `pyaudio`:

- Make sure PortAudio is installed (e.g. on macOS with Homebrew: `brew install portaudio`).
- Then try:

```bash
pip install --no-cache-dir pyaudio
```

or reinstall all requirements:

```bash
pip install --no-cache-dir -r requirements.txt
```

### 6.2 Microphone not detected / permission issues

- Ensure your OS microphone settings allow your terminal / Python to access the microphone.
- Check that another application is not exclusively holding the microphone.
- On some systems, the OS may prompt you the first time; accept microphone access for the terminal.

### 6.3 Poor recognition quality

- Speak clearly and close to the microphone.
- Avoid very noisy environments.
- For Whisper, consider using a larger model (e.g. `"medium"` or `"large"`) if your hardware allows it.
- Increase the duration of ambient noise calibration in the source code if necessary (e.g. use `duration=2` instead of `1`).

### 6.4 Whisper is very slow

- Use a smaller model (e.g. `"tiny"` or `"base"`).
- Close other heavy applications.
- Whisper can use GPU acceleration if you have a compatible GPU and the correct PyTorch install; otherwise it will run on CPU.

---

## 7. Project Files Overview

- `app.py` &mdash; Online speech-to-text using Google Web Speech API.
- `offline_app.py` &mdash; Offline speech-to-text using Whisper.
- `requirements.txt` &mdash; Python dependencies for both apps.
- `README.md` &mdash; This documentation.

---

## 8. Running Summary

**Online mode:**

```bash
source .venv/bin/activate       # or Windows equivalent
python app.py
```

**Offline mode (Whisper):**

```bash
source .venv/bin/activate       # or Windows equivalent
python offline_app.py
```

Press `Ctrl+C` at any time to stop either app.# SIGGRAPH
