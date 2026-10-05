import pytest
from pathlib import Path
from aegis.ingestion.scanner import get_file_format, compute_hash
from aegis.models.domain import Format

def test_compute_hash(tmp_path):
    p = tmp_path / "test.txt"
    p.write_bytes(b"hello world")
    h = compute_hash(p)
    assert h == "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"

def test_get_file_format_valid(tmp_path):
    pdf = tmp_path / "test.pdf"
    pdf.write_bytes(b"%PDF-1.4\ncontent")
    fmt, err = get_file_format(pdf)
    assert fmt == Format.PDF
    assert err is None

    png = tmp_path / "test.png"
    png.write_bytes(b'\x89PNG\r\n\x1a\n')
    fmt, err = get_file_format(png)
    assert fmt == Format.PNG
    assert err is None

    jsonf = tmp_path / "test.json"
    jsonf.write_bytes(b'{"key": "value"}')
    fmt, err = get_file_format(jsonf)
    assert fmt == Format.JSON
    assert err is None

    zip_file = tmp_path / "test.docx"
    zip_file.write_bytes(b'PK\x03\x04\x00')
    fmt, err = get_file_format(zip_file)
    assert fmt == Format.DOCX
    assert err is None

def test_get_file_format_invalid(tmp_path):
    pdf = tmp_path / "fake.pdf"
    pdf.write_bytes(b"NOT A PDF")
    fmt, err = get_file_format(pdf)
    assert fmt is None
    assert "Invalid PDF" in err

    unknown = tmp_path / "test.xyz"
    unknown.write_bytes(b"data")
    fmt, err = get_file_format(unknown)
    assert fmt is None
    assert "Unsupported" in err
