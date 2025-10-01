import csv, time, json
import paho.mqtt.client as mqtt

# HiveMQ Cloud parameters
mqtt_host = "your-mqtt-host.s1.eu.hivemq.cloud"
mqtt_port = 8883
mqtt_topic = "machine/temperature"
csv_file = "data.csv"

mqtt_username = "your_username"
mqtt_password = "your_password"


def main():
    client = mqtt.Client()
    client.username_pw_set(mqtt_username, mqtt_password)

    # Enable TLS/SSL
    client.tls_set()
    client.tls_insecure_set(True)

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

