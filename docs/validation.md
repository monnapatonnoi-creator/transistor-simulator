# Validation log — BJT DC Bias

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

Test run: `python -m unittest discover -s tests -v`
Ran 33 tests ... OK
