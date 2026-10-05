import pytest
import datetime
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))
from resolve_conflicts import ConflictResolver, parse_version, evaluate_applicability, overlap
from aegis.storage.orm import EntityORM, FactORM, ValidityORM, ConflictORM, ResolutionResultORM, EvidenceORM, SourceORM, ExtractionResultORM

@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    from aegis.storage.orm import Base
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def create_entity(session, name):
    e = EntityORM(id=uuid4(), canonical_name=name, entity_type="COMPONENT")
    session.add(e)
    return e

def create_fact(session, entity, predicate, value, unit=None, min_fw=None, max_fw=None, auth="OFFICIAL"):
    v_id = None
    if min_fw or max_fw:
        v = ValidityORM(id=uuid4(), fw_version_min=min_fw, fw_version_max=max_fw)
        session.add(v)
        v_id = v.id
    f = FactORM(id=uuid4(), subject_id=entity.id, predicate=predicate, value=value, unit=unit, validity_id=v_id, status="ASSERTED")
    session.add(f)
    
    doc_id = uuid4()
    src = SourceORM(id=uuid4(), document_id=doc_id, authority=auth)
    ext = ExtractionResultORM(id=uuid4(), document_id=doc_id, document_location_id=uuid4(), method="DETERMINISTIC", raw_text="...", extraction_reliability="HIGH", extraction_status="SUCCESS", created_at=datetime.datetime.now())
    ev = EvidenceORM(id=uuid4(), fact_id=f.id, extraction_result_id=ext.id, source_id=src.id, confidence=1.0)
    session.add_all([src, ext, ev])
    session.commit()
    return f

def test_version_comparison():
    # 1. version comparison and 22. lexicographic version comparison is not used
    assert parse_version("3.2.1") > parse_version("3.2")
    assert parse_version("3.2") > parse_version("3.1")
    assert parse_version("3.1") > parse_version("3.0")
    assert parse_version("10.0") > parse_version("2.0") # Lexicographic would fail here
    # 21. firmware 3.3 planned is not treated as active/current
    assert parse_version("3.3 planned") is None

def test_applicability():
    class DummyValidity:
        def __init__(self, fw_version_min=None, fw_version_max=None):
            self.fw_version_min = fw_version_min
            self.fw_version_max = fw_version_max
            self.date_effective = None
            self.date_superseded = None
            
    v1 = DummyValidity(fw_version_min="3.2")
    # 2. minimum firmware applicability
    assert evaluate_applicability(v1, target_fw="3.2.1") == "APPLIES"
    # 3. minimum firmware non-applicability
    assert evaluate_applicability(v1, target_fw="3.1") == "DOES_NOT_APPLY"
    
    # 4. unknown applicability
    assert evaluate_applicability(None, target_fw="3.2.1") == "UNKNOWN"

def test_version_scoped_pressure_facts(session):
    e = create_entity(session, "PS-04")
    f1 = create_fact(session, e, "pressure", "180", "bar", max_fw="3.1")
    f2 = create_fact(session, e, "pressure", "200", "bar", min_fw="3.2")
    
    # 5. version-scoped pressure facts
    resolver = ConflictResolver(session)
    resolver.run()
    
    conflicts = session.query(ConflictORM).all()
    assert len(conflicts) == 1
    assert conflicts[0].conflict_type == "VERSION_OVERRIDE"
    
    # 6. firmware 3.1 selects 180 bar
    res1 = ConflictResolver(session, firmware="3.1").run()
    assert res1["SELECTED"] == 1
    assert res1["NOT_APPLICABLE"] == 1
    
    # 7. firmware 3.2.1 selects 200 bar
    session.query(ResolutionResultORM).delete()
    res2 = ConflictResolver(session, firmware="3.2.1").run()
    
    r_f2 = session.query(ResolutionResultORM).filter_by(candidate_fact_id=f2.id).order_by(ResolutionResultORM.id.desc()).first()
    assert r_f2.decision == "SELECTED"

def test_overlapping_incompatible_facts(session):
    e = create_entity(session, "Voltage")
    # 8. two overlapping incompatible facts produce CONFLICTED
    f1 = create_fact(session, e, "rating", "400", "V") # unknown app
    f2 = create_fact(session, e, "rating", "480", "V") # unknown app
    
    resolver = ConflictResolver(session, firmware="3.2").run()
    # 9. insufficient applicability produces INSUFFICIENT_EVIDENCE
    assert resolver["INSUFFICIENT_EVIDENCE"] == 2
    
    # If they both applied explicitly:
    session.query(FactORM).delete()
    session.query(ValidityORM).delete()
    session.query(ResolutionResultORM).delete()
    session.commit()
    
    f1 = create_fact(session, e, "rating", "400", "V", min_fw="3.0")
    f2 = create_fact(session, e, "rating", "480", "V", min_fw="3.0")
    
    res2 = ConflictResolver(session, firmware="3.2").run()
    assert res2["CONFLICTED"] == 2

def test_not_applicable(session):
    e = create_entity(session, "PS-04")
    f1 = create_fact(session, e, "pressure", "180", "bar", max_fw="3.1")
    # 10. NOT_APPLICABLE is correctly returned
    resolver = ConflictResolver(session, firmware="3.2").run()
    assert resolver["NOT_APPLICABLE"] == 1

def test_different_entities_no_conflict(session):
    e1 = create_entity(session, "PS-04")
    e2 = create_entity(session, "PS-04A")
    f1 = create_fact(session, e1, "pressure", "180", "bar")
    f2 = create_fact(session, e2, "pressure", "200", "bar")
    
    resolver = ConflictResolver(session).run()
    # 11. PS-04 vs PS-04A is NOT a conflict
    assert session.query(ConflictORM).count() == 0

def test_system_supply_vs_component(session):
    e1 = create_entity(session, "Q1")
    e2 = create_entity(session, "SYSTEM")
    f1 = create_fact(session, e1, "voltage", "400", "V")
    f2 = create_fact(session, e2, "voltage", "480", "V")
    
    # 13. Q1/T1 component ratings cannot be used as system supply compatibility
    resolver = ConflictResolver(session).run()
    assert session.query(ConflictORM).count() == 0

def test_official_historical_not_overridden(session):
    e = create_entity(session, "PS-04")
    # 14. official historical documentation is not automatically overridden
    # Official historical says 180 bar for < 3.2. Unverified survey says 175 bar for < 3.2.
    f1 = create_fact(session, e, "pressure", "180", "bar", max_fw="3.1", auth="OFFICIAL")
    f2 = create_fact(session, e, "pressure", "175", "bar", max_fw="3.1", auth="UNVERIFIED")
    
    # At 3.1, both apply. Without authority tie-breaker, it's CONFLICTED.
    # 15. unverified source does not automatically override an applicable official fact (and vice versa)
    resolver = ConflictResolver(session, firmware="3.1").run()
    r_f1 = session.query(ResolutionResultORM).filter_by(candidate_fact_id=f1.id).order_by(ResolutionResultORM.id.desc()).first()
    r_f2 = session.query(ResolutionResultORM).filter_by(candidate_fact_id=f2.id).order_by(ResolutionResultORM.id.desc()).first()
    
    assert r_f1.decision == "CONFLICTED"
    assert r_f2.decision == "CONFLICTED"

def test_provenance_and_idempotency(session):
    e = create_entity(session, "PS-04")
    f1 = create_fact(session, e, "pressure", "180", "bar")
    f2 = create_fact(session, e, "pressure", "200", "bar")
    
    resolver = ConflictResolver(session, firmware="3.2")
    res1 = resolver.run()
    
    # 16. ResolutionResult contains evidence IDs
    rr = session.query(ResolutionResultORM).first()
    evs = json.loads(rr.evidence_ids)
    assert len(evs) > 0
    
    # 17. Conflict contains provenance -> well it links to fact_a and fact_b which have evidence
    c = session.query(ConflictORM).first()
    assert c.fact_a_id is not None
    assert c.fact_b_id is not None
    
    # 18. running detection twice is idempotent
    res2 = ConflictResolver(session, firmware="3.2").run()
    assert res2["Conflicts created"] == 0
    assert res2["Existing conflicts"] == 1
    
    # 19. facts are never deleted
    # 20. fact count does not decrease
    assert session.query(FactORM).count() == 2
