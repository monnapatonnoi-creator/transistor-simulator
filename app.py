from __future__ import annotations

from flask import Flask, redirect, render_template, request, url_for

from dc_bias import BIAS_REGISTRY, REGION_LABELS, calculate
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

    @app.post("/calculate", endpoint="calculate_bias")
    def calculate_bias():
        # Placeholder: real calculation is implemented in Task 6.
        return redirect(url_for("index"))

    return app
