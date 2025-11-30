# Lafufu Twin - SIGGRAPH Asia

This repository contains the resource code and documentation for the Lafufu Twin research project presented at SIGGRAPH Asia. The project implements an interactive robotic system with speech recognition, natural language processing, text-to-speech synthesis, and motor control, integrated via MQTT communication.

## Overview

The Lafufu Twin system consists of multiple components that work together to create an interactive robotic experience:

- **Speech-to-Text (S2T)**: Captures and transcribes human speech using both online (Google Web Speech API) and offline (Whisper) methods
- **Large Language Model (LLM)**: Processes transcribed speech using a local Ollama instance for natural language understanding and response generation
- **Text-to-Speech (T2S)**: Converts LLM responses into spoken audio with synchronized motor movements
- **MQTT Communication**: Enables real-time data exchange between the Raspberry Pi and external systems (e.g., Unreal Engine)
- **Motor Control**: Manages stepper motors for robot mouth and head movements synchronized with speech

## Repository Structure

```
SIGGRAPH/
├── LafufuTwins/          # Main project directory
│   └── main.py           # Entry point (placeholder)
├── llm-app/              # Local Ollama chat client
│   ├── app.py            # CLI tool for interacting with Ollama
│   ├── requirements.txt  # Python dependencies
│   └── README.md         # Detailed documentation
├── s2t1/                 # Speech-to-Text module
│   ├── app.py            # Online STT (Google Web Speech API)
│   ├── offline_app.py    # Offline STT (Whisper)
│   ├── requirements.txt  # Python dependencies
│   └── README.md         # Detailed documentation
├── t2s1/                 # Text-to-Speech module
│   ├── robot_speech.py   # Main robot speech coordinator
│   ├── tts_service.py    # Google TTS integration
│   ├── audio_player.py   # Audio playback (mpg123)
│   ├── motor_controller.py # Stepper motor control
│   └── stepper_28byj.py  # 28BYJ-48 stepper driver
├── mqtt/                 # MQTT communication module
│   ├── pi_mqtt_app.py    # Raspberry Pi MQTT broker/client
│   └── __init__.py
└── README.md             # This file
```

## Components

### 1. Speech-to-Text (`s2t1/`)

Provides two implementations for converting speech to text:
- **Online**: Uses Google Web Speech API (requires internet connection)
- **Offline**: Uses OpenAI Whisper model running locally (no internet required)

**Key Features:**
- Microphone input with ambient noise calibration
- Continuous listening mode
- Support for multiple Whisper model sizes (tiny, base, small, medium, large)

See [`s2t1/README.md`](s2t1/README.md) for detailed setup and usage instructions.

### 2. Large Language Model (`llm-app/`)

A Python CLI client for interacting with a local [Ollama](https://ollama.com/) service. Enables natural language processing and conversation management.

**Key Features:**
- Connects to local Ollama server
- Supports conversation history via JSON files
- Configurable model selection
- Simple HTTP API integration

See [`llm-app/README.md`](llm-app/README.md) for detailed setup and usage instructions.

### 3. Text-to-Speech (`t2s1/`)

Converts text responses into spoken audio and synchronizes robot motor movements.

**Key Features:**
- Google Text-to-Speech (gTTS) integration
- Stepper motor control for mouth and head movements
- Synchronized audio playback and motor motion
- Hardware abstraction for development (can run in simulation mode)

**Hardware Requirements:**
- Raspberry Pi with GPIO access
- 28BYJ-48 stepper motors with ULN2003 drivers
- `mpg123` for audio playback

### 4. MQTT Communication (`mqtt/`)

Enables real-time bidirectional communication between the Raspberry Pi and external systems (e.g., Unreal Engine).

**Key Features:**
- MQTT broker/client implementation
- State publishing (robot pose, dialogue, audio levels, etc.)
- Command subscription for external control
- JSON-based message format

**Topics:**
- `siggraph/pi/state`: Pi → External systems (state updates)
- `siggraph/pi/commands`: External systems → Pi (commands)

## Prerequisites

### System Requirements
- Python 3.8+ (3.10+ recommended for `llm-app`)
- Raspberry Pi (for hardware components)
- Microphone (for speech input)
- MQTT broker (e.g., Mosquitto) for MQTT communication

### Software Dependencies

**For Speech-to-Text:**
- PortAudio (system-level audio library)
- PyAudio (Python audio library)
- SpeechRecognition
- OpenAI Whisper (for offline mode)

**For LLM App:**
- Ollama server running locally
- Requests library

**For Text-to-Speech:**
- Google Text-to-Speech (gTTS)
- mpg123 (audio player)
- RPi.GPIO (for Raspberry Pi GPIO control)

**For MQTT:**
- paho-mqtt

## Quick Start

### 1. Set Up Speech-to-Text

```bash
cd s2t1
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Online mode
python app.py

# Offline mode
python offline_app.py
```

### 2. Set Up LLM Client

```bash
cd llm-app
pip install -r requirements.txt

# Ensure Ollama is running locally
python app.py --prompt "Hello, how are you?"
```

### 3. Set Up Text-to-Speech (on Raspberry Pi)

```bash
cd t2s1
pip install gtts
sudo apt-get install mpg123  # On Raspberry Pi

# Run in simulation mode (no hardware)
python robot_speech.py
```

### 4. Set Up MQTT Communication

```bash
# Install Mosquitto broker (on Raspberry Pi)
sudo apt-get install mosquitto mosquitto-clients

# Install Python MQTT client
pip install paho-mqtt

# Run the MQTT app
cd mqtt
python3 pi_mqtt_app.py
```

## Integration Workflow

A typical interaction flow:

1. **Speech Input**: User speaks into microphone → `s2t1/` transcribes speech
2. **Language Processing**: Transcribed text → `llm-app/` processes with Ollama → generates response
3. **Speech Output**: Response text → `t2s1/` synthesizes audio and controls motors
4. **State Publishing**: Robot state (pose, dialogue, etc.) → `mqtt/` publishes to external systems

## Development Notes

- The `t2s1/` module can run in simulation mode (`motor_enabled=False`) for development without hardware
- MQTT topics and message formats are defined in `mqtt/pi_mqtt_app.py`
- Each component can be developed and tested independently
- See individual component READMEs for detailed documentation

## License

This repository is part of the Lafufu Twin research project for SIGGRAPH Asia.

## Contributing

This is a research project repository. For questions or contributions, please refer to the project maintainers.

---

For detailed documentation on each component, please refer to the README files in each subdirectory.
