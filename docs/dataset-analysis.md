# Aegis Series-7 HCS Dataset Analysis

## 1. File Inventory, Format, and Source Reliability

| File Path | Format | Extraction Strategy | Source Authority | Rev/Effective Date | Applicability to Questions | Extraction Reliability |
|-----------|--------|---------------------|------------------|--------------------|----------------------------|------------------------|
| `configuration/configuration_export.json` | JSON | Deterministic JSON parsing | Official (Machine) | FW 3.2.1 / 2026-02-03 | Current operations, interlocks | High (structured text) |
| `diagrams/system_diagram_hydraulic.pdf` | PDF (born-digital) | SVG/Layout Analysis/Vision | Official | Unstated | Current (Hydraulic layout) | Low (diagram parsing) |
| `diagrams/system_diagram_electrical.png` | PNG | Vision LLM / OCR | Official | Unstated | Current (Electrical layout) | Low (image parsing) |
| `diagrams/wiring_diagram.pdf` | PDF (born-digital) | SVG/Layout Analysis/Vision | Official | Unstated | Current (Wiring connections) | Low (diagram parsing) |
| `engineering_bulletins/ECN-1042.pdf` | PDF (born-digital) | PDF Text Extraction + LLM | Official | FW >= 3.2 | Current & Historical context | High (text) |
| `engineering_bulletins/ECN-1058.pdf` | PDF (born-digital) | PDF Text Extraction + LLM | Official | Immediate (post-3.2) | Current (Alarm A17 spec) | High (text) |
| `extra/training_slide_excerpt.pptx` | PPTX | `python-pptx` extraction + LLM | Informal | Unstated | Unofficial / Training facts | Medium (text) |
| `low_trust/site_survey_notes.docx` | DOCX | `python-docx` extraction + LLM | Field notes (unverified) | Unstated | Untrusted / Noise | Medium (text) |
| `manuals/legacy_manual_v1.html` | HTML | HTML parsing + LLM | Official (Superseded) | FW 3.0 & 3.1 | Historical facts (pre-3.2) | High (text) |
| `manuals/maintenance_manual.pdf` | PDF (born-digital) | PDF Text Extraction + LLM | Official | Rev 3 | Current operations, reset, A17 | High (text) |
| `manuals/operator_manual.pdf` | PDF (born-digital) | PDF Text Extraction + LLM | Official | Rev 4 (FW >= 3.2) | Current operations, start, ranges | High (text) |
| `noise/safety_data_sheet_hydraulic_fluid.pdf` | PDF (born-digital) | PDF Text Extraction + LLM | Official | 2025-02-11 | Irrelevant / Noise | High (text) |
| `reference/alarm_reference.pdf` | PDF (born-digital) | PDF Table Extraction + LLM | Official | Rev 5 | Current alarm rules | High (text) |
| `reference/component_register.xlsx` | XLSX | Deterministic Pandas/Excel | Official | Unstated | Current (Locations/Aliases) | High (structured text) |
| `reference/revision_history.xlsx` | XLSX | Deterministic Pandas/Excel | Official | Unstated | Release dates, FW context | High (structured text) |
| `reference/terminology_glossary.docx` | DOCX | `python-docx` extraction + LLM | Official | Rev 2 | Official definitions | High (text) |
| `scans/scanned_appendix_calibration.pdf` | PDF (scanned) | OCR (e.g., Tesseract) + LLM | Official | 2026-01-09 | Calibration records | Medium (OCR noise) |
| `screenshots/screen_01_home.png` | PNG | Vision LLM / OCR | Official (HMI) | Unstated | Current UI values | Medium (image parsing) |
| `screenshots/screen_02_alarms.png` | PNG | Vision LLM / OCR | Official (HMI) | Unstated | Current UI alarms | Medium (image parsing) |
| `screenshots/screen_03_diagnostics.png` | PNG | Vision LLM / OCR | Official (HMI) | Unstated | Current UI diagnostics | Medium (image parsing) |

## 2. Important Entities
- **System:** Aegis Series-7 Hydraulic Control System (HCS)
- **Primary Subsystem:** Hydraulic Power Unit (HPU)
- **Components:**
  - `PLC-03` (HCS Controller)
  - `IV-21` (Isolation Valve 21)
  - `PS-04` (Pressure Sensor 04)
  - `PS-04A` (Pressure Sensor 04A)
  - `PS-40` (Pressure Sensor 40)
  - `Q1` (Main Disconnect)
  - `T1` (Control Transformer)
  - `TB-7` (Terminal Block 7)
- **Software Revisions:** 3.0, 3.1, 3.2, 3.2.1, 3.3 (planned)
- **Alarms:** A17 (Hydraulic Pressure Low), A18 (Hydraulic Pressure High), A19 (Pressure Sensor Signal Invalid)
- **Engineering Changes:** ECN-1042, ECN-1058

## 3. Identifier Variants and Aliases

### Confirmed Aliases (Source verified)
- **HPU** = Hydraulic Power Unit (`terminology_glossary.docx`, `component_register.xlsx` Row 2)
- **IV-21** = Isolation Valve 21 (`component_register.xlsx` Row 3)
- **PS-04** = Pressure Sensor 04, P04, PS04 (`component_register.xlsx` Row 4)
- **PS-04A** = Pressure Sensor 04A, P04A, PS04A (`component_register.xlsx` Row 5)
- **PLC-03** = HCS Controller (`terminology_glossary.docx`)

### Candidate / Ambiguous Aliases (Require evidence or disambiguation)
- **"Hydraulic Unit", "HP unit", "Hydraulic Power Pack", "the unit", "hydraulic pack"**: Used informally across `training_slide_excerpt.pptx` (Slide 2), `operator_manual.pdf` (Section 1). May refer to HPU, but generic terms ("the unit") are potentially ambiguous.
- **"Controller", "Aegis Controller"**: Generic terms; need contextual evidence to map explicitly to PLC-03.
- **"PRESSURE XDCR"**: Present in `wiring_diagram.pdf`. A drawing note claims it refers to PS-04A, but this is a candidate alias requiring explicit extraction and verification.
- **"Isolation Valve", "IV21", "IV-21 SOLENOID"**: Candidate aliases for IV-21 found in `component_register.xlsx` and `wiring_diagram.pdf`.

## 4. Known Contradictions
- **Normal Operating Pressure:**
  - `legacy_manual_v1.html` (Section 5): 180 bar (Pre-FW 3.2).
  - `operator_manual.pdf` (Section 5): 200 bar (FW >= 3.2).
  - `site_survey_notes.docx`: Operator reports 175 bar (unverified field note).
- **Terminology Scope:**
  - `terminology_glossary.docx` explicitly states it omits "HP unit".
  - `training_slide_excerpt.pptx` (Slide 2) introduces an "Auxiliary Reservoir", which it admits is omitted from standard manuals.
- **Alarm References:**
  - `alarm_reference.pdf` (Pre-Rev 5) referenced PS-04 directly for Alarm A17.
  - `ECN-1058.pdf` (Section 1) corrects this to evaluate against "whichever pressure sensor is active".

## 5. Version-Dependent Information
- **Software Revisions Prior to 3.2:**
  - Pressure Sensor: `PS-04` (Ref: `ECN-1042.pdf` Section 1)
  - Normal Operating Pressure Setpoint: `180 bar` (Ref: `legacy_manual_v1.html` Section 5)
- **Software Revisions 3.2 and Later:**
  - Pressure Sensor: `PS-04A` (Ref: `ECN-1042.pdf` Section 1)
  - Normal Operating Pressure Setpoint: `200 bar` (Ref: `ECN-1042.pdf` Section 1, `operator_manual.pdf` Section 5)
- **Software Revision 3.2.1:**
  - Alarm A17 documentation corrected to remove specific sensor name reference (`ECN-1058.pdf`).

## 6. Documents Requiring OCR
- `scans/scanned_appendix_calibration.pdf` (Scanned record, skewed, contains moderate OCR noise)
- UI screenshots: `screen_01_home.png`, `screen_02_alarms.png`, `screen_03_diagnostics.png`
- Raster diagrams: `system_diagram_electrical.png`

## 7. Documents Requiring Image/Diagram Interpretation
- `diagrams/system_diagram_hydraulic.pdf` (Topology conveyed via shapes and interconnecting lines)
- `diagrams/system_diagram_electrical.png` (Raster schematic requiring visual interpretation of electrical connectivity)
- `diagrams/wiring_diagram.pdf` (Connectivity between blocks like PLC-03, TB-7, J-14, J-15, and field devices)
- UI Screenshots (`screen_01_home.png`, `screen_02_alarms.png`, `screen_03_diagnostics.png`) require interpreting spatial layout to map values to labels.

## 8. Mapping of Evaluation Questions to Relevant Sources
1. What must be true before starting the Hydraulic Power Unit? -> `configuration_export.json` (startup_interlocks), `operator_manual.pdf` (Sec 4.3), `training_slide_excerpt.pptx` (Slide 3)
2. What is the current normal operating pressure for the HPU, and under what conditions does that apply? -> `operator_manual.pdf` (Sec 5), `ECN-1042.pdf` (Sec 1)
3. What does alarm A17 indicate, and what are its possible causes? -> `alarm_reference.pdf` (Table), `maintenance_manual.pdf` (Sec 4)
4. Is PS-04 the same component as PS-04A? -> `ECN-1042.pdf` (Sec 1), `component_register.xlsx`
5. Which document introduced the change from PS-04 to PS-04A? -> `ECN-1042.pdf`
6. Which components connect directly to the HCS controller, according to the hydraulic schematic? -> Candidate sources: `system_diagram_hydraulic.pdf` (hydraulic/control connections) and `diagrams/wiring_diagram.pdf` (electrical connections). Both must be parsed to distinguish hydraulic from electrical connections. Neither should be assumed to contain the complete answer without verifying.
7. What action is required if alarm A17 persists for more than 10 seconds? -> `alarm_reference.pdf` (Table), `maintenance_manual.pdf` (Sec 4)
8. Under what circumstances must the controller not be reset? -> `maintenance_manual.pdf` (Sec 3), `operator_manual.pdf` (Sec 7)
9. What was the operating pressure threshold before software revision 3.2, and what changed it? -> `legacy_manual_v1.html` (Sec 5), `operator_manual.pdf` (Sec 5), `ECN-1042.pdf` (Sec 1)
10. Which alarm is associated with a pressure sensor reading below 150 bar? -> `alarm_reference.pdf` (Table), `configuration_export.json` (alarms)
11. According to the component register, what is the location of the isolation valve IV-21? -> `component_register.xlsx`
12. Does the training slide deck introduce any component or alarm not found in the manuals? -> `training_slide_excerpt.pptx` (Slide 2)
13. What sensor ID appears on the diagnostics screenshot, and does it match a known component? -> `screen_03_diagnostics.png`, `component_register.xlsx`
14. Per the revision history, when did software revision 3.2 take effect, and what changed alongside it? -> `revision_history.xlsx`, `ECN-1042.pdf`
15. What does sensor_ps04a_threshold_bar in the configuration export correspond to in the operator manual's terminology? -> `configuration_export.json`, `operator_manual.pdf` (Sec 5)
16. Does the 200 bar threshold apply to all Aegis HCS units, or only some? -> `ECN-1042.pdf` (Sec 1), `operator_manual.pdf` (Sec 5)
17. Is PS-04 the same as PS-40? -> `configuration_export.json` (sensors), `component_register.xlsx`
18. What was the pressure limit before revision 3.2? -> `legacy_manual_v1.html` (Sec 5)
19. What is the maximum continuous operating temperature of PS-04A? -> **Potential abstention case**. Must explicitly check `ECN-1042.pdf`, `component_register.xlsx`, `scanned_appendix_calibration.pdf`, and `operator_manual.pdf` before concluding the information is unavailable.
20. What is the calibration interval for the electrical system diagram's voltage sensor? -> `system_diagram_electrical.png`, `scanned_appendix_calibration.pdf`
21. Who approved engineering bulletin ECN-1058? -> `ECN-1058.pdf` (Verify visually or via text extraction).
22. What is the mean time between failures for the isolation valve IV-21? -> **Potential abstention case**. Must explicitly check `maintenance_manual.pdf`, `component_register.xlsx`, `scanned_appendix_calibration.pdf`, and diagram text before concluding the information is unavailable.
23. Is the Aegis Series-7 HCS compatible with a 3-phase 400V supply? -> Candidate sources: `system_diagram_electrical.png`, `component_register.xlsx`, `operator_manual.pdf`. Exact evidence needed: Explicit declaration of system supply requirements or tolerance in the electrical diagram/manuals. Do not infer compatibility solely from the 480V rating of Q1 or T1.

## 9. Risks and Unresolved Issues
1. **Conflicting Truths:** Distinguishing between historical facts (legacy manuals), current truth (FW 3.2+ docs), and untrusted noise (field notes) is critical. Failing to enforce provenance and version applicability will lead to hallucinations.
2. **Vision/Diagram Parsing:** Standard text extraction fails on diagrams where meaning is conveyed geometrically (lines, flow directions). Both `system_diagram_hydraulic.pdf` and `wiring_diagram.pdf` require robust spatial analysis to distinguish electrical vs. hydraulic topology.
3. **Abstention Handling:** Questions 19 and 22 represent high-risk abstention targets. The QA system must exhaustively verify all potential candidate files, tables, diagrams, and scans to confirm absence of data, explicitly citing the search space before concluding the answer is unavailable.
4. **Aliasing Challenges:** Ambiguous terms ("the unit", "Controller", "PRESSURE XDCR") cannot be merged deterministically without explicit evidence. The ingestion pipeline must represent uncertain matches rather than silently combining them.
