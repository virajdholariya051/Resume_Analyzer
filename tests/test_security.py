"""Security-focused tests: filename sanitization, PDF fallback, error handling."""

import os
import tempfile
from backend.utils.file_parser import save_uploaded_file, extract_text


class _FakeUpload:
    """Minimal stand-in for a Streamlit UploadedFile."""

    def __init__(self, name, data=b"hello"):
        self.name = name
        self._data = data

    def getbuffer(self):
        return self._data


def test_save_upload_strips_path_traversal():
    """A malicious filename must not escape the upload directory."""
    up_dir = tempfile.mkdtemp(prefix="ra_upload_")
    malicious = _FakeUpload(os.path.join("..", "..", "evil.pdf"))
    path = save_uploaded_file(malicious, up_dir)
    assert path is not None
    # Resolved path must remain inside the upload directory.
    assert os.path.commonpath([os.path.abspath(up_dir), os.path.abspath(path)]) == os.path.abspath(up_dir)
    assert os.path.basename(path) == "evil.pdf"


def test_extract_text_unsupported_extension():
    assert extract_text("somefile.txt") is None


def test_extract_text_missing_pdf_returns_none():
    """A non-existent / corrupt PDF should return None, not raise."""
    assert extract_text("does_not_exist_12345.pdf") is None


def test_extract_text_corrupt_pdf(tmp_path):
    """A file with a .pdf extension but garbage content returns None gracefully."""
    bad = tmp_path / "corrupt.pdf"
    bad.write_bytes(b"%PDF-1.4 this is not a real pdf body \x00\x01")
    assert extract_text(str(bad)) is None
