from aegis.models.domain import Format
from .base import DocumentExtractor
from .json_ext import JsonExtractor
from .xlsx_ext import XlsxExtractor
from .html_ext import HtmlExtractor
from .docx_ext import DocxExtractor
from .pptx_ext import PptxExtractor
from .pdf_ext import PdfExtractor
from .image_ext import ImageExtractor

class ExtractorFactory:
    _extractors = {
        Format.JSON.value: JsonExtractor(),
        Format.XLSX.value: XlsxExtractor(),
        Format.HTML.value: HtmlExtractor(),
        Format.DOCX.value: DocxExtractor(),
        Format.PPTX.value: PptxExtractor(),
        Format.PDF.value: PdfExtractor(),
        Format.PNG.value: ImageExtractor()
    }
    
    @classmethod
    def get_extractor(cls, format_val: str) -> DocumentExtractor:
        return cls._extractors.get(format_val)
