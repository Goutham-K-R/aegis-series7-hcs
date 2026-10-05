import pytest
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from aegis.storage.orm import Base, ExtractionResultORM, DocumentORM, DocumentLocationORM, FactORM, EntityORM, EvidenceORM
from aegis.knowledge.builder import KnowledgeBuilder
from datetime import datetime, timezone

@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    sess = Session()
    yield sess
    sess.close()

def test_no_conflict_resolution(session):
    dt = datetime.now(timezone.utc)
    doc = DocumentORM(id=uuid4(), filename="a.txt", relative_path="a.txt", format="DOCX", hash="1", file_size=1, discovered_timestamp=dt, ingestion_status="REGISTERED")
    loc = DocumentLocationORM(id=uuid4(), document_id=doc.id, location_type="PAGE", location_value="1")
    ext1 = ExtractionResultORM(id=uuid4(), document_id=doc.id, document_location_id=loc.id, method="DETERMINISTIC", raw_text="Maximum pressure for PS-04 is 180 bar", extraction_reliability="HIGH", extraction_status="SUCCESS", created_at=dt)
    ext2 = ExtractionResultORM(id=uuid4(), document_id=doc.id, document_location_id=loc.id, method="DETERMINISTIC", raw_text="Maximum pressure for PS-04A is 200 bar", extraction_reliability="HIGH", extraction_status="SUCCESS", created_at=dt)
    
    session.add_all([doc, loc, ext1, ext2])
    session.commit()
    
    builder = KnowledgeBuilder(session, mode='test')
    builder.build_knowledge()
    
    facts = session.query(FactORM).all()
    assert len(facts) == 2
    
    ps04_fact = next(f for f in facts if f.value == "180")
    ps04a_fact = next(f for f in facts if f.value == "200")
    
    ent_ps04 = session.query(EntityORM).filter_by(id=ps04_fact.subject_id).first()
    ent_ps04a = session.query(EntityORM).filter_by(id=ps04a_fact.subject_id).first()
    
    assert ent_ps04.canonical_name == "PS-04"
    assert ent_ps04a.canonical_name == "PS-04A"
    assert ent_ps04.id != ent_ps04a.id

def test_voltage_distinct_facts(session):
    dt = datetime.now(timezone.utc)
    doc = DocumentORM(id=uuid4(), filename="b.txt", relative_path="b.txt", format="DOCX", hash="2", file_size=1, discovered_timestamp=dt, ingestion_status="REGISTERED")
    loc = DocumentLocationORM(id=uuid4(), document_id=doc.id, location_type="PAGE", location_value="1")
    ext = ExtractionResultORM(id=uuid4(), document_id=doc.id, document_location_id=loc.id, method="DETERMINISTIC", raw_text="System has 480 V transformer. Can run on 400 V supply.", extraction_reliability="HIGH", extraction_status="SUCCESS", created_at=dt)
    
    session.add_all([doc, loc, ext])
    session.commit()
    
    builder = KnowledgeBuilder(session, mode='test')
    builder.build_knowledge()
    
    facts = session.query(FactORM).all()
    assert len(facts) == 2
    assert any(f.value == "480" for f in facts)
    assert any(f.value == "400" for f in facts)

def test_alias_ambiguous_remains_unconfirmed(session):
    dt = datetime.now(timezone.utc)
    doc = DocumentORM(id=uuid4(), filename="c.txt", relative_path="c.txt", format="DOCX", hash="3", file_size=1, discovered_timestamp=dt, ingestion_status="REGISTERED")
    loc = DocumentLocationORM(id=uuid4(), document_id=doc.id, location_type="PAGE", location_value="1")
    ext = ExtractionResultORM(id=uuid4(), document_id=doc.id, document_location_id=loc.id, method="DETERMINISTIC", raw_text="The PRESSURE XDCR is connected", extraction_reliability="HIGH", extraction_status="SUCCESS", created_at=dt)
    
    session.add_all([doc, loc, ext])
    session.commit()
    
    builder = KnowledgeBuilder(session, mode='test')
    builder.build_knowledge()
    
    from aegis.storage.orm import AliasORM
    aliases = session.query(AliasORM).all()
    assert len(aliases) == 1
    assert aliases[0].alias_name == "PRESSURE XDCR"
    assert aliases[0].is_confirmed is False

def test_idempotent_extraction(session):
    dt = datetime.now(timezone.utc)
    doc = DocumentORM(id=uuid4(), filename="a.txt", relative_path="a.txt", format="DOCX", hash="1", file_size=1, discovered_timestamp=dt, ingestion_status="REGISTERED")
    loc = DocumentLocationORM(id=uuid4(), document_id=doc.id, location_type="PAGE", location_value="1")
    ext1 = ExtractionResultORM(id=uuid4(), document_id=doc.id, document_location_id=loc.id, method="DETERMINISTIC", raw_text="Maximum pressure for PS-04 is 180 bar", extraction_reliability="HIGH", extraction_status="SUCCESS", created_at=dt)
    session.add_all([doc, loc, ext1])
    session.commit()
    
    builder = KnowledgeBuilder(session, mode='test')
    builder.build_knowledge()
    facts_count = session.query(FactORM).count()
    assert facts_count == 1
    
    builder.build_knowledge()
    assert session.query(FactORM).count() == facts_count

def test_evidence_presence(session):
    dt = datetime.now(timezone.utc)
    doc = DocumentORM(id=uuid4(), filename="e.txt", relative_path="e.txt", format="DOCX", hash="4", file_size=1, discovered_timestamp=dt, ingestion_status="REGISTERED")
    loc = DocumentLocationORM(id=uuid4(), document_id=doc.id, location_type="PAGE", location_value="1")
    ext = ExtractionResultORM(id=uuid4(), document_id=doc.id, document_location_id=loc.id, method="DETERMINISTIC", raw_text="Maximum pressure for PS-04 is 180 bar", extraction_reliability="HIGH", extraction_status="SUCCESS", created_at=dt)
    session.add_all([doc, loc, ext])
    session.commit()
    
    KnowledgeBuilder(session, mode="test").build_knowledge()
    fact = session.query(FactORM).first()
    assert fact is not None
    ev = session.query(EvidenceORM).filter_by(fact_id=fact.id).first()
    assert ev is not None
    assert ev.extraction_result_id == ext.id
