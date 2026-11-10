# BJT DC Bias Web App

A Flask web application that computes the DC operating point of a **NPN Common Emitter
with Voltage-Divider Bias**, built for ENG29 2121 Lab 02. This is W2 of the Virtual
Transistor Laboratory — more bias types and analyses are added in later weeks without
changing this week's routes or templates.

## What it does

- Browser form accepts `VCC`, `R1`, `R2`, `RC`, `RE`, `β`, `VBE` (resistors in Ω or kΩ).
- Python backend computes `VTH`, `RTH`, `IB`, `IC`, `IE`, `VB`, `VE`, `VC`, `VCE`
  with units and an operating-region verdict (Forward Active / Cutoff / Saturation).
- Invalid input shows a readable error on the same page; results outside the
  forward-active assumption are flagged with a warning.
- Results come from the backend on every request — nothing is hard-coded in HTML.

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

## Test

```powershell
python -m unittest discover -s tests -v
```

Expected output: `Ran 33 tests ... OK`.

## Model and limitations

- Equations: `VTH = VCC·R2/(R1+R2)`, `RTH = R1∥R2`, `IB = (VTH−VBE)/(RTH+(β+1)RE)`,
  `IC = β·IB`, `IE = (β+1)·IB`, `VE = IE·RE`, `VB = VE+VBE`, `VC = VCC−IC·RC`,
  `VCE = VC−VE`.
- Fixed β and fixed VBE, forward-active approximation only. No Early effect, no
  temperature dependence, no self-heating.
- Not a SPICE simulation. Values outside the active region are labelled and their raw
  numbers are de-emphasised, not corrected.
- Do not open `templates/index.html` directly (`file://`); it requires the Flask server.

## Project structure

```
app.py                  # Flask routes and request parsing only
dc_bias.py              # pure engineering model (no HTML/HTTP knowledge)
units.py                # SI formatting with engineering units
templates/index.html    # one form + result panel (Jinja)
templates/base.html     # page shell
static/style.css
tests/test_dc_bias.py   # engineering math, validation, regions
tests/test_web.py       # Flask test client: GET, POST, errors, warnings
requirements.txt        # Flask>=3.0,<4
README.md               # this file
AGENTS.md               # conventions for AI coding sessions
docs/
  design-note.md        # student-written summary of this design
  validation.md         # independent reference numbers + evidence
  reflection.md         # what was learned / limits
```

## Commits and delivery

Commit with GitHub Desktop, one per task, prefixes `feat:`, `test:`, `docs:`, `chore:`.
Never commit `.venv/`, `__pycache__/`, `.env`, or credentials.
Submit the repository URL + latest commit SHA through Moodle.
