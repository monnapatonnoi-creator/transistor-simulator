"""ngspice-backed CE amplifier simulation engine.

This module is pure Python: it validates inputs, writes SPICE netlists, runs the
external ngspice executable and parses its output. It knows nothing about Flask.
All values inside the model are SI (V, ohm, F, Hz, s).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

ANALYSES = ("dc", "ac", "tran")
MODEL_NAME = "LAB4NPN"
MODEL_LINE = ".model LAB4NPN NPN(IS=1E-14 BF=100 VAF=100)"
MAX_FREQ_HZ = 100_000.0

FIELDS = (
    "vcc", "r1", "r2", "rc", "re", "rl",
    "cin_f", "cout_f", "amplitude_v", "freq_hz",
)


class SpiceError(Exception):
    """Base class for every expected simulation failure."""


class InvalidInput(SpiceError):
    """Input is missing, non-numeric, non-finite or outside the allowed range."""


class NgspiceUnavailable(SpiceError):
    """The ngspice executable could not be found."""


class RunFailed(SpiceError):
    """ngspice exited with a non-zero status or timed out."""


class OutputEmpty(SpiceError):
    """ngspice produced no usable raw output."""


class ParseFailed(SpiceError):
    """The raw output could not be interpreted."""


@dataclass(frozen=True)
class SimInput:
    """Validated SI parameters for the reference CE voltage-divider circuit."""

    vcc: float
    r1: float
    r2: float
    rc: float
    re: float
    rl: float
    cin_f: float
    cout_f: float
    amplitude_v: float
    freq_hz: float

    def __post_init__(self) -> None:
        for name in FIELDS:
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise InvalidInput(f"{name} must be a number")
            if not math.isfinite(value):
                raise InvalidInput(f"{name} must be finite")
            if value <= 0:
                raise InvalidInput(f"{name} must be greater than zero")
        if self.freq_hz > MAX_FREQ_HZ:
            raise InvalidInput(f"freq_hz must not exceed {MAX_FREQ_HZ:g}")


def _num(value: float) -> str:
    """Format a validated float for a SPICE deck (no user text is ever passed)."""
    return format(float(value), ".8g")


def build_netlist(params: SimInput, analysis: str) -> str:
    """Return a complete ngspice deck for the requested analysis."""
    if analysis not in ANALYSES:
        raise InvalidInput(f"Unknown analysis: {analysis}")

    period = 1.0 / params.freq_hz
    directives = {
        "dc": ".op",
        "ac": ".ac dec 20 10 10Meg",
        "tran": ".tran {step} {stop}".format(
            step=_num(period / 200.0), stop=_num(5.0 * period)
        ),
    }

    lines = [
        "* CE voltage divider reference - Lab 04",
        f"VCC vcc 0 {_num(params.vcc)}",
        f"VIC vcc rc_top 0",
        f"R1 vcc base {_num(params.r1)}",
        f"R2 base 0 {_num(params.r2)}",
        f"RC rc_top col {_num(params.rc)}",
        f"RE emi 0 {_num(params.re)}",
        f"RL out 0 {_num(params.rl)}",
        f"CIN in base {_num(params.cin_f)}",
        f"COUT col out {_num(params.cout_f)}",
        f"Q1 col base emi {MODEL_NAME}",
        "VS in 0 SIN(0 {amp} {freq}) AC 1".format(
            amp=_num(params.amplitude_v), freq=_num(params.freq_hz)
        ),
        MODEL_LINE,
        ".save v(in) v(out) v(base) v(emi) v(col) i(vic)",
        directives[analysis],
        ".end",
        "",
    ]
    return "\n".join(lines)
