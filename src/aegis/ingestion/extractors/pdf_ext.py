from pathlib import Path
from typing import List
from pypdf import PdfReader
from aegis.models.domain import Document, ExtractionMethod, ExtractionReliability, ExtractionStatus, LocationType
from .base import DocumentExtractor, ExtractedUnit

class PdfExtractor(DocumentExtractor):
    def extract(self, document: Document, file_path: Path) -> List[ExtractedUnit]:
        units = []
        try:
            reader = PdfReader(file_path)
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text and text.strip():
                    clean_text = " ".join(text.split())
                    units.append(ExtractedUnit(
                        raw_text=clean_text,
                        location_type=LocationType.PAGE,
                        location_value=f"Page {i + 1}",
                        reliability=ExtractionReliability.MEDIUM, # PDFs are inherently medium reliability due to layout
                        status=ExtractionStatus.SUCCESS,
                        method=ExtractionMethod.DETERMINISTIC
                    ))
                else:
                    # Likely scanned or image-only
                    units.append(ExtractedUnit(
                        raw_text="",
                        location_type=LocationType.PAGE,
                        location_value=f"Page {i + 1}",
                        reliability=ExtractionReliability.LOW,
                        status=ExtractionStatus.REQUIRES_OCR,
                        method=ExtractionMethod.DETERMINISTIC
                    ))
        except Exception as e:
            units.append(ExtractedUnit(
                raw_text="",
                location_type=LocationType.PAGE,
                location_value="Unknown",
                reliability=ExtractionReliability.LOW,
                status=ExtractionStatus.FAILED,
                method=ExtractionMethod.DETERMINISTIC
            ))
        return units
