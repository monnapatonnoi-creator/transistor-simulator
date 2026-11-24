# Lab 04 — CE Amplifier Simulator v1 Design

## Intent

ต่อยอด Flask BJT DC Bias app จาก Lab 3 ให้เป็น Common-Emitter Amplifier Simulator v1
ตามใบงาน Lab 04: ยังใช้ DC Bias แบบประมาณเดิมได้ครบ 3 แบบ และเพิ่มการจำลองจริงด้วย
ngspice สำหรับ **CE Voltage Divider อ้างอิงหนึ่งวงจร** (`.op`, `.ac`, `.tran`) พร้อม
ตัวเลข/กราฟที่มีที่มาชัดเจน ตรวจได้ใน browser และรันซ้ำจาก repo ได้

## Goals

- คง `app.py` เส้นทางเดิม `/` และ `/calculate`, `dc_bias.py`, `units.py`, `DEFAULTS`,
  ผล A1–A5 และ 66 tests เดิม **ไม่เปลี่ยน**
- เพิ่มหนทาง SPICE เฉพาะวงจร CE อ้างอิง: รับค่าที่ validate แล้ว → สร้าง netlist →
  เรียก ngspice ภายนอกด้วย `subprocess.run` → parse ผลจริง → แสดงผล/กราฟ/สถานะ
- แยกป้ายให้ชัดระหว่าง **Analytical (Lab 3)** กับ **SPICE (ngspice)** และไม่บังคับ
  ให้ตัวเลขสองชุดเท่ากัน
- เมื่อ solver ไม่มี/run fail/output ว่าง/timeout/input ผิด ต้องแสดง error และไม่โชว์
  กราฟหรือ status success
- ต้องมีหลักฐาน B1–B8, README, validation note, screenshot จริง และ commit/push

## Non-goals / Anti-goals

- ไม่ทำ circuit editor, AC ของทุก bias mode, FET, bypass capacitor, animated overlay,
  deploy สาธารณะ หรือเขียน SPICE solver เอง
- ไม่ poison ผลAnalytic ด้วยค่าจาก SPICE และไม่ hard-code gain/waveform/phase
- ไม่ใช้ภาพ/กราฟตัวอย่างในใบงานเป็นหลักฐานผล
- ไม่ commit `.venv/`, `__pycache__/`, `*.pyc`, `.env`, run files ขนาดใหญ่

## Constraints

- `AGENTS.md`: `dc_bias.py` บริสุทธิ์, `app.py` parse/dispatch/render, template display,
  `units.py` format เท่านั้น; เขียน failing test ก่อนแก้; ใช้ `.venv\Scripts\python.exe`
- `mega` ยังเป็นหน่วยผิด; `mohm` = MΩ ตาม Lab 3
- ngspice **ไม่ได้ติดตั้งอยู่ในเครื่องตอน recon** และไม่มี Starter Kit/ไฟล์ model แจกใน
  repo/Downloads — ผู้ใช้เลือกให้ติดตั้ง ngspice ก่อนทำ แนวทางที่เลือกคือ A (ด้านล่าง)
- ใบงานเตือนว่า ngspice เป็น external program ไม่ใช่ pip package; ห้ามผสม
  `.control ... .endc` กับ batch `-b -o -r` โดยไม่ทดสอบจริง
- ใช้ batch mode `ngspice -b -o <log> -r <raw> <netlist>` (ปรับตามผลทดสอบจริง)
- บันทึกความจริงเรื่อง tool: สภาพแวดล้อมนี้มี in-app browser ไม่มี Playwright MCP
  ถ้าใช้ browser tool อื่นต้องระบุวิธีใน validation ว่าทำด้วย tool อะไร

## Approaches

1. **`spice_engine.py` + server-drawn SVG (เลือก)** — route ใหม่ `/simulate` รับค่า
   ที่validate แล้ว, engine สร้าง netlist/เรียก ngspice/parse, server วาด SVG จาก array
   จริง; ไม่增加 dependency, ทดสอบได้ทั้ง unittest และ browser, ได้แกน/หน่วยตามที่ควบคุม
2. `.control` ให้ ngspice export กราฟเอง — parser น้อยแต่เสี่ยง syntax/batch และควบคุม
   label ได้ยากกว่า; ใบงานเตือนไว้
3. PySpice/Chart.js — dependency และ abstraction เพิ่ม ไม่จำเป็นสำหรับ v1

## Design

### สถาปัตยกรรมและขอบเขตไฟล์

- ใหม่ `spice_engine.py`: pure Python ไม่ import flask; มี `EngineError` และ subclass
  (`NgspiceUnavailable`, `RunFailed`, `OutputEmpty`, `ParseFailed`, `InvalidInput`),
  `SimResult` dataclass, `validate_sim_input()`, `build_netlist()`, `run_analysis()`,
  `parse_*()`, `find_ngspice()`, `version()`; ทุกค่าที่ใส่ netlist มาจาก float ที่ผ่าน
  validation แล้ว-format ด้วย pattern ของตัวเลขเท่านั้น (ไม่ส่ง string ดิบจากฟอร์ม)
- `app.py`: เพียงเพิ่ม route `POST /simulate` ที่อ่าน form → validate → เรียก
  `spice_engine.run_analysis()` → render เดิมพร้อม context `sim`, `sim_form`,
  `sim_errors`; ไม่ใส่สูตรฟิสิกส์/ไม่ parse log ใน route
- `templates/index.html`: เพิ่ม section **SPICE Simulation (ngspice)** ด้านล่าง DC Bias
  เดิม: select analysis (dc/ac/tran), ค่าวงจร reference, amplitude (mV) และ frequency
  (kHz), ปุ่ม Run, status badge, ตารางผล, `<details>` netlist + log excerpt,
  error block; หัวข้อแยก "Analytical (Lab 3)" กับ "SPICE (ngspice)"
- `static/style.css`: style เฉพาะ section ใหม่, status success/error, กราฟ responsive
- `templates/index.html` วาดกราฟเป็น inline SVG จาก array ที่ engine ส่งมา (server-side)
  — ไม่มี physics ใน JS; `static/diagram.js` ของ Lab 3 ไม่ถูกแก้

### วงจรอ้างอิง (Input Fixture — ห้ามใช้เป็นผลสำเร็จรูป)

`VCC=12 V`, `R1=100 kΩ`, `R2=22 kΩ`, `RC=2.2 kΩ`, `RE=1 kΩ` (ไม่ bypass),
`RL=10 kΩ`, `Cin=Cout=10 µF`, source `10 mV peak / 1 kHz`, NPN Q1, ground ร่วม

SPICE form ต้องแก้ค่าวงจร/แหล่งสัญญาณได้ (B3 เปลี่ยน RE, B6 เปลี่ยน amplitude/frequency)
และค่าเริ่มต้นต้องตรง fixture ข้างบน; node ที่วัด `Vin` คือฝั่ง source ก่อน `Cin`
(ประกาศชัดในหน้าเว็บและ validation)

### Netlist และ Analysis

- ใช้ model ที่ระบุชื่อ/พารามิเตอร์ใน README ว่าเป็น **demo model ที่เลือกเอง**
  (`LAB4NPN`, เช่น `IS`/`BF`/`VAF`) เพราะไม่มี Starter Kit; ต้องมีช่องปรับหรือ
  เปลี่ยนง่ายผ่าน config และแสดงชื่อบนหน้าเว็บ ถ้าอาจารย์แจก model จริงให้แทนที่
- DC `.op`: coupling capacitor เป็น open circuit สำหรับ DC; อ่าน `VB, VE, VC, VCE, IC`
  ตามทิศอ้างอิงที่ประกาศ (IC = กระแสผ่าน RC)
- AC `.ac` sweep เชิงทศนิยม เช่น 10 Hz–10 MHz (ให้ครอบ cutoff); บันทึก freq,
  `vdb(vin)`, `vp(vin)`, `vdb(vout)`, `vp(vout)`; gain dB = `vdb(vout)−vdb(vin)`,
  magnitude = `10^(dB/20)`, phase = `vp(vout)−vp(vin)`; หา −3 dB เทียบกับ passband
  เฉพาะเมื่อมีจุดตัดจริง ไม่เช่นนั้นแสดง "not determined in sweep range"
- Transient `.tran`: สัญญาณ `SIN(0 A F)`; หน้าต่างเวลาประมาณ 5 รอบของความถี่ที่ตั้ง,
  step ให้ละเอียดพอ (~200 จุด/รอบ) และมีขีดจำกัดเพื่อกันรันนาน; บันทึก `time, vin, vout`
  พร้อมหน่วย ms/V และตรวจทิศทางกลับเฟส
- **ผล probe จริง:** ngspice 47 เขียน raw แบบ ASCII และข้าม `.print` ทันทีที่ใช้ `-r`
  ดังนั้น parser อ่าน raw file โดยตรง ไม่ใช่ log/`.print`; log เก็บไว้เป็นหลักฐาน
  สถานะ/เวอร์ชันเท่านั้น
- sweep จริงของ fixture (10 Hz–10 MHz, model ด้านบน) มี gain ~4.74–4.86 dB คงที่
  ไม่มีจุด −3 dB → หน้าต้องแสดง `not determined in sweep range` ตามใบงาน
  (ห้ามแต่ง cutoff)

### Engine run / error paths

- `find_ngspice()`: `NGSPICE_EXE` override → `shutil.which("ngspice")`; ถ้าไม่มีให้ error
  พร้อมวิธีติดตั้ง/ตั้งค่า (ไม่ hard-code path เครื่องนี้ลง repo)
- `subprocess.run([exe, "-b", "-o", log_path, "-r", raw_path, netlist_path], timeout=30,
  cwd=tempdir, capture_output=True, text=True)`; ไม่ใช้ `shell=True`
- ตรวจ return code, stdout/stderr, ว่ามี log/ผลจริง, array ไม่ว่าง และค่าตัวเลข finite
- ทุก error ถูกจับใน route → render status `Error` + ข้อความ + init netlist ที่พยายามรัน
  (หรือข้อความอธิบาย) และ ** result เก่า/กราฟเก่าหายไปเสมอ **

### Validation ranges

- VCC > 0; R1,R2,RC,RE,RL > 0; amplitude > 0; frequency > 0 และอยู่ในช่วงที่กำหนด
  (เช่น 100 Hz–100 kHz); หน่วยที่ยอมรับชัดเจน; ปฏิเสธอักขระที่ไม่ใช่ตัวเลขก่อนสร้าง
  netlist; จำกัดขนาด sweep/step เพื่อกัน timeout

### B1–B8 (จากใบงาน Lab 04)

| Case | Action | Expected | Evidence |
|---|---|---|---|
| B1 | เปิด Fixed/Emitter/Divider แล้วกรอกชุดค่า Lab 3 | ผลเดิมตรง A1–A5 และสลับโหมดได้ | ค่าที่อ่านจริง |
| B2 | เลือก CE Reference แล้ว Run DC | `VB/VE/VC/VCE/IC` จาก ngspice พร้อม model + run status | หน้าเว็บ + log |
| B3 | เปลี่ยน RE ค่าเดียวแล้ว Run ซ้ำ | operating point/gain เปลี่ยน ไม่ใช่ค่าค้าง | ผลก่อน/หลัง |
| B4 | Run AC ดู Bode | freq/gain magnitude/phase มีหน่วยและมาจาก run จริง | chart + engine output |
| B5 | Run `.tran` ที่ 10 mV/1 kHz | Vin/Vout ตามเวลา มีป้าย กลับเฟส | screenshot + สรุปเฟส |
| B6 | เปลี่ยน amplitude หรือ freq แล้ว Run ซ้ำ | waveform เปลี่ยน ไม่ใช่กราฟ hard-code | ภาพก่อน/หลัง |
| B7 | RE=0 หรือ engine ไม่พร้อม | error ชัด ไม่ค้าง ไม่ส่ง success ปลอม | ข้อความจริง |
| B8 | desktop/mobile viewport + เปลี่ยนโหมด | อ่านง่าย ไม่ตัดกราฟ/ปุ่ม | screenshot 2 ขนาด |

### Calls ที่ผู้เขียน design ตัดสินแทน (builder-check ถาม)

- B1–B8 เอากจากใบงานข้างบน; ใบงานไม่กำหนดตัวเลข SPICE ที่ต้องเท่ากัน และ Starter Kit ไม่มี → ใช้ `LAB4NPN` demo model ที่ระบุพารามิเตอร์/ชื่อให้ตรงไปตรงมาใน README พร้อมวิธีแทนที่
- `/simulate` ไม่แตะ `result` ของ Analytical: error ของ SPICE ล้างเฉพาะ area ผล SPICE ส่วนผล Lab 3 ยังอยู่เหมือนเดิม (คนละที่มา คนละ panel)
- −3 dB อ้างอิง gain ต่ำความถี่ของ sweep (plateau ช่วงต้น) และต้องมีจุดตัดจริงใน sweep จึงรายงาน cutoff; ไม่เช่นนั้นใช้ข้อความ "not determined in sweep range"
- ฟอร์ม SPICE แยกจากฟอร์ม Lab 3 ใช้ field `sim_vcc`, `sim_r1`, `sim_r2`, `sim_rc`, `sim_re`, `sim_rl`, `sim_cin_uf`, `sim_cout_uf`, `sim_amplitude_mv`, `sim_freq_khz`, `analysis`; หน่วยเป็น label ที่มองเห็น (V, kΩ, µF, mV, kHz) และแปลงเป็น float ก่อนสร้าง netlist
- ความถี่ของ source กระทบ `SIN` ใน `.tran` (และจุด marker บนกราฟ AC) ส่วน sweep ของ `.ac` ยังครอบช่วงกว้าง fixed เพื่อให้ Bode plot มีความหมาย; ไม่สุ่มสแกนตาม freq เดียว

### Tests และหลักฐาน

- `tests/test_spice_engine.py` (TDD): netlist ตรง fixture และไม่มี raw user text,
  validation ผิด, parser ตัวอย่าง, fake executable กรณีไม่มี/fail/empty/timeout
- `tests/test_web_simulate.py` (TDD): `/simulate` success/error ด้วย engine แบบ stub,
  66 tests เดิมยังผ่าน, ไม่มีกราฟโชว์ตอน error
- `tests/test_spice_integration.py`: `skipUnless(engine available)` รัน `.op/.ac/.tran`
  จริง ตรวจ array ไม่ว่าง/มีหน่วย/เปลี่ยน RE แล้วผลเปลี่ยน
- browser (in-app browser/tool ที่มีจริง): B1–B8 บันทึก expected/observed/evidence
  และ screenshot desktop/mobile; ถ้า Playwright MCP ไม่มีให้เขียน NOT RUN ตรงๆ
- `docs/validation.md` เพิ่มตาราง B1–B8 + เวอร์ชัน ngspice + model + ข้อจำกัด;
  `README.md` เพิ่ม install/run/reproduce; `docs/reflection.md` บันทึก 3–5 บรรทัด
  ว่า AI ทำอะไร/nักศึกษาตรวจอะไร;  attempted Impeccable ต้องบันทึกผลจริง

## Left to Builder

- รูปแบบ log จริงของ ngspice Windows ที่ติดตั้งใหม่ และจะ parse จาก `.print` หรือ raw
  ให้ตัดสินหลังรันจริง แล้วอัปเดต design นี้ถ้าต่างจากที่คาด
- รายละเอียด SVG plot (scale, tick, legend, color) ให้เหมาะกับ engineering tool
- รายละเอียด range/step ที่แม่นยำหลังทดสอบความเร็ว/เสถียร
- วิธีติดตั้ง ngspice ให้ได้ PATH บนเครื่องนี้ (installer หรือ portable + `NGSPICE_EXE`)
