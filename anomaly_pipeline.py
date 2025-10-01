import time
import paho.mqtt.client as mqtt
from river import anomaly, compose, preprocessing, time_series, linear_model, optim,feature_extraction
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score,accuracy_score
import numpy as np
import pandas as pd
import json


# MQTT and model parameters from DSL
mqtt_host = "localhost"
mqtt_port = 1883
mqtt_topic = "machine/temperature"
attribute = "value"


    
mqtt_username = ""
mqtt_password = ""
    


mqtt_ssl = False

mqtt_webPath = ""
mqtt_webPort = 0

threshold = 0.8
start_index = 1000

evaluation = {
    "name": "Eval",
    "labels_file": "labels.csv",
    "anomalies_file": "alerts.csv",
    "scores_file": "results.csv",
    "metrics": ['F1Score', 'Precision', 'Recall', 'Accuracy', 'ROCAUC']
}



import redis

redis_client = redis.Redis(
    host="localhost",
    port=6379,
    db=0
)
redis_scores_key = "anomaly_scores"
redis_alerts_key = "anomaly_alerts"



output_path = "results.csv"
def write_score(value, score):
    with open(output_path, "a") as f:
        flat_scores = np.array(score).flatten()
        for s in flat_scores:
            f.write(f"{s}\n")

       




alerts_path = "alerts.csv"
def write_anomalies(value, is_anomaly):
    with open(alerts_path, "a") as f:
        flat_alerts=np.array(is_anomaly).flatten()
        for s in flat_alerts:
            f.write(f"{int(s)}\n")
        



start_index = int(start_index)


preproc_instance = preprocessing.StandardScaler()




anomaly_model = anomaly.StandardAbsoluteDeviation()
quantile_filter = anomaly.QuantileFilter(anomaly_model, q=0.8)





cnt = 0
training_buffer = []


def handle_standard_model(x_val):
    global cnt
    cnt += 1

    # Learn preprocessor incrementally
    if preproc_instance:
        preproc_instance.learn_one({'x': x_val})
        x_val_scaled = preproc_instance.transform_one({'x': x_val})['x']
    else:
        x_val_scaled = x_val

    # During training phase
    if cnt <= start_index:
        anomaly_model.learn_one(None,x_val_scaled)
        score = anomaly_model.score_one(None,x_val_scaled)
        quantile_filter.learn_one(None,score)
        return 0.0, 0  # No detection yet

    # After training: detection
    score = anomaly_model.score_one(None,x_val_scaled)
    is_anomaly = quantile_filter.classify(score)
    #anomaly_model.learn_one(None,x_val_scaled)

    return score, is_anomaly

def handle_custom_model(batch_values):
    return anomaly_model.handleBatch(batch_values)

def handle_svm_hs(x_val):
    global cnt
    cnt += 1
    # Wrap input for consistency with River format
    x_dict = {'x': x_val}

    # Preprocessing
    if preproc_instance:
        preproc_instance.learn_one(x_dict)
        x_val_scaled = preproc_instance.transform_one(x_dict)['x']
    else:
        x_val_scaled = x_val
    x_dict = {'x': x_val_scaled}

    # Training phase
    if cnt <= start_index:
        anomaly_model.learn_one(x_dict)
        return 0.0, 0  # Still warming up

    # Detection phase
    score = anomaly_model.score_one(x_dict)
    is_anomaly = anomaly_model.classify(score)
    return score, is_anomaly   
    
def handle_arima_model(x_val):
    global cnt
    cnt += 1

    if preproc_instance:
        preproc_instance.learn_one({'x': x_val})
        x_val = preproc_instance.transform_one({'x': x_val})['x']
    else:
        x_val = x_val

    if cnt <= start_index:
        anomaly_model.learn_one(None,x_val)
        return 0.0, 0   # score=0, no alert

    score = anomaly_model.score_one(None,x_val)
    
    if score is None or np.isnan(score) or np.isinf(score):
        return 0.0, 0
    score = np.clip(score, -1e6, 1e6)

    is_anomaly = anomaly_model.classify(score)
    
    return score, is_anomaly

def load_values(path):
    df = pd.read_csv(path, header=None)
    return df.iloc[:, 0]

def on_message(client, userdata, message):
    try:
        payload = json.loads(message.payload.decode())
        x_val = float(payload.get(attribute))

        
        # ---- RIVER path ----
        
        score, is_anomaly = handle_standard_model(x_val)
        

        write_score(x_val, score)
        write_anomalies(x_val, is_anomaly)
        
        redis_client.rpush(redis_scores_key, json.dumps({"value": x_val, "score": score}))
        if is_anomaly:
            redis_client.rpush(redis_alerts_key, json.dumps({"value": x_val, "score": score}))
        
        print(f"Received value: {x_val}, Score: {score}")
        if is_anomaly:
            print(f"ALERT: Anomaly detected for value: {x_val}, Score: {score}")

        
    except Exception as e:
        print(f"Error handling message: {e}")

if __name__ == "__main__":
    use_websockets =True if mqtt_webPath !="" else False

    if use_websockets:
        client = mqtt.Client(transport="websockets")
    else:
        client = mqtt.Client()

    client.on_message = on_message

    use_tls = mqtt_ssl

    if use_tls:
        client.tls_set()
        client.tls_insecure_set(True)


    if mqtt_username or mqtt_password:
        client.username_pw_set(mqtt_username, mqtt_password or None)

    try:
        client.connect("localhost", 1883)
        client.subscribe("machine/temperature")
        print(f"Subscribed to topic 'machine/temperature'")
        client.loop_forever()

    except KeyboardInterrupt:

        print("Streaming stopped by user.")
        print(" Do you want to continue with the evaluation so far? (y/n)")
        user_input = input().strip().lower()
        

        if user_input == "y":
            if evaluation is None:
                print("Evaluation cannot be performed — no Evaluation block was provided in the DSL.")
                exit(0)
              	
            print("Continuing with evaluation...")
            eval = evaluation

            y_true_full = load_values(eval["labels_file"])
            y_pred = load_values(eval["anomalies_file"])
            if len(y_true_full) != len(y_pred):
                print(f"[Warning] Labels and predictions have different lengths "
                      f"({len(y_true_full)} vs {len(y_pred)}). Truncating to shortest.")

            min_len = min(len(y_true_full), len(y_pred))
            y_true = y_true_full[:min_len]
            y_pred = y_pred[:min_len]
            for metric in eval["metrics"]:
                if metric == "F1Score":
                    print("F1Score:", f1_score(y_true, y_pred))
                elif metric == "Precision":
                    print("Precision:", precision_score(y_true, y_pred))
                elif metric == "Recall":
                    print("Recall:", recall_score(y_true, y_pred))
                elif metric == "Accuracy":
                    print("Accuracy:", accuracy_score(y_true, y_pred))
                elif metric == "ROCAUC":
                    y_scores = load_values(eval["scores_file"])
                    min_len = min(len(y_true_full), len(y_scores))
                    y_true_roc = y_true_full[:min_len]
                    y_scores = y_scores[:min_len]

                    if len(set(y_true_roc)) < 2:
                        print("ROCAUC: Cannot compute ROC AUC — only one class present in y_true.")
                    else:
                        print("ROCAUC:", roc_auc_score(y_true_roc, y_scores))

        else:
            print("Exiting without evaluation.")
            exit(0)
