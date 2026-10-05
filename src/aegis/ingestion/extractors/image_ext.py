from pathlib import Path
from typing import List
from aegis.models.domain import Document, ExtractionMethod, ExtractionReliability, ExtractionStatus, LocationType
from .base import DocumentExtractor, ExtractedUnit

class ImageExtractor(DocumentExtractor):
    def extract(self, document: Document, file_path: Path) -> List[ExtractedUnit]:
        # No deterministic OCR available without ML/Vision dependencies
        return [ExtractedUnit(
            raw_text="",
            location_type=LocationType.PIXEL_BOUNDS,
            location_value="Entire Image",
            reliability=ExtractionReliability.LOW,
            status=ExtractionStatus.REQUIRES_OCR,
            method=ExtractionMethod.VISION_MODEL
        )]
