import cv2
import time
import pyttsx3
import threading
import numpy as np
from collections import deque

class SeniorMonitorExpert:
    def __init__(self):
        # 1. Configurações de Voz Personalizada
        self.engine = pyttsx3.init()
        self._configurar_voz(sexo='feminino') # Opções: 'masculino' ou 'feminino'
        
        # 2. Visão Computacional (Haar Cascades)
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye_tree_eyeglasses.xml')
        
        # 3. Lógica de Tempo e Sinais
        self.olhos_fechados_start = None
        self.last_alert_time = 0
        self.buffer_presenca = deque(maxlen=15) # Suavização de sinal
        
        # 4. Processamento de Imagem
        self.clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        self.cap = cv2.VideoCapture(0)

    def _configurar_voz(self, sexo='feminino'):
        """ Procura no sistema por vozes em português """
        voices = self.engine.getProperty('voices')
        self.engine.setProperty('rate', 175) # Velocidade natural
        
        # Tenta encontrar voz em PT-BR pelo nome ou ID
        for voice in voices:
            if "brazil" in voice.name.lower() or "portuguese" in voice.name.lower():
                if sexo == 'feminino' and "maria" in voice.name.lower():
                    self.engine.setProperty('voice', voice.id)
                    break
                if sexo == 'masculino' and "daniel" in voice.name.lower():
                    self.engine.setProperty('voice', voice.id)
                    break
                # Se não achar pelo nome, pega a primeira em PT que encontrar
                self.engine.setProperty('voice', voice.id)

    def falar(self, texto):
        """ Threading para não travar a detecção facial """
        def _speak():
            try:
                # Engine local para estabilidade no Python 3.13
                local_engine = pyttsx3.init()
                local_engine.setProperty('rate', 170)
                # Copia a voz selecionada
                local_engine.setProperty('voice', self.engine.getProperty('voice'))
                local_engine.say(texto)
                local_engine.runAndWait()
            except: pass
        threading.Thread(target=_speak, daemon=True).start()

    def process_image(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Ajuste de Brilho Dinâmico (Modo Noturno)
        brilho = np.mean(gray)
        if brilho < 60:
            gray = self.clahe.apply(gray)
            # Gamma Correction
            gray = np.uint8(np.clip((gray / 255.0)**(1/1.5) * 255.0, 0, 255))
        else:
            gray = self.clahe.apply(gray)

        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5, minSize=(150, 150))
        
        status = "Ativo"
        cor = (0, 255, 0)
        olhos_vistos = False

        for (x, y, w, h) in faces:
            # ROI focada apenas na linha dos olhos (Data Science Optimization)
            roi_gray = gray[y + int(h/5):y + int(h/1.7), x:x+w]
            eyes = self.eye_cascade.detectMultiScale(roi_gray, 1.1, 7, minSize=(35, 35))
            
            olhos_vistos = len(eyes) > 0
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 1)

            # Lógica de Tempo (Micro-sonos e Sono Profundo)
            if not olhos_vistos:
                if self.olhos_fechados_start is None:
                    self.olhos_fechados_start = time.time()
                
                duracao = time.time() - self.olhos_fechados_start
                
                if 0.5 <= duracao < 1.5:
                    status = "ALERTA: Micro-sono!"
                    cor = (0, 165, 255)
                elif duracao >= 1.5:
                    status = "DORMINDO!"
                    cor = (0, 0, 255)
                    if time.time() - self.last_alert_time > 3:
                        self.falar("Douglas! Acorda agora!")
                        self.last_alert_time = time.time()
            else:
                self.olhos_fechados_start = None

        return frame, status, cor

    def run(self):
        print("Monitor iniciado. Pressione ESC para sair.")
        while True:
            ret, frame = self.cap.read()
            if not ret: break
            
            frame = cv2.flip(frame, 1)
            frame, status, cor = self.process_image(frame)
            
            # UI
            cv2.putText(frame, f"STATUS: {status}", (20, 50), 0, 0.8, cor, 2)
            cv2.imshow('Douglas Expert Monitor', frame)
            
            if cv2.waitKey(1) & 0xFF == 27: break

        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    monitor = SeniorMonitorExpert()
    monitor.run()