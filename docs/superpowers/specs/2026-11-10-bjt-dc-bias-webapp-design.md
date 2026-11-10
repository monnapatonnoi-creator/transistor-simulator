# Design — BJT DC Bias Web App (Lab 2, W2 of the Virtual Transistor Laboratory)

- **Course:** ENG29 2121 Computer Programming for Electrical Engineers, 2/2569
- **Date:** 2026-11-10
- **Status:** Draft for approval
- **Repo:** `transistor-simulator` (one repo for W2–W11)
- **Author:** OpenCode session with the student (owner: monnapatonnoi-creator)

## 1. Intent and why

The student must deliver a **working multi-file Flask web application** in a single
180-minute lab, and that application is the **first vertical slice of a Virtual
Transistor Laboratory** that will grow until W11 (more bias types, SPICE-backed DC,
AC/gain/Bode, transient, interactive schematics, FET).

The decision that matters today is therefore not "how fast can we ship a
calculator", but "**can W3–W7 add features without rewriting the W2 app**".
Speed still matters: grading requires a runnable localhost demo, real backend
calculation, tests, and a GitHub commit *today*.

Success for this slice:

1. A browser form posts `VCC, R1, R2, RC, RE, β, VBE` to Flask; Python computes the
   DC operating point; the rendered page shows `VTH, RTH, IB, IC, IE, VB, VE, VC, VCE`
   with units and an operating-region verdict.
2. Invalid input produces readable errors instead of a crash.
3. Results outside the forward-active assumption are labelled as such.
4. At least 3 engineering unit tests and at least 1 Flask client test pass.
5. The student can explain what `dc_bias.py` does, and can change an equation
   without touching HTML.

## 2. Goals

- G1. One route, one result model, one template: adding a bias type in W3 is a
  registry entry plus one function.
- G2. Engineering logic is pure Python, importable with no Flask and no HTML.
- G3. Every number shown carries a unit and is produced by the backend.
- G4. The UI renders results from a single structured object, so W4 (ngspice) and
  W5 (AC) can add sections without redesigning the page.
- G5. The repo is reproducible from a clean clone via `README.md`.

## 3. Non-goals (W2 explicitly does not do)

- AC small-signal, gain, Bode plots, transient, signal generator, overlay animation.
- ngspice or any SPICE integration. The W2 model is the forward-active
  approximation.
- Interactive/clickable schematic, drag-and-drop circuit editor.
- FET, multiple transistors, or arbitrary topologies.
- User accounts, database, deployment, authentication.
- JavaScript build tooling or a frontend framework. Server-rendered HTML + CSS only.
- Bias types other than Voltage Divider being *selectable* (the seam exists, the
  options do not — see §7.4).

## 4. Anti-goals (fails even if it "works")

- Numbers written into the HTML or JS instead of computed in Python.
- Opening `templates/index.html` directly (`file://`) counts as "working".
- Equations living in the template.
- A UI that shows a plausible-looking answer with no warning when the
  forward-active assumption is violated (e.g. `VTH ≤ VBE`, `VCE ≤ VCE_sat`).
- Tests that assert the implementation's own output (self-fulfilling tests) rather
  than an independently computed reference.
- Committing `.venv/`, `__pycache__/`, `.env`, or credentials.

## 5. Constraints

- **Time:** 180 min total; build window ~75 min. Anything that cannot be finished,
  tested, and demonstrated today is out.
- **Toolchain (verified on this machine):** Windows 10/11, Python 3.14.2 at
  `C:\Program Files\Python314` (not yet on PATH), pip 25.3, Git 2.56.0,
  GitHub Desktop 3.6.10, OpenCode Desktop 2.2.6 + Superpowers.
- **Flask not yet installed**; a venv must be created at `.venv`.
- **Commits** are made by the student through **GitHub Desktop** (not CLI), so the
  work must land in small, individually reviewable diffs.
- **Model scope:** fixed β and fixed VBE, forward-active only. No Early effect,
  no temperature dependence, no self-heating.
- **Grading:** rubric in the lab handout (10 points) and acceptance items A1–A7.

## 6. Approaches considered

### A. Bias Registry + Shared Result Model — **chosen**
`dc_bias.py` owns one `BiasResult` dataclass and a registry mapping a bias-type key
to a calculation function; `calculate(bias_type, params)` returns that object and
`app.py` passes it to one template.

- Pros: W3 adds a bias type without touching route/template; W4 can swap the internals
  of `calculate()` for ngspice and keep the same result shape; the "one object →
  one template" rule keeps UI work linear instead of multiplicative.
- Cons: ~30–40 extra lines and a result model that must be designed up front.

### B. One module per bias type, branching in the route
Cheap for today, but every new feature edits `app.py`, the template, and the tests.
Cost moves to W3–W7, exactly where the multi-week goal lives. Rejected.

### C. Generic MNA / netlist solver from day one
Closest to SPICE and maximally extensible, but far too large for 180 minutes and it
risks shipping nothing runnable — which fails A1–A7 outright. Rejected; revisit at W4
as `ngspice` integration rather than a hand-written solver (the lab doc forbids
building a SPICE solver for W2).

Student picked **A**.

## 7. Design as decided

### 7.1 Repository layout

```
transistor-simulator/
├── app.py                     # Flask app factory + HTTP routes only
├── dc_bias.py                 # engineering model: params, result, registry
├── templates/
│   ├── base.html              # shell, header, footer, CSS link
│   └── index.html             # form + results, no physics
├── static/
│   └── style.css
├── tests/
│   ├── test_dc_bias.py        # engineering math, validation, region logic
│   └── test_web.py            # Flask test client: GET, POST ok, POST invalid
├── requirements.txt           # flask (pinned major)
├── README.md                  # install/run/test, incl. PowerShell steps
├── AGENTS.md                  # conventions for the AI agent
├── .gitignore
└── docs/
    ├── design-note.md         # short student-written summary of this design
    ├── validation.md          # independent reference numbers + evidence
    ├── reflection.md          # what was learned / limits
    └── superpowers/specs/
        └── 2026-11-10-bjt-dc-bias-webapp-design.md
```

### 7.2 Engineering model (`dc_bias.py`)

```python
@dataclass(frozen=True)
class BiasParams:
    vcc: float          # V
    r1: float           # ohm
    r2: float           # ohm
    rc: float           # ohm
    re: float           # ohm
    beta: float         # dimensionless
    vbe: float = 0.70   # V

@dataclass(frozen=True)
class BiasResult:
    bias_type: str
    vth: float; rth: float            # V, ohm
    ib: float; ic: float; ie: float   # A
    vb: float; ve: float; vc: float; vce: float   # V
    region: str                        # "active" | "cutoff" | "saturation" | "invalid"
    warnings: tuple[str, ...]
```

- All SI base units internally (**volts, ohms, amperes**). The UI converts kΩ → Ω
  before it reaches the model; the model never parses "100k".
- Registry: `BIAS_REGISTRY: dict[str, BiasType]` where
  `BiasType = namedtuple("BiasType", "key label fn")`, with `"voltage_divider"` /
  "Voltage Divider" registered in W2. `calculate(bias_type, params)` raises
  `UnknownBiasType` for anything else.
- The registry is the **single source of truth for the `bias_type` select**: `GET /`
  passes `bias_types=BIAS_REGISTRY.values()` (or the key/label pairs) to the template,
  and the template loops over it. W3 therefore adds a bias type with a registry entry
  and a function only — no route edit, no template edit. A W2 web test asserts the
  rendered `<option>` values equal the registry keys, so the seam is exercised before
  it has a second entry.
- Equations (forward-active approximation, as specified by the lab):
  `VTH = VCC·R2/(R1+R2)`, `RTH = R1·R2/(R1+R2)`,
  `IB = (VTH − VBE)/(RTH + (β+1)·RE)`, `IC = β·IB`, `IE = (β+1)·IB`,
  `VE = IE·RE`, `VB = VE + VBE`, `VC = VCC − IC·RC`, `VCE = VC − VE`.
- Region rules (all thresholds module-level constants so W4 can revisit):
  - **The equations above always run, unmodified.** Region is a *label on the
    result*, never a correction of it. In cutoff/saturation the numbers shown are
    still the raw forward-active output (they will be physically impossible, e.g.
    negative `IC`); that is intentional and is what the UI must communicate.
  - `IB ≤ 0` or `VTH ≤ VBE` → `cutoff` + warning "device is off; forward-active
    equations do not apply — these values are not usable".
  - else `VCE ≤ VCE_SAT` (default `0.2 V`) → `saturation` + warning.
  - else `active`.
  - Additionally warn when `VCE > VCC` (result physically implausible under the
    assumption) without changing the region verdict.
- The module raises `ValueError`/a typed `BiasInputError` for physically invalid
  inputs (`R ≤ 0`, `β ≤ 0`, `VCC ≤ 0`, `VBE < 0`, `VBE ≥ VCC`) — HTTP never sees it.

### 7.3 Web layer (`app.py`)

- `create_app()` factory (testable, no import-time side effects).
- `GET /` → form pre-filled with the lab's starter values: **VCC 12 V, R1 100 kΩ,
  R2 22 kΩ, RC 2.2 kΩ, RE 1 kΩ, β 100, VBE 0.70 V**, resistors shown in kΩ, no
  result panel.
- `POST /calculate` → parse form, convert units, call `calculate()`, re-render
  `index.html` with the result. **Validation errors re-render the same page with
  HTTP 200**, field-level messages, and the user's submitted values preserved
  (response status is a deliberate choice: the page is a valid document, not a
  missing resource; malformed/unknown routes still 404).
- Form field names: `bias_type, vcc, r1, r1_unit, r2, r2_unit, rc, rc_unit,
  re, re_unit, beta, vbe`. Unit selects are `ohm|kohm`, default `kohm` for
  resistors, `V`/dimensionless implied for the rest.
- No math in `app.py`: it may convert units and assemble `BiasParams`, nothing else.

### 7.4 Extensibility seams (the point of choosing A)

- **W3:** add `fixed_bias()` / `emitter_bias()` in `dc_bias.py` (or `bias/*.py`),
  register them, and populate the `bias_type` select. Route and result template
  are untouched.
- **W4:** `calculate()` internally delegates to an ngspice-backed implementation and
  maps the operating point back into `BiasResult`; add a `method` field
  (`"analytic" | "spice"`) to the result so the UI can label the source.
- **W5–W7:** new analytics live in their own modules (`ac_analysis.py`,
  `transient.py`) returning their own dataclasses; templates compose via Jinja
  includes/macros rather than one monolithic page.
- The `bias_type` select ships in W2 with **one** option, so the control and the
  contract are exercised by tests before there is a second option.

### 7.5 Presentation

- Server-rendered, one column, works down to 360 px wide. No framework, no JS
  required for the core flow.
- Result panel prints values with 3 significant figures and explicit units
  (`V`, `mA`, `µA`, `kΩ`).
- Operating region shown as a labelled status line plus, when not `active`, a
  warning block listing each `warnings` entry.
- **Outside the active region the numeric table is de-emphasised** (muted colour,
  no highlighting) and carries a short sentence above it: "These values come from
  forward-active equations whose assumptions are violated here. Do not use them."
  The region line and the warning block stay high-contrast. Numbers are never
  hidden and never replaced by corrected values (student decision, §6/§9).
- Errors and warnings are visually distinct (error = red block, warning = amber).
- The page must state the model's assumptions in one line ("fixed β, fixed VBE,
  forward-active approximation; not a SPICE simulation").

### 7.6 Testing strategy

- `tests/test_dc_bias.py` (stdlib `unittest`):
  1. Reference case: VCC 12 V, R1 100 kΩ, R2 22 kΩ, RC 2.2 kΩ, RE 1 kΩ, β 100,
     VBE 0.70 V → VTH ≈ 2.1639 V, RTH ≈ 18.033 kΩ, IB ≈ 12.299 µA,
     IC ≈ 1.2299 mA, IE ≈ 1.2422 mA, VE ≈ 1.2422 V, VB ≈ 1.9422 V,
     VC ≈ 9.2943 V, VCE ≈ 8.0521 V, region `active`.
     Tolerances: 1e-3 relative (values asserted against independent hand calculation,
     recorded in `docs/validation.md`).
  2. Region test: `VTH ≤ VBE` (e.g. R1 100 kΩ, R2 5 kΩ, VCC 5 V, VBE 0.7) → `cutoff`
     and non-empty warnings; the returned values must equal the raw equations
     (regression test pinning "label, not correction").
  3. Region test: saturation (e.g. RC large / VCC low) → `saturation` + warning,
     again with raw values.
  4. Validation: `R2 = 0`, `β = 0`, `VCC = -1` each raise the input error.
  5. Registry: unknown bias type raises; registry contains `voltage_divider`.
- `tests/test_web.py` (Flask test client):
  1. `GET /` → 200, form present, no result panel, defaults equal the starter values.
  2. `GET /` → the `bias_type` `<option>` values equal `BIAS_REGISTRY` keys
     (registry-driven select, §7.2).
  3. `POST /calculate` with the reference case → 200, body contains computed
     `8.05`/`VCE` markers proving backend rendering.
  4. `POST /calculate` with `beta=0` → 200, shows an error message, does not 500.
  5. `POST /calculate` with non-numeric `vcc=abc` → 200, shows an error.
- Run: `python -m unittest discover -s tests -v`.

### 7.7 Reproducibility and delivery

- `requirements.txt`: `Flask>=3.0,<4`.
- `README.md`: Windows PowerShell first (venv activate path), then macOS/Linux;
  `python -m flask --app app run --debug`; test command; screenshot expectations.
- Commits via GitHub Desktop, one per task, messages
  `feat|test|docs|chore: <area> — <what>`; final push before the lab ends.
- Deliverables: repo URL + commit SHA + screenshot + test log; `docs/validation.md`
  and `docs/reflection.md` filled in by the student. The 10-point rubric also scores
  Brainstorm+Planning (this document + plan), Tests/Validation/Warning, and
  Review/README/Reflection — all present in the layout above (§7.1, §7.6, §7.7).

### 7.8 Local environment prerequisites (do first, ~5 min)

1. Add `C:\Program Files\Python314` and `...\Python314\Scripts` to the user PATH.
2. `python -m venv .venv`; activate; `pip install -r requirements.txt`.
3. `git init` in `transistor-simulator` (or create the repo in GitHub Desktop) before
   the first commit; publish from GitHub Desktop.

## 8. What is left to the builder

- Exact CSS/visual language (typography, colours, spacing) — free choice; must stay
  legible at 360 px and must not hide units.
- Whether `base.html` + `index.html` is worth splitting for a one-page app (both
  acceptable; `base.html` is preferred for W5+).
- Decimal formatting helper details (3 significant figures, trailing zeros).
- Exact wording of error and warning strings (must be understandable to a
  second-year student, in English or Thai — one language throughout).
- Whether validation lives in a small `forms.py` helper or inline in `app.py`
  (inline is acceptable for W2 if it stays under ~30 lines).
- Test helper fixtures for building `BiasParams` from the reference case.

## 9. Acceptance mapping (A1–A7 from the handout)

| Lab item | Where this design satisfies it |
|---|---|
| A1 GET / 200 + form | §7.3, test `test_web.py::test_index_get` |
| A2 POST computes in Python | §7.2–7.3, test posts reference case and asserts rendered numbers |
| A3 matches independent calculation | §7.6 reference values, `docs/validation.md` |
| A4 validation | §7.2 input errors, `test_web.py` invalid cases |
| A5 outside active region warning | §7.2 region rules + warning rendering §7.5 |
| A6 ≥3 engineering tests + ≥1 Flask test | §7.6 (5 engineering, 4 web) |
| A7 clone, install, run, test from README | §7.7 |

## 10. Risks

- **Python PATH / Flask install eats lab time.** Mitigation: do §7.8 before the build
  window; a failure here is the most likely reason the demo is late.
- **3-significant-figure assertions drift** when formatting changes. Mitigation:
  tests assert on numeric model output from `dc_bias.py`; the web test asserts on
  unambiguous fragments only.
- **Scope creep toward W4/W5.** Mitigation: non-goals in §3 are enforced at review;
  the seams exist precisely so extra features can wait.
- **Python 3.14 + Flask compatibility.** Mitigation: Flask ≥3.0 supports 3.14;
  verify `import flask` immediately after install, before writing code.
