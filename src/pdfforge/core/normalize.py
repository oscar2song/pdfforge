"""
PDF Normalization Core Logic
Handles PDF page size normalization and OCR
"""

from typing import Optional

import fitz  # type: ignore  # type: ignore  # type: ignore

from ..exceptions.pdf_exceptions import PDFNormalizationError
from ..models.normalize_options import NormalizeOptions
from ..models.pdf_file import PDFFile
from ..utils.ocr_utils import add_text_layer_ocr, perform_ocr_on_page
from ..utils.pdf_utils import has_text_layer


class PDFNormalizer:
    """Handles PDF normalization operations"""

    def __init__(self, options: Optional[NormalizeOptions] = None):
        self.options = options or NormalizeOptions()

    def normalize(self, pdf_file: PDFFile) -> fitz.Document:
        """
        Normalize PDF to target page size

        Args:
            pdf_file: PDFFile object to normalize

        Returns:
            fitz.Document: Normalized PDF document

        Raises:
            PDFNormalizationError: If normalization fails
        """
        try:
            source_doc = fitz.open(pdf_file.path)
            output_doc = fitz.open()

            print("=" * 80)
            print("PDF NORMALIZATION CORE PROCESS")
            print("=" * 80)
            print(f"Input: {pdf_file.name}")
            print(f"Target size: {self.options.page_size} " + f"{self.options.orientation}")

            # Get target dimensions
            target_width, target_height = self._get_target_dimensions()

            for page_num in range(len(source_doc)):
                source_page = source_doc[page_num]
                new_page = output_doc.new_page(width=target_width, height=target_height)

                self._process_page(source_page, new_page, target_width, target_height)

                # Add OCR if requested
                if self.options.add_ocr:
                    self._add_ocr_to_page(source_page, new_page)

            source_doc.close()
            return output_doc

        except Exception as e:
            raise PDFNormalizationError(f"Failed to normalize PDF: {str(e)}")

    def _get_target_dimensions(self) -> tuple:
        """Get target page dimensions based on options"""
        if self.options.page_size == "custom":
            target_width = self.options.custom_width
            target_height = self.options.custom_height
            if self.options.orientation.lower() == "landscape":
                target_width, target_height = target_height, target_width
        else:
            from config import Config

            page_size_key = f"{self.options.page_size.lower()}-" f"{self.options.orientation.lower()}"
            if page_size_key in Config.PAGE_SIZES:
                target_width, target_height = Config.PAGE_SIZES[page_size_key]
            else:
                target_width, target_height = Config.PAGE_SIZES["letter"]

        return target_width, target_height

    def _process_page(
        self,
        source_page: fitz.Page,
        new_page: fitz.Page,
        target_width: float,
        target_height: float,
    ):
        """Process individual page for normalization"""
        original_rotation = source_page.rotation
        page_rect = source_page.rect

        if original_rotation != 0:
            source_page.set_rotation(0)
            derotated_rect = source_page.rect
        else:
            derotated_rect = page_rect

        # Calculate scaling with conservative margins
        top_margin = 25 if self.options.add_header_footer_space else 15
        bottom_margin = 20 if self.options.add_header_footer_space else 15
        side_margin = 20

        available_width = target_width - 2 * side_margin
        available_height = target_height - top_margin - bottom_margin

        if original_rotation in [90, 270]:
            content_width = derotated_rect.height
            content_height = derotated_rect.width

            scale_x = available_width / content_width
            scale_y = available_height / content_height
            scale = min(scale_x, scale_y)

            scaled_width = content_width * scale
            scaled_height = content_height * scale
            x_offset = side_margin + (available_width - scaled_width) / 2
            y_offset = top_margin + (available_height - scaled_height) / 2

            target_rect = fitz.Rect(
                x_offset,
                y_offset,
                x_offset + scaled_width,
                y_offset + scaled_height,
            )
            new_page.show_pdf_page(target_rect, source_page.parent, source_page.number, rotate=90)

        else:
            scale_x = available_width / derotated_rect.width
            scale_y = available_height / derotated_rect.height
            scale = min(scale_x, scale_y)

            scaled_width = derotated_rect.width * scale
            scaled_height = derotated_rect.height * scale
            x_offset = side_margin + (available_width - scaled_width) / 2
            y_offset = top_margin + (available_height - scaled_height) / 2

            target_rect = fitz.Rect(
                x_offset,
                y_offset,
                x_offset + scaled_width,
                y_offset + scaled_height,
            )
            new_page.show_pdf_page(target_rect, source_page.parent, source_page.number)

    def _add_ocr_to_page(self, source_page: fitz.Page, new_page: fitz.Page):
        """Add OCR text layer to page"""
        if not has_text_layer(source_page) or self.options.force_ocr:
            ocr_text = perform_ocr_on_page(source_page)
            if ocr_text:
                add_text_layer_ocr(new_page, ocr_text)
