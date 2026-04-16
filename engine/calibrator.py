import time

class Calibrator:
    def __init__(self, duration=5):
        self.duration = duration
        self.start_time = None
        self.ear_readings = []
        self.is_calibrated = False
        self.final_threshold = 0.20 # Default

    def update(self, current_ear):
        if self.start_time is None:
            self.start_time = time.time()
            print("Calibrando... Olhe para a câmera e pisque normalmente.")

        elapsed = time.time() - self.start_time
        if elapsed < self.duration:
            self.ear_readings.append(current_ear)
            return f"Calibrando: {int((elapsed/self.duration)*100)}%"
        else:
            if not self.is_calibrated:
                # Define threshold como 75% da média de abertura
                self.final_threshold = (sum(self.ear_readings) / len(self.ear_readings)) * 0.75
                self.is_calibrated = True
                print(f"Calibração concluída! Threshold definido em: {self.final_threshold:.2f}")
            return "Calibrado"