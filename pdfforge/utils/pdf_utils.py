"""
PDF Utility Functions
"""

import typing
from typing import Dict

import fitz  # type: ignore  # type: ignore  # type: ignore


def detect_pdf_type(page: fitz.Page) -> Dict[str, typing.Any]:
    """
    Detect if PDF page is image-based (scanned) or text-based.
    """
    try:
        text_content = page.get_text().strip()

        image_count = 0
        if "/Resources" in page and "/XObject" in page["/Resources"]:
            xObject = page["/Resources"]["/XObject"].get_object()
            for obj in xObject:
                if xObject[obj]["/Subtype"] == "/Image":
                    image_count += 1

        is_image_based = len(text_content) < 100 and image_count > 0

        return {
            "is_image_based": is_image_based,
            "text_length": len(text_content),
            "image_count": image_count,
            "has_content": len(text_content) > 0 or image_count > 0,
        }
    except Exception:
        return {
            "is_image_based": True,
            "text_length": 0,
            "image_count": 0,
            "has_content": False,
        }


def has_content_in_header_area(page: fitz.Page, threshold_y: int = 60) -> bool:
    """Detect if page has traditional header that needs extra space."""
    try:
        pdf_type = detect_pdf_type(page)

        if pdf_type["is_image_based"]:
            return True

        header_rect = fitz.Rect(0, 0, page.rect.width, 40)
        text = page.get_text("text", clip=header_rect).strip()

        if not text:
            drawings = page.get_drawings()
            for drawing in drawings:
                if drawing["rect"].y0 < 40 and drawing["rect"].height < 2:
                    return True
            return False

        lines = text.split("\n")
        header_keywords = [
            "confidential",
            "secret",
            "internal",
            "draft",
            "proprietary",
            "classified",
            "restricted",
        ]

        if len(text) < 100:
            text_lower = text.lower()
            if any(keyword in text_lower for keyword in header_keywords):
                return True

        if len(lines) <= 2 and all(len(line.strip()) < 50 for line in lines):
            return True

        return False

    except Exception:
        return True


def has_small_top_margin(page: fitz.Page, threshold: int = 80) -> bool:
    """Detect if page has very small top margin."""
    try:
        pdf_type = detect_pdf_type(page)

        if pdf_type["is_image_based"]:
            return True

        text_dict = page.get_text("dict")
        if not text_dict or "blocks" not in text_dict:
            return False

        min_y = float("inf")
        for block in text_dict["blocks"]:
            if block.get("type") == 0:
                if "lines" in block and block["lines"]:
                    first_line = block["lines"][0]
                    y_pos = first_line.get("bbox", [0, 0, 0, 0])[1]
                    min_y = min(min_y, y_pos)

        drawings = page.get_drawings()
        for drawing in drawings:
            if drawing["rect"].height > 5:
                min_y = min(min_y, drawing["rect"].y0)

        return min_y < threshold

    except Exception:
        return True


def has_text_layer(page: fitz.Page) -> bool:
    """Check if a PDF page has a text layer."""
    try:
        text = page.get_text().strip()
        return len(text) > 10
    except Exception:
        return False
