from typing import Optional

try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None

from stepper_28byj import Stepper28BYJ


class MotorController:
    """High-level controller for robot steppers.

    - mouth_stepper moves continuously while the robot is "talking".
    - head_stepper can perform nodding gestures.
    """

    def __init__(self, enabled: bool = True) -> None:
        # Mouth: your chosen pins for ULN2003 IN1..IN4
        self.mouth_stepper = Stepper28BYJ(
            pins=[17, 27, 22, 23],  # IN1..IN4 -> GPIO17,27,22,23
            step_delay=0.003,
            enabled=enabled,
            name="mouth",
        )

        # Example second stepper; adjust pins to your wiring when you add it.
        # If you don't have a second motor yet, you can ignore head_stepper usages.
        self.head_stepper: Optional[Stepper28BYJ] = Stepper28BYJ(
            pins=[5, 6, 13, 19],   # example BCM pins; change to match your wiring
            step_delay=0.004,
            enabled=enabled,
            name="head",
        )

    def start_talking_motion(self) -> None:
        """Start mouth motion to accompany speech."""
        self.mouth_stepper.start_continuous(direction=1)

    def stop_talking_motion(self) -> None:
        """Stop mouth motion."""
        self.mouth_stepper.stop_continuous()

    def nod_head(self, times: int = 2) -> None:
        """Simple nodding pattern: a few short back-and-forth motions."""
        if self.head_stepper is None:
            return

        for _ in range(times):
            self.head_stepper.step(steps=150, direction=1)
            self.head_stepper.step(steps=150, direction=-1)

    def cleanup(self) -> None:
        """Release GPIO resources."""
        self.mouth_stepper.cleanup()
        if self.head_stepper is not None:
            self.head_stepper.cleanup()

        if GPIO is not None:
            try:
                GPIO.cleanup()
            except RuntimeError:
                # If GPIO already cleaned up or not initialized, ignore.
                pass
