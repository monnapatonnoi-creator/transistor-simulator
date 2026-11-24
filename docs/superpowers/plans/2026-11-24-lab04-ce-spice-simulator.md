# Lab 04 CE Amplifier Simulator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** ต่อยอด Flask DC Bias app เป็น CE Amplifier Simulator v1 ที่รัน ngspice จริงสำหรับ `.op/.ac/.tran` โดยคง Lab 3 เดิมครบ

**Architecture:** ฟอร์มใหม่ `sim_*` ในหน้าเดิมส่งค่าไป `POST /simulate` → `app.py` parse เป็นเลข → `spice_engine.py` validate, สร้าง netlist, เรียก ngspice ด้วย `subprocess.run([...], timeout, cwd=tmp)` และ parse log จริง → `plots.py` วาด SVG จาก array จริง → render พร้อม status/model/netlist/error แยกจากผล Analytical; ทุก error ล้างผล SPICE เท่านั้น

**Tech Stack:** Python 3.14, Flask 3.1, unittest, ngspice 47 (external binary), SVG, in-app browser

**Spec:** `docs/superpowers/specs/2026-11-24-lab04-ce-spice-simulator-design.md`

## Global Constraints

- `AGENTS.md`: `dc_bias.py` บริสุทธิ์; `app.py` parse/dispatch/render เท่านั้น; template display only; `units.py` format เท่านั้น; failing test มาก่อนแก้; commit ต่อ task
- ห้ามเปลี่ยน `DEFAULTS`, `dc_bias.py`, `units.py`, ผล A1–A5 (`1.23 mA`/`8.05 V`, `1.13 mA`/`9.51 V`, `1.03 mA`/`8.71 V`, `940 µA`, RB=0 error) และ 66 tests เดิม
- `mega` ยังเป็นหน่วยผิด; `mohm` = `MΩ`
- ใช้ `.venv\Scripts\python.exe -m unittest discover -s tests` เสมอ (PATH ไม่มี `python`)
- ngspice เป็นโปรแกรมภายนอก: ไม่ `shell=True`, ต้องมี `timeout` และ `cwd` แยกต่อรอบ, ตรวจ return code/ output ว่าง/ parse พัง
- ห้ามแต่ง gain/phase/waveform/cutoff; ถ้า sweep ไม่มีจุด −3 dB ให้แสดง `not determined in sweep range`
- ไม่ commit `.venv/`, `__pycache__/`, `*.pyc`, `.env`, run files ขนาดใหญ่
- ผู้ใช้เลือก native execution และให้ทำต่อเนื่องเร็ว

## Review Focus

- ใส่ `RE=0` หรือ amplitude/frequency ติดลบ/ผิดหน่วย → ต้อง error ก่อนสร้าง netlist และไม่มีกราฟ/ success ปลอม — ทดสอบ Task 2 (`test_rejects_nonpositive_passives`) และ Task 5 (`test_simulate_invalid_input_shows_error`)
- ฟอร์มมีข้อความ เช่น `1; rm -rf` → ต้องปฏิเสธหรือแปลงเป็น float ก่อนเทลง netlist ห้ามผ่านเข้า command/solver — ทดสอบ Task 2 (`test_rejects_non_numeric_form_text`)
- ngspice ไม่มีใน PATH / exe ผิด / return code ไม่เป็นศูนย์ / log ว่าง / timeout → status Error ไม่โชว์ผลเก่า — ทดสอบ Task 4 (`test_missing_engine`, `test_failed_run`, `test_empty_output`, `test_timeout`)
- เปลี่ยน `RE` หรือ amplitude/frequency แล้ว Run ใหม่ → ผล/กราฟต้องเปลี่ยนตาม run จริง ไม่ใช่ constant — ทดสอบ Task 3 (`test_parser_uses_input_columns`) และ Task 6 (browser B3/B6)
- เปิด Desktop/Mobile และสลับโหมด → กราฟ/หน่วย/ปุ่มไม่ถูกตัด และผล Lab 3 ยังอ่านได้ — ทดสอบ Task 6 (browser B1/B8)

---

### Task 1: ngspice Toolchain และเก็บ Design/Plan ลง repo

**Files:**
- Modify: `README.md`
- Create: `docs/superpowers/specs/2026-11-24-lab04-ce-spice-simulator-design.md` (เขียนแล้ว)
- Create: `docs/superpowers/plans/2026-11-24-lab04-ce-spice-simulator.md` (ไฟล์นี้)

**Interfaces:**
- Produces: ngspice executable ที่เรียกได้จาก PATH หรือ path ที่记录ไว้สำหรับ `NGSPICE_EXE`; เวอร์ชันจริงสำหรับ validation note

- [ ] **Step 1: ติดตั้ง ngspice จาก installer ทางการ** (SourceForge `ngspice` project → Windows build) และเพิ่ม executable ลง user PATH; ถ้า installer ต้องการสิทธิ์ให้แจ้งผู้ใช้ก่อน อย่า hard-code path เครื่องนี้ลง repo
- [ ] **Step 2: ตรวจ** `ngspice --version` ต้องขึ้นเลขเวอร์ชันจริง (คาด 47.x) และ `.venv\Scripts\python.exe -c "import shutil; print(shutil.which('ngspice'))"` ต้องไม่ใช่ `None`
- [ ] **Step 3: อัปเดต README** ส่วนติดตั้ง ngspice (Windows PATH, `NGSPICE_EXE` override) และเวอร์ชันที่ทดสอบจริง
- [ ] **Step 4: Commit** `git add docs/superpowers README.md && git commit -m "docs: add Lab 04 design, plan and ngspice setup"`

---

### Task 2: Input Validation และ Netlist Generator

**Files:**
- Create: `spice_engine.py`
- Test: `tests/test_spice_engine.py`

**Interfaces:**
- Consumes: dict ของค่าที่ `app.py` แปลงเป็น float แล้ว
- Produces: `SimInput` (dataclass), `SpiceError` + `InvalidInput`, `ANALYSES`, `MODEL_NAME`, `MODEL_LINE`, `SimInput(**values)` validate ใน `__post_init__`, `build_netlist(params: SimInput, analysis: str) -> str`

- [ ] **Step 1: เขียน failing tests** ใน `tests/test_spice_engine.py`:
  - `test_reference_netlist_contains_expected_nodes_and_directives`: `SimInput(vcc=12.0, r1=100_000.0, r2=22_000.0, rc=2_200.0, re=1_000.0, rl=10_000.0, cin_f=10e-6, cout_f=10e-6, amplitude_v=0.010, freq_hz=1000.0)` → `build_netlist(p,"dc")` มี `VCC`, `R1`, `R2`, `RC`, `RE`, `RL`, `CIN`, `COUT`, `Q1`, `LAB4NPN`, `.op`, `.end` และสายต่อ base/collector/emitter ครบ; `ac` มี `.ac`, `tran` มี `.tran` และ `SIN(0 0.01 1000)`
  - `test_rejects_nonpositive_passives`: RE=0, RL=−1, amplitude=0, freq=0, freq=200_000 → แต่ละกรณี `InvalidInput`
  - `test_rejects_non_numeric_form_text`: ส่ง `"1; rm -rf"` เป็นค่า → `InvalidInput`/`TypeError` (ไม่มี string หลุดเข้า netlist)
  - `test_unknown_analysis`: `build_netlist(p,"bode")` → `InvalidInput`

- [ ] **Step 2: รันให้ fail** — `.venv\Scripts\python.exe -m unittest tests.test_spice_engine -v` → FAIL เพราะยังไม่มี module
- [ ] **Step 3: Implement** `spice_engine.py`: `SimInput` เก็บ SI ทุกตัว, validate ช่วง `0 < freq_hz <= 100_000` และบวกค่าอื่น; `build_netlist()` format เฉพาะ `{:g}`/`.8g` ของ float, model line `MODEL_LINE = ".model LAB4NPN NPN(IS=1E-14 BF=100 VAF=100)"`, ใช้ node `vcc`,`base`,`col`,`emi`,`in`,`out`, ground `0`, วัด Vin ที่ node `in` ก่อน CIN
- [ ] **Step 4: รันทั้งชุดให้ผ่าน** — คาด `Ran 70 tests ... OK` (66 เดิม + 4 ใหม่)
- [ ] **Step 5: Commit** — `feat: add validated CE netlist builder`

---

### Task 3: Real-run Probe, Log Fixtures และ Parsers

**Files:**
- Create: `tests/fixtures/lab4_dc.log`, `lab4_ac.log`, `lab4_tran.log` (log จริงจาก ngspice ที่ติดตั้ง)
- Modify: `spice_engine.py`
- Test: `tests/test_spice_engine.py`

**Interfaces:**
- Consumes: `SimInput`, `build_netlist()` จาก Task 2
- Produces: `OpResult(vb,ve,vc,vce,ic)`, `AcPoint(freq_hz,gain_db,gain_mag,phase_deg)`, `TranPoint(time_s,vin_v,vout_v)`, `parse_op(log: str) -> OpResult`, `parse_ac(text: str) -> list[AcPoint]`, `parse_tran(text: str) -> list[TranPoint]`, `find_cutoff(points: list[AcPoint]) -> float | None`

- [ ] **Step 1: Probe จริง** — รัน netlist fixture 3 แบบด้วย `ngspice -b -o <tmp.log> -r <tmp.raw> <tmp.cir>` (เติม `.print`/`.dc` ถ้าจำเป็น) แล้ว copy log ไป `tests/fixtures/`; บันทึกใน design doc ว่ารูปแบบจริงเป็นแบบไหน ถ้าต่างจากที่คาดไว้
- [ ] **Step 2: เขียน failing tests** กับ fixture จริง:
  - `test_parse_op_values`: `parse_op(DC_LOG)` ได้ `vce ≈ vc−ve`, `ic > 0`, หน่วยเป็น V/V/V/V/A
  - `test_parse_ac_uses_input_columns`: `parse_ac(AC_LOG)` ได้ list ไม่为空, `gain_db == vdb(out)−vdb(in)` ทุกจุด, `phase_deg == vp(out)−vp(in)`, `find_cutoff()` หา −3 dB เทียบ low-frequency plateau
  - `test_parse_tran_pairs`: `parse_tran(TRAN_LOG)` ได้ time/vin/vout FEW รอบ และ `vin` มี amplitude ใกล้ 0.010 V
  - `test_no_cutoff_returns_none`: input ที่ไม่ตัดในช่วง → `None`
- [ ] **Step 3: Run to fail** — `.venv\Scripts\python.exe -m unittest tests.test_spice_engine.TestParsers -v`
- [ ] **Step 4: Implement parsers** อ่านเฉพาะ column ที่ `.print` ยืนยันแล้วจาก fixture; ปฏิเสธบรรทัดที่ parse ไม่สำเร็จด้วย `SpiceError` (ไม่ใช่คืน 0 หลอก)
- [ ] **Step 5: Run ทั้งชุดให้ผ่าน** — คาด `Ran 74 tests ... OK`
- [ ] **Step 6: Commit** — `feat: parse real ngspice output`

---

### Task 4: Subprocess Runner และ Error Paths

**Files:**
- Modify: `spice_engine.py`
- Test: `tests/test_spice_engine.py`

**Interfaces:**
- Consumes: `find_ngspice()`, `parse_*()` จาก Task 3
- Produces: `SimResult(analysis, status, model, netlist, log_excerpt, op, ac, tran, warnings)`, `run_analysis(params: SimInput, analysis: str, *, exe: str | None = None, timeout: float = 30.0) -> SimResult`, `ngspice_version(exe: str | None = None) -> str`

- [ ] **Step 1: failing tests** ด้วย fake exe (สคริปต์ python ใน temp ที่เขียน log ตาม fixture หรือ exit code/delay):
  - `test_run_analysis_success`: exe ปกติ + fixture log → `status=="success"`, `op`/`ac`/`tran` ตรง analysis
  - `test_missing_engine`: `exe="/nonexistent/ngspice"` → `NgspiceUnavailable`
  - `test_failed_run`, `test_empty_output`, `test_timeout`: fake exit 1 / log ว่าง / หน่วงเกิน timeout → `RunFailed`/`OutputEmpty`/`RunFailed`
  - `test_subprocess_uses_list_and_cwd`: monkeypatch `subprocess.run` ตรวจ args เป็น list ไม่มี `shell=True`, มี `timeout` และ `cwd` เป็น temp dir
- [ ] **Step 2: run to fail**
- [ ] **Step 3: Implement** `find_ngspice()`: `NGSPICE_EXE` → `shutil.which("ngspice")`; `run_analysis()` สร้าง `TemporaryDirectory`, เขียน `.cir`, เรียก `[exe,"-b","-o",log,"-r",raw,cir]`, capture output, ตรวจ return code/ไฟล์/parse, return `SimResult`; ทุก exception ถูกแปลงเป็น subclass ของ `SpiceError`
- [ ] **Step 4: run ทั้งชุดผ่าน** — คาด `Ran 79 tests ... OK`
- [ ] **Step 5: Commit** — `feat: run ngspice safely with explicit error paths`

---

### Task 5: Route `/simulate`, Plots และ UI

**Files:**
- Create: `plots.py`, `tests/test_web_simulate.py`
- Modify: `app.py`, `templates/index.html`, `static/style.css`
- Test: `tests/test_web_simulate.py`

**Interfaces:**
- Consumes: `SimInput`, `run_analysis()`, `SimResult` จาก Tasks 2–4; ฟอร์ม `sim_*`
- Produces: `POST /simulate` endpoint, `sim_plots.mag/wave` เป็น `markupsafe.Markup`, context `sim`, `sim_form`, `sim_errors`, `sim_status`

- [ ] **Step 1: failing tests** (monkeypatch `run_analysis` ให้คืน `SimResult` จาก fixture):
  - `test_simulate_dc_shows_spice_values_and_labels`: POST `/simulate` analysis=dc → เห็น `SPICE (ngspice)`, `VB`, `VCE`, `IC`, `LAB4NPN`, status `Success`, netlist ใน `<details>`; ไม่มีคำว่า `Mock`
  - `test_simulate_ac_has_axes_units_and_cutoff`: POST ac → มี `<svg`, `Hz`, `dB`, `deg`, legend gain/phase และ `not determined in sweep range` ถ้า `find_cutoff` คืน `None`
  - `test_simulate_tran_has_time_and_legend`: POST tran → มี `ms`, `Vin`, `Vout`, `<svg`
  - `test_simulate_invalid_input_shows_error`: `sim_re=0` → error block, ไม่มี `<svg` ของผล SPICE
  - `test_simulate_engine_error_shows_error`: `run_analysis` raise `NgspiceUnavailable` → status `Error`, ไม่มีกราฟ
  - `test_lab3_calculate_unchanged`: POST `/calculate` ด้วย `REFERENCE_FORM` ยังได้ `1.23 mA`/`8.05 V`
- [ ] **Step 2: run to fail**
- [ ] **Step 3: Implement `plots.py`**: `bode_svg(points: list[AcPoint], cutoff_hz: float|None) -> Markup` และ `waveform_svg(points: list[TranPoint]) -> Markup`; วาดแกน log-x สำหรับ Bode, label `Frequency (Hz)`, `Gain (dB)`, `Phase (deg)`, legend; waveform label `Time (ms)`, `Vin (V)`, `Vout (V)`; ไม่คำนวณ physics เพิ่ม
- [ ] **Step 4: Implement route** ใน `app.py`: helper `_parse_sim_form(form) -> (dict|None, errors)` แปลง field `sim_*` (resistor kΩ, cap µF, mV, kHz) เป็น SI; เรียก `run_analysis`; จับ `SpiceError` → `sim_errors` + status; ส่ง context เดิมของ `/calculate` ครบ + context ใหม่; ไม่แตะ `/calculate`
- [ ] **Step 5: Implement template/CSS** section ใหม่ด้านล่าง DC Bias: select `analysis`, ค่า fixture, ปุ่ม Run, status badge, ตารางผล SPICE, `<details>` netlist/log, error block, `<div class="sim-plots">`; แยกหัวข้อ "Analytical reference (Lab 3)" กับ "SPICE (ngspice)"; CSS responsive
- [ ] **Step 6: run ทั้งชุดผ่าน** — คาด `Ran 85 tests ... OK`
- [ ] **Step 7: Commit** — `feat: add SPICE simulation UI and plots`

---

### Task 6: Integration, Browser Acceptance B1–B8, Docs และ Publish

**Files:**
- Create: `tests/test_spice_integration.py`, `docs/captures/` (screenshot)
- Modify: `docs/validation.md`, `README.md`, `docs/reflection.md`
- Test: browser จริง + `.venv\Scripts\python.exe -m unittest discover -s tests`

**Interfaces:**
- Consumes: ทุก task ก่อนหน้า; ngspice ที่ติดตั้งจริง
- Produces: หลักฐาน B1–B8, ผลรันจริง, commit/push พร้อม SHA

- [ ] **Step 1: integration test** `skipUnless(shutil.which("ngspice"))`: รัน jริง 3 analysis ด้วย fixture; ตรวจ array ไม่为空 ค่า finite; เปลี่ยน RE เป็น 2 kΩ แล้วรัน dc/ac ใหม่ว่าผลเปลี่ยน; เปลี่ยน amplitude 10 mV→20 mV แล้ว tran ต้องเปลี่ยน
- [ ] **Step 2: restart Flask** แล้วเปิด browser จริง ตรวจ B1–B8 ตามตารางใน spec: Navigate → Snapshot → Fill/Select → Click → Snapshot → Compare → Screenshot; ใช้ in-app browser หากไม่มี Playwright MCP และระบุชื่อ tool ใน validation อย่างตรงไปตรงมา
- [ ] **Step 3: UI skill** พยายามโหลด/ติดตั้ง `impeccable` (`npx impeccable install`) ถ้าได้ให้ critique → polish เฉพาะ UI → audit; ถ้าไม่ได้ให้บันทึกใน validation ว่าไม่ได้ทำและเหตุผล ห้ามอ้างว่าทำ
- [ ] **Step 4: docs** เติมตาราง B1–B8 พร้อม status `PASS/FAIL/NOT RUN`, expected/observed/evidence/units, เวอร์ชัน ngspice + model; README วิธีรันซ้ำ; reflection 3–5 บรรทัด AI vs นักศึกษา
- [ ] **Step 5: verification** `.venv\Scripts\python.exe -m unittest discover -s tests` ต้อง `OK`; HTTP 200; ห้ามมี failure ที่ซ่อนไว้
- [ ] **Step 6: Commit และ Push** ตามที่ผู้ใช้ต้องการ; รายงาน SHA สุดท้าย
