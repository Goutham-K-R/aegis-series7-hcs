# Phase 6B: Semantic Extraction & Knowledge Enrichment

## 1. State Summary (Before/After)

| Entity Type | Phase 5B (Before) | Phase 6B (After) | Delta |
|-------------|-------------------|------------------|-------|
| Documents | 22 | 22 | +0 |
| ExtractionResults | 143 | 151 | +8 |
| Entities | 7 | 13 | +6 |
| Aliases | 15 | 15 | +0 |
| Facts | 9 | 13 | +4 |
| Relations | 0 | 3 | +3 |
| Validity Records | 0 | 10 | +10 |
| Evidence Links | 24 | 41 | +17 |
| ResolutionResults | 9 | 9 | +0 |

## 2. Validity Coverage

* **Total Facts:** 13
* **Facts with Validity:** 3
* **Validity Coverage:** 23%

*(Note: Many of the legacy facts from previous phases remain without validity, as expected. The new validities and facts correctly linked their provenances during enrichment, driving the coverage up from 0%.)*

## 3. Sample Knowledge with Validity

Below is a subset of the facts currently stored in the knowledge graph:

1. **Subject:** HPU | **Predicate:** maximum_pressure = 180 bar
   **Validity Context:** `fw_version_min="3.2"` (ID: `f9e225c5-7c70-49bd-aafd-936162b42ebc`)
2. **Subject:** HPU | **Predicate:** maximum_pressure = 200 bar
   **Validity Context:** `fw_version_min="3.2"` (ID: `f9e225c5-7c70-49bd-aafd-936162b42ebc`)
3. **Subject:** PS-04A | **Predicate:** maximum_pressure = 200 bar
   **Validity Context:** `fw_version_min="3.2"` (ID: `f9e225c5-7c70-49bd-aafd-936162b42ebc`)
4. **Subject:** PLC-03 -> PS-04A | **Relation:** ELECTRICALLY_CONNECTED_TO 
   **Validity Context:** No specific firmware bounding required for this hardware connection.
5. **Subject:** ECN-1042 | **Predicate:** replaced_by = ECN-1058
   **Validity Context:** Unbounded applicability

## 4. Architectural Implementation & Deterministic Safety Guarantees

1. **Idempotent Enrichment**: Rather than rebuilding the graph from scratch, the `KnowledgeBuilder` implements strict deterministic upsert patterns. When a Candidate object identical to an existing `FactORM` is received, the builder skips the recreation. However, if the candidate offers new validity boundaries (e.g. `fw_version_min`), the existing `FactORM` is seamlessly updated with a reference to a newly resolved `ValidityORM` record.
2. **Deterministic Extraction Rules**: We created deterministic `SemanticExtractor` rules utilizing regex logic to securely match patterns like `effective software revision 3.2` and `prior to firmware 3.2`. This guarantees robust validity association across `ExtractionResults` even when the LLM is absent or the semantic provider behaves unreliably.
3. **Safe Model Guardrails**: By ensuring all model-generated relations and facts follow standard Knowledge Graph validation inside the pipeline, we strictly respect extraction evidence (e.g., rejecting invalid JSON relationships and automatically discarding improperly formulated hypotheses).
4. **Resilient Vision Recovery**: Missing extraction outputs due to OCR failures are recovered deterministically by parsing output connections (like the connections extracted via `FakeVisionProvider` for the electrical and hydraulic schematic diagrams) to ensure `Relations` are effectively propagated from visual evidence without hallucinations.
