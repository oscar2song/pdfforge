"""
Unit tests for TOC core helpers and extraction normalization.
"""

from __future__ import annotations

from typing import List

import fitz

from pdfforge.core.toc import TOCGenerator


def make_pdf_with_texts(texts: List[str]) -> fitz.Document:
    """Create an in-memory PDF where each string in texts is the full-page text of a page."""
    doc = fitz.open()
    for t in texts:
        page = doc.new_page(width=612, height=792)
        # Put the text near the top so get_text() surely captures it
        page.insert_text((72, 72), t)
    return doc


class TestDetectExistingTOCPages:
    def test_detects_zero_when_no_keywords(self):
        doc = make_pdf_with_texts(["Hello", "World"])  # no TOC keywords
        try:
            gen = TOCGenerator()
            count = gen._detect_existing_toc_pages(doc)
            assert count == 0
        finally:
            doc.close()

    def test_detects_one_toc_page(self):
        doc = make_pdf_with_texts(["Table of Contents", "First chapter"])  # 1 TOC page at start
        try:
            gen = TOCGenerator()
            count = gen._detect_existing_toc_pages(doc)
            assert count == 1
        finally:
            doc.close()

    def test_detects_two_consecutive_toc_pages(self):
        # Two consecutive pages with TOC-like content
        doc = make_pdf_with_texts(["Table of Contents", "Contents", "Body starts"])
        try:
            gen = TOCGenerator()
            count = gen._detect_existing_toc_pages(doc)
            assert count == 2
        finally:
            doc.close()

    def test_stops_counting_on_break(self):
        # First is TOC-like, second is not => should not count further
        doc = make_pdf_with_texts(["Contents", "Body starts", "Contents"])  # only leading pages are counted
        try:
            gen = TOCGenerator()
            count = gen._detect_existing_toc_pages(doc)
            assert count == 1
        finally:
            doc.close()


class TestExtractBookmarksNormalization:
    def test_extract_bookmarks_normalizes_by_old_toc_pages(self):
        # Build a PDF with 2 leading TOC pages to trigger detection
        doc = make_pdf_with_texts(["Table of Contents", "Contents", "Chapter 1", "Chapter 2"])
        try:
            # Set a TOC that references PDF pages in 1-based terms (PyMuPDF convention)
            # Suppose original bookmarks pointed at the first content page as page 3 (after two TOC pages)
            # Structure: [level, title, page]
            doc.set_toc(
                [
                    [1, "Intro", 3],
                    [1, "Chapter 2", 4],
                ]
            )

            gen = TOCGenerator()
            bookmarks = gen.extract_bookmarks(doc)

            # Expect normalization: subtract detected 2 TOC pages so UI starts at 1
            assert [b.title for b in bookmarks] == ["Intro", "Chapter 2"]
            assert [b.page for b in bookmarks] == [1, 2]
            assert [b.level for b in bookmarks] == [0, 0]
        finally:
            doc.close()

    def test_extract_returns_empty_when_no_toc(self):
        doc = make_pdf_with_texts(["Hello world"])  # no bookmarks
        try:
            gen = TOCGenerator()
            # Ensure get_toc() returns [] by default
            assert doc.get_toc() == []
            bookmarks = gen.extract_bookmarks(doc)
            assert bookmarks == []
        finally:
            doc.close()
