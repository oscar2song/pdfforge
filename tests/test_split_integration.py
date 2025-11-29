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


def test_split_pages_start_pages_1_3_7_produces_expected_suffixes(tmp_path):
    # Create a 10-page test PDF
    input_pdf = tmp_path / "sample.pdf"
    _make_pdf(str(input_pdf), 10)

    svc = SplitService()
    payload = svc.split(str(input_pdf), {"split_type": "pages", "page_ranges": "1,3,7"})
    assert payload.get("success"), payload
    files = payload.get("output_files", [])

    # Expect exactly three outputs with suffixes 1-2, 3-6, 7-10
    assert len(files) == 3, files
    names = [Path(f).name for f in files]
    assert any(name.endswith("split_pages_1-2.pdf") for name in names), names
    assert any(name.endswith("split_pages_3-6.pdf") for name in names), names
    assert any(name.endswith("split_pages_7-10.pdf") for name in names), names

    # Clean up created outputs
    for f in files:
        try:
            os.remove(f)
        except Exception:
            pass
