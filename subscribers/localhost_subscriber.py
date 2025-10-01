import paho.mqtt.client as mqtt
import json

mqtt_host = "localhost"
mqtt_port = 1883
mqtt_topic = "machine/temperature/alerts"

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        print(f"Received: {payload}")
    except Exception as e:
        print(f"Error: {e}")

def main():
    client = mqtt.Client()
    client.on_message = on_message
    client.connect(mqtt_host, mqtt_port)
    client.subscribe(mqtt_topic, qos=0)
    print(f"Subscribed to {mqtt_topic} on {mqtt_host}:{mqtt_port}")
    client.loop_forever()

if __name__ == "__main__":
    main()

