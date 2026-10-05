from enum import Enum
from pydantic import BaseModel
from typing import List, Optional, Any, Dict

class ClaimType(Enum):
    FACTUAL = "FACTUAL"
    QUALIFIED = "QUALIFIED"
    ABSTENTION = "ABSTENTION"
    CONFLICT = "CONFLICT"
    SOURCE_DESCRIPTION = "SOURCE_DESCRIPTION"

class Claim(BaseModel):
    claim_id: str
    text: str
    evidence_ids: List[str] = []
    confidence: float
    claim_type: ClaimType

class GeneratedAnswer(BaseModel):
    text: str
    claims: List[Claim] = []
    is_fallback: bool = False
    validation_status: str = "PENDING"
