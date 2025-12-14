# MQTT demo: LLM text -> Webpage

This demo publishes text to MQTT topic `llm/text` and renders it in a browser via MQTT-over-WebSockets.

## 1) Broker (Mosquitto)

Install (Debian):

    sudo apt-get update
    sudo apt-get install -y mosquitto mosquitto-clients

Run broker with WebSockets enabled:

    mosquitto -c mqtt_demo/mosquitto.conf -v

Ports:
- MQTT TCP: 1883
- WebSockets: 9001

## 2) Publisher (Python)

Install:

    python3 -m pip install paho-mqtt

Run:

    python3 mqtt_demo/publisher.py

Optional env vars:
- MQTT_HOST (default: localhost)
- MQTT_PORT (default: 1883)
- MQTT_TOPIC (default: llm/text)

## 3) Web subscriber

Serve the page:

    python3 -m http.server 8080 --directory mqtt_demo/web

Open:

    http://localhost:8080/

If your broker is not on the same machine as the browser, edit `mqtt_demo/web/index.html` and change:

    ws://localhost:9001  ->  ws://<broker-ip>:9001
