# Reflection — BJT DC Bias Web App

What I learned: separating frontend from backend makes each part testable on its own.
The engineering module has no Flask in it, so the DC math for all three bias types could
be verified with plain unit tests before touching the web layer. Adding `required` to
each registry entry turned "which inputs belong to this circuit?" into data rather than
duplicated `if` statements — one tuple drives validation, parsing, and which fields the
template shows.

What was hard: deciding how to show the new modes without JavaScript. I chose a separate
GET form for the dropdown with hidden inputs for the typed values, so switching mode
reloads the page but does not erase what was entered. The alternative — showing every
field and letting the user guess which ones matter — was rejected because A5 (RB = 0)
must produce a clear error instead of silently using an unused R1/R2 value.

The most useful result was A4. Increasing RE from 1 kΩ to 2 kΩ reduced IC from 1.026 mA
to 0.940 mA and raised VE, which is direct evidence of emitter degeneration: the
`(β+1)RE` term in the base-path denominator stabilises the current. It also caught a
presentation detail — `0.940 mA` is rendered as `940 µA` by the shared Lab 02 formatter,
which is the same operating point, so I corrected the test expectation rather than
changing the formatter and disturbing the Lab 02 numbers.

I also had to revise an earlier claim from my design note: a registry alone does not
mean the Flask route and template never change. The dropdown is registry-driven, but
per-mode fields do require the route to pass `required` and the template to use it.
The important boundary is that `dc_bias.py` still knows nothing about HTTP or HTML.

Limitation of this model: fixed β and fixed VBE mean it is only accurate near the design
point. Real transistors vary with temperature and current, so this is a teaching tool,
not a design-signoff simulator. Results outside forward-active are labelled with raw
numbers left visible and a warning, never quietly fixed.

## Lab 04 — what the AI did / what you should check

- The AI installed ngspice 47, generated and ran real `.op/.ac/.tran` decks, parsed the
  ASCII raw files, and kept the SPICE panel strictly separate from the unchanged
  analytical panel; no simulation value or plot is hard-coded in HTML.
- The AI validated B1–B7 in a real browser and captured desktop/mobile screenshots for
  B8; every observed number and the exact ngspice version/model are in
  `docs/validation.md`. Impeccable could not be used (no Node/npx installed), and that
  is recorded as NOT RUN rather than claimed.
- You should independently verify the model choice: `LAB4NPN` was self-chosen because
  no Starter Kit model came with the handout. Check the model line in the evidence
  panel, replace it with your assigned device if required, and rerun the three analyses.
- You should also check the −3 dB rule by eye on the Bode plot. The reference sweep is
  flat (4.74–4.86 dB), so the honest answer is `not determined in sweep range`; if your
  device gives a real roll-off, confirm the reported cutoff is the first downward
  crossing 3 dB below the passband maximum.
