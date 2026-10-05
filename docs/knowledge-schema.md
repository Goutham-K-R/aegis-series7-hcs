# Aegis Series-7 HCS Knowledge Schema

This document outlines the explicit typed models for the knowledge representation, designed independently of any specific LLM implementation.

## 1. Entity Definitions

**`Document`**
- `id`: UUID
- `filename`: String (e.g., "operator_manual.pdf")
- `format`: Enum (PDF, PNG, JSON, XLSX, HTML, DOCX, PPTX)
- `hash`: String (SHA-256 for integrity)

**`DocumentLocation`**
- `id`: UUID
- `document_id`: UUID (FK to Document)
- `location_type`: Enum (PAGE, SHEET, SLIDE, SECTION, CELL, PIXEL_BOUNDS)
- `location_value`: String (e.g., "Page 5", "Sheet1:B12")

**`Source`**
*Separates metadata concepts to prevent collapsing trust into a single score.*
- `id`: UUID
- `document_id`: UUID
- `authority`: Enum (OFFICIAL, INFORMAL, UNVERIFIED)
- `revision`: String (e.g., "Rev 4")
- `effective_date`: Date / String (e.g., "2025-09-30")
- `applicability`: String (e.g., "Applies to FW >= 3.2")
- `relevance_score`: Float (0.0 to 1.0) - *Classifies noise independently of authority*

**`ExtractionResult`**
- `id`: UUID
- `document_location_id`: UUID
- `method`: Enum (DETERMINISTIC, OCR, VISION_MODEL, LLM_TEXT, HYBRID)
- `raw_text`: String (Exact text or markup extracted)
- `extraction_reliability`: Enum (HIGH, MEDIUM, LOW)

## 2. Fact Schema

**`Fact`**
*The atomic unit of knowledge.*
- `id`: UUID
- `subject_id`: UUID (FK to Entity)
- `predicate`: String (e.g., "has_operating_pressure")
- `value`: String/JSON (e.g., "200")
- `unit`: String (e.g., "bar", "seconds")
- `validity_id`: UUID (FK to Validity context, optional)
- `status`: Enum (ASSERTED, CONTESTED, WITHDRAWN) - *Historical facts remain ASSERTED; their Validity determines applicability to a query.*

## 3. Provenance Schema

**`Evidence`**
*Links a Fact/Entity/Alias/Relation to its origin.*
- `id`: UUID
- `fact_id`: UUID (FK to Fact, optional)
- `entity_id`: UUID (FK to Entity, optional)
- `alias_id`: UUID (FK to Alias, optional)
- `relation_id`: UUID (FK to Relation, optional)
- `extraction_result_id`: UUID (FK to ExtractionResult)
- `source_id`: UUID (FK to Source)
- `confidence`: Float (0.0 to 1.0) - *Confidence in the extraction/interpretation*

## 4. Entity & Alias Model

**`Entity`**
- `id`: UUID
- `canonical_name`: String (e.g., "PS-04A")
- `entity_type`: Enum (COMPONENT, SYSTEM, ALARM, DOCUMENT, MEASUREMENT)

**`Alias`**
*Explicit mapping of variants to canonical entities.*
- `id`: UUID
- `canonical_entity_id`: UUID (FK to Entity)
- `alias_name`: String (e.g., "the unit", "PRESSURE XDCR")
- `is_confirmed`: Boolean (True if hard evidence exists, False if uncertain/candidate)
- `confidence`: Float (0.0 to 1.0)
- `resolution_method`: Enum (EXACT, REGISTER, DOCUMENT, CONTEXT, MODEL)

## 5. Revision/Validity Model

**`Validity`**
*Defines the boundaries where a Fact holds true.*
- `id`: UUID
- `fw_version_min`: String (e.g., "3.2")
- `fw_version_max`: String (optional, e.g., "3.1")
- `date_effective`: Date (optional)
- `date_superseded`: Date (optional)

## 6. Conflict Model

**`Conflict`**
*Explicitly links mutually exclusive claims.*
- `id`: UUID
- `fact_a_id`: UUID
- `fact_b_id`: UUID
- `conflict_type`: Enum (VERSION_OVERRIDE, CONTRADICTION, TERMINOLOGY_MISMATCH)
- `resolution_note`: String (To be used by the deterministic Evidence Verification component)

## 7. Relation Model

**`Relation`**
*Connects two entities (e.g., physical/electrical connectivity).*
- `id`: UUID
- `source_entity_id`: UUID
- `target_entity_id`: UUID
- `relation_type`: Enum (ELECTRICALLY_CONNECTED_TO, HYDRAULICALLY_CONNECTED_TO, PART_OF)
- `validity_id`: UUID (Optional)
- `confidence`: Float (0.0 to 1.0)

## 8. Resolution Result

**`ResolutionResult`**
*The auditable, deterministic output passed to the LLM Answerer.*
- `id`: UUID
- `query_id`: UUID
- `candidate_fact_id`: UUID
- `decision`: Enum (SELECTED, CONFLICTED, INSUFFICIENT_EVIDENCE, NOT_APPLICABLE)
- `reason`: String (Detailed reason for the decision, factoring in authority, dates, etc.)
- `applicability_status`: String
- `conflict_status`: String
- `confidence`: Float (0.0 to 1.0)
- `evidence_ids`: Array of UUID (FKs to Evidence)

---

## 9. Example Records

### Example PS-04 / PS-04A / PS-40 Entities
Distinct entities, preventing invalid merging.

```json
[
  { "id": "e1", "canonical_name": "PS-04", "entity_type": "COMPONENT" },
  { "id": "e2", "canonical_name": "PS-04A", "entity_type": "COMPONENT" },
  { "id": "e3", "canonical_name": "PS-40", "entity_type": "COMPONENT" }
]
```

### Example Aliases (Confirmed vs. Ambiguous)
```json
[
  {
    "id": "a1",
    "canonical_entity_id": "e2",
    "alias_name": "P04A",
    "is_confirmed": true,
    "confidence": 1.0,
    "resolution_method": "REGISTER"
  },
  {
    "id": "a2",
    "canonical_entity_id": "e2",
    "alias_name": "PRESSURE XDCR",
    "is_confirmed": false,
    "confidence": 0.6,
    "resolution_method": "DOCUMENT"
  }
]
```

### Example Versioned Facts (180 bar vs 200 bar)

**Validity Contexts**
```json
[
  { "id": "v1", "fw_version_max": "3.1" },
  { "id": "v2", "fw_version_min": "3.2" }
]
```

**Facts**
*Historical facts are NOT globally marked as superseded. Both remain ASSERTED; applicability is resolved via Validity at query time.*
```json
[
  {
    "id": "f1",
    "subject_id": "HPU",
    "predicate": "normal_operating_pressure",
    "value": "180",
    "unit": "bar",
    "validity_id": "v1",
    "status": "ASSERTED"
  },
  {
    "id": "f2",
    "subject_id": "HPU",
    "predicate": "normal_operating_pressure",
    "value": "200",
    "unit": "bar",
    "validity_id": "v2",
    "status": "ASSERTED"
  }
]
```

### Example Resolution Result (Handling a Conflict)
A field engineer reports 175 bar (unverified), contradicting official specs (200 bar). The deterministic resolver evaluates all factors and outputs this auditable result:

```json
{
  "id": "rr1",
  "query_id": "q123",
  "candidate_fact_id": "f2", // 200 bar Official Fact
  "decision": "SELECTED",
  "reason": "Official authority and FW >= 3.2 applicability overrides unverified field note. Conflict resolved.",
  "applicability_status": "APPLICABLE",
  "conflict_status": "RESOLVED_FAVORING_CURRENT_CANDIDATE",
  "confidence": 0.95,
  "evidence_ids": ["ev_official_manual", "ev_survey_notes"]
}
```

### Example Relation with Provenance
```json
{
  "id": "r1",
  "source_entity_id": "e_plc03",
  "target_entity_id": "e_ps04a",
  "relation_type": "ELECTRICALLY_CONNECTED_TO",
  "confidence": 0.85
}
```

### Example Provenance & Evidence
Linking the Relation to its exact diagram extraction.

```json
{
  "id": "ev2",
  "relation_id": "r1",
  "source_id": "src_wiring_diagram", 
  "extraction_result_id": "ext_vision_model_run",
  "confidence": 0.9
}
```
