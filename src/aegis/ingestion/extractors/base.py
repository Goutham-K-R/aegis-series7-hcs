from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from pathlib import Path
from aegis.models.domain import Document, ExtractionResult, ExtractionStatus, ExtractionMethod, ExtractionReliability, LocationType

class ExtractedUnit:
    """A single piece of extracted content with provenance."""
    def __init__(self, raw_text: str, location_type: LocationType, location_value: str, reliability: ExtractionReliability, status: ExtractionStatus, method: ExtractionMethod):
        self.raw_text = raw_text
        self.location_type = location_type
        self.location_value = location_value
        self.reliability = reliability
        self.status = status
        self.method = method

class DocumentExtractor(ABC):
    """Base interface for all document extractors."""
    @abstractmethod
    def extract(self, document: Document, file_path: Path) -> List[ExtractedUnit]:
        """Extract content units from the document."""
        pass
