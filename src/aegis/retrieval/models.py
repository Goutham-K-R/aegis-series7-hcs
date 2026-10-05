from enum import Enum
from pydantic import BaseModel
from typing import List, Optional, Any, Dict

class VerificationDecision(Enum):
    VERIFIED = "VERIFIED"
    NOT_VERIFIED = "NOT_VERIFIED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    CONFLICTED = "CONFLICTED"
    NOT_APPLICABLE = "NOT_APPLICABLE"

class RetrievalMethod(Enum):
    EXACT = "EXACT"
    STRUCTURED = "STRUCTURED"
    FTS = "FTS"
    SEMANTIC = "SEMANTIC"

class QueryAnalysis(BaseModel):
    original_query: str
    normalized_query: str
    entities: List[str] = []
    aliases: List[str] = []
    requested_predicate: Optional[str] = None
    requested_value: Optional[str] = None
    requested_unit: Optional[str] = None
    firmware_context: Optional[str] = None
    date_context: Optional[str] = None
    document_context: Optional[str] = None
    relation_type: Optional[str] = None
    ambiguity_indicators: List[str] = []

class RetrievalCandidate(BaseModel):
    fact_id: Optional[str] = None
    relation_id: Optional[str] = None
    entity_id: Optional[str] = None
    evidence_id: Optional[str] = None
    extraction_result_id: Optional[str] = None
    source_id: Optional[str] = None
    retrieval_method: RetrievalMethod
    retrieval_score: float = 1.0
    matched_terms: List[str] = []

class VerifiedEvidence(BaseModel):
    fact_id: Optional[str] = None
    relation_id: Optional[str] = None
    evidence_id: str
    extraction_result_id: str
    source_id: str
    document_id: str
    document_filename: Optional[str] = None
    document_location: Optional[str] = None
    extraction_method: str
    extraction_reliability: str
    source_authority: str
    validity_info: Optional[Dict[str, Any]] = None
    
    # Payload for Answer Generation
    subject: Optional[str] = None
    predicate: Optional[str] = None
    value: Optional[str] = None
    unit: Optional[str] = None

class RetrievalResult(BaseModel):
    query: str
    query_analysis: QueryAnalysis
    candidates: List[RetrievalCandidate] = []
    verified_evidence: List[VerifiedEvidence] = []
    decision: VerificationDecision = VerificationDecision.NOT_VERIFIED
    reason: str = ""
