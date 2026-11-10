"""Format SI values with engineering units for display.

Values stay in SI (V, A, ohm) inside the model; this module only formats.
"""

from __future__ import annotations

import math


def _sig(value: float, digits: int = 3) -> str:
    """Format with a fixed number of significant digits, never in scientific notation."""
    if value == 0:
        return "0"
    magnitude = math.floor(math.log10(abs(value)) + 1e-12)
    decimals = max(digits - 1 - magnitude, 0)
    return f"{value:.{decimals}f}"


def fmt_current(amperes: float) -> str:
    magnitude = abs(amperes)
    if magnitude < 1e-3:
        return f"{_sig(amperes * 1e6)} µA"
    if magnitude < 1:
        return f"{_sig(amperes * 1e3)} mA"
    return f"{_sig(amperes)} A"


def fmt_voltage(volts: float) -> str:
    return f"{_sig(volts)} V"


def fmt_resistance(ohms: float) -> str:
    magnitude = abs(ohms)
    if magnitude >= 1e6:
        return f"{_sig(ohms / 1e6)} MΩ"
    if magnitude >= 1e3:
        return f"{_sig(ohms / 1e3)} kΩ"
    return f"{_sig(ohms)} Ω"
