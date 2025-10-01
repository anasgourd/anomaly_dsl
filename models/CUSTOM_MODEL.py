from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.layers import Dropout
import numpy as np
import tensorflow as tf
import random

seed = 42
random.seed(seed)
np.random.seed(seed)
tf.random.set_seed(seed)



class AnomalyDetector:
    def __init__(self):
        pass

def create_dataset(data, time_step=28):
    X, y = [], []
    for i in range(len(data) - time_step):
        X.append(data[i:i + time_step])
        y.append(data[i + time_step])
    return np.array(X), np.array(y)

def profile_stream(data, time_step=288,threshold_percentile=0.99):
    scaler = StandardScaler()
    data_scaled = scaler.fit_transform(data.reshape(-1, 1))

    X, y = create_dataset(data_scaled, time_step)

    X = X.reshape((X.shape[0], X.shape[1], 1))


    model = Sequential([
        LSTM(150, return_sequences=True, input_shape=(time_step, 1)),
        Dropout(0.2),
        LSTM(75, return_sequences=False),
        Dense(1)
    ])
    model.compile(optimizer='adam', loss='mean_squared_error')



    model.fit(X, y, epochs=5, verbose=1, shuffle=False)

    normal_predictions = model.predict(X)
    normal_prediction_error = np.abs(normal_predictions.flatten() - y.flatten())
    p = float(threshold_percentile*100)

    threshold = np.percentile(normal_prediction_error, p)


    buffer = data_scaled[-time_step:]

    return model, scaler, threshold, buffer

class CUSTOM_Detector(AnomalyDetector):
    def __init__(self, batch_size=288, start_index=1152, threshold=0.99):
        super().__init__()
        self.batch_size = batch_size
        self.start_index = start_index  # how many points to train on
        self.threshold = threshold # overrideable or computed during training
        self.model = None
        self.scaler = None
        self.buffer = []
        self.time_step = 10
        self._hist = []
    def handleBatch(self, batch):
        values = []
        for val in batch:
            values.append(val)
        if len(values) == 0:
            return [],[]
        if self.model is None:
            self._hist.extend(values)
            if len(self._hist) <= self.start_index:
                return [0.0]*len(values), [0]*len(values)

            train_data = np.array(self._hist[-self.start_index:], dtype=np.float32)
            self.model, self.scaler, self.threshold, self.buffer = profile_stream(train_data, time_step=self.time_step, threshold_percentile=self.threshold)

            return [0.0]*len(values), [0]*len(values)
        

        data_scaled = self.scaler.transform(np.array(batch).reshape(-1, 1))

        if len(self.buffer) > 0:
            self.buffer = np.array(self.buffer).reshape(-1, 1)
            combined_scaled = np.concatenate([self.buffer, data_scaled], axis=0)
        else:
            combined_scaled = data_scaled

        # guard: not enough samples to form a window
        if combined_scaled.shape[0] <= self.time_step:
            self.buffer = combined_scaled[-self.time_step:].reshape(-1, 1)
            return [0.0]*len(values), [0]*len(values)
        

        X_batch, y_batch = create_dataset(combined_scaled, self.time_step)
        if len(X_batch) == 0:
            return [0.0] * len(batch), [0] * len(batch)
        X_batch = X_batch.reshape((X_batch.shape[0], self.time_step, 1))

        predictions = self.model.predict(X_batch, verbose=0)
        prediction_error=np.abs(predictions - y_batch)
        #prediction_error=np.abs(predictions.ravel() - y_batch.ravel())
        anomaly_scores = prediction_error.flatten().tolist()

        is_anomaly = [int(score > self.threshold) for score in anomaly_scores]
        self.buffer = combined_scaled[-self.time_step:].reshape(-1, 1)

        return anomaly_scores, is_anomaly
