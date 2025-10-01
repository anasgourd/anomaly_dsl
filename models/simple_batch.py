class AnomalyDetector:
    def __init__(self):
        pass

class CUSTOM_Detector(AnomalyDetector):
    def __init__(self,batch_size,start_index,threshold):
        self.threshold = 80.0
        self.trained = True  # δεν έχει warmup

    def handleBatch(self, values):
        vals = [float(v) for v in values]
        scores = [(v - self.threshold) for v in vals]  # απόσταση από threshold
        flags  = [1 if score<0 else 0 for score in scores]
        return scores, flags
