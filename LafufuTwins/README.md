# Virtual Assistant with Speech-to-Text and Ollama

A Python-based virtual assistant that uses speech recognition to listen to your voice commands and responds using Ollama's AI models. The assistant can maintain conversation context and speak responses back to you.

## Features

- 🎤 **Speech-to-Text**: Uses Google Speech Recognition to convert your voice to text
- 🧠 **AI-Powered Responses**: Leverages Ollama for intelligent responses using various LLM models
- 🔊 **Text-to-Speech**: Speaks responses back to you using pyttsx3
- 💬 **Conversation History**: Maintains context throughout the conversation
- ⚙️ **Configurable Models**: Choose from any Ollama-supported model
- 🧪 **Built-in Testing**: Test microphone and Ollama connection before running

## Prerequisites

- Python 3.8 or higher
- Ollama installed and running ([Download Ollama](https://ollama.ai))
- A working microphone
- macOS, Linux, or Windows

## Installation

### 1. Install Ollama

If you haven't already, install Ollama:

```bash
# Visit https://ollama.ai to download and install
# Or on macOS:
brew install ollama
```

### 2. Pull an Ollama Model

```bash
# Pull the default model (llama2)
ollama pull llama2

# Or use another model (optional)
ollama pull mistral
ollama pull codellama
```

### 3. Start Ollama Server

```bash
ollama serve
```

Keep this running in a separate terminal window.

### 4. Install Python Dependencies

```bash
pip install -r requirements.txt
```

#### Additional Setup for PyAudio

**macOS:**
```bash
brew install portaudio
pip install pyaudio
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install portaudio19-dev python3-pyaudio
pip install pyaudio
```

**Windows:**
```bash
pip install pipwin
pipwin install pyaudio
```

## Usage

### Basic Usage

Start the virtual assistant with the default model (llama2):

```bash
python main.py
```

### Use a Different Model

```bash
python main.py --model mistral
python main.py --model codellama
```

### Test Your Setup

Test microphone:
```bash
python main.py --test-mic
```

Test Ollama connection:
```bash
python main.py --test-ollama
```

Run all tests:
```bash
python main.py --test-all
```

### Voice Commands

Once running, the assistant will listen for your voice input. Some special commands:

- Say **"exit"**, **"quit"**, or **"goodbye"** to stop the assistant
- Say **"clear history"** or **"reset conversation"** to clear conversation context
- Press **Ctrl+C** to interrupt at any time

## Example Interaction

```
🤖 Virtual Assistant - Powered by Ollama
============================================================

🚀 Starting Virtual Assistant...
Using model: llama2

Commands:
  - Say 'exit', 'quit', or 'goodbye' to stop
  - Say 'clear history' to reset the conversation
  - Press Ctrl+C to interrupt

============================================================
🤖 Assistant: Hello! I'm your virtual assistant. How can I help you today?

🎤 Listening... (speak now)
🔄 Processing speech...
📝 You said: What is the weather like today?
🧠 Thinking with llama2...
🤖 Assistant: I apologize, but I don't have access to real-time weather information...

🎤 Listening... (speak now)
```

## Project Structure

```
LafufuTwins/
├── main.py              # Main application entry point
├── assistant.py         # Virtual assistant core logic
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Configuration

You can customize the assistant by modifying the `VirtualAssistant` class in `assistant.py`:

- **Speech rate**: Change `self.tts_engine.setProperty("rate", 150)`
- **Volume**: Change `self.tts_engine.setProperty("volume", 0.9)`
- **Timeout**: Modify `self.recognizer.listen(source, timeout=5, phrase_time_limit=10)`

## Troubleshooting

### Microphone Not Working

1. Check that your microphone is connected and enabled
2. Run `python main.py --test-mic` to see available microphones
3. Ensure your OS has granted microphone permissions to Terminal/Python

### Ollama Connection Failed

1. Make sure Ollama is running: `ollama serve`
2. Check if the model is installed: `ollama list`
3. Pull the model if needed: `ollama pull llama2`
4. Test connection: `python main.py --test-ollama`

### Speech Recognition Issues

- Speak clearly and at a moderate pace
- Reduce background noise
- Adjust the ambient noise duration in `assistant.py`
- Check your internet connection (Google Speech Recognition requires internet)

### PyAudio Installation Issues

If you encounter issues installing PyAudio:

- **macOS**: Make sure Xcode Command Line Tools are installed: `xcode-select --install`
- **Linux**: Install PortAudio development headers: `sudo apt-get install portaudio19-dev`
- **Windows**: Use pipwin as described in the installation section

## Dependencies

- `speechrecognition`: Speech-to-text conversion
- `pyaudio`: Audio input/output
- `ollama`: Python client for Ollama API
- `pyttsx3`: Text-to-speech conversion

## Privacy Note

This application uses Google's Speech Recognition API for speech-to-text conversion, which sends audio data to Google's servers. All Ollama processing is done locally on your machine.

## License

This project is open source and available for personal and educational use.

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## Future Enhancements

Potential features to add:

- [ ] Support for offline speech recognition (Vosk, Whisper)
- [ ] Wake word detection ("Hey Assistant")
- [ ] Multiple voice profiles
- [ ] Plugin system for custom commands
- [ ] Web interface
- [ ] Docker support
- [ ] Conversation export/import
- [ ] Custom TTS voices

## Support

For issues related to:
- **Ollama**: Visit [Ollama Documentation](https://github.com/ollama/ollama)
- **Speech Recognition**: Check [SpeechRecognition docs](https://github.com/Uberi/speech_recognition)
- **This project**: Open an issue in this repository

---

Built with ❤️ using Python, Ollama, and open-source libraries