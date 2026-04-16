import cv2
import time
import pyttsx3
import threading
import numpy as np
from collections import deque
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from PIL import Image, ImageTk
from datetime import datetime, timedelta
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
        self.log_buffer = []
        self.buffer_size = 10
        
        # Estatísticas do dia
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
        
    def log_event(self, event, details, severity="INFO"):
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_buffer.append(f"{timestamp},{event},{details},{severity}")
        
        # Atualiza estatísticas
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
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write("\n".join(self.log_buffer) + "\n")
            self.log_buffer = []
    
    def update_medication_stats(self, total):
        self.stats['medications_total'] = total
    
    def add_activity_period(self, activity, start, end):
        self.stats['activity_periods'].append({
            'activity': activity,
            'start': start,
            'end': end,
            'duration': (end - start).total_seconds() / 60  # minutos
        })
    
    def add_risk_peak(self, risk, time):
        self.stats['risk_peaks'].append({'risk': risk, 'time': time})
    
    def get_summary(self):
        # Calcula período mais ativo
        active_periods = [p for p in self.stats['activity_periods'] if p['activity'] == 'ativo']
        most_active = max(active_periods, key=lambda x: x['duration']) if active_periods else None
        
        # Calcula risco médio
        avg_risk = np.mean([p['risk'] for p in self.stats['risk_peaks']]) if self.stats['risk_peaks'] else 0
        
        # Taxa de adesão medicamentos
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
            'risk_peaks': self.stats['risk_peaks'][-5:] if self.stats['risk_peaks'] else []  # Últimos 5
        }

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
                if self.debug:
                    print(f"🚨 QUEDA DETECTADA! Movimento: {movement_speed:.0f}px")
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
        
    def check_night(self):
        hour = datetime.now().hour
        self.active = hour < 6 or hour >= 22
        return self.active

# ==================== DASHBOARD ====================
class RealtimeDashboard:
    def __init__(self, parent):
        self.parent = parent
        self.figure = Figure(figsize=(8, 4), dpi=70, facecolor='#2c3e50')
        self.canvas = FigureCanvasTkAgg(self.figure, parent)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.risk_history = deque(maxlen=30)
        self.setup_graphs()
        
    def setup_graphs(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_title('Monitoramento em Tempo Real', color='white', fontsize=10)
        ax.set_facecolor('#34495e')
        ax.tick_params(colors='white')
        ax.set_ylim([0, 1])
        ax.set_xlabel('Tempo', color='white')
        ax.set_ylabel('Nível', color='white')
        self.figure.tight_layout()
        self.canvas.draw()
    
    def update_dashboard(self, fall_risk, is_sleeping):
        self.risk_history.append(fall_risk)
        
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        if len(self.risk_history) > 0:
            ax.plot(list(self.risk_history), color='orange', linewidth=2, label='Risco')
            ax.axhline(y=0.7, color='red', linestyle='--', alpha=0.5, label='Alerta')
        
        ax.set_title('Risco de Queda', color='white', fontsize=10)
        ax.set_facecolor('#34495e')
        ax.tick_params(colors='white')
        ax.set_ylim([0, 1])
        ax.legend(loc='upper right', facecolor='#34495e', labelcolor='white')
        
        self.figure.tight_layout()
        self.canvas.draw()

# ==================== CALENDÁRIO DE MEDICAMENTOS ====================
class MedicationCalendar:
    def __init__(self):
        self.medications = []
        self.medications_file = "medications.json"
        self.load_medications()
    
    def add_medication(self, name, dosage, schedule, notes=""):
        med = {'name': name, 'dosage': dosage, 'schedule': schedule, 'notes': notes, 'last_taken': None}
        self.medications.append(med)
        self.save_medications()
        return med
    
    def save_medications(self):
        with open(self.medications_file, 'w') as f:
            json.dump(self.medications, f, indent=2)
    
    def load_medications(self):
        if os.path.exists(self.medications_file):
            try:
                with open(self.medications_file, 'r') as f:
                    self.medications = json.load(f)
            except:
                self.medications = []
    
    def check_reminders(self):
        current = datetime.now()
        reminders = []
        for med in self.medications:
            for schedule_time in med['schedule']:
                try:
                    hour, minute = map(int, schedule_time.split(':'))
                    scheduled = current.replace(hour=hour, minute=minute, second=0)
                    diff = abs((current - scheduled).total_seconds())
                    if diff < 300:
                        last = med.get('last_taken')
                        if not last or datetime.fromisoformat(last).date() != current.date():
                            reminders.append(med)
                except:
                    pass
        return reminders
    
    def mark_as_taken(self, name):
        for med in self.medications:
            if med['name'] == name:
                med['last_taken'] = datetime.now().isoformat()
                self.save_medications()
                return True
        return False
    
    def get_today_schedule(self):
        today = datetime.now().date()
        schedule = []
        total = 0
        for med in self.medications:
            for time_str in med['schedule']:
                total += 1
                taken = False
                if med.get('last_taken'):
                    try:
                        last_date = datetime.fromisoformat(med['last_taken']).date()
                        taken = last_date == today
                    except:
                        pass
                schedule.append({'name': med['name'], 'dosage': med['dosage'], 'time': time_str, 'taken': taken})
        return sorted(schedule, key=lambda x: x['time']), total
    
    def get_medication_stats(self):
        schedule, total = self.get_today_schedule()
        taken = sum(1 for s in schedule if s['taken'])
        return taken, total

# ==================== INTERFACE PRINCIPAL ====================
class SeniorMonitorExpert:
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
        self.last_alert = 0
        self.last_reminder_check = 0
        self.movement_history = deque(maxlen=10)
        self.prev_center = None
        self.face_detected = False
        self.frame_count = 0
        self.process_every_n_frames = 2
        
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
        
        # Inicializa stats de medicamentos
        taken, total = self.medications.get_medication_stats()
        self.logger.update_medication_stats(total)
        
        print("✅ Sistema otimizado inicializado!")
    
    def _init_engine(self):
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 170)
        except:
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
                self.engine.say(texto)
                self.engine.runAndWait()
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
        cv2.rectangle(frame, (10, 30), (10 + bar_width, 30 + bar_height), (50, 50, 50), -1)
        cv2.rectangle(frame, (10, 30), (10 + int(bar_width * progress), 30 + bar_height), (0, 0, 255), -1)
        return frame
    
    def process_frame_light(self, frame):
        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        status = "Ativo"
        ear = 0.3
        movement = 0
        self.face_detected = False
        
        if self.frame_count % self.process_every_n_frames == 0:
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5, minSize=(60, 60))
        else:
            faces = []
        
        for (x, y, fw, fh) in faces:
            self.face_detected = True
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
        
        # Detecção de sono
        if ear < 0.2:
            if self.eyes_closed_start is None:
                self.eyes_closed_start = time.time()
            duration = time.time() - self.eyes_closed_start
            
            if duration >= 1.5:
                status = "😴 DORMINDO"
                if not self.is_sleeping:
                    self.logger.log_event("SLEEP", "Sono profundo detectado", "WARNING")
                self.is_sleeping = True
                if time.time() - self.last_alert > 30:
                    self.sound_manager.play_alert('sleep')
                    self.last_alert = time.time()
            elif duration >= 0.5:
                status = "⚠️ SONOLENTO"
                if not self.is_sleeping:
                    self.logger.log_event("SLEEP", "Micro-sono detectado", "INFO")
                self.is_sleeping = True
            else:
                self.is_sleeping = False
        else:
            self.eyes_closed_start = None
            self.is_sleeping = False
        
        # Cálculo de risco
        avg_movement = np.mean(self.movement_history) if self.movement_history else 0
        
        self.fall_risk = 0
        if avg_movement > 200:
            self.fall_risk += 0.5
        if not self.face_detected and len(self.movement_history) > 0:
            self.fall_risk += 0.3
        if self.is_sleeping:
            self.fall_risk += 0.1
        
        self.fall_risk = min(self.fall_risk, 1.0)
        
        # Registra picos de risco
        if self.fall_risk > 0.7:
            self.logger.add_risk_peak(self.fall_risk, datetime.now())
        
        # Detecção de queda
        is_fall = self.fall_detector.detect_fall(avg_movement, None, h, self.face_detected)
        
        if is_fall:
            status = "🚨 QUEDA!"
            self.sound_manager.play_alert('fall')
            self.falar("URGENTE! Queda detectada!")
            self.logger.log_event("FALL", f"Movimento: {avg_movement:.0f}px", "CRITICAL")
        
        # Registra atividade
        new_activity = "ativo" if not self.is_sleeping else "dormindo"
        if new_activity != self.current_activity:
            self.logger.add_activity_period(self.current_activity, self.last_activity_change, datetime.now())
            self.current_activity = new_activity
            self.last_activity_change = datetime.now()
        
        # Cores por risco
        risk_color = self.get_risk_color(self.fall_risk)
        
        # Interface na tela
        cv2.putText(frame, f"{status}", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, risk_color, 2)
        cv2.putText(frame, f"Risco: {self.fall_risk:.0%}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, risk_color, 1)
        cv2.putText(frame, f"Mov: {avg_movement:.0f}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
        
        if self.eyes_closed_start:
            duration = time.time() - self.eyes_closed_start
            frame = self.draw_sleep_bar(frame, duration)
        
        if self.fall_risk > 0.7:
            cv2.putText(frame, "ALTO RISCO!", (w-100, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        
        if self.dashboard:
            self.dashboard.update_dashboard(self.fall_risk, self.is_sleeping)
        
        return frame
    
    def update_medication_list(self):
        if self.med_listbox:
            self.med_listbox.delete(0, tk.END)
            schedule, _ = self.medications.get_today_schedule()
            if not schedule:
                self.med_listbox.insert(tk.END, " Nenhum medicamento")
            else:
                for item in schedule:
                    status = "✅" if item['taken'] else "⏰"
                    text = f"{status} {item['time']} - {item['name']} ({item['dosage']})"
                    self.med_listbox.insert(tk.END, text)
                    if not item['taken']:
                        self.med_listbox.itemconfig(tk.END, fg='orange')
    
    def add_medication_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Adicionar Medicamento")
        dialog.geometry("400x400")
        dialog.configure(bg='#2c3e50')
        
        tk.Label(dialog, text="Nome:", bg='#2c3e50', fg='white').pack(pady=5)
        name_entry = tk.Entry(dialog, width=30)
        name_entry.pack(pady=5)
        
        tk.Label(dialog, text="Dosagem:", bg='#2c3e50', fg='white').pack(pady=5)
        dosage_entry = tk.Entry(dialog, width=30)
        dosage_entry.pack(pady=5)
        
        tk.Label(dialog, text="Horários (ex: 08:00, 20:00):", bg='#2c3e50', fg='white').pack(pady=5)
        schedule_entry = tk.Entry(dialog, width=30)
        schedule_entry.pack(pady=5)
        
        def save():
            name = name_entry.get().strip()
            dosage = dosage_entry.get().strip()
            schedule = [s.strip() for s in schedule_entry.get().split(',') if s.strip()]
            if name and dosage and schedule:
                self.medications.add_medication(name, dosage, schedule)
                taken, total = self.medications.get_medication_stats()
                self.logger.update_medication_stats(total)
                self.update_medication_list()
                dialog.destroy()
                self.falar(f"Medicamento {name} adicionado")
        
        tk.Button(dialog, text="Salvar", command=save, bg='#27ae60', fg='white', padx=20).pack(pady=15)
    
    def mark_taken_dialog(self):
        if not self.medications.medications:
            messagebox.showinfo("Info", "Nenhum medicamento cadastrado")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Marcar como Tomado")
        dialog.geometry("300x250")
        dialog.configure(bg='#2c3e50')
        
        listbox = tk.Listbox(dialog, height=8)
        listbox.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        for med in self.medications.medications:
            listbox.insert(tk.END, med['name'])
        
        def mark():
            selection = listbox.curselection()
            if selection:
                name = self.medications.medications[selection[0]]['name']
                if self.medications.mark_as_taken(name):
                    taken, total = self.medications.get_medication_stats()
                    self.logger.update_medication_stats(total)
                    self.logger.log_event("MEDICATION", f"Medicamento tomado: {name}", "INFO")
                    self.update_medication_list()
                    self.falar(f"{name} registrado")
                    dialog.destroy()
        
        tk.Button(dialog, text="Marcar", command=mark, bg='#27ae60', fg='white').pack(pady=10)
    
    def generate_report(self):
        """Gera relatório completo com todas as estatísticas"""
        
        # Coleta estatísticas
        stats = self.logger.get_summary()
        schedule, _ = self.medications.get_today_schedule()
        
        # Prepara o relatório
        report = f"""
{'='*60}
RELATÓRIO COMPLETO - SENIOR MONITOR
{'='*60}

📅 Data e Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
⏱️  Tempo de monitoramento: Desde o início do programa

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
        
        # Lista medicamentos
        for item in schedule:
            status = "✅ TOMADO" if item['taken'] else "⏰ PENDENTE"
            report += f"      • {item['time']} - {item['name']} ({item['dosage']}) - {status}\n"
        
        # Período mais ativo
        if stats['most_active_period']:
            report += f"""
📈 ATIVIDADE:
   • Período mais ativo: {stats['most_active_period']['activity']}
   • Duração: {stats['most_active_period']['duration']:.0f} minutos
"""
        
        # Últimos picos de risco
        if stats['risk_peaks']:
            report += f"""
🚨 ÚLTIMOS PICOS DE RISCO:
"""
            for peak in stats['risk_peaks']:
                report += f"      • {peak['time'].strftime('%H:%M:%S')} - Risco: {peak['risk']:.1%}\n"
        
        # Recomendações
        report += f"""
{'='*60}
💡 RECOMENDAÇÕES PERSONALIZADAS
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
        if stats['deep_sleeps'] > 2:
            report += "   • 😴 Sono excessivo durante o dia - Verificar qualidade do sono noturno\n"
        
        if (stats['micro_sleeps'] <= 5 and stats['fall_alerts'] == 0 and 
            stats['high_risk_count'] <= 3 and stats['med_adherence'] >= 80):
            report += "   • ✅ Ótimo dia! Mantenha os cuidados e continue assim!\n"
        
        report += f"""
{'='*60}
📁 ARQUIVO GERADO: relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt
{'='*60}
"""
        
        # Salva relatório
        filename = f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Mostra preview
        messagebox.showinfo("📄 Relatório Gerado", 
                           f"Relatório salvo como:\n{filename}\n\n" +
                           f"Resumo:\n"
                           f"- Eventos de sono: {stats['micro_sleeps'] + stats['deep_sleeps']}\n"
                           f"- Alertas de queda: {stats['fall_alerts']}\n"
                           f"- Adesão medicamentos: {stats['med_adherence']:.1f}%\n\n"
                           f"Clique em OK para abrir o arquivo")
        
        # Pergunta se quer abrir
        if messagebox.askyesno("Abrir Relatório", "Deseja abrir o arquivo agora?"):
            os.startfile(filename)
    
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
                cv2.putText(frame, "MODO SIMULACAO", (200, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
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
                    messagebox.showwarning("💊 Lembrete", f"Hora de tomar {med['name']}\n{med['dosage']}")
                self.last_reminder_check = now
            
            if self.video_label:
                self.video_label.after(33, self.update_frame)
                
        except Exception as e:
            print(f"Erro: {e}")
            if self.video_label:
                self.video_label.after(100, self.update_frame)
    
    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("Senior Monitor Expert")
        self.root.geometry("1200x700")
        self.root.configure(bg='#2c3e50')
        
        self.root.bind('<F1>', lambda e: self.add_medication_dialog())
        self.root.bind('<F2>', lambda e: self.mark_taken_dialog())
        self.root.bind('<F3>', lambda e: self.generate_report())
        self.root.bind('<Escape>', lambda e: self.quit_app())
        
        main = tk.Frame(self.root, bg='#2c3e50')
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        video_frame = tk.Frame(main, bg='black', width=650, height=500)
        video_frame.pack(side='left', padx=5)
        video_frame.pack_propagate(False)
        self.video_label = tk.Label(video_frame, bg='black')
        self.video_label.pack(fill=tk.BOTH, expand=True)
        
        right = tk.Frame(main, bg='#2c3e50', width=500)
        right.pack(side='right', fill=tk.BOTH, expand=True, padx=5)
        
        dash_frame = tk.Frame(right, bg='#2c3e50', height=300)
        dash_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.dashboard = RealtimeDashboard(dash_frame)
        
        med_frame = tk.LabelFrame(right, text="💊 Medicamentos de Hoje", bg='#2c3e50', fg='white', font=('Arial', 10, 'bold'))
        med_frame.pack(fill=tk.X, pady=5)
        
        self.med_listbox = tk.Listbox(med_frame, height=4, font=('Arial', 9), bg='#34495e', fg='white')
        self.med_listbox.pack(fill=tk.X, padx=5, pady=5)
        self.update_medication_list()
        
        btn_frame = tk.Frame(right, bg='#2c3e50')
        btn_frame.pack(fill=tk.X, pady=10)
        
        buttons = [
            ("➕ Medicamento (F1)", self.add_medication_dialog),
            ("✅ Tomado (F2)", self.mark_taken_dialog),
            ("📊 Relatório (F3)", self.generate_report),
            ("❌ Sair (ESC)", self.quit_app)
        ]
        
        for text, cmd in buttons:
            tk.Button(btn_frame, text=text, command=cmd, bg='#3498db', fg='white', 
                     font=('Arial', 9), padx=8, pady=4).pack(side='left', padx=4)
        
        self.status_label = tk.Label(right, text="✅ Sistema Ativo", font=('Arial', 9), 
                                     bg='#2c3e50', fg='#2ecc71')
        self.status_label.pack(pady=5)
        
        info = "F1=Add | F2=Tomado | F3=Relatório | ESC=Sair"
        tk.Label(right, text=info, font=('Arial', 8), bg='#2c3e50', fg='gray').pack()
    
    def quit_app(self):
        # Registra período final
        self.logger.add_activity_period(self.current_activity, self.last_activity_change, datetime.now())
        
        self.running = False
        if self.cap:
            self.cap.release()
        if self.root:
            self.root.quit()
            self.root.destroy()
    
    def run(self):
        print("="*60)
        print("🚀 SENIOR MONITOR - RELATÓRIO COMPLETO")
        print("="*60)
        print("✅ Sistema inicializado")
        print("✅ Relatório agora inclui:")
        print("   - Estatísticas de sono")
        print("   - Alertas de queda")
        print("   - Adesão a medicamentos")
        print("   - Picos de risco")
        print("   - Recomendações personalizadas")
        print("="*60)
        print("\nComandos: F1=Medicamento | F2=Tomado | F3=Relatório | ESC=Sair")
        print("="*60)
        
        self.setup_gui()
        self.update_frame()
        
        if self.root:
            self.root.mainloop()

if __name__ == "__main__":
    monitor = SeniorMonitorExpert()
    monitor.run()