"""Engineering model for BJT DC bias calculations.

SI units only: volts, ohms, amperes. This module knows nothing about HTTP or HTML.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

VCE_SAT = 0.2

REGION_LABELS = {
    "active": "Forward Active",
    "cutoff": "Cutoff",
    "saturation": "Saturation",
}


class BiasInputError(ValueError):
    """Raised when component values cannot describe a physical circuit."""


class UnknownBiasType(ValueError):
    """Raised when a bias type key is absent from BIAS_REGISTRY."""


@dataclass(frozen=True)
class BiasParams:
    vcc: float
    r1: float
    r2: float
    rc: float
    re: float
    beta: float
    vbe: float = 0.70


@dataclass(frozen=True)
class BiasResult:
    bias_type: str
    vth: float
    rth: float
    ib: float
    ic: float
    ie: float
    vb: float
    ve: float
    vc: float
    vce: float
    region: str
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class BiasType:
    key: str
    label: str
    fn: Callable[[BiasParams], BiasResult]


def voltage_divider(p: BiasParams) -> BiasResult:
    """Forward-active DC operating point of a voltage-divider biased NPN."""
    vth = p.vcc * p.r2 / (p.r1 + p.r2)
    rth = p.r1 * p.r2 / (p.r1 + p.r2)
    ib = (vth - p.vbe) / (rth + (p.beta + 1.0) * p.re)
    ic = p.beta * ib
    ie = (p.beta + 1.0) * ib
    ve = ie * p.re
    vb = ve + p.vbe
    vc = p.vcc - ic * p.rc
    vce = vc - ve
    return BiasResult(
        bias_type="voltage_divider",
        vth=vth,
        rth=rth,
        ib=ib,
        ic=ic,
        ie=ie,
        vb=vb,
        ve=ve,
        vc=vc,
        vce=vce,
        region="active",
        warnings=(),
    )


BIAS_REGISTRY: dict[str, BiasType] = {
    "voltage_divider": BiasType("voltage_divider", "Voltage Divider", voltage_divider),
}


def validate_params(p: BiasParams) -> None:
    """Raise BiasInputError for the first physically invalid component value."""
    for field in ("vcc", "r1", "r2", "rc", "re", "beta"):
        if getattr(p, field) <= 0:
            raise BiasInputError(f"{field} must be greater than zero")
    if p.vbe < 0:
        raise BiasInputError("vbe must not be negative")
    if p.vbe >= p.vcc:
        raise BiasInputError("vbe must be less than vcc")


def calculate(bias_type: str, p: BiasParams) -> BiasResult:
    """Validate the parameters and evaluate the registered bias type."""
    if bias_type not in BIAS_REGISTRY:
        raise UnknownBiasType(f"Unknown bias type: {bias_type}")
    validate_params(p)
    return BIAS_REGISTRY[bias_type].fn(p)
