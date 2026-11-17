# Live Circuit Diagram Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** แสดงภาพวงจรในหน้าเว็บและอัปเดตโหมด/ค่าที่กรอกแบบ realtime ขณะพิมพ์

**Architecture:** ฝัง SVG ไว้ใน `templates/index.html` ให้ server render ค่าเริ่มต้นจาก `form`/`result` (ไม่พังเมื่อไม่มี JS) แล้วให้ `static/diagram.js` ฟัง event `input`/`change` แก้ `<text data-bind>` และสลับ class `is-hidden` ของ `<g data-group>` — JS ไม่คำนวณ physics และไม่ยิง request

**Tech Stack:** Python 3.14, Flask 3.1, Jinja, SVG, vanilla JavaScript, unittest, in-app browser

**Spec:** `docs/superpowers/specs/2026-11-17-live-circuit-diagram-design.md`

## Global Constraints

- `AGENTS.md`: `dc_bias.py` บริสุทธิ์; `app.py` parse/render; template display only; `units.py` format อย่างเดียว
- ห้ามเปลี่ยนผล A1–A5: `1.23 mA`/`8.05 V`, `1.13 mA`/`9.51 V`, `1.03 mA`/`8.71 V`, `940 µA`, RB=0 error
- `mega` ยังเป็นหน่วยผิด; ใช้ `mohm` แสดง `MΩ`
- ใช้ `.venv\Scripts\python.exe -m unittest discover -s tests` (baseline 61 tests)
- ไม่ commit `.venv/`, `__pycache__/`, `*.pyc`, `.env`
- ผู้ใช้ต้องการต่อเนื่อง/เร็ว และใช้ native execution ใน session นี้

## Review Focus

- กรอก `RB = 1` + เลือกหน่วย MΩ ต้องเห็นข้อความ `1 MΩ` ไม่ใช่ `1 mohm` — ทดสอบใน Task 1 (server render) และ Task 2 (browser)
- เปลี่ยน dropdown โหมดเป็น Fixed Bias ต้องซ่อน R1/R2/RE และโชว์ RB ทันทีโดยยังไม่กด Apply mode — ทดสอบ Task 2
- พิมพ์ตัวเลขทับค่าที่มีอยู่ต้องอัป_date label ในภาพทุก keystroke โดยไม่รีโหลดหน้า — ทดสอบ Task 2
- หลังแก้ค่า ผล `IC`/`VCE` เก่าต้องไม่โชว์ต่อ — ทดสอบ Task 2
- ปิด JS / เปิดด้วย test client ภาพต้องแสดงค่าจาก `form` และ `result` ถูกต้อง — ทดสอบ Task 1

---

### Task 1: Server-rendered inline SVG

**Files:**
- Modify: `templates/index.html` (เพิ่ม macro หน่วย + SVG block หลัง errors)
- Modify: `static/style.css` (เพิ่ม `.live-diagram`, `.diagram-group.is-hidden`)
- Test: `tests/test_web.py` (class `TestLiveDiagram`)

**Interfaces:**
- Consumes: `form`, `active_bias`, `result`, `region_labels` ที่ `app.py` ส่งให้ template อยู่แล้ว; `REFERENCE_FORM`
- Produces: `<svg class="live-diagram">`, `<text data-bind="...">`, `<g data-group="..." class="diagram-group[ is-hidden]">`

- [ ] **Step 1: เขียน failing test** ใน `tests/test_web.py`:
  - `test_diagram_is_rendered_with_current_values`: GET `/` → มี `class="live-diagram"`, `data-bind="vcc">12 V`, `data-bind="r1">100 kΩ`, `data-bind="beta">100`
  - `test_diagram_uses_megaohm_label`: GET `/?bias_type=fixed_bias&rb=1&rb_unit=mohm` → มี `data-bind="rb">1 MΩ`
  - `test_diagram_groups_follow_bias_mode`: GET `/`, `/?bias_type=fixed_bias`, `/?bias_type=emitter_bias` → ตรวจ class ของ `<g data-group="r1|r2|rb|re|emitter-direct">` ว่ามี/ไม่มี `is-hidden` ตามโหมด
  - `test_diagram_result_values`: POST `/calculate` ด้วย `REFERENCE_FORM` → มี `data-bind="ic">1.23 mA`, `data-bind="vce">8.05 V`

- [ ] **Step 2: รันให้ fail** — `.venv\Scripts\python.exe -m unittest tests.test_web.TestLiveDiagram -v` → 4 failures เพราะยังไม่มี SVG

- [ ] **Step 3: เพิ่ม macro และ SVG block** ใน `templates/index.html`:
  - `{% macro unit_label(u) %}` แปลง `ohm/kohm/mohm` → `Ω/kΩ/MΩ`
  - วาดแหล่งจ่าย VCC, transistor NPN, RC, R1/R2/RB/RE, ground ตาม layout เดิมใน `docs/images/voltage-divider.svg`
  - ทุกตัวเลขที่เปลี่ยนได้อยู่ใน `<text data-bind="...">`; กลุ่ม resistor อยู่ใน `<g data-group="...">`
  - `class="diagram-group is-hidden"` ถูกใส่ด้วย Jinja ตาม `active_bias`
  - `ic`/`vce` ใช้ filter เดิมถ้ามี `result` มิฉะนั้น `—`
  - เพิ่ม CSS `.live-diagram { width:100%; max-width:820px }` และ `.diagram-group.is-hidden { display:none }`

- [ ] **Step 4: รันทั้งชุดให้ผ่าน** — คาด `Ran 65 tests ... OK`

- [ ] **Step 5: Commit** — `feat: render live circuit diagram in page`

---

### Task 2: JavaScript live updates

**Files:**
- Create: `static/diagram.js`
- Modify: `templates/base.html` (โหลด script ด้วย `defer`)
- Modify: `README.md`

**Interfaces:**
- Consumes: `data-bind` และ `data-group` จาก Task 1; ชื่อ field เดิมในฟอร์ม (`vcc`, `r1`, `rb`, `rc`, `re`, `beta`, `vbe`, `*_unit`, `carry_*_unit`, `bias_type`)
- Produces: ไม่มี Python API ใหม่ — เป็นพฤติกรรม DOM ตรวจด้วย browser

- [ ] **Step 1: เขียน `static/diagram.js`**:
  - ฟัง `input` และ `change` แบบ delegated บน `document`
  - อ่านโหมดจาก `select[name="bias_type"]`; ใช้ `divider/fixed_bias/emitter_bias` สลับ group ตามตาราง:
    divider → โชว์ `r1,r2,re`; fixed → โชว์ `rb,emitter-direct`; emitter → โชว์ `rb,re`
  - อ่านค่าจาก `input[name="<field>"]` หรือ `form[field].value`, หน่วยจาก `select[name="<field>_unit"]` หรือ hidden `carry_<field>_unit`, map `ohm→Ω`, `kohm→kΩ`, `mohm→MΩ`
  - อัปเดต `textContent` ของ `[data-bind="<field>"]` ทุก.field ที่พบ; ใช้ `textContent` เท่านั้น
  - เมื่อ有任何การแก้ค่า ให้ `[data-bind="ic"]` และ `[data-bind="vce"]` แสดง `— (กด Calculate)`
  - `mode-title` แสดง `Voltage Divider Bias` / `Fixed Bias` / `Emitter Bias`

- [ ] **Step 2: โหลด script** — เพิ่ม `<script src="{{ url_for('static', filename='diagram.js') }}" defer></script>` ใน `base.html`

- [ ] **Step 3: ตรวจใน browser จริง** — เปิด `http://127.0.0.1:5000/` แล้วใช้ browser tools:
  - `select` dropdown `bias_type` เป็น `fixed_bias` → `evaluate` ตรวจ `data-group="r1"` มี `is-hidden`, `data-group="rb"` ไม่มี
  - `fill` `rb` เป็น `1`, `select` `rb_unit` เป็น `mohm` → `evaluate` ตรวจ `[data-bind="rb"].textContent === "1 MΩ"`
  - `fill` `rb` เป็น `2.2` → ตรวจ `"2.2 MΩ"` โดยไม่ reload; ตรวจ `ic` เป็น `— (กด Calculate)`

- [ ] **Step 4: อัปเดต README** — อธิบายว่าภาพอยู่ในหน้าเว็บและอัปเดตขณะพิมพ์; ปรับ expected tests เป็น 65

- [ ] **Step 5: รันทั้งชุด + restart เว็บให้โหลดโค้ดใหม่** — คาด `Ran 65 tests ... OK`; restart Flask แล้ว GET 200

- [ ] **Step 6: Commit** — `feat: update circuit diagram while typing`
