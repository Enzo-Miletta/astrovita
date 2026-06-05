"""
health_monitor.py
-----------------
Logica de avaliacao de estado de saude/fadiga da tripulacao a partir das
metricas calculadas. Centraliza thresholds, geracao de alertas e
classificacao do nivel de fadiga.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import List


class FatigueLevel(Enum):
    NOMINAL = "NOMINAL"
    ATENCAO = "ATENCAO"
    CRITICO = "CRITICO"


@dataclass
class HealthState:
    """Estado consolidado de um quadro de analise."""
    ear: float = 0.0
    mar: float = 0.0
    blink_rate: float = 0.0
    yawn_count: int = 0
    head_tilt: float = 0.0
    shoulder_tilt: float = 0.0
    eyes_closed_seconds: float = 0.0
    fatigue: FatigueLevel = FatigueLevel.NOMINAL
    alerts: List[str] = field(default_factory=list)


class HealthMonitor:
    """
    Avalia o estado de saude da tripulacao com base em metricas faciais
    e posturais. Thresholds inspirados em literatura de deteccao de
    sonolencia de motoristas, adaptados ao contexto de monitoramento
    de tripulacao em missoes espaciais.
    """

    # Thresholds principais
    EAR_CLOSED = 0.21          # abaixo disso, olho considerado fechado
    MAR_YAWN = 0.60            # acima disso, bocejo
    HEAD_TILT_MAX = 18.0       # graus de inclinacao lateral aceitavel
    SHOULDER_TILT_MAX = 12.0   # graus de inclinacao de ombros aceitavel
    DROWSY_SECONDS = 1.5       # olhos fechados por mais que isso = alerta
    BLINK_RATE_HIGH = 28.0     # piscadas/min elevadas = fadiga ocular
    YAWN_WINDOW_LIMIT = 3      # bocejos na janela que disparam critico

    def __init__(self) -> None:
        self._eyes_closed_start: float | None = None
        self.yawn_count = 0
        self._mouth_open = False
        self._last_yawn_times: List[float] = []

    def _update_yawn(self, mar: float, now: float) -> bool:
        """Maquina de estados de bocejo. Retorna True quando um bocejo termina."""
        yawned = False
        if mar > self.MAR_YAWN:
            self._mouth_open = True
        else:
            if self._mouth_open:
                self.yawn_count += 1
                self._last_yawn_times.append(now)
                yawned = True
            self._mouth_open = False
        # Mantem apenas bocejos dos ultimos 60s
        self._last_yawn_times = [t for t in self._last_yawn_times
                                 if now - t <= 60.0]
        return yawned

    def evaluate(self, ear: float, mar: float, blink_rate: float,
                 head_tilt: float, shoulder_tilt: float,
                 face_present: bool) -> HealthState:
        now = time.time()
        alerts: List[str] = []

        # Tempo de olhos fechados
        eyes_closed_seconds = 0.0
        if face_present and ear < self.EAR_CLOSED:
            if self._eyes_closed_start is None:
                self._eyes_closed_start = now
            eyes_closed_seconds = now - self._eyes_closed_start
        else:
            self._eyes_closed_start = None

        # Bocejo
        self._update_yawn(mar, now)

        # Geracao de alertas
        score = 0
        if eyes_closed_seconds >= self.DROWSY_SECONDS:
            alerts.append("SONOLENCIA: olhos fechados prolongados")
            score += 2
        if blink_rate >= self.BLINK_RATE_HIGH:
            alerts.append("FADIGA OCULAR: taxa de piscadas elevada")
            score += 1
        if len(self._last_yawn_times) >= 1:
            alerts.append(f"BOCEJO detectado (x{len(self._last_yawn_times)} no ultimo min)")
            score += len(self._last_yawn_times)
        if abs(head_tilt) > self.HEAD_TILT_MAX:
            alerts.append("POSTURA: cabeca inclinada")
            score += 1
        if abs(shoulder_tilt) > self.SHOULDER_TILT_MAX:
            alerts.append("POSTURA: ombros desalinhados")
            score += 1
        if not face_present:
            alerts.append("TRIPULANTE FORA DE QUADRO")

        # Classificacao do nivel de fadiga
        if score >= 4 or eyes_closed_seconds >= self.DROWSY_SECONDS:
            fatigue = FatigueLevel.CRITICO
        elif score >= 1:
            fatigue = FatigueLevel.ATENCAO
        else:
            fatigue = FatigueLevel.NOMINAL

        return HealthState(
            ear=ear,
            mar=mar,
            blink_rate=blink_rate,
            yawn_count=self.yawn_count,
            head_tilt=head_tilt,
            shoulder_tilt=shoulder_tilt,
            eyes_closed_seconds=eyes_closed_seconds,
            fatigue=fatigue,
            alerts=alerts,
        )
