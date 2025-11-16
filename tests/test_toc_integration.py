"""
Integration tests for multi-page TOC generation and old-TOC handling.
"""

from __future__ import annotations

from typing import List

import fitz
import pytest

from pdfforge.core.toc import TOCGenerator


def make_content_pdf(page_count: int = 30) -> fitz.Document:
    """Create a content PDF with given number of pages and simple text labels."""
    doc = fitz.open()
    for i in range(page_count):
        page = doc.new_page(width=612, height=792)
        page.insert_text((72, 72), f"Content Page {i + 1}")
    return doc


def add_outline(doc: fitz.Document, titles: List[str]):
    """Set a simple outline where each title points to a valid 1-based page.

    If there are more titles than pages, map extra titles to the last page to stay within range.
    """
    toc = []
    page_count = doc.page_count
    for idx, t in enumerate(titles, start=1):
        page_num = idx if idx <= page_count else page_count
        toc.append([1, t, page_num])
    doc.set_toc(toc)


@pytest.mark.parametrize("toc_pages_needed", [2, 3])
def test_add_toc_multi_page_generation(tmp_path, toc_pages_needed):
    # Create a content PDF and add many bookmarks to force multiple TOC pages
    content_pages = 50 if toc_pages_needed == 3 else 25
    doc = make_content_pdf(page_count=content_pages)

    # Create many bookmarks — approx 40 per page with current defaults; we'll exceed one page
    titles = [f"Section {i}" for i in range(1, 120 if toc_pages_needed == 3 else 70)]
    add_outline(doc, titles)

    # Save input
    input_path = tmp_path / "input.pdf"
    doc.save(input_path.as_posix())
    doc.close()

    # Run TOC generation
    output_path = tmp_path / "output_with_toc.pdf"
    gen = TOCGenerator()
    result = gen.add_toc_to_pdf(
        input_pdf_path=input_path.as_posix(),
        output_pdf_path=output_path.as_posix(),
        bookmarks=None,  # extract from PDF
    )

    assert result["success"] is True
    assert result["toc_pages"] >= toc_pages_needed  # should be at least requested count

    # Open output and verify a few sampled outline entries are correctly offset
    out_doc = fitz.open(output_path.as_posix())
    try:
        toc = out_doc.get_toc()
        assert len(toc) >= 3
        num_toc_pages = result["toc_pages"]

        # Sample first, middle, last
        samples = [toc[0], toc[len(toc) // 2], toc[-1]]
        content_pages = len(out_doc) - num_toc_pages
        for level, title, page in samples:
            # page is 1-based in outline; should equal num_toc_pages + user_page
            # Estimate the intended user_page from title and clamp to content_pages
            if title.startswith("Section "):
                intended = int(title.split(" ")[1])
                user_page = min(intended, content_pages)
            else:
                # Fallback: skip if title not matching pattern
                continue
            assert page == num_toc_pages + user_page
    finally:
        out_doc.close()


def test_existing_toc_detection_and_normalization(tmp_path):
    # Build a PDF with two leading TOC-like pages, then content pages with bookmarks
    doc = fitz.open()
    # Old TOC pages
    for txt in ("Table of Contents", "Contents"):
        p = doc.new_page(width=612, height=792)
        p.insert_text((72, 72), txt)
    # Content pages
    for i in range(5):
        p = doc.new_page(width=612, height=792)
        p.insert_text((72, 72), f"Body Page {i + 1}")

    # Set bookmarks that (incorrectly) include the two TOC pages in their page numbers
    # PyMuPDF TOC uses 1-based page numbers; first content page is at PDF page 3
    doc.set_toc(
        [
            [1, "Intro", 3],  # should normalize to user page 1
            [1, "Next", 4],  # should normalize to user page 2
        ]
    )

    input_path = tmp_path / "with_old_toc.pdf"
    doc.save(input_path.as_posix())
    doc.close()

    # Extraction should normalize pages for UI to start from 1
    gen = TOCGenerator()
    pdf_doc = fitz.open(input_path.as_posix())
    try:
        bookmarks = gen.extract_bookmarks(pdf_doc)
        assert [b.page for b in bookmarks] == [1, 2]
    finally:
        pdf_doc.close()

    # And adding a new TOC should remove old ones and rebuild
    output_path = tmp_path / "rebuilt.pdf"
    result = gen.add_toc_to_pdf(
        input_pdf_path=input_path.as_posix(),
        output_pdf_path=output_path.as_posix(),
        bookmarks=None,
    )
    assert result["success"] is True
    assert result["old_toc_pages_removed"] >= 1  # at least one old TOC page removed

    # Verify outline points to shifted pages (num_toc_pages + user_page)
    out_doc = fitz.open(output_path.as_posix())
    try:
        num_toc_pages = result["toc_pages"]
        toc = out_doc.get_toc()
        first = toc[0]
        assert first[2] == num_toc_pages + 1  # Intro
    finally:
        out_doc.close()
