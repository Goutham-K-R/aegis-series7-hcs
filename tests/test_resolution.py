import pytest
from uuid import uuid4
from aegis.storage.orm import EntityORM, AliasORM, EvidenceORM, ExtractionResultORM, SourceORM, DocumentORM, DocumentLocationORM, FactORM
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

# Add scripts directory to path to import resolve_entities
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))
from resolve_entities import EntityResolver, normalize_name

@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    from aegis.storage.orm import Base
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def create_candidate_entity(session, name, etype="COMPONENT"):
    ent = EntityORM(id=uuid4(), canonical_name=name, entity_type=etype)
    session.add(ent)
    session.commit()
    return ent

def test_normalization_rules():
    assert normalize_name("P04") == "PS-04"
    assert normalize_name("PS04") == "PS-04"
    assert normalize_name("P04A") == "PS-04A"
    assert normalize_name("PS04A") == "PS-04A"
    assert normalize_name("PS-04") == "PS-04"
    assert normalize_name("PS-40") == "PS-40"
    assert normalize_name("IV21") == "IV-21"
    assert normalize_name("Hydraulic Power Unit") == "HPU"
    assert normalize_name("Controller") == "CONTROLLER"
    assert normalize_name("PRESSURE XDCR") == "PRESSURE XDCR"
    assert normalize_name("PLC-03") == "PLC-03"

def test_resolve_p04_to_ps04(session):
    e1 = create_candidate_entity(session, "P04")
    
    resolver = EntityResolver(session)
    stats = resolver.resolve()
    
    assert stats["Resolved"] == 1
    
    e1_updated = session.query(EntityORM).filter_by(id=e1.id).first()
    assert e1_updated.resolved_entity_id is not None
    
    canonical = session.query(EntityORM).filter_by(id=e1_updated.resolved_entity_id).first()
    assert canonical.canonical_name == "PS-04"
    
    alias = session.query(AliasORM).filter_by(canonical_entity_id=canonical.id).first()
    assert alias is not None
    assert alias.alias_name == "P04"
    assert alias.resolution_method == "EXACT"

def test_ps04_and_ps04a_remain_distinct(session):
    e1 = create_candidate_entity(session, "PS-04")
    e2 = create_candidate_entity(session, "PS-04A")
    e3 = create_candidate_entity(session, "PS-40")
    
    resolver = EntityResolver(session)
    stats = resolver.resolve()
    
    assert stats["Resolved"] == 0 # They are already canonical
    assert stats["Unresolved"] == 3
    
    canonicals = session.query(EntityORM).filter(EntityORM.resolved_entity_id == None).all()
    names = {c.canonical_name for c in canonicals}
    assert "PS-04" in names
    assert "PS-04A" in names
    assert "PS-40" in names
    assert len(canonicals) == 3

def test_ambiguous_names_unresolved(session):
    e1 = create_candidate_entity(session, "Controller")
    e2 = create_candidate_entity(session, "PRESSURE XDCR")
    
    resolver = EntityResolver(session)
    stats = resolver.resolve()
    
    assert stats["Resolved"] == 0
    assert stats["Ambiguous aliases left unresolved"] == 2
    
    # Must have no resolved entity id
    assert e1.resolved_entity_id is None
    assert e2.resolved_entity_id is None

def test_provenance_preserved(session):
    e1 = create_candidate_entity(session, "PS04A")
    
    import datetime
    doc = DocumentORM(id=uuid4(), filename="test.pdf", relative_path=".", format="PDF", hash="123", file_size=100, discovered_timestamp=datetime.datetime.now(), ingestion_status="SUCCESS")
    loc = DocumentLocationORM(id=uuid4(), document_id=doc.id, location_type="PAGE", location_value="1")
    src = SourceORM(id=uuid4(), document_id=doc.id, authority="OFFICIAL")
    ext = ExtractionResultORM(id=uuid4(), document_id=doc.id, document_location_id=loc.id, method="DETERMINISTIC", raw_text="...", extraction_reliability="HIGH", extraction_status="SUCCESS", created_at=datetime.datetime.now())
    
    ev = EvidenceORM(id=uuid4(), entity_id=e1.id, extraction_result_id=ext.id, source_id=src.id, confidence=1.0)
    
    session.add_all([doc, loc, src, ext, ev])
    session.commit()
    
    resolver = EntityResolver(session)
    resolver.resolve()
    
    canonical = session.query(EntityORM).filter_by(canonical_name="PS-04A").first()
    alias = session.query(AliasORM).filter_by(alias_name="PS04A").first()
    
    assert canonical is not None
    assert alias is not None
    
    # Original evidence remains
    orig_ev = session.query(EvidenceORM).filter_by(entity_id=e1.id).first()
    assert orig_ev is not None
    
    # New evidence created for alias
    alias_ev = session.query(EvidenceORM).filter_by(alias_id=alias.id).first()
    assert alias_ev is not None
    assert alias_ev.extraction_result_id == ext.id
    assert alias_ev.source_id == src.id

def test_idempotency(session):
    e1 = create_candidate_entity(session, "IV21")
    
    resolver = EntityResolver(session)
    stats1 = resolver.resolve()
    assert stats1["Resolved"] == 1
    
    # Second run
    resolver2 = EntityResolver(session)
    stats2 = resolver2.resolve()
    
    assert stats2["Resolved"] == 0
    assert stats2["Canonical entities created"] == 0
    assert stats2["Aliases resolved"] == 0

def test_does_not_perform_conflict_resolution(session):
    e1 = create_candidate_entity(session, "PS-04")
    e2 = create_candidate_entity(session, "PS-04A")
    
    f1 = FactORM(id=uuid4(), subject_id=e1.id, predicate="pressure", value="180", unit="bar", status="ASSERTED")
    f2 = FactORM(id=uuid4(), subject_id=e2.id, predicate="pressure", value="200", unit="bar", status="ASSERTED")
    session.add_all([f1, f2])
    session.commit()
    
    resolver = EntityResolver(session)
    resolver.resolve()
    
    # Facts should be completely unchanged
    facts = session.query(FactORM).all()
    assert len(facts) == 2
    assert facts[0].value == "180"
    assert facts[1].value == "200"
    assert facts[0].subject_id != facts[1].subject_id
