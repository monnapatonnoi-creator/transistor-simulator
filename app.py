from __future__ import annotations

from flask import Flask, render_template, request

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
    "rb": "1000",
    "rb_unit": "kohm",
    "rc": "2.2",
    "rc_unit": "kohm",
    "re": "1",
    "re_unit": "kohm",
    "beta": "100",
    "vbe": "0.70",
    "bias_type": "voltage_divider",
}

RESISTOR_FIELDS = ("r1", "r2", "rb", "rc", "re")


def _to_ohms(raw: str, unit: str) -> float:
    if unit == "kohm":
        return float(raw) * 1000.0
    if unit == "ohm":
        return float(raw)
    raise ValueError(f"Unknown unit: {unit}")


def _parse_request(form, required: tuple[str, ...]):
    """Return (BiasParams, []) or (None, [error messages]). Parse only needed fields."""
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

    values = {f: 0.0 for f in RESISTOR_FIELDS}
    for field in RESISTOR_FIELDS:
        if field in required:
            values[field] = resistor(field)

    vcc = number("vcc")
    beta = number("beta")
    vbe = number("vbe")
    if errors:
        return None, errors
    try:
        params = BiasParams(
            vcc=vcc, r1=values["r1"], r2=values["r2"], rb=values["rb"],
            rc=values["rc"], re=values["re"], beta=beta, vbe=vbe,
        )
    except TypeError:
        return None, errors
    return params, []


def _form_from(source) -> dict:
    form = DEFAULTS.copy()
    for key in DEFAULTS:
        value = source.get(key)
        if value is not None:
            form[key] = value
    return form


def create_app() -> Flask:
    app = Flask(__name__)
    app.jinja_env.filters["fmt_current"] = fmt_current
    app.jinja_env.filters["fmt_voltage"] = fmt_voltage
    app.jinja_env.filters["fmt_resistance"] = fmt_resistance

    @app.get("/")
    def index():
        active = request.args.get("bias_type", "voltage_divider")
        if active not in BIAS_REGISTRY:
            active = "voltage_divider"
        visible_fields = set(BIAS_REGISTRY[active].required)
        return render_template(
            "index.html",
            bias_types=list(BIAS_REGISTRY.values()),
            form=_form_from(request.args),
            active_bias=active,
            visible_fields=visible_fields,
            errors=[],
            result=None,
            region_labels=REGION_LABELS,
        )

    @app.post("/calculate", endpoint="calculate_bias")
    def calculate_bias():
        form = request.form
        active = form.get("bias_type", "voltage_divider")
        bias = BIAS_REGISTRY.get(active)
        required = bias.required if bias else ()
        params, errors = _parse_request(form, required)
        result = None
        if params is not None:
            try:
                result = calculate(active, params)
            except (BiasInputError, UnknownBiasType) as exc:
                errors.append(str(exc))
        return render_template(
            "index.html",
            bias_types=list(BIAS_REGISTRY.values()),
            form=form,
            active_bias=active,
            visible_fields=set(required),
            errors=errors,
            result=result,
            region_labels=REGION_LABELS,
        )

    return app
