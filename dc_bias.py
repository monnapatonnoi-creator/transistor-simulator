"""Engineering model for BJT DC bias calculations.

SI units only: volts, ohms, amperes. This module knows nothing about HTTP or HTML.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
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
    r1: float = 0.0
    r2: float = 0.0
    rc: float = 0.0
    re: float = 0.0
    beta: float = 0.0
    vbe: float = 0.70
    rb: float = 0.0


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
    required: tuple[str, ...] = ()


def _finish(bias_type: str, vth: float, rth: float, ib: float, ve: float, p: BiasParams) -> BiasResult:
    """Shared forward-active collation from IB and VE (no region labelling)."""
    ic = p.beta * ib
    ie = (p.beta + 1.0) * ib
    vb = ve + p.vbe
    vc = p.vcc - ic * p.rc
    return BiasResult(
        bias_type=bias_type,
        vth=vth,
        rth=rth,
        ib=ib,
        ic=ic,
        ie=ie,
        vb=vb,
        ve=ve,
        vc=vc,
        vce=vc - ve,
        region="active",
        warnings=(),
    )


def fixed_bias(p: BiasParams) -> BiasResult:
    """Forward-active DC operating point of a base-resistor (fixed) biased NPN.

    Emitter is tied directly to ground, so VE is 0 V. VTH/RTH are reported as
    VCC/RB so the result schema and region classification stay uniform.
    """
    ib = (p.vcc - p.vbe) / p.rb
    return _finish("fixed_bias", p.vcc, p.rb, ib, 0.0, p)


def emitter_bias(p: BiasParams) -> BiasResult:
    """Single-supply emitter-bias NPN: RB from VCC to base, RE from emitter to ground."""
    ib = (p.vcc - p.vbe) / (p.rb + (p.beta + 1.0) * p.re)
    ie = (p.beta + 1.0) * ib
    return _finish("emitter_bias", p.vcc, p.rb, ib, ie * p.re, p)


def voltage_divider(p: BiasParams) -> BiasResult:
    """Forward-active DC operating point of a voltage-divider biased NPN."""
    vth = p.vcc * p.r2 / (p.r1 + p.r2)
    rth = p.r1 * p.r2 / (p.r1 + p.r2)
    ib = (vth - p.vbe) / (rth + (p.beta + 1.0) * p.re)
    return _finish("voltage_divider", vth, rth, ib, (p.beta + 1.0) * ib * p.re, p)


BIAS_REGISTRY: dict[str, BiasType] = {
    "voltage_divider": BiasType(
        "voltage_divider", "Voltage Divider", voltage_divider,
        ("vcc", "r1", "r2", "re", "rc", "beta", "vbe"),
    ),
    "fixed_bias": BiasType(
        "fixed_bias", "Fixed Bias", fixed_bias,
        ("vcc", "rb", "rc", "beta", "vbe"),
    ),
    "emitter_bias": BiasType(
        "emitter_bias", "Emitter Bias", emitter_bias,
        ("vcc", "rb", "re", "rc", "beta", "vbe"),
    ),
}


def validate_params(p: BiasParams, required: tuple[str, ...] | None = None) -> None:
    """Raise BiasInputError for the first invalid value used by the chosen mode.

    ``required=None`` keeps the legacy Lab 2 behaviour of checking every resistor.
    """
    check = required if required is not None else ("vcc", "r1", "r2", "rc", "re", "beta")
    for field in check:
        if getattr(p, field) <= 0:
            raise BiasInputError(f"{field} must be greater than zero")
    if p.vbe < 0:
        raise BiasInputError("vbe must not be negative")
    if p.vbe >= p.vcc:
        raise BiasInputError("vbe must be less than vcc")


def classify_region(p: BiasParams, r: BiasResult) -> tuple[str, tuple[str, ...]]:
    """Label the operating region. The result values are never corrected here."""
    warnings: list[str] = []
    if r.ib <= 0 or r.vth <= p.vbe:
        warnings.append(
            "Device is off (VTH <= VBE). Forward-active equations do not apply; "
            "these values are not usable."
        )
        region = "cutoff"
    elif r.vce <= VCE_SAT:
        warnings.append(
            "Device is in saturation (VCE <= 0.2 V). Forward-active equations do "
            "not apply; these values are not usable."
        )
        region = "saturation"
    else:
        region = "active"
    if r.vce > p.vcc:
        warnings.append(
            "VCE exceeds VCC; the forward-active result is physically implausible."
        )
    return region, tuple(warnings)


def calculate(bias_type: str, p: BiasParams) -> BiasResult:
    """Validate the parameters, evaluate the bias type, then label its region."""
    if bias_type not in BIAS_REGISTRY:
        raise UnknownBiasType(f"Unknown bias type: {bias_type}")
    bias = BIAS_REGISTRY[bias_type]
    validate_params(p, bias.required)
    raw = bias.fn(p)
    region, warnings = classify_region(p, raw)
    return replace(raw, region=region, warnings=warnings)
