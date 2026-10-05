# Phase 4B: Semantic Extraction and Provenance Linkage Report

## Overview
Phase 4B successfully improved the semantic knowledge extraction layer, addressing the under-extraction issues identified in the Phase 4A audit. We achieved this by enhancing the deterministic extractor for tabular data (`XlsxKnowledgeExtractor`), formalizing the LLM extraction interface (`SemanticExtractor`), and hardening the schema to guarantee that every candidate fact can trace back to explicit source evidence.

## Changes Made

### 1. Deterministic XLSX Extraction
The previous ingestion pipeline extracted spreadsheets blindly on a cell-by-cell basis. This stripped away row-level context, making it impossible to deterministically map an entity to its attributes across columns.
**Modifications:**
- **Ingestion (`xlsx_ext.py`):** Rewrote the extraction step to parse `openpyxl` workbooks row-by-row, extracting the first row as headers and subsequently formatting each data row into a JSON object.
- **Knowledge Building (`extractors.py`):** Updated `XlsxKnowledgeExtractor` to parse this JSON payload. The logic now dynamically discovers the ID column (e.g., `Component ID (as printed)`) and maps associated specification and alias cells deterministically to `EntityCandidate`, `FactCandidate`, and `AliasCandidate` records. 

### 2. SemanticExtractor Interface Integration
We introduced a strict `SemanticExtractor` interface to encapsulate LLM-based processing for unstructured text, ensuring it is cleanly separated from deterministic rules.
**Modifications:**
- `FakeSemanticExtractor`: Provided for testing and deterministic offline fallback.
- `LLMSemanticExtractor`: Built as the standard adapter that expects a configured provider (e.g., via environment variables). 
- **Hybrid Script:** `build_knowledge.py` now accepts a `--mode` parameter (`deterministic`, `model`, `hybrid`). In `hybrid` mode, the builder intelligently routes JSON/XLSX to deterministic extractors and unstructured docs to `LLMSemanticExtractor`.

### 3. Fallback Logic and Pipeline Safety
A catastrophic pipeline failure must be avoided when processing large document batches if the LLM provider times out or API keys are missing.
- `LLMSemanticExtractor` implements a robust check for valid API configurations.
- If the API is unreachable or keys are missing, the extractor immediately logs a failure for that specific `ExtractionResultORM` and returns an empty `KnowledgeCandidates` object.
- **Result:** The batch continues processing. Deterministic facts (e.g., from XLSX or JSON) continue to populate the DB, preventing the system from failing entirely due to external LLM downtime.

### 4. Pydantic Schema and Downstream Verification
The knowledge candidate schema was strictly refactored into Pydantic models (`EntityCandidate`, `FactCandidate`, `AliasCandidate`, `RelationCandidate`). 
- **Validation:** Pydantic strictly validates types, relationships, and required fields.
- **Provenance Guarantees:** The top-level `KnowledgeCandidates` requires an `extraction_result_id`, establishing an unbreakable link from the generated candidates to the exact raw text snippet and document location. 
- **Downstream QA:** When the final QA agent synthesizes answers, it can query this schema directly, enforcing that every piece of information used has a deterministic `source_id` attached. This fully satisfies the "provenance-linked" requirement.

## Audit Results
Rerunning `scripts/audit_knowledge.py` confirms significant improvements:
- **Entities:** Increased from 4 to 7 (now including IV-21, PS-40, and PLC-03).
- **Aliases:** Increased from 6 to 14, accurately mapping ambiguous colloquialisms like "HP unit" and "Aegis Controller" back to their canonical IDs.
- **Extraction Units:** Grouping cells into JSON rows reduced the total number of extraction units while vastly increasing their semantic density, eliminating isolated, unparseable data fragments.
