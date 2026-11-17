# Live Circuit Diagram Design

## Intent

ผู้ใช้ต้องการเห็นภาพวงจรอยู่ในหน้าเว็บเลย และภาพต้องเปลี่ยนตามโหมดที่เลือกและค่าที่กรอก
**ขณะพิมพ์** (ไม่ต้องกด Calculate ก่อน) เพื่อใช้สาธิตรูปแบบการ bias แต่ละแบบใน Lab 03
และแนบผลลัพธ์ส่งงานโดยไม่ต้องเปิดไฟล์ภาพแยก

## Goals

- ภาพ SVG แสดงในหน้าเว็บด้านบนตารางผลลัพธ์
- เปลี่ยนโหมด/ตัวเลข/หน่วยแล้วภาพอัปเดตทันทีในขณะพิมพ์
- รูปยังแสดงค่าถูกต้องแม้ JavaScript ปิดหรือเปิดหน้าด้วย Flask test client

## Non-goals / Anti-goals

- ไม่คำนวณ physics ใน JavaScript หรือ template — `dc_bias.py` เป็นแหล่งเดียวของผลลัพธ์
- ไม่เปลี่ยน `dc_bias.py`, `units.py`, `DEFAULTS`, หรือผล A1–A5
- `mega` ยังต้องเป็นหน่วยผิด; ใช้ `mohm` สำหรับ MΩ ตามเดิม
- ไม่ลบไฟล์ SVG/PNG เดิมใน `docs/images/` — ยังใช้แนบ Moodle ได้
- ไม่เพิ่ม JS framework หรือ build step

## Constraints

- `AGENTS.md`: `app.py` parse/render เท่านั้น, template display only, `dc_bias.py` บริสุทธิ์
- เว็บเดิมใช้ GET `/` + Apply mode ไม่มี JS; งานนี้เพิ่ม JS เฉพาะส่วนอัปเดตภาพ
- ต้องผ่าน `.venv\Scripts\python.exe -m unittest discover -s tests`
- ใช้ `.venv\Scripts\python.exe` เสมอ (PATH ไม่มี `python`)
- ไม่ commit `.venv/`, `__pycache__/`, `*.pyc`, `.env`

## Approaches

1. **Inline SVG + JS แก้ DOM (เลือก)** — server render ข้อความ/_group เริ่มต้นจาก `form`,
   JS ฟัง `input`/`change` แล้วแก้ `<text>` และสลับ class โชว์/ซ่อน ไม่ยิง request ทุกตัวอักษร,
   ยังทดสอบ server render ได้ด้วย unittest
2. **JS โหลด `/diagram.svg`** — แหล่งภาพเดียวฝั่ง server แต่มี network ทุกครั้งที่พิมพ์
   ต้อง debounce และเพิ่ม route/helper มากขึ้น → ไม่เลือก
3. **Auto-submit ฟอร์มทุกการแก้ค่า** — focus หลุด ไม่ตรงความต้องการแบบขณะพิมพ์ → ตัด

## Design

- ใส่ `<svg class="live-diagram">` ไว้ใน `templates/index.html` ก่อนฟอร์ม สร้างจาก SVG เดิม
  ใน `docs/images/` แต่ย้ายตัวเลขที่เปลี่ยนได้ไปอยู่ใน `<text data-bind="...">`
- กลุ่มที่ต้องโชว์/ซ้อนตามโหมดใช้ `class="diagram-group"` และ `is-hidden` (CSS `display:none`)
  ตั้งค่าเริ่มต้นด้วย Jinja ตาม `active_bias`: `shape-r1`, `shape-r2` เฉพาะ divider;
  `shape-rb` เฉพาะ fixed/emitter; `shape-re` เฉพาะ divider/emitter;
  `shape-emitter-direct` เฉพาะ fixed
- ตัวอักษรที่มี `data-bind`: `mode-title`, `vcc`, `r1`, `r2`, `rb`, `rc`, `re`, `beta`,
  `vbe`, `ic`, `vce`; ค่าที่ render มาจาก `form` + macro แปลงหน่วยใน template
  (`ohm`→`Ω`, `kohm`→`kΩ`, `mohm`→`MΩ`)
- ถ้ามี `result` ให้ render `ic`/`vce` ผ่าน filter เดิม; ถ้าไม่มีให้ render `—`
- เพิ่ม `static/diagram.js` และโหลดจาก `templates/base.html` ด้วย `defer`;
  JS อ่านค่า from `input[name=...]`, select name `_unit` หรือ `carry_..._unit`,
  ใช้ `textContent` เท่านั้น และสลับ class `is-hidden` ตาม select `bias_type`
- หลังผู้ใช้แก้ค่า ภาพจะเปลี่ยน `ic`/`vce` เป็น `— (กด Calculate)` เพื่อไม่ให้結果เก่าหลอก
- ไม่เพิ่ม physics/unit conversion ลง JS: JS แค่ copying string ของหน่วยที่เลือก

## Left to Builder

- รายละเอียดเส้น/สี/typography ของ SVG ให้ใกล้เคียง `docs/images/*.svg` เดิม
- ขนาด `viewBox` และ responsive width เลือกให้พอดีกับคอลัมน์ 760px เดิม
- ชื่อ class เสริมและโครงสร้าง event listener เลือกได้ตามสะดวก ขอแค่ตรงตาม `data-bind` ข้างบน
