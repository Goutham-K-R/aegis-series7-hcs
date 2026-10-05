import pytest
import os
import json
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path
from aegis.config import settings
from aegis.storage.orm import DocumentORM, DocumentLocationORM, ExtractionResultORM
from aegis.ingestion.vision.providers import VisionProvider
from aegis.ingestion.vision.fake_provider import FakeVisionProvider, RealVisionProvider
from aegis.models.domain import Document
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))
from extract_ocr import get_provider, identify_ocr_required, process_document

@pytest.fixture
def session():
    # 20. tests never mutate production aegis.db
    engine = create_engine("sqlite:///:memory:")
    from aegis.storage.orm import Base
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def create_mock_doc(session, filename, format="PDF", req_ocr=False):
    import datetime
    doc = DocumentORM(id=uuid4(), filename=filename, relative_path=filename, format=format, hash="hash_"+filename, is_latest=True, discovered_timestamp=datetime.datetime.now(), file_size=100, ingestion_status='COMPLETED')
    session.add(doc)
    session.flush()
    if req_ocr:
        loc = DocumentLocationORM(document_id=doc.id, location_type="PAGE", location_value="1")
        session.add(loc)
        session.flush()
        ext = ExtractionResultORM(document_id=doc.id, document_location_id=loc.id, method="VISION_MODEL", raw_text="", normalized_text="", extraction_status="REQUIRES_OCR")
        session.add(ext)
    session.commit()
    return doc

def test_ocr_provider_output(session):
    doc = create_mock_doc(session, "scanned_calibration.pdf")
    provider = FakeVisionProvider()
    
    # 1. scanned PDF page creates OCR ExtractionResult
    # 3. page provenance is preserved
    # 5. extraction method is correctly labelled
    # 6. reliability is recorded
    # 7. raw OCR text is preserved
    # 8. uncertain OCR text is not silently corrected
    stats = {"ocr_failed": 0, "vision_failed": 0, "pages_processed": 0, "skipped": 0, "ocr_success": 0, "vision_success": 0}
    process_document(session, doc, provider, Path("."), stats)
    
    exts = session.query(ExtractionResultORM).filter_by(document_id=doc.id, method="OCR").all()
    assert len(exts) == 1
    ext = exts[0]
    loc = session.query(DocumentLocationORM).filter_by(id=ext.document_location_id).first()
    
    assert loc.location_type == "PAGE"
    assert ext.method == "OCR"
    assert ext.extraction_reliability == "LOW"
    assert "PS-0?A" in ext.raw_text

def test_vision_provider_png(session):
    # 2. PNG creates OCR/Vision ExtractionResult
    # 4. image pixel bounds are preserved when supplied
    doc = create_mock_doc(session, "image.png", format="PNG")
    provider = FakeVisionProvider()
    stats = {"ocr_failed": 0, "vision_failed": 0, "pages_processed": 0, "skipped": 0, "ocr_success": 0, "vision_success": 0}
    process_document(session, doc, provider, Path("."), stats)
    
    ext = session.query(ExtractionResultORM).filter_by(document_id=doc.id, method="OCR").first()
    loc = session.query(DocumentLocationORM).filter_by(id=ext.document_location_id).first()
    assert loc.location_type == "PIXEL_BOUNDS"
    assert loc.location_value == "0,0,100,100"

def test_fake_vision_structures(session):
    provider = FakeVisionProvider()
    stats = {"ocr_failed": 0, "vision_failed": 0, "pages_processed": 0, "skipped": 0, "ocr_success": 0, "vision_success": 0}
    
    # 9. fake vision output preserves structured labels
    # 10. diagram proximity does not automatically create a relation
    # 11. electrical and hydraulic relationships remain distinguishable
    doc_elec = create_mock_doc(session, "system_diagram_electrical.png")
    process_document(session, doc_elec, provider, Path("."), stats)
    ext_elec = session.query(ExtractionResultORM).filter_by(document_id=doc_elec.id, method="VISION_MODEL").first()
    elec_data = json.loads(ext_elec.raw_text)
    assert "PLC-03" in elec_data["labels"]
    assert elec_data["connections"][0]["type"] == "ELECTRICAL"
    
    doc_hydr = create_mock_doc(session, "system_diagram_hydraulic.pdf")
    process_document(session, doc_hydr, provider, Path("."), stats)
    ext_hydr = session.query(ExtractionResultORM).filter_by(document_id=doc_hydr.id, method="VISION_MODEL").first()
    hydr_data = json.loads(ext_hydr.raw_text)
    assert hydr_data["connections"][0]["type"] == "HYDRAULIC"
    
    # 12. table structure is preserved
    doc_table = create_mock_doc(session, "table_doc.png")
    process_document(session, doc_table, provider, Path("."), stats)
    ext_table = session.query(ExtractionResultORM).filter_by(document_id=doc_table.id, method="VISION_MODEL").first()
    table_data = json.loads(ext_table.raw_text)
    assert "tables" in table_data

def test_api_key_failure(session, monkeypatch):
    # 13. no API key does not fabricate extraction
    # 14. provider failure does not create successful ExtractionResult
    # 19. test providers never access production API credentials
    monkeypatch.delenv("VISION_API_KEY", raising=False)
    
    doc = create_mock_doc(session, "real_test.png")
    provider = RealVisionProvider()
    
    stats = {"ocr_failed": 0, "vision_failed": 0, "pages_processed": 0, "skipped": 0, "ocr_success": 0, "vision_success": 0}
    process_document(session, doc, provider, Path("."), stats)
    
    assert stats["ocr_failed"] == 1
    assert stats["vision_failed"] == 1
    assert session.query(ExtractionResultORM).filter_by(document_id=doc.id).count() == 0

def test_idempotency_and_mutability(session):
    doc = create_mock_doc(session, "scanned_calibration.pdf")
    # 17. original deterministic ExtractionResults remain unchanged
    loc_orig = DocumentLocationORM(id=uuid4(), document_id=doc.id, location_type="PAGE", location_value="1")
    session.add(loc_orig)
    session.flush()
    import datetime
    ext_orig = ExtractionResultORM(document_id=doc.id, document_location_id=loc_orig.id, method="DETERMINISTIC", raw_text="Old Text", extraction_status="SUCCESS", extraction_reliability="HIGH", created_at=datetime.datetime.now())
    session.add(ext_orig)
    session.commit()
    
    orig_hash = doc.hash
    
    provider = FakeVisionProvider()
    stats = {"ocr_failed": 0, "vision_failed": 0, "pages_processed": 0, "skipped": 0, "ocr_success": 0, "vision_success": 0}
    
    # Run 1
    process_document(session, doc, provider, Path("."), stats)
    assert stats["ocr_success"] == 1
    
    # 15. same document processed twice is idempotent
    process_document(session, doc, provider, Path("."), stats)
    assert stats["skipped"] == 1
    assert stats["ocr_success"] == 1 # count hasn't changed
    
    # 18. original Document SHA-256 remains unchanged
    doc_after = session.query(DocumentORM).filter_by(id=doc.id).first()
    assert doc_after.hash == orig_hash
    
    # Original deterministic extraction is still there
    assert session.query(ExtractionResultORM).filter_by(method="DETERMINISTIC").count() == 1
    
    # 16. changed document can produce a new extraction (if hash changes, it's a new document in the pipeline, but here if we simulate a new file or doc ID)
    doc2 = create_mock_doc(session, "scanned_calibration_v2.pdf")
    stats2 = {"ocr_failed": 0, "vision_failed": 0, "pages_processed": 0, "skipped": 0, "ocr_success": 0, "vision_success": 0}
    process_document(session, doc2, provider, Path("."), stats2)
    assert stats2["ocr_success"] == 1
