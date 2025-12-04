# T2S1 - Text-to-Speech Robot Controller

A Python-based text-to-speech (TTS) system integrated with stepper motor control for creating an animated robot speaker. This project enables a robot to "talk" by synchronizing speech audio playback with mouth motor movements.

## Features

- **Text-to-Speech Synthesis**: Convert text to natural-sounding speech using Google Text-to-Speech (gTTS)
- **Motor Control**: Coordinate stepper motor movements with speech playback
- **28BYJ-48 Stepper Support**: Optimized driver for 28BYJ-48 stepper motors with ULN2003 driver boards
- **Dual Motor Support**: Control both mouth and head motors independently
- **Simulation Mode**: Develop and test without Raspberry Pi hardware
- **Blocking Audio Playback**: Synchronized audio playback using mpg123

## Hardware Requirements

- Raspberry Pi (any model with GPIO pins)
- 28BYJ-48 stepper motor(s) with ULN2003 driver board(s)
- Audio output (speakers or headphones connected to Pi)
- Power supply for stepper motors (typically 5V)

## Software Requirements

```bash
# System dependencies (Raspberry Pi)
sudo apt-get update
sudo apt-get install mpg123

# Python dependencies
pip install gtts RPi.GPIO
```

## Project Structure

```
t2s1/
├── robot_speech.py       # Main orchestrator class
├── tts_service.py        # Text-to-speech synthesis
├── audio_player.py       # Audio playback control
├── motor_controller.py   # High-level motor coordination
└── stepper_28byj.py      # Low-level stepper driver
```

## Module Descriptions

### `robot_speech.py`
Main entry point that coordinates TTS generation, audio playback, and motor control. The `RobotSpeaker` class provides a simple interface for making the robot speak.

### `tts_service.py`
Handles text-to-speech conversion using gTTS. Supports saving to file or generating in-memory bytes.

**Key functions:**
- `synthesize_to_file()`: Generate MP3 file from text
- `synthesize_to_bytes()`: Generate in-memory MP3 bytes

### `audio_player.py`
Manages audio playback using mpg123 with blocking behavior to ensure synchronization.

### `motor_controller.py`
High-level abstraction for controlling multiple stepper motors. Manages mouth movements during speech and head nodding gestures.

**Default GPIO pins:**
- Mouth motor: GPIO 17, 27, 22, 23 (IN1-IN4)
- Head motor: GPIO 5, 6, 13, 19 (IN1-IN4)

### `stepper_28byj.py`
Low-level driver for 28BYJ-48 stepper motors using half-step sequence. Supports both discrete stepping and continuous motion in a background thread.

## Usage

### Basic Usage

```python
from robot_speech import RobotSpeaker

# Create robot speaker (simulation mode for development)
robot = RobotSpeaker(motor_enabled=False)

# Make the robot speak
robot.speak("Hello, I am a talking robot!")

# Cleanup when done
robot.cleanup()
```

### On Raspberry Pi with Hardware

```python
from robot_speech import RobotSpeaker

# Enable motors for actual hardware control
robot = RobotSpeaker(motor_enabled=True)

try:
    robot.speak("Hello, world!")
finally:
    robot.cleanup()
```

### Interactive CLI Mode

Run the main script directly for interactive testing:

```bash
python robot_speech.py
```

This starts an interactive prompt where you can type text for the robot to speak.

### Advanced Motor Control

```python
from motor_controller import MotorController

motors = MotorController(enabled=True)

# Start talking motion
motors.start_talking_motion()
# ... play audio ...
motors.stop_talking_motion()

# Perform head nod gesture
motors.nod_head(times=3)

motors.cleanup()
```

### Custom Stepper Control

```python
from stepper_28byj import Stepper28BYJ

# Initialize stepper on custom pins
stepper = Stepper28BYJ(
    pins=[17, 27, 22, 23],  # BCM pin numbers
    step_delay=0.003,       # Speed control
    enabled=True,
    name="my_motor"
)

# Discrete stepping
stepper.step(steps=200, direction=1)  # Move 200 steps forward

# Continuous motion
stepper.start_continuous(direction=1)
# ... do other things ...
stepper.stop_continuous()

stepper.cleanup()
```

## Configuration

### GPIO Pin Configuration

Edit `motor_controller.py` to change GPIO pin assignments:

```python
self.mouth_stepper = Stepper28BYJ(
    pins=[17, 27, 22, 23],  # Your IN1-IN4 pins
    step_delay=0.003,
    enabled=enabled,
    name="mouth",
)
```

### Motor Speed

Adjust `step_delay` parameter (lower = faster):
- Default mouth: 0.003 seconds
- Default head: 0.004 seconds

### Language Support

The TTS service supports multiple languages via gTTS:

```python
robot.speak("Bonjour!", lang="fr")  # French
robot.speak("Hola!", lang="es")     # Spanish
robot.speak("こんにちは", lang="ja")  # Japanese
```

## Development Mode

For development on non-Raspberry Pi systems, set `motor_enabled=False`:

```python
robot = RobotSpeaker(motor_enabled=False)
```

This enables testing without GPIO hardware, with simulated motor control logging to console.

## Technical Details

### 28BYJ-48 Stepper Motor

- **Type**: 5V unipolar stepper motor
- **Step angle**: 5.625° (with 1/64 reduction)
- **Steps per revolution**: 4096 (half-step mode)
- **Drive sequence**: 8-step half-step sequence for smooth motion

### Threading Model

The stepper driver uses background threads for continuous motion, allowing non-blocking motor control during audio playback.

## Troubleshooting

### Audio Issues

- Ensure mpg123 is installed: `sudo apt-get install mpg123`
- Check audio output: `aplay -l` to list audio devices
- Verify volume settings: `alsamixer`

### Motor Not Moving

- Check GPIO pin connections match code configuration
- Verify 5V power supply to ULN2003 board
- Test in simulation mode first (`motor_enabled=False`)
- Check for GPIO permission issues: add user to `gpio` group

### ImportError: No module named 'RPi.GPIO'

- Install RPi.GPIO: `pip install RPi.GPIO`
- Or run in simulation mode for development

## License

[Add your license information here]

## Contributors

[Add contributor information here]

## Related Projects

- [gTTS](https://github.com/pndurette/gTTS) - Google Text-to-Speech Python library
- [RPi.GPIO](https://pypi.org/project/RPi.GPIO/) - Raspberry Pi GPIO interface

## Future Enhancements

- [ ] Add emotion-based motor patterns (excited, sad, etc.)
- [ ] Support for other stepper motor types
- [ ] Real-time lip-sync animation
- [ ] Multiple language voice selection
- [ ] Servo motor support for additional movements
- [ ] Integration with speech recognition for conversation mode
