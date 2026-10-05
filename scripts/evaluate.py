import json
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from aegis.config import settings
from aegis.qa import QuestionAnswerService
from aegis.storage.orm import DocumentORM, ExtractionResultORM, EntityORM, AliasORM, FactORM, RelationORM, ValidityORM, EvidenceORM, ConflictORM, ResolutionResultORM

logging.basicConfig(level=logging.WARNING)

def count_records(session):
    return {
        "Documents": session.query(DocumentORM).count(),
        "ExtractionResults": session.query(ExtractionResultORM).count(),
        "Entities": session.query(EntityORM).count(),
        "Aliases": session.query(AliasORM).count(),
        "Facts": session.query(FactORM).count(),
        "Relations": session.query(RelationORM).count(),
        "Validity": session.query(ValidityORM).count(),
        "Evidence": session.query(EvidenceORM).count(),
        "Conflicts": session.query(ConflictORM).count(),
        "ResolutionResults": session.query(ResolutionResultORM).count()
    }

def main():
    engine = create_engine(settings.db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # 1. DB Immutability snapshot BEFORE
    before_counts = count_records(session)
    
    with open("fixtures/evaluation_questions.json") as f:
        questions = json.load(f)
        
    service = QuestionAnswerService(session)
    
    metrics = {
        "total": len(questions),
        "verified": 0,
        "conflicted": 0,
        "insufficient_evidence": 0,
        "not_applicable": 0,
        "unsupported_claims": 0,
        "total_factual_claims": 0,
        "claims_with_valid_evidence": 0,
        "reasons": {}
    }
    
    print("Executing Evaluation...")
    for q in questions:
        text = q["text"]
        answer, rr = service.answer_question(text)
        
        # update decision metrics
        decision_val = rr.decision.value
        
        if decision_val == "VERIFIED":
            metrics["verified"] += 1
        elif decision_val == "CONFLICTED":
            metrics["conflicted"] += 1
        elif decision_val == "INSUFFICIENT_EVIDENCE":
            metrics["insufficient_evidence"] += 1
            if not rr.query_analysis.entities and not rr.query_analysis.requested_predicate:
                diagnostic = "SEMANTIC_MAPPING_FAILURE"
            elif rr.query_analysis.entities and not rr.candidates:
                diagnostic = "NO_EVIDENCE"
            elif rr.candidates:
                diagnostic = "RETRIEVAL_FAILURE"
            else:
                diagnostic = "NO_EVIDENCE"
            metrics["reasons"][diagnostic] = metrics["reasons"].get(diagnostic, 0) + 1
        elif decision_val == "NOT_APPLICABLE":
            metrics["not_applicable"] += 1
            metrics["reasons"]["NOT_APPLICABLE"] = metrics["reasons"].get("NOT_APPLICABLE", 0) + 1
            
        # track claims
        for claim in answer.claims:
            if claim.claim_type.value == "FACTUAL":
                metrics["total_factual_claims"] += 1
                
                # claim validity
                if not claim.evidence_ids:
                    metrics["unsupported_claims"] += 1
                else:
                    valid_eids = {ev.evidence_id for ev in rr.verified_evidence}
                    if all(eid in valid_eids for eid in claim.evidence_ids):
                        metrics["claims_with_valid_evidence"] += 1
                    else:
                        metrics["unsupported_claims"] += 1
                        
    # 2. DB Immutability snapshot AFTER
    after_counts = count_records(session)
    
    immutability_passed = before_counts == after_counts
    
    print("\n================ EVALUATION METRICS ================\n")
    print(f"Total Questions: {metrics['total']}")
    print(f"Verified Answers: {metrics['verified']}")
    print(f"Conflicted Answers: {metrics['conflicted']}")
    print(f"Insufficient Evidence: {metrics['insufficient_evidence']}")
    print(f"Not Applicable: {metrics['not_applicable']}")
    
    print("\nAbstention Reasons:")
    for k, v in metrics["reasons"].items():
        print(f"  {k}: {v}")
    
    print(f"\nTotal Factual Claims: {metrics['total_factual_claims']}")
    print(f"Unsupported Claims: {metrics['unsupported_claims']}")
    
    prov_cov = (metrics['claims_with_valid_evidence'] / metrics['total_factual_claims']) * 100 if metrics['total_factual_claims'] > 0 else 100
    print(f"Provenance Coverage: {prov_cov:.1f}%")
    
    print(f"\nDatabase Immutability Passed: {immutability_passed}")
    if not immutability_passed:
        print("Before:", before_counts)
        print("After:", after_counts)
        
if __name__ == "__main__":
    main()
