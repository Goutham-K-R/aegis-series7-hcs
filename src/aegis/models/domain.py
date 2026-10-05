from enum import Enum
from typing import Optional, List
from uuid import UUID, uuid4
from datetime import date, datetime, timezone
from pydantic import BaseModel, Field

class Format(str, Enum):
    PDF = "PDF"
    PNG = "PNG"
    JSON = "JSON"
    XLSX = "XLSX"
    HTML = "HTML"
    DOCX = "DOCX"
    PPTX = "PPTX"
    UNKNOWN = "UNKNOWN"

class IngestionStatus(str, Enum):
    REGISTERED = "REGISTERED"
    ERROR = "ERROR"

class Document(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    filename: str
    relative_path: str
    format: Format
    hash: str
    file_size: int
    discovered_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ingestion_status: IngestionStatus = IngestionStatus.REGISTERED
    version: int = 1
    is_latest: bool = True

class LocationType(str, Enum):
    PAGE = "PAGE"
    SHEET = "SHEET"
    SLIDE = "SLIDE"
    SECTION = "SECTION"
    CELL = "CELL"
    PIXEL_BOUNDS = "PIXEL_BOUNDS"

class DocumentLocation(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    document_id: UUID
    location_type: LocationType
    location_value: str

class Authority(str, Enum):
    OFFICIAL = "OFFICIAL"
    INFORMAL = "INFORMAL"
    UNVERIFIED = "UNVERIFIED"

class Source(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    document_id: UUID
    authority: Authority
    revision: Optional[str] = None
    effective_date: Optional[str] = None
    applicability: Optional[str] = None
    relevance_score: float = Field(default=1.0, ge=0.0, le=1.0)

class ExtractionMethod(str, Enum):
    DETERMINISTIC = "DETERMINISTIC"
    OCR = "OCR"
    VISION_MODEL = "VISION_MODEL"
    LLM_TEXT = "LLM_TEXT"
    HYBRID = "HYBRID"

class ExtractionReliability(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class ExtractionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    REQUIRES_OCR = "REQUIRES_OCR"
    UNSUPPORTED = "UNSUPPORTED"
    FAILED = "FAILED"

class ExtractionResult(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    document_id: UUID
    document_location_id: UUID
    method: ExtractionMethod
    raw_text: str
    normalized_text: Optional[str] = None
    extraction_reliability: ExtractionReliability
    extraction_status: ExtractionStatus
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class EntityType(str, Enum):
    COMPONENT = "COMPONENT"
    SYSTEM = "SYSTEM"
    ALARM = "ALARM"
    DOCUMENT = "DOCUMENT"
    MEASUREMENT = "MEASUREMENT"

class Entity(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    canonical_name: str
    entity_type: EntityType

class ResolutionMethod(str, Enum):
    EXACT = "EXACT"
    REGISTER = "REGISTER"
    DOCUMENT = "DOCUMENT"
    CONTEXT = "CONTEXT"
    MODEL = "MODEL"

class Alias(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    canonical_entity_id: UUID
    alias_name: str
    is_confirmed: bool
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    resolution_method: ResolutionMethod

class Validity(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    fw_version_min: Optional[str] = None
    fw_version_max: Optional[str] = None
    date_effective: Optional[date] = None
    date_superseded: Optional[date] = None

class FactStatus(str, Enum):
    ASSERTED = "ASSERTED"
    CONTESTED = "CONTESTED"
    WITHDRAWN = "WITHDRAWN"

class Fact(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    subject_id: UUID
    predicate: str
    value: str
    unit: Optional[str] = None
    validity_id: Optional[UUID] = None
    status: FactStatus

class ConflictType(str, Enum):
    VERSION_OVERRIDE = "VERSION_OVERRIDE"
    CONTRADICTION = "CONTRADICTION"
    TERMINOLOGY_MISMATCH = "TERMINOLOGY_MISMATCH"

class Conflict(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    fact_a_id: UUID
    fact_b_id: UUID
    conflict_type: ConflictType
    resolution_note: str

class RelationType(str, Enum):
    ELECTRICALLY_CONNECTED_TO = "ELECTRICALLY_CONNECTED_TO"
    HYDRAULICALLY_CONNECTED_TO = "HYDRAULICALLY_CONNECTED_TO"
    PART_OF = "PART_OF"

class Relation(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    source_entity_id: UUID
    target_entity_id: UUID
    relation_type: RelationType
    validity_id: Optional[UUID] = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

class Evidence(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    fact_id: Optional[UUID] = None
    entity_id: Optional[UUID] = None
    alias_id: Optional[UUID] = None
    relation_id: Optional[UUID] = None
    extraction_result_id: UUID
    source_id: UUID
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

class ResolutionDecision(str, Enum):
    SELECTED = "SELECTED"
    CONFLICTED = "CONFLICTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    NOT_APPLICABLE = "NOT_APPLICABLE"

class ResolutionResult(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    query_id: UUID
    candidate_fact_id: UUID
    decision: ResolutionDecision
    reason: str
    applicability_status: str
    conflict_status: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    evidence_ids: List[UUID]
