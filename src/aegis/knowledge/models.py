from pydantic import BaseModel, Field
from typing import List, Optional
from aegis.models.domain import EntityType, ResolutionMethod, RelationType

class EntityCandidate(BaseModel):
    canonical_name: str
    entity_type: EntityType = EntityType.COMPONENT

class FactCandidate(BaseModel):
    subject: str
    subject_type: EntityType = EntityType.COMPONENT
    predicate: str
    value: str
    unit: Optional[str] = None
    negated: bool = False
    validity_context: Optional[str] = None
    fw_version_min: Optional[str] = None
    fw_version_max: Optional[str] = None

class AliasCandidate(BaseModel):
    canonical_name: str
    entity_type: EntityType = EntityType.COMPONENT
    alias_name: str
    is_confirmed: bool = False
    resolution_method: ResolutionMethod = ResolutionMethod.MODEL

class RelationCandidate(BaseModel):
    source_entity: str
    relation_type: RelationType
    target_entity: str
    polarity: str = "POSITIVE"
    confidence: str = "HIGH"
    explicit_support: bool = True

class SemanticExtractionResponse(BaseModel):
    entities: List[EntityCandidate] = Field(default_factory=list)
    aliases: List[AliasCandidate] = Field(default_factory=list)
    facts: List[FactCandidate] = Field(default_factory=list)
    relations: List[RelationCandidate] = Field(default_factory=list)

class ValidityCandidate(BaseModel):
    fw_version_min: Optional[str] = None
    fw_version_max: Optional[str] = None
    date_effective: Optional[str] = None
    date_superseded: Optional[str] = None

class KnowledgeCandidates(BaseModel):
    extraction_result_id: str
    entities: List[EntityCandidate] = Field(default_factory=list)
    facts: List[FactCandidate] = Field(default_factory=list)
    aliases: List[AliasCandidate] = Field(default_factory=list)
    relations: List[RelationCandidate] = Field(default_factory=list)
    validities: List[ValidityCandidate] = Field(default_factory=list)
