import paho.mqtt.client as mqtt
import json

# Flespi broker parameters (dummy placeholders)
mqtt_host = "mqtt.flespi.io"
mqtt_port = 1883
mqtt_topic = "machine/temperature/alerts"

# Authentication with API token
mqtt_token = "YOUR_FLESPI_API_TOKEN"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to Flespi broker successfully")
        client.subscribe(mqtt_topic)
        print(f"Subscribed to topic: {mqtt_topic}")
    else:
        print(f"Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        print(f"Received message on {msg.topic}: {payload}")
    except Exception as e:
        print(f"Error decoding message: {e}")

def main():
    client = mqtt.Client()
    client.username_pw_set(mqtt_token, password="")  # token auth
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(mqtt_host, mqtt_port, 60)
    client.loop_forever()

if __name__ == "__main__":
    main()

