# s2t-llm-t2s

End-to-end voice assistant that chains:

1. Speech-to-text (microphone input)
2. Local LLM (Ollama via `llm-app` client)
3. Text-to-speech robot output (`t2s1`)

## Layout

- `s2t1/`  – original speech-to-text demo (speech_recognition)
- `llm-app/` – original Ollama chat client
- `t2s1/`  – original text-to-speech robot controller
- `main.py` – new orchestrator that wires all three together

## Requirements

You need:

- Python 3
- `speech_recognition`
- a working microphone
- a running Ollama server (default `http://localhost:11434`) with a model available
- gTTS and audio playback tools as required by `t2s1` (see its README)

Example Python deps (inside a virtualenv):

```bash
pip install speechrecognition requests gtts
```

## Running

From this directory:

```bash
python main.py
```

Then follow the prompt:

- Press Enter to record audio
- Speak into the microphone
- The recognized text is sent to the LLM
- The assistant reply is printed and spoken via the robot TTS system
