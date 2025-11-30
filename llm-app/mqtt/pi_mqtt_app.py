"""Simple MQTT app for Raspberry Pi acting as broker + publisher/subscriber.

Assumptions
-----------
- An MQTT broker (e.g. Mosquitto) is installed and running on the Pi on port 1883.
- This script runs *on the Pi* and connects to the local broker.
- Unreal Engine 5.7 will connect to the Pi's IP as an MQTT client and
  subscribe to the same topics used here.

Install dependencies
--------------------
    pip install paho-mqtt

Run on the Pi
-------------
    python3 pi_mqtt_app.py

Then, in Unreal, configure your MQTT client to connect to:
    host: <PI_IP_ADDRESS>
    port: 1883
    topic (subscribe): siggraph/pi/state
    topic (optional, publish from UE): siggraph/pi/commands
"""

import json
import random
import signal
import sys
import threading
import time
from dataclasses import dataclass, asdict

import paho.mqtt.client as mqtt


BROKER_HOST = "localhost"  # on the Pi this should be fine; UE uses the Pi's IP address
BROKER_PORT = 1883
KEEPALIVE = 60

TOPIC_STATE = "siggraph/pi/state"      # Pi -> Unreal (state data)
TOPIC_COMMANDS = "siggraph/pi/commands"  # Unreal -> Pi (optional commands)

PUBLISH_INTERVAL_SECONDS = 0.1  # 10 Hz example


@dataclass
class PiState:
    """Payload sent from the Pi to Unreal.

    You can treat this as the canonical schema on both sides (Python + UE).

    FIELDS
    ------
    - dialogue: latest utterance or transcript text.
    - app_state: high-level state label (e.g. "Idle", "Listening", "Speaking").
    - arm_*: position/rotation of a tracked arm in Pi/world space.
    - head_*: position/rotation of the head.
    - eyes_open: whether eyes are currently open.
    - audio_level: normalized audio level 0..1.
    - is_speaking: whether audio is considered active speech.
    """

    timestamp: float

    # Conversational context
    dialogue: str
    app_state: str

    # Arm pose
    arm_pos_x: float
    arm_pos_y: float
    arm_pos_z: float
    arm_rot_pitch: float
    arm_rot_yaw: float
    arm_rot_roll: float

    # Head pose
    head_pos_x: float
    head_pos_y: float
    head_pos_z: float
    head_rot_pitch: float
    head_rot_yaw: float
    head_rot_roll: float

    # Eyes & audio
    eyes_open: bool
    audio_level: float
    is_speaking: bool


class PiMqttApp:
    def __init__(self, broker_host: str = BROKER_HOST, broker_port: int = BROKER_PORT) -> None:
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client = mqtt.Client(client_id="pi-mqtt-app", clean_session=True)

        # Attach callbacks
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        self._stop_event = threading.Event()

    # MQTT callbacks -----------------------------------------------------

    def _on_connect(self, client, userdata, flags, rc):  # type: ignore[override]
        if rc == 0:
            print("[MQTT] Connected to broker")
            # Subscribe to commands coming from Unreal
            client.subscribe(TOPIC_COMMANDS, qos=0)
            print(f"[MQTT] Subscribed to commands topic: {TOPIC_COMMANDS}")
        else:
            print(f"[MQTT] Failed to connect, return code {rc}")

    def _on_disconnect(self, client, userdata, rc):  # type: ignore[override]
        print(f"[MQTT] Disconnected from broker (rc={rc})")

    def _on_message(self, client, userdata, msg):  # type: ignore[override]
        payload = msg.payload.decode("utf-8", errors="ignore")
        print(f"[MQTT] Received message on {msg.topic}: {payload}")
        # TODO: Parse and act on commands from Unreal here.

    # Public API ---------------------------------------------------------

    def start(self) -> None:
        """Connect to the broker and start the publish loop in the main thread."""
        print(f"[MQTT] Connecting to {self.broker_host}:{self.broker_port} ...")
        self.client.connect(self.broker_host, self.broker_port, KEEPALIVE)

        # Run the MQTT network loop in a background thread
        self.client.loop_start()

        try:
            while not self._stop_event.is_set():
                self.publish_state()
                time.sleep(PUBLISH_INTERVAL_SECONDS)
        except KeyboardInterrupt:
            print("\n[MQTT] Stopping due to keyboard interrupt...")
        finally:
            self.stop()

    def stop(self) -> None:
        self._stop_event.set()
        try:
            self.client.disconnect()
        finally:
            self.client.loop_stop()
            print("[MQTT] Client stopped")

    # Data generation / publishing --------------------------------------

    def publish_state(self) -> None:
        """Publish one state sample to Unreal.

        Replace the body of this function to pull real data from sensors,
        files, or other parts of your application.
        """
        state = self._generate_example_state()
        payload = json.dumps(asdict(state))
        result = self.client.publish(TOPIC_STATE, payload=payload, qos=0, retain=False)
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            print(f"[MQTT] Failed to publish state: rc={result.rc}")

    def _generate_example_state(self) -> PiState:
        """Generate example data.

        Replace this with real inputs from your dialogue manager, trackers,
        audio analysis, etc.
        """
        now = time.time()

        # Fake some motion over time so you can see values changing in UE.
        t = now % 10.0

        arm_pos_x = t
        arm_pos_y = 0.0
        arm_pos_z = 0.0
        arm_rot_pitch = 0.0
        arm_rot_yaw = (t / 10.0) * 360.0
        arm_rot_roll = 0.0

        head_pos_x = 0.0
        head_pos_y = 0.0
        head_pos_z = 170.0  # e.g. 170 cm height
        head_rot_pitch = 0.0
        head_rot_yaw = (t / 10.0) * 45.0
        head_rot_roll = 0.0

        # Eyes blink every few seconds
        eyes_open = (int(t) % 4) != 0

        # Simulate audio level + speaking state
        is_speaking = (int(now) % 6) < 3
        audio_level = random.uniform(0.5, 1.0) if is_speaking else random.uniform(0.0, 0.2)

        dialogue = "Hello from Pi" if is_speaking else ""
        app_state = "Speaking" if is_speaking else "Idle"

        return PiState(
            timestamp=now,
            dialogue=dialogue,
            app_state=app_state,
            arm_pos_x=arm_pos_x,
            arm_pos_y=arm_pos_y,
            arm_pos_z=arm_pos_z,
            arm_rot_pitch=arm_rot_pitch,
            arm_rot_yaw=arm_rot_yaw,
            arm_rot_roll=arm_rot_roll,
            head_pos_x=head_pos_x,
            head_pos_y=head_pos_y,
            head_pos_z=head_pos_z,
            head_rot_pitch=head_rot_pitch,
            head_rot_yaw=head_rot_yaw,
            head_rot_roll=head_rot_roll,
            eyes_open=eyes_open,
            audio_level=audio_level,
            is_speaking=is_speaking,
        )


def _install_signal_handlers(app: PiMqttApp) -> None:
    def handler(signum, frame):  # type: ignore[override]
        print(f"\n[MQTT] Caught signal {signum}, shutting down...")
        app.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)


if __name__ == "__main__":
    app = PiMqttApp()
    _install_signal_handlers(app)
    app.start()
