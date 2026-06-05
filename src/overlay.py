"""
overlay.py
----------
Renderizacao do HUD (Heads-Up Display) estilo painel de missao sobre o
quadro de video. Desenha metricas, barras, alertas e o nivel de fadiga.
"""

from __future__ import annotations

from typing import Tuple

import cv2

from health_monitor import FatigueLevel, HealthState

# Paleta de cores (BGR)
COLOR_BG = (25, 25, 25)
COLOR_PANEL = (40, 40, 40)
COLOR_TEXT = (235, 235, 235)
COLOR_OK = (90, 200, 90)
COLOR_WARN = (60, 180, 250)
COLOR_CRIT = (60, 60, 235)
COLOR_ACCENT = (200, 160, 60)

LEVEL_COLOR = {
    FatigueLevel.NOMINAL: COLOR_OK,
    FatigueLevel.ATENCAO: COLOR_WARN,
    FatigueLevel.CRITICO: COLOR_CRIT,
}


def _draw_panel(frame, x: int, y: int, w: int, h: int,
                alpha: float = 0.55) -> None:
    """Desenha um painel semitransparente."""
    overlay = frame.copy()
    cv2.rectangle(overlay, (x, y), (x + w, y + h), COLOR_PANEL, -1)
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)


def _draw_bar(frame, x: int, y: int, w: int, h: int,
              value: float, vmin: float, vmax: float,
              color: Tuple[int, int, int]) -> None:
    """Barra horizontal de nivel."""
    cv2.rectangle(frame, (x, y), (x + w, y + h), (70, 70, 70), 1)
    ratio = (value - vmin) / (vmax - vmin) if vmax > vmin else 0
    ratio = max(0.0, min(1.0, ratio))
    fill = int(w * ratio)
    if fill > 0:
        cv2.rectangle(frame, (x, y), (x + fill, y + h), color, -1)


def draw_hud(frame, state: HealthState, fps: float,
             recording: bool, session_seconds: float) -> None:
    """Desenha o painel completo de monitoramento sobre o frame."""
    h, w = frame.shape[:2]

    # ---- Cabecalho ----
    _draw_panel(frame, 0, 0, w, 40, alpha=0.6)
    cv2.putText(frame, "ASTROVITA :: MONITOR DE SAUDE DA TRIPULACAO",
                (12, 27), cv2.FONT_HERSHEY_SIMPLEX, 0.6, COLOR_ACCENT, 2)
    mm = int(session_seconds // 60)
    ss = int(session_seconds % 60)
    cv2.putText(frame, f"T+ {mm:02d}:{ss:02d}  |  {fps:4.1f} FPS",
                (w - 230, 27), cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_TEXT, 1)

    # ---- Painel lateral de metricas ----
    panel_w = 250
    _draw_panel(frame, 8, 50, panel_w, 230, alpha=0.5)
    tx = 20
    ty = 78
    line = 26

    def metric(label: str, value: str, color=COLOR_TEXT):
        nonlocal ty
        cv2.putText(frame, label, (tx, ty),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (170, 170, 170), 1)
        cv2.putText(frame, value, (tx + 150, ty),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        ty += line

    metric("EAR (olhos)", f"{state.ear:.3f}")
    _draw_bar(frame, tx, ty - 18, 140, 6, state.ear, 0.10, 0.35, COLOR_ACCENT)
    ty += 6
    metric("MAR (boca)", f"{state.mar:.3f}")
    _draw_bar(frame, tx, ty - 18, 140, 6, state.mar, 0.0, 1.0, COLOR_ACCENT)
    ty += 6
    metric("Piscadas/min", f"{state.blink_rate:4.1f}")
    metric("Bocejos", f"{state.yawn_count}")
    metric("Inclin. cabeca", f"{state.head_tilt:+5.1f} deg")
    metric("Inclin. ombros", f"{state.shoulder_tilt:+5.1f} deg")
    metric("Olhos fechados", f"{state.eyes_closed_seconds:4.1f} s")

    # ---- Status de fadiga ----
    color = LEVEL_COLOR[state.fatigue]
    _draw_panel(frame, w - 230, 50, 222, 56, alpha=0.55)
    cv2.putText(frame, "ESTADO:", (w - 218, 74),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (170, 170, 170), 1)
    cv2.putText(frame, state.fatigue.value, (w - 218, 98),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

    # ---- Alertas ----
    if state.alerts:
        ay = h - 20 - (len(state.alerts) * 24)
        _draw_panel(frame, 8, ay - 10, w - 16, len(state.alerts) * 24 + 14,
                    alpha=0.5)
        for i, alert in enumerate(state.alerts):
            cv2.putText(frame, f"! {alert}", (20, ay + 12 + i * 24),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_CRIT, 1)

    # ---- Indicador de gravacao ----
    if recording:
        cv2.circle(frame, (w - 24, h - 24), 8, COLOR_CRIT, -1)
        cv2.putText(frame, "REC", (w - 70, h - 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_CRIT, 2)

    # ---- Borda colorida segundo estado ----
    cv2.rectangle(frame, (0, 0), (w - 1, h - 1), color, 3)
