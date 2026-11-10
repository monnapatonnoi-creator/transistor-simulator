# Coding conventions (for AI sessions and future contributors)

## Layer rules

- **`dc_bias.py`** — pure Python: dataclasses, equations, validation, registry.
  It knows nothing about Flask, HTML, or HTTP. No imports from `flask`.
- **`app.py`** — Flask only: parses forms, converts units, calls `dc_bias.calculate()`,
  renders templates. No physics equations here.
- **`templates/*.html`** — Jinja display only. No physics formulas, no numeric
  results hard-coded except form defaults and unit labels.
- **`units.py`** — formatting helper: SI value → `12.3 µA`, `18.0 kΩ`, etc.

## Adding a bias type (W3+)

1. Add a function `fn(p: BiasParams) -> BiasResult` in `dc_bias.py` (or a new
   `bias/` module).
2. Register it in `BIAS_REGISTRY` with `BiasType(key, label, fn)`.
3. Add its own unit tests in `tests/test_dc_bias.py`.
4. **Do not edit `app.py` or `templates/index.html`** — the `bias_type` dropdown
   loops over the registry.

## Units and naming

- SI inside the model: volts, ohms, amperes. kΩ→Ω conversion happens in `app.py`.
- Region keys: `"active"`, `"cutoff"`, `"saturation"` (lowercase).
- Display labels come only from `REGION_LABELS`.

## Commits

- One commit per task: `feat:`, `test:`, `docs:`, `chore:`.
- Never commit `.venv/`, `__pycache__/`, `*.pyc`, `.env`, credentials.
- Run `python -m unittest discover -s tests -v` before claiming a task done.
- If you fix anything, write the failing test first (TDD).
