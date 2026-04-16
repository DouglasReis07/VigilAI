import pyttsx3
import threading
import time

class AlertManager:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 160)
        self.last_alert_time = 0

    def _speak(self, text):
        # Roda em uma thread separada para não travar a webcam
        self.engine.say(text)
        self.engine.runAndWait()

    def trigger(self, text, interval=5):
        current_time = time.time()
        if current_time - self.last_alert_time > interval:
            threading.Thread(target=self._speak, args=(text,), daemon=True).start()
            self.last_alert_time = current_time