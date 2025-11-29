import os
from pathlib import Path

from pdfforge.services.split_service import SplitService
from PyPDF2 import PdfWriter


def _make_pdf(path: str, pages: int):
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=595, height=842)
    with open(path, "wb") as f:
        writer.write(f)


def test_split_pages_ranges_hyphens(tmp_path):
    # Create a 12-page test PDF
    input_pdf = tmp_path / "sample2.pdf"
    _make_pdf(str(input_pdf), 12)

    svc = SplitService()
    payload = svc.split(str(input_pdf), {"split_type": "pages", "page_ranges": "1-2,6-9"})
    assert payload.get("success"), payload
    files = payload.get("output_files", [])

    # Expect two outputs with suffixes 1-2 and 6-9
    assert len(files) == 2, files
    names = [Path(f).name for f in files]
    assert any(name.endswith("split_pages_1-2.pdf") for name in names), names
    assert any(name.endswith("split_pages_6-9.pdf") for name in names), names

    for f in files:
        try:
            os.remove(f)
        except Exception:
            pass
