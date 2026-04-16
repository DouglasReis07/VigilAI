import cv2
import time
import pyttsx3
import threading
import numpy as np
from collections import deque
import tkinter as tk
from tkinter import messagebox, scrolledtext
from PIL import Image, ImageTk
from datetime import datetime
import os
import json
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import warnings
warnings.filterwarnings('ignore')

# ==================== LOGS COMPLETOS ====================
class ActivityLogger:
    def __init__(self):
        self.log_file = f"log_{datetime.now().strftime('%Y%m%d')}.csv"
        self.log_buffer = deque(maxlen=50)
        self.buffer_size = 10
        
        self.stats = {
            'micro_sleeps': 0,
            'deep_sleeps': 0,
            'fall_alerts': 0,
            'high_risk_events': [],
            'posture_issues': 0,
            'medications_taken': 0,
            'medications_total': 0,
            'activity_periods': [],
            'risk_peaks': []
        }
        
        try:
            if not os.path.exists(self.log_file):
                with open(self.log_file, 'w', encoding='utf-8') as f:
                    f.write("timestamp,event,details,severity\n")
        except Exception as e:
            print(f"Erro ao criar arquivo de log: {e}")
    
    def log_event(self, event, details, severity="INFO"):
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_buffer.append(f"{timestamp},{event},{details},{severity}")
        
        if event == "SLEEP":
            if "Micro-sono" in details:
                self.stats['micro_sleeps'] += 1
            elif "Sono profundo" in details:
                self.stats['deep_sleeps'] += 1
        elif event == "FALL":
            self.stats['fall_alerts'] += 1
        elif event == "HIGH_RISK":
            self.stats['high_risk_events'].append(details)
        elif event == "MEDICATION":
            if "tomado" in details.lower():
                self.stats['medications_taken'] += 1
        
        if len(self.log_buffer) >= self.buffer_size:
            self._flush_buffer()
    
    def _flush_buffer(self):
        if self.log_buffer:
            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write("\n".join(self.log_buffer) + "\n")
                self.log_buffer.clear()
            except Exception as e:
                print(f"Erro ao salvar logs: {e}")
    
    def update_medication_stats(self, total):
        self.stats['medications_total'] = total
    
    def add_activity_period(self, activity, start, end):
        self.stats['activity_periods'].append({
            'activity': activity,
            'start': start,
            'end': end,
            'duration': (end - start).total_seconds() / 60
        })
    
    def add_risk_peak(self, risk, time):
        self.stats['risk_peaks'].append({'risk': risk, 'time': time})
    
    def increment_medication_taken(self):
        self.stats['medications_taken'] += 1
    
    def get_summary(self):
        active_periods = [p for p in self.stats['activity_periods'] if p['activity'] == 'ativo']
        most_active = max(active_periods, key=lambda x: x['duration']) if active_periods else None
        
        avg_risk = np.mean([p['risk'] for p in self.stats['risk_peaks']]) if self.stats['risk_peaks'] else 0
        
        med_adherence = 0
        if self.stats['medications_total'] > 0:
            med_adherence = (self.stats['medications_taken'] / self.stats['medications_total']) * 100
        
        return {
            'micro_sleeps': self.stats['micro_sleeps'],
            'deep_sleeps': self.stats['deep_sleeps'],
            'fall_alerts': self.stats['fall_alerts'],
            'high_risk_count': len(self.stats['high_risk_events']),
            'med_adherence': med_adherence,
            'medications_taken': self.stats['medications_taken'],
            'medications_total': self.stats['medications_total'],
            'most_active_period': most_active,
            'avg_risk': avg_risk,
            'risk_peaks': self.stats['risk_peaks'][-5:] if self.stats['risk_peaks'] else []
        }
    
    def close(self):
        self._flush_buffer()

# ==================== DETECÇÃO DE QUEDA ====================
class FallDetector:
    def __init__(self):
        self.fall_threshold = 200
        self.fall_history = deque(maxlen=10)
        self.consecutive_falls = 0
        self.min_falls_to_confirm = 3
        self.last_fall_time = 0
        self.cooldown = 30
        self.debug = False
        
    def detect_fall(self, movement_speed, face_y, frame_height, face_detected):
        current_time = time.time()
        
        if current_time - self.last_fall_time < self.cooldown:
            return False
        
        if movement_speed > 250 and not face_detected and self.consecutive_falls > 0:
            self.consecutive_falls += 1
            if self.consecutive_falls >= self.min_falls_to_confirm:
                self.consecutive_falls = 0
                self.last_fall_time = current_time
                return True
        
        if movement_speed < 100:
            self.consecutive_falls = 0
        elif movement_speed > 200:
            self.consecutive_falls += 1
        
        return False

# ==================== SONS ====================
class SoundManager:
    def __init__(self):
        self.enabled = True
        
    def play_alert(self, alert_type):
        if not self.enabled:
            return
        try:
            import winsound
            sounds = {
                'fall': (1000, 800),
                'sleep': (800, 400),
                'medication': (600, 300)
            }
            if alert_type in sounds:
                freq, duration = sounds[alert_type]
                winsound.Beep(freq, duration)
        except:
            pass

# ==================== MODO NOTURNO ====================
class NightMode:
    def __init__(self):
        self.active = False
        self.last_check = 0
        self.check_interval = 60
        
    def check_night(self):
        current_time = time.time()
        if current_time - self.last_check > self.check_interval:
            hour = datetime.now().hour
            self.active = hour < 6 or hour >= 22
            self.last_check = current_time
        return self.active
    
    def get_bg_color(self):
        return '#1a1a2e' if self.active else '#2c3e50'

# ==================== DASHBOARD ====================
class RealtimeDashboard:
    def __init__(self, parent):
        self.parent = parent
        self.figure = Figure(figsize=(8, 4), dpi=70, facecolor='#2c3e50')
        self.canvas = FigureCanvasTkAgg(self.figure, parent)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.risk_history = deque(maxlen=30)
        self.sleep_history = deque(maxlen=30)
        self.setup_graphs()
        
    def setup_graphs(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_title('Monitoramento em Tempo Real - VigilAI', color='white', fontsize=10)
        ax.set_facecolor('#34495e')
        ax.tick_params(colors='white')
        ax.set_ylim([0, 1])
        ax.set_xlabel('Tempo', color='white')
        ax.set_ylabel('Nível', color='white')
        self.figure.tight_layout()
        self.canvas.draw()
    
    def update_dashboard(self, fall_risk, is_sleeping):
        self.risk_history.append(fall_risk)
        self.sleep_history.append(1 if is_sleeping else 0)
        
        self.figure.clear()
        
        ax1 = self.figure.add_subplot(211)
        if len(self.risk_history) > 0:
            ax1.plot(list(self.risk_history), color='orange', linewidth=2, label='Risco')
            ax1.axhline(y=0.7, color='red', linestyle='--', alpha=0.5, label='Alerta')
        ax1.set_title('Risco de Queda - VigilAI', color='white', fontsize=9)
        ax1.set_facecolor('#34495e')
        ax1.tick_params(colors='white')
        ax1.set_ylim([0, 1])
        ax1.legend(loc='upper right', facecolor='#34495e', labelcolor='white')
        
        ax2 = self.figure.add_subplot(212)
        if len(self.sleep_history) > 0:
            ax2.plot(list(self.sleep_history), color='blue', linewidth=2, label='Sono')
        ax2.set_title('Estado de Sono - VigilAI', color='white', fontsize=9)
        ax2.set_facecolor('#34495e')
        ax2.tick_params(colors='white')
        ax2.set_ylim([-0.1, 1.1])
        ax2.set_yticks([0, 1])
        ax2.set_yticklabels(['Acordado', 'Dormindo'], color='white')
        ax2.legend(loc='upper right', facecolor='#34495e', labelcolor='white')
        
        self.figure.tight_layout()
        self.canvas.draw()

# ==================== CALENDÁRIO DE MEDICAMENTOS ====================
def validate_time(time_str):
    try:
        hour, minute = map(int, time_str.split(':'))
        return 0 <= hour <= 23 and 0 <= minute <= 59
    except:
        return False

class MedicationCalendar:
    def __init__(self):
        self.medications = []
        self.medications_file = "medications.json"
        self.load_medications()
    
    def add_medication(self, name, dosage, schedule, notes=""):
        med = {
            'name': name, 
            'dosage': dosage, 
            'schedule': schedule, 
            'notes': notes, 
            'last_taken': None,
            'last_taken_date': None
        }
        self.medications.append(med)
        self.save_medications()
        print(f"✅ Medicamento adicionado: {name}")
        return med
    
    def save_medications(self):
        try:
            with open(self.medications_file, 'w', encoding='utf-8') as f:
                json.dump(self.medications, f, indent=2, ensure_ascii=False)
            print(f"💾 Medicamentos salvos: {len(self.medications)}")
        except Exception as e:
            print(f"Erro ao salvar medicamentos: {e}")
    
    def load_medications(self):
        if os.path.exists(self.medications_file):
            try:
                with open(self.medications_file, 'r', encoding='utf-8') as f:
                    self.medications = json.load(f)
                print(f"📂 Medicamentos carregados: {len(self.medications)}")
            except Exception as e:
                print(f"Erro ao carregar medicamentos: {e}")
                self.medications = []
    
    def check_reminders(self):
        current = datetime.now()
        reminders = []
        for med in self.medications:
            for schedule_time in med['schedule']:
                try:
                    hour, minute = map(int, schedule_time.split(':'))
                    scheduled = current.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    diff = abs((current - scheduled).total_seconds())
                    
                    if diff < 300:
                        last_taken = med.get('last_taken_date')
                        today_str = current.strftime('%Y-%m-%d')
                        
                        if last_taken != today_str:
                            reminders.append(med)
                            break
                except Exception as e:
                    print(f"Erro ao verificar lembrete: {e}")
        return reminders
    
    def mark_as_taken(self, name):
        try:
            for med in self.medications:
                if med['name'] == name:
                    now = datetime.now()
                    med['last_taken'] = now.strftime('%H:%M:%S')
                    med['last_taken_date'] = now.strftime('%Y-%m-%d')
                    self.save_medications()
                    print(f"✅ Medicamento marcado como tomado: {name}")
                    return True
            print(f"❌ Medicamento não encontrado: {name}")
            return False
        except Exception as e:
            print(f"Erro ao marcar medicamento: {e}")
            return False
    
    def get_today_schedule(self):
        today = datetime.now().date()
        today_str = today.strftime('%Y-%m-%d')
        schedule = []
        total = 0
        
        for med in self.medications:
            for time_str in med['schedule']:
                total += 1
                taken = False
                
                if med.get('last_taken_date') == today_str:
                    taken = True
                
                schedule.append({
                    'name': med['name'], 
                    'dosage': med['dosage'], 
                    'time': time_str, 
                    'taken': taken
                })
        
        return sorted(schedule, key=lambda x: x['time']), total
    
    def get_medication_stats(self):
        schedule, total = self.get_today_schedule()
        taken = sum(1 for s in schedule if s['taken'])
        return taken, total

# ==================== INTERFACE PRINCIPAL VIGILAI ====================
class VigilAI:
    def __init__(self):
        # Módulos
        self.dashboard = None
        self.medications = MedicationCalendar()
        self.logger = ActivityLogger()
        self.fall_detector = FallDetector()
        self.sound_manager = SoundManager()
        self.night_mode = NightMode()
        
        self.fall_detector.debug = False
        
        # Voz
        self.engine = None
        self._init_engine()
        
        # Câmera
        self.cap = None
        self.face_cascade = None
        self.eye_cascade = None
        self._init_camera()
        
        # Estado
        self.eyes_closed_start = None
        self.last_alert_time = 0
        self.last_reminder_check = 0
        self.movement_history = deque(maxlen=10)
        self.prev_center = None
        self.face_detected = False
        self.frame_count = 0
        self.base_process_rate = 2
        self.process_every_n_frames = self.base_process_rate
        self.high_motion_count = 0
        
        # Interface
        self.root = None
        self.video_label = None
        self.med_listbox = None
        self.running = True
        
        # Estatísticas
        self.fall_risk = 0
        self.is_sleeping = False
        self.last_activity_change = datetime.now()
        self.current_activity = "ativo"
        
        # FPS
        self.last_fps_time = time.time()
        self.fps_count = 0
        self.fps = 0
        self.show_fps = False
        
        taken, total = self.medications.get_medication_stats()
        self.logger.update_medication_stats(total)
        
        print("✅ VigilAI - Sistema de Monitoramento inicializado!")
    
    def _init_engine(self):
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 170)
            self.engine.setProperty('volume', 0.9)
        except Exception as e:
            print(f"Erro na voz: {e}")
            self.engine = None
    
    def _init_camera(self):
        try:
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        except Exception as e:
            print(f"⚠️ Erro ao carregar cascades: {e}")
        
        for i in [0, 1]:
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
                ret, frame = cap.read()
                if ret and frame is not None:
                    self.cap = cap
                    print(f"✅ Câmera {i} OK (modo rápido)")
                    return
                cap.release()
        
        print("⚠️ Modo simulação")
        self.cap = None
    
    def falar(self, texto):
        if self.engine:
            def speak():
                try:
                    self.engine.say(texto)
                    self.engine.runAndWait()
                except Exception as e:
                    print(f"Erro ao falar: {e}")
            threading.Thread(target=speak, daemon=True).start()
    
    def get_risk_color(self, risk):
        if risk > 0.7:
            return (0, 0, 255)
        elif risk > 0.4:
            return (0, 165, 255)
        return (0, 255, 0)
    
    def draw_sleep_bar(self, frame, duration):
        bar_width = 150
        bar_height = 10
        progress = min(duration / 5, 1.0)
        
        cv2.rectangle(frame, (10, 95), (10 + bar_width, 95 + bar_height), (50, 50, 50), -1)
        cv2.rectangle(frame, (10, 95), (10 + int(bar_width * progress), 95 + bar_height), (0, 0, 255), -1)
        return frame
    
    def process_frame_light(self, frame):
        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        status = "Ativo"
        ear = 0.3
        movement = 0
        self.face_detected = False
        face_y = 0
        
        if self.frame_count % self.process_every_n_frames == 0:
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5, minSize=(60, 60))
        else:
            faces = []
        
        for (x, y, fw, fh) in faces:
            self.face_detected = True
            face_y = y + fh
            cv2.rectangle(frame, (x, y), (x+fw, y+fh), (255, 0, 0), 1)
            
            roi = gray[y:y+fh, x:x+fw]
            eyes = self.eye_cascade.detectMultiScale(roi, 1.1, 5, minSize=(15, 15))
            ear = 0.1 if len(eyes) < 2 else 0.3
            
            if self.prev_center:
                dx = (x+fw//2) - self.prev_center[0]
                dy = (y+fh//2) - self.prev_center[1]
                movement = np.sqrt(dx*dx + dy*dy)
                self.movement_history.append(movement)
            
            self.prev_center = (x+fw//2, y+fh//2)
        
        self.frame_count += 1
        
        avg_movement = np.mean(self.movement_history) if self.movement_history else 0
        
        if avg_movement > 100:
            self.high_motion_count = min(10, self.high_motion_count + 1)
        else:
            self.high_motion_count = max(0, self.high_motion_count - 1)
        
        if self.high_motion_count > 3:
            self.process_every_n_frames = 1
        elif self.high_motion_count == 0:
            self.process_every_n_frames = self.base_process_rate
        
        # Detecção de sono com alerta de voz
        sleep_duration = 0
        current_time = time.time()
        
        if ear < 0.2:
            if self.eyes_closed_start is None:
                self.eyes_closed_start = current_time
                print("👀 Olhos fechados detectados!")
            
            sleep_duration = current_time - self.eyes_closed_start
            
            if sleep_duration >= 1.5:
                status = "😴 DORMINDO"
                if not self.is_sleeping:
                    self.logger.log_event("SLEEP", "Sono profundo detectado", "WARNING")
                    self.falar("Acorde! Está dormindo!")
                    self.sound_manager.play_alert('sleep')
                self.is_sleeping = True
                
                if current_time - self.last_alert_time > 10:
                    self.falar("Acorde! Você está dormindo!")
                    self.last_alert_time = current_time
                    
            elif sleep_duration >= 0.5:
                status = "⚠️ SONOLENTO"
                if not self.is_sleeping:
                    self.logger.log_event("SLEEP", "Micro-sono detectado", "INFO")
                    self.falar("Cuidado, está com sono!")
                    self.sound_manager.play_alert('sleep')
                self.is_sleeping = True
            else:
                self.is_sleeping = False
        else:
            if self.eyes_closed_start is not None:
                print(f"👀 Olhos abertos após {current_time - self.eyes_closed_start:.1f}s")
            self.eyes_closed_start = None
            self.is_sleeping = False
        
        # Cálculo do risco de queda
        self.fall_risk = 0
        if avg_movement > 200:
            self.fall_risk += 0.5
        if not self.face_detected and len(self.movement_history) > 0:
            self.fall_risk += 0.3
        if self.is_sleeping:
            self.fall_risk += 0.1
        
        self.fall_risk = min(self.fall_risk, 1.0)
        
        if self.fall_risk > 0.7:
            self.logger.add_risk_peak(self.fall_risk, datetime.now())
        
        # Detecção de queda
        is_fall = self.fall_detector.detect_fall(avg_movement, face_y, h, self.face_detected)
        
        if is_fall:
            status = "🚨 QUEDA!"
            self.sound_manager.play_alert('fall')
            self.falar("URGENTE! Queda detectada! Acionando socorro!")
            self.logger.log_event("FALL", f"Movimento: {avg_movement:.0f}px", "CRITICAL")
        
        # Atividade
        new_activity = "ativo" if not self.is_sleeping else "dormindo"
        if new_activity != self.current_activity:
            self.logger.add_activity_period(self.current_activity, self.last_activity_change, datetime.now())
            self.current_activity = new_activity
            self.last_activity_change = datetime.now()
        
        risk_color = self.get_risk_color(self.fall_risk)
        
        # Interface na tela
        cv2.putText(frame, f"{status}", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, risk_color, 2)
        cv2.putText(frame, f"Risco Queda: {self.fall_risk:.0%}", (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.6, risk_color, 2)
        cv2.putText(frame, f"Movimento: {avg_movement:.0f}px", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        if self.eyes_closed_start:
            duration = current_time - self.eyes_closed_start
            cv2.putText(frame, f"Olhos fechados: {duration:.1f}s", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            frame = self.draw_sleep_bar(frame, duration)
        
        if self.fall_risk > 0.7:
            cv2.putText(frame, "⚠️ ALTO RISCO!", (w-130, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        if self.show_fps:
            self.fps_count += 1
            if time.time() - self.last_fps_time >= 1:
                self.fps = self.fps_count
                self.fps_count = 0
                self.last_fps_time = time.time()
            cv2.putText(frame, f"FPS: {self.fps}", (w-70, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
        
        if self.dashboard:
            self.dashboard.update_dashboard(self.fall_risk, self.is_sleeping)
        
        return frame
    
    def update_medication_list(self):
        if self.med_listbox:
            self.med_listbox.delete(0, tk.END)
            schedule, _ = self.medications.get_today_schedule()
            
            if not schedule:
                self.med_listbox.insert(tk.END, " Nenhum medicamento")
                self.med_listbox.itemconfig(0, fg='gray')
            else:
                for item in schedule:
                    status = "✅" if item['taken'] else "⏰"
                    text = f"{status} {item['time']} - {item['name']} ({item['dosage']})"
                    self.med_listbox.insert(tk.END, text)
                    
                    if item['taken']:
                        self.med_listbox.itemconfig(tk.END, fg='green')
                    else:
                        self.med_listbox.itemconfig(tk.END, fg='orange')
    
    def add_medication_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Adicionar Medicamento - VigilAI")
        dialog.geometry("400x450")
        dialog.configure(bg='#2c3e50')
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="Nome:", bg='#2c3e50', fg='white', font=('Arial', 10)).pack(pady=5)
        name_entry = tk.Entry(dialog, width=30, font=('Arial', 10))
        name_entry.pack(pady=5)
        
        tk.Label(dialog, text="Dosagem:", bg='#2c3e50', fg='white', font=('Arial', 10)).pack(pady=5)
        dosage_entry = tk.Entry(dialog, width=30, font=('Arial', 10))
        dosage_entry.pack(pady=5)
        
        tk.Label(dialog, text="Horários (ex: 08:00, 20:00):", bg='#2c3e50', fg='white', font=('Arial', 10)).pack(pady=5)
        schedule_entry = tk.Entry(dialog, width=30, font=('Arial', 10))
        schedule_entry.pack(pady=5)
        
        error_label = tk.Label(dialog, text="", bg='#2c3e50', fg='red', font=('Arial', 9))
        error_label.pack(pady=5)
        
        def save():
            name = name_entry.get().strip()
            dosage = dosage_entry.get().strip()
            schedule_raw = [s.strip() for s in schedule_entry.get().split(',') if s.strip()]
            
            errors = []
            if not name:
                errors.append("Nome é obrigatório")
            if not dosage:
                errors.append("Dosagem é obrigatória")
            if not schedule_raw:
                errors.append("Pelo menos um horário é obrigatório")
            else:
                invalid_times = [t for t in schedule_raw if not validate_time(t)]
                if invalid_times:
                    errors.append(f"Horário inválido: {', '.join(invalid_times)}")
            
            if errors:
                error_label.config(text="\n".join(errors))
                return
            
            self.medications.add_medication(name, dosage, schedule_raw)
            taken, total = self.medications.get_medication_stats()
            self.logger.update_medication_stats(total)
            self.update_medication_list()
            dialog.destroy()
            self.falar(f"Medicamento {name} adicionado")
            messagebox.showinfo("Sucesso", f"Medicamento {name} adicionado com sucesso!")
        
        tk.Button(dialog, text="Salvar", command=save, bg='#27ae60', fg='white', 
                 font=('Arial', 10, 'bold'), padx=20, pady=5).pack(pady=15)
    
    def mark_taken_dialog(self):
        if not self.medications.medications:
            messagebox.showinfo("Info", "Nenhum medicamento cadastrado")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Marcar Medicamento como Tomado - VigilAI")
        dialog.geometry("350x300")
        dialog.configure(bg='#2c3e50')
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="Selecione o medicamento:", bg='#2c3e50', fg='white', 
                font=('Arial', 11, 'bold')).pack(pady=10)
        
        listbox_frame = tk.Frame(dialog, bg='#2c3e50')
        listbox_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(listbox_frame, height=6, font=('Arial', 10), 
                              bg='#34495e', fg='white', selectbackground='#3498db',
                              yscrollcommand=scrollbar.set)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)
        
        for med in self.medications.medications:
            listbox.insert(tk.END, f"{med['name']} - {med['dosage']}")
        
        def mark():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("Seleção", "Selecione um medicamento")
                return
            
            selected = listbox.get(selection[0])
            name = selected.split(' - ')[0]
            
            if self.medications.mark_as_taken(name):
                taken, total = self.medications.get_medication_stats()
                self.logger.update_medication_stats(total)
                self.logger.increment_medication_taken()
                self.logger.log_event("MEDICATION", f"Medicamento tomado: {name}", "INFO")
                self.update_medication_list()
                self.falar(f"{name} registrado como tomado")
                self.sound_manager.play_alert('medication')
                messagebox.showinfo("Sucesso", f"✅ {name} registrado como tomado!")
                dialog.destroy()
            else:
                messagebox.showerror("Erro", f"Não foi possível marcar {name}")
        
        btn_frame = tk.Frame(dialog, bg='#2c3e50')
        btn_frame.pack(pady=15)
        
        tk.Button(btn_frame, text="✅ Marcar como Tomado", command=mark, 
                 bg='#27ae60', fg='white', font=('Arial', 10, 'bold'), 
                 padx=15, pady=5).pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="Cancelar", command=dialog.destroy, 
                 bg='#e74c3c', fg='white', font=('Arial', 10, 'bold'), 
                 padx=15, pady=5).pack(side='left', padx=5)
    
    def generate_report(self):
        stats = self.logger.get_summary()
        schedule, _ = self.medications.get_today_schedule()
        
        report = f"""
{'='*60}
RELATÓRIO VIGILAI - SISTEMA DE MONITORAMENTO
{'='*60}

📅 Data e Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

{'='*60}
📊 ESTATÍSTICAS DO DIA
{'='*60}

😴 SONO E CANSACO:
   • Micro-sonos detectados: {stats['micro_sleeps']}
   • Sono profundo detectado: {stats['deep_sleeps']}
   • Total de eventos de sono: {stats['micro_sleeps'] + stats['deep_sleeps']}

⚠️  QUEDAS E RISCOS:
   • Alertas de queda: {stats['fall_alerts']}
   • Picos de alto risco: {stats['high_risk_count']}
   • Risco médio do dia: {stats['avg_risk']:.1%}

💊 MEDICAMENTOS:
   • Total de doses do dia: {stats['medications_total']}
   • Doses tomadas: {stats['medications_taken']}
   • Taxa de adesão: {stats['med_adherence']:.1f}%
   
   Detalhamento:
"""
        for item in schedule:
            status = "✅ TOMADO" if item['taken'] else "⏰ PENDENTE"
            report += f"      • {item['time']} - {item['name']} ({item['dosage']}) - {status}\n"
        
        if stats['most_active_period']:
            report += f"""
📈 ATIVIDADE:
   • Período mais ativo: {stats['most_active_period']['activity']}
   • Duração: {stats['most_active_period']['duration']:.0f} minutos
"""
        
        if stats['risk_peaks']:
            report += f"""
🚨 ÚLTIMOS PICOS DE RISCO:
"""
            for peak in stats['risk_peaks']:
                report += f"      • {peak['time'].strftime('%H:%M:%S')} - Risco: {peak['risk']:.1%}\n"
        
        report += f"""
{'='*60}
💡 RECOMENDAÇÕES PERSONALIZADAS - VIGILAI
{'='*60}
"""
        
        if stats['micro_sleeps'] > 5:
            report += "   • ⚠️ Muitos episódios de micro-sono - Consulte um médico\n"
        if stats['fall_alerts'] > 0:
            report += "   • 🚨 Quedas detectadas - Procure assistência médica\n"
        if stats['high_risk_count'] > 3:
            report += "   • ⚠️ Alto risco de queda frequente - Revise ambiente doméstico\n"
        if stats['med_adherence'] < 80 and stats['medications_total'] > 0:
            report += "   • 💊 Baixa adesão aos medicamentos - Crie lembretes adicionais\n"
        
        if (stats['micro_sleeps'] <= 5 and stats['fall_alerts'] == 0 and 
            stats['high_risk_count'] <= 3 and stats['med_adherence'] >= 80):
            report += "   • ✅ Ótimo dia! Mantenha os cuidados e continue assim!\n"
        
        filename = f"relatorio_vigilai_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        messagebox.showinfo("📄 Relatório VigilAI", 
                           f"Relatório salvo como:\n{filename}\n\n" +
                           f"Resumo:\n"
                           f"- Eventos de sono: {stats['micro_sleeps'] + stats['deep_sleeps']}\n"
                           f"- Alertas de queda: {stats['fall_alerts']}\n"
                           f"- Adesão medicamentos: {stats['med_adherence']:.1f}%")
    
    def view_logs(self):
        logs = []
        if os.path.exists(self.logger.log_file):
            with open(self.logger.log_file, 'r', encoding='utf-8') as f:
                logs = f.readlines()[1:]
        
        if not logs:
            messagebox.showinfo("Logs", "Nenhum evento registrado hoje")
            return
        
        log_window = tk.Toplevel(self.root)
        log_window.title("Logs do Dia - VigilAI")
        log_window.geometry("600x400")
        log_window.configure(bg='#2c3e50')
        
        text_area = scrolledtext.ScrolledText(log_window, wrap=tk.WORD, width=80, height=20, font=('Courier', 9))
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        for log in logs[-100:]:
            text_area.insert(tk.END, log)
        
        text_area.config(state=tk.DISABLED)
    
    def update_frame(self):
        if not self.running:
            return
        
        try:
            if self.cap:
                ret, frame = self.cap.read()
                if not ret:
                    if self.video_label:
                        self.video_label.after(100, self.update_frame)
                    return
                frame = cv2.flip(frame, 1)
                frame = cv2.resize(frame, (640, 480))
            else:
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(frame, "VIGILAI - MODO SIMULACAO", (150, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            
            frame = self.process_frame_light(frame)
            
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            
            if self.video_label:
                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)
            
            now = time.time()
            if now - self.last_reminder_check > 60:
                reminders = self.medications.check_reminders()
                for med in reminders:
                    self.sound_manager.play_alert('medication')
                    self.falar(f"Hora de tomar {med['dosage']} de {med['name']}")
                    messagebox.showwarning("💊 Lembrete VigilAI", f"Hora de tomar {med['name']}\n{med['dosage']}")
                self.last_reminder_check = now
            
            if self.video_label:
                self.video_label.after(33, self.update_frame)
                
        except Exception as e:
            print(f"Erro: {e}")
            if self.video_label:
                self.video_label.after(100, self.update_frame)
    
    def setup_gui(self):
        bg_color = self.night_mode.get_bg_color()
        
        self.root = tk.Tk()
        self.root.title("VigilAI - Sistema de Monitoramento Inteligente")
        self.root.geometry("1200x700")
        self.root.configure(bg=bg_color)
        
        # Teclas de atalho
        self.root.bind('<F1>', lambda e: self.add_medication_dialog())
        self.root.bind('<F2>', lambda e: self.mark_taken_dialog())
        self.root.bind('<F3>', lambda e: self.generate_report())
        self.root.bind('<F4>', lambda e: self.view_logs())
        self.root.bind('<F5>', lambda e: self.toggle_fps())
        self.root.bind('<Escape>', lambda e: self.quit_app())
        self.root.bind('<F11>', lambda e: self.toggle_fullscreen())
        
        # Layout principal
        main = tk.Frame(self.root, bg=bg_color)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Frame do vídeo (esquerda)
        video_frame = tk.Frame(main, bg='black', width=650, height=500)
        video_frame.pack(side='left', padx=5)
        video_frame.pack_propagate(False)
        self.video_label = tk.Label(video_frame, bg='black')
        self.video_label.pack(fill=tk.BOTH, expand=True)
        
        # Painel direito
        right = tk.Frame(main, bg=bg_color, width=500)
        right.pack(side='right', fill=tk.BOTH, expand=True, padx=5)
        
        # Dashboard
        dash_frame = tk.Frame(right, bg=bg_color, height=300)
        dash_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.dashboard = RealtimeDashboard(dash_frame)
        
        # Medicamentos
        med_frame = tk.LabelFrame(right, text="💊 Medicamentos de Hoje - VigilAI", bg=bg_color, fg='white', font=('Arial', 10, 'bold'))
        med_frame.pack(fill=tk.X, pady=5)
        
        self.med_listbox = tk.Listbox(med_frame, height=4, font=('Arial', 9), bg='#34495e', fg='white')
        self.med_listbox.pack(fill=tk.X, padx=5, pady=5)
        self.update_medication_list()
        
        # Botões
        btn_frame = tk.Frame(right, bg=bg_color)
        btn_frame.pack(fill=tk.X, pady=10)
        
        buttons = [
            ("➕ Medicamento (F1)", self.add_medication_dialog, '#3498db'),
            ("✅ Tomado (F2)", self.mark_taken_dialog, '#27ae60'),
            ("📊 Relatório (F3)", self.generate_report, '#e67e22'),
            ("📋 Logs (F4)", self.view_logs, '#9b59b6'),
            ("🎮 FPS (F5)", self.toggle_fps, '#1abc9c'),
            ("❌ Sair (ESC)", self.quit_app, '#e74c3c')
        ]
        
        for text, cmd, color in buttons:
            tk.Button(btn_frame, text=text, command=cmd, bg=color, fg='white', 
                     font=('Arial', 9), padx=8, pady=4).pack(side='left', padx=4)
        
        # Status
        self.status_label = tk.Label(right, text="✅ VigilAI Ativo | Monitorando...", font=('Arial', 9), 
                                     bg=bg_color, fg='#2ecc71')
        self.status_label.pack(pady=5)
        
        # Info
        info = "VigilAI - F1=Add | F2=Tomado | F3=Relatório | F4=Logs | F5=FPS | F11=Tela Cheia | ESC=Sair"
        tk.Label(right, text=info, font=('Arial', 8), bg=bg_color, fg='gray').pack()
    
    def toggle_fps(self):
        self.show_fps = not self.show_fps
        self.falar(f"FPS {'ativado' if self.show_fps else 'desativado'}")
    
    def toggle_fullscreen(self):
        self.root.attributes('-fullscreen', not self.root.attributes('-fullscreen'))
    
    def quit_app(self):
        self.logger.add_activity_period(self.current_activity, self.last_activity_change, datetime.now())
        self.logger.close()
        self.running = False
        if self.cap:
            self.cap.release()
        if self.root:
            self.root.quit()
            self.root.destroy()
    
    def run(self):
        print("="*60)
        print("🔍 VIGILAI - SISTEMA DE MONITORAMENTO INTELIGENTE")
        print("="*60)
        print("✅ Monitoramento de sono (micro-sonos e sono profundo)")
        print("✅ Detecção de queda por movimento brusco")
        print("✅ Cálculo de risco de queda com cores")
        print("✅ Barra de progresso do sono")
        print("✅ Dashboard com gráficos em tempo real")
        print("✅ Medicamentos com lembretes")
        print("✅ Relatórios completos com estatísticas")
        print("✅ Alertas de voz para sono")
        print("="*60)
        print("\n📌 Comandos VigilAI:")
        print("   F1 - Adicionar medicamento")
        print("   F2 - Marcar medicamento como tomado")
        print("   F3 - Gerar relatório completo")
        print("   F4 - Visualizar logs do dia")
        print("   F5 - Ativar/desativar FPS")
        print("   F11 - Tela cheia")
        print("   ESC - Sair")
        print("="*60)
        
        self.setup_gui()
        self.update_frame()
        
        if self.root:
            self.root.mainloop()

if __name__ == "__main__":
    vigil = VigilAI()
    vigil.run()