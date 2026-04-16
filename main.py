import cv2
import time
import pyttsx3
import threading
import numpy as np
from collections import deque
import math
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from datetime import datetime
import os
import json

class EyeAspectRatio:
    """Detecção de olhos usando método simplificado"""
    def __init__(self):
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        self.eye_close_counter = 0
        self.EAR_THRESHOLD = 0.2
        self.EAR_CONSEC_FRAMES = 2
        self.total_blinks = 0
        
    def detect_eyes(self, frame, face_roi):
        """Detecta olhos na região do rosto"""
        if face_roi is None or face_roi.size == 0:
            return None, None, 1.0
        
        eyes = self.eye_cascade.detectMultiScale(face_roi, 1.1, 5, minSize=(30, 30))
        
        # Simula EAR baseado na detecção de olhos
        if len(eyes) < 2:
            # Olhos fechados ou não detectados
            self.eye_close_counter += 1
            ear = 0.1
        else:
            if self.eye_close_counter >= self.EAR_CONSEC_FRAMES:
                self.total_blinks += 1
            self.eye_close_counter = 0
            ear = 0.3
        
        return eyes, eyes, ear

class VideoRecorder:
    """Gravação de eventos e playback"""
    def __init__(self, save_dir="recordings"):
        self.is_recording = False
        self.out = None
        self.event_buffer = deque(maxlen=300)
        self.save_dir = save_dir
        self.current_event_type = None
        
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
    
    def start_recording(self, event_type, frame):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.save_dir}/event_{event_type}_{timestamp}.avi"
        
        self.out = cv2.VideoWriter(filename, cv2.VideoWriter_fourcc(*'XVID'), 20.0, 
                                   (frame.shape[1], frame.shape[0]))
        
        for buffered_frame in self.event_buffer:
            self.out.write(buffered_frame)
        
        self.is_recording = True
        self.current_event_type = event_type
        print(f"🎥 Gravação iniciada: {event_type}")
        return filename
    
    def record_frame(self, frame):
        if self.is_recording and self.out:
            self.out.write(frame)
    
    def stop_recording(self):
        if self.out:
            self.out.release()
            self.is_recording = False
            print(f"🎥 Gravação finalizada")
    
    def add_to_buffer(self, frame):
        self.event_buffer.append(frame.copy())

class PostureAnalyzer:
    """Análise de postura simplificada"""
    def __init__(self):
        self.posture_history = deque(maxlen=100)
        self.bad_posture_counter = 0
        
    def analyze_posture(self, frame, face_position):
        """Analisa postura baseado na posição do rosto"""
        h, w = frame.shape[:2]
        posture_status = "Postura normal"
        bad_posture = False
        
        if face_position:
            x, y, w_face, h_face = face_position
            
            # Verifica se rosto está muito próximo (pode indicar inclinação)
            if h_face > h * 0.6:
                posture_status = "Muito próximo - Corrija postura"
                bad_posture = True
            # Verifica se rosto está muito alto ou baixo
            elif y < h * 0.2:
                posture_status = "Inclinado para baixo"
                bad_posture = True
            elif y + h_face > h * 0.8:
                posture_status = "Inclinado para cima"
                bad_posture = True
        
        self.posture_history.append(1 if bad_posture else 0)
        return posture_status, bad_posture

class FallPredictor:
    """Previsão de queda simplificada"""
    def __init__(self):
        self.feature_history = deque(maxlen=50)
        
    def extract_features(self, movement_speed, posture_data, eye_state):
        features = {
            'movement_speed': movement_speed,
            'posture_instability': np.std(posture_data) if posture_data else 0,
            'eye_state': eye_state,
            'time_of_day': datetime.now().hour
        }
        return features
    
    def predict_fall_risk(self, features):
        """Prediz risco de queda baseado em regras simples"""
        risk_score = 0
        
        # Regras simples para calcular risco
        if features['movement_speed'] > 100:
            risk_score += 0.4
        if features['posture_instability'] > 0.5:
            risk_score += 0.3
        if features['eye_state'] < 0.2:  # Olhos fechados
            risk_score += 0.2
        if 0 <= features['time_of_day'] <= 6:  # Madrugada
            risk_score += 0.1
        
        risk_score = min(risk_score, 1.0)
        
        if risk_score > 0.7:
            return "🔴 ALTO RISCO DE QUEDA", risk_score
        elif risk_score > 0.4:
            return "🟡 RISCO MODERADO", risk_score
        return "🟢 RISCO BAIXO", risk_score

class ReportGenerator:
    """Geração de relatórios periódicos"""
    def __init__(self, report_dir="reports"):
        self.report_dir = report_dir
        self.daily_stats = {
            'date': datetime.now().date(),
            'micro_sleeps': 0,
            'deep_sleeps': 0,
            'fall_alerts': 0,
            'bad_posture_count': 0,
            'active_hours': []
        }
        
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)
    
    def update_stats(self, event_type, value=None):
        if event_type == 'micro_sleep':
            self.daily_stats['micro_sleeps'] += 1
        elif event_type == 'deep_sleep':
            self.daily_stats['deep_sleeps'] += 1
        elif event_type == 'fall':
            self.daily_stats['fall_alerts'] += 1
        elif event_type == 'bad_posture':
            self.daily_stats['bad_posture_count'] += 1
    
    def generate_daily_report(self):
        """Gera relatório em TXT (simplificado)"""
        filename = f"{self.report_dir}/relatorio_{self.daily_stats['date']}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("="*50 + "\n")
            f.write("RELATÓRIO DIÁRIO - MONITOR SENIOR\n")
            f.write("="*50 + "\n\n")
            f.write(f"Data: {self.daily_stats['date']}\n\n")
            f.write("ESTATÍSTICAS:\n")
            f.write(f"- Micro-sonos: {self.daily_stats['micro_sleeps']}\n")
            f.write(f"- Sono profundo: {self.daily_stats['deep_sleeps']}\n")
            f.write(f"- Alertas de queda: {self.daily_stats['fall_alerts']}\n")
            f.write(f"- Más posturas: {self.daily_stats['bad_posture_count']}\n\n")
            
            # Recomendações
            f.write("RECOMENDAÇÕES:\n")
            if self.daily_stats['fall_alerts'] > 0:
                f.write("- Alto número de quedas - Consulte um médico\n")
            if self.daily_stats['bad_posture_count'] > 50:
                f.write("- Muitas más posturas - Exercícios de alongamento\n")
            if self.daily_stats['micro_sleeps'] > 10:
                f.write("- Muitos micro-sonos - Verificar qualidade do sono\n")
        
        print(f"📄 Relatório gerado: {filename}")
        return filename

class PowerSaver:
    """Modo economia de energia"""
    def __init__(self):
        self.last_movement_time = time.time()
        self.idle_threshold = 300
        self.current_quality = 'high'
        self.power_saving_active = False
        
        self.quality_settings = {
            'high': {'width': 640, 'height': 480, 'fps': 30, 'scale': 1.0},
            'medium': {'width': 480, 'height': 360, 'fps': 20, 'scale': 0.75},
            'low': {'width': 320, 'height': 240, 'fps': 15, 'scale': 0.5}
        }
    
    def check_idle(self, movement_detected):
        if movement_detected:
            self.last_movement_time = time.time()
            return
        
        idle_time = time.time() - self.last_movement_time
        
        if idle_time > self.idle_threshold and self.current_quality != 'low':
            self.reduce_quality()
        elif movement_detected and self.current_quality != 'high':
            self.increase_quality()
    
    def reduce_quality(self):
        if self.current_quality == 'high':
            self.current_quality = 'medium'
            self.power_saving_active = True
            print("🔋 Modo economia ativado")
        elif self.current_quality == 'medium':
            self.current_quality = 'low'
            print("🔋 Modo ultra economia")
    
    def increase_quality(self):
        if self.current_quality == 'low':
            self.current_quality = 'medium'
            print("⚡ Retornando qualidade média")
        elif self.current_quality == 'medium':
            self.current_quality = 'high'
            self.power_saving_active = False
            print("⚡ Modo normal restaurado")
    
    def get_quality_settings(self):
        return self.quality_settings[self.current_quality]

class SeniorMonitorExpert:
    def __init__(self):
        # Inicializa módulos
        self.eye_detector = EyeAspectRatio()
        self.video_recorder = VideoRecorder()
        self.posture_analyzer = PostureAnalyzer()
        self.fall_predictor = FallPredictor()
        self.report_generator = ReportGenerator()
        self.power_saver = PowerSaver()
        
        # Configurações de Voz
        self.engine = None
        self._init_engine()
        
        # Face cascade
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Configuração da Câmera
        self.cap = None
        self._init_camera()
        
        # Lógica de Tempo
        self.olhos_fechados_start = None
        self.last_alert_time = 0
        self.last_fall_alert_time = 0
        self.last_posture_alert = 0
        self.last_report_time = time.time()
        
        # Estatísticas
        self.movement_history = deque(maxlen=30)
        self.prev_face_center = None
        
        # Interface
        self.root = None
        self.video_label = None
        self.status_label = None
        self.running = True
        
        print("✅ Sistema inicializado!")
    
    def _init_engine(self):
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 175)
        except Exception as e:
            print(f"Erro na voz: {e}")
            self.engine = None
    
    def _init_camera(self):
        camera_indices = [0, 1, 2]
        for index in camera_indices:
            cap = cv2.VideoCapture(index)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    self.cap = cap
                    print(f"✅ Câmera {index} inicializada!")
                    return
                cap.release()
        print("⚠️ Modo simulação ativado")
        self.cap = None
    
    def falar(self, texto):
        if self.engine:
            def speak():
                self.engine.say(texto)
                self.engine.runAndWait()
            threading.Thread(target=speak, daemon=True).start()
    
    def process_frame(self, frame):
        """Processa frame com todas as análises"""
        quality = self.power_saver.get_quality_settings()
        if quality['scale'] != 1.0:
            frame = cv2.resize(frame, (quality['width'], quality['height']))
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5, minSize=(100, 100))
        
        status = "Ativo"
        cor = (0, 255, 0)
        face_roi = None
        face_pos = None
        
        for (x, y, w, h) in faces:
            face_pos = (x, y, w, h)
            face_roi = gray[y:y+h, x:x+w]
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            
            # Detecta olhos
            eyes, _, ear = self.eye_detector.detect_eyes(frame, face_roi)
            
            # Desenha olhos
            for (ex, ey, ew, eh) in eyes:
                cv2.rectangle(frame, (x+ex, y+ey), (x+ex+ew, y+ey+eh), (0, 255, 0), 1)
            
            # Verifica sono
            if ear < 0.2:
                if self.olhos_fechados_start is None:
                    self.olhos_fechados_start = time.time()
                    self.video_recorder.add_to_buffer(frame)
                
                duracao = time.time() - self.olhos_fechados_start
                
                if 0.5 <= duracao < 1.5:
                    status = "⚠️ Micro-sono!"
                    cor = (0, 165, 255)
                    self.report_generator.update_stats('micro_sleep')
                elif duracao >= 1.5:
                    status = "😴 DORMINDO!"
                    cor = (0, 0, 255)
                    self.report_generator.update_stats('deep_sleep')
                    if time.time() - self.last_alert_time > 5:
                        self.falar("Acorda agora!")
                        self.last_alert_time = time.time()
            else:
                self.olhos_fechados_start = None
            
            # Análise de postura
            posture_status, bad_posture = self.posture_analyzer.analyze_posture(frame, face_pos)
            if bad_posture and time.time() - self.last_posture_alert > 10:
                self.falar("Cuidado com a postura")
                self.last_posture_alert = time.time()
                self.report_generator.update_stats('bad_posture')
            
            # Detecção de movimento
            movement_detected = False
            if self.prev_face_center:
                movement = np.linalg.norm(np.array([x+w//2, y+h//2]) - np.array(self.prev_face_center))
                movement_detected = movement > 20
                self.movement_history.append(movement)
                
                # Previsão de queda
                avg_movement = np.mean(self.movement_history) if self.movement_history else 0
                features = self.fall_predictor.extract_features(
                    avg_movement,
                    list(self.posture_analyzer.posture_history),
                    ear
                )
                risk_text, risk_score = self.fall_predictor.predict_fall_risk(features)
                
                if risk_score > 0.7 and time.time() - self.last_fall_alert_time > 30:
                    self.falar(f"Atenção! {risk_text}")
                    self.video_recorder.start_recording("high_risk", frame)
                    self.report_generator.update_stats('fall')
                    self.last_fall_alert_time = time.time()
            
            self.prev_face_center = (x+w//2, y+h//2)
            
            # Desenha informações
            cv2.putText(frame, f"Status: {status}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, cor, 2)
            cv2.putText(frame, f"Postura: {posture_status}", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)
            cv2.putText(frame, f"Qualidade: {self.power_saver.current_quality.upper()}", (10, 90), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            
            if self.video_recorder.is_recording:
                cv2.putText(frame, "🔴 GRAVANDO", (10, 120), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        
        # Verifica economia de energia
        self.power_saver.check_idle(len(faces) > 0)
        
        # Grava frame
        self.video_recorder.record_frame(frame)
        self.video_recorder.add_to_buffer(frame)
        
        # Gera relatório periódico
        if time.time() - self.last_report_time > 3600:
            self.report_generator.generate_daily_report()
            self.last_report_time = time.time()
        
        return frame
    
    def update_frame(self):
        if not self.running:
            return
        
        try:
            if self.cap:
                ret, frame = self.cap.read()
                if not ret:
                    self._init_camera()
                    if self.video_label:
                        self.video_label.after(100, self.update_frame)
                    return
                frame = cv2.flip(frame, 1)
            else:
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(frame, "MODO DE SIMULACAO", (150, 240), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                cv2.putText(frame, "Pressione ESC para sair", (200, 300), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            frame = self.process_frame(frame)
            
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img = img.resize((800, 600), Image.Resampling.LANCZOS)
            imgtk = ImageTk.PhotoImage(image=img)
            
            if self.video_label:
                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)
            
            if self.video_label:
                self.video_label.after(33, self.update_frame)
                
        except Exception as e:
            print(f"Erro: {e}")
            if self.video_label:
                self.video_label.after(100, self.update_frame)
    
    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("Senior Monitor Expert - Sistema Completo")
        self.root.geometry("850x700")
        self.root.configure(bg='black')
        
        video_frame = tk.Frame(self.root, bg='black')
        video_frame.pack(padx=10, pady=10)
        self.video_label = tk.Label(video_frame, bg='black')
        self.video_label.pack()
        
        control_frame = tk.Frame(self.root, bg='black')
        control_frame.pack(pady=10)
        
        tk.Button(control_frame, text="Gerar Relatório", command=self.generate_report,
                 bg='blue', fg='white', font=('Arial', 10, 'bold'), padx=10, pady=5).pack(side='left', padx=5)
        
        tk.Button(control_frame, text="Sair", command=self.quit_app,
                 bg='red', fg='white', font=('Arial', 10, 'bold'), padx=10, pady=5).pack(side='left', padx=5)
        
        info_text = """
        🚀 SISTEMA COMPLETO - RECURSOS ATIVOS:
        ✅ Detecção de olhos e sono
        ✅ Gravação automática de eventos
        ✅ Análise de postura
        ✅ Previsão de risco de queda
        ✅ Relatórios periódicos
        ✅ Modo economia de energia
        """
        
        tk.Label(self.root, text=info_text, font=('Arial', 9), 
                fg='lightgray', bg='black', justify='left').pack(pady=5)
    
    def generate_report(self):
        filename = self.report_generator.generate_daily_report()
        messagebox.showinfo("Relatório Gerado", f"Relatório salvo em:\n{filename}")
    
    def quit_app(self):
        print("🛑 Encerrando sistema...")
        self.running = False
        self.video_recorder.stop_recording()
        if self.cap:
            self.cap.release()
        if self.root:
            self.root.quit()
            self.root.destroy()
    
    def run(self):
        print("="*60)
        print("🚀 SENIOR MONITOR EXPERT - SISTEMA COMPLETO")
        print("="*60)
        print("Recursos ativos:")
        print("✅ Detecção de olhos e sono")
        print("✅ Gravação automática de eventos")
        print("✅ Análise de postura")
        print("✅ Previsão de risco de queda")
        print("✅ Relatórios periódicos")
        print("✅ Modo economia de energia")
        print("="*60)
        
        self.setup_gui()
        self.update_frame()
        
        if self.root:
            self.root.mainloop()

if __name__ == "__main__":
    monitor = SeniorMonitorExpert()
    monitor.run()