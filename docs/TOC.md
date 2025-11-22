# Table of Contents (TOC) — Generator and Styling Guide

This guide explains how PDFForge generates Table of Contents (TOC) pages, how bookmarks are interpreted, and how to customize the layout via `TOCStyle`.

## Overview

TOC generation is implemented in:
- `src/src/pdfforge/core/toc.py` — classes `TOCGenerator`, `TOCStyle`, `BookmarkEntry`, and `BookmarkManager`
- `src/src/pdfforge/services/toc_service.py` — service layer wrappers used by routes and UI

Typical workflows:
- Extract existing PDF bookmarks (for preview/edit in UI)
- Add TOC pages at the beginning with Roman numeral pagination
- Update the PDF outline (bookmarks) so they point to the correct pages after TOC insertion

## Key Data Classes

### `BookmarkEntry`
Represents a single entry that appears in the TOC and the PDF bookmarks.

```
@dataclass
class BookmarkEntry:
    title: str
    page: int   # User page number (1-based, content pages)
    level: int = 0
```

Notes:
- `page` is 1-based and refers to the content page number as the user sees it (Arabic numerals). Do not include TOC pages in this numbering.

### `TOCStyle`
Controls the visual appearance and layout of the TOC pages.

```
@dataclass
class TOCStyle:
    font_name: str = "helv"
    font_size: int = 12
    title: str = "Table of Contents"
    title_font_size: int = 18
    show_page_numbers: bool = True
    indent_per_level: int = 20
    leader_dots: bool = False
    line_spacing: float = 1.67
    margin_top: int = 80
    margin_left: int = 60
    margin_right: int = 50
    margin_bottom: int = 72
    separator_left: float = 50.0
    separator_right: float = 562.0
    page_number_x: float = 500.0
    page_number_position: str = "bottom-center"    # "top-center", "bottom-center", "top-right", "bottom-right"
    page_number_font_size: int = 11
```

Important fields:
- `leader_dots`: if you want dotted leaders between titles and numbers, enable this and draw via `_draw_leader_dots()` (currently optional in layout).
- `page_number_position`: where Roman numerals appear on TOC pages.
- `separator_left`/`separator_right` and `page_number_x` are adapted at runtime to the actual page width.

## Page Numbering Model

- Users supply bookmarks with pages `1, 2, 3, ...` that refer to the content pages only.
- When TOC pages are inserted at the beginning, the PDF’s internal page indices shift.
- We keep the TOC text showing user page numbers, but link targets and PDF bookmarks must point to the new, actual PDF pages.

### Link Target Calculation
Given:
- `num_toc_pages` — the number of TOC pages inserted at the beginning
- `bookmark.page` — the user-facing content page number (1-based)

Target PDF page index (0-based) for a link is:
```
num_toc_pages + (bookmark.page - 1)
```

This ensures clicking a TOC entry jumps to the correct page in the document after the TOC has been inserted.

### PDF Bookmarks (Outline) Calculation
PDF bookmarks use 1-based page numbers. After inserting TOC pages at the beginning, each content page is shifted by `num_toc_pages` pages. Therefore the correct bookmark page is:
```
actual_pdf_page = num_toc_pages + bookmark.page
```

## Multi‑Page TOC

The generator splits bookmarks across multiple TOC pages based on available vertical space:
- It computes `max_entries_per_page` using margins and `line_spacing`.
- Bookmarks are sliced into batches per page.
- First page shows the title and a separator line; subsequent pages show a continuation header.

## Three‑Column TOC Layout and Title Wrapping

The TOC rows use a professional three‑column layout that prevents long titles from overflowing the margins:

- Left column: Title text. Long titles automatically wrap into multiple lines within the available width.
- Middle (optional): Leader dots. When `leader_dots=True`, dotted leaders are drawn along the last title line’s baseline toward the page number column.
- Right column: Page number, right‑aligned. The column reserves width for up to 4–5 digits, keeping alignment consistent.

The columns adapt to the detected page size (Letter, A4, etc.) by measuring the page width and font metrics at runtime. The clickable link rectangle for each TOC entry spans the full wrapped block so clicking anywhere on the entry jumps to the correct destination.

### New `TOCStyle` fields for layout

```
@dataclass
class TOCStyle:
    inter_col_gap: int = 12              # gap between title and page number columns
    page_number_reserve_digits: int = 5  # reserve width for up to N digits
    dot_spacing: int = 8                 # spacing between leader dots (points)
    dot_radius: float = 0.5              # radius for each dot
    leader_dots: bool = False            # enable/disable dotted leaders
```

Notes:
- The layout respects existing margins: `margin_left`, `margin_right`, and `indent_per_level` for nested entries.
- `page_number_reserve_digits` keeps page numbers neatly aligned even for large documents.
- When `leader_dots` is enabled, the dots won’t intrude into the page‑number reserve column.
- Link targets and PDF outline calculations remain unchanged (see formulas above).

## Roman Numerals on TOC Pages

TOC pages use Roman numerals (e.g., `i, ii, iii, ...`) drawn at the position specified by `page_number_position` with `page_number_font_size`.

## Service Layer Usage

The `TOCService` builds a `TOCStyle` from a JSON dict and calls `TOCGenerator.add_toc_to_pdf(...)`. Example:

```python
from pdfforge.core.toc import TOCStyle, BookmarkEntry
from pdfforge.services.toc_service import TOCService

svc = TOCService()
bookmarks = [
    BookmarkEntry(title="Introduction", page=1, level=0),
    BookmarkEntry(title="Chapter 1", page=3, level=0),
    BookmarkEntry(title="Section 1.1", page=4, level=1),
]

toc_style = {
    "title": "Table of Contents",
    "show_page_numbers": True,
    "leader_dots": False,
    "page_number_position": "bottom-center",
    "page_number_font_size": 10,
}

result = svc.add_toc_to_file(
    input_path="/path/to/input.pdf",
    original_filename="input.pdf",
    bookmarks_data=[{"title": b.title, "page": b.page, "level": b.level} for b in bookmarks],
    toc_style_config=toc_style,
)
```

## Tips and Edge Cases

- Ensure there is at least one bookmark; otherwise TOC generation will return an error.
- Extremely long titles may wrap visually; consider shorter titles or reduced font size.
- Deeply nested levels are supported (`indent_per_level` controls indent).
- For very large documents, the generator automatically creates multiple TOC pages.
- When customizing layout, remember `separator_left/right` and `page_number_x` are adjusted to the page width; you can provide defaults but the generator will align them at runtime.

## Troubleshooting

- If links don’t land on the expected page, verify the link target calculation and the number of inserted TOC pages.
- If Roman numerals overlap content, tweak `page_number_position` or `page_number_font_size`.
- Verify fonts: the code uses `helv` (Helvetica/Arial) name exposed by PyMuPDF.


## Existing TOC detection & normalization

Some PDFs already contain TOC pages at the beginning. PDFForge will:

- Detect consecutive TOC pages at the start by scanning text for keywords like "Table of Contents" or "Contents" within the first 10 pages.
- Normalize extracted bookmarks so the UI always shows the document body starting from page 1 (TOC pages are excluded from numbering).
- When adding a new TOC, remove old TOC pages and rebuild links/outline so that:
  - TOC text shows user page numbers (1, 2, 3, ...), excluding TOC pages.
  - Click targets use: `target_index = num_toc_pages + (bookmark.page - 1)` (0-based page index).
  - PDF outline entries use: `actual_pdf_page = num_toc_pages + bookmark.page` (1-based page number).

Notes:
- Detection is conservative to avoid false positives and only considers leading pages.
- If more keywords are desired (e.g., localized titles), detection can be extended easily.
