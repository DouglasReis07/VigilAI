import cv2
import time
import pyttsx3
import threading
import numpy as np
from collections import deque
import math

class SeniorMonitorExpert:
    def __init__(self):
        # 1. Configurações de Voz Personalizada (CORRIGIDO)
        self.engine = None
        self._init_engine()
        
        # 2. Visão Computacional (Haar Cascades)
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye_tree_eyeglasses.xml')
        
        # 3. Lógica de Tempo e Sinais
        self.olhos_fechados_start = None
        self.last_alert_time = 0
        self.last_fall_alert_time = 0  # Para queda
        self.buffer_presenca = deque(maxlen=15)
        
        # 4. Processamento de Imagem
        self.clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        
        # 5. Configuração da Câmera com Tratamento de Falhas
        self.cap = None
        self._init_camera()
        
        # 6. Detecção de Queda
        self.prev_face_center = None
        self.fall_detected = False
        self.fall_confirm_frames = 0
        self.FALL_THRESHOLD = 150  # Movimento brusco em pixels
        self.FALL_CONFIRMATION_FRAMES = 3  # Frames para confirmar queda
        
        # 7. Modo Noturno
        self.last_brightness_check = 0
        self.night_mode = False
        self.BRIGHTNESS_THRESHOLD = 60
        self.NIGHT_MODE_COOLDOWN = 30  # segundos entre mudanças de modo
        
        # 8. Queue para mensagens de voz (evita sobrecarga)
        self.voice_queue = deque(maxlen=10)
        self.voice_thread_running = True
        self._start_voice_worker()
        
    def _init_engine(self):
        """Inicializa engine de voz de forma segura"""
        try:
            self.engine = pyttsx3.init()
            self._configurar_voz(sexo='feminino')
            self.engine.setProperty('rate', 175)
        except Exception as e:
            print(f"Erro ao inicializar engine de voz: {e}")
            self.engine = None
    
    def _init_camera(self):
        """Inicializa câmera com tratamento de falhas e fallback"""
        camera_indices = [0, 1, 2]  # Tenta diferentes índices
        
        for index in camera_indices:
            print(f"Tentando câmera {index}...")
            cap = cv2.VideoCapture(index)
            if cap.isOpened():
                # Testa se realmente captura frames
                ret, frame = cap.read()
                if ret and frame is not None:
                    self.cap = cap
                    print(f"✅ Câmera {index} inicializada com sucesso!")
                    return
                else:
                    cap.release()
            else:
                print(f"❌ Câmera {index} não disponível")
        
        # Se nenhuma câmera funcionar, cria uma câmera virtual de fallback
        print("⚠️ Nenhuma câmera encontrada! Usando modo de simulação.")
        self.cap = None
    
    def _start_voice_worker(self):
        """Worker thread para processar fila de mensagens de voz"""
        def voice_worker():
            while self.voice_thread_running:
                if self.voice_queue and self.engine:
                    try:
                        message = self.voice_queue.popleft()
                        # Evita mensagens duplicadas muito próximas
                        if hasattr(self, '_last_message') and time.time() - self._last_message_time < 2:
                            if self._last_message == message:
                                continue
                        
                        self.engine.say(message)
                        self.engine.runAndWait()
                        self._last_message = message
                        self._last_message_time = time.time()
                    except Exception as e:
                        print(f"Erro na reprodução de voz: {e}")
                time.sleep(0.1)
        
        self.voice_thread = threading.Thread(target=voice_worker, daemon=True)
        self.voice_thread.start()
    
    def _configurar_voz(self, sexo='feminino'):
        """Configura voz em português"""
        if not self.engine:
            return
            
        voices = self.engine.getProperty('voices')
        self.engine.setProperty('rate', 175)
        
        for voice in voices:
            if "brazil" in voice.name.lower() or "portuguese" in voice.name.lower():
                if sexo == 'feminino' and ("maria" in voice.name.lower() or "female" in voice.name.lower()):
                    self.engine.setProperty('voice', voice.id)
                    break
                if sexo == 'masculino' and ("daniel" in voice.name.lower() or "male" in voice.name.lower()):
                    self.engine.setProperty('voice', voice.id)
                    break
                # Fallback para primeira voz em português
                self.engine.setProperty('voice', voice.id)
    
    def falar(self, texto):
        """Adiciona mensagem à fila de voz (thread-safe)"""
        if self.engine:
            self.voice_queue.append(texto)
    
    def enhance_low_light(self, frame):
        """Melhoria de imagem para baixa luminosidade (simula IR)"""
        # Converte para LAB
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Aplica CLAHE no canal L
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        l = clahe.apply(l)
        
        # Aumenta contraste nas cores
        a = cv2.addWeighted(a, 1.2, a, 0, 0)
        b = cv2.addWeighted(b, 1.2, b, 0, 0)
        
        # Merge e conversão de volta
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        # Redução de ruído
        enhanced = cv2.fastNlMeansDenoisingColored(enhanced, None, 5, 5, 7, 21)
        
        # Aumenta brilho geral
        enhanced = cv2.convertScaleAbs(enhanced, alpha=1.1, beta=20)
        
        # Adiciona efeito "verde" característico de visão noturna
        if self.night_mode:
            enhanced[:,:,1] = np.clip(enhanced[:,:,1] * 1.2, 0, 255)  # Aumenta verde
        
        return enhanced
    
    def detect_fall(self, face_center, frame_shape):
        """Detecta quedas baseado em movimento brusco e posição"""
        if face_center is None:
            # Reset se perdeu o rosto
            if self.prev_face_center is not None:
                self.fall_confirm_frames += 1
                if self.fall_confirm_frames >= self.FALL_CONFIRMATION_FRAMES:
                    # Perdeu o rosto por muitos frames - pode ser queda
                    current_time = time.time()
                    if current_time - self.last_fall_alert_time > 10:  # Evita spam
                        return True
            return False
        
        self.fall_confirm_frames = 0
        
        if self.prev_face_center is not None:
            # Calcula movimento
            movement = np.linalg.norm(face_center - self.prev_face_center)
            
            # Verifica se está muito próximo da borda inferior (pode estar caído)
            height = frame_shape[0]
            is_near_ground = face_center[1] > height * 0.8
            
            # Movimento brusco + próximo ao chão = possível queda
            if movement > self.FALL_THRESHOLD and is_near_ground:
                current_time = time.time()
                if current_time - self.last_fall_alert_time > 10:  # Alerta a cada 10 segundos no máximo
                    self.last_fall_alert_time = current_time
                    return True
            
            # Movimento extremamente brusco (queda rápida)
            if movement > self.FALL_THRESHOLD * 1.5:
                current_time = time.time()
                if current_time - self.last_fall_alert_time > 10:
                    self.last_fall_alert_time = current_time
                    return True
        
        self.prev_face_center = face_center
        return False
    
    def check_night_mode(self, frame):
        """Verifica condições de luz e ativa/desativa modo noturno"""
        current_time = time.time()
        
        # Verifica a cada N segundos
        if current_time - self.last_brightness_check > self.NIGHT_MODE_COOLDOWN:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            brightness = np.mean(gray)
            
            new_mode = brightness < self.BRIGHTNESS_THRESHOLD
            
            if new_mode != self.night_mode:
                self.night_mode = new_mode
                if self.night_mode:
                    self.falar("Ativando modo de visão noturna")
                    print("🌙 Modo noturno ativado")
                else:
                    print("☀️ Modo normal ativado")
            
            self.last_brightness_check = current_time
        
        return self.night_mode
    
    def process_image(self, frame):
        """Processa frame com todas as melhorias"""
        original_height, original_width = frame.shape[:2]
        
        # 1. Verifica modo noturno
        night_mode_active = self.check_night_mode(frame)
        
        # 2. Aplica melhorias de baixa luminosidade se necessário
        if night_mode_active:
            frame = self.enhance_low_light(frame)
        
        # 3. Processamento padrão
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brilho = np.mean(gray)
        
        if brilho < 60:
            gray = self.clahe.apply(gray)
            gray = np.uint8(np.clip((gray / 255.0)**(1/1.5) * 255.0, 0, 255))
        else:
            gray = self.clahe.apply(gray)
        
        # 4. Detecção facial
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5, minSize=(150, 150))
        
        status = "Ativo"
        cor = (0, 255, 0)
        olhos_vistos = False
        face_center = None
        fall_detected = False
        
        # 5. Processa cada face detectada
        for (x, y, w, h) in faces:
            # Calcula centro da face
            face_center = (x + w//2, y + h//2)
            
            # ROI focada apenas na linha dos olhos
            roi_gray = gray[y + int(h/5):y + int(h/1.7), x:x+w]
            eyes = self.eye_cascade.detectMultiScale(roi_gray, 1.1, 7, minSize=(35, 35))
            
            olhos_vistos = len(eyes) > 0
            
            # Desenha retângulo da face
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            
            # Desenha pontos dos olhos
            for (ex, ey, ew, eh) in eyes:
                cv2.rectangle(frame, (x+ex, y+int(h/5)+ey), (x+ex+ew, y+int(h/5)+ey+eh), (0, 255, 0), 1)
            
            # Lógica de detecção de sono
            if not olhos_vistos:
                if self.olhos_fechados_start is None:
                    self.olhos_fechados_start = time.time()
                
                duracao = time.time() - self.olhos_fechados_start
                
                if 0.5 <= duracao < 1.5:
                    status = "⚠️ ALERTA: Micro-sono!"
                    cor = (0, 165, 255)
                elif duracao >= 1.5:
                    status = "😴 DORMINDO!"
                    cor = (0, 0, 255)
                    if time.time() - self.last_alert_time > 3:
                        self.falar("Douglas! Acorda agora!")
                        self.last_alert_time = time.time()
            else:
                self.olhos_fechados_start = None
            
            # 6. Detecção de queda
            fall_detected = self.detect_fall(face_center, frame.shape)
            if fall_detected:
                status = "🚨 QUEDA DETECTADA! 🚨"
                cor = (0, 0, 255)
                if time.time() - self.last_fall_alert_time > 15:
                    self.falar("URGENTE! Queda detectada! Acionando socorro!")
                    self.last_fall_alert_time = time.time()
        
        # Se não detectou face, pode ser queda
        if face_center is None and self.prev_face_center is not None:
            fall_detected = self.detect_fall(None, frame.shape)
            if fall_detected:
                status = "🚨 QUEDA DETECTADA! 🚨"
                cor = (0, 0, 255)
        
        return frame, status, cor, night_mode_active, fall_detected
    
    def draw_info_panel(self, frame, status, cor, night_mode, fall_detected):
        """Desenha painel de informações na tela"""
        # Background semi-transparente para informações
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (400, 120), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, 0.3, frame, 0.7, 0)
        
        # Status principal
        cv2.putText(frame, f"STATUS: {status}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, cor, 2)
        
        # Informações adicionais
        y_offset = 60
        cv2.putText(frame, f"Modo Noturno: {'ATIVADO' if night_mode else 'DESATIVADO'}", 
                   (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0) if night_mode else (200, 200, 200), 1)
        
        y_offset += 25
        if fall_detected:
            cv2.putText(frame, "⚠️ ALERTA DE QUEDA!", (10, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        # Frame rate e info da câmera
        y_offset += 25
        if self.cap is not None:
            cv2.putText(frame, f"Camera: OK", (10, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        else:
            cv2.putText(frame, f"Camera: SIMULACAO", (10, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        
        return frame
    
    def run(self):
        """Loop principal com todas as melhorias"""
        print("="*50)
        print("🚀 SENIOR MONITOR EXPERT - VERSÃO AVANÇADA")
        print("="*50)
        print("Recursos ativos:")
        print("✅ Sistema de voz com fila")
        print("✅ Detecção de queda")
        print("✅ Modo noturno automático")
        print("✅ Tratamento de falhas de câmera")
        print("\nComandos:")
        print("ESC - Sair")
        print("n   - Alternar modo noturno manualmente")
        print("f   - Simular queda (teste)")
        print("="*50)
        
        # Modo de simulação se não tiver câmera
        simulation_mode = self.cap is None
        
        while True:
            if simulation_mode:
                # Cria frame de simulação
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(frame, "MODO DE SIMULACAO", (150, 240), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                ret = True
            else:
                ret, frame = self.cap.read()
                if not ret:
                    print("⚠️ Falha na captura de frame. Tentando reiniciar câmera...")
                    self._init_camera()
                    simulation_mode = self.cap is None
                    continue
            
            # Espelha frame para comportamento natural
            if not simulation_mode:
                frame = cv2.flip(frame, 1)
            
            # Processa imagem
            frame, status, cor, night_mode, fall_detected = self.process_image(frame)
            
            # Desenha painel de informações
            frame = self.draw_info_panel(frame, status, cor, night_mode, fall_detected)
            
            # Comandos de teclado
            cv2.imshow('Senior Monitor Expert - Versao Avancada', frame)
            key = cv2.waitKey(1) & 0xFF
            
            if key == 27:  # ESC
                print("🛑 Encerrando monitor...")
                break
            elif key == ord('n'):  # Alterna modo noturno manual
                self.night_mode = not self.night_mode
                print(f"Modo noturno {'ativado' if self.night_mode else 'desativado'} manualmente")
            elif key == ord('f'):  # Simula queda (teste)
                print("⚠️ Teste de queda acionado!")
                self.falar("Teste de queda detectado!")
                fall_detected = True
        
        # Limpeza
        if self.cap is not None:
            self.cap.release()
        self.voice_thread_running = False
        cv2.destroyAllWindows()
        print("✅ Monitor encerrado com sucesso!")

if __name__ == "__main__":
    monitor = SeniorMonitorExpert()
    monitor.run()