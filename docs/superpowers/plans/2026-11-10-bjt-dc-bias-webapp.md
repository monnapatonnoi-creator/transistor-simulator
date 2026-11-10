# BJT DC Bias Web App Implementation Plan (Lab 2 / W2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a runnable multi-file Flask app that computes the DC operating point of a voltage-divider-biased BJT from browser input, with validation, region warnings, and automated tests.

**Architecture:** One pure-Python engineering module (`dc_bias.py`) owns `BiasParams`, `BiasResult`, validation, the equation set, and a bias-type registry; Flask (`app.py`) only parses forms, converts units, calls `calculate()`, and renders one template. A formatting module (`units.py`) turns SI floats into display strings. W3+ add bias types through the registry without touching route or template.

**Tech Stack:** Python 3.14, Flask ≥3.0 <4, Jinja2 templates, plain CSS, `unittest` (stdlib) only, no JavaScript.

**Spec:** `docs/superpowers/specs/2026-11-10-bjt-dc-bias-webapp-design.md`

## Global Constraints

- Python 3.14.2 at `C:\Program Files\Python314`; venv at `.venv`. `pip install -r requirements.txt` must be the only install step.
- `requirements.txt` contains exactly `Flask>=3.0,<4`. No pytest, no numpy, no JS tooling.
- SI units inside `dc_bias.py`: volts, ohms, amperes. Unit conversion (kΩ→Ω) happens in `app.py` only. `dc_bias.py` never sees a unit string.
- Every number on screen is computed by the backend in this request. No numeric literal may appear in a template except form defaults and unit labels.
- Validation errors re-render the page with **HTTP 200**, preserve submitted values, and show messages. Unknown routes stay 404.
- Region is a label, never a correction: the forward-active equations always run and their raw values are displayed, de-emphasised, when the region is not `active`.
- Thresholds: `VCE_SAT = 0.2` V; `cutoff` when `IB <= 0` or `VTH <= VBE`; extra warning when `VCE > VCC`.
- Display: 3 significant figures, explicit units (`V`, `mA`, `µA`, `A`, `Ω`, `kΩ`), never scientific notation.
- UI copy and error strings are **English** (tests assert them verbatim).
- Layout must remain usable at 360 px width; no framework, no JS.
- Commits go through **GitHub Desktop**, one per task, prefixes `feat:`, `test:`, `docs:`, `chore:`.
- Never commit `.venv/`, `__pycache__/`, `.env`, or credentials.

## Review Focus

1. **Non-numeric / blank / whitespace input in any field** — the user expects a plain error message on the same page; the program must not return 500. Pinned in Task 7 (`vcc=abc`, `vcc="   "`).
2. **Zero or negative component values** — a user typing `R2 = 0` expects "must be greater than zero", not `ZeroDivisionError`. Pinned in Task 2.
3. **Hostile form fields** — unknown `bias_type`, unknown unit token, missing unit field: error, not a crash or a silent wrong answer. Pinned in Tasks 5 and 7.
4. **Boundary region cases** — `VTH` exactly equal to `VBE` (IB = 0) must be labelled `cutoff`, never a division by zero or a bogus `active` verdict. Pinned in Task 3.
5. **Extreme magnitudes** — 470 Ω to 10 MΩ and currents near 1 µA must render in engineering units with 3 significant figures, never `1.23e-05`. Pinned in Task 4.

---

### Task 1: Engineering core — parameters, result model, voltage-divider math

**Files:**
- Create: `.gitignore`, `requirements.txt`, `dc_bias.py`, `tests/test_dc_bias.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `BiasInputError(ValueError)`, `UnknownBiasType(ValueError)`, `BiasParams` (frozen dataclass: `vcc, r1, r2, rc, re, beta, vbe=0.70`), `BiasResult` (frozen dataclass: `bias_type: str, vth, rth, ib, ic, ie, vb, ve, vc, vce: float, region: str, warnings: tuple[str, ...]`), `BIAS_REGISTRY: dict[str, BiasType]`, `BiasType` (frozen dataclass: `key: str, label: str, fn: Callable[[BiasParams], BiasResult]`), `voltage_divider(p: BiasParams) -> BiasResult`, `VCE_SAT: float`.

- [ ] **Step 1: Create the repository in GitHub Desktop (manual, student)**

`File → Add local repository…` → choose `C:\Users\b6829162\Documents\Default Project\transistor-simulator` → when prompted, create the repository → `Publish repository`. Do not add a README from the app.

- [ ] **Step 2: Create the venv and install the dependency**

```powershell
cd "C:\Users\b6829162\Documents\Default Project\transistor-simulator"
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install "Flask>=3.0,<4"
python -c "import flask; print(flask.__version__)"
```

Expected: a `3.x` version prints. If `python` is not recognised, add `C:\Program Files\Python314` and `...\Python314\Scripts` to the user PATH, reopen the terminal, and retry.

- [ ] **Step 3: Write `.gitignore` and `requirements.txt`**

`.gitignore`: `.venv/`, `__pycache__/`, `*.pyc`, `.env`, `.pytest_cache/`
`requirements.txt`: one line, `Flask>=3.0,<4`

- [ ] **Step 4: Write the failing reference test**

```python
# tests/test_dc_bias.py
import unittest
from dc_bias import BiasParams, voltage_divider

REFERENCE = BiasParams(vcc=12.0, r1=100e3, r2=22e3, rc=2.2e3, re=1e3, beta=100.0, vbe=0.70)

class TestVoltageDivider(unittest.TestCase):
    def test_reference_operating_point(self):
        r = voltage_divider(REFERENCE)
        self.assertAlmostEqual(r.vth, 2.1639344262, places=8)
        self.assertAlmostEqual(r.rth, 18032.786885, delta=1e-3)
        self.assertAlmostEqual(r.ib, 1.229858e-05, delta=1e-11)
        self.assertAlmostEqual(r.ic, 1.229858e-03, delta=1e-9)
        self.assertAlmostEqual(r.ie, 1.242157e-03, delta=1e-9)
        self.assertAlmostEqual(r.ve, 1.2421567277, places=6)
        self.assertAlmostEqual(r.vb, 1.9421567277, places=6)
        self.assertAlmostEqual(r.vc, 9.2943120782, places=6)
        self.assertAlmostEqual(r.vce, 8.0521553505, places=6)
        self.assertEqual(r.region, "active")
        self.assertEqual(r.warnings, ())

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 5: Run it and confirm it fails**

Run: `.venv\Scripts\python.exe -m unittest tests.test_dc_bias -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'dc_bias'` (or ImportError).

- [ ] **Step 6: Implement `dc_bias.py`**

Implement the two dataclasses, `BiasType`, `BIAS_REGISTRY = {"voltage_divider": BiasType("voltage_divider", "Voltage Divider", voltage_divider)}`, `VCE_SAT = 0.2`, `REGION_LABELS = {"active": "Forward Active", "cutoff": "Cutoff", "saturation": "Saturation"}`, and `voltage_divider()` using exactly the spec's equations. Set `region="active"` and `warnings=()` for now (Task 3 owns classification). Raise the two exception classes (bodies may be `pass`; they are raised in Task 2).

- [ ] **Step 7: Run the test and confirm it passes**

Run: `.venv\Scripts\python.exe -m unittest tests.test_dc_bias -v`
Expected: `OK` (1 test).

- [ ] **Step 8: Commit (GitHub Desktop)**

Summary: `feat: add BJT voltage-divider DC bias model`
Files: `dc_bias.py`, `tests/test_dc_bias.py`, `requirements.txt`, `.gitignore`, `docs/superpowers/specs/2026-11-10-bjt-dc-bias-webapp-design.md`

---

### Task 2: Input validation

**Files:**
- Modify: `dc_bias.py`
- Test: `tests/test_dc_bias.py`

**Interfaces:**
- Consumes: `BiasParams`, `BiasInputError`, `UnknownBiasType`, `BIAS_REGISTRY`.
- Produces: `validate_params(p: BiasParams) -> None` (raises `BiasInputError`), `calculate(bias_type: str, p: BiasParams) -> BiasResult` (validates, dispatches, raises `UnknownBiasType`).

- [ ] **Step 1: Write the failing tests**

```python
# append to tests/test_dc_bias.py
from dc_bias import BiasInputError, UnknownBiasType, calculate

class TestValidation(unittest.TestCase):
    def test_zero_resistor_rejected(self):
        p = BiasParams(vcc=12.0, r1=100e3, r2=0.0, rc=2.2e3, re=1e3, beta=100.0)
        with self.assertRaises(BiasInputError) as ctx:
            calculate("voltage_divider", p)
        self.assertIn("r2 must be greater than zero", str(ctx.exception))

    def test_zero_beta_rejected(self):
        p = BiasParams(vcc=12.0, r1=100e3, r2=22e3, rc=2.2e3, re=1e3, beta=0.0)
        with self.assertRaises(BiasInputError) as ctx:
            calculate("voltage_divider", p)
        self.assertIn("beta must be greater than zero", str(ctx.exception))

    def test_negative_vcc_rejected(self):
        p = BiasParams(vcc=-1.0, r1=100e3, r2=22e3, rc=2.2e3, re=1e3, beta=100.0)
        with self.assertRaises(BiasInputError) as ctx:
            calculate("voltage_divider", p)
        self.assertIn("vcc must be greater than zero", str(ctx.exception))

    def test_vbe_at_or_above_vcc_rejected(self):
        p = BiasParams(vcc=12.0, r1=100e3, r2=22e3, rc=2.2e3, re=1e3, beta=100.0, vbe=12.0)
        with self.assertRaises(BiasInputError) as ctx:
            calculate("voltage_divider", p)
        self.assertIn("vbe must be less than vcc", str(ctx.exception))

    def test_unknown_bias_type_rejected(self):
        with self.assertRaises(UnknownBiasType):
            calculate("fixed_bias", REFERENCE)

    def test_registry_contains_voltage_divider(self):
        self.assertIn("voltage_divider", BIAS_REGISTRY)
```

- [ ] **Step 2: Run and confirm failure**

Run: `.venv\Scripts\python.exe -m unittest tests.test_dc_bias -v`
Expected: FAIL — `ImportError: cannot import name 'calculate'` / `BiasInputError` not raised.

- [ ] **Step 3: Implement validation and dispatch in `dc_bias.py`**

`validate_params` checks, in this order, and raises `BiasInputError` with the first failure:
`vcc > 0`, `r1 > 0`, `r2 > 0`, `rc > 0`, `re > 0`, `beta > 0`, `vbe >= 0`, `vbe < vcc`.
Message format: `f"{field} must be greater than zero"`, or `"vbe must be less than vcc"`.
`calculate` raises `UnknownBiasType(f"Unknown bias type: {bias_type}")` when the key is absent, then calls `validate_params`, then `BIAS_REGISTRY[bias_type].fn(p)`.

- [ ] **Step 4: Run and confirm all pass**

Run: `.venv\Scripts\python.exe -m unittest tests.test_dc_bias -v`
Expected: `OK` (7 tests).

- [ ] **Step 5: Commit (GitHub Desktop)**

Summary: `feat: validate component values before calculation`
Files: `dc_bias.py`, `tests/test_dc_bias.py`

---

### Task 3: Operating-region classification and warnings

**Files:**
- Modify: `dc_bias.py`
- Test: `tests/test_dc_bias.py`

**Interfaces:**
- Consumes: `BiasParams`, `BiasResult`, `calculate`, `VCE_SAT`, `REGION_LABELS`.
- Produces: `classify_region(p: BiasParams, r: BiasResult) -> tuple[str, tuple[str, ...]]`; `calculate()` now returns a `BiasResult` whose `region`/`warnings` come from `classify_region`, values untouched.

- [ ] **Step 1: Write the failing tests**

```python
# append to tests/test_dc_bias.py
from dc_bias import REGION_LABELS, VCE_SAT

CUTOFF = BiasParams(vcc=5.0, r1=100e3, r2=5e3, rc=2.2e3, re=1e3, beta=100.0, vbe=0.70)
SATURATED = BiasParams(vcc=12.0, r1=100e3, r2=22e3, rc=10e3, re=1e3, beta=100.0, vbe=0.70)

class TestRegion(unittest.TestCase):
    def test_cutoff_labelled_and_values_left_raw(self):
        r = calculate("voltage_divider", CUTOFF)
        self.assertEqual(r.region, "cutoff")
        self.assertTrue(r.warnings)
        self.assertAlmostEqual(r.ib, -4.367402e-06, delta=1e-11)   # raw, negative, not corrected
        self.assertAlmostEqual(r.vce, 6.401936, places=5)

    def test_saturation_labelled_and_values_left_raw(self):
        r = calculate("voltage_divider", SATURATED)
        self.assertEqual(r.region, "saturation")
        self.assertTrue(r.warnings)
        self.assertAlmostEqual(r.vce, -1.540738, places=5)          # VCE <= VCE_SAT
        self.assertLess(r.vce, VCE_SAT)

    def test_ib_exactly_zero_is_cutoff(self):
        # Deliberate exact-arithmetic boundary case: VTH = 1.0*3/(1+3) = 0.75 exactly,
        # VBE = 0.75 exactly, so IB = 0.0 and the region must be cutoff, not active.
        p = BiasParams(vcc=1.0, r1=1.0, r2=3.0, rc=100.0, re=100.0, beta=100.0, vbe=0.75)
        r = calculate("voltage_divider", p)
        self.assertEqual(r.ib, 0.0)
        self.assertEqual(r.region, "cutoff")
        self.assertTrue(r.warnings)

    def test_active_has_no_warnings(self):
        r = calculate("voltage_divider", REFERENCE)
        self.assertEqual(r.region, "active")
        self.assertEqual(r.warnings, ())

    def test_region_labels_cover_every_region(self):
        self.assertEqual(REGION_LABELS["active"], "Forward Active")
        self.assertEqual(set(REGION_LABELS), {"active", "cutoff", "saturation"})
```

- [ ] **Step 2: Run and confirm failure**

Run: `.venv\Scripts\python.exe -m unittest tests.test_dc_bias -v`
Expected: FAIL — cutoff case reports `active`; `VCE_SAT`/`REGION_LABELS` import may fail if not yet defined.

- [ ] **Step 3: Implement `classify_region` and use it in `calculate`**

Rules, first match wins, verdict is a label only:
1. `r.ib <= 0 or r.vth <= p.vbe` → `"cutoff"`, warning `"Device is off (VTH <= VBE). Forward-active equations do not apply; these values are not usable."`
2. `r.vce <= VCE_SAT` → `"saturation"`, warning `"Device is in saturation (VCE <= 0.2 V). Forward-active equations do not apply; these values are not usable."`
3. else `"active"`, no warning.
Then, independently, if `r.vce > p.vcc`, append `"VCE exceeds VCC; the forward-active result is physically implausible."`.
Return the result with `dataclasses.replace(result, region=region, warnings=tuple(warnings))`.

- [ ] **Step 4: Run and confirm all pass**

Run: `.venv\Scripts\python.exe -m unittest tests.test_dc_bias -v`
Expected: `OK` (12 tests).

- [ ] **Step 5: Commit (GitHub Desktop)**

Summary: `feat: classify cutoff, saturation and active regions`
Files: `dc_bias.py`, `tests/test_dc_bias.py`

---

### Task 4: Engineering-unit formatting

**Files:**
- Create: `units.py`, `tests/test_units.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `fmt_current(amperes: float) -> str`, `fmt_voltage(volts: float) -> str`, `fmt_resistance(ohms: float) -> str`, and `_sig(value: float, digits: int = 3) -> str` (3 significant figures, trailing zeros kept, `-0.0` normalised to `0`).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_units.py
import unittest
from units import fmt_current, fmt_resistance, fmt_voltage

class TestFormatting(unittest.TestCase):
    def test_microamp_range(self):
        self.assertEqual(fmt_current(1.229858e-05), "12.3 µA")
        self.assertEqual(fmt_current(-4.367402e-06), "-4.37 µA")

    def test_milliamp_range(self):
        self.assertEqual(fmt_current(1.229858e-03), "1.23 mA")
        self.assertEqual(fmt_current(1.060325e-03), "1.06 mA")

    def test_amp_range(self):
        self.assertEqual(fmt_current(0.5), "500 mA")

    def test_voltage_three_sig_figs(self):
        self.assertEqual(fmt_voltage(8.0521553505), "8.05 V")
        self.assertEqual(fmt_voltage(12.0), "12.0 V")

    def test_resistance_ranges(self):
        self.assertEqual(fmt_resistance(18032.786885), "18.0 kΩ")
        self.assertEqual(fmt_resistance(1000.0), "1.00 kΩ")
        self.assertEqual(fmt_resistance(470.0), "470 Ω")
        self.assertEqual(fmt_resistance(10e6), "10.0 MΩ")

    def test_no_scientific_notation(self):
        for text in (fmt_current(1e-7), fmt_resistance(10e6), fmt_voltage(1e-3)):
            self.assertNotIn("e", text.replace("µ", "").lower())

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run and confirm failure**

Run: `.venv\Scripts\python.exe -m unittest tests.test_units -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'units'`.

- [ ] **Step 3: Implement `units.py`**

Selection rule uses `abs(value)`: current `< 1e-3` → µA (`value*1e6`), `< 1` → mA (`value*1e3`), else A. Resistance `>= 1e6` → MΩ, `>= 1e3` → kΩ, else Ω. Voltage always V. Each string is `_sig(value, 3) + " " + unit`, where `_sig` uses `f"{value:.3g}"` and pads trailing zeros so exactly 3 significant digits show when the value is non-zero (e.g. `12` → `12.0`, `1` → `1.00`); zero renders `0`.

- [ ] **Step 4: Run and confirm all pass**

Run: `.venv\Scripts\python.exe -m unittest tests.test_units -v`
Expected: `OK` (6 tests).

- [ ] **Step 5: Commit (GitHub Desktop)**

Summary: `feat: format SI values with engineering units`
Files: `units.py`, `tests/test_units.py`

---

### Task 5: Flask shell, GET form, registry-driven bias select

**Files:**
- Create: `app.py`, `templates/base.html`, `templates/index.html`, `static/style.css`, `tests/test_web.py`

**Interfaces:**
- Consumes: `BIAS_REGISTRY`, `BiasParams`, `REGION_LABELS`, `fmt_*` from Tasks 1–4.
- Produces: `create_app() -> Flask`; route `GET /` → `render_template("index.html", bias_types=list(BIAS_REGISTRY.values()), form=DEFAULTS, errors=[], result=None)`; `DEFAULTS = {"vcc": "12", "r1": "100", "r1_unit": "kohm", "r2": "22", "r2_unit": "kohm", "rc": "2.2", "rc_unit": "kohm", "re": "1", "re_unit": "kohm", "beta": "100", "vbe": "0.70", "bias_type": "voltage_divider"}`; Jinja filters `fmt_current`, `fmt_voltage`, `fmt_resistance` registered on the app.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_web.py
import unittest
from app import create_app, DEFAULTS
from dc_bias import BIAS_REGISTRY

class TestIndexPage(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def test_get_index_returns_form(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        body = resp.get_data(as_text=True)
        for field in ("vcc", "r1", "r2", "rc", "re", "beta", "vbe", "bias_type"):
            self.assertIn(f'name="{field}"', body)
        self.assertNotIn('data-testid="result-panel"', body)

    def test_defaults_prefilled_in_kohm(self):
        body = self.client.get("/").get_data(as_text=True)
        self.assertIn('value="12"', body)
        self.assertIn('value="100"', body)
        self.assertIn('value="22"', body)
        self.assertIn('value="2.2"', body)
        self.assertIn('value="0.70"', body)
        self.assertIn('<option value="kohm" selected', body)

    def test_bias_options_come_from_registry(self):
        body = self.client.get("/").get_data(as_text=True)
        for key in BIAS_REGISTRY:
            self.assertIn(f'<option value="{key}"', body)

    def test_stylesheet_is_linked(self):
        body = self.client.get("/").get_data(as_text=True)
        self.assertIn('/static/style.css', body)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run and confirm failure**

Run: `.venv\Scripts\python.exe -m unittest tests.test_web -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app'`.

- [ ] **Step 3: Implement the app shell and templates**

`app.py`: `create_app()` builds `Flask(__name__)`, registers the three Jinja filters from `units`, defines `DEFAULTS`, and the `GET /` route. No calculation logic.
`templates/base.html`: `<!doctype html>`, `<meta name="viewport" content="width=device-width, initial-scale=1">`, `<link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">`, header "BJT DC Bias", `{% block content %}{% endblock %}`, footer line stating the model assumption ("fixed β, fixed VBE, forward-active approximation; not a SPICE simulation").
`templates/index.html`: extends base; a `<form method="post" action="{{ url_for('calculate_bias') }}">`; a `<select name="bias_type" data-testid="bias-type">` looping `bias_types` with `option.key`/`option.label`; number inputs `vcc`, `r1`, `r2`, `rc`, `re`, `beta`, `vbe` with `step="any"`, each resistor paired with `<select name="rN_unit">` whose options are written as `<option value="kohm"{% if form.rN_unit == 'kohm' %} selected{% endif %}>` (same for `ohm`); a submit button "Calculate DC Bias". No result markup yet (Task 6) and no numbers typed into the template beyond `form.*` values.
`static/style.css`: one column, max-width 760px, system font stack, 360 px-safe, form rows as grid, `.error` red block, `.warning` amber block, `.muted` for de-emphasised values, `.mono` for numeric cells.

- [ ] **Step 4: Run and confirm all pass**

Run: `.venv\Scripts\python.exe -m unittest tests.test_web -v`
Expected: `OK` (4 tests).

- [ ] **Step 5: Sanity-check in the browser**

Run: `.venv\Scripts\python.exe -m flask --app app run --debug` then open `http://127.0.0.1:5000/`.
Expected: form visible with 12 / 100 / 22 / 2.2 / 1 / 100 / 0.70 pre-filled, one bias option, no result panel. Stop the server.

- [ ] **Step 6: Commit (GitHub Desktop)**

Summary: `feat: add Flask shell with bias input form`
Files: `app.py`, `templates/base.html`, `templates/index.html`, `static/style.css`, `tests/test_web.py`

---

### Task 6: POST /calculate — success path and result panel

**Files:**
- Modify: `app.py`, `templates/index.html`
- Test: `tests/test_web.py`

**Interfaces:**
- Consumes: `calculate`, `BiasParams`, `fmt_*`, `REGION_LABELS`, `DEFAULTS`.
- Produces: `POST /calculate` (endpoint name `calculate_bias`) rendering `index.html` with `result: BiasResult | None`; helper `_to_ohms(raw: str, unit: str) -> float`; result panel markup with `data-testid="result-panel"`, rows for VTH, RTH, IB, IC, IE, VB, VE, VC, VCE, and a `data-testid="region"` element containing the label from `REGION_LABELS`.

- [ ] **Step 1: Write the failing tests**

```python
# append to tests/test_web.py
REFERENCE_FORM = {
    "bias_type": "voltage_divider", "vcc": "12",
    "r1": "100", "r1_unit": "kohm", "r2": "22", "r2_unit": "kohm",
    "rc": "2.2", "rc_unit": "kohm", "re": "1", "re_unit": "kohm",
    "beta": "100", "vbe": "0.70",
}

class TestCalculate(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def test_reference_case_renders_backend_values(self):
        resp = self.client.post("/calculate", data=REFERENCE_FORM)
        self.assertEqual(resp.status_code, 200)
        body = resp.get_data(as_text=True)
        self.assertIn('data-testid="result-panel"', body)
        self.assertIn("8.05 V", body)      # VCE
        self.assertIn("1.23 mA", body)     # IC
        self.assertIn("12.3 µA", body)     # IB
        self.assertIn("18.0 kΩ", body)     # RTH
        self.assertIn("Forward Active", body)

    def test_beta_changes_result(self):
        form = dict(REFERENCE_FORM, beta="50")
        body = self.client.post("/calculate", data=form).get_data(as_text=True)
        self.assertIn("1.06 mA", body)
        self.assertNotIn("1.23 mA", body)
```

- [ ] **Step 2: Run and confirm failure**

Run: `.venv\Scripts\python.exe -m unittest tests.test_web -v`
Expected: FAIL — 404 (no `calculate_bias` route) or missing result panel.

- [ ] **Step 3: Implement the route and parsing**

`_to_ohms(raw, unit)`: `"kohm"` → `float(raw) * 1000`, `"ohm"` → `float(raw)`, anything else raises `ValueError`. Missing unit falls back to `"kohm"`.
Route: read the form with `request.form`, build `BiasParams` (missing field → `""`, which fails `float()`), call `calculate(form.get("bias_type", ""), params)`, and render the page with `result=...` and `form=<submitted values>`. Task 7 adds error handling around this; for now let exceptions propagate.
`index.html`: after the form, `{% if result %}` render `data-testid="result-panel"` with a `<table>`; use `result.vth|fmt_voltage`, `result.rth|fmt_resistance`, `result.ib|fmt_current`, `result.ic|fmt_current`, `result.ie|fmt_current`, `result.vb|fmt_voltage`, `result.ve|fmt_voltage`, `result.vc|fmt_voltage`, `result.vce|fmt_voltage`; region label in `data-testid="region"` via `{{ region_labels[result.region] }}`; pass `region_labels=REGION_LABELS` from the route.

- [ ] **Step 4: Run and confirm all pass**

Run: `.venv\Scripts\python.exe -m unittest tests.test_web -v`
Expected: `OK` (6 tests).

- [ ] **Step 5: Commit (GitHub Desktop)**

Summary: `feat: calculate DC bias on POST and render results`
Files: `app.py`, `templates/index.html`, `tests/test_web.py`

---

### Task 7: Validation errors on the web layer

**Files:**
- Modify: `app.py`, `templates/index.html`
- Test: `tests/test_web.py`

**Interfaces:**
- Consumes: `BiasInputError`, `UnknownBiasType`, `_to_ohms`, `DEFAULTS`.
- Produces: `_parse_request(form) -> tuple[BiasParams | None, list[str]]` in `app.py`; error block with `data-testid="error-block"`; all validation failures render with HTTP 200 and `result=None`.

- [ ] **Step 1: Write the failing tests**

```python
# append to tests/test_web.py
class TestValidationWeb(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def test_zero_beta_shows_error(self):
        resp = self.client.post("/calculate", data=dict(REFERENCE_FORM, beta="0"))
        self.assertEqual(resp.status_code, 200)
        body = resp.get_data(as_text=True)
        self.assertIn('data-testid="error-block"', body)
        self.assertIn("beta must be greater than zero", body)
        self.assertNotIn('data-testid="result-panel"', body)

    def test_non_numeric_vcc_shows_error(self):
        resp = self.client.post("/calculate", data=dict(REFERENCE_FORM, vcc="abc"))
        self.assertEqual(resp.status_code, 200)
        body = resp.get_data(as_text=True)
        self.assertIn("vcc must be a number", body)

    def test_whitespace_input_shows_error(self):
        resp = self.client.post("/calculate", data=dict(REFERENCE_FORM, vcc="   "))
        body = resp.get_data(as_text=True)
        self.assertIn("vcc must be a number", body)

    def test_unknown_unit_shows_error(self):
        resp = self.client.post("/calculate", data=dict(REFERENCE_FORM, r1_unit="mega"))
        body = resp.get_data(as_text=True)
        self.assertIn("Unknown unit: mega", body)

    def test_unknown_bias_type_shows_error(self):
        resp = self.client.post("/calculate", data=dict(REFERENCE_FORM, bias_type="fixed_bias"))
        body = resp.get_data(as_text=True)
        self.assertIn("Unknown bias type: fixed_bias", body)

    def test_submitted_values_preserved(self):
        body = self.client.post("/calculate", data=dict(REFERENCE_FORM, beta="0", r1="47")).get_data(as_text=True)
        self.assertIn('value="47"', body)
```

- [ ] **Step 2: Run and confirm failure**

Run: `.venv\Scripts\python.exe -m unittest tests.test_web -v`
Expected: FAIL — 500 responses / missing error block.

- [ ] **Step 3: Implement error collection**

`_parse_request(form)`: convert each numeric field with `float(raw.strip())` inside `try/except ValueError`, adding `f"{field} must be a number"` on failure; convert resistors with `_to_ohms`, adding `f"Unknown unit: {unit}"` for unrecognised units; skip dependent conversions when a field already failed. Return `(None, errors)` if any error, else `(BiasParams(...), [])`.
Route: on `errors` → render with `errors=errors, result=None, form=submitted`; catch `BiasInputError`/`UnknownBiasType` from `calculate` and append `str(exc)` to `errors`, then render the same way. `bias_type` missing or empty → `"Unknown bias type: "` is acceptable; do not crash.
`index.html`: render `data-testid="error-block"` listing `errors` when non-empty.

- [ ] **Step 4: Run and confirm all pass**

Run: `.venv\Scripts\python.exe -m unittest tests.test_web -v`
Expected: `OK` (12 tests).

- [ ] **Step 5: Commit (GitHub Desktop)**

Summary: `feat: show readable errors for invalid input`
Files: `app.py`, `templates/index.html`, `tests/test_web.py`

---

### Task 8: Outside-active presentation (A5)

**Files:**
- Modify: `templates/index.html`, `static/style.css`
- Test: `tests/test_web.py`

**Interfaces:**
- Consumes: `result.region`, `result.warnings`, `REGION_LABELS`.
- Produces: warning block `data-testid="warning-block"` listing every warning; result table carries class `is-invalid` when `result.region != "active"`; a sentence above the table carrying `data-testid="model-caveat"`.

- [ ] **Step 1: Write the failing tests**

```python
# append to tests/test_web.py
CUTOFF_FORM = dict(REFERENCE_FORM, vcc="5", r2="5")
SAT_FORM = dict(REFERENCE_FORM, rc="10")

class TestRegionPresentation(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    def test_cutoff_shows_warning_and_caveat(self):
        body = self.client.post("/calculate", data=CUTOFF_FORM).get_data(as_text=True)
        self.assertIn("Cutoff", body)
        self.assertIn('data-testid="warning-block"', body)
        self.assertIn("do not apply", body)
        self.assertIn('data-testid="model-caveat"', body)
        self.assertIn("is-invalid", body)

    def test_saturation_shows_warning(self):
        body = self.client.post("/calculate", data=SAT_FORM).get_data(as_text=True)
        self.assertIn("Saturation", body)
        self.assertIn('data-testid="warning-block"', body)

    def test_active_has_no_warning_or_caveat(self):
        body = self.client.post("/calculate", data=REFERENCE_FORM).get_data(as_text=True)
        self.assertNotIn('data-testid="warning-block"', body)
        self.assertNotIn('data-testid="model-caveat"', body)
        self.assertNotIn("is-invalid", body)
```

- [ ] **Step 2: Run and confirm failure**

Run: `.venv\Scripts\python.exe -m unittest tests.test_web -v`
Expected: FAIL — warning block and caveat absent.

- [ ] **Step 3: Implement the presentation**

`index.html`: `{% if result.warnings %}` render `data-testid="warning-block"` with one line per warning; `{% if result.region != "active" %}` render `data-testid="model-caveat"` with "These values come from forward-active equations whose assumptions are violated here. Do not use them." and add `is-invalid` to the table's class list. Region line stays high-contrast; table values use `.muted` when `is-invalid`.
`style.css`: `.is-invalid td.value { color: #6b7a88; }` and `.warning { background:#fff4e9; border-left:4px solid #b85c2c; padding:12px; }`, `.error` red equivalent.

- [ ] **Step 4: Run and confirm all pass**

Run: `.venv\Scripts\python.exe -m unittest discover -s tests -v`
Expected: `OK` (33 tests: 18 engineering + 15 web).

- [ ] **Step 5: Commit (GitHub Desktop)**

Summary: `feat: flag results outside the forward-active region`
Files: `templates/index.html`, `static/style.css`, `tests/test_web.py`

---

### Task 9: README, AGENTS.md, validation log and final verification

**Files:**
- Create: `README.md`, `AGENTS.md`, `docs/design-note.md`, `docs/validation.md`, `docs/reflection.md`

**Interfaces:**
- Consumes: everything above.
- Produces: reproducible instructions and the student's written evidence.

- [ ] **Step 1: Write `README.md`**

Sections: What it does; Requirements (Python 3.10+, Flask); Setup (PowerShell block with `python -m venv .venv`, `.venv\Scripts\Activate.ps1`, `python -m pip install -r requirements.txt`); Run (`python -m flask --app app run --debug`, open `http://127.0.0.1:5000/`); Test (`python -m unittest discover -s tests -v`); Model and limitations (fixed β/VBE, forward-active only, values outside the region are labelled not corrected); Project structure; Note that opening `templates/index.html` directly is not supported.

- [ ] **Step 2: Write `AGENTS.md`**

Conventions for future AI sessions: no physics in templates, no Flask in `dc_bias.py`, new bias types go through `BIAS_REGISTRY` with their own tests, SI units internally, commit prefixes, never commit `.venv`/`.env`, run the full test suite before claiming a task done.

- [ ] **Step 3: Write `docs/validation.md`**

Table of the reference case with the independent hand calculation (VTH 2.164 V, RTH 18.03 kΩ, IB 12.30 µA, IC 1.230 mA, IE 1.242 mA, VE 1.242 V, VB 1.942 V, VC 9.294 V, VCE 8.052 V) beside the app's displayed values, plus the cutoff and saturation cases and the warning text observed. Include the date and the command output line `Ran 33 tests ... OK`.

- [ ] **Step 4: Write `docs/design-note.md` and `docs/reflection.md`**

design-note: two paragraphs in the student's own words — the registry approach and why extending to Fixed/Emitter bias in W3 needs no route/template change.
reflection: what was learned about frontend/backend separation, one thing that was hard, one limitation of the forward-active model.

- [ ] **Step 5: Run the full suite and the app**

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe -m flask --app app run --debug
```

Expected: `Ran 33 tests` / `OK`; server starts on 5000. Open the page, submit the reference case, then submit β=0 and a cutoff case, and confirm the three states (result / error / warning) visually. Stop the server.

- [ ] **Step 6: Commit and push (GitHub Desktop)**

Summary: `docs: add README, validation log and reflection`
Files: `README.md`, `AGENTS.md`, `docs/design-note.md`, `docs/validation.md`, `docs/reflection.md`
Then `Push origin`. Record the commit SHA from `History` for submission.

---

## Self-review notes

- Spec §7.1 layout → Tasks 1, 4, 5, 9 (files created); §7.2 model → Tasks 1–3; §7.2 registry-driven select → Task 5 test; §7.3 web → Tasks 5–7; §7.4 seams → registry + `calculate()` indirection; §7.5 presentation → Tasks 5, 6, 8; §7.6 tests → 33 tests across Tasks 1–8 (spec's list is a floor; the plan exceeds it); §7.7 delivery → Task 9; §7.8 prerequisites → Task 1 Steps 1–2.
- Review Focus items 1–5 map to Tasks 7, 2, 5+7, 3, 4 respectively.
- Types are consistent across tasks: `BiasResult.region` is a lowercase key everywhere (`"active" | "cutoff" | "saturation"`); display labels come only from `REGION_LABELS`.
