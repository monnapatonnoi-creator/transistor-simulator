# Design note — BJT DC Bias Web App (student summary)

This app separates the calculation from the screen. `dc_bias.py` does the math with the
equations the lab gave and returns one result object with the same keys for every mode
(`VTH`, `RTH`, `IB`, `IC`, `IE`, `VB`, `VE`, `VC`, `VCE`, region, warnings). `app.py` only
reads the form, converts kΩ→Ω, calls the model, and hands the result to the Jinja
template. Numbers are never typed into the HTML — the backend computes them on every
request. The layer boundary from Lab 02 was kept intact in Lab 03.

## Registry and required fields

`BIAS_REGISTRY` now holds three entries, each a `BiasType(key, label, fn, required)`:

| Key | Function | `required` fields |
|---|---|---|
| `voltage_divider` | `voltage_divider` | vcc, r1, r2, re, rc, beta, vbe |
| `fixed_bias` | `fixed_bias` | vcc, rb, rc, beta, vbe |
| `emitter_bias` | `emitter_bias` | vcc, rb, re, rc, beta, vbe |

`required` is the key addition in Lab 03. `validate_params()` checks only the fields a
mode actually uses, so a fixed-bias circuit is not rejected for having `R1 = R2 = RE = 0`.
It also makes the screen declarative: the route passes the mode's `required` set to the
template as `visible_fields`, and Jinja renders only those inputs. The mode switch is a
small separate GET form with hidden values; pressing **Apply mode** reloads the page,
which keeps already-typed numbers without any JavaScript.

To keep one shared result schema, fixed and emitter bias report `VTH = VCC` and
`RTH = RB`. That is a reporting convention, not a physical Thevenin equivalent of a
divider; it lets `classify_region()` and the result table work unchanged for all modes.

I originally wrote that adding a bias type would never touch the route or the HTML.
Lab 03 showed the limit of that claim: the dropdown still comes from the registry, but
mode-specific fields require the route to read `required` and the template to branch on
`visible_fields`. The model/HTTP boundary, however, did not move at all.

## What A4 taught

Doubling RE from 1 kΩ to 2 kΩ in emitter bias dropped IC from 1.026 mA to 0.940 mA.
The denominator `RB + (β+1)RE` shows why: the emitter resistor is reflected to the base
by `β+1`, so it dominates RB and provides negative feedback. This is the practical
advantage of emitter bias over fixed bias — IC depends much less on β, which is why a
fixed-β classroom model is less misleading here than it is for fixed bias.

## Forward-active limits

If the device is actually cut off or saturated, the equations still print numbers, but
those numbers are physically wrong. We keep showing the raw values, mark the region, and
add a warning so the user knows not to trust them. That is better than hiding numbers or
silently correcting them. This behaviour is identical across all three modes.
