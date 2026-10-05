import os
import json
from typing import List
from pathlib import Path
from aegis.ingestion.vision.providers import VisionProvider
from aegis.ingestion.extractors.base import ExtractedUnit
from aegis.models.domain import Document, ExtractionMethod, ExtractionReliability, ExtractionStatus, LocationType

class FakeVisionProvider(VisionProvider):
    def extract_ocr(self, document: Document, file_path: Path) -> List[ExtractedUnit]:
        if "scanned" in file_path.name.lower():
            return [ExtractedUnit(
                raw_text="PS-0?A calibration: 195 bar",
                location_type=LocationType.PAGE,
                location_value="1",
                reliability=ExtractionReliability.LOW,
                status=ExtractionStatus.SUCCESS,
                method=ExtractionMethod.OCR
            )]
        elif "png" in file_path.name.lower() or "jpg" in file_path.name.lower():
            return [ExtractedUnit(
                raw_text="Some OCR text from image",
                location_type=LocationType.PIXEL_BOUNDS,
                location_value="0,0,100,100",
                reliability=ExtractionReliability.MEDIUM,
                status=ExtractionStatus.SUCCESS,
                method=ExtractionMethod.OCR
            )]
        return []

    def extract_vision(self, document: Document, file_path: Path) -> List[ExtractedUnit]:
        if "electrical" in file_path.name.lower():
            return [ExtractedUnit(
                raw_text=json.dumps({
                    "labels": ["PLC-03", "PS-04A"],
                    "connections": [{"source": "PLC-03", "target": "PS-04A", "type": "ELECTRICAL"}]
                }),
                location_type=LocationType.PIXEL_BOUNDS,
                location_value="10,10,200,200",
                reliability=ExtractionReliability.HIGH,
                status=ExtractionStatus.SUCCESS,
                method=ExtractionMethod.VISION_MODEL
            )]
        elif "hydraulic" in file_path.name.lower():
            return [ExtractedUnit(
                raw_text=json.dumps({
                    "labels": ["HPU", "IV-21"],
                    "connections": [{"source": "HPU", "target": "IV-21", "type": "HYDRAULIC"}]
                }),
                location_type=LocationType.PAGE,
                location_value="1",
                reliability=ExtractionReliability.MEDIUM,
                status=ExtractionStatus.SUCCESS,
                method=ExtractionMethod.VISION_MODEL
            )]
        elif "table" in file_path.name.lower():
            return [ExtractedUnit(
                raw_text=json.dumps({
                    "tables": [{"headers": ["Component", "Value"], "rows": [["PS-04", "180 bar"]]}]
                }),
                location_type=LocationType.PAGE,
                location_value="1",
                reliability=ExtractionReliability.HIGH,
                status=ExtractionStatus.SUCCESS,
                method=ExtractionMethod.VISION_MODEL
            )]
        elif "wiring" in file_path.name.lower():
            return [ExtractedUnit(
                raw_text=json.dumps({
                    "labels": ["Controller", "Sensor"],
                    "connections": [{"source": "Controller", "target": "Sensor", "type": "ELECTRICAL"}]
                }),
                location_type=LocationType.PAGE,
                location_value="1",
                reliability=ExtractionReliability.MEDIUM,
                status=ExtractionStatus.SUCCESS,
                method=ExtractionMethod.VISION_MODEL
            )]
        return []

class RealVisionProvider(VisionProvider):
    def __init__(self):
        self.api_key = os.getenv("VISION_API_KEY")
        if not self.api_key:
            # We don't crash, but we'll return an error status in the units or raise an exception that the script catches
            pass
            
    def extract_ocr(self, document: Document, file_path: Path) -> List[ExtractedUnit]:
        if not self.api_key:
            raise RuntimeError("VISION_API_KEY not set. Cannot perform OCR.")
        return []

    def extract_vision(self, document: Document, file_path: Path) -> List[ExtractedUnit]:
        if not self.api_key:
            raise RuntimeError("VISION_API_KEY not set. Cannot perform Vision extraction.")
        return []
