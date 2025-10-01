import csv, time, json
import paho.mqtt.client as mqtt

# Flespi broker parameters
mqtt_host = "mqtt.flespi.io"
mqtt_port = 1883
mqtt_topic = "machine/temperature"
csv_file = "data.csv"

# Authentication with API token (dummy value for example purposes)
mqtt_token = "YOUR_API_TOKEN_HERE"

def main():
    # Use token as username, password left empty
    client = mqtt.Client()
    client.username_pw_set(mqtt_token, password="")
    client.connect(mqtt_host, mqtt_port)
    client.loop_start()
    print(f"Publishing to {mqtt_topic} on {mqtt_host}:{mqtt_port}")

    with open(csv_file, "r") as f:
        reader = csv.reader(f)
        for row in reader:
            try:
                value = float(row[0])
                payload = json.dumps({"value": value})
                client.publish(mqtt_topic, payload, retain=False)
                print(f"Sent: {payload}")
                time.sleep(0.01)
            except Exception as e:
                print(f"Skipping row: {e}")

    client.loop_stop()
    client.disconnect()

if __name__ == "__main__":
    main()

