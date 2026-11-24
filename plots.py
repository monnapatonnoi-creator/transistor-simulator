"""Server-side SVG plots drawn only from parsed ngspice data."""

from __future__ import annotations

import math
from typing import Sequence

from markupsafe import Markup

from spice_engine import AcPoint, TranPoint

WIDTH = 720
HEIGHT = 330
MARGIN = {"left": 70, "right": 70, "top": 32, "bottom": 58}
PLOT_W = WIDTH - MARGIN["left"] - MARGIN["right"]
PLOT_H = HEIGHT - MARGIN["top"] - MARGIN["bottom"]


def _thin(items: Sequence, limit: int = 240) -> list:
    if len(items) <= limit:
        return list(items)
    step = math.ceil(len(items) / limit)
    reduced = list(items[::step])
    if reduced[-1] is not items[-1]:
        reduced.append(items[-1])
    return reduced


def _scale(value: float, low: float, high: float, start: float, length: float) -> float:
    if high == low:
        return start + length / 2
    return start + (value - low) / (high - low) * length


def _ticks(low: float, high: float, count: int = 5) -> list[float]:
    if high <= low:
        return [low]
    return [low + (high - low) * i / count for i in range(count + 1)]


def _fmt(value: float) -> str:
    return f"{value:.4g}"


def _polyline(coords: list[tuple[float, float]], colour: str, series: str) -> str:
    points = " ".join(f"{x:.2f},{y:.2f}" for x, y in coords)
    return (f'<polyline data-series="{series}" fill="none" stroke="{colour}" '
            f'stroke-width="2" points="{points}"/>')


def bode_svg(points: list[AcPoint], cutoff_hz: float | None = None) -> Markup:
    """Gain and phase versus logarithmic frequency, from real AC sweep points."""
    if not points:
        return Markup("")
    sample = _thin(points)
    freqs = [max(p.freq_hz, 1e-30) for p in sample]
    log_f = [math.log10(f) for f in freqs]
    gains = [p.gain_db for p in sample]
    phases = [p.phase_deg for p in sample]

    def padded(values: list[float]) -> tuple[float, float]:
        low, high = min(values), max(values)
        pad = max((high - low) * 0.12, 1.0)
        return low - pad, high + pad

    x_min, x_max = min(log_f), max(log_f)
    if x_min == x_max:
        x_min -= 1
        x_max += 1
    g_min, g_max = padded(gains)
    p_min, p_max = padded(phases)

    x = lambda value: _scale(math.log10(max(value, 1e-30)), x_min, x_max,
                             MARGIN["left"], PLOT_W)
    yg = lambda value: (MARGIN["top"] + PLOT_H
                        - _scale(value, g_min, g_max, 0, PLOT_H))
    yp = lambda value: (MARGIN["top"] + PLOT_H
                        - _scale(value, p_min, p_max, 0, PLOT_H))

    parts = [
        f'<svg data-testid="bode-plot" viewBox="0 0 {WIDTH} {HEIGHT}" '
        'xmlns="http://www.w3.org/2000/svg" role="img" '
        'aria-label="Bode plot of gain and phase">',
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#ffffff"/>',
    ]
    for tick in _ticks(x_min, x_max):
        px = MARGIN["left"] + (tick - x_min) / (x_max - x_min) * PLOT_W
        parts.append(f'<line x1="{px:.1f}" y1="{MARGIN["top"]}" x2="{px:.1f}" '
                     f'y2="{MARGIN["top"] + PLOT_H}" stroke="#e5e7eb"/>')
        parts.append(f'<text x="{px:.1f}" y="{HEIGHT - 34}" font-size="11" '
                     f'text-anchor="middle" fill="#4b5563">{_fmt(10 ** tick)}</text>')
    for tick in _ticks(g_min, g_max):
        py = yg(tick)
        parts.append(f'<line x1="{MARGIN["left"]}" y1="{py:.1f}" '
                     f'x2="{MARGIN["left"] + PLOT_W}" y2="{py:.1f}" stroke="#e5e7eb"/>')
        parts.append(f'<text x="{MARGIN["left"] - 8}" y="{py + 4:.1f}" font-size="11" '
                     f'text-anchor="end" fill="#1d4ed8">{_fmt(tick)}</text>')
    for tick in _ticks(p_min, p_max):
        py = yp(tick)
        parts.append(f'<text x="{MARGIN["left"] + PLOT_W + 8}" y="{py + 4:.1f}" '
                     f'font-size="11" fill="#b45309">{_fmt(tick)}</text>')

    parts.append(_polyline([(x(p.freq_hz), yg(p.gain_db)) for p in sample],
                           "#2563eb", "gain"))
    parts.append(_polyline([(x(p.freq_hz), yp(p.phase_deg)) for p in sample],
                           "#d97706", "phase"))
    if cutoff_hz is not None and x_min <= math.log10(cutoff_hz) <= x_max:
        cx = x(cutoff_hz)
        parts.append(f'<line x1="{cx:.1f}" y1="{MARGIN["top"]}" x2="{cx:.1f}" '
                     f'y2="{MARGIN["top"] + PLOT_H}" stroke="#dc2626" stroke-dasharray="5 4"/>')
        parts.append(f'<text x="{cx + 6:.1f}" y="{MARGIN["top"] + 14}" font-size="11" '
                     f'fill="#dc2626">-3 dB</text>')

    parts.extend([
        f'<text x="{MARGIN["left"]}" y="{HEIGHT - 10}" font-size="12" '
        'fill="#17344b">Frequency (Hz) — log scale</text>',
        f'<text x="10" y="{MARGIN["top"] - 10}" font-size="12" '
        'fill="#1d4ed8">Gain (dB)</text>',
        f'<text x="{WIDTH - 66}" y="{MARGIN["top"] - 10}" font-size="12" '
        'fill="#b45309">Phase (deg)</text>',
        '<g font-size="12">',
        f'<line x1="{MARGIN["left"]}" y1="16" x2="{MARGIN["left"] + 22}" y2="16" '
        'stroke="#2563eb" stroke-width="2"/>',
        f'<text x="{MARGIN["left"] + 28}" y="20" fill="#1d4ed8">Gain</text>',
        f'<line x1="{MARGIN["left"] + 92}" y1="16" x2="{MARGIN["left"] + 114}" y2="16" '
        'stroke="#d97706" stroke-width="2"/>',
        f'<text x="{MARGIN["left"] + 120}" y="20" fill="#b45309">Phase</text>',
        '</g>',
        '</svg>',
    ])
    return Markup("\n".join(parts))


def waveform_svg(points: list[TranPoint]) -> Markup:
    """Vin and Vout versus time, from real transient samples."""
    if not points:
        return Markup("")
    sample = _thin(points)
    times = [p.time_s * 1000.0 for p in sample]
    vin = [p.vin_v for p in sample]
    vout = [p.vout_v for p in sample]
    x_min, x_max = min(times), max(times)
    if x_min == x_max:
        x_max = x_min + 1
    all_volts = vin + vout
    y_min, y_max = min(all_volts), max(all_volts)
    pad = max((y_max - y_min) * 0.15, 0.001)
    y_min, y_max = y_min - pad, y_max + pad

    x = lambda value: _scale(value, x_min, x_max, MARGIN["left"], PLOT_W)
    y = lambda value: (MARGIN["top"] + PLOT_H
                       - _scale(value, y_min, y_max, 0, PLOT_H))

    parts = [
        f'<svg data-testid="waveform-plot" viewBox="0 0 {WIDTH} {HEIGHT}" '
        'xmlns="http://www.w3.org/2000/svg" role="img" '
        'aria-label="Input and output voltage versus time">',
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#ffffff"/>',
    ]
    for tick in _ticks(x_min, x_max):
        px = x(tick)
        parts.append(f'<line x1="{px:.1f}" y1="{MARGIN["top"]}" x2="{px:.1f}" '
                     f'y2="{MARGIN["top"] + PLOT_H}" stroke="#e5e7eb"/>')
        parts.append(f'<text x="{px:.1f}" y="{HEIGHT - 34}" font-size="11" '
                     f'text-anchor="middle" fill="#4b5563">{_fmt(tick)}</text>')
    for tick in _ticks(y_min, y_max):
        py = y(tick)
        parts.append(f'<line x1="{MARGIN["left"]}" y1="{py:.1f}" '
                     f'x2="{MARGIN["left"] + PLOT_W}" y2="{py:.1f}" stroke="#e5e7eb"/>')
        parts.append(f'<text x="{MARGIN["left"] - 8}" y="{py + 4:.1f}" font-size="11" '
                     f'text-anchor="end" fill="#4b5563">{_fmt(tick)}</text>')

    parts.append(_polyline([(x(t), y(v)) for t, v in zip(times, vin)],
                           "#2563eb", "vin"))
    parts.append(_polyline([(x(t), y(v)) for t, v in zip(times, vout)],
                           "#dc2626", "vout"))
    parts.extend([
        f'<text x="{MARGIN["left"]}" y="{HEIGHT - 10}" font-size="12" '
        'fill="#17344b">Time (ms)</text>',
        f'<text x="10" y="{MARGIN["top"] - 10}" font-size="12" '
        'fill="#17344b">Voltage (V)</text>',
        '<g font-size="12">',
        f'<line x1="{MARGIN["left"]}" y1="16" x2="{MARGIN["left"] + 22}" y2="16" '
        'stroke="#2563eb" stroke-width="2"/>',
        f'<text x="{MARGIN["left"] + 28}" y="20" fill="#1d4ed8">Vin (V)</text>',
        f'<line x1="{MARGIN["left"] + 120}" y1="16" x2="{MARGIN["left"] + 142}" y2="16" '
        'stroke="#dc2626" stroke-width="2"/>',
        f'<text x="{MARGIN["left"] + 148}" y="20" fill="#b91c1c">Vout (V)</text>',
        '</g>',
        '</svg>',
    ])
    return Markup("\n".join(parts))
