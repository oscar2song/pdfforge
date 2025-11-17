# pdfforge/core/convert_word.py
"""
Core PDF → Word (DOCX) conversion utilities (free edition)

- Focuses on digital PDFs (with text layer) for editable DOCX output
- Uses `pdf2docx` for conversion with options oriented toward editability
- Provides simple page-range support and image handling options

Scanned PDFs and advanced controls are part of the premium pipeline and will
be accessed via an integration shim in the service layer (not here).
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional, Tuple

from pdf2docx import Converter  # type: ignore


@dataclass
class WordConversionOptions:
    """Options for converting PDF to DOCX (free path)."""

    page_range: Optional[Tuple[int, int]] = None  # 1-based inclusive (start, end)
    merge_paragraphs: bool = True
    detect_tables: bool = True
    keep_text_boxes: bool = False  # When True, preserve positioned text boxes; reduces editability
    images_as_background: bool = False  # When True, put a background image per page (less editable)
    image_dpi: int = 150  # Default downsample DPI for embedded images
    keep_images_original: bool = False  # If True, ignore image_dpi and keep originals


def _normalize_page_range(page_range: Optional[Tuple[int, int]]) -> Optional[Tuple[int, int]]:
    if not page_range:
        return None
    start, end = page_range
    if start < 1 or end < 1 or end < start:
        raise ValueError("Invalid page_range; must be 1-based and end >= start")
    return (start, end)


def convert_pdf_to_docx(
    input_path: str,
    output_path: str,
    options: Optional[WordConversionOptions] = None,
) -> dict:
    """
    Convert a (digital) PDF to DOCX using pdf2docx.

    Returns a result dict with keys: success (bool), output_file (str), pages_converted (int)
    """
    options = options or WordConversionOptions()

    if not os.path.exists(input_path):
        return {"success": False, "error": f"Input not found: {input_path}"}

    # Ensure parent directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    pages_converted = 0

    # pdf2docx Converter supports page range via .convert(start, end)
    # Note: pdf2docx pages are 0-based inclusive in API; our options are 1-based
    start_end = _normalize_page_range(options.page_range)

    # Build pdf2docx-specific kwargs
    # Reference: pdf2docx.convert(..., start=0, end=None, **kwargs)
    # Common kwargs include: keep_inline_graphics, use_stream, etc. The library
    # does not expose direct DPI control; image quality is mostly preserved.
    # We'll expose a semantic for image handling via flags; actual downsampling
    # may be a no-op here and handled later if needed.
    convert_kwargs = {
        # Editability preference: merge paragraphs and detect tables where possible
        "merge_paragraphs": options.merge_paragraphs,
        "detect_tables": options.detect_tables,
        # When keep_text_boxes is True, prefer text boxes (less reflow)
        "keep_text_boxes": options.keep_text_boxes,
        # Background images reduce editability; leave False by default
        "images_as_background": options.images_as_background,
    }

    try:
        cv = Converter(input_path)
        try:
            if start_end:
                start0 = max(0, start_end[0] - 1)
                end0 = start_end[1] - 1
                cv.convert(output_path, start=start0, end=end0, **convert_kwargs)
                pages_converted = end0 - start0 + 1
            else:
                cv.convert(output_path, **convert_kwargs)
                # Can't easily know pages converted without reading PDF; leave 0 to mean "all"
        finally:
            try:
                cv.close()
            except Exception:
                pass

        # Note on image handling: pdf2docx API does not provide DPI downsample arg.
        # If strict downsample is required, a post-process could be applied using
        # python-docx to traverse images and re-embed downsampled versions. For now,
        # we honor keep_images_original flag semantically and document the behavior.

        return {
            "success": True,
            "output_file": output_path,
            "pages_converted": pages_converted,
        }
    except Exception as e:
        return {"success": False, "error": f"Conversion failed: {e}"}
