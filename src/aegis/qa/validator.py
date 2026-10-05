import logging
from aegis.retrieval.models import RetrievalResult
from aegis.qa.models import GeneratedAnswer, ClaimType

logger = logging.getLogger("aegis_qa_validator")

class ClaimValidator:
    def validate(self, answer: GeneratedAnswer, rr: RetrievalResult) -> GeneratedAnswer:
        valid_ev_ids = {ev.evidence_id for ev in rr.verified_evidence}
        
        is_valid = True
        
        for claim in answer.claims:
            if claim.claim_type == ClaimType.FACTUAL:
                if not claim.evidence_ids:
                    logger.warning(f"Validation failed: Factual claim has no evidence citations. Claim: {claim.text}")
                    is_valid = False
                    break
                    
                for eid in claim.evidence_ids:
                    if eid not in valid_ev_ids:
                        logger.warning(f"Validation failed: Claim cites unknown evidence ID {eid}. Claim: {claim.text}")
                        is_valid = False
                        break
                        
        if not is_valid:
            answer.validation_status = "FAILED"
        else:
            answer.validation_status = "PASSED"
            
        return answer
