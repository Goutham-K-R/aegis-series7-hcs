import logging
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict
from sqlalchemy.orm import Session
from aegis.models.domain import IngestionStatus
from aegis.storage.orm import DocumentORM
from aegis.storage.repository import WriteRepository
from aegis.ingestion.scanner import get_file_format, compute_hash

logger = logging.getLogger(__name__)

class DocumentRegistry:
    def __init__(self, session: Session):
        self.session = session
        self.repo = WriteRepository(session, DocumentORM)
        
    def _is_safe_path(self, base_dir: Path, target_path: Path) -> bool:
        try:
            resolved_target = target_path.resolve(strict=True)
            resolved_base = base_dir.resolve(strict=True)
            return resolved_base in resolved_target.parents
        except Exception:
            return False

    def scan_and_register(self, base_dir: Path) -> dict:
        base_dir = base_dir.resolve()
        stats = {"discovered": 0, "new": 0, "unchanged": 0, "changed": 0, "duplicates": 0, "errors": 0}
        
        if not base_dir.exists() or not base_dir.is_dir():
            logger.error(f"Base directory {base_dir} does not exist.")
            return stats
            
        hash_dict = defaultdict(list)
            
        for filepath in base_dir.rglob("*"):
            if not filepath.is_file():
                continue
                
            stats["discovered"] += 1
                
            if not self._is_safe_path(base_dir, filepath):
                logger.error(f"Path traversal detected or invalid path: {filepath}")
                stats["errors"] += 1
                continue
                
            rel_path = str(filepath.relative_to(base_dir).as_posix())
            fmt, error = get_file_format(filepath)
            
            if error:
                logger.warning(f"File validation failed for {rel_path}: {error}")
                stats["errors"] += 1
                continue
                
            try:
                file_hash = compute_hash(filepath)
                file_size = filepath.stat().st_size
            except Exception as e:
                logger.warning(f"Failed to read file for hash: {rel_path} - {e}")
                stats["errors"] += 1
                continue
            
            hash_dict[file_hash].append(rel_path)
            
            # Check for existing document by relative path
            existing_docs = self.session.query(DocumentORM).filter_by(
                relative_path=rel_path, is_latest=True
            ).all()
            
            if not existing_docs:
                doc = DocumentORM(
                    filename=filepath.name,
                    relative_path=rel_path,
                    format=fmt.value,
                    hash=file_hash,
                    file_size=file_size,
                    discovered_timestamp=datetime.now(timezone.utc),
                    ingestion_status=IngestionStatus.REGISTERED.value,
                    version=1,
                    is_latest=True
                )
                self.repo.add(doc)
                stats["new"] += 1
            else:
                existing_doc = existing_docs[0]
                if existing_doc.hash == file_hash:
                    stats["unchanged"] += 1
                else:
                    existing_doc.is_latest = False
                    
                    new_doc = DocumentORM(
                        filename=filepath.name,
                        relative_path=rel_path,
                        format=fmt.value,
                        hash=file_hash,
                        file_size=file_size,
                        discovered_timestamp=datetime.now(timezone.utc),
                        ingestion_status=IngestionStatus.REGISTERED.value,
                        version=existing_doc.version + 1,
                        is_latest=True
                    )
                    self.repo.add(new_doc)
                    stats["changed"] += 1
                    
        self.session.commit()
        
        for h, paths in hash_dict.items():
            if len(paths) > 1:
                stats["duplicates"] += (len(paths) - 1)
                
        return stats
