# BJT DC Bias Web App

A Flask web application that computes the DC operating point of an NPN common-emitter
circuit for three single-supply bias types: **Voltage Divider** (Lab 02), **Fixed Bias**
and **Emitter Bias** (Lab 03), built for ENG29 2121.

## What it does

- Pick a bias type from the dropdown and press **Apply mode**. The page reloads showing
  only the fields that circuit uses — no JavaScript.
  - **Voltage Divider** — `VCC`, `R1`, `R2`, `RC`, `RE`, `β`, `VBE`
  - **Fixed Bias** — `VCC`, `RB`, `RC`, `β`, `VBE` (emitter tied to ground)
  - **Emitter Bias** — `VCC`, `RB`, `RE`, `RC`, `β`, `VBE`
- Resistors accept Ω, kΩ or MΩ (1 MΩ = 1000 kΩ = 1,000,000 Ω). The model keeps SI units internally.
- The backend computes `VTH`, `RTH`, `IB`, `IC`, `IE`, `VB`, `VE`, `VC`, `VCE` and a
  region verdict (Forward Active / Cutoff / Saturation). Invalid input and results
  outside the forward-active assumptions are flagged with readable warnings.
- All numbers come from the backend on every request — nothing is hard-coded in HTML.
- An inline circuit diagram sits above the form and updates while you type: it shows
  only the resistors used by the selected mode and displays the entered values and
  units (`Ω`, `kΩ`, `MΩ`). Press **Calculate DC Bias** to refresh `IC`/`VCE` in the diagram.

## Requirements

- Python 3.10+ (tested with 3.14.2)
- Flask ≥3.0, <4

## Setup (Windows PowerShell)

```powershell
cd transistor-simulator
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

macOS / Linux:

```bash
cd transistor-simulator
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

> If `python` is not recognised, add `C:\Program Files\Python314` and
> `C:\Program Files\Python314\Scripts` to your user PATH and open a new terminal.

## Run

```powershell
python -m flask --app app run --debug
```

Open `http://127.0.0.1:5000/` in your browser.

> The Flask debug server is for local development only. Do not expose it to a public network.

### One-click start (Windows)

Double-click `เปิดเว็บ.vbs` to start the server in the background, then open
`http://127.0.0.1:5000/`. It calls `run_web.ps1`, which does nothing if the server
already answers on port 5000. Both scripts resolve paths from their own folder, so
they still work after cloning the repository somewhere else.

## Test

```powershell
python -m unittest discover -s tests -v
```

Expected output: `Ran 65 tests ... OK`.

## Example — Lab 03 A2 (Fixed Bias)

1. Select **Fixed Bias** → **Apply mode**.
2. Enter `VCC = 12` V, `RB = 1` MΩ (or `1000` kΩ), `RC = 2.2` kΩ, `β = 100`, `VBE = 0.70` V.
3. Press **Calculate DC Bias** → `IB 11.3 µA`, `IC 1.13 mA`, `VCE 9.51 V`, region Forward Active.

For A3/A4, select **Emitter Bias** with the same values plus `RE = 1` kΩ
(`IC 1.03 mA`, `VCE 8.71 V`), then change `RE` to 2 kΩ
(`IC 940 µA`, `VCE 8.03 V`). See `docs/validation.md` for all five acceptance cases.

## Circuit diagrams

Static diagrams for the three bias modes, with the Lab 03 reference values labelled
on each one. PNG versions are ready to attach to the submission; SVG sources are
editable and stored alongside them.

| Mode | PNG | SVG |
|---|---|---|
| Voltage Divider (A1) | [PNG](docs/images/voltage-divider.png) | [SVG](docs/images/voltage-divider.svg) |
| Fixed Bias (A2, A5) | [PNG](docs/images/fixed-bias.png) | [SVG](docs/images/fixed-bias.svg) |
| Emitter Bias (A3, A4) | [PNG](docs/images/emitter-bias.png) | [SVG](docs/images/emitter-bias.svg) |

## Model and limitations

Common forward-active equations (all modes): `IC = β·IB`, `IE = (β+1)·IB`,
`VB = VE+VBE`, `VC = VCC−IC·RC`, `VCE = VC−VE`.

- **Voltage Divider** (Lab 02, unchanged): `VTH = VCC·R2/(R1+R2)`, `RTH = R1∥R2`,
  `IB = (VTH−VBE)/(RTH+(β+1)RE)`.
- **Fixed Bias**: `IB = (VCC−VBE)/RB`, `VE = 0`. `VTH`/`RTH` are reported as `VCC`/`RB`
  so every mode shares the same result schema.
- **Emitter Bias**: `IB = (VCC−VBE)/(RB+(β+1)RE)`.

Fixed β and fixed VBE, forward-active approximation only. No Early effect, no
temperature dependence, no self-heating. Not a SPICE simulation: values outside the
active region are labelled and shown raw with a warning, never silently corrected.
Do not open `templates/index.html` directly (`file://`); it requires the Flask server.

## Project structure

```
app.py                  # Flask routes, form parsing, unit conversion (no equations)
dc_bias.py              # pure engineering model: dataclasses, equations, registry
units.py                # SI formatting with engineering units
templates/index.html    # mode switch + mode-specific form + result panel (Jinja)
templates/base.html     # page shell
static/style.css
tests/test_dc_bias.py   # engineering math, validation, regions
tests/test_web.py       # Flask test client: GET, POST, errors, warnings, A1–A5
requirements.txt        # Flask>=3.0,<4
README.md               # this file
AGENTS.md               # conventions for AI coding sessions
docs/
  design-note.md        # student-written summary of this design
  validation.md         # Lab 02 + Lab 03 A1–A5 reference numbers and evidence
  reflection.md         # what was learned / limits
  images/               # circuit diagrams: editable SVG + submission-ready PNG
docs/superpowers/
  specs/                # approved Lab 03 design spec
  plans/                # implementation plan
```

## Commits and delivery

Commit with GitHub Desktop, one per task, prefixes `feat:`, `test:`, `docs:`, `chore:`.
Never commit `.venv/`, `__pycache__/`, `.env`, or credentials.
Submit the repository URL + latest commit SHA through Moodle.
