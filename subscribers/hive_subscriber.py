import paho.mqtt.client as mqtt
import json

# HiveMQ Cloud parameters (dummy placeholders for example)
mqtt_host = "your-hivemq-cloud-host.s1.eu.hivemq.cloud"
mqtt_port = 8883
mqtt_topic = "machine/temperature/alerts"

mqtt_username = "your_username"
mqtt_password = "your_password"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected successfully to HiveMQ Cloud")
        client.subscribe(mqtt_topic)
        print(f"Subscribed to topic: {mqtt_topic}")
    else:
        print(f"Connection failed with code {rc}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        print(f" Received on {msg.topic}: {payload}")
    except Exception as e:
        print(f"Error decoding: {e}")

def main():
    client = mqtt.Client()
    client.username_pw_set(mqtt_username, mqtt_password)

    # Enable TLS/SSL
    client.tls_set()
    client.tls_insecure_set(True)

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(mqtt_host, mqtt_port)
    client.loop_forever()

if __name__ == "__main__":
    main()

