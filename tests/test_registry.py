import pytest
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from aegis.storage.orm import Base, DocumentORM
from aegis.ingestion.registry import DocumentRegistry

@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    sess = Session()
    yield sess
    sess.close()

def test_scan_and_register_empty(session, tmp_path):
    registry = DocumentRegistry(session)
    stats = registry.scan_and_register(tmp_path)
    assert stats["discovered"] == 0
    assert stats["errors"] == 0

def test_scan_and_register_files(session, tmp_path):
    registry = DocumentRegistry(session)
    
    # Create valid files
    pdf1 = tmp_path / "doc1.pdf"
    pdf1.write_bytes(b"%PDF-doc1")
    
    # Nested directory
    nested = tmp_path / "nested"
    nested.mkdir()
    json1 = nested / "data.json"
    json1.write_bytes(b'{"a": 1}')
    
    # Invalid file
    invalid = tmp_path / "bad.pdf"
    invalid.write_bytes(b"not pdf")
    
    # Duplicate file
    pdf2 = tmp_path / "doc2.pdf"
    pdf2.write_bytes(b"%PDF-doc1") # Same content as doc1
    
    stats = registry.scan_and_register(tmp_path)
    
    assert stats["discovered"] == 4
    assert stats["errors"] == 1 # bad.pdf
    assert stats["new"] == 3
    assert stats["duplicates"] == 1
    
    # Test change detection
    pdf1.write_bytes(b"%PDF-doc1-changed")
    
    stats2 = registry.scan_and_register(tmp_path)
    assert stats2["discovered"] == 4
    assert stats2["errors"] == 1
    assert stats2["changed"] == 1
    assert stats2["unchanged"] == 2 # doc2, nested json
    
    docs = session.query(DocumentORM).filter_by(relative_path="doc1.pdf").order_by(DocumentORM.version.desc()).all()
    assert len(docs) == 2
    assert docs[0].version == 2
    assert docs[0].is_latest is True
    assert docs[1].version == 1
    assert docs[1].is_latest is False

def test_path_traversal(session, tmp_path):
    registry = DocumentRegistry(session)
    
    target_path = Path("/etc/passwd")
    # _is_safe_path should return False for paths outside base_dir
    assert not registry._is_safe_path(tmp_path, target_path)
