# Validation log — BJT Bias & CE Amplifier Simulator

## Lab 02 reference case (A1, Voltage Divider)

Reference case from the lab handout: VCC 12 V, R1 100 kΩ, R2 22 kΩ, RC 2.2 kΩ,
RE 1 kΩ, β 100, VBE 0.70 V.

| Quantity | Hand calculation | App output |
|---|---:|---:|
| VTH | 2.164 V | 2.16 V |
| RTH | 18.03 kΩ | 18.0 kΩ |
| IB | 12.30 µA | 12.3 µA |
| IC | 1.230 mA | 1.23 mA |
| IE | 1.242 mA | 1.24 mA |
| VE | 1.242 V | 1.24 V |
| VB | 1.942 V | 1.94 V |
| VC | 9.294 V | 9.29 V |
| VCE | 8.052 V | 8.05 V |

Hand calculation:

VTH = 12 × 22 / (100 + 22) = 2.1639 V
RTH = 100 × 22 / 122 = 18.033 kΩ
IB = (2.1639 − 0.70) / (18.033k + 101 × 1k) = 12.299 µA
IC = 100 × IB = 1.2299 mA
IE = 101 × IB = 1.2422 mA
VE = 1.2422 V, VB = 1.9422 V
VC = 12 − 1.2299m × 2.2k = 9.2943 V
VCE = 9.2943 − 1.2422 = 8.0521 V

Region: Forward Active — VCE > 0.2 V, IB > 0. App shows "Forward Active" with no warnings. ✓

Cutoff check: VCC 5 V, R2 5 kΩ → VTH = 0.238 V < VBE 0.70 V → IB negative (−4.37 µA).
App labels "Cutoff" with warning; raw values shown de-emphasised. ✓

Saturation check: RC 10 kΩ → VCE = −1.54 V ≤ 0.2 V → "Saturation" with warning. ✓

## Lab 03 acceptance cases A1–A5

All reference numbers below were calculated independently by hand **before** comparing
with the app. The automated checks use Flask's test client in
`tests/test_web.py::TestLab03Cases`; repeat the same five cases in a real browser at
`http://127.0.0.1:5000/` before submission.

| Case | Inputs (unless noted: VCC 12 V, RC 2.2 kΩ, β 100, VBE 0.70 V) | Independent reference | App output | Status |
|---|---|---|---|---|
| **A1** Divider | R1 100 kΩ, R2 22 kΩ, RE 1 kΩ | IC 1.230 mA, VCE 8.052 V, RTH 18.03 kΩ | `1.23 mA`, `8.05 V`, `18.0 kΩ` | ✓ identical to Lab 02 |
| **A2** Fixed | RB 1 MΩ, emitter grounded | IB 11.30 µA, IC 1.130 mA, VCE 9.514 V | `11.3 µA`, `1.13 mA`, `9.51 V`, `Mode: fixed_bias` | ✓ |
| **A3** Emitter | RB 1 MΩ, RE 1 kΩ | IB 10.263 µA, IC 1.026 mA, VE 1.037 V, VCE 8.705 V | `1.03 mA`, `8.71 V` | ✓ |
| **A4** Emitter, RE doubled | RB 1 MΩ, RE 2 kΩ | IB 9.401 µA, IC 0.940 mA, VE 1.899 V, VCE 8.033 V — **IC lower than A3** | `940 µA`, `8.03 V` (`940 µA` = `0.940 mA`) | ✓ |
| **A5** Fixed, RB = 0 | RB 0 | Reject: `rb must be greater than zero` | Error block shown, no result panel | ✓ |

Independent hand calculations:

- **A2:** IB = (12 − 0.70) / 1 M = 11.30 µA; IC = 100·IB = 1.130 mA;
  VE = 0; VC = 12 − 1.130m × 2.2k = 9.514 V; VCE = 9.514 − 0 = 9.514 V.
- **A3:** IB = (12 − 0.70) / (1 M + 101 × 1 k) = 11.3 / 1.101 M = 10.263 µA;
  IC = 1.026 mA; IE = 101·IB = 1.0366 mA; VE = 1.0366 V;
  VC = 12 − 1.026m × 2.2k = 9.742 V; VCE = 9.742 − 1.037 = 8.705 V.
- **A4:** IB = 11.3 / (1 M + 101 × 2 k) = 11.3 / 1.202 M = 9.401 µA;
  IC = 0.940 mA; IE = 0.9495 mA; VE = 0.9495m × 2k = 1.899 V;
  VC = 12 − 0.940m × 2.2k = 9.932 V; VCE = 9.932 − 1.899 = 8.033 V.
  Increasing RE adds `(β+1)·RE` to the base-path resistance, so IB and IC fall —
  the expected negative feedback of an emitter resistor.
- **A5:** RB = 0 is not a valid resistor. Validation rejects it before calculation,
  so no stale result panel is rendered.

The formatter inherited from Lab 02 displays currents below 1 mA in µA, hence A4
appears as `940 µA` rather than `0.94 mA`; the two are the same operating point.
`units.py` was deliberately left unchanged so every Lab 02 number stays identical.

Test run: `python -m unittest discover -s tests -v` →
`Ran 66 tests ... OK` (18 model + 6 units + 40 web/diagram + 2 launcher checks).

---

# Lab 04 — CE Amplifier Simulator (real ngspice)

## Engine and model

- Executable: `C:\Users\b6829162\AppData\Local\Programs\ngspice\Spice64\bin\ngspice.exe`
- Version reported **by the executable itself** in each raw header:
  `ngspice-47, Build Aug 11 2026   13:49:23`
- Invocation: `ngspice -b -o <log> -r <raw> <deck>` via `subprocess.run([...])`,
  `cwd` = a private `TemporaryDirectory`, `timeout=30`, no `shell=True`, no user text
  interpolated into a command string. The generated netlist and the log excerpt are
  displayed in the page under “Netlist and ngspice log (evidence)”.
- BJT model is a **self-chosen demo model**, not a Starter Kit part:
  `.model LAB4NPN NPN(IS=1E-14 BF=100 VAF=100)`. The handout supplied no lib/model,
  so the app states the full model line on every successful run. Replace this one line
  in `spice_engine.py::MODEL_LINE` to use a different transistor.
- AC sweep is fixed at `.ac dec 20 10 10Meg` (121 points, 10 Hz–10 MHz). The −3 dB
  reference is the low-frequency passband plateau (first sweep decade), **not** the
  global maximum: a mid-band peak must not shift the reference and invent a cutoff.
  If there is no downward crossing of that threshold the page honestly says
  `not determined in sweep range` (no fabricated cutoff). Non-finite raw values are
  rejected as `ParseFailed` instead of becoming a fake `Success`.
- `v(out)` is AC-coupled through `COUT`, so the transient waveform is centred on 0 V;
  this is expected and is why the plot shows a small inverted signal rather than the
  DC collector level.

## B1–B8 acceptance (real browser observations)

Browser: OpenCode in-app Chromium at `http://localhost:5001/` (Flask `--no-debug`).
Every value below was read from the rendered page, not computed for the table.

| Case | Expected | Observed in browser | Evidence / status |
|---|---|---|---|
| **B1** Lab 3 A1–A5 still correct after mode switch | A1 `1.23 mA` / `8.05 V`; A2 `1.13 mA` / `9.51 V`; A3 `1.03 mA` / `8.71 V`; A4 `940 µA`; A5 explicit RB error | A1 `IC 1.23 mA`, `VCE 8.05 V`, `VTH 2.16 V`, `RTH 18.0 kΩ`, `IB 12.3 µA`; A2 `IC 1.13 mA`, `VCE 9.51 V`, `RTH 1.00 MΩ`, `IB 11.3 µA`, `Forward Active`; A3 `IC 1.03 mA`, `VCE 8.71 V`, `IB 10.3 µA`; A4 `IC 940 µA`, `VCE 8.03 V`, `IB 9.40 µA`; A5 `rb must be greater than zero`, no result panel | PASS — `data-testid="result-panel"` text read after each Calculate |
| **B2** CE reference DC run | `VB/VE/VC/VCE/IC` from ngspice + model + status | `Success · ngspice-47, Build Aug 11 2026 13:49:23 · model LAB4NPN`; `VB 1.95 V`, `VE 1.29 V`, `VC 9.19 V`, `VCE 7.90 V`, `IC 1.28 mA` | PASS — page status + DC table + netlist/log details |
| **B3** change RE only, rerun | operating point must change, not a cached value | SPICE `RE` 1 kΩ → 2 kΩ: `VB 2.05 V`, `VE 1.40 V`, `VC 10.5 V`, `VCE 9.06 V`, `IC 696 µA` (was `1.95/1.29/9.19/7.90/1.28m`) | PASS — before/after snapshots, same form otherwise |
| **B4** AC sweep Bode plot with units | freq/gain/phase labelled, real run | `Sweep: 10.0–10000000.0 Hz · Gain 4.74–4.86 dB · Phase -166.7–-180.0 deg`; `−3 dB cutoff: not determined in sweep range`; axes `Frequency (Hz) — log scale`, `Gain (dB)`, `Phase (deg)`; Bode svg present | PASS — flat real sweep has no crossing, so no cutoff invented |
| **B5** `.tran` at 10 mV / 1 kHz | Vin/Vout vs time, labelled, inverted | `1008 time samples · 0.0–5.0 ms`; svg legend `Vin (V)`, `Vout (V)`, axis `Time (ms)`; the two traces are 180° out of phase (negative `Σ vin·vout` in the parser test) | PASS — waveform svg + transient summary |
| **B6** change amplitude, rerun | waveform must come from the new run | Source 10 mV → 20 mV: netlist line changed from `VS in 0 SIN(0 0.01 1000)` to `VS in 0 SIN(0 0.02 1000)`; sample count stayed `1008`, SVG auto-scales so the *netlist line* is the unambiguous evidence | PASS — netlist evidence in details panel |
| **B7** RE = 0 / engine missing | clear error, no fake success | `sim_re=0` → `re must be greater than zero`; no `sim-result`, no `bode-plot`, no `waveform-plot`. Engine-missing path covered by `tests/test_spice_runner.py` (`NgspiceUnavailable`) | PASS — browser + unit tests |
| **B8** desktop/mobile viewport + mode switch | readable, no clipped graph/button | headless Chrome screenshots at **1280×3000** and **390×4400** of a real `/simulate` POST (emitter-bias analytical mode + AC result). Page uses `max-width:1000px`, single-column `.row` and horizontally scrollable plot containers under 640 px | PASS — `docs/captures/lab04-desktop.png`, `docs/captures/lab04-mobile.png` |

### B1 → B2 sequential post-review recheck

After restarting Flask at `http://127.0.0.1:5001/` with the review fixes loaded, the
same browser tab was used for: **Calculate DC Bias** (A1 defaults) → **Run SPICE**
(DC). Before the second click the result panel showed `Result — voltage_divider`,
`IC 1.23 mA`, `VCE 8.05 V`. After the real ngspice run returned
`Success · ngspice-47, Build Aug 11 2026 13:49:23 · model LAB4NPN`, the analytical
panel still showed `1.23 mA` / `8.05 V` and the SPICE table separately showed
`VB 1.95 V`, `VE 1.29 V`, `VC 9.19 V`, `VCE 7.90 V`, `IC 1.28 mA`.
This verifies the SPICE form carries the Lab 3 result instead of erasing it.
Evidence: `docs/captures/lab04-sequential.png` (469×3264).

## UI polish attempt (honest result)

`npx impeccable install` was **NOT RUN**: Node.js/npm/npx are not installed in this
environment (`Get-Command npx` → none; no `C:\Program Files\nodejs`). No Impeccable
critique or audit was performed, and none is claimed. Layout was checked manually
with the two B8 screenshots and the responsive CSS media query instead.

## Automated verification

```
C:\Users\b6829162\Documents\Default Project\transistor-simulator\.venv\Scripts\python.exe -m unittest discover -s tests -v
Ran 99 tests in 12.704s
OK
```

Includes 3 real-ngspice integration tests (`tests/test_spice_integration.py`) that skip
only when the executable is genuinely unavailable; all 3 ran here and passed.
