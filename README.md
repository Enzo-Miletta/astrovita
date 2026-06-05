# Monitor de Saúde da Tripulação

O AstroVita captura vídeo da **webcam em tempo real** e realiza **inferência visual** com **MediaPipe Face Mesh + Pose** para monitorar continuamente sinais de **fadiga, sonolência e postura** de tripulantes em missões espaciais ou centros de controle remotos — emitindo alertas precoces antes que o erro humano comprometa a missão.

---

## Descrição da Solução

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


### Pipeline de Visão Computacional

```
Webcam ──► Captura (OpenCV) ──► BGR→RGB ──► MediaPipe Face Mesh + Pose
        ──► Extração de landmarks ──► Métricas (EAR/MAR/ângulos/piscadas)
        ──► HealthMonitor (classificação) ──► HUD (overlay) ──► Exibição + Log CSV
```

---

## Bibliotecas Utilizadas

- **OpenCV
- **MediaPipe
- **NumPy

---


### Clonar e instalar

```bash
# (recomendado) criar ambiente virtual (Rodar em 3.11_3)
python -m venv .venv
# Windows:
.venv\Scripts\activate

pip install -r requirements.txt
```

### Executar

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
## 👤 Autor

### Desenvolvido por:
 **Enzo Miletta Herrera da Silva - RM98677**
**Fabricio Bettarello Heluani - RM554638**
**Vitor Victorino Couto - RM554965**
---