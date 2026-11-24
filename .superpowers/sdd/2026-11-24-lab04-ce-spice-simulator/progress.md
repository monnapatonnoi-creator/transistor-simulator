# SDD ledger — plan: docs/superpowers/plans/2026-11-24-lab04-ce-spice-simulator.md

Pre-flight: interfaces consistent across Tasks 1–6 (SimInput → build_netlist → parse_* → run_analysis → /simulate → browser/docs); no conflicts.
Ruling: native worktree tool created a separate empty repo instead of linking transistor-simulator — used `git worktree add` in the correct repo; cost: manual cleanup of the stray worktree, already removed.
Ruling: session has no `bash` on PATH, so the SDD shell scripts cannot run — ledger and task briefs are maintained manually from the plan file; cost: no automated task-done gating, compensated by explicit test commands and outputs recorded here.
Baseline: `.venv` lives in the main checkout; worktree tests use that interpreter with worktree as cwd — 66 tests OK at 1d94369.

Task 1 — DONE (c6a50d2).
Ruling: SourceForge download URL needed the `downloads.sourceforge.net/project/...` mirror; the `/download` page returned HTML. Archive extracted to `%LOCALAPPDATA%\Programs\ngspice\Spice64\bin\ngspice.exe`.
Ruling: user PATH was updated, but harness shells launched before that change do not see it; engine must support `NGSPICE_EXE` and a standard-install fallback. `ngspice -v` hangs when stdout is captured, so version detection will read the `Command: ngspice-47, Build ...` header from a real batch raw file.
Probe result: ngspice accepts `ngspice -b -o log -r raw deck.cir`; `.print` lines are ignored when `-r` is supplied, and raw files are ASCII with named vectors (`v(in)`, `v(out)`, `i(vcc)`), so parsers will read **raw ASCII**, not `.print` log text. Design doc updated to record this deviation.

Task 2 — DONE (d1510fb). 70 tests OK. `SimInput` validates SI floats only; `build_netlist()` uses a 0 V source `VIC` in series with RC so collector current is an actual saved vector `i(vic)`; no raw form text reaches the deck. Verified the generated decks run in ngspice with exit 0.

Task 3 — DONE (f1466f1). 77 tests OK. Real fixtures committed in `tests/fixtures/`. Debugging evidence: (1) ngspice prefixes **every** raw row with its index, not just the first — misalignment made `time` negative; fixed by stripping the index per line; (2) frequency in complex raw is a complex value with ~1e-311 imaginary part — converted via `.real`; (3) `v(out)` is AC-coupled and centred on 0 V, so assertions expecting multi-volt swings were wrong and were corrected; (4) the reference sweep is flat (4.74–4.86 dB) with no −3 dB crossing, so `find_cutoff()` correctly returns `None` and the UI will say `not determined in sweep range`.

Task 4 — DONE (8fc5d82). 85 tests OK. `run_analysis()` uses `subprocess.run([...], cwd=tempdir, timeout, capture_output=True, check=False)`, no `shell`. Errors are explicit (`NgspiceUnavailable`, `RunFailed`, `OutputEmpty`, `ParseFailed`). `find_ngspice()` checks `NGSPICE_EXE`, PATH, then standard user install locations; verified real detection and version output `ngspice-47, Build Aug 11 2026 13:49:23`. Test-only bug fixed: the temporary `cwd` is deleted when the call returns, so the existence assertion was moved inside the mocked subprocess call.

Task 5 — DONE (0f4ac69). 92 tests OK. Added `plots.py` (server-side SVG from parsed arrays only), `POST /simulate`, separate SPICE panel with status/netlist/log/error, and responsive CSS. Real end-to-end Flask client check (no mocks): dc/ac/tran all returned 200 + Success + correct plot panel + ngspice-47 version; `sim_re=0` returned the explicit error with no result panel. Lab 3 `/calculate` still gives 1.23 mA / 8.05 V.

Task 6 / validation — DONE (82b15ec). 95 tests OK. Browser B1–B8 verified in real Chromium; A1–A5 Lab 03 numbers unchanged, B2 DC `1.95/1.29/9.19/7.90 V` + `IC 1.28 mA`, B3 RE 2 kΩ changes the operating point, B4 AC `10–10 MHz` flat with honest `not determined in sweep range`, B5 `1008` transient samples, B6 amplitude edit visible in the real netlist, B7 explicit `re must be greater than zero`, B8 desktop/mobile screenshots committed. Impeccable NOT RUN (no Node/npx), recorded honestly.

Fresh-context review — fixed in 3f1f097 with failing tests first: `/simulate` preserved the Lab 3 result via hidden `lab3_*` state; non-finite raw values now raise `ParseFailed`; the −3 dB reference is the low-frequency passband plateau, not the global sweep maximum. B1→B2 sequential browser recheck added with screenshot; 99 tests OK.

Integration — PR #1 `lab04-ce-simulator` → `main` merged as `1b8cce0401889fde99a013f5c8adac40bf7a170a`; tests re-run on the merged `main` tree: 99 tests OK.
