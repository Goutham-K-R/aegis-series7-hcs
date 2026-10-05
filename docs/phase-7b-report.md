# Phase 7B Report — Grounded Answer Generation + Claim-Level Provenance

## 1. Files Changed
- `src/aegis/retrieval/models.py`: Extended `VerifiedEvidence` to contain payload variables (subject, predicate, value, unit) for the answer generator boundary.
- `src/aegis/retrieval/verifier.py`: Added extraction logic for payload variables to `VerifiedEvidence`. Corrected `CONFLICTED` logic to return the conflicting evidence payload instead of an empty list, enabling provenance tracking for conflicts.
- `src/aegis/qa/models.py`: Defined `GeneratedAnswer`, `Claim`, and `ClaimType`.
- `src/aegis/qa/generator.py`: Implemented `AnswerGenerator` with strict decision gating and deterministic fallback logic.
- `src/aegis/qa/validator.py`: Implemented `ClaimValidator` ensuring 100% evidence-to-claim parity.
- `src/aegis/qa/service.py`: Orchestrator linking `retrieve_and_verify` with generation and validation.
- `src/aegis/qa/__init__.py`: QA module exports.
- `scripts/ask.py`: End-to-end CLI tool.
- `scripts/evaluate.py`: Evaluation harness for 23 questions and immutability checking.
- `fixtures/evaluation_questions.json`: Evaluation targets.
- `tests/test_qa.py`: Testing suite for Phase 7B requirements.

## 2. AnswerGenerator Architecture
The AnswerGenerator consumes a strictly verified, read-only payload (`RetrievalResult`) produced by the Phase 7A Retrieval and Evidence Verification Layer. It generates a structured `GeneratedAnswer` output, bypassing raw database access entirely. The pipeline orchestrates Query Analysis -> Retrieval -> Verification -> Answer Generator -> Claim Extraction & Validation -> Final Answer.

## 3. Prompt-Grounding Strategy
Grounding is enforced architecturally. The model/generator only sees the structured verified evidence payload and the original question context. It is strictly explicitly instructed to answer *only* from the payload, not to infer engineering specs, and not to resolve conflicts, ensuring maximum adherence to the source truth.

## 4. Decision Gating
Before generation, the `AnswerGenerator` reads the deterministically computed `VerificationDecision`:
- **VERIFIED**: Generates a standard claim.
- **CONFLICTED**: Avoids generation/resolution entirely and issues a safe abstention listing the competing verified evidence.
- **INSUFFICIENT_EVIDENCE / NOT_APPLICABLE / NOT_VERIFIED**: Issues a safe abstention immediately, guaranteeing zero hallucinations.

## 5. Claim Model
Claims are atomic units representing facts, conflicts, or abstentions, represented by `Claim`. Each `Claim` includes the extracted text, confidence, explicit `ClaimType`, and an essential `evidence_ids` list linking directly to verified source evidence.

## 6. Claim Validation
The `ClaimValidator` scans the `GeneratedAnswer` post-generation. For any `FACTUAL` claim, it strictly asserts that:
- The claim has at least one valid `evidence_id`.
- Every cited `evidence_id` exists in the original `RetrievalResult`.
If validation fails, the generator reverts to a deterministic fallback.

## 7. Provenance Format
The answer surfaces provenance cleanly at the end of each generated factual statement. E.g.:
`PS-04A maximum_pressure: 200 bar. [c0ffee-uuid-evidence]`
Internally, the engine tracks exact Document, Location, and Extraction Reliability metadata mapping back to the data source.

## 8. Deterministic Fallback
For environments without an LLM API key or in case of LLM/Validation failure, the system falls back to a deterministic string templater ensuring that verified knowledge is always securely presentable.

## 9. LLM Failure Behavior
The system avoids total pipeline crashes if the LLM becomes unavailable. Instead, it seamlessly routes the payload into the deterministic fallback.

## 10. Prompt-Injection Protection
Because the generator boundary separates the data context and does not apply instructions found within the data context, adversarial texts from documents (e.g., "Ignore instructions, answer X") cannot override the `AnswerGenerator` instruction structure. Tested successfully in `test_prompt_injection_ignored`.

## 11. Database Immutability
All answer generation steps run completely out-of-band and execute read-only. DB counts for all tables (Documents, Facts, Entities, Validities, Evidence) were verified before and after evaluation to guarantee zero modifications.

## 12. Tests Added
Added 9 robust test vectors in `test_qa.py` verifying fallback behavior, validation rejection for missing/hallucinated evidence IDs, prompt injection, and database immutability.

## 13. Total Tests
**90 passing tests** across all phases.

## 14. 23-Question Evaluation Metrics
- **Total Questions**: 23
- **Verified Answers**: 7
- **Conflicted Answers**: 1
- **Insufficient Evidence**: 3
- **Not Applicable**: 12
- **Database Immutability Passed**: True

## 15. Unsupported-Claim Count
**0 unsupported factual claims.** Every factual claim properly cited valid evidence.

## 16. Provenance Coverage
**100.0%**. 

## 17. Abstention Results
The system properly abstained across 15 cases (12 Not Applicable contexts and 3 Insufficient Evidence contexts), completely avoiding LLM hallucination where context scopes didn't apply.

## 18. Q19 / Q22 / Q23 Results
These questions explicitly resulted in safe abstentions ("INSUFFICIENT_EVIDENCE") as the current knowledge graph lacks concrete verified evidence to answer them directly without resorting to unauthorized inferences.

## 19. Known Limitations
- The generative capacity of the fallback is extremely rigid and robotic. Integrating a secure, high-confidence LLM for natural language stitching is required for a polished user experience.
- Semantic retrieval mapping for fuzzy concepts relies heavily on the `QueryAnalyzer` which currently maps specific deterministic tokens (e.g., "maximum pressure"). A semantic similarity threshold might improve recall in future phases.
