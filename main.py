"""
AstroVita - Monitor de Saude da Tripulacao
==========================================
Global Solution :: Space Connect (FIAP)

Solucao de Visao Computacional em Python que captura video da webcam em
tempo real e realiza inferencia visual (Face Mesh + Pose via MediaPipe)
para monitorar sinais de fadiga e estado de saude de tripulantes em
missoes espaciais ou em centros de controle remotos.

Inferencias realizadas:
  - Deteccao e rastreamento de landmarks faciais (468 pontos);
  - Deteccao de pose / postura corporal (ombros);
  - EAR (Eye Aspect Ratio)  -> sonolencia / olhos fechados;
  - MAR (Mouth Aspect Ratio) -> bocejos;
  - Taxa de piscadas por minuto -> fadiga ocular;
  - Inclinacao de cabeca e ombros -> postura;
  - Classificacao de nivel de fadiga (NOMINAL / ATENCAO / CRITICO).

Aplicacao pratica (Space Connect):
  Monitoramento autonomo e continuo da saude/atencao da tripulacao,
  emitindo alertas precoces de fadiga em ambientes criticos onde o erro
  humano pode comprometer a missao.

Controles:
  q / ESC  -> sair
  r        -> iniciar/parar gravacao de video
  m        -> mostrar/ocultar malha facial
  ESPACO   -> pausar/retomar

Uso:
  python main.py                 # webcam padrao (indice 0)
  python main.py --source 1      # outra webcam
  python main.py --source video.mp4   # arquivo de video
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from datetime import datetime

import cv2
import mediapipe as mp

# Permite importar os modulos da pasta src/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from metrics import (BlinkCounter, MovingAverage, RateTracker,  # noqa: E402
                     eye_aspect_ratio, head_tilt_angle,
                     mouth_aspect_ratio, shoulder_tilt_angle)
from health_monitor import HealthMonitor  # noqa: E402
from overlay import draw_hud  # noqa: E402

# ---------------------------------------------------------------------------
# Verificacao de compatibilidade do MediaPipe
# ---------------------------------------------------------------------------
# A API legada `mp.solutions` (Face Mesh / Pose) existe ate o mediapipe
# 0.10.14. Versoes mais novas (0.10.18+) removeram esse modulo. Se o pip
# instalou uma versao incompativel (comum no Python 3.12+), avisamos de forma
# clara em vez de deixar o traceback cru aparecer.
if not hasattr(mp, "solutions") or not hasattr(mp.solutions, "face_mesh"):
    print("\n[ERRO] Versao incompativel do MediaPipe detectada:",
          getattr(mp, "__version__", "desconhecida"))
    print("Este projeto usa a API `mp.solutions`, disponivel ate a versao 0.10.14.")
    print("\nSolucao (use Python 3.10 ou 3.11):")
    print("  pip uninstall -y mediapipe")
    print('  pip install "mediapipe==0.10.14" "numpy<2"')
    print("\nSe o seu Python for 3.12+, a 0.10.14 nao tem instalador.")
    print("Crie um ambiente com Python 3.11, por exemplo:")
    print("  py -3.11 -m venv .venv  &&  .venv\\Scripts\\activate")
    print('  pip install "mediapipe==0.10.14" "numpy<2" opencv-python')
    raise SystemExit(1)

# ---------------------------------------------------------------------------
# Indices de landmarks do MediaPipe Face Mesh
# ---------------------------------------------------------------------------
# Olho esquerdo e direito (ordem: ext, topo1, topo2, int, baixo2, baixo1)
LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]
# Boca (canto_esq, topo, canto_dir, baixo)
MOUTH = [61, 13, 291, 14]
# Centros aproximados dos olhos (para angulo da cabeca)
LEFT_EYE_CENTER = 159
RIGHT_EYE_CENTER = 386

# Indices de pose (MediaPipe Pose)
L_SHOULDER = 11
R_SHOULDER = 12


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="AstroVita - Monitor de Saude da Tripulacao (GS Space Connect)")
    p.add_argument("--source", default="0",
                   help="Indice da webcam (0,1,...) ou caminho de arquivo de video")
    p.add_argument("--width", type=int, default=1280, help="Largura de captura")
    p.add_argument("--height", type=int, default=720, help="Altura de captura")
    p.add_argument("--no-pose", action="store_true",
                   help="Desativa a deteccao de pose (mais leve)")
    p.add_argument("--log", default="logs/session_log.csv",
                   help="Caminho do arquivo CSV de log")
    return p.parse_args()


def open_source(source: str, width: int, height: int) -> cv2.VideoCapture:
    """Abre webcam (indice) ou arquivo de video."""
    cap = cv2.VideoCapture(int(source)) if source.isdigit() \
        else cv2.VideoCapture(source)
    if source.isdigit():
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    return cap


def to_pixel(landmark, w: int, h: int):
    return (landmark.x * w, landmark.y * h)


def main() -> int:
    args = parse_args()

    cap = open_source(args.source, args.width, args.height)
    if not cap.isOpened():
        print(f"[ERRO] Nao foi possivel abrir a fonte de video: {args.source}")
        return 1

    mp_face = mp.solutions.face_mesh
    mp_pose = mp.solutions.pose
    mp_draw = mp.solutions.drawing_utils
    mp_styles = mp.solutions.drawing_styles

    face_mesh = mp_face.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    pose = None if args.no_pose else mp_pose.Pose(
        model_complexity=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    # Componentes de metricas
    blink_counter = BlinkCounter()
    blink_rate = RateTracker(window_seconds=60.0)
    ear_smooth = MovingAverage(size=3)
    mar_smooth = MovingAverage(size=3)
    monitor = HealthMonitor()

    # Estado de UI
    show_mesh = True
    paused = False
    recording = False
    writer = None

    # Logging
    os.makedirs(os.path.dirname(args.log) or ".", exist_ok=True)
    log_file = open(args.log, "w", newline="", encoding="utf-8")
    log_writer = csv.writer(log_file)
    log_writer.writerow(["timestamp", "ear", "mar", "blink_rate",
                         "yawn_count", "head_tilt", "shoulder_tilt",
                         "eyes_closed_s", "fatigue"])

    os.makedirs("recordings", exist_ok=True)

    start_time = time.time()
    prev_t = start_time
    fps = 0.0

    print("[INFO] AstroVita iniciado. Pressione 'q' ou ESC para sair.")

    while True:
        if not paused:
            ok, frame = cap.read()
            if not ok:
                print("[INFO] Fim do video / sem quadros.")
                break
            frame = cv2.flip(frame, 1)  # espelha para sensacao de espelho

        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False

        face_results = face_mesh.process(rgb)
        pose_results = pose.process(rgb) if pose is not None else None

        rgb.flags.writeable = True

        ear = 0.0
        mar = 0.0
        head_tilt = 0.0
        shoulder_tilt = 0.0
        face_present = False
        now = time.time()

        # ----- Inferencia facial -----
        if face_results.multi_face_landmarks:
            face_present = True
            face_landmarks = face_results.multi_face_landmarks[0]
            pts = [to_pixel(lm, w, h) for lm in face_landmarks.landmark]

            left_ear = eye_aspect_ratio(pts, LEFT_EYE)
            right_ear = eye_aspect_ratio(pts, RIGHT_EYE)
            ear = ear_smooth.update((left_ear + right_ear) / 2.0)
            mar = mar_smooth.update(mouth_aspect_ratio(pts, MOUTH))

            if blink_counter.update(ear):
                blink_rate.add_event(now)

            head_tilt = head_tilt_angle(pts[LEFT_EYE_CENTER],
                                        pts[RIGHT_EYE_CENTER])

            if show_mesh:
                mp_draw.draw_landmarks(
                    image=frame,
                    landmark_list=face_landmarks,
                    connections=mp_face.FACEMESH_TESSELATION,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=mp_styles
                    .get_default_face_mesh_tesselation_style(),
                )

        # ----- Inferencia de pose -----
        if pose_results and pose_results.pose_landmarks:
            lm = pose_results.pose_landmarks.landmark
            ls = to_pixel(lm[L_SHOULDER], w, h)
            rs = to_pixel(lm[R_SHOULDER], w, h)
            shoulder_tilt = shoulder_tilt_angle(ls, rs)
            if show_mesh:
                cv2.line(frame, (int(ls[0]), int(ls[1])),
                         (int(rs[0]), int(rs[1])), (200, 160, 60), 2)
                cv2.circle(frame, (int(ls[0]), int(ls[1])), 5, (90, 200, 90), -1)
                cv2.circle(frame, (int(rs[0]), int(rs[1])), 5, (90, 200, 90), -1)

        # ----- Avaliacao de saude -----
        current_rate = blink_rate.rate_per_minute(now)
        state = monitor.evaluate(ear, mar, current_rate,
                                 head_tilt, shoulder_tilt, face_present)

        # ----- FPS -----
        dt = now - prev_t
        prev_t = now
        if dt > 0:
            fps = 0.9 * fps + 0.1 * (1.0 / dt)

        session_seconds = now - start_time

        # ----- HUD -----
        draw_hud(frame, state, fps, recording, session_seconds)

        # ----- Gravacao -----
        if recording and writer is not None:
            writer.write(frame)

        # ----- Log CSV -----
        log_writer.writerow([
            datetime.now().isoformat(timespec="seconds"),
            f"{state.ear:.4f}", f"{state.mar:.4f}",
            f"{state.blink_rate:.2f}", state.yawn_count,
            f"{state.head_tilt:.2f}", f"{state.shoulder_tilt:.2f}",
            f"{state.eyes_closed_seconds:.2f}", state.fatigue.value,
        ])

        cv2.imshow("AstroVita - Monitor de Saude da Tripulacao", frame)

        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), 27):  # q ou ESC
            break
        elif key == ord("m"):
            show_mesh = not show_mesh
        elif key == ord(" "):
            paused = not paused
        elif key == ord("r"):
            recording = not recording
            if recording:
                fname = os.path.join(
                    "recordings",
                    f"astrovita_{datetime.now():%Y%m%d_%H%M%S}.mp4")
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                writer = cv2.VideoWriter(fname, fourcc, 20.0, (w, h))
                print(f"[INFO] Gravando em {fname}")
            else:
                if writer is not None:
                    writer.release()
                    writer = None
                print("[INFO] Gravacao encerrada.")

    # ----- Limpeza -----
    cap.release()
    if writer is not None:
        writer.release()
    log_file.close()
    face_mesh.close()
    if pose is not None:
        pose.close()
    cv2.destroyAllWindows()
    print("[INFO] Sessao encerrada. Log salvo em:", args.log)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
