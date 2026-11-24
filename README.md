# BJT Bias & CE Amplifier Simulator

A Flask web application built for ENG29 2121:

- **Analytical panel (Lab 02/03)** — DC operating point of an NPN common-emitter
  circuit for three single-supply bias types: **Voltage Divider**, **Fixed Bias** and
  **Emitter Bias**. Pure fixed-β / fixed-VBE equations, unchanged from Lab 03.
- **SPICE panel (Lab 04)** — real external ngspice `.op`, `.ac` and `.tran` runs of a
  common-emitter voltage-divider amplifier, with the generated netlist, log excerpt,
  status, version/model evidence and server-drawn plots. No mocked or hard-coded
  simulation numbers.

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
- The **SPICE (ngspice)** panel has its own form (V, kΩ, µF, mV, kHz). Choose
  `.op` / `.ac` / `.tran` and press **Run SPICE**. Validation errors and engine errors
  clear only the SPICE result area — the analytical Lab 3 result stays untouched.
- The AC view plots gain (dB) and phase (deg) against log frequency from the real sweep.
  The −3 dB reference is the low-frequency passband plateau (first sweep decade), not
  the global peak; a cutoff is reported only when the sweep actually crosses that
  threshold, otherwise it says `not determined in sweep range`. The transient view plots
  `Vin` and `Vout` versus time from real samples.

## Requirements

- Python 3.10+ (tested with 3.14.2)
- Flask ≥3.0, <4
- ngspice 47 (external executable, only for the Lab 04 SPICE section)

### ngspice (Lab 04)

The SPICE section calls an external `ngspice` binary; it is **not** a pip package.
On Windows, download the official `ngspice-47_64.7z` archive from
<https://sourceforge.net/projects/ngspice/files/ng-spice-rework/47/>, extract it,
and add the folder containing `ngspice.exe` (for example
`...\ngspice\Spice64\bin`) to your user PATH. Open a new terminal afterwards and
check that `shutil.which("ngspice")` is not `None`.

If PATH cannot be changed, set the environment variable `NGSPICE_EXE` to the full
path of `ngspice.exe` before starting Flask. The app also checks the standard
Windows user install location as a fallback. The version used to produce the
recorded results was **ngspice-47, Build Aug 11 2026 13:49:23**; the app reports
the exact version from the executable at run time in the status panel.
The app runs it in batch mode with an argument list, a timeout and a private
temporary working directory — never through a shell.

### SPICE circuit and transistor model

The netlist is the reference CE voltage-divider stage: `VCC` → `RC` → collector,
`R1`/`R2` divider → base, `RE` → ground, `CIN`/`COUT` coupling capacitors and a 10 kΩ
`RL`. The source is `VS in 0 SIN(0 <amplitude> <freq>) AC 1`; `.tran` uses 200 steps
per period over five periods, `.ac` uses `dec 20 10 10Meg`.

No Starter Kit library was supplied with the handout, so the simulator ships an
explicit demo model:

```spice
.model LAB4NPN NPN(IS=1E-14 BF=100 VAF=100)
```

The full model line is shown in the status/netlist evidence on every successful run.
To simulate a real device, edit `MODEL_LINE` in `spice_engine.py` (and add any
`.include` you need); no other file has to change.

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

Expected output: `Ran 99 tests ... OK` (66 Lab 02/03 tests + 30 SPICE
unit/route tests + 3 real-ngspice integration tests). The integration tests skip
themselves only when no ngspice executable can be found.

## Example — Lab 03 A2 (Fixed Bias)

1. Select **Fixed Bias** → **Apply mode**.
2. Enter `VCC = 12` V, `RB = 1` MΩ (or `1000` kΩ), `RC = 2.2` kΩ, `β = 100`, `VBE = 0.70` V.
3. Press **Calculate DC Bias** → `IB 11.3 µA`, `IC 1.13 mA`, `VCE 9.51 V`, region Forward Active.

For A3/A4, select **Emitter Bias** with the same values plus `RE = 1` kΩ
(`IC 1.03 mA`, `VCE 8.71 V`), then change `RE` to 2 kΩ
(`IC 940 µA`, `VCE 8.03 V`). See `docs/validation.md` for all five acceptance cases.

## Example — Lab 04 SPICE runs

Use the lower **SPICE (ngspice)** panel. Defaults are
`VCC 12 V`, `R1 100 kΩ`, `R2 22 kΩ`, `RC 2.2 kΩ`, `RE 1 kΩ`, `RL 10 kΩ`,
`Cin = Cout = 10 µF`, source `10 mV` peak at `1 kHz`.

1. **DC:** keep `Analysis = DC operating point (.op)` and press **Run SPICE**.
   Expect `Success · ngspice-47, ... · model LAB4NPN` and
   `VB 1.95 V`, `VE 1.29 V`, `VC 9.19 V`, `VCE 7.90 V`, `IC 1.28 mA`.
   Open “Netlist and ngspice log (evidence)” to see the deck actually executed.
2. **Parameter sweep:** change only SPICE `RE` to `2` kΩ and rerun DC →
   `VB 2.05 V`, `VE 1.40 V`, `VC 10.5 V`, `VCE 9.06 V`, `IC 696 µA`.
3. **AC:** select `AC sweep (.ac)` → a Bode plot with
   `Sweep: 10.0–10000000.0 Hz`, gain ≈ `4.74–4.86 dB`, phase ≈ `-166.7–-180.0 deg`.
   With the demo model there is no −3 dB crossing in this range, so the page says
   `not determined in sweep range` rather than inventing a number.
4. **Transient:** select `Transient (.tran)` → `1008 time samples · 0.0–5.0 ms`,
   with `Vin (V)` / `Vout (V)` traces 180° out of phase. Change source to `20 mV`
   and rerun; the netlist line becomes `VS in 0 SIN(0 0.02 1000)`.
5. **Error path:** set SPICE `RE` to `0` → `re must be greater than zero`, with no
   result panel or plots. If ngspice is missing you get a clear
   `ngspice not found — install it or set NGSPICE_EXE ...` message.

The B1–B8 browser evidence table, engine version and limitations are in
`docs/validation.md`; desktop/mobile screenshots are in `docs/captures/`.

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
temperature dependence, no self-heating. These numbers are **not** SPICE results:
values outside the active region are labelled and shown raw with a warning, never
silently corrected, and they are displayed in a separate panel from the ngspice run.

The SPICE panel uses the `LAB4NPN` model above: it has Early effect (`VAF=100`) but
still no temperature model, parasitics or real Starter Kit device. It is a teaching
demo, not design sign-off. Do not open `templates/index.html` directly (`file://`);
it requires the Flask server.

## Project structure

```
app.py                  # Flask routes, form parsing, unit conversion (no equations)
dc_bias.py              # pure analytical model: dataclasses, equations, registry
spice_engine.py         # pure Python: validation, netlist, ngspice runner, raw parsers
plots.py                # server-side SVG built only from parsed ngspice arrays
units.py                # SI formatting with engineering units
templates/index.html    # analytical + SPICE panels, forms, results, evidence (Jinja)
templates/base.html     # page shell
static/style.css        # responsive styling for both panels
tests/test_dc_bias.py   # analytical math, validation, regions
tests/test_web.py       # Flask test client: GET, POST, errors, warnings, A1–A5
tests/test_spice_*.py   # netlist, parser, runner, route, real-ngspice integration
tests/fixtures/         # genuine ngspice raw + log files used by parser tests
requirements.txt        # Flask>=3.0,<4
README.md               # this file
AGENTS.md               # conventions for AI coding sessions
docs/
  design-note.md        # student-written summary of the analytical design
  validation.md         # Lab 02/03 numbers + Lab 04 B1–B8 browser evidence
  reflection.md         # what was learned / limits
  images/               # circuit diagrams: editable SVG + submission-ready PNG
  captures/             # Lab 04 desktop/mobile screenshots
docs/superpowers/
  specs/                # approved Lab 03 + Lab 04 design specs
  plans/                # implementation plans
```

## Commits and delivery

Commit with GitHub Desktop, one per task, prefixes `feat:`, `test:`, `docs:`, `chore:`.
Never commit `.venv/`, `__pycache__/`, `.env`, or credentials.
Submit the repository URL + latest commit SHA through Moodle.
