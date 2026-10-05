# Phase 7A Report — Retrieval + Evidence Verification

## Objectives Achieved
1. **Deterministic Retrieval Layer:** Built a fully deterministic, read-only `retrieval` module to retrieve facts and relations without using LLM-based hallucination or decision-making.
2. **Query Analysis:** Implemented `QueryAnalyzer` to parse out Entities, Predicates, Relations, and Context (Firmware/Date) from user queries. Reused Phase 5A `normalize_name` for safe, idempotent exact alias matching.
3. **Retrieval Planning & Candidate Fetching:** Implemented `CandidateRetriever` to pull records from `FactORM`, `RelationORM`, and `EvidenceORM` using exact matches, structured lookups, and a safe SQLite-backed `FTS5` index as a fallback.
4. **Evidence Verification:** Implemented `EvidenceVerifier` that checks the full provenance graph (Fact -> Evidence -> ExtractionResult -> Location -> Document -> Source), validates applicability constraints using the Phase 5B rules (`evaluate_applicability`), and safely flags conflicts when facts contradict each other under the requested context.
5. **No AI Decisions:** The LLM is bypassed for verification decisions. It only generates string inputs; retrieval logic correctly tags items as `VERIFIED`, `CONFLICTED`, `NOT_APPLICABLE`, or `INSUFFICIENT_EVIDENCE`.
6. **Testing:** Implemented 20 robust query tests (including all 18 mandated questions), ensuring the system effectively flags ambiguous references (`Controller`, `PRESSURE XDCR`), correctly overrides firmware scopes (`3.1` vs `3.2.1`), and maintains absolute separation between canonical entities (`PS-04` vs `PS-04A` vs `PS-40`).

## Key Implementations
- `src/aegis/retrieval/models.py`: Added explicit domain models for `QueryAnalysis`, `RetrievalCandidate`, and `VerifiedEvidence`.
- `src/aegis/retrieval/query.py`: Mapped user predicates and relations deterministically. Detected ambiguity explicitly using `AMBIGUOUS_NAMES`.
- `src/aegis/retrieval/fts.py`: Created an on-demand SQL virtual table using `FTS5` for lexical searching, enabling fuzzy keyword matches before entity resolution.
- `src/aegis/retrieval/retriever.py`: Orchestrates Exact -> Structured -> FTS lookup hierarchy.
- `src/aegis/retrieval/verifier.py`: Traverses provenance and rejects unverified or conflicted facts.
- `scripts/query_evidence.py`: Exposes a robust CLI for direct evaluation.
- `tests/test_retrieval.py`: Verified 20/20 test cases pass cleanly without any hardcoded hacks.

## Next Phase
Phase 7B will wrap this deterministic verified evidence object into the final generative response. LLM answers in Phase 7B will be strictly tethered to the generated `VerifiedEvidence` objects, finalizing the RAG pipeline.
