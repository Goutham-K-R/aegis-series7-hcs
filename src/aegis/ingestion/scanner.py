import hashlib
import json
from pathlib import Path
from typing import Optional, Tuple
from aegis.models.domain import Format

def get_file_format(path: Path) -> Tuple[Optional[Format], Optional[str]]:
    """Determine format via extension and content validation. Return (Format, ErrorString)."""
    ext = path.suffix.lower()
    
    # Read magic bytes
    try:
        with open(path, 'rb') as f:
            header = f.read(8)
    except Exception as e:
        return None, f"Failed to read file: {e}"
        
    if ext == '.pdf':
        if header.startswith(b'%PDF'):
            return Format.PDF, None
        return None, "Invalid PDF magic bytes"
    elif ext == '.png':
        if header.startswith(b'\x89PNG\r\n\x1a\n'):
            return Format.PNG, None
        return None, "Invalid PNG magic bytes"
    elif ext in ('.docx', '.xlsx', '.pptx'):
        if header.startswith(b'PK\x03\x04'):
            if ext == '.docx': return Format.DOCX, None
            if ext == '.xlsx': return Format.XLSX, None
            if ext == '.pptx': return Format.PPTX, None
        return None, f"Invalid {ext} magic bytes (not a ZIP/Office Open XML)"
    elif ext == '.json':
        try:
            with open(path, 'r', encoding='utf-8') as f:
                json.load(f)
            return Format.JSON, None
        except Exception:
            return None, "Invalid JSON content"
    elif ext in ('.html', '.htm'):
        # Just ensure we can read it as text, HTML can start with anything depending on formatting
        try:
            with open(path, 'r', encoding='utf-8') as f:
                f.read(1024)
            return Format.HTML, None
        except Exception:
            return None, "Invalid HTML content"
            
    return None, f"Unsupported extension: {ext}"

def compute_hash(path: Path, chunk_size=8192) -> str:
    sha256 = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b''):
            sha256.update(chunk)
    return sha256.hexdigest()
