import threading
import time
from typing import List, Optional

try:
    # gpiozero will, in turn, use a pin factory such as RPi.GPIO, lgpio, or pigpio
    from gpiozero import DigitalOutputDevice
except ImportError:  # pragma: no cover - dependency issue
    DigitalOutputDevice = None  # type: ignore


class Stepper28BYJ:
    """Control a 28BYJ-48 stepper motor using a ULN2003 driver board.

    This implementation uses the gpiozero library. It creates four
    ``DigitalOutputDevice`` instances (one per IN1..IN4 input on the
    ULN2003 board) and drives them with a half-step sequence.

    Pins are specified as BCM GPIO numbers in IN1..IN4 order.
    """

    # Half-step sequence for 28BYJ-48 (8 micro-steps per full step pattern)
    _HALF_STEP_SEQUENCE: List[List[int]] = [
        [1, 0, 0, 0],
        [1, 1, 0, 0],
        [0, 1, 0, 0],
        [0, 1, 1, 0],
        [0, 0, 1, 0],
        [0, 0, 1, 1],
        [0, 0, 0, 1],
        [1, 0, 0, 1],
    ]

    def __init__(
        self,
        pins: List[int],
        step_delay: float = 0.002,
        enabled: bool = True,
        name: str = "stepper",
    ) -> None:
        if len(pins) != 4:
            raise ValueError("pins must be a list of 4 BCM GPIO pins in IN1..IN4 order")

        self.pins = pins
        self.step_delay = step_delay
        self.enabled = enabled
        self.name = name

        self._lock = threading.Lock()
        self._continuous = False
        self._thread: Optional[threading.Thread] = None

        # gpiozero DigitalOutputDevice instances, one per pin
        self._devices: List[DigitalOutputDevice] = []

        if not self.enabled:
            print(f"[{self.name}] (sim) initialized on pins {self.pins}")
            return

        if DigitalOutputDevice is None:
            raise RuntimeError(
                "gpiozero is not available. Install it and run on a Raspberry Pi "
                "or set enabled=False for simulation."
            )

        # Initialize each output device low
        for pin in self.pins:
            dev = DigitalOutputDevice(pin=pin, active_high=True, initial_value=False)
            self._devices.append(dev)

        print(f"[{self.name}] initialized on pins {self.pins} (gpiozero)")

    # ------------------------------------------------------------------
    # Low-level helpers
    # ------------------------------------------------------------------
    def _write_index(self, index: int, value: int) -> None:
        if not self.enabled or not self._devices:
            return
        dev = self._devices[index]
        if value:
            dev.on()
        else:
            dev.off()

    def _set_step(self, bits: List[int]) -> None:
        if not self.enabled:
            # Simulation: just log if desired
            # print(f"[{self.name}] (sim) step bits={bits}")
            return
        for i, value in enumerate(bits):
            self._write_index(i, value)

    def _off(self) -> None:
        # Turn off all coils
        if not self.enabled:
            return
        for dev in self._devices:
            dev.off()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def step(self, steps: int, direction: int = 1) -> None:
        """Move a given number of half-steps.

        Positive `steps` use the provided `direction`; negative `steps` invert it.
        """

        if steps == 0:
            return

        if not self.enabled:
            print(f"[{self.name}] (sim) step {steps} dir={direction}")
            # Still sleep to simulate timing so callers behave similarly
            time.sleep(abs(steps) * self.step_delay)
            return

        actual_dir = 1 if direction >= 0 else -1
        if steps < 0:
            steps = -steps
            actual_dir *= -1

        sequence = self._HALF_STEP_SEQUENCE
        seq_len = len(sequence)

        for i in range(steps):
            idx = (i * actual_dir) % seq_len
            self._set_step(sequence[idx])
            time.sleep(self.step_delay)

        self._off()

    @staticmethod
    def degrees_to_steps(degrees: float, steps_per_rev: int = 4096) -> int:
        """Convert an output-shaft angle (degrees) to half-steps.

        For a 28BYJ-48 in half-step mode, a common value is ~4096 half-steps per
        output-shaft revolution (gearbox included).
        """
        return int(round(abs(degrees) * steps_per_rev / 360.0))

    def _oscillate_loop(self, swing_steps: int, start_direction: int) -> None:
        sequence = self._HALF_STEP_SEQUENCE
        seq_len = len(sequence)
        direction = 1 if start_direction >= 0 else -1
        idx = 0 if direction > 0 else seq_len - 1
        steps_taken = 0

        try:
            while True:
                with self._lock:
                    if not self._continuous:
                        break

                if self.enabled:
                    self._set_step(sequence[idx])

                time.sleep(self.step_delay)

                idx = (idx + direction) % seq_len
                steps_taken += 1

                if steps_taken >= swing_steps:
                    steps_taken = 0
                    direction = -direction
        finally:
            self._off()

    def start_oscillating(
        self,
        swing_degrees: float = 30.0,
        steps_per_rev: int = 4096,
        start_direction: int = 1,
    ) -> None:
        """Start alternating motion: +swing_degrees then -swing_degrees, repeating."""
        swing_steps = self.degrees_to_steps(swing_degrees, steps_per_rev=steps_per_rev)
        if swing_steps <= 0:
            return

        with self._lock:
            if self._continuous:
                return
            self._continuous = True

        if not self.enabled:
            print(
                f"[{self.name}] (sim) start_oscillating degrees={swing_degrees} steps={swing_steps} dir={start_direction}"
            )

        self._thread = threading.Thread(
            target=self._oscillate_loop,
            args=(swing_steps, 1 if start_direction >= 0 else -1),
            daemon=True,
        )
        self._thread.start()

    def _continuous_loop(self, direction: int) -> None:
        if not self.enabled:
            # Simulation: spin with sleeps only
            while True:
                with self._lock:
                    if not self._continuous:
                        break
                time.sleep(self.step_delay)
            return

        sequence = self._HALF_STEP_SEQUENCE
        seq_len = len(sequence)

        i = 0
        try:
            while True:
                with self._lock:
                    if not self._continuous:
                        break

                idx = (i * direction) % seq_len
                self._set_step(sequence[idx])
                time.sleep(self.step_delay)
                i += 1
        finally:
            self._off()

    def start_continuous(self, direction: int = 1) -> None:
        with self._lock:
            if self._continuous:
                return
            self._continuous = True

        if not self.enabled:
            print(f"[{self.name}] (sim) start_continuous dir={direction}")
            # No thread needed; but to keep API consistent, we still start one

        self._thread = threading.Thread(
            target=self._continuous_loop,
            args=(1 if direction >= 0 else -1,),
            daemon=True,
        )
        self._thread.start()

    def stop_continuous(self) -> None:
        with self._lock:
            if not self._continuous:
                return
            self._continuous = False

        if not self.enabled:
            print(f"[{self.name}] (sim) stop_continuous")

        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

    def cleanup(self) -> None:
        """Stop motion and release GPIO resources."""

        self.stop_continuous()
        self._off()

        # Close gpiozero devices
        for dev in self._devices:
            try:
                dev.close()
            except Exception:
                pass
        self._devices.clear()
