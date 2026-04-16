import cv2
import time
import pyttsx3
import threading
import numpy as np
from collections import deque
import math
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from PIL import Image, ImageTk
from datetime import datetime, timedelta
import os
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import speech_recognition as sr
from textblob import TextBlob
import tensorflow as tf
from tensorflow import keras
from sklearn.preprocessing import StandardScaler
import joblib
import requests
from dataclasses import dataclass
from typing import List, Dict, Any
import warnings
warnings.filterwarnings('ignore')

# ==================== DASHBOARD COM GRÁFICOS ====================
class RealtimeDashboard:
    """Dashboard com gráficos em tempo real"""
    def __init__(self, parent):
        self.parent = parent
        self.figure = Figure(figsize=(10, 6), dpi=100, facecolor='#2c3e50')
        self.canvas = FigureCanvasTkAgg(self.figure, parent)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Dados históricos
        self.sleep_history = deque(maxlen=100)
        self.posture_history = deque(maxlen=100)
        self.activity_history = deque(maxlen=100)
        self.risk_history = deque(maxlen=100)
        self.timestamps = deque(maxlen=100)
        
        # Estatísticas
        self.stats = {
            'good_posture': 0,
            'bad_posture': 0,
            'micro_sleeps': 0,
            'deep_sleeps': 0,
            'fall_risks': 0,
            'avg_risk': 0
        }
        
        self.setup_graphs()
        
    def setup_graphs(self):
        """Configura os gráficos"""
        self.figure.clear()
        
        # Gráfico 1: Sono e alertas
        self.ax1 = self.figure.add_subplot(221)
        self.ax1.set_title('Alertas de Sono (Última Hora)', color='white')
        self.ax1.set_facecolor('#34495e')
        self.ax1.tick_params(colors='white')
        
        # Gráfico 2: Qualidade da postura
        self.ax2 = self.figure.add_subplot(222)
        self.ax2.set_title('Qualidade da Postura', color='white')
        self.ax2.set_facecolor('#34495e')
        self.ax2.tick_params(colors='white')
        
        # Gráfico 3: Risco de queda
        self.ax3 = self.figure.add_subplot(223)
        self.ax3.set_title('Evolução do Risco de Queda', color='white')
        self.ax3.set_facecolor('#34495e')
        self.ax3.tick_params(colors='white')
        
        # Gráfico 4: Atividades diárias
        self.ax4 = self.figure.add_subplot(224)
        self.ax4.set_title('Atividades Diárias', color='white')
        self.ax4.set_facecolor('#34495e')
        self.ax4.tick_params(colors='white')
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def update_dashboard(self, sleep_status, posture_status, fall_risk, activity, ear_value):
        """Atualiza os gráficos em tempo real"""
        current_time = datetime.now()
        self.timestamps.append(current_time)
        
        # Atualiza histórico
        self.sleep_history.append(1 if sleep_status in ['micro_sleep', 'deep_sleep'] else 0)
        self.posture_history.append(1 if 'ruim' in posture_status.lower() else 0)
        self.risk_history.append(fall_risk)
        
        # Atualiza estatísticas
        if sleep_status == 'micro_sleep':
            self.stats['micro_sleeps'] += 1
        elif sleep_status == 'deep_sleep':
            self.stats['deep_sleeps'] += 1
        
        if 'ruim' in posture_status.lower():
            self.stats['bad_posture'] += 1
        else:
            self.stats['good_posture'] += 1
        
        if fall_risk > 0.7:
            self.stats['fall_risks'] += 1
        
        self.stats['avg_risk'] = np.mean(self.risk_history) if self.risk_history else 0
        
        # Atualiza gráficos
        self.figure.clear()
        
        # Gráfico 1: Alertas de sono
        ax1 = self.figure.add_subplot(221)
        if len(self.sleep_history) > 0:
            ax1.plot(list(self.sleep_history), color='red', linewidth=2)
        ax1.set_title('Alertas de Sono', color='white', fontsize=10)
        ax1.set_facecolor('#34495e')
        ax1.tick_params(colors='white')
        ax1.set_ylim([-0.1, 1.1])
        ax1.set_ylabel('Alerta', color='white')
        
        # Gráfico 2: Postura
        ax2 = self.figure.add_subplot(222)
        labels = ['Postura Boa', 'Postura Ruim']
        sizes = [self.stats['good_posture'], self.stats['bad_posture']]
        colors = ['#2ecc71', '#e74c3c']
        if sum(sizes) > 0:
            ax2.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', textprops={'color': 'white'})
        ax2.set_title('Qualidade da Postura', color='white', fontsize=10)
        
        # Gráfico 3: Risco de queda
        ax3 = self.figure.add_subplot(223)
        if len(self.risk_history) > 0:
            ax3.plot(list(self.risk_history), color='orange', linewidth=2)
            ax3.axhline(y=0.7, color='red', linestyle='--', label='Alto Risco')
            ax3.axhline(y=0.4, color='yellow', linestyle='--', label='Risco Moderado')
        ax3.set_title('Evolução do Risco de Queda', color='white', fontsize=10)
        ax3.set_facecolor('#34495e')
        ax3.tick_params(colors='white')
        ax3.set_ylim([0, 1])
        ax3.set_ylabel('Risco', color='white')
        ax3.legend(loc='upper right', facecolor='#34495e', labelcolor='white')
        
        # Gráfico 4: Atividades
        ax4 = self.figure.add_subplot(224)
        activities = ['Dormindo', 'Descansando', 'Ativo', 'Exercício']
        activity_counts = [0, 0, 0, 0]
        for act in self.activity_history:
            if act == 'dormindo':
                activity_counts[0] += 1
            elif act == 'descansando':
                activity_counts[1] += 1
            elif act == 'ativo':
                activity_counts[2] += 1
            elif act == 'exercicio':
                activity_counts[3] += 1
        
        bars = ax4.bar(activities, activity_counts, color=['#3498db', '#95a5a6', '#2ecc71', '#e67e22'])
        ax4.set_title('Atividades Diárias', color='white', fontsize=10)
        ax4.set_facecolor('#34495e')
        ax4.tick_params(colors='white', rotation=45)
        ax4.set_ylabel('Duração (minutos)', color='white')
        
        self.figure.tight_layout()
        self.canvas.draw()

# ==================== ANÁLISE DE SENTIMENTOS E ESTRESSE ====================
class VoiceSentimentAnalyzer:
    """Análise de sentimentos e estresse através da voz"""
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.emotion_history = deque(maxlen=50)
        self.stress_levels = deque(maxlen=50)
        self.last_analysis = 0
        self.analysis_interval = 300  # 5 minutos
        
    def analyze_speech(self, audio_file=None):
        """Analisa sentimento da voz"""
        try:
            if audio_file:
                with sr.AudioFile(audio_file) as source:
                    audio = self.recognizer.record(source)
            else:
                # Usa microfone
                with sr.Microphone() as source:
                    print("🎤 Ouvindo...")
                    audio = self.recognizer.listen(source, timeout=5)
            
            # Reconhece fala
            text = self.recognizer.recognize_google(audio, language='pt-BR')
            
            # Análise de sentimento
            blob = TextBlob(text)
            sentiment = blob.sentiment.polarity  # -1 (negativo) a +1 (positivo)
            subjectivity = blob.sentiment.subjectivity
            
            # Detecta estresse baseado no tom
            stress_level = self.calculate_stress_level(sentiment, subjectivity, text)
            
            # Classifica emoção
            emotion = self.classify_emotion(sentiment, stress_level)
            
            # Registra histórico
            self.emotion_history.append(emotion)
            self.stress_levels.append(stress_level)
            
            return {
                'text': text,
                'sentiment': sentiment,
                'subjectivity': subjectivity,
                'stress_level': stress_level,
                'emotion': emotion,
                'timestamp': datetime.now()
            }
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except Exception as e:
            print(f"Erro na análise de voz: {e}")
            return None
    
    def calculate_stress_level(self, sentiment, subjectivity, text):
        """Calcula nível de estresse (0-1)"""
        stress = 0
        
        # Sentimento negativo aumenta estresse
        if sentiment < -0.3:
            stress += 0.5
        elif sentiment < 0:
            stress += 0.3
        
        # Palavras de estresse
        stress_words = ['estresse', 'ansiedade', 'preocupado', 'cansado', 'dor', 'problema']
        for word in stress_words:
            if word in text.lower():
                stress += 0.1
        
        # Subjetividade indica emoção
        if subjectivity > 0.7:
            stress += 0.2
        
        return min(stress, 1.0)
    
    def classify_emotion(self, sentiment, stress_level):
        """Classifica emoção baseada no sentimento e estresse"""
        if sentiment > 0.5:
            return 'feliz'
        elif sentiment > 0:
            return 'neutro'
        elif sentiment > -0.3:
            return 'triste'
        else:
            if stress_level > 0.7:
                return 'estressado'
            return 'irritado'
    
    def get_emotional_state(self):
        """Retorna estado emocional atual"""
        if not self.emotion_history:
            return "Indisponível", 0
        
        recent_emotions = list(self.emotion_history)[-10:]
        avg_stress = np.mean(self.stress_levels) if self.stress_levels else 0
        
        # Determina emoção predominante
        from collections import Counter
        common_emotion = Counter(recent_emotions).most_common(1)[0][0]
        
        return common_emotion, avg_stress

# ==================== RECONHECIMENTO DE ATIVIDADES DIÁRIAS ====================
class ActivityRecognizer:
    """Reconhecimento de atividades diárias"""
    def __init__(self):
        self.current_activity = "ativo"
        self.activity_start_time = time.time()
        self.activity_history = deque(maxlen=100)
        
        # Parâmetros para cada atividade
        self.activities_params = {
            'dormindo': {
                'eye_closed_threshold': 0.2,
                'min_duration': 3600,  # 1 hora
                'movement_max': 20
            },
            'descansando': {
                'eye_closed_threshold': 0.2,
                'min_duration': 300,  # 5 minutos
                'movement_max': 50
            },
            'comendo': {
                'movement_range': [50, 150],
                'min_duration': 300,  # 5 minutos
                'head_stable': False
            },
            'lendo': {
                'head_stable': True,
                'min_duration': 600,  # 10 minutos
                'movement_max': 30
            },
            'exercicio': {
                'movement_range': [150, 500],
                'min_duration': 300,  # 5 minutos
                'breathing_heavy': True
            },
            'assistindo_tv': {
                'head_stable': True,
                'eye_open': True,
                'movement_max': 40
            },
            'ativo': {
                'movement_range': [20, 150],
                'default': True
            }
        }
    
    def recognize_activity(self, features):
        """Reconhece atividade atual baseada nas features"""
        current_time = time.time()
        duration = current_time - self.activity_start_time
        
        # Extrai features
        movement = features.get('movement', 0)
        eye_state = features.get('eye_state', 1.0)  # 1 = aberto, 0 = fechado
        head_stable = features.get('head_stable', True)
        hour = datetime.now().hour
        
        # Verifica cada atividade
        detected_activity = self.current_activity
        
        # Dormindo (prioridade máxima)
        if eye_state < self.activities_params['dormindo']['eye_closed_threshold']:
            if duration > self.activities_params['dormindo']['min_duration'] or hour < 6 or hour > 22:
                detected_activity = 'dormindo'
        
        # Descansando
        elif eye_state < self.activities_params['descansando']['eye_closed_threshold']:
            if duration > self.activities_params['descansando']['min_duration']:
                detected_activity = 'descansando'
        
        # Exercício
        elif movement > self.activities_params['exercicio']['movement_range'][0]:
            detected_activity = 'exercicio'
        
        # Comendo
        elif self.activities_params['comendo']['movement_range'][0] <= movement <= \
             self.activities_params['comendo']['movement_range'][1]:
            detected_activity = 'comendo'
        
        # Lendo
        elif head_stable and movement < self.activities_params['lendo']['movement_max']:
            if duration > self.activities_params['lendo']['min_duration']:
                detected_activity = 'lendo'
        
        # Assistindo TV
        elif head_stable and eye_state > 0.8:
            detected_activity = 'assistindo_tv'
        
        # Padrão: ativo
        else:
            detected_activity = 'ativo'
        
        # Muda atividade se necessário
        if detected_activity != self.current_activity:
            self.activity_start_time = current_time
            self.activity_history.append({
                'activity': self.current_activity,
                'duration': duration,
                'start_time': datetime.now() - timedelta(seconds=duration)
            })
            self.current_activity = detected_activity
        
        return detected_activity, duration
    
    def get_activity_summary(self):
        """Retorna resumo das atividades do dia"""
        summary = {}
        for activity in self.activity_history:
            name = activity['activity']
            if name not in summary:
                summary[name] = 0
            summary[name] += activity['duration']
        
        return summary

# ==================== CALENDÁRIO DE MEDICAMENTOS ====================
@dataclass
class Medication:
    name: str
    dosage: str
    schedule: List[str]  # Lista de horários "08:00", "20:00"
    start_date: datetime
    end_date: datetime = None
    notes: str = ""
    last_taken: datetime = None

class MedicationCalendar:
    """Sistema de lembretes de medicamentos"""
    def __init__(self):
        self.medications: List[Medication] = []
        self.reminder_history = []
        self.medications_file = "medications.json"
        self.load_medications()
        
        # Thread para verificar lembretes
        self.running = True
        self.reminder_thread = threading.Thread(target=self.check_reminders_loop, daemon=True)
        self.reminder_thread.start()
    
    def add_medication(self, name, dosage, schedule, notes=""):
        """Adiciona novo medicamento"""
        med = Medication(
            name=name,
            dosage=dosage,
            schedule=schedule,
            start_date=datetime.now(),
            notes=notes
        )
        self.medications.append(med)
        self.save_medications()
        return med
    
    def remove_medication(self, index):
        """Remove medicamento"""
        if 0 <= index < len(self.medications):
            self.medications.pop(index)
            self.save_medications()
    
    def save_medications(self):
        """Salva medicamentos em arquivo"""
        data = []
        for med in self.medications:
            data.append({
                'name': med.name,
                'dosage': med.dosage,
                'schedule': med.schedule,
                'start_date': med.start_date.isoformat(),
                'end_date': med.end_date.isoformat() if med.end_date else None,
                'notes': med.notes,
                'last_taken': med.last_taken.isoformat() if med.last_taken else None
            })
        
        with open(self.medications_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_medications(self):
        """Carrega medicamentos do arquivo"""
        if os.path.exists(self.medications_file):
            with open(self.medications_file, 'r') as f:
                data = json.load(f)
                for item in data:
                    med = Medication(
                        name=item['name'],
                        dosage=item['dosage'],
                        schedule=item['schedule'],
                        start_date=datetime.fromisoformat(item['start_date']),
                        end_date=datetime.fromisoformat(item['end_date']) if item['end_date'] else None,
                        notes=item.get('notes', ''),
                        last_taken=datetime.fromisoformat(item['last_taken']) if item.get('last_taken') else None
                    )
                    self.medications.append(med)
    
    def check_reminders(self):
        """Verifica lembretes pendentes"""
        current_time = datetime.now()
        reminders = []
        
        for med in self.medications:
            # Verifica se ainda está no período
            if med.end_date and current_time > med.end_date:
                continue
            
            # Verifica cada horário
            for schedule_time in med.schedule:
                schedule_hour, schedule_minute = map(int, schedule_time.split(':'))
                schedule_datetime = current_time.replace(hour=schedule_hour, minute=schedule_minute, second=0)
                
                # Verifica se é hora do remédio (janela de 5 minutos)
                time_diff = abs((current_time - schedule_datetime).total_seconds())
                if time_diff < 300:  # 5 minutos
                    # Verifica se já foi tomado hoje
                    if med.last_taken and med.last_taken.date() == current_time.date():
                        continue
                    
                    reminders.append({
                        'medication': med,
                        'scheduled_time': schedule_time,
                        'time_diff': time_diff
                    })
        
        return reminders
    
    def check_reminders_loop(self):
        """Loop para verificar lembretes"""
        while self.running:
            reminders = self.check_reminders()
            if reminders:
                for reminder in reminders:
                    self.reminder_history.append({
                        'timestamp': datetime.now(),
                        'medication': reminder['medication'].name,
                        'scheduled_time': reminder['scheduled_time']
                    })
            time.sleep(30)  # Verifica a cada 30 segundos
    
    def mark_as_taken(self, medication_name):
        """Marca medicamento como tomado"""
        for med in self.medications:
            if med.name == medication_name:
                med.last_taken = datetime.now()
                self.save_medications()
                return True
        return False
    
    def get_today_schedule(self):
        """Retorna agenda de hoje"""
        today = datetime.now().date()
        schedule = []
        
        for med in self.medications:
            for time_str in med.schedule:
                taken = False
                if med.last_taken and med.last_taken.date() == today:
                    # Verifica se já foi tomado neste horário
                    hour, minute = map(int, time_str.split(':'))
                    taken_time = med.last_taken.replace(second=0, microsecond=0)
                    scheduled_time = med.last_taken.replace(hour=hour, minute=minute, second=0)
                    taken = abs((taken_time - scheduled_time).total_seconds()) < 3600
                
                schedule.append({
                    'medication': med,
                    'time': time_str,
                    'taken': taken
                })
        
        return sorted(schedule, key=lambda x: x['time'])

# ==================== MACHINE LEARNING AVANÇADO ====================
class AdvancedMLPredictor:
    """Predição avançada usando LSTM"""
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.model_file = "advanced_fall_model.h5"
        self.scaler_file = "advanced_scaler.pkl"
        self.sequence_length = 30
        self.n_features = 8
        
        # Carrega ou cria modelo
        self.load_or_create_model()
        
        # Buffer para sequências
        self.feature_buffer = deque(maxlen=self.sequence_length)
        self.predictions_history = deque(maxlen=100)
    
    def create_model(self):
        """Cria modelo LSTM"""
        model = keras.Sequential([
            keras.layers.LSTM(64, input_shape=(self.sequence_length, self.n_features), return_sequences=True),
            keras.layers.Dropout(0.2),
            keras.layers.LSTM(32, return_sequences=False),
            keras.layers.Dropout(0.2),
            keras.layers.Dense(16, activation='relu'),
            keras.layers.Dense(1, activation='sigmoid')
        ])
        
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy', keras.metrics.AUC()]
        )
        
        return model
    
    def load_or_create_model(self):
        """Carrega modelo existente ou cria novo"""
        if os.path.exists(self.model_file) and os.path.exists(self.scaler_file):
            self.model = keras.models.load_model(self.model_file)
            self.scaler = joblib.load(self.scaler_file)
            print("✅ Modelo LSTM carregado")
        else:
            self.model = self.create_model()
            # Treina com dados sintéticos
            self.train_with_synthetic_data()
            print("✅ Novo modelo LSTM criado e treinado")
    
    def train_with_synthetic_data(self):
        """Treina modelo com dados sintéticos"""
        print("🔄 Treinando modelo LSTM com dados sintéticos...")
        
        # Gera dados sintéticos
        X_train = []
        y_train = []
        
        for _ in range(1000):
            # Sequência normal
            normal_seq = np.random.randn(self.sequence_length, self.n_features) * 0.1
            X_train.append(normal_seq)
            y_train.append(0)
            
            # Sequência de risco
            risk_seq = np.random.randn(self.sequence_length, self.n_features) * 0.3
            risk_seq[-10:, 0] += 2.0  # Aumenta movimento
            risk_seq[-5:, 1] -= 1.0   # Queda na postura
            X_train.append(risk_seq)
            y_train.append(1)
        
        X_train = np.array(X_train)
        y_train = np.array(y_train)
        
        # Normaliza
        X_train_reshaped = X_train.reshape(-1, self.n_features)
        self.scaler.fit(X_train_reshaped)
        X_train_normalized = np.array([self.scaler.transform(seq) for seq in X_train])
        
        # Treina
        self.model.fit(
            X_train_normalized, y_train,
            epochs=20,
            batch_size=32,
            validation_split=0.2,
            verbose=0
        )
        
        # Salva modelo
        self.model.save(self.model_file)
        joblib.dump(self.scaler, self.scaler_file)
        print("✅ Modelo treinado e salvo")
    
    def extract_features(self, movement_speed, posture_quality, ear_value, 
                        activity_type, stress_level, hour, movement_variance,
                        head_stability):
        """Extrai features para predição"""
        # Mapeia atividade para número
        activity_map = {
            'dormindo': 0, 'descansando': 1, 'ativo': 2,
            'exercicio': 3, 'comendo': 4, 'lendo': 5, 'assistindo_tv': 6
        }
        activity_code = activity_map.get(activity_type, 2)
        
        features = np.array([
            movement_speed,
            posture_quality,
            ear_value,
            activity_code / 6.0,  # Normaliza
            stress_level,
            hour / 23.0,  # Normaliza
            movement_variance,
            head_stability
        ])
        
        return features
    
    def predict_fall_risk_advanced(self, features_dict):
        """Prediz risco de queda usando LSTM"""
        # Extrai features
        features = self.extract_features(
            features_dict.get('movement_speed', 0),
            features_dict.get('posture_quality', 1),
            features_dict.get('ear_value', 1),
            features_dict.get('activity_type', 'ativo'),
            features_dict.get('stress_level', 0),
            features_dict.get('hour', datetime.now().hour),
            features_dict.get('movement_variance', 0),
            features_dict.get('head_stability', 1)
        )
        
        # Adiciona ao buffer
        self.feature_buffer.append(features)
        
        # Prediz se tem sequência completa
        if len(self.feature_buffer) == self.sequence_length:
            sequence = np.array(list(self.feature_buffer))
            sequence_normalized = self.scaler.transform(sequence)
            sequence_normalized = sequence_normalized.reshape(1, self.sequence_length, self.n_features)
            
            risk_score = float(self.model.predict(sequence_normalized, verbose=0)[0][0])
            self.predictions_history.append(risk_score)
            
            # Suaviza predição com média móvel
            if len(self.predictions_history) > 5:
                risk_score = np.mean(list(self.predictions_history)[-5:])
            
            return risk_score
        
        return 0

# ==================== INTERFACE PRINCIPAL ====================
class SeniorMonitorExpert:
    def __init__(self):
        # Inicializa módulos
        self.dashboard = None
        self.voice_analyzer = VoiceSentimentAnalyzer()
        self.activity_recognizer = ActivityRecognizer()
        self.medication_calendar = MedicationCalendar()
        self.ml_predictor = AdvancedMLPredictor()
        
        # Configurações de Voz
        self.engine = None
        self._init_engine()
        
        # Face cascade
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        
        # Configuração da Câmera
        self.cap = None
        self._init_camera()
        
        # Lógica de Tempo
        self.olhos_fechados_start = None
        self.last_alert_time = 0
        self.last_voice_analysis = 0
        self.movement_history = deque(maxlen=30)
        self.prev_face_center = None
        
        # Interface
        self.root = None
        self.video_label = None
        self.status_label = None
        self.medication_frame = None
        self.running = True
        
        print("✅ Sistema avançado inicializado!")
    
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
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5, minSize=(100, 100))
        
        status = "Ativo"
        cor = (0, 255, 0)
        ear_value = 1.0
        movement_speed = 0
        
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            
            # Detecta olhos
            roi_gray = gray[y:y+h, x:x+w]
            eyes = self.eye_cascade.detectMultiScale(roi_gray, 1.1, 5, minSize=(20, 20))
            
            # Calcula EAR simulado
            if len(eyes) < 2:
                ear_value = 0.1
            else:
                ear_value = 0.3
            
            # Desenha olhos
            for (ex, ey, ew, eh) in eyes:
                cv2.rectangle(frame, (x+ex, y+ey), (x+ex+ew, y+ey+eh), (0, 255, 0), 1)
            
            # Detecção de sono
            if ear_value < 0.2:
                if self.olhos_fechados_start is None:
                    self.olhos_fechados_start = time.time()
                
                duracao = time.time() - self.olhos_fechados_start
                
                if 0.5 <= duracao < 1.5:
                    status = "⚠️ Micro-sono!"
                    cor = (0, 165, 255)
                elif duracao >= 1.5:
                    status = "😴 DORMINDO!"
                    cor = (0, 0, 255)
                    if time.time() - self.last_alert_time > 5:
                        self.falar("Acorda agora!")
                        self.last_alert_time = time.time()
            else:
                self.olhos_fechados_start = None
            
            # Calcula movimento
            if self.prev_face_center:
                movement = np.linalg.norm(np.array([x+w//2, y+h//2]) - np.array(self.prev_face_center))
                movement_speed = movement
                self.movement_history.append(movement)
            
            self.prev_face_center = (x+w//2, y+h//2)
        
        # Reconhecimento de atividade
        movement_avg = np.mean(self.movement_history) if self.movement_history else 0
        features = {
            'movement': movement_avg,
            'eye_state': ear_value,
            'head_stable': movement_avg < 30
        }
        activity, activity_duration = self.activity_recognizer.recognize_activity(features)
        
        # Análise de voz periódica
        current_time = time.time()
        if current_time - self.last_voice_analysis > 300:  # A cada 5 minutos
            voice_result = self.voice_analyzer.analyze_speech()
            if voice_result:
                emotion, stress = self.voice_analyzer.get_emotional_state()
                if stress > 0.7:
                    self.falar("Percebo que você está estressado. Respire fundo e relaxe.")
            self.last_voice_analysis = current_time
        
        # Predição ML avançada
        movement_variance = np.var(self.movement_history) if len(self.movement_history) > 1 else 0
        emotion, stress_level = self.voice_analyzer.get_emotional_state()
        
        ml_features = {
            'movement_speed': movement_avg,
            'posture_quality': 1 if 'ruim' not in status else 0,
            'ear_value': ear_value,
            'activity_type': activity,
            'stress_level': stress_level,
            'hour': datetime.now().hour,
            'movement_variance': movement_variance,
            'head_stability': 1 if movement_avg < 30 else 0
        }
        
        fall_risk = self.ml_predictor.predict_fall_risk_advanced(ml_features)
        
        # Alertas de risco
        if fall_risk > 0.7:
            cv2.putText(frame, "🔴 ALTO RISCO DE QUEDA!", (10, 150), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            if time.time() - self.last_alert_time > 30:
                self.falar("Atenção! Alto risco de queda detectado!")
                self.last_alert_time = time.time()
        
        # Atualiza dashboard
        if self.dashboard:
            self.dashboard.update_dashboard(status, status, fall_risk, activity, ear_value)
        
        # Desenha informações na tela
        cv2.putText(frame, f"Status: {status}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, cor, 2)
        cv2.putText(frame, f"Atividade: {activity}", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)
        cv2.putText(frame, f"Risco Queda: {fall_risk:.2%}", (10, 90), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)
        cv2.putText(frame, f"Estresse: {stress_level:.1%}", (10, 120), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 165, 0), 1)
        
        return frame
    
    def update_medication_display(self):
        """Atualiza display de medicamentos"""
        if self.medication_frame:
            # Limpa frame
            for widget in self.medication_frame.winfo_children():
                widget.destroy()
            
            # Título
            tk.Label(self.medication_frame, text="💊 Medicamentos de Hoje", 
                    font=('Arial', 12, 'bold'), bg='#2c3e50', fg='white').pack(pady=5)
            
            # Lista de medicamentos
            schedule = self.medication_calendar.get_today_schedule()
            
            if not schedule:
                tk.Label(self.medication_frame, text="Nenhum medicamento agendado", 
                        bg='#2c3e50', fg='white').pack()
            else:
                for item in schedule:
                    med = item['medication']
                    time_str = item['time']
                    taken = item['taken']
                    
                    frame = tk.Frame(self.medication_frame, bg='#34495e')
                    frame.pack(fill='x', padx=5, pady=2)
                    
                    status = "✅" if taken else "⏰"
                    color = 'green' if taken else 'orange'
                    
                    tk.Label(frame, text=f"{status} {time_str} - {med.name}", 
                            font=('Arial', 10), bg='#34495e', fg=color).pack(side='left', padx=5)
                    
                    if not taken:
                        tk.Button(frame, text="Tomado", 
                                 command=lambda m=med.name: self.mark_medication_taken(m),
                                 bg='green', fg='white', font=('Arial', 8)).pack(side='right', padx=5)
    
    def mark_medication_taken(self, medication_name):
        """Marca medicamento como tomado"""
        if self.medication_calendar.mark_as_taken(medication_name):
            self.falar(f"Medicamento {medication_name} registrado")
            self.update_medication_display()
    
    def add_medication_dialog(self):
        """Diálogo para adicionar medicamento"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Adicionar Medicamento")
        dialog.geometry("400x400")
        dialog.configure(bg='#2c3e50')
        
        tk.Label(dialog, text="Nome do Medicamento:", bg='#2c3e50', fg='white').pack(pady=5)
        name_entry = tk.Entry(dialog, width=30)
        name_entry.pack(pady=5)
        
        tk.Label(dialog, text="Dosagem:", bg='#2c3e50', fg='white').pack(pady=5)
        dosage_entry = tk.Entry(dialog, width=30)
        dosage_entry.pack(pady=5)
        
        tk.Label(dialog, text="Horários (separados por vírgula):", bg='#2c3e50', fg='white').pack(pady=5)
        tk.Label(dialog, text="Ex: 08:00, 14:00, 20:00", bg='#2c3e50', fg='gray').pack()
        schedule_entry = tk.Entry(dialog, width=30)
        schedule_entry.pack(pady=5)
        
        tk.Label(dialog, text="Observações:", bg='#2c3e50', fg='white').pack(pady=5)
        notes_text = tk.Text(dialog, height=5, width=40)
        notes_text.pack(pady=5)
        
        def save_medication():
            name = name_entry.get()
            dosage = dosage_entry.get()
            schedule = [s.strip() for s in schedule_entry.get().split(',')]
            notes = notes_text.get("1.0", tk.END).strip()
            
            if name and dosage and schedule:
                self.medication_calendar.add_medication(name, dosage, schedule, notes)
                self.update_medication_display()
                dialog.destroy()
                self.falar(f"Medicamento {name} adicionado")
            else:
                messagebox.showwarning("Campos incompletos", "Preencha todos os campos obrigatórios")
        
        tk.Button(dialog, text="Salvar", command=save_medication, 
                 bg='green', fg='white', font=('Arial', 10, 'bold')).pack(pady=10)
    
    def update_frame(self):
        """Atualiza frame na interface"""
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
            
            frame = self.process_frame(frame)
            
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img = img.resize((640, 480), Image.Resampling.LANCZOS)
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
        """Configura interface gráfica"""
        self.root = tk.Tk()
        self.root.title("Senior Monitor Expert - Sistema Avançado com IA")
        self.root.geometry("1400x800")
        self.root.configure(bg='#2c3e50')
        
        # Frame principal com grid
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Esquerda: Vídeo
        left_frame = tk.Frame(main_frame, bg='black')
        left_frame.pack(side='left', fill=tk.BOTH, expand=True)
        
        self.video_label = tk.Label(left_frame, bg='black')
        self.video_label.pack()
        
        # Direita: Dashboard e Medicamentos
        right_frame = tk.Frame(main_frame, bg='#2c3e50', width=600)
        right_frame.pack(side='right', fill=tk.BOTH, padx=10)
        right_frame.pack_propagate(False)
        
        # Dashboard
        dashboard_frame = tk.Frame(right_frame, bg='#2c3e50')
        dashboard_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.dashboard = RealtimeDashboard(dashboard_frame)
        
        # Medicamentos
        self.medication_frame = tk.Frame(right_frame, bg='#2c3e50', height=300)
        self.medication_frame.pack(fill=tk.X, pady=10)
        self.medication_frame.pack_propagate(False)
        
        self.update_medication_display()
        
        # Botões de controle
        control_frame = tk.Frame(right_frame, bg='#2c3e50')
        control_frame.pack(fill=tk.X, pady=10)
        
        tk.Button(control_frame, text="➕ Adicionar Medicamento", 
                 command=self.add_medication_dialog,
                 bg='#3498db', fg='white', font=('Arial', 10, 'bold')).pack(side='left', padx=5)
        
        tk.Button(control_frame, text="🎤 Testar Microfone", 
                 command=self.test_microphone,
                 bg='#e67e22', fg='white', font=('Arial', 10, 'bold')).pack(side='left', padx=5)
        
        tk.Button(control_frame, text="📊 Gerar Relatório", 
                 command=self.generate_complete_report,
                 bg='#27ae60', fg='white', font=('Arial', 10, 'bold')).pack(side='left', padx=5)
        
        tk.Button(control_frame, text="❌ Sair", 
                 command=self.quit_app,
                 bg='#e74c3c', fg='white', font=('Arial', 10, 'bold')).pack(side='left', padx=5)
        
        # Status
        self.status_label = tk.Label(right_frame, text="Sistema Ativo", 
                                     font=('Arial', 10), bg='#2c3e50', fg='green')
        self.status_label.pack(pady=5)
    
    def test_microphone(self):
        """Testa o microfone"""
        def test():
            result = self.voice_analyzer.analyze_speech()
            if result:
                messagebox.showinfo("Análise de Voz", 
                                   f"Texto: {result['text']}\n"
                                   f"Sentimento: {result['sentiment']:.2f}\n"
                                   f"Estresse: {result['stress_level']:.1%}\n"
                                   f"Emoção: {result['emotion']}")
            else:
                messagebox.showwarning("Erro", "Não foi possível capturar áudio")
        
        threading.Thread(target=test, daemon=True).start()
    
    def generate_complete_report(self):
        """Gera relatório completo"""
        activity_summary = self.activity_recognizer.get_activity_summary()
        emotion, stress = self.voice_analyzer.get_emotional_state()
        
        report = f"""
        RELATÓRIO COMPLETO
        =================
        Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}
        
        RESUMO DE ATIVIDADES:
        {json.dumps(activity_summary, indent=2)}
        
        ESTADO EMOCIONAL:
        Emoção predominante: {emotion}
        Nível de estresse: {stress:.1%}
        
        MEDICAMENTOS:
        """
        
        for med in self.medication_calendar.medications:
            report += f"\n- {med.name}: {med.dosage} - Horários: {', '.join(med.schedule)}"
        
        # Salva relatório
        filename = f"relatorio_completo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        messagebox.showinfo("Relatório Gerado", f"Relatório salvo como:\n{filename}")
    
    def quit_app(self):
        """Encerra aplicação"""
        print("🛑 Encerrando sistema...")
        self.running = False
        self.medication_calendar.running = False
        if self.cap:
            self.cap.release()
        if self.root:
            self.root.quit()
            self.root.destroy()
    
    def run(self):
        """Executa o sistema"""
        print("="*60)
        print("🚀 SENIOR MONITOR EXPERT - SISTEMA AVANÇADO COM IA")
        print("="*60)
        print("Recursos avançados ativados:")
        print("✅ Dashboard com gráficos em tempo real")
        print("✅ Análise de sentimentos e estresse por voz")
        print("✅ Reconhecimento de atividades diárias")
        print("✅ Calendário de medicamentos com lembretes")
        print("✅ Machine Learning avançado (LSTM)")
        print("="*60)
        
        self.setup_gui()
        self.update_frame()
        
        # Inicia verificação de lembretes de voz
        def check_voice_reminders():
            while self.running:
                reminders = self.medication_calendar.check_reminders()
                for reminder in reminders:
                    med = reminder['medication']
                    self.falar(f"Hora de tomar {med.dosage} de {med.name}")
                    messagebox.showwarning("Lembrete de Medicamento", 
                                          f"Hora de tomar {med.name}\nDosagem: {med.dosage}")
                time.sleep(60)
        
        reminder_thread = threading.Thread(target=check_voice_reminders, daemon=True)
        reminder_thread.start()
        
        if self.root:
            self.root.mainloop()

if __name__ == "__main__":
    monitor = SeniorMonitorExpert()
    monitor.run()