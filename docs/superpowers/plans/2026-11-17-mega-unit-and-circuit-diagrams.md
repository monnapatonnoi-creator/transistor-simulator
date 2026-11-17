# MΩ Unit and Circuit Diagrams Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** ให้กรอกความต้านทานเป็น MΩ ได้ทั้ง 5 ช่อง และเพิ่มภาพวงจรทั้ง 3 แบบสำหรับแนบใบงาน Lab 03

**Architecture:** คงชั้นเดิม — `app.py` เป็นคนแปลงหน่วย, `dc_bias.py` ไม่แตะ, template แค่เพิ่ม option; ภาพเป็นไฟล์ SVG ที่เขียนเองแล้ว export PNG ด้วย browser screenshot เก็บใน `docs/images/`

**Tech Stack:** Python 3.14, Flask 3.1, unittest, SVG, browser screenshot

**Spec:** `docs/superpowers/specs/2026-11-17-mega-unit-and-circuit-diagrams-design.md`

## Global Constraints

- AGENTS.md: `dc_bias.py` บริสุทธิ์, `app.py` แค่ parse/render, template แสดงอย่างเดียว
- ต้องผ่าน `.venv\Scripts\python.exe -m unittest discover -s tests` (baseline 54 tests)
- `mega` ยังต้องเป็นหน่วยผิด (test เดิม `test_unknown_unit_shows_error`)
- A1–A5 ผลลัพธ์ไม่เปลี่ยน: A1 `1.23 mA`/`8.05 V`, A2 `1.13 mA`/`9.51 V`, A3 `1.03 mA`/`8.71 V`, A4 `940 µA`, A5 error RB=0
- ไม่ commit `.venv/`, `__pycache__/`, `*.pyc`, `.env`
- ใช้ `.venv\Scripts\python.exe` รันเทสต์ (PATH ไม่มี `python`)
- ผู้ใช้ push ไปแล้ว → ต้อง commit + push ใหม่ + แจ้ง SHA ใหม่

## Review Focus

- กรอก `mega` ต้องยัง error `Unknown unit: mega` — ทดสอบโดย test เดิมใน Task 1
- `mohm` ต้องคูณ 1,000,000 พอดี — ทดสอบ `_to_ohms("1","mohm") == 1e6` ใน Task 1
- เปลี่ยนหน่วยแล้วสลับโหมดต้องไม่เสีย `mohm` — ทดสอบ hidden `carry_rb_unit` ใน Task 1
- ค่า default ต้องยังเป็น `1000 kΩ` — ทดสอบ value เดิมใน Task 1
- ภาพต้องมี label ครบและตัวเลขตรง A1–A5 — ทดสอบเนื้อหา SVG ใน Task 2

---

### Task 1: หน่วย MΩ

**Files:**
- Modify: `app.py:35-40`, `templates/index.html` (5 dropdown), `tests/test_web.py`, `README.md`

**Interfaces:**
- Consumes: `_to_ohms(raw: str, unit: str) -> float`, `create_app()`, `FIXED_FORM` ใน tests
- Produces: `unit == "mohm"` คืน `float(raw) * 1_000_000.0`

- [ ] **Step 1: เขียน failing test** ใน `tests/test_web.py` (import `_to_ohms` เพิ่มจาก `app`):
  - `test_mohm_conversion`: `_to_ohms("1","mohm") == 1e6`, `_to_ohms("2.2","mohm") == 2.2e6`
  - `test_mohm_option_in_every_resistor_field`: GET `/` และ `/?bias_type=fixed_bias` → มี `<option value="mohm">MΩ</option>` ครบ
  - `test_mohm_rb_reproduces_a2`: POST `dict(FIXED_FORM, rb="1", rb_unit="mohm")` → มี `1.13 mA`, `9.51 V`
  - `test_mohm_unit_survives_mode_switch`: GET fixed with `rb_unit=mohm` → มี `name="rb_unit" value="mohm"`; GET divider with `carry_rb_unit=mohm` → มี `name="carry_rb_unit" value="mohm"`

- [ ] **Step 2: รันให้ fail** — `.venv\Scripts\python.exe -m unittest tests.test_web -v`

- [ ] **Step 3: แก้โค้ด** — เพิ่ม branch `mohm` ใน `_to_ohms()`; เพิ่ม option ต่อจาก `kΩ` ใน dropdown ของ r1, r2, rb, rc, re; เพิ่มบรรทัดหน่วยใน README

- [ ] **Step 4: รันทั้งชุดให้ผ่าน** — คาด `Ran 58 tests ... OK`

- [ ] **Step 5: Commit** — `feat: add megaohm unit to resistor fields`

---

### Task 2: ภาพวงจร 3 แบบ

**Files:**
- Create: `docs/images/voltage-divider.svg`, `docs/images/fixed-bias.svg`, `docs/images/emitter-bias.svg` และ `.png` ที่ตรงกัน
- Create: `tests/test_diagrams.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: ไม่มี — ไฟล์ภาพสแตติก
- Produces: ไฟล์ภาพที่ลิงก์ได้จาก README

- [ ] **Step 1: เขียน failing test** ใน `tests/test_diagrams.py`:
  - `test_diagram_files_exist`: ทั้ง 6 ไฟล์ (3 svg + 3 png) มีอยู่จริง
  - `test_svg_labels`: แต่ละ SVG มี `VCC`, `RC`, `β`, `VBE`, `GND`; divider มี `R1`, `R2`, `100 kΩ`; fixed มี `RB`, `1 MΩ`; emitter มี `RB`, `RE`, `1 MΩ`

- [ ] **Step 2: รันให้ fail** — `.venv\Scripts\python.exe -m unittest tests.test_diagrams -v`

- [ ] **Step 3: เขียน SVG 3 ไฟล์** — วาดแหล่งจ่าย VCC, transistor NPN, RC, RE/RB ตามโหมด, สัญลักษณ์กราวด์, ค่าอ้างอิงจาก spec ด้วยเส้นและตัวอักษรชัดเจน

- [ ] **Step 4: export PNG** — ใช้ browser screenshot ของ SVG แต่ละไฟล์ บันทึกเป็น `docs/images/*.png`; ตรวจว่าไฟล์มีขนาด > 0

- [ ] **Step 5: อัปเดต README** — เพิ่มหัวข้อภาพวงจรพร้อมลิงก์ไปยัง PNG ทั้ง 3 ภาพ

- [ ] **Step 6: รันทั้งชุดให้ผ่าน** — คาด `Ran 60 tests ... OK`

- [ ] **Step 7: Commit** — `docs: add circuit diagrams for three bias modes`
