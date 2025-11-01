"""
PDF Merge Core Logic
Handles the low-level PDF merging operations
"""

import os
import tempfile
from typing import Dict, List, Optional, Any

import fitz  # type: ignore

from ..exceptions.pdf_exceptions import PDFMergeError
from ..models.merge_options import MergeOptions
from ..models.pdf_file import PDFFile
from ..utils.ocr_utils import get_safe_page_number_position
from ..utils.font_utils import ProjectFontManager


def create_bookmarks(pdf_doc, file_info: List[Dict[str, Any]], toc_page_count: int = 0):
    """
    Create bookmarks/table of contents for merged PDF
    UPDATED: Account for TOC pages in bookmark positions

    file_info: [{'name': 'doc1.pdf', 'start_page': 0, 'page_count': 10}, ...]
    toc_page_count: Number of TOC pages at the beginning (default: 0)
    """
    toc = []

    for info in file_info:
        # Calculate the bookmark position accounting for TOC pages
        # Add toc_page_count to skip over TOC pages
        bookmark_page = info['start_page'] + 1 ###+ toc_page_count

        # Create bookmark entry: [level, title, page_number]
        toc.append([1, info['name'], bookmark_page])

    pdf_doc.set_toc(toc)
    print(f"✓ Bookmarks created with TOC offset: +{toc_page_count} pages")


class PDFMerger:
    """Handles PDF merging operations using exact app.py logic"""

    def __init__(self, options: Optional[MergeOptions] = None):
        self.options = options or MergeOptions()
        # Initialize fonts
        ProjectFontManager.initialize_fonts()

    def merge(self, files: List[PDFFile]) -> fitz.Document:
        """
        Merge multiple PDF files into one using EXACT app.py logic
        """
        output_pdf = fitz.open()
        source_pdfs = []  # Keep track of all opened source PDFs

        try:
            print("=" * 80)
            print("PDF MERGE CORE PROCESS - EXACT APP.PY BOOKMARK LOGIC")
            print("=" * 80)
            print(f"Add headers: {self.options.add_headers}")
            print(f"Add bookmarks: {self.options.add_bookmarks}")
            print(f"Add table of contents: {self.options.add_toc}")
            print(f"Starting page number: {self.options.page_start}")
            print(f"Using font: {ProjectFontManager.get_default_font()}")
            print()

            total_page_number = self.options.page_start
            total_pages_processed = 0
            file_info = []  # For bookmarks - EXACT app.py structure
            current_page = 0  # Track current page in output PDF (0-indexed)
            toc_page_count = 0  # Track number of TOC pages

            # Check if all headers are empty (like app.py)
            if self.options.add_headers:
                all_headers_empty = all(
                    not file.header_line1.strip() and not file.header_line2.strip()
                    for file in files
                )
                if all_headers_empty:
                    print("📝 Note: All headers are empty - merging as-is (simple merge)")
                    self.options.add_headers = False

            # Create TOC page if requested (must be before adding content)
            if self.options.add_toc and len(files) > 1:
                print("📑 Creating Table of Contents page...")
                toc_page_info = self._create_toc_page(output_pdf, files)
                toc_page_count = toc_page_info['page_count']
                current_page += toc_page_count  # TOC pages count in PDF structure
                # DON'T increment total_page_number - TOC doesn't get page numbers
                print(f"  - Added {toc_page_count} TOC page(s) (no headers or page numbers)")

            for idx, pdf_file in enumerate(files):
                file_path = pdf_file.path

                if not os.path.exists(file_path):
                    print(f"⚠ Warning: File not found - {file_path}")
                    continue

                source_pdf = fitz.open(file_path)
                source_pdfs.append(source_pdf)
                page_count = len(source_pdf)

                # Store starting page for bookmarks - EXACT app.py logic
                # This is 0-indexed position in the output PDF
                start_page_idx = current_page

                print(f"Processing PDF {idx + 1}: {pdf_file.name} ({page_count} pages)")
                print(f"  - Start page in output: {start_page_idx} (0-indexed)")
                print(f"  - Content starts at page number: {total_page_number}")
                print(f"  - Bookmark will point to: {start_page_idx + 1} (1-indexed)")

                # Process each page
                for page_num in range(page_count):
                    if self.options.add_headers:
                        self._process_page_with_headers(
                            output_pdf,
                            source_pdf,
                            page_num,
                            pdf_file,
                            total_page_number,
                        )
                    else:
                        self._copy_page_directly(
                            output_pdf,
                            source_pdf,
                            page_num,
                            total_page_number,
                        )

                    total_page_number += 1  # Only increment for content pages
                    current_page += 1  # Increment for all pages (TOC + content)

                # Track file info for bookmarks - EXACT app.py structure
                file_info.append({
                    'name': pdf_file.name,
                    'start_page': start_page_idx,  # 0-indexed start position
                    'page_count': page_count
                })

                total_pages_processed += page_count

            # Add bookmarks if requested - EXACT app.py logic
            if self.options.add_bookmarks and len(file_info) > 1:
                print(f"\nCreating bookmarks for {len(file_info)} files:")
                for info in file_info:
                    bookmark_target = info['start_page'] + 1 + toc_page_count
                    print(f"  - '{info['name']}' -> page {bookmark_target}")

                # Pass the TOC page count to bookmarks
                create_bookmarks(output_pdf, file_info, toc_page_count)
                print("✓ Bookmarks created with TOC adjustment")

            if total_pages_processed > 0:
                print("\n" + "=" * 80)
                print(f"✓ Merge complete!")
                print(f"✓ Processed {len(files)} PDF files")
                print(f"✓ Total {total_pages_processed} content pages")
                print(f"✓ Output PDF has {len(output_pdf)} total pages")
                if self.options.add_toc:
                    print(f"✓ Table of Contents added ({toc_page_count} page(s))")
                    print(f"✓ Use bookmarks for navigation")
                print("=" * 80)

            return output_pdf

        except Exception as e:
            try:
                output_pdf.close()
            except:
                pass
            raise PDFMergeError(f"Failed to merge PDFs: {str(e)}")
        finally:
            for source_pdf in source_pdfs:
                try:
                    source_pdf.close()
                except:
                    pass

    def _create_toc_page(self, output_pdf: fitz.Document, files: List[PDFFile]) -> Dict[str, Any]:
        """
        Create a table of contents page (without clickable links)
        Returns information about the TOC page for reference
        """
        # Create a new page for TOC - NO headers or page numbers
        toc_page = output_pdf.new_page(-1, width=612, height=792)

        # Add title
        title = "Table of Contents"
        title_font_size = 18
        title_y = 50

        ProjectFontManager.insert_text_with_font(
            toc_page, (50, title_y),
            title,
            fontsize=title_font_size,
            variant='regular',
            color=(0, 0, 0)
        )

        # Add separator line under title
        toc_page.draw_line(
            (50, title_y + 10),
            (562, title_y + 10),
            width=1,
            color=(0, 0, 0)
        )

        # Calculate starting positions for TOC entries
        entry_start_y = title_y + 40
        line_height = 20
        current_y = entry_start_y

        # Track CONTENT page numbers
        #current_content_page = 2  # TOC is page 1, content starts at page 2
        current_content_page = 1  # Don't count TOC , content starts at page 1

        # Calculate total pages for each document
        doc_page_counts = []
        for pdf_file in files:
            try:
                with fitz.open(pdf_file.path) as doc:
                    doc_page_counts.append(len(doc))
            except:
                doc_page_counts.append(0)

        # Add each file to TOC (without links)
        for idx, pdf_file in enumerate(files):
            if current_y > 700:  # Prevent overflow
                break

            entry_text = f"{idx + 1}. {pdf_file.name}"
            page_text = f"Page {current_content_page}"

            # Add entry text (left-aligned)
            ProjectFontManager.insert_text_with_font(
                toc_page, (60, current_y),
                entry_text,
                fontsize=12,
                variant='regular',
                color=(0, 0, 0)
            )

            # Add page number (right-aligned)
            page_text_width = ProjectFontManager.get_text_length(page_text, fontsize=12, variant='regular')
            ProjectFontManager.insert_text_with_font(
                toc_page, (562 - page_text_width, current_y),
                page_text,
                fontsize=12,
                variant='regular',
                color=(0, 0, 0)
            )

            current_y += line_height
            current_content_page += doc_page_counts[idx]

        # Add note about navigation
        note_text = "Use PDF bookmarks (navigation pane) to jump to documents"
        note_y = 750
        note_font_size = 9
        note_width = ProjectFontManager.get_text_length(note_text, fontsize=note_font_size, variant='regular')
        note_x = (612 - note_width) / 2

        ProjectFontManager.insert_text_with_font(
            toc_page, (note_x, note_y),
            note_text,
            fontsize=note_font_size,
            variant='regular',
            color=(0.5, 0.5, 0.5)
        )

        print("✓ Table of Contents page created")
        print(f"  - TOC references content pages starting at Page 2")
        print(f"  - Use bookmarks for navigation")

        return {
            'page_count': 1,
            'entries_created': min(len(files), int((700 - entry_start_y) / line_height))
        }

    def _process_page_with_headers(
            self,
            output_pdf: fitz.Document,
            source_pdf: fitz.Document,
            page_num: int,
            pdf_file: PDFFile,
            page_number: int,
    ):
        """Process and add page with headers"""
        new_page = output_pdf.new_page(-1, width=612, height=792)  # Use -1 to append

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
            new_page = output_pdf[-1]  # Get the last page we just added
            self._add_page_number_only(new_page, page_number)

    def _add_header_footer(self, page: fitz.Page, pdf_file: PDFFile, page_number: int):
        """Add headers and footers to page using individual file headers"""
        header_notes = [pdf_file.header_line1, pdf_file.header_line2]
        page_width = page.rect.width
        page_height = page.rect.height

        margin = 30
        font_size = 10

        # Add header text
        header_y = 25
        line_height = 12

        if header_notes[0]:
            ProjectFontManager.insert_text_with_font(
                page, (margin, header_y),
                header_notes[0],
                fontsize=font_size,
                variant='regular'
            )

        if header_notes[1]:
            ProjectFontManager.insert_text_with_font(
                page, (margin, header_y + line_height),
                header_notes[1],
                fontsize=font_size,
                variant='regular'
            )

        # Add page number
        if self.options.add_page_numbers:
            self._add_page_number_only(page, page_number)

        # Add header separator only if headers are present
        if header_notes[0] or header_notes[1]:
            header_line_y = 45
            page.draw_line(
                (margin, header_line_y),
                (page_width - margin, header_line_y),
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
            x = page_width / 2
            y = 25
        elif safe_position == "bottom-center":
            x = page_width / 2
            y = page_height - 25
        elif safe_position == "top-right":
            x = page_width - 50
            y = 25
        elif safe_position == "bottom-right":
            x = page_width - 50
            y = page_height - 25
        else:
            x = page_width / 2
            y = 25

        # Add semi-transparent background
        bg_padding = 5
        text_width = ProjectFontManager.get_text_length(page_text, fontsize=self.options.page_number_font_size,
                                                        variant='regular')
        bg_rect = fitz.Rect(
            x - text_width / 2 - bg_padding,
            y - self.options.page_number_font_size - bg_padding,
            x + text_width / 2 + bg_padding,
            y + bg_padding,
        )
        page.draw_rect(bg_rect, color=(1, 1, 1), fill=(1, 1, 1), fill_opacity=0.7)

        # Insert page number
        ProjectFontManager.insert_text_with_font(
            page, (x - text_width / 2, y),
            page_text,
            fontsize=self.options.page_number_font_size,
            variant='regular'
        )


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
