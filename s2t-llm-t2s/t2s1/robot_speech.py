from tts_service import synthesize_to_file
from audio_player import play_audio_blocking
from motor_controller import MotorController


class RobotSpeaker:
    """Coordinates text-to-speech audio playback with robot motor motion."""

    def __init__(self, motor_enabled: bool = False) -> None:
        self.motors = MotorController(enabled=motor_enabled)

    def speak(self, text: str, lang: str = "en", audio_path: str = "speech.mp3") -> None:
        """Generate speech audio from text, play it back, and move motors while playing."""
        mp3_path = synthesize_to_file(text, audio_path, lang=lang)

        try:
            # Optional: perform a head nod before speaking
            # self.motors.nod_head(times=1)

            self.motors.start_talking_motion()
            play_audio_blocking(mp3_path)
        finally:
            self.motors.stop_talking_motion()

    def cleanup(self) -> None:
        self.motors.cleanup()


def main() -> None:
    """Simple CLI for testing robot speech integration."""
    # For development on your laptop: set motor_enabled=False (simulation).
    # On the Raspberry Pi with hardware connected: set motor_enabled=True.
    robot = RobotSpeaker(motor_enabled=False)

    try:
        while True:
            try:
                text = input("Enter text for the robot to speak (or 'quit'): ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if not text or text.lower() == "quit":
                break

            robot.speak(text)
    finally:
        robot.cleanup()


if __name__ == "__main__":
    main()
