import uuid
from datetime import date
from sqlalchemy import Column, String, Float, Boolean, Date, Enum, ForeignKey, Integer, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.types import CHAR, TypeDecorator

Base = declarative_base()

class GUID(TypeDecorator):
    """Platform-independent GUID type."""
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return uuid.UUID(value)

class DocumentORM(Base):
    __tablename__ = 'documents'
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    filename = Column(String, nullable=False)
    relative_path = Column(String, nullable=False)
    format = Column(String, nullable=False)
    hash = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    discovered_timestamp = Column(DateTime, nullable=False)
    ingestion_status = Column(String, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    is_latest = Column(Boolean, nullable=False, default=True)

class DocumentLocationORM(Base):
    __tablename__ = 'document_locations'
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    document_id = Column(GUID, ForeignKey('documents.id'), nullable=False)
    location_type = Column(String, nullable=False)
    location_value = Column(String, nullable=False)

class SourceORM(Base):
    __tablename__ = 'sources'
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    document_id = Column(GUID, ForeignKey('documents.id'), nullable=False)
    authority = Column(String, nullable=False)
    revision = Column(String, nullable=True)
    effective_date = Column(String, nullable=True)
    applicability = Column(String, nullable=True)
    relevance_score = Column(Float, nullable=False, default=1.0)

class ExtractionResultORM(Base):
    __tablename__ = 'extraction_results'
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    document_id = Column(GUID, ForeignKey('documents.id'), nullable=False)
    document_location_id = Column(GUID, ForeignKey('document_locations.id'), nullable=False)
    method = Column(String, nullable=False)
    raw_text = Column(String, nullable=False)
    normalized_text = Column(String, nullable=True)
    extraction_reliability = Column(String, nullable=False)
    extraction_status = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)

class EntityORM(Base):
    __tablename__ = 'entities'
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    canonical_name = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    resolved_entity_id = Column(GUID, ForeignKey('entities.id'), nullable=True)

class AliasORM(Base):
    __tablename__ = 'aliases'
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    canonical_entity_id = Column(GUID, ForeignKey('entities.id'), nullable=True)
    alias_name = Column(String, nullable=False)
    is_confirmed = Column(Boolean, nullable=False)
    confidence = Column(Float, nullable=False, default=1.0)
    resolution_method = Column(String, nullable=False)

class ValidityORM(Base):
    __tablename__ = 'validities'
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    fw_version_min = Column(String, nullable=True)
    fw_version_max = Column(String, nullable=True)
    date_effective = Column(Date, nullable=True)
    date_superseded = Column(Date, nullable=True)

class FactORM(Base):
    __tablename__ = 'facts'
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    subject_id = Column(GUID, ForeignKey('entities.id'), nullable=False)
    predicate = Column(String, nullable=False)
    value = Column(String, nullable=False)
    unit = Column(String, nullable=True)
    validity_id = Column(GUID, ForeignKey('validities.id'), nullable=True)
    status = Column(String, nullable=False)

class ConflictORM(Base):
    __tablename__ = 'conflicts'
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    fact_a_id = Column(GUID, ForeignKey('facts.id'), nullable=False)
    fact_b_id = Column(GUID, ForeignKey('facts.id'), nullable=False)
    conflict_type = Column(String, nullable=False)
    resolution_note = Column(String, nullable=False)

class RelationORM(Base):
    __tablename__ = 'relations'
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    source_entity_id = Column(GUID, ForeignKey('entities.id'), nullable=False)
    target_entity_id = Column(GUID, ForeignKey('entities.id'), nullable=False)
    relation_type = Column(String, nullable=False)
    validity_id = Column(GUID, ForeignKey('validities.id'), nullable=True)
    confidence = Column(Float, nullable=False, default=1.0)

class EvidenceORM(Base):
    __tablename__ = 'evidence'
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    fact_id = Column(GUID, ForeignKey('facts.id'), nullable=True)
    entity_id = Column(GUID, ForeignKey('entities.id'), nullable=True)
    alias_id = Column(GUID, ForeignKey('aliases.id'), nullable=True)
    relation_id = Column(GUID, ForeignKey('relations.id'), nullable=True)
    validity_id = Column(GUID, ForeignKey('validities.id'), nullable=True)
    extraction_result_id = Column(GUID, ForeignKey('extraction_results.id'), nullable=False)
    source_id = Column(GUID, ForeignKey('sources.id'), nullable=False)
    confidence = Column(Float, nullable=False, default=1.0)

class ResolutionResultORM(Base):
    __tablename__ = 'resolution_results'
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    query_id = Column(GUID, nullable=False)
    candidate_fact_id = Column(GUID, ForeignKey('facts.id'), nullable=False)
    decision = Column(String, nullable=False)
    reason = Column(String, nullable=False)
    applicability_status = Column(String, nullable=False)
    conflict_status = Column(String, nullable=False)
    confidence = Column(Float, nullable=False, default=1.0)
    # evidence_ids should be stored in a relationship or a JSON array. 
    # For simplicity in SQLite we'll store as JSON string or a separate mapping table, 
    # but here we'll use a string for the JSON array of UUIDs.
    evidence_ids = Column(String, nullable=False) 
