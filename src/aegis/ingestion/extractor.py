import logging
from typing import Dict, List
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy.orm import Session
from aegis.storage.orm import DocumentORM, DocumentLocationORM, ExtractionResultORM
from aegis.storage.repository import WriteRepository
from aegis.ingestion.extractors.factory import ExtractorFactory
from aegis.ingestion.extractors.base import ExtractedUnit

logger = logging.getLogger(__name__)

class BatchExtractor:
    def __init__(self, session: Session, dataset_path: Path):
        self.session = session
        self.dataset_path = dataset_path.resolve()
        self.doc_repo = WriteRepository(session, DocumentORM)
        self.loc_repo = WriteRepository(session, DocumentLocationORM)
        self.ext_repo = WriteRepository(session, ExtractionResultORM)

    def extract_all(self) -> dict:
        stats = {
            "total_documents": 0,
            "SUCCESS": 0,
            "PARTIAL": 0,
            "REQUIRES_OCR": 0,
            "FAILED": 0,
            "UNSUPPORTED": 0,
            "total_results": 0
        }
        
        docs = self.session.query(DocumentORM).filter_by(is_latest=True).all()
        stats["total_documents"] = len(docs)
        
        for doc_orm in docs:
            file_path = (self.dataset_path / doc_orm.relative_path).resolve()
            
            if self.dataset_path not in file_path.parents:
                logger.error(f"Path traversal blocked for document {doc_orm.id}")
                stats["FAILED"] += 1
                continue
                
            extractor = ExtractorFactory.get_extractor(doc_orm.format)
            if not extractor:
                logger.warning(f"No extractor for format {doc_orm.format}")
                stats["UNSUPPORTED"] += 1
                continue
                
            try:
                units = extractor.extract(doc_orm, file_path)
                
                doc_status = "SUCCESS"
                
                if not units:
                    doc_status = "FAILED"
                else:
                    statuses = set(u.status.value for u in units)
                    if "FAILED" in statuses:
                        doc_status = "PARTIAL"
                    elif "REQUIRES_OCR" in statuses:
                        doc_status = "REQUIRES_OCR"
                
                for unit in units:
                    loc_orm = DocumentLocationORM(
                        document_id=doc_orm.id,
                        location_type=unit.location_type.value,
                        location_value=unit.location_value
                    )
                    self.loc_repo.add(loc_orm)
                    
                    ext_orm = ExtractionResultORM(
                        document_id=doc_orm.id,
                        document_location_id=loc_orm.id,
                        method=unit.method.value,
                        raw_text=unit.raw_text,
                        normalized_text=unit.raw_text,
                        extraction_reliability=unit.reliability.value,
                        extraction_status=unit.status.value,
                        created_at=datetime.now(timezone.utc)
                    )
                    self.ext_repo.add(ext_orm)
                    stats["total_results"] += 1
                    
                stats[doc_status] += 1
                
                self.session.commit()
                
            except Exception as e:
                logger.error(f"Failed to extract document {doc_orm.id}: {e}")
                self.session.rollback()
                stats["FAILED"] += 1
                
        return stats
