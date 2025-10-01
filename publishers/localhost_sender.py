import csv, time, json
import paho.mqtt.client as mqtt

mqtt_host = "localhost"
mqtt_port = 1883
mqtt_topic = "machine/temperature"
csv_file = "data.csv"

def main():
    client = mqtt.Client()
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

