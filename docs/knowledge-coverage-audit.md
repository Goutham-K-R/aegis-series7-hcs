# Phase 4A Knowledge Coverage Audit

This audit evaluates the output of the Phase 4 semantic knowledge extraction implementation. It compares the structured knowledge candidates generated against the raw extracted text units (from Phase 3C) to determine coverage ratios and identify under-extraction rules.

## 1. Extraction Coverage Table

| Document | Format | Method | Reliability | Units | Candidates (Ev Links) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| evaluation-questions.pdf | PDF | DETERMINISTIC | MEDIUM | 1 | 3 |
| task-description.pdf | PDF | DETERMINISTIC | MEDIUM | 3 | 0 |
| configuration_export.json | JSON | DETERMINISTIC | HIGH | 25 | 2 |
| system_diagram_electrical.png | PNG | VISION_MODEL | LOW | 1 | 0 |
| system_diagram_hydraulic.pdf | PDF | DETERMINISTIC | MEDIUM | 1 | 1 |
| wiring_diagram.pdf | PDF | DETERMINISTIC | MEDIUM | 1 | 2 |
| ECN-1042.pdf | PDF | DETERMINISTIC | MEDIUM | 1 | 2 |
| ECN-1058.pdf | PDF | DETERMINISTIC | MEDIUM | 1 | 0 |
| training_slide_excerpt.pptx | PPTX | DETERMINISTIC | HIGH | 19 | 0 |
| site_survey_notes.docx | DOCX | DETERMINISTIC | HIGH | 8 | 0 |
| legacy_manual_v1.html | HTML | DETERMINISTIC | HIGH | 30 | 3 |
| maintenance_manual.pdf | PDF | DETERMINISTIC | MEDIUM | 1 | 1 |
| operator_manual.pdf | PDF | DETERMINISTIC | MEDIUM | 2 | 3 |
| safety_data_sheet_hydraulic_fluid.pdf | PDF | DETERMINISTIC | MEDIUM | 2 | 0 |
| alarm_reference.pdf | PDF | DETERMINISTIC | MEDIUM | 2 | 1 |
| component_register.xlsx | XLSX | DETERMINISTIC | HIGH | 78 | 0 |
| revision_history.xlsx | XLSX | DETERMINISTIC | HIGH | 24 | 0 |
| terminology_glossary.docx | DOCX | DETERMINISTIC | HIGH | 24 | 1 |
| scanned_appendix_calibration.pdf | PDF | DETERMINISTIC | LOW | 1 | 0 |
| screen_01_home.png | PNG | VISION_MODEL | LOW | 1 | 0 |
| screen_02_alarms.png | PNG | VISION_MODEL | LOW | 1 | 0 |
| screen_03_diagnostics.png | PNG | VISION_MODEL | LOW | 1 | 0 |

**Total Eligible Units**: 228  
**Total Evidence Links Generated**: 19  
**Coverage Ratio**: ~8.3%

## 2. Current Knowledge Inventory

### Entities
- 4ea44e7b-4a63-47a9-93b6-733c5b216701: PS-04A (COMPONENT)
- e72ba4c0-b8f4-44b5-b3c9-40cd39f7a1d4: HPU (SYSTEM)
- edcf09ba-367e-4064-9093-cb8d3d44da85: PLC-03 (COMPONENT)
- b119f0e4-20e3-4ea9-b71c-b3e2443743e2: PS-04 (COMPONENT)

### Facts
- 04576ce3-dead-4535-99f1-40ecf085f0a2: PS-04A maximum_pressure 150 bar [ASSERTED]
- 52c5ed5d-acb5-41c4-8138-0ec4e3fea3d6: HPU voltage_compatibility 400 V [ASSERTED]
- 01aa08e2-707f-48df-a3cc-0becce9e78f7: HPU firmware_version 3.2.1 None [ASSERTED]
- 79a91a86-8408-4bcc-ae9d-623830d25e37: HPU configured_pressure 50 None [ASSERTED]
- 3e465e42-9c8d-4536-a0fb-3f162c638632: PS-04A maximum_pressure 180 bar [ASSERTED]
- 0e43c3de-c335-49de-ab8a-5a4a4828d28a: HPU maximum_pressure 180 bar [ASSERTED]
- 7bad80ec-b38b-436b-89de-cb7cd4d56a3f: PS-04 maximum_pressure 180 bar [ASSERTED]
- 65f66886-cd63-49be-8066-f37e528a0ce7: PS-04A maximum_pressure 200 bar [ASSERTED]
- 7e367dce-5724-472d-8a95-ef9a29a8a785: PS-04A maximum_pressure 50 bar [ASSERTED]
- 4cd4f7f0-dd9c-4584-9c20-c7f1ac1ff4f9: PS-04A maximum_pressure 200 bar [ASSERTED]
- aef8a163-9d35-4c50-8608-9b351f29c686: HPU maximum_pressure 50 bar [ASSERTED]
- 9d47e0e2-7b2f-4388-9c50-fd1d93844153: PS-04A maximum_pressure 150 bar [ASSERTED]

### Aliases
- 35284338-c4a2-4153-8b39-20baeff0231f: HPU = Hydraulic Power Unit (Confirmed: True)
- d5db8e88-9559-4642-9a09-f389e62207ef: HPU = Hydraulic Power Unit (Confirmed: True)
- fb6ff238-67be-45f0-8496-1b08a4a1ad2a: PS-04A = PRESSURE XDCR (Confirmed: False)
- ec430c38-479a-4a2e-ae6f-f07fb956de43: HPU = Hydraulic Power Unit (Confirmed: True)
- 396d2582-8b45-4822-bebc-a5f2a4f9c99c: HPU = Hydraulic Power Unit (Confirmed: True)
- 195e0dfe-8452-40dd-91d0-713ef75ba783: HPU = Hydraulic Power Unit (Confirmed: True)

### Relations
- 349be71d-59a0-4625-b56d-e42a9a031360: PLC-03 ELECTRICALLY_CONNECTED_TO PS-04A

## 3. Expected Entity Coverage

| Entity | Status | Source Example (Missed in Extraction) |
| :--- | :--- | :--- |
| Aegis Series-7 HCS | MISSING | `configuration_export.json` -> `$.export_metadata.system` |
| HPU | PRESENT | N/A |
| PLC-03 | PRESENT | N/A |
| IV-21 | MISSING | `component_register.xlsx` -> `Sheet: Components, Cell: A3` |
| PS-04 | PRESENT | N/A |
| PS-04A | PRESENT | N/A |
| PS-40 | MISSING | `component_register.xlsx` -> `Sheet: Components, Cell: A6` |
| Q1 | MISSING | `component_register.xlsx` -> `Sheet: Components, Cell: A12` |
| T1 | MISSING | `component_register.xlsx` -> `Sheet: Components, Cell: A13` |
| TB-7 | MISSING | `component_register.xlsx` -> `Sheet: Components, Cell: A11` |
| A17 | MISSING | `component_register.xlsx` -> `Sheet: Components, Cell: A8` |
| A18 | MISSING | `component_register.xlsx` -> `Sheet: Components, Cell: A9` |
| A19 | MISSING | `component_register.xlsx` -> `Sheet: Components, Cell: A10` |
| ECN-1042 | MISSING | `revision_history.xlsx` -> `Sheet: Revision History, Cell: D4` |
| ECN-1058 | MISSING | `ECN-1058.pdf` -> `Page 1` |
| firmware 3.0 | MISSING | (Not caught by regex) |
| firmware 3.1 | MISSING | (Not caught by regex) |
| firmware 3.2 | MISSING | `component_register.xlsx` -> `Sheet: Components, Cell: F5` |
| firmware 3.2.1 | PRESENT | Extracted from `configuration_export.json` |
| planned firmware 3.3| MISSING | (Not caught by regex) |

## 4. Expected Fact Coverage

- **maximum pressure**: PRESENT
- **180 bar**: PRESENT
- **200 bar**: PRESENT
- **175 bar**: MISSING. Source text exists in `site_survey_notes.docx` but rule-based extraction missed it because it didn't match the narrow "maximum pressure" regex pattern.
- **PS-04**: PRESENT
- **PS-04A**: PRESENT
- **alarm A17/A18/A19**: MISSING. The tabular lists in `component_register.xlsx` and mentions in PDFs were entirely skipped because the XLSX and text extractors lack generic entity detection.
- **firmware applicability**: MISSING. Mentions of "effective software rev 3.2" exist in XLSX but produced no candidates.
- **component specifications**: MISSING. Details about T1 or IV-21 are present but completely skipped.
- **electrical supply / 400 V / 480 V**: MISSING. Present in diagrams/scans which were skipped (Requires OCR), and missed in standard text if formatted slightly differently.
- **transformer T1**: MISSING. Present in XLSX.
- **IV-21**: MISSING. Present in multiple documents (legacy manual, site survey, component register) but missed by rules.
- **controller connections**: AMBIGUOUS. Present in diagrams (Requires Diagram Interpretation). One relation generated via text rule.
- **revision changes**: MISSING. ECN history exists in `revision_history.xlsx` but completely missed.
- **temperature limits**: MISSING. Mention exists but was ignored by extraction rules.
- **MTBF**: MISSING. Present in raw text but ignored.

## 5. Missed Candidate Evidence (Under-extraction Findings)

The current rule-based architecture (`KnowledgeExtractorFactory`) exhibits severe **under-extraction**. Important explicit domain statements exist in the `ExtractionResult` records but are failing to produce candidates.

**Examples:**
- `revision_history.xlsx / Cell: C4` contains: *"Pressure sensor PS-04 replaced by PS-04A. Normal HPU discharge pressure setpoint changed from 180 bar..."*
  *Why missed?* The XLSX extractor only specifically checked if the cell was precisely a number followed by "bar". It missed the dense historic facts.
- `site_survey_notes.docx / Paragraph 4` contains: *"Checked the gauge on the local panel and it read about 175 bar during a normal run, not 180 like the..."*
  *Why missed?* The regex strictly required "maximum pressure" preceding the bar measurement.
- `component_register.xlsx / Cell: A3` contains: *"IV-21"*
  *Why missed?* The extractor lacks an entity generation rule for anything other than PS-04(A) and HPU.
  
**Finding:** Hardcoded deterministic regex rules are insufficient for extracting the complex, interconnected engineering semantics of the dataset.

## 6. OCR / Diagram Limitations

5 documents correctly flagged as `REQUIRES_OCR` or `VISION_MODEL` (e.g. `system_diagram_electrical.png`, `scanned_appendix_calibration.pdf`). No hallucinations were attempted for these, which is working safely by design. Facts embedded purely in these files (like 400V vs 480V ratings in schematics) correctly wait for a future vision phase.

## 7. Conflict-Preservation Verification

- **180 bar vs 200 bar**: Both values were successfully extracted as `ASSERTED` facts against `PS-04A` and `HPU` across multiple documents without collapsing into a single true value.
- **PS-04 vs PS-04A**: Retained as separate UUID components.
- **Ambiguous Aliases**: "PRESSURE XDCR" correctly marked `is_confirmed: False` and tied to PS-04A solely as a candidate. 
*Status*: **VERIFIED SAFE.**

## 8. Relation Audit

**Relation Generated:** `PLC-03 ELECTRICALLY_CONNECTED_TO PS-04A`
- **Source:** Likely a manual or ECN PDF.
- **Why generated:** Tripped a hardcoded rule (`if "PLC-03" in text and "connected to" in text...`).
- **Safety:** **UNSAFE.** This relation was inferred purely from text co-occurrence. In an industrial context, "not connected to" or "previously connected to" would trigger this exact same rule, falsely asserting an active electrical bond.

## 9. Recommendations for Phase 4B

The Phase 4A diagnostic audit reveals that while the deterministic structure is **safe** and **preserves provenance perfectly**, it suffers from massive **under-extraction** (~8.3% coverage).

**Recommendations for Phase 4B:**
1. **Implement the LLM Semantic Adapter**: Replace `RuleBasedTextExtractor` with a carefully prompted LLM parser using strictly validated Pydantic outputs (`FactCandidate`, `EntityCandidate`). 
2. **Bind the LLM Output**: Guarantee the LLM only operates on single `ExtractionResult` units at a time to maintain the exact 1-to-1 provenance map.
3. **Expand XLSX Extraction**: Treat `component_register.xlsx` and `revision_history.xlsx` as relational tables rather than isolated cells, parsing rows into structured entities and events deterministically before falling back on LLMs.
