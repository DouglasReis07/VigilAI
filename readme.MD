# 🤖 VigilAI - Sistema de Monitoramento


[![Version](https://img.shields.io/badge/version-3.0-blue.svg)](https://github.com/seu-repo)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

Um sistema inteligente de monitoramento que usa a câmera do computador para detectar situações de risco, como quedas, sonolência excessiva e esquecimento de medicamentos.

## ✨ Funcionalidades

### 🎯 Principais
- ✅ **Detecção de Queda** - Identifica quedas por movimento brusco com confirmação multi-frame
- ✅ **Monitoramento de Sono** - Detecta micro-sonos (0.5s) e sono profundo (1.5s+)
- ✅ **Alertas de Voz** - Avisos falados: "Cuidado, está com sono!" e "Acorde! Está dormindo!"
- ✅ **Cálculo de Risco** - Mostra probabilidade de queda em tempo real (0-100%)
- ✅ **Cores por Risco** - Verde 🟢 (baixo), Laranja 🟡 (moderado), Vermelho 🔴 (alto)
- ✅ **Barra de Progresso do Sono** - Visualização do tempo com olhos fechados
- ✅ **Dashboard Gráfico** - Dois gráficos: risco de queda + estado de sono

### 💊 Medicamentos
- ✅ **Cadastro de Remédios** - Nome, dosagem, múltiplos horários
- ✅ **Lembretes Automáticos** - Som e janela popup no horário
- ✅ **Controle de Adesão** - Marcar quando foi tomado com data/hora
- ✅ **Persistência** - Dados salvos em arquivo JSON
- ✅ **Relatório de Conformidade** - Percentual de cumprimento diário

### 📊 Relatórios e Logs
- ✅ **Relatório Diário Completo** - Estatísticas de sono, quedas, medicamentos
- ✅ **Logs de Eventos** - Histórico em CSV com timestamp
- ✅ **Gráficos de Tendência** - Evolução do risco ao longo do tempo
- ✅ **Recomendações** - Sugestões personalizadas baseadas nos dados
- ✅ **Picos de Risco** - Registro dos momentos de maior perigo

### 🎮 Interface
- ✅ **Teclas de Atalho** - F1 a F5, F11, ESC
- ✅ **Modo Noturno** - Automático entre 22h e 6h
- ✅ **Tela Cheia** - Pressione F11
- ✅ **FPS Opcional** - Ative com F5 para monitorar performance
- ✅ **Processamento Adaptativo** - Ajusta automaticamente para melhor performance

## 🚀 Instalação

### Pré-requisitos
- Python 3.8 ou superior
- Webcam (integrada ou USB)
- Windows (recomendado) / Linux / Mac

### Passo a Passo

1. **Clone o repositório**
```bash
git clone https://github.com/DouglasReis07/VigilAI.git
cd VigilAI
Instale as dependencias 
pip install -r requirements.txt
Crie um ambiente virtual (recomendado)

bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
Instale as dependências

bash
pip install opencv-python numpy pyttsx3 pillow matplotlib
Execute o programa

bash
python main.py
🎮 Como Usar
Comandos Rápidos
Tecla	Função	Descrição
F1	Adicionar Medicamento	Abre formulário para novo remédio
F2	Marcar Tomado	Marca medicamento como tomado hoje
F3	Gerar Relatório	Cria relatório completo do dia
F4	Ver Logs	Mostra histórico de eventos
F5	FPS	Ativa/desativa contador de FPS
F11	Tela Cheia	Alterna modo tela cheia
ESC	Sair	Encerra o programa
Adicionando Medicamentos
Pressione F1

Preencha os campos:

Nome: Ex: "Losartana"

Dosagem: Ex: "50mg", "1 comprimido"

Horários: Ex: "08:00, 20:00" (separados por vírgula)

Clique em "Salvar"

Marcando Medicamento como Tomado
Pressione F2

Selecione o medicamento na lista

Clique em "Marcar como Tomado"

O sistema confirma com voz e som

Interpretando os Alertas
Alertas de Sono
Tempo	Status	Alerta de Voz
0.5 - 1.5 segundos	⚠️ SONOLENTO	"Cuidado, está com sono!"
> 1.5 segundos	😴 DORMINDO	"Acorde! Está dormindo!" (repetido a cada 10s)
Cores do Risco de Queda

Cor	           Risco	     Significado	  Ação Recomendada
🟢 Verde	  0-40%	        Baixo	         Monitoramento normal
🟡 Laranja	  40-70%	    Moderado	     Atenção redobrada
🔴 Vermelho	  70-100%	    Alto	         Intervenção imediata

O que aparece na tela
text
┌─────────────────────────────────────────────────────────────┐
│  😴 DORMINDO                                    FPS: 30     │
│  Risco Queda: 75%                                           │
│  Movimento: 180px                                           │
│  Olhos fechados: 2.3s                                       │
│  [████████░░]                                         │
│  ⚠️ ALTO RISCO!                                             │
└─────────────────────────────────────────────────────────────┘

📁 Arquivos Gerados
Arquivo	Conteúdo	            Formato
medications.json	            Lista de medicamentos cadastrados	JSON
log_YYYYMMDD.csv	            Histórico de eventos do dia	        CSV
relatorio_YYYYMMDD_HHMMSS.txt	Relatório completo	                TXT
📊 Exemplo de Relatório
text
============================================================
RELATÓRIO COMPLETO - SENIOR MONITOR
============================================================

📅 Data e Hora: 20/01/2024 15:30:00

============================================================
📊 ESTATÍSTICAS DO DIA
============================================================

😴 SONO E CANSACO:
   • Micro-sonos detectados: 3
   • Sono profundo detectado: 1
   • Total de eventos de sono: 4

⚠️ QUEDAS E RISCOS:
   • Alertas de queda: 0
   • Picos de alto risco: 2
   • Risco médio do dia: 35.5%

💊 MEDICAMENTOS:
   • Total de doses do dia: 4
   • Doses tomadas: 3
   • Taxa de adesão: 75.0%
   
   Detalhamento:
      • 08:00 - Losartana (50mg) - ✅ TOMADO
      • 08:30 - Metformina (500mg) - ✅ TOMADO
      • 20:00 - Losartana (50mg) - ⏰ PENDENTE
      • 20:30 - Metformina (500mg) - ✅ TOMADO

============================================================
💡 RECOMENDAÇÕES PERSONALIZADAS
============================================================
   • 💊 Baixa adesão aos medicamentos - Crie lembretes adicionais
🔧 Configuração Avançada
Ajustando Sensibilidade
No arquivo main.py, você pode ajustar:

python
# Detecção de queda (quanto maior, menos sensível)
self.fall_threshold = 200

# Tempo para alerta de sono (segundos)
if sleep_duration >= 1.5:  # Sono profundo
if sleep_duration >= 0.5:  # Micro-sono

# Risco de queda
if avg_movement > 200:  # Movimento brusco
    self.fall_risk += 0.5
Personalizando Voz
python
# Velocidade da fala (padrão: 170)
self.engine.setProperty('rate', 150)  # Mais lento
self.engine.setProperty('rate', 200)  # Mais rápido

# Volume (0-1)
self.engine.setProperty('volume', 0.9)
🐛 Solução de Problemas
A câmera não funciona
bash
# Verifique se a câmera está conectada
# Teste com outro aplicativo
# O sistema tenta automaticamente os índices 0 e 1
Sem som nos alertas
python
# Verifique se o som do Windows está ativado
# O sistema usa winsound (Windows) - em Linux/Mac pode não funcionar
O programa está lento
O sistema já usa processamento adaptativo

Reduza a resolução da câmera (altere no código)

Feche outros programas

📈 Performance
Modo	                  CPU	      RAM	         FPS
Normal (parado)	         8-12%	    ~100MB	        15-20
Normal (movimento)	     15-20%	    ~100MB	        20-25
Alta Performance	     25-35%	    ~120MB	         30

🔒 Privacidade
✅ Todos os dados ficam localmente no seu computador

✅ Nenhuma imagem é enviada para a nuvem

✅ Logs são salvos em formato texto simples

✅ Você pode desligar a câmera a qualquer momento

🤝 Contribuindo
Sugestões são bem-vindas! Abra uma issue ou envie um pull request.

Ideias para futuras melhorias
Notificações por WhatsApp/Telegram

Dashboard web para acesso remoto

Reconhecimento facial para múltiplos usuários

Detecção de postura curvada

Botão de emergência físico

📄 Licença
MIT License - Proibido para uso comercial!

👨‍💻 Autor
Seu Nome - @DouglasReis07

🙏 Agradecimentos
OpenCV pela biblioteca de visão computacional

Tkinter pela interface gráfica

pyttsx3 pela síntese de voz

⚡ Quick Start
bash
# 1. Instalar dependências
pip install opencv-python numpy pyttsx3 pillow matplotlib

# 2. Executar
python main.py

# 3. Comandos básicos
# F1 - Adicionar remédio
# F2 - Marcar tomado
# F3 - Relatório completo
# ESC - Sair

🎯 Teste Rápido
Teste o sono: Feche os olhos por 2 segundos → Ouça "Acorde! Está dormindo!"

Teste o risco: Mexa a cabeça rapidamente → Veja o risco aumentar

Teste medicamento: Adicione um remédio com horário atual → Receba o lembrete

Feito com ❤️ para cuidar de quem amamos

