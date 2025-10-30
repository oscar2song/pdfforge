"""
OCR Utility Functions
"""

import io
import re

import fitz  # type: ignore  # type: ignore  # type: ignore
import pytesseract  # type: ignore  # type: ignore  # type: ignore
from PIL import Image


def detect_existing_page_numbers(page: fitz.Page, position: str, font_size: int) -> bool:
    """
    Detect if there are existing page numbers at the target position.
    """
    try:
        page_width = page.rect.width
        page_height = page.rect.height

        # Define detection areas based on position
        if position == "top-center":
            detect_rect = fitz.Rect(page_width / 2 - 50, 10, page_width / 2 + 50, 40)
        elif position == "bottom-center":
            detect_rect = fitz.Rect(
                page_width / 2 - 50,
                page_height - 40,
                page_width / 2 + 50,
                page_height - 10,
            )
        elif position == "top-right":
            detect_rect = fitz.Rect(page_width - 100, 10, page_width - 10, 40)
        elif position == "bottom-right":
            detect_rect = fitz.Rect(
                page_width - 100,
                page_height - 40,
                page_width - 10,
                page_height - 10,
            )
        else:  # top-center as default
            detect_rect = fitz.Rect(page_width / 2 - 50, 10, page_width / 2 + 50, 40)

        # Extract text from detection area
        text = page.get_text("text", clip=detect_rect).strip()

        # Look for page number patterns
        page_number_patterns = [
            r"\b\d{1,3}\b",  # 1-3 digit numbers
            r"\bpage\s*\d+\b",  # "page 1" etc.
            r"\b\d+\s*of\s*\d+\b",  # "1 of 10" etc.
        ]

        for pattern in page_number_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True

        return False

    except Exception:
        return False


def get_safe_page_number_position(page: fitz.Page, preferred_position: str, font_size: int) -> str:
    """
    Find a safe position for page number that doesn't
    conflict with existing content.
    """
    positions_to_try = [
        preferred_position,
        "top-right",
        "bottom-right",
        "bottom-center",
        "top-center",  # Fallback to original
    ]

    for position in positions_to_try:
        if not detect_existing_page_numbers(page, position, font_size):
            return position

    return "top-right"


def perform_ocr_on_page(page: fitz.Page) -> str:
    """Perform OCR on a PDF page to extract text."""
    try:
        pix = page.get_pixmap(matrix=fitz.Matrix(300 / 72, 300 / 72))
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        text = pytesseract.image_to_string(img)
        return str(text)
    except Exception:
        return ""


def add_text_layer_ocr(page: fitz.Page, text: str):
    """Add invisible text layer to a PDF page for searchability."""
    if not text or len(text.strip()) < 5:
        return

    rect = page.rect
    try:
        page.insert_textbox(rect, text, fontsize=1, color=(1, 1, 1), align=fitz.TEXT_ALIGN_LEFT)
    except Exception:
        pass
