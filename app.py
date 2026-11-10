from __future__ import annotations

from flask import Flask, redirect, render_template, request, url_for

from dc_bias import BIAS_REGISTRY, REGION_LABELS, BiasParams, calculate
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

    def _to_ohms(raw: str, unit: str) -> float:
        if unit == "kohm":
            return float(raw) * 1000.0
        if unit == "ohm":
            return float(raw)
        raise ValueError(f"Unknown unit: {unit}")

    @app.post("/calculate", endpoint="calculate_bias")
    def calculate_bias():
        form = request.form
        params = BiasParams(
            vcc=float(form["vcc"]),
            r1=_to_ohms(form["r1"], form.get("r1_unit", "kohm")),
            r2=_to_ohms(form["r2"], form.get("r2_unit", "kohm")),
            rc=_to_ohms(form["rc"], form.get("rc_unit", "kohm")),
            re=_to_ohms(form["re"], form.get("re_unit", "kohm")),
            beta=float(form["beta"]),
            vbe=float(form["vbe"]),
        )
        result = calculate(form.get("bias_type", ""), params)
        return render_template(
            "index.html",
            bias_types=list(BIAS_REGISTRY.values()),
            form=form,
            errors=[],
            result=result,
            region_labels=REGION_LABELS,
        )

    return app
