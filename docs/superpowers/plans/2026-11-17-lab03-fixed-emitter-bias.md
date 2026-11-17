# Lab 03 Fixed + Emitter Bias Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** เพิ่ม Fixed Bias และ Emitter Bias แบบแหล่งจ่ายเดียวเข้าเว็บ Flask เดิม โดย Voltage Divider ยังให้ผลเดิมทุกตัวเลข

**Architecture:** คงชั้นเดิมจาก Lab 2 — `dc_bias.py` เป็นโมเดลบริสุทธิ์ มี registry ของฟังก์ชันแต่ละวงจร + คำจำกัดช่องที่ใช้ต่อโหมด; `app.py` แค่ parse form ตามโหมดและ render; Jinja แสดงเฉพาะช่องที่ required ของโหมดที่เลือก (แบบ A: dropdown เป็นฟอร์ม GET แยก โหลดหน้าใหม่ ไม่ใช้ JS)

**Tech Stack:** Python 3.14, Flask 3.1, unittest (stdlib), Git CLI

**Spec:** `docs/superpowers/specs/2026-11-17-lab03-fixed-emitter-bias-design.md`

## Global Constraints

- `dc_bias.py` ห้าม import flask/HTML; `app.py` ห้ามมีสมการ; หน่วยภายในเป็น SI (V, Ω, A)
- kΩ→Ω แปลงที่ `app.py` เท่านั้น; รองรับ `ohm` / `kohm` (1 MΩ = 1000 kΩ)
- ผลลัพธ์ต้องมี key เดิม `vth, rth, ib, ic, ie, vb, ve, vc, vce, region, warnings`
- ตั้ง `vth = vcc`, `rth = rb` สำหรับ fixed/emitter เพื่อให้ `classify_region()` ใช้โครงเดิมได้
- VALID input แต่ IB ≤ 0 หรือ VCE ≤ 0.2 → warning + ค่าดิบ (แก้ไขค่าไม่ได้) เหมือนเดิม
- ไม่ commit `.venv/`, `__pycache__/`, `*.pyc`, `.env`
- Base commit ก่อนเริ่ม: `bcc1478`; commit 1 ครั้งต่อ task; รัน `python -m unittest discover -s tests` ก่อน commit ทุกครั้ง
- ใช้ `.venv/Scripts/python.exe` (PATH ไม่มี `python`); git อยู่ที่ `C:\Users\b6829162\AppData\Local\Programs\Git\cmd`
- ใบงาน Lab 03: `C:\Users\b6829162\Downloads\ENG29_2121_Lab03_BJT_Bias_Web_App.html`

## Review Focus

- เปลี่ยนโหมดแล้วค่าที่กรอกค้างอยู่หาย → GET form ต้องส่ง hidden value ทุกช่องไปด้วย (ทดสอบใน Task 2)
- Fixed กับ RB = 0 → ต้อง error ว่า `rb must be greater than zero` ไม่ใช่ error ของ r1/r2/re และต้องไม่โชว์ผลเก่า (Task 3)
- Emitter เปลี่ยน RE 1→2 kΩ แล้ว IC ต้องลด (A4) → ทดสอบตรงสมการ + เว็บ (Task 1, 3)
- กรอก `bias_type=fixed_bias` ต้องคำนวณได้ แต่ `no_such_bias` ต้อง error (Task 1)
- A1 Divider ต้องได้ผลเท่าเดิม 8.05 V / 1.23 mA (Task 1, 4)

---

### Task 1: โมเดล — เพิ่ม rb, fixed_bias, emitter_bias, validate ตามโหมด

**Files:**
- Modify: `dc_bias.py`
- Test: `tests/test_dc_bias.py`

**Interfaces:**
- Consumes: `BiasParams`, `BiasResult`, `BiasType`, `BIAS_REGISTRY`, `calculate`, `validate_params` ของเดิม
- Produces: `BiasParams.rb: float = 0.0`; ฟังก์ชัน `fixed_bias(p)->BiasResult`, `emitter_bias(p)->BiasResult`; `BiasType.required: tuple[str,...]`; `validate_params(p, required=None)`; registry มี key `fixed_bias`, `emitter_bias`

- [ ] **Step 1: เขียน failing test** ใน `tests/test_dc_bias.py`:
  - แก้ `test_unknown_bias_type_rejected`: ใช้ `calculate("no_such_bias", REFERENCE)`
  - เพิ่ม `test_fixed_reference`: `p = BiasParams(vcc=12, rb=1e6, rc=2.2e3, beta=100, vbe=0.70)` → `ib≈1.13e-5`, `ic≈1.13e-3`, `ve==0`, `vth==12`, `rth==1e6`, `vce≈9.514`, region active
  - เพิ่ม `test_emitter_reference`: `p = BiasParams(vcc=12, rb=1e6, re=1e3, rc=2.2e3, beta=100, vbe=0.70)` → `ib≈1.02634e-5`, `ic≈1.02634e-3`, `ve≈1.03661`, `vce≈8.7055`
  - เพิ่ม `test_emitter_more_re_reduces_ic`: RE=2e3 → `ic <` RE=1e3
  - เพิ่ม `test_fixed_does_not_require_r1_r2_re`: `calculate("fixed_bias", p)` โดย p ไม่ส่ง r1/r2/re → ไม่ raise
  - เพิ่ม `test_zero_rb_rejected`: `calculate("fixed_bias", BiasParams(..., rb=0))` → error `rb must be greater than zero`
  - เพิ่ม `test_registry_has_three_bias_types`: key ครบ 3 ตัว

- [ ] **Step 2: รันเทสต์ให้ fail** — `.venv\Scripts\python.exe -m unittest tests.test_dc_bias -v` คาด FAIL (rb ไม่มี, ไม่มีฟังก์ชันใหม่)

- [ ] **Step 3: แก้ `dc_bias.py`**
  - `BiasParams`: เพิ่ม `rb: float = 0.0` ต่อท้าย vbe
  - `BiasType`: เพิ่ม `required: tuple[str, ...] = ()`
  - เขียน `fixed_bias(p)` และ `emitter_bias(p)` ตาม design; ใช้ common helper คำนวณ `ic, ie, vb, vc, vce` จาก `ib, ve` ได้ถ้าต้องการ (DRY)
  - `validate_params(p, required=None)`: ตรวจ `vcc, rc, beta > 0`, vbe เดิม แล้ว loop เฉพาะ field ใน required (skip ถ้า None → ใช้ list เก่าเพื่อ backward compatible)
  - registry: ใส่ `required` ให้ทั้ง 3 ตัวตาม design; `calculate()` ส่ง `required` เข้า validate

- [ ] **Step 4: รันเทสต์ให้ผ่าน** — คาด 18 tests OK (12 เดิม + 6 ใหม่)

- [ ] **Step 5: Commit** — `feat: add fixed and emitter bias models with per-mode validation`

---

### Task 2: เว็บ — switch โหมดแบบ A + แสดงเฉพาะช่องที่ใช้

**Files:**
- Modify: `app.py`, `templates/index.html`
- Test: `tests/test_web.py`

**Interfaces:**
- Consumes: `BIAS_REGISTRY[key].key/label/required`, `calculate(bias_type, params)`
- Produces: `GET /?bias_type=<key>` → หน้าเดิมพร้อม `active_bias`, `visible_fields`; `POST /calculate` รับ `rb`/`rb_unit` เมื่อโหมดใช้

- [ ] **Step 1: เขียน failing test** ใน `tests/test_web.py`:
  - แก้ `test_unknown_bias_type_shows_error`: ใช้ `bias_type="no_such_bias"`
  - `test_get_default_still_shows_all_divider_fields`: GET `/` → มี `name="r1"`, `name="r2"`, `name="re"` และ **ไม่มี** `name="rb"`
  - `test_get_fixed_mode_hides_r1_and_re`: GET `/?bias_type=fixed_bias` → มี `name="rb"`; ไม่มี `name="r1"`, `name="r2"`, `name="re"`; มี `<option value="fixed_bias" selected`
  - `test_get_emitter_mode_hides_r1_r2`: GET `/?bias_type=emitter_bias` → มี `name="rb"`, `name="re"`; ไม่มี `name="r1"`, `name="r2"`
  - `test_mode_switch_preserves_typed_values`: GET `/?bias_type=fixed_bias&vcc=9&rb=470&rb_unit=kohm&rc=1.5&rc_unit=kohm&beta=80&vbe=0.65` → `value="9"`, `value="470"`, `value="1.5"`, `value="80"`, `value="0.65"` อยู่ในฟอร์ม POST

- [ ] **Step 2: รันให้ fail** — `.venv\Scripts\python.exe -m unittest tests.test_web -v`

- [ ] **Step 3: แก้ `app.py`**
  - `DEFAULTS`: เพิ่ม `rb: "1000"`, `rb_unit: "kohm"`, `bias_type: "voltage_divider"` (คงเดิม)
  - `_parse_request(form, required)`: parse เฉพาะ resistor ที่อยู่ใน required; ถ้าไม่ต้องการให้ return `None` แทน (ไม่ error)
  - `index()`: อ่าน `request.args.get("bias_type", "voltage_divider")`; ถ้าไม่รู้จักให้ fallback divider; ส่ง `active_bias`, `visible_fields=set(required)`, `form` ที่ merge DEFAULTS กับ query args
  - `calculate_bias()`: ใช้ `required` ของโหมดที่เลือก; ส่ง `active_bias` + `visible_fields` เข้า render ด้วยเสมอ

- [ ] **Step 4: แก้ `templates/index.html`**
  - ฟอร์ม GET แยก (action `/`, method `get`) มี dropdown `name="bias_type"` selected ตาม `active_bias` + hidden input ทุกช่อง (ค่าจาก `form`) + ปุ่ม `Apply mode`
  - ฟอร์ม POST เดิม: เพิ่ม `<input type="hidden" name="bias_type" value="{{ active_bias }}">`; render ช่อง `rb` เฉพาะเมื่อ `"rb" in visible_fields`, `r1/r2` เฉพาะ voltage_divider, `re` เฉพาะ emitter/divider; `vcc/rc/beta/vbe` แสดงทุกโหมด
  - ข้อความ error/result เพิ่มบรรทัดบอกโหมดที่เลือก เช่น `<p>Mode: {{ active_bias }}</p>` ใกล้ผลลัพธ์

- [ ] **Step 5: รันให้ผ่าน** — `tests.test_web` ต้อง OK (12 เดิม + 5 ใหม่)

- [ ] **Step 6: Commit** — `feat: switch bias mode via GET form and show mode fields only`

---

### Task 3: เว็บ — validation ตามโหมด + ผล A2–A5

**Files:**
- Modify: `app.py` (ถ้าจำเป็น), `templates/index.html` (ถ้าจำเป็น), `tests/test_web.py`

**Interfaces:**
- Consumes: `calculate()` จาก Task 1, context จาก Task 2
- Produces: หน้า POST ที่ error เฉพาะช่องที่ใช้ และระบุโหมดชัดเจน

- [ ] **Step 1: เขียน failing test** ใน `tests/test_web.py`:
  - `test_fixed_reference_case`: POST `bias_type=fixed_bias, vcc=12, rb=1000, rb_unit=kohm, rc=2.2, rc_unit=kohm, beta=100, vbe=0.70` → status 200, มี `1.13 mA`, `9.51 V`, `Mode: fixed_bias`
  - `test_emitter_reference_case`: POST emitter `rb=1000 ko, re=1 ko` → มี `1.03 mA`, `8.71 V`
  - `test_emitter_re_change_affects_result`: เหมือนเดิมแต่ re=2 → `1.03 mA` หาย, มี `0.94 mA`
  - `test_fixed_zero_rb_shows_error`: rb=0 → status 200, error `rb must be greater than zero`, ไม่มี result panel
  - `test_fixed_missing_rb_shows_error`: ไม่ส่ง rb → error `rb must be a number`
  - `test_unknown_mode_shows_error`: `no_such_bias` → error `Unknown bias type: no_such_bias`
  - `test_divider_unchanged`: ใช้ REFERENCE_FORM เดิม → ยังได้ `8.05 V`, `1.23 mA`, `18.0 kΩ`

- [ ] **Step 2: รันให้ fail**

- [ ] **Step 3: แก้โค้ดตามที่ fail จริง** (คาดว่า Task 1+2 ครอบ大部分 อาจไม่ต้องแก้ — ถ้าผ่านเลยให้ข้าม step นี้และ record ว่าเป็น verification)

- [ ] **Step 4: รันทั้งชุดให้ผ่าน** — `.venv\Scripts\python.exe -m unittest discover -s tests -v` คาด ~42 tests OK

- [ ] **Step 5: Commit** — `test: cover Lab 03 A1 to A5 browser cases via web client`

---

### Task 4: เอกสาร + ตรวจ最终结果

**Files:**
- Modify: `README.md`, `docs/validation.md`, `docs/design-note.md`, `docs/reflection.md`

**Interfaces:**
- Consumes: ผลจาก Task 1–3

- [ ] **Step 1: อัปเดต README** — บอก 3 โหมด, วิธี switch, ตัวอย่าง RB 1 MΩ, วิธีรันเหมือนเดิม

- [ ] **Step 2: อัปเดต `docs/validation.md`** — ใส่ตาราง A1–A5 ตามใบงาน พร้อม input/c expected/วิธีตรวจ/สถานะ และค่าอ้างอิงอิสระ:
  - A1 Divider: IC 1.23 mA, VCE 8.05 V
  - A2 Fixed RB 1M: IC 1.13 mA, VCE 9.51 V
  - A3 Emitter RB 1M RE 1k: IC 1.03 mA, VCE 8.71 V
  - A4 Emitter RE 2k: IC 0.94 mA (ลดจาก A3)
  - A5 Fixed RB 0: error `rb must be greater than zero`
  - ระบุว่าทดสอบผ่าน Flask web client + ต้องตรวจซ้ำใน browser จริงโดยนักศึกษา

- [ ] **Step 3: อัปเดต design-note / reflection** — อธิบายRegistry + required fields, สิ่งที่เรียนรู้จาก A4

- [ ] **Step 4: รัน verification สุดท้าย** — `.venv\Scripts\python.exe -m unittest discover -s tests -v` ต้อง OK; `git status --short` ต้องไม่มี `.venv/`

- [ ] **Step 5: Commit** — `docs: add Lab 03 A1-A5 validation table and update README`
