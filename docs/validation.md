# Validation log — BJT DC Bias

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
`Ran 65 tests ... OK` (18 model + 6 units + 39 web/diagram + 2 launcher checks).
