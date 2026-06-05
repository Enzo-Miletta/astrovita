"""
metrics.py
----------
Funcoes de calculo de metricas faciais e posturais para o monitor de
saude da tripulacao (AstroVita - GS Space Connect / FIAP).

Todas as metricas sao puramente geometricas, calculadas a partir dos
landmarks normalizados retornados pelo MediaPipe Face Mesh e Pose.
"""

from __future__ import annotations

import math
from collections import deque
from typing import Deque, List, Tuple


def _euclidean(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Distancia euclidiana entre dois pontos 2D."""
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def eye_aspect_ratio(landmarks: List[Tuple[float, float]],
                     eye_idx: List[int]) -> float:
    """
    Calcula o EAR (Eye Aspect Ratio) de um olho.

    eye_idx deve conter 6 indices na ordem:
        [canto_externo, topo1, topo2, canto_interno, baixo2, baixo1]

    EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)

    Valores baixos (< ~0.20) indicam olho fechado.
    """
    p1 = landmarks[eye_idx[0]]
    p2 = landmarks[eye_idx[1]]
    p3 = landmarks[eye_idx[2]]
    p4 = landmarks[eye_idx[3]]
    p5 = landmarks[eye_idx[4]]
    p6 = landmarks[eye_idx[5]]

    vertical = _euclidean(p2, p6) + _euclidean(p3, p5)
    horizontal = 2.0 * _euclidean(p1, p4)
    if horizontal == 0:
        return 0.0
    return vertical / horizontal


def mouth_aspect_ratio(landmarks: List[Tuple[float, float]],
                       mouth_idx: List[int]) -> float:
    """
    Calcula o MAR (Mouth Aspect Ratio).

    mouth_idx na ordem:
        [canto_esq, topo, canto_dir, baixo]

    MAR alto (> ~0.6) indica boca muito aberta (bocejo).
    """
    left = landmarks[mouth_idx[0]]
    top = landmarks[mouth_idx[1]]
    right = landmarks[mouth_idx[2]]
    bottom = landmarks[mouth_idx[3]]

    vertical = _euclidean(top, bottom)
    horizontal = _euclidean(left, right)
    if horizontal == 0:
        return 0.0
    return vertical / horizontal


def head_tilt_angle(left_eye: Tuple[float, float],
                    right_eye: Tuple[float, float]) -> float:
    """
    Angulo de inclinacao da cabeca (em graus) baseado na linha dos olhos.
    0 graus = cabeca reta. Valores positivos/negativos = inclinacao lateral.
    """
    dx = right_eye[0] - left_eye[0]
    dy = right_eye[1] - left_eye[1]
    return math.degrees(math.atan2(dy, dx))


def shoulder_tilt_angle(left_shoulder: Tuple[float, float],
                        right_shoulder: Tuple[float, float]) -> float:
    """
    Angulo de inclinacao dos ombros (em graus). Util para detectar
    postura desalinhada / curvada, sinal de fadiga.
    """
    dx = right_shoulder[0] - left_shoulder[0]
    dy = right_shoulder[1] - left_shoulder[1]
    return math.degrees(math.atan2(dy, dx))


class BlinkCounter:
    """
    Contador de piscadas com maquina de estados simples baseada em EAR.

    Uma piscada e contabilizada quando o EAR cai abaixo de `close_thresh`
    por pelo menos `consec_frames` quadros consecutivos e depois sobe
    acima de `open_thresh`.
    """

    def __init__(self, close_thresh: float = 0.21,
                 open_thresh: float = 0.25,
                 consec_frames: int = 2) -> None:
        self.close_thresh = close_thresh
        self.open_thresh = open_thresh
        self.consec_frames = consec_frames
        self.counter = 0
        self.total_blinks = 0
        self._closed = False

    def update(self, ear: float) -> bool:
        """Atualiza o estado. Retorna True no quadro em que uma piscada termina."""
        blinked = False
        if ear < self.close_thresh:
            self.counter += 1
            if self.counter >= self.consec_frames:
                self._closed = True
        else:
            if self._closed and ear > self.open_thresh:
                self.total_blinks += 1
                blinked = True
            self.counter = 0
            self._closed = False
        return blinked


class RateTracker:
    """
    Calcula uma taxa por minuto a partir de timestamps de eventos
    dentro de uma janela deslizante (default 60s).
    """

    def __init__(self, window_seconds: float = 60.0) -> None:
        self.window = window_seconds
        self._events: Deque[float] = deque()

    def add_event(self, timestamp: float) -> None:
        self._events.append(timestamp)

    def rate_per_minute(self, now: float) -> float:
        # Remove eventos fora da janela
        while self._events and (now - self._events[0]) > self.window:
            self._events.popleft()
        if not self._events:
            return 0.0
        elapsed = max(now - self._events[0], 1e-6)
        # Normaliza para 60s
        return len(self._events) * (60.0 / min(elapsed, self.window))


class MovingAverage:
    """Media movel simples para suavizar metricas ruidosas."""

    def __init__(self, size: int = 5) -> None:
        self._buf: Deque[float] = deque(maxlen=size)

    def update(self, value: float) -> float:
        self._buf.append(value)
        return sum(self._buf) / len(self._buf)
