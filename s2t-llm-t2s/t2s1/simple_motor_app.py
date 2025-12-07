#!/usr/bin/env python3

from stepper_28byj import Stepper28BYJ
import time

def main():
    # BCM pin numbers: IN1, IN2, IN3, IN4
    pins = [18, 23, 24, 25]

    # step_delay: smaller = faster; adjust if motor skips or stalls
    stepper = Stepper28BYJ(
        pins=pins,
        step_delay=0.003,
        enabled=True,
        name="my_stepper"
    )

    try:
        print("Stepping 200 steps forward...")
        stepper.step(steps=200, direction=1)
        time.sleep(1)

        print("Stepping 200 steps backward...")
        stepper.step(steps=200, direction=-1)
        time.sleep(1)

        print("Continuous rotate forward for 3 seconds...")
        stepper.start_continuous(direction=1)
        time.sleep(3)
        stepper.stop_continuous()

        print("Done.")

    finally:
        # Always clean up GPIO
        print("Cleaning up GPIO...")
        stepper.cleanup()

if __name__ == "__main__":
    main()
