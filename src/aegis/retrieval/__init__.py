from .query import QueryAnalyzer
from .retriever import CandidateRetriever
from .verifier import EvidenceVerifier
from .models import QueryAnalysis, RetrievalCandidate, VerifiedEvidence, VerificationDecision, RetrievalResult

def retrieve_and_verify(query: str, session) -> RetrievalResult:
    qa = QueryAnalyzer().analyze(query)
    retriever = CandidateRetriever(session)
    candidates = retriever.retrieve(qa)
    
    verifier = EvidenceVerifier(session)
    verified, decision, reason = verifier.verify(qa, candidates)
    
    return RetrievalResult(
        query=query,
        query_analysis=qa,
        candidates=candidates,
        verified_evidence=verified,
        decision=decision,
        reason=reason
    )
