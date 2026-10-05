from pathlib import Path
from typing import List
from bs4 import BeautifulSoup
from aegis.models.domain import Document, ExtractionMethod, ExtractionReliability, ExtractionStatus, LocationType
from .base import DocumentExtractor, ExtractedUnit

class HtmlExtractor(DocumentExtractor):
    def extract(self, document: Document, file_path: Path) -> List[ExtractedUnit]:
        units = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f, 'html.parser')
                
            # Extract basic tags
            for idx, element in enumerate(soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'td', 'th'])):
                text = element.get_text(separator=' ', strip=True)
                if text:
                    clean_text = " ".join(text.split())
                    units.append(ExtractedUnit(
                        raw_text=clean_text,
                        location_type=LocationType.SECTION,
                        location_value=f"{element.name}_{idx}",
                        reliability=ExtractionReliability.HIGH,
                        status=ExtractionStatus.SUCCESS,
                        method=ExtractionMethod.DETERMINISTIC
                    ))
        except Exception as e:
            units.append(ExtractedUnit(
                raw_text="",
                location_type=LocationType.SECTION,
                location_value="Unknown",
                reliability=ExtractionReliability.LOW,
                status=ExtractionStatus.FAILED,
                method=ExtractionMethod.DETERMINISTIC
            ))
        return units
