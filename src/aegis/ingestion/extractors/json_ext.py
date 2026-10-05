import json
from pathlib import Path
from typing import List
from aegis.models.domain import Document, ExtractionMethod, ExtractionReliability, ExtractionStatus, LocationType
from .base import DocumentExtractor, ExtractedUnit

class JsonExtractor(DocumentExtractor):
    def extract(self, document: Document, file_path: Path) -> List[ExtractedUnit]:
        units = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            def traverse(obj, path):
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        traverse(v, f"{path}.{k}" if path else f"$.{k}")
                elif isinstance(obj, list):
                    for i, v in enumerate(obj):
                        traverse(v, f"{path}[{i}]")
                else:
                    if obj is not None and str(obj).strip():
                        # normalize whitespace but preserve exact values
                        clean_text = " ".join(str(obj).split())
                        units.append(ExtractedUnit(
                            raw_text=clean_text,
                            location_type=LocationType.SECTION,
                            location_value=path if path else "$",
                            reliability=ExtractionReliability.HIGH,
                            status=ExtractionStatus.SUCCESS,
                            method=ExtractionMethod.DETERMINISTIC
                        ))
            
            traverse(data, "")
            
        except Exception as e:
            units.append(ExtractedUnit(
                raw_text="",
                location_type=LocationType.SECTION,
                location_value="root",
                reliability=ExtractionReliability.LOW,
                status=ExtractionStatus.FAILED,
                method=ExtractionMethod.DETERMINISTIC
            ))
        return units
