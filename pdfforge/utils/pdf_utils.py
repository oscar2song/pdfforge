"""
PDF Utility Functions
"""

import fitz  # type: ignore
from typing import Dict, Any, Optional
from ..exceptions.pdf_exceptions import PDFValidationError


def validate_pdf(file_path: str) -> bool:
    """
    Validate that a file is a valid PDF
    """
    try:
        with fitz.open(file_path) as doc:
            # If we can open it without errors, it's a valid PDF
            page_count = len(doc)
            if page_count == 0:
                raise PDFValidationError("PDF has no pages")
            return True
    except Exception as e:
        raise PDFValidationError(f"Invalid PDF file: {str(e)}")


def analyze_pdf(file_path: str) -> Dict[str, Any]:
    """
    Analyze PDF properties and return analysis results
    """
    try:
        with fitz.open(file_path) as doc:
            page_count = len(doc)

            # Analyze first page for basic properties
            if page_count > 0:
                first_page = doc[0]
                page_size = first_page.rect
                page_width = page_size.width
                page_height = page_size.height

                # Determine page orientation
                if page_width > page_height:
                    orientation = "landscape"
                else:
                    orientation = "portrait"

                # Determine page size category
                if page_width > 1000 or page_height > 1000:
                    size_category = "large"
                elif page_width < 400 or page_height < 400:
                    size_category = "small"
                else:
                    size_category = "standard"
            else:
                page_width = 0
                page_height = 0
                orientation = "unknown"
                size_category = "unknown"

            return {
                "page_count": page_count,
                "page_width": page_width,
                "page_height": page_height,
                "orientation": orientation,
                "size_category": size_category,
                "is_valid": True
            }

    except Exception as e:
        return {
            "page_count": 0,
            "page_width": 0,
            "page_height": 0,
            "orientation": "unknown",
            "size_category": "unknown",
            "is_valid": False,
            "error": str(e)
        }


def is_pdf_scanned(file_path: str) -> bool:
    """
    Check if PDF is likely scanned (contains mostly images)
    """
    try:
        with fitz.open(file_path) as doc:
            text_ratio_threshold = 0.1  # If less than 10% of pages have text, consider it scanned

            pages_with_text = 0
            total_pages = len(doc)

            for page_num in range(total_pages):
                page = doc[page_num]
                text = page.get_text()
                if text.strip():  # If page has any text
                    pages_with_text += 1

            text_ratio = pages_with_text / total_pages if total_pages > 0 else 0
            return text_ratio < text_ratio_threshold

    except Exception:
        return False


def get_pdf_metadata(file_path: str) -> Dict[str, Any]:
    """
    Extract PDF metadata
    """
    try:
        with fitz.open(file_path) as doc:
            metadata = doc.metadata
            return {
                "title": metadata.get("title", ""),
                "author": metadata.get("author", ""),
                "subject": metadata.get("subject", ""),
                "keywords": metadata.get("keywords", ""),
                "creator": metadata.get("creator", ""),
                "producer": metadata.get("producer", ""),
                "creation_date": metadata.get("creationDate", ""),
                "modification_date": metadata.get("modDate", ""),
                "page_count": len(doc)
            }
    except Exception as e:
        return {"error": str(e)}


def has_text_layer(file_path: str) -> bool:
    """
    Check if PDF has a text layer (not just scanned images)
    """
    try:
        with fitz.open(file_path) as doc:
            for page_num in range(min(3, len(doc))):  # Check first 3 pages
                page = doc[page_num]
                text = page.get_text()
                if text.strip():  # If page has any text
                    return True
            return False
    except Exception:
        return False


def detect_pdf_type(page: fitz.Page) -> Dict[str, Any]:
    """
    Detect the type of PDF content on a page
    """
    try:
        # Get text content
        text = page.get_text()
        has_text = bool(text.strip())

        # Get images
        image_list = page.get_images()
        has_images = len(image_list) > 0

        # Analyze content
        if has_text and not has_images:
            pdf_type = "text"
        elif has_images and not has_text:
            pdf_type = "image"
        elif has_text and has_images:
            pdf_type = "mixed"
        else:
            pdf_type = "unknown"

        return {
            "type": pdf_type,
            "has_text": has_text,
            "has_images": has_images,
            "text_length": len(text),
            "image_count": len(image_list)
        }
    except Exception as e:
        return {
            "type": "error",
            "error": str(e)
        }