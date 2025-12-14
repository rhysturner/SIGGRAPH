import os
import time
import json
import paho.mqtt.client as mqtt

BROKER_HOST = os.environ.get("MQTT_HOST", "localhost")
BROKER_PORT = int(os.environ.get("MQTT_PORT", "1883"))
TOPIC = os.environ.get("MQTT_TOPIC", "llm/text")


def get_llm_text() -> str:
    """Replace this with your actual LLM output."""
    return "Hello from the LLM at " + time.strftime("%H:%M:%S")


def main():
    client = mqtt.Client()
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)

    while True:
        text = get_llm_text()
        payload = {"text": text, "ts": time.time()}
        client.publish(TOPIC, json.dumps(payload), qos=0, retain=False)
        print("published:", payload)
        time.sleep(1)


if __name__ == "__main__":
    main()
