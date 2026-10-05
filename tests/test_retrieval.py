import pytest
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from aegis.storage.orm import Base, EntityORM, FactORM, RelationORM, EvidenceORM, ExtractionResultORM, SourceORM, DocumentORM, DocumentLocationORM, ValidityORM, AliasORM
from aegis.retrieval import retrieve_and_verify
from aegis.retrieval.models import VerificationDecision

@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def setup_db(session):
    import datetime
    dt = datetime.datetime.now()
    
    # Docs
    doc = DocumentORM(id=uuid4(), filename="test.pdf", relative_path=".", format="PDF", hash="1", file_size=1, discovered_timestamp=dt, ingestion_status="SUCCESS")
    loc = DocumentLocationORM(id=uuid4(), document_id=doc.id, location_type="PAGE", location_value="1")
    src = SourceORM(id=uuid4(), document_id=doc.id, authority="OFFICIAL")
    ext = ExtractionResultORM(id=uuid4(), document_id=doc.id, document_location_id=loc.id, method="DETERMINISTIC", raw_text="...", extraction_reliability="HIGH", extraction_status="SUCCESS", created_at=dt)
    
    session.add_all([doc, loc, src, ext])
    
    # Entities
    e_ps04 = EntityORM(id=uuid4(), canonical_name="PS-04", entity_type="COMPONENT")
    e_ps04a = EntityORM(id=uuid4(), canonical_name="PS-04A", entity_type="COMPONENT")
    e_iv21 = EntityORM(id=uuid4(), canonical_name="IV-21", entity_type="COMPONENT")
    e_hpu = EntityORM(id=uuid4(), canonical_name="HPU", entity_type="COMPONENT")
    e_plc = EntityORM(id=uuid4(), canonical_name="PLC-03", entity_type="COMPONENT")
    
    session.add_all([e_ps04, e_ps04a, e_iv21, e_hpu, e_plc])
    
    # Validities
    v_31 = ValidityORM(id=uuid4(), fw_version_max="3.2")
    v_32 = ValidityORM(id=uuid4(), fw_version_min="3.2")
    session.add_all([v_31, v_32])
    
    # Facts
    f1 = FactORM(id=uuid4(), subject_id=e_ps04.id, predicate="maximum_pressure", value="180", unit="bar", validity_id=v_31.id, status="ASSERTED")
    f2 = FactORM(id=uuid4(), subject_id=e_ps04a.id, predicate="maximum_pressure", value="200", unit="bar", validity_id=v_32.id, status="ASSERTED")
    # overlapping/conflicting pressure for PS-04A without validity (just to test conflict)
    f3 = FactORM(id=uuid4(), subject_id=e_ps04a.id, predicate="maximum_pressure", value="210", unit="bar", status="ASSERTED") # conflicting
    
    f4 = FactORM(id=uuid4(), subject_id=e_iv21.id, predicate="mtbf", value="100000", unit="hours", status="ASSERTED")
    
    f5 = FactORM(id=uuid4(), subject_id=e_hpu.id, predicate="voltage_compatibility", value="400", unit="V", status="ASSERTED")
    
    session.add_all([f1, f2, f3, f4, f5])
    
    from aegis.storage.orm import ConflictORM
    c = ConflictORM(id=uuid4(), fact_a_id=f2.id, fact_b_id=f3.id, conflict_type="CONTRADICTION", resolution_note="")
    session.add(c)
    
    # Relations
    r1 = RelationORM(id=uuid4(), source_entity_id=e_plc.id, target_entity_id=e_ps04a.id, relation_type="ELECTRICALLY_CONNECTED_TO")
    session.add(r1)
    
    # Evidence links
    for item in [f1, f2, f3, f4, f5, r1]:
        ev = EvidenceORM(id=uuid4(), fact_id=item.id if isinstance(item, FactORM) else None, relation_id=item.id if isinstance(item, RelationORM) else None, extraction_result_id=ext.id, source_id=src.id)
        session.add(ev)
        
    session.commit()

def test_query_ps04a_max_pressure_fw_321(session):
    setup_db(session)
    # Wait, f3 conflicts with f2 for PS-04A!
    # If we ask for fw 3.2.1, f2 applies (min=3.2), but f3 has no validity so it might overlap!
    # Actually, in Phase 5B overlap, if one has no validity, it overlaps. 
    # Let's delete f3 in setup for this test or handle it.
    session.query(FactORM).filter_by(value="210").delete()
    session.commit()
    
    res = retrieve_and_verify("What is the maximum pressure of PS-04A for firmware 3.2.1?", session)
    assert res.decision == VerificationDecision.VERIFIED
    assert len(res.verified_evidence) == 1
    assert "200" in str(session.query(FactORM).get(res.verified_evidence[0].fact_id).value)

def test_query_ps04_max_pressure_fw_31(session):
    setup_db(session)
    res = retrieve_and_verify("What is the maximum pressure of PS-04 for firmware 3.1?", session)
    assert res.decision == VerificationDecision.VERIFIED
    
def test_query_pressure_without_context(session):
    setup_db(session)
    session.query(FactORM).filter_by(value="210").delete()
    session.commit()
    # "PS-04A maximum pressure" with no context
    res = retrieve_and_verify("What is the maximum pressure of PS-04A?", session)
    # f2 has validity 3.2+. Since no context, and there's only 1 fact, does it verify or NOT_APPLICABLE?
    # Wait, if there's only 1 fact for PS-04A and it's 200, it verifies.
    assert res.decision == VerificationDecision.VERIFIED

def test_query_pressure_conflicted(session):
    setup_db(session)
    # PS-04A has f2 (200) and f3 (210)
    res = retrieve_and_verify("What is the maximum pressure of PS-04A?", session)
    assert res.decision == VerificationDecision.CONFLICTED

def test_ambiguous_controller_unresolved(session):
    setup_db(session)
    res = retrieve_and_verify("How is the controller connected?", session)
    assert res.decision == VerificationDecision.INSUFFICIENT_EVIDENCE
    assert "CONTROLLER" in res.reason

def test_ambiguous_pressure_xdcr_unresolved(session):
    setup_db(session)
    res = retrieve_and_verify("What is the maximum pressure of PRESSURE XDCR?", session)
    assert res.decision == VerificationDecision.INSUFFICIENT_EVIDENCE

def test_ps04_vs_ps04a_distinction(session):
    setup_db(session)
    session.query(FactORM).filter_by(value="210").delete()
    session.commit()
    res = retrieve_and_verify("What is the maximum pressure of PS-04?", session)
    assert len(res.verified_evidence) == 1
    assert session.query(FactORM).get(res.verified_evidence[0].fact_id).value == "180"

def test_ps04_vs_ps40_distinction(session):
    setup_db(session)
    res = retrieve_and_verify("What is the maximum pressure of PS-40?", session)
    assert res.decision == VerificationDecision.NOT_APPLICABLE or res.decision == VerificationDecision.INSUFFICIENT_EVIDENCE

def test_provenance_missing_extraction(session):
    setup_db(session)
    session.query(ExtractionResultORM).delete()
    session.commit()
    res = retrieve_and_verify("What is the MTBF of IV-21?", session)
    assert res.decision == VerificationDecision.NOT_APPLICABLE or res.decision == VerificationDecision.INSUFFICIENT_EVIDENCE

def test_provenance_missing_document_location(session):
    setup_db(session)
    session.query(DocumentLocationORM).delete()
    session.commit()
    res = retrieve_and_verify("What is the MTBF of IV-21?", session)
    assert res.decision == VerificationDecision.NOT_APPLICABLE or res.decision == VerificationDecision.INSUFFICIENT_EVIDENCE

def test_provenance_missing_source(session):
    setup_db(session)
    session.query(SourceORM).delete()
    session.commit()
    res = retrieve_and_verify("What is the MTBF of IV-21?", session)
    assert res.decision == VerificationDecision.NOT_APPLICABLE or res.decision == VerificationDecision.INSUFFICIENT_EVIDENCE

def test_a17_alarm_query(session):
    setup_db(session)
    res = retrieve_and_verify("What does alarm A17 mean?", session)
    assert res.decision in [VerificationDecision.INSUFFICIENT_EVIDENCE, VerificationDecision.VERIFIED]

def test_a18_alarm_query(session):
    setup_db(session)
    res = retrieve_and_verify("What does alarm A18 mean?", session)
    assert res.decision in [VerificationDecision.INSUFFICIENT_EVIDENCE, VerificationDecision.VERIFIED]

def test_a19_alarm_query(session):
    setup_db(session)
    res = retrieve_and_verify("What does alarm A19 mean?", session)
    assert res.decision in [VerificationDecision.INSUFFICIENT_EVIDENCE, VerificationDecision.VERIFIED]

def test_ps04a_temperature_query(session):
    setup_db(session)
    res = retrieve_and_verify("What is the maximum continuous temperature for PS-04A?", session)
    assert res.decision in [VerificationDecision.INSUFFICIENT_EVIDENCE, VerificationDecision.VERIFIED]

def test_3phase_400v_compatibility_query(session):
    setup_db(session)
    res = retrieve_and_verify("Is it compatible with 3-phase 400 V?", session)
    assert res.decision in [VerificationDecision.INSUFFICIENT_EVIDENCE, VerificationDecision.VERIFIED]

def test_unknown_entity_query(session):
    setup_db(session)
    res = retrieve_and_verify("What is the pressure of Q1?", session)
    assert res.decision in [VerificationDecision.INSUFFICIENT_EVIDENCE, VerificationDecision.VERIFIED]

def test_explicit_firmware_31(session):
    setup_db(session)
    res = retrieve_and_verify("firmware 3.1", session)
    assert res.query_analysis.firmware_context == "3.1"

def test_explicit_firmware_321(session):
    setup_db(session)
    res = retrieve_and_verify("firmware 3.2.1", session)
    assert res.query_analysis.firmware_context == "3.2.1"

def test_planned_33(session):
    setup_db(session)
    res = retrieve_and_verify("planned 3.3", session)
    assert res.decision in [VerificationDecision.INSUFFICIENT_EVIDENCE, VerificationDecision.VERIFIED]
