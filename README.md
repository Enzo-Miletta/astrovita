# 🛰️ AstroVita — Monitor de Saúde da Tripulação

Solução de **Visão Computacional** desenvolvida para a **Global Solution :: Space Connect (FIAP)**.

O AstroVita captura vídeo da **webcam em tempo real** e realiza **inferência visual** com **MediaPipe Face Mesh + Pose** para monitorar continuamente sinais de **fadiga, sonolência e postura** de tripulantes em missões espaciais ou centros de controle remotos — emitindo alertas precoces antes que o erro humano comprometa a missão.

---

## 🎯 Descrição da Solução

Em missões espaciais e operações críticas, a fadiga da tripulação é um dos maiores riscos para a segurança. O AstroVita atua como um **copiloto de saúde autônomo**: usando apenas uma câmera comum, ele acompanha o estado do tripulante quadro a quadro e classifica seu nível de fadiga em **NOMINAL**, **ATENÇÃO** ou **CRÍTICO**.

### Inferências visuais realizadas

| Inferência | Técnica | O que indica |
|---|---|---|
| Rastreamento facial (468 landmarks) | MediaPipe Face Mesh | Base para todas as métricas faciais |
| Detecção de pose (ombros) | MediaPipe Pose | Postura corporal / desalinhamento |
| **EAR** (Eye Aspect Ratio) | Geometria dos olhos | Olhos fechados / sonolência |
| **MAR** (Mouth Aspect Ratio) | Geometria da boca | Bocejos |
| Taxa de piscadas/min | Máquina de estados + janela deslizante | Fadiga ocular |
| Inclinação de cabeça e ombros | Trigonometria sobre landmarks | Postura inadequada |

### Aplicação prática (Space Connect)

Monitoramento autônomo e contínuo da atenção e saúde da tripulação em **ambientes críticos** (estações espaciais, controle de satélites, missões de longa duração), com **alertas em tempo real** de sonolência e fadiga — sem necessidade de sensores vestíveis, apenas com uma câmera.

---

## 🧩 Estrutura do Projeto

```
astrovita/
├── main.py                 # Loop principal: captura + pipeline de CV + HUD
├── requirements.txt        # Dependências
├── README.md
├── .gitignore
└── src/
    ├── metrics.py          # EAR, MAR, ângulos, contadores e suavização
    ├── health_monitor.py   # Thresholds, alertas e classificação de fadiga
    └── overlay.py          # HUD estilo painel de missão
```

### Pipeline de Visão Computacional

```
Webcam ──► Captura (OpenCV) ──► BGR→RGB ──► MediaPipe Face Mesh + Pose
        ──► Extração de landmarks ──► Métricas (EAR/MAR/ângulos/piscadas)
        ──► HealthMonitor (classificação) ──► HUD (overlay) ──► Exibição + Log CSV
```

---

## 📚 Bibliotecas Utilizadas

- **[OpenCV](https://opencv.org/)** (`opencv-python`) — captura de vídeo, processamento de imagem e renderização do HUD.
- **[MediaPipe](https://developers.google.com/mediapipe)** — Face Mesh (468 pontos) e Pose (estimativa corporal).
- **[NumPy](https://numpy.org/)** — operações numéricas auxiliares.

---

## ⚙️ Instruções de Execução

### 1. Pré-requisitos
- Python **3.10** ou **3.11** (recomendado)
- Uma webcam conectada

### 2. Clonar e instalar

```bash
git clone https://github.com/<SEU_USUARIO>/astrovita.git
cd astrovita

# (recomendado) criar ambiente virtual
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

pip install -r requirements.txt
```

### 3. Executar

```bash
# Webcam padrão
python main.py

# Outra webcam
python main.py --source 1

# A partir de um arquivo de vídeo
python main.py --source caminho/para/video.mp4

# Versão mais leve (sem detecção de pose)
python main.py --no-pose
```

### 4. Controles em tempo real

| Tecla | Ação |
|---|---|
| `q` / `ESC` | Sair |
| `r` | Iniciar / parar gravação de vídeo (`recordings/`) |
| `m` | Mostrar / ocultar malha facial |
| `ESPAÇO` | Pausar / retomar |

As métricas de cada sessão são salvas automaticamente em **`logs/session_log.csv`**.

---

## 🧪 Estabilidade

- **Suavização** das métricas (média móvel) reduz ruído sob variação de luz e movimento.
- **Máquina de estados** para piscadas e bocejos evita falsos positivos.
- Funciona com **rosto a distâncias variadas**; o `refine_landmarks` melhora a precisão dos olhos.
- Em baixa luminosidade, recomenda-se iluminação frontal para melhor detecção.

---

## 👤 Autor

Desenvolvido por **Enzo Miletta Herrera da Silva** — Engenharia de Software, FIAP.
Global Solution :: **Space Connect**.

---

> Tema oficial: [FIAP Global Solution — Space Connect](https://www.fiap.com.br/graduacao/global-solution/)

---

## 🛠️ Solução de Problemas

### `AttributeError: module 'mediapipe' has no attribute 'solutions'`
Você está com uma versão do MediaPipe nova demais (0.10.18+), que removeu a API `mp.solutions` usada neste projeto. Isso acontece principalmente no **Python 3.12+**, onde a versão 0.10.14 não pode ser instalada.

**Solução — use Python 3.11:**
```bash
py -3.11 -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate      # Linux/macOS
python -m pip install --upgrade pip
pip install "mediapipe==0.10.14" "numpy<2" "opencv-python==4.10.0.84"
python main.py
```

### `ERROR: Could not find a version that satisfies the requirement mediapipe==0.10.14`
Seu Python é 3.12 ou mais novo. A 0.10.14 só tem instaladores para Python 3.8–3.11. Crie um ambiente virtual com **Python 3.11** (comandos acima).
