class AnomalyDetector:
    def __init__(self):
        pass

class CUSTOM_Detector(AnomalyDetector):
    """
    Αν η τιμή < threshold => anomaly.
    Επιστρέφει κατευθείαν (score, flag) για κάθε τιμή.
    """
    def __init__(self,start_index, threshold: float = 60.0):
        self.threshold = 80.0

    def handle_one(self, x: float):
        score = x - self.threshold
        flag = 1 if score<0 else 0
        return score, flag
