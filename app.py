from __future__ import annotations

from flask import Flask, redirect, render_template, request, url_for

from dc_bias import (
    BIAS_REGISTRY,
    REGION_LABELS,
    BiasInputError,
    BiasParams,
    UnknownBiasType,
    calculate,
)
from units import fmt_current, fmt_voltage, fmt_resistance

DEFAULTS = {
    "vcc": "12",
    "r1": "100",
    "r1_unit": "kohm",
    "r2": "22",
    "r2_unit": "kohm",
    "rc": "2.2",
    "rc_unit": "kohm",
    "re": "1",
    "re_unit": "kohm",
    "beta": "100",
    "vbe": "0.70",
    "bias_type": "voltage_divider",
}


def _to_ohms(raw: str, unit: str) -> float:
    if unit == "kohm":
        return float(raw) * 1000.0
    if unit == "ohm":
        return float(raw)
    raise ValueError(f"Unknown unit: {unit}")


def _parse_request(form):
    """Return (BiasParams, []) or (None, [error messages])."""
    errors: list[str] = []

    def number(field: str):
        raw = (form.get(field) or "").strip()
        if not raw:
            errors.append(f"{field} must be a number")
            return None
        try:
            return float(raw)
        except ValueError:
            errors.append(f"{field} must be a number")
            return None

    def resistor(field: str):
        raw = (form.get(field) or "").strip()
        unit = form.get(f"{field}_unit", "kohm")
        if not raw:
            errors.append(f"{field} must be a number")
            return None
        try:
            return _to_ohms(raw, unit)
        except ValueError as exc:
            errors.append(str(exc))
            return None

    vcc = number("vcc")
    r1 = resistor("r1")
    r2 = resistor("r2")
    rc = resistor("rc")
    re_ = resistor("re")
    beta = number("beta")
    vbe = number("vbe")
    if errors:
        return None, errors
    try:
        params = BiasParams(vcc=vcc, r1=r1, r2=r2, rc=rc, re=re_, beta=beta, vbe=vbe)
    except TypeError:
        return None, errors
    return params, []


def create_app() -> Flask:
    app = Flask(__name__)
    app.jinja_env.filters["fmt_current"] = fmt_current
    app.jinja_env.filters["fmt_voltage"] = fmt_voltage
    app.jinja_env.filters["fmt_resistance"] = fmt_resistance

    @app.get("/")
    def index():
        return render_template(
            "index.html",
            bias_types=list(BIAS_REGISTRY.values()),
            form=DEFAULTS.copy(),
            errors=[],
            result=None,
            region_labels=REGION_LABELS,
        )

    @app.post("/calculate", endpoint="calculate_bias")
    def calculate_bias():
        form = request.form
        params, errors = _parse_request(form)
        result = None
        if params is not None:
            try:
                result = calculate(form.get("bias_type", ""), params)
            except (BiasInputError, UnknownBiasType) as exc:
                errors.append(str(exc))
        return render_template(
            "index.html",
            bias_types=list(BIAS_REGISTRY.values()),
            form=form,
            errors=errors,
            result=result,
            region_labels=REGION_LABELS,
        )

    return app
