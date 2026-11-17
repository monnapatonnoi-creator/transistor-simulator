# Design (short) — Lab 03: Fixed Bias + Emitter Bias

## Intent / why
ต่อยอดเว็บ Lab 2 ให้เลือกได้ 3 วงจรตามใบงาน Lab 03 โดย **ไม่เขียนเว็บใหม่** และ
**Voltage Divider ต้องให้ผลเดิมทุกตัวเลข** เพื่อใช้เป็น A1 baseline

## Goals
- เพิ่ม `fixed_bias` (RB จาก VCC→Base, Emitter ลงกราวด์) และ `emitter_bias`
  (RB จาก VCC→Base, RE จาก Emitter→กราวด์) ใน `dc_bias.py`
- ฟอร์มเลือกโหมดแล้วโหลดหน้าใหม่ (แบบ A) เฉพาะช่องที่ใช้เท่านั้นที่โชว์ ไม่ใช้ JS
- ตรวจเฉพาะอินพุตที่โหมดนั้นต้องการ ผล และ region ยังใช้โครงเดิม

## Non-goals / anti-goals
- ไม่ทำ SPICE, load line, AC/transient, bypass capacitor
- ไม่ย้ายสมการเข้า HTML, ไม่สร้างโปรเจกต์ใหม่, ไม่แก้ผล Divider
- ไม่ต้องติดตั้ง Playwright ใน requirements (ใช้ Browser Tool ที่มีอยู่)

## Constraints
- โค้ดเดิม 33 tests ต้องผ่าน (แก้เฉพาะ 2 test ที่ใช้ `fixed_bias` เป็นชื่อ unknown)
- AGENTS.md: dc_bias.py บริสุทธิ์, app.py แค่ parse/render, TDD ก่อนแก้
- อินพุตและหน่วยตามใบงาน: VCC 12 V, RC 2.2 kΩ, β 100, VBE 0.70 V ร่วมทุกโหมด

## Approaches (ที่พิจารณา)
- **A — โหลดฟอร์มใหม่ตามโหมด (เลือกแล้วทำ GET)** ← เลือกแล้วโดยผู้ใช้
  ฟอร์มเลือกโหมดเป็น GET แยกต่างหาก ตัวคำนวณเป็น POST ที่มี hidden `bias_type`
  ข้อดี: ตรงใบงาน ไม่ต้อง JavaScript ข้อเสีย: หน้ารีโหลดตอนเปลี่ยนโหมด
- **B — โชว์ทุกช่องแล้ว disable ช่องที่ไม่ใช้** ถูกปฏิเสธ (ผู้ใช้เลือก A)

## Design (รายละเอียดที่ตัดสินแล้ว)
1. `BiasParams` เพิ่ม `rb: float = 0.0` ต่อท้าย (default ทำให้โค้ด/test เก่าที่สร้าง
   `BiasParams(...)` โดยไม่ส่ง rb ยังใช้ได้)
2. `BiasType` เพิ่มฟิลด์ `required: tuple[str, ...]` ระบุช่องที่โหมดนั้นใช้
   - `fixed_bias`: `("vcc", "rb", "rc", "beta", "vbe")`
   - `emitter_bias`: `("vcc", "rb", "re", "rc", "beta", "vbe")`
   - `voltage_divider`: `("vcc", "r1", "r2", "re", "rc", "beta", "vbe")`
3. `validate_params(p, required=...)` ตรวจค่าร่วม (vcc, rc, beta > 0 และ vbe ถูกต้อง)
   + เฉพาะฟิลด์ใน required เท่านั้น → Fixed ไม่บังคับ R1/R2/RE
4. สมการใหม่ (SI Ω/A):
   - Fixed: `ib = (vcc − vbe)/rb`, `vth = vcc`, `rth = rb`, `ve = 0`,
     `vb = vbe`, `ic = β·ib`, `ie = (β+1)·ib`, `vc = vcc − ic·rc`, `vce = vc − ve`
   - Emitter: `ib = (vcc − vbe)/(rb + (β+1)·re)`, `vth = vcc`, `rth = rb`,
     ส่วนที่เหลือเหมือน Divider
   - กำหนด `vth = vcc`, `rth = rb` ให้ทั้งสองโหมดเพื่อให้ `BiasResult` และ
     `classify_region()` (ที่เช็ก `vth <= vbe`) ทำงานเหมือนเดิมโดยไม่เปลี่ยนโครงผลลัพธ์
5. `calculate()` เรียก `validate_params(p, required)` ตาม registry ก่อนเรียก fn
6. `app.py`: parse `rb` เฉพาะเมื่อโหมดใช้, `GET /?bias_type=<key>` กำหนดโหมดที่เลือก
   ฟอร์มนั้นเป็น GET ส่วนฟอร์มคำนวณ POST มี hidden bias_type; ส่ง context
   `active_bias` + `required` เข้า template เพื่อเลือกแสดงช่อง
7. `templates/index.html`: dropdown อยู่ในฟอร์ม GET ที่ submit ทันทีเมื่อเปลี่ยน
   (ใช้ปุ่ม "Apply" ก็ได้ — ไม่บังคับ auto-submit ถ้าไม่ใช้ JS) ช่องที่แสดงตาม required
   ผล/ข้อผิดพลาดระบุโหมดที่เลือก และ `__init__` กันผลเก่าหลุดเมื่อกรอกผิด (ทำอยู่แล้ว)
8. Tests: แก้ 2 test ที่ใช้ `fixed_bias` เป็น unknown → เปลี่ยนเป็น `no_such_bias`;
   เพิ่ม test สำหรับสมการ Fixed/Emitter, validation ตามโหมด, และ web A2–A5
9. Docs: อัปเดต README, docs/validation.md (ตาราง A1–A5 + ค่าอ้างอิงอิสระ),
   docs/design-note.md, docs/reflection.md

## หลักฐานอิสระที่ต้องใส่ใน validation (คำนวณมือ)
- A2 Fixed: VCC 12, RB 1 MΩ, RC 2.2 kΩ, β 100, VBE 0.70
  IB = (12−0.70)/1M = 11.3 µA → IC = 1.13 mA → VE = 0 →
  VC = 12 − 1.13m×2.2k = 9.514 V → VCE = 9.514 V
- A3 Emitter: RB 1 MΩ, RE 1 kΩ → IB = 11.3/1,101,000 = 10.2634 µA →
  IC = 1.02634 mA → IE = 1.03661 mA → VE = 1.03661 V →
  VC = 12 − 1.02634m×2.2k = 9.7421 V → VCE = 8.7055 V
- A4 Emitter RE=2 kΩ → IB = 11.3/1,202,000 = 9.4010 µA → IC = 0.9401 mA
  (ลดจาก A3 เพราะ RE เพิ่ม)

## What's left to the builder
เขียน failing test ก่อน → แก้ทีละชั้น → รัน 33+ tests → commit ต่อจาก `bcc1478`
