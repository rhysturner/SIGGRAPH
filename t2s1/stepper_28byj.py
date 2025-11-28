import time
import threading
from typing import List, Optional

try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None  # Allows import on non-Pi systems


class Stepper28BYJ:
    """Controller for a 28BYJ-48 stepper motor driven by ULN2003 on Raspberry Pi.

    - Uses BCM pin numbering.
    - Pins must be given in IN1..IN4 order.
    """

    # Half-step sequence for 28BYJ-48 + ULN2003
    _HALF_STEP_SEQUENCE: List[List[int]] = [
        [1, 0, 0, 0],  # step 0
        [1, 1, 0, 0],  # step 1
        [0, 1, 0, 0],  # step 2
        [0, 1, 1, 0],  # step 3
        [0, 0, 1, 0],  # step 4
        [0, 0, 1, 1],  # step 5
        [0, 0, 0, 1],  # step 6
        [1, 0, 0, 1],  # step 7
    ]

    def __init__(
        self,
        pins: List[int],
        step_delay: float = 0.002,
        enabled: bool = True,
        name: str = "stepper",
    ) -> None:
        """Initialize the stepper driver.

        :param pins:       List of 4 BCM GPIO pins [IN1, IN2, IN3, IN4].
        :param step_delay: Delay between half-steps (seconds). Larger = slower.
        :param enabled:    False => simulation only, no GPIO calls.
        :param name:       Identifier used in logs (useful with multiple motors).
        """
        if len(pins) != 4:
            raise ValueError("pins must be a list of 4 BCM GPIO pins in IN1..IN4 order")

        self.pins = pins
        self.step_delay = step_delay
        self.enabled = enabled
        self.name = name

        self._continuous = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        if self.enabled:
            if GPIO is None:
                raise RuntimeError(
                    "RPi.GPIO is not available. Install it and run on a Raspberry Pi "
                    "or set enabled=False for simulation."
                )

            GPIO.setmode(GPIO.BCM)
            for pin in self.pins:
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.LOW)
        else:
            print(f"[{self.name}] (sim) initialized on pins {self.pins}")

    # --- Low-level helpers -------------------------------------------------

    def _set_step(self, bits: List[int]) -> None:
        if not self.enabled:
            # Simulation: no GPIO calls
            return

        for pin, value in zip(self.pins, bits):
            GPIO.output(pin, GPIO.HIGH if value else GPIO.LOW)

    def _off(self) -> None:
        if not self.enabled:
            return
        for pin in self.pins:
            GPIO.output(pin, GPIO.LOW)

    # --- Basic stepping ----------------------------------------------------

    def step(self, steps: int, direction: int = 1) -> None:
        """Move the motor by a fixed number of half-steps.

        :param steps:     Number of half-steps to move (can be negative).
        :param direction: +1 for forward, -1 for reverse. If steps < 0, direction is inverted.
        """
        if steps == 0:
            return

        if steps < 0:
            steps = -steps
            direction = -direction

        seq = self._HALF_STEP_SEQUENCE
        idx = 0 if direction > 0 else len(seq) - 1

        for _ in range(steps):
            self._set_step(seq[idx])
            time.sleep(self.step_delay)
            idx = (idx + direction) % len(seq)

        self._off()

    # --- Continuous motion (background thread) -----------------------------

    def _continuous_loop(self, direction: int) -> None:
        seq = self._HALF_STEP_SEQUENCE
        idx = 0 if direction > 0 else len(seq) - 1

        try:
            while True:
                with self._lock:
                    if not self._continuous:
                        break

                self._set_step(seq[idx])
                time.sleep(self.step_delay)
                idx = (idx + direction) % len(seq)
        finally:
            self._off()

    def start_continuous(self, direction: int = 1) -> None:
        """Start continuous stepping in a background thread.

        :param direction: +1 forward, -1 reverse
        """
        with self._lock:
            if self._continuous:
                return
            self._continuous = True

        if not self.enabled:
            print(f"[{self.name}] (sim) start_continuous dir={direction}")
            return

        self._thread = threading.Thread(
            target=self._continuous_loop,
            args=(direction,),
            daemon=True,
        )
        self._thread.start()

    def stop_continuous(self) -> None:
        """Stop continuous motion if running."""
        with self._lock:
            if not self._continuous:
                return
            self._continuous = False

        if not self.enabled:
            print(f"[{self.name}] (sim) stop_continuous")
            return

        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

        self._off()

    # --- Cleanup -----------------------------------------------------------

    def cleanup(self) -> None:
        """Turn off coils.

        Does NOT call GPIO.cleanup() so multiple steppers can coexist.
        Call GPIO.cleanup() once in your top-level on exit.
        """
        self.stop_continuous()
        self._off()
