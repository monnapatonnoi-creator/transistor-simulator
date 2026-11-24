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
from markupsafe import Markup
from plots import bode_svg, waveform_svg
from spice_engine import (
    ANALYSES,
    InvalidInput,
    SimInput,
    SpiceError,
    run_analysis,
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

SIM_DEFAULTS = {
    "analysis": "dc",
    "sim_vcc": "12",
    "sim_r1": "100",
    "sim_r2": "22",
    "sim_rc": "2.2",
    "sim_re": "1",
    "sim_rl": "10",
    "sim_cin_uf": "10",
    "sim_cout_uf": "10",
    "sim_amplitude_mv": "10",
    "sim_freq_khz": "1",
}


def _sim_form_from(source) -> dict:
    form = SIM_DEFAULTS.copy()
    for key in SIM_DEFAULTS:
        value = source.get(key)
        if value is not None:
            form[key] = value
    return form


def _parse_sim_form(form):
    """Convert the SPICE form to validated SI values; no physics happens here."""
    errors: list[str] = []
    analysis = form.get("analysis", "dc")
    if analysis not in ANALYSES:
        errors.append("analysis must be dc, ac or tran")

    def number(field: str, scale: float) -> float | None:
        raw = (form.get(field) or "").strip()
        try:
            return float(raw) * scale
        except ValueError:
            errors.append(f"{field} must be a number")
            return None

    values = {
        "vcc": number("sim_vcc", 1.0),
        "r1": number("sim_r1", 1000.0),
        "r2": number("sim_r2", 1000.0),
        "rc": number("sim_rc", 1000.0),
        "re": number("sim_re", 1000.0),
        "rl": number("sim_rl", 1000.0),
        "cin_f": number("sim_cin_uf", 1e-6),
        "cout_f": number("sim_cout_uf", 1e-6),
        "amplitude_v": number("sim_amplitude_mv", 1e-3),
        "freq_hz": number("sim_freq_khz", 1000.0),
    }
    if errors:
        return analysis, None, errors
    try:
        return analysis, SimInput(**values), errors
    except (InvalidInput, SpiceError) as exc:
        return analysis, None, [str(exc)]


def _to_ohms(raw: str, unit: str) -> float:
    if unit == "mohm":
        return float(raw) * 1_000_000.0
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
        # A field hidden in the current mode travels as carry_* so switching back
        # restores it instead of silently falling back to the default.
        carried = source.get("carry_" + key)
        if carried is not None:
            form[key] = carried
    return form


def _lab3_form(source) -> dict:
    """Lab 3 fields carried through /simulate so its result is not lost."""
    form = _form_from(source)
    return {key: form[key] for key in DEFAULTS}


def _analytical_state(form):
    """Return (active, visible_fields, result, errors) for one Lab 3 form."""
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
    return active, set(required), result, errors


def create_app() -> Flask:
    app = Flask(__name__)
    app.jinja_env.filters["fmt_current"] = fmt_current
    app.jinja_env.filters["fmt_voltage"] = fmt_voltage
    app.jinja_env.filters["fmt_resistance"] = fmt_resistance

    def render_index(**overrides):
        context = {
            "bias_types": list(BIAS_REGISTRY.values()),
            "form": DEFAULTS.copy(),
            "active_bias": "voltage_divider",
            "visible_fields": set(BIAS_REGISTRY["voltage_divider"].required),
            "errors": [],
            "result": None,
            "region_labels": REGION_LABELS,
            "sim": None,
            "sim_form": SIM_DEFAULTS.copy(),
            "sim_errors": [],
            "sim_status": "",
            "sim_plots": {"mag": Markup(""), "wave": Markup("")},
            "lab3_hidden": _lab3_form({}),
            "lab3_has_result": False,
        }
        context.update(overrides)
        return render_template("index.html", **context)

    @app.get("/")
    def index():
        active = request.args.get("bias_type", "voltage_divider")
        if active not in BIAS_REGISTRY:
            active = "voltage_divider"
        visible_fields = set(BIAS_REGISTRY[active].required)
        return render_index(
            form=_form_from(request.args),
            active_bias=active,
            visible_fields=visible_fields,
            lab3_hidden=_lab3_form(request.args),
        )

    @app.post("/calculate", endpoint="calculate_bias")
    def calculate_bias():
        form = request.form
        active, required, result, errors = _analytical_state(form)
        return render_index(
            form=_form_from(form),
            active_bias=active if active in BIAS_REGISTRY else "voltage_divider",
            visible_fields=required,
            errors=errors,
            result=result,
            lab3_hidden=_lab3_form(form),
            lab3_has_result=result is not None,
        )

    @app.post("/simulate", endpoint="simulate")
    def simulate():
        analysis, params, errors = _parse_sim_form(request.form)
        sim = None
        plots = {"mag": Markup(""), "wave": Markup("")}
        status = "Error"
        if params is not None:
            try:
                sim = run_analysis(params, analysis)
            except SpiceError as exc:
                errors.append(str(exc))
            else:
                status = "Success"
                if sim.ac:
                    plots["mag"] = bode_svg(sim.ac, sim.cutoff_hz)
                if sim.tran:
                    plots["wave"] = waveform_svg(sim.tran)
        form = request.form
        # The SPICE form carries the last calculated Lab 3 state in lab3_*
        # fields; recompute it so a successful or failed run cannot erase it.
        lab3 = _lab3_form(dict(form))
        if form.get("lab3_has_result") == "1":
            active, required, result, _ = _analytical_state(lab3)
        else:
            active, required, result = "voltage_divider", set(), None
        return render_index(
            form=lab3,
            active_bias=active if active in BIAS_REGISTRY else "voltage_divider",
            visible_fields=required,
            result=result,
            sim=sim,
            sim_form=_sim_form_from(form),
            sim_errors=errors,
            sim_status=status,
            sim_plots=plots,
            lab3_hidden=lab3,
            lab3_has_result=result is not None,
        )

    return app
