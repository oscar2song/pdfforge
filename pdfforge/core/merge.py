"""
PDF Merge Core Logic
Handles the low-level PDF merging operations
"""

import os
import tempfile
from typing import Dict, List, Optional

import fitz  # type: ignore

from ..exceptions.pdf_exceptions import PDFMergeError
from ..models.merge_options import MergeOptions
from ..models.pdf_file import PDFFile
from ..utils.ocr_utils import get_safe_page_number_position


class PDFMerger:
    """Handles PDF merging operations"""

    def __init__(self, options: Optional[MergeOptions] = None):
        self.options = options or MergeOptions()

    def merge(self, files: List[PDFFile]) -> fitz.Document:
        """
        Merge multiple PDF files into one

        Args:
            files: List of PDFFile objects to merge

        Returns:
            fitz.Document: Merged PDF document

        Raises:
            PDFMergeError: If merge fails
        """
        output_pdf = fitz.open()
        source_pdfs = []  # Keep track of all opened source PDFs

        try:
            print("=" * 80)
            print("PDF MERGE CORE PROCESS")
            print("=" * 80)

            total_page_number = self.options.page_start

            for pdf_file in files:
                print(f"Processing: {pdf_file.name}")
                try:
                    source_pdf = fitz.open(pdf_file.path)
                    source_pdfs.append(source_pdf)  # Keep reference
                    page_count = len(source_pdf)

                    self._add_file_to_output(output_pdf, source_pdf, pdf_file, total_page_number)
                    total_page_number += page_count

                except Exception as e:
                    print(f"❌ Error processing {pdf_file.name}: {str(e)}")
                    # Close this specific source PDF if it failed
                    try:
                        source_pdf.close()
                    except:
                        pass
                    continue

            if self.options.add_bookmarks and len(files) > 1:
                self._create_bookmarks(output_pdf, files)

            return output_pdf

        except Exception as e:
            # Close output PDF on error
            try:
                output_pdf.close()
            except:
                pass
            raise PDFMergeError(f"Failed to merge PDFs: {str(e)}")
        finally:
            # Always close all source PDFs
            for source_pdf in source_pdfs:
                try:
                    source_pdf.close()
                except:
                    pass

    def _add_file_to_output(self, output_pdf: fitz.Document, source_pdf: fitz.Document, pdf_file: PDFFile,
                            start_page: int) -> None:
        """Add a single PDF file to the output document"""
        for page_num in range(len(source_pdf)):
            current_page_number = start_page + page_num

            if self.options.add_headers:
                self._process_page_with_headers(
                    output_pdf,
                    source_pdf,
                    page_num,
                    pdf_file,
                    current_page_number,
                )
            else:
                self._copy_page_directly(output_pdf, source_pdf, page_num, current_page_number)

    def _process_page_with_headers(
            self,
            output_pdf: fitz.Document,
            source_pdf: fitz.Document,
            page_num: int,
            pdf_file: PDFFile,
            page_number: int,
    ):
        """Process and add page with headers"""
        new_page = output_pdf.new_page(width=612, height=792)  # Letter size

        src_page = source_pdf[page_num]
        src_rect = src_page.rect

        # Calculate scaling
        margin = 30
        header_space = 50
        footer_space = 15 if self.options.add_footer_line else 5

        available_width = 612 - 2 * margin
        available_height = 792 - header_space - footer_space

        scale_x = available_width / src_rect.width
        scale_y = available_height / src_rect.height
        scale = min(scale_x, scale_y, self.options.scale_factor)

        scaled_width = src_rect.width * scale
        scaled_height = src_rect.height * scale

        x_offset = (612 - scaled_width) / 2
        y_offset = header_space + (available_height - scaled_height) / 2

        target_rect = fitz.Rect(
            x_offset,
            y_offset,
            x_offset + scaled_width,
            y_offset + scaled_height,
        )

        # Insert source page content
        new_page.show_pdf_page(target_rect, source_pdf, page_num)

        # Add headers and page numbers
        self._add_header_footer(new_page, pdf_file, page_number)

    def _copy_page_directly(
            self,
            output_pdf: fitz.Document,
            source_pdf: fitz.Document,
            page_num: int,
            page_number: int,
    ):
        """Copy page without modifications"""
        output_pdf.insert_pdf(source_pdf, from_page=page_num, to_page=page_num)

        if self.options.add_page_numbers:
            new_page = output_pdf[-1]
            self._add_page_number_only(new_page, page_number)

    def _add_header_footer(self, page: fitz.Page, pdf_file: PDFFile, page_number: int):
        """Add headers and footers to page"""
        header_notes = [pdf_file.header_line1, pdf_file.header_line2]
        page_width = page.rect.width
        page_height = page.rect.height

        margin = 30
        font_size = 10

        # Add header text
        header_y = 25
        line_height = 12

        if header_notes[0]:
            page.insert_text(
                (margin, header_y),
                header_notes[0],
                fontsize=font_size,
                fontname="helv",
            )

        if header_notes[1]:
            page.insert_text(
                (margin, header_y + line_height),
                header_notes[1],
                fontsize=font_size,
                fontname="helv",
            )

        # Add page number
        if self.options.add_page_numbers:
            self._add_page_number_only(page, page_number)

        # Add header separator
        if header_notes[0] or header_notes[1]:
            header_line_y = 45
            page.draw_line(
                (margin, header_line_y),
                (page_width - margin, header_line_y),
                width=0.5,
            )

        # Add footer line if requested
        if self.options.add_footer_line:
            footer_line_y = page_height - 25
            page.draw_line(
                (margin, footer_line_y),
                (page_width - margin, footer_line_y),
                width=0.5,
            )

    def _add_page_number_only(self, page: fitz.Page, page_number: int):
        """Add only page number with smart positioning"""
        page_text = f"{page_number}"
        page_width = page.rect.width
        page_height = page.rect.height

        # Get safe position
        safe_position = get_safe_page_number_position(
            page,
            self.options.page_number_position,
            self.options.page_number_font_size,
        )

        # Calculate coordinates
        if safe_position == "top-center":
            x = (
                        page_width
                        - fitz.get_text_length(
                    page_text,
                    fontsize=self.options.page_number_font_size,
                    fontname="helv",
                )
                ) / 2
            y = 25
        elif safe_position == "bottom-center":
            x = (
                        page_width
                        - fitz.get_text_length(
                    page_text,
                    fontsize=self.options.page_number_font_size,
                    fontname="helv",
                )
                ) / 2
            y = page_height - 25
        elif safe_position == "top-right":
            x = (
                    page_width
                    - fitz.get_text_length(
                page_text,
                fontsize=self.options.page_number_font_size,
                fontname="helv",
            )
                    - 25
            )
            y = 25
        elif safe_position == "bottom-right":
            x = (
                    page_width
                    - fitz.get_text_length(
                page_text,
                fontsize=self.options.page_number_font_size,
                fontname="helv",
            )
                    - 25
            )
            y = page_height - 25
        else:
            x = (
                        page_width
                        - fitz.get_text_length(
                    page_text,
                    fontsize=self.options.page_number_font_size,
                    fontname="helv",
                )
                ) / 2
            y = 25

        # Add semi-transparent background
        bg_padding = 5
        text_width = fitz.get_text_length(
            page_text,
            fontsize=self.options.page_number_font_size,
            fontname="helv",
        )
        bg_rect = fitz.Rect(
            x - bg_padding,
            y - self.options.page_number_font_size - bg_padding,
            x + text_width + bg_padding,
            y + bg_padding,
        )
        page.draw_rect(bg_rect, color=(1, 1, 1), fill=(1, 1, 1), fill_opacity=0.7)

        # Insert page number
        page.insert_text(
            (x, y),
            page_text,
            fontsize=self.options.page_number_font_size,
            fontname="helv",
        )

    def _create_bookmarks(self, output_pdf: fitz.Document, files: List[PDFFile]):
        """Create bookmarks for merged documents"""
        toc = []
        current_page = 0

        for pdf_file in files:
            # Get actual page count by opening the file temporarily
            try:
                with fitz.open(pdf_file.path) as doc:
                    page_count = len(doc)
                    toc.append([1, pdf_file.name_without_extension, current_page])
                    current_page += page_count
            except:
                # Fallback if we can't open the file
                toc.append([1, pdf_file.name_without_extension, current_page])
                current_page += 1  # Assume at least 1 page

        output_pdf.set_toc(toc)


# Standalone function for backward compatibility
def merge_pdfs_enhanced(file_configs: List[Dict], options: Optional[Dict] = None) -> str:
    """Legacy function wrapper for backward compatibility"""
    # Convert to new models
    pdf_files = [PDFFile.from_dict(config) for config in file_configs]
    merge_options = MergeOptions.from_dict(options or {})

    # Use new class
    merger = PDFMerger(merge_options)
    merged_pdf = merger.merge(pdf_files)

    # Save to temporary file
    output_filename = "merged.pdf"
    if merge_options.output_filename:
        output_filename = merge_options.output_filename
        if not output_filename.endswith(".pdf"):
            output_filename += ".pdf"

    output_path = os.path.join(tempfile.gettempdir(), output_filename)
    merged_pdf.save(output_path, garbage=4, deflate=True)
    merged_pdf.close()

    return output_path
