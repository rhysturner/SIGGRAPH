import json
import sys
import types
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

# Ensure the project root is on sys.path so `mqtt` can be imported
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# If paho-mqtt is not installed in the environment running tests, provide a
# minimal stub so that `mqtt.pi_mqtt_app` can be imported without error.
if "paho.mqtt.client" not in sys.modules:
    paho_pkg = types.ModuleType("paho")
    mqtt_pkg = types.ModuleType("paho.mqtt")
    client_mod = types.ModuleType("paho.mqtt.client")

    class _StubClient:
        pass

    client_mod.Client = _StubClient
    client_mod.MQTT_ERR_SUCCESS = 0

    sys.modules["paho"] = paho_pkg
    sys.modules["paho.mqtt"] = mqtt_pkg
    sys.modules["paho.mqtt.client"] = client_mod

from mqtt.pi_mqtt_app import (
    BROKER_HOST,
    BROKER_PORT,
    KEEPALIVE,
    TOPIC_COMMANDS,
    TOPIC_STATE,
    PiMqttApp,
    PiState,
)


@pytest.fixture
@patch("mqtt.pi_mqtt_app.mqtt.Client")
def app_with_mock_client(mock_client_cls):
    """Create a PiMqttApp instance whose underlying mqtt.Client is mocked."""
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client

    app = PiMqttApp(broker_host=BROKER_HOST, broker_port=BROKER_PORT)
    return app, mock_client


def test_start_connects_to_mqtt_broker_and_runs_loop_once(app_with_mock_client):
    """PiMqttApp connects to the broker and starts the loop.

    The publish loop would normally run forever, so we stop it after one
    iteration by setting the internal stop event from a patched publish_state.
    """

    app, mock_client = app_with_mock_client

    # Make publish_state stop the loop after a single call so start() returns.
    def _stop_after_one():
        app._stop_event.set()

    with patch.object(app, "publish_state", side_effect=_stop_after_one) as publish_mock:
        app.start()

    # connect should be called with the configured host/port and KEEPALIVE.
    mock_client.connect.assert_called_once_with(BROKER_HOST, BROKER_PORT, KEEPALIVE)
    # MQTT network loop should be started and then stopped via stop().
    mock_client.loop_start.assert_called_once()
    mock_client.disconnect.assert_called_once()
    mock_client.loop_stop.assert_called_once()
    # We should have attempted to publish at least once.
    publish_mock.assert_called_once()


def test_on_connect_subscribes_to_command_topic(app_with_mock_client):
    """PiMqttApp subscribes to the correct command topic on successful connect."""
    app, mock_client = app_with_mock_client

    # rc == 0 indicates a successful connection
    app._on_connect(mock_client, userdata=None, flags={}, rc=0)

    mock_client.subscribe.assert_called_once_with(TOPIC_COMMANDS, qos=0)


def test_on_message_processes_incoming_command_message(app_with_mock_client, capsys):
    """PiMqttApp processes incoming MQTT messages on the command topic.

    Currently this means decoding the payload and printing a log line.
    """
    app, _ = app_with_mock_client

    class Msg:
        topic = TOPIC_COMMANDS
        payload = b'{"cmd": "test"}'

    msg = Msg()

    app._on_message(client=None, userdata=None, msg=msg)
    captured = capsys.readouterr()

    assert TOPIC_COMMANDS in captured.out
    assert '{"cmd": "test"}' in captured.out


def test_publish_state_sends_pistate_json_to_state_topic(app_with_mock_client):
    """PiMqttApp publishes PiState data to the correct topic in JSON format."""
    app, mock_client = app_with_mock_client

    # Provide deterministic PiState so we can assert on the JSON payload.
    state = PiState(
        timestamp=123.456,
        dialogue="hello",
        app_state="Idle",
        arm_pos_x=1.0,
        arm_pos_y=2.0,
        arm_pos_z=3.0,
        arm_rot_pitch=4.0,
        arm_rot_yaw=5.0,
        arm_rot_roll=6.0,
        head_pos_x=7.0,
        head_pos_y=8.0,
        head_pos_z=9.0,
        head_rot_pitch=10.0,
        head_rot_yaw=11.0,
        head_rot_roll=12.0,
        eyes_open=True,
        audio_level=0.5,
        is_speaking=False,
    )

    with patch.object(app, "_generate_example_state", return_value=state):
        # Simulate a successful publish result from paho-mqtt.
        mock_client.publish.return_value = SimpleNamespace(rc=0)

        app.publish_state()

    mock_client.publish.assert_called_once()
    args, kwargs = mock_client.publish.call_args

    # First positional argument is the topic.
    assert args[0] == TOPIC_STATE

    # Payload should be valid JSON representing the PiState fields.
    payload = kwargs["payload"]
    data = json.loads(payload)

    assert data["timestamp"] == pytest.approx(123.456)
    assert data["dialogue"] == "hello"
    assert data["app_state"] == "Idle"
    assert data["arm_pos_x"] == 1.0
    assert data["head_rot_yaw"] == 11.0
    assert data["eyes_open"] is True
    assert data["is_speaking"] is False

    # QoS and retain flags must match the implementation.
    assert kwargs["qos"] == 0
    assert kwargs["retain"] is False


def test_stop_gracefully_disconnects_from_broker(app_with_mock_client):
    """PiMqttApp.stop() sets the stop event and disconnects from the broker."""
    app, mock_client = app_with_mock_client

    # Stop the app and ensure MQTT client methods are called.
    app.stop()

    assert app._stop_event.is_set()
    mock_client.disconnect.assert_called_once()
    mock_client.loop_stop.assert_called_once()
