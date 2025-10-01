import csv
import time
import json
import paho.mqtt.client as mqtt
import ssl

# MQTT connection details
# Change to your MQTT broker host if needed
mqtt_host="mqtt-dashboard.com"
mqtt_port=8884                    # Default MQTT port
mqtt_topic = "machine/temperature"  # Change if needed

mqtt_username = ""
mqtt_password =""

# CSV file path
csv_file = "data.csv"

# CSV column name with the values to send
attribute = "value" 

def main():
    #client = mqtt.Client()
    client = mqtt.Client(transport="websockets")
        
    #client.username_pw_set(mqtt_username, mqtt_password)
    
    client.tls_set()   
    client.tls_insecure_set(True)
    # boost throughput: επιτρέψε pipeline QoS1
    #client.max_inflight_messages_set(50)    
    #client.max_queued_messages_set(20000)  
    client.connect(mqtt_host, mqtt_port)
    client.loop_start()
    
    print(f"Publishing to topic '{mqtt_topic}' on host '{mqtt_host}'")

    with open(csv_file, "r") as f:
        reader=csv.reader(f)
        for row in reader:
            try:
                value = float(row[0])
                
                payload = json.dumps({"value": value})

                #client.publish(mqtt_topic, payload)
		        
                info = client.publish(mqtt_topic, payload,retain=False)
                #info.wait_for_publish()

                print(f"Sent: {payload}")
                time.sleep(0.01)  # Delay between messages
            except Exception as e:
                print(f"Skipping row due to error: {e}")

    client.loop_stop()
    client.disconnect()

if __name__ == "__main__":
    main()

