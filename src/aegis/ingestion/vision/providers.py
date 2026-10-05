from abc import ABC, abstractmethod
from typing import List
from pathlib import Path
from aegis.ingestion.extractors.base import ExtractedUnit
from aegis.models.domain import Document

class VisionProvider(ABC):
    """Base interface for OCR and Vision models."""
    
    @abstractmethod
    def extract_ocr(self, document: Document, file_path: Path) -> List[ExtractedUnit]:
        """Extract text using basic OCR."""
        pass
        
    @abstractmethod
    def extract_vision(self, document: Document, file_path: Path) -> List[ExtractedUnit]:
        """Extract structured information using a vision model (e.g., for diagrams/tables)."""
        pass
