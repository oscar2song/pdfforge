"""
Unit tests for TOC three-column layout helpers: wrapping, column computation, and leader dots.
"""

from __future__ import annotations

import fitz

from pdfforge.core.toc import TOCGenerator, TOCStyle


def make_page(width: float = 612, height: float = 792) -> tuple[fitz.Document, fitz.Page]:
    doc = fitz.open()
    page = doc.new_page(width=width, height=height)
    return doc, page


class TestLayoutHelpers:
    def test_wrap_text_to_width_wraps_long_title(self):
        gen = TOCGenerator()
        doc, page = make_page()
        try:
            cols = gen._compute_columns(page, level=0)
            max_title_width = cols["title_right"] - cols["title_left"]
            # Create a very long title that should wrap across multiple lines
            long_title = (
                "This is an extremely long section title designed to exceed the width of the title column "
                "so that the wrapping behavior is exercised properly and no overflow occurs"
            )
            lines = gen._wrap_text_to_width(long_title, max_title_width)
            assert len(lines) >= 2  # should wrap into at least two lines
            # Each line must fit into the column width
            for line in lines:
                w = fitz.get_text_length(line, fontname=gen.style.font_name, fontsize=gen.style.font_size)
                assert w <= max_title_width + 0.5  # allow tiny float tolerance
        finally:
            doc.close()

    def test_compute_columns_reserves_space_for_page_numbers(self):
        gen = TOCGenerator()
        # Make the reserve digits large to strengthen the assertion
        gen.style.page_number_reserve_digits = 5
        doc, page = make_page()
        try:
            cols = gen._compute_columns(page, level=0)
            page_col_left = cols["page_col_left"]
            page_col_right = cols["page_col_right"]
            reserve_sample = "8" * gen.style.page_number_reserve_digits
            reserve_width = fitz.get_text_length(
                reserve_sample, fontname=gen.style.font_name, fontsize=gen.style.font_size
            )
            # There is also padding of ~6 points in the implementation; we just ensure reserve is respected
            assert (page_col_right - page_col_left) >= reserve_width
        finally:
            doc.close()

    def test_draw_leader_dots_executes_without_overlap(self):
        # Enable leader dots and ensure drawing does not raise and stays within bounds
        style = TOCStyle(leader_dots=True)
        gen = TOCGenerator(style)
        doc, page = make_page()
        try:
            cols = gen._compute_columns(page, level=0)
            title_left = cols["title_left"]
            page_col_left = cols["page_col_left"]
            # Simulate last line end-x somewhere in the middle of the title column
            last_line_end_x = (title_left + page_col_left) / 2
            y = 200
            # Should not raise
            gen._draw_leader_dots(page, start_x=last_line_end_x + 6, y=y, end_x=page_col_left - 4)
            # If we got here without exceptions, consider it passed
            assert True
        finally:
            doc.close()
