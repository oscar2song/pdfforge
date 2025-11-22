"""
PDF Merge Core Logic with Two-Pass Approach and Separate Pagination
"""

import os
import tempfile
from typing import Any, Dict, List, Optional

import fitz  # type: ignore

from ..exceptions.pdf_exceptions import PDFMergeError
from ..models.merge_options import MergeOptions
from ..models.pdf_file import PDFFile
from ..utils.font_utils import ProjectFontManager
from ..utils.ocr_utils import get_safe_page_number_position
from ..utils.pdf_utils import detect_pdf_type


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
        bookmark_page = info["start_page"] + 1 + toc_page_count

        # Create bookmark entry: [level, title, page_number]
        toc.append([1, info["name"], bookmark_page])

    pdf_doc.set_toc(toc)
    print(f"✓ Bookmarks created with TOC offset: +{toc_page_count} pages")


class PDFMerger:
    """Handles PDF merging operations with Two-Pass Approach and Separate Pagination"""

    def __init__(self, options: Optional[MergeOptions] = None):
        self.options = options or MergeOptions()
        # Initialize fonts
        ProjectFontManager.initialize_fonts()

    def merge(self, files: List[PDFFile]) -> fitz.Document:
        """
        Merge multiple PDF files using Two-Pass Approach:
        Pass 1: Create all content pages and collect page information
        Pass 2: Add TOC with Roman numerals and working links
        """
        output_pdf = fitz.open()
        source_pdfs = []

        # Get target page dimensions from options
        page_width, page_height = self.options.get_page_dimensions()

        # Auto-detect page size if requested
        if self.options.target_page_size == "auto" and files:
            page_width, page_height = self._detect_common_page_size(files)

        try:
            print("=" * 80)
            print("PDF MERGE - TWO-PASS APPROACH WITH SEPARATE PAGINATION")
            print("=" * 80)
            print(f"Target page size: {page_width:.0f} x {page_height:.0f} pts")
            print(f"Add headers: {self.options.add_headers}")
            print(f"Add bookmarks: {self.options.add_bookmarks}")
            print(f"Add table of contents: {self.options.add_toc}")
            print(f"Starting page number: {self.options.page_start}")
            print(f"Page number position: {self.options.page_number_position}")
            print(f"Using font: {ProjectFontManager.get_default_font()}")
            print()

            # === PASS 1: CREATE ALL CONTENT PAGES ===
            print("=== PASS 1: Creating Content Pages ===")

            content_pages_info: List[Dict[str, Any]] = []
            file_info: List[Dict[str, Any]] = []
            current_content_page_index = 0

            # First, create all content pages without TOC
            for idx, pdf_file in enumerate(files):
                file_path = pdf_file.path

                if not os.path.exists(file_path):
                    print(f"⚠ Warning: File not found - {file_path}")
                    continue

                source_pdf = fitz.open(file_path)
                source_pdfs.append(source_pdf)
                page_count = len(source_pdf)

                file_start_index = current_content_page_index

                print(f"Processing PDF {idx + 1}: {pdf_file.name} ({page_count} pages)")
                print(f"  - Start position in output: {file_start_index} (0-indexed)")

                for page_num in range(page_count):
                    page_info = {
                        "source_pdf": source_pdf,
                        "page_num": page_num,
                        "pdf_file": pdf_file,
                        "content_page_number": self.options.page_start + len(content_pages_info),
                        "output_index": current_content_page_index,
                        "file_name": pdf_file.name,
                    }

                    if self.options.add_headers:
                        self._process_page_with_headers(
                            output_pdf,
                            source_pdf,
                            page_num,
                            pdf_file,
                            page_info["content_page_number"],
                            page_width,  # ← ADDED
                            page_height,  # ← ADDED
                        )
                    else:
                        self._copy_page_directly(
                            output_pdf,
                            source_pdf,
                            page_num,
                            page_info["content_page_number"],
                            page_width,  # ← ADDED
                            page_height,  # ← ADDED
                        )

                    content_pages_info.append(page_info)
                    current_content_page_index += 1

                file_info.append({"name": pdf_file.name, "start_page": file_start_index, "page_count": page_count})

            # === PASS 2: ADD TOC WITH ROMAN NUMERALS AND WORKING LINKS ===
            print("\n=== PASS 2: Adding TOC with Roman Numerals ===")

            toc_page_count = 0
            if self.options.add_toc and len(files) > 1:
                toc_page_count = self._create_toc_with_links(
                    output_pdf, files, content_pages_info, page_width, page_height  # ← ADDED  # ← ADDED
                )
                print(f"✓ Added {toc_page_count} TOC page(s) with Roman numerals")

            # === UPDATE PAGE NUMBERS WITH SEPARATE PAGINATION ===
            print("\n=== Applying Separate Pagination ===")
            self._apply_separate_pagination(output_pdf, toc_page_count, content_pages_info)

            # === ADD BOOKMARKS ===
            if self.options.add_bookmarks and len(file_info) > 1:
                print(f"\nCreating bookmarks for {len(file_info)} files:")
                for info in file_info:
                    bookmark_target = info["start_page"] + 1 + toc_page_count
                    print(f"  - '{info['name']}' -> page {bookmark_target}")

                create_bookmarks(output_pdf, file_info, toc_page_count)
                print("✓ Bookmarks created with TOC adjustment")

            # Final summary
            print("\n" + "=" * 80)
            print("✓ Merge complete!")
            print(f"✓ Processed {len(files)} PDF files")
            print(f"✓ Total {len(content_pages_info)} content pages")
            print(f"✓ Output PDF has {len(output_pdf)} total pages")
            if self.options.add_toc:
                print(f"✓ Table of Contents: {toc_page_count} page(s) (Roman numerals)")
                print(f"✓ Content pages: {len(content_pages_info)} pages (Arabic numerals)")
                print("✓ TOC links are fully functional")
            print("=" * 80)

            return output_pdf

        except Exception as e:
            try:
                output_pdf.close()
            except (AttributeError, OSError, ValueError):
                pass
            raise PDFMergeError(f"Failed to merge PDFs: {str(e)}")
        finally:
            for source_pdf in source_pdfs:
                try:
                    source_pdf.close()
                except (AttributeError, OSError, ValueError):
                    pass

    def _detect_common_page_size(self, files: List[PDFFile]) -> tuple[float, float]:
        """
        Auto-detect the most common page size from source files
        Returns: (width, height) in points
        """
        from collections import Counter

        page_sizes = []

        for pdf_file in files[:5]:  # Check first 5 files
            if not os.path.exists(pdf_file.path):
                continue
            try:
                doc = fitz.open(pdf_file.path)
                if len(doc) > 0:
                    rect = doc[0].rect
                    # Round to nearest 10 to group similar sizes
                    width = round(rect.width / 10) * 10
                    height = round(rect.height / 10) * 10
                    page_sizes.append((width, height))
                doc.close()
            except (AttributeError, OSError, ValueError):
                continue

        if page_sizes:
            # Return most common page size
            most_common = Counter(page_sizes).most_common(1)[0][0]
            print(f"📐 Auto-detected page size: {most_common[0]:.0f} x {most_common[1]:.0f} pts")
            return most_common

        # Default to letter size
        return (612, 792)

    def _create_toc_with_links(
        self,
        output_pdf: fitz.Document,
        files: List[PDFFile],
        content_pages_info: List[Dict],
        page_width: float,
        page_height: float,
    ) -> int:
        """Create TOC with Roman numerals - DYNAMIC PAGE SIZE"""
        toc_page = output_pdf.new_page(0, width=page_width, height=page_height)
        """
        Create TOC with Roman numerals and working links to content pages
        Returns number of TOC pages created
        """
        toc_pages = [toc_page]

        # Calculate content page starts for each file
        file_page_starts = {}
        current_file = None
        for page_info in content_pages_info:
            if page_info["file_name"] != current_file:
                file_page_starts[page_info["file_name"]] = page_info["content_page_number"]
                current_file = page_info["file_name"]

        # Add title - CENTER ALIGNED with top margin
        title = "Table of Contents"
        title_font_size = 18
        title_y = 80  # Increased from 50 for better top margin

        title_width = ProjectFontManager.get_text_length(title, fontsize=title_font_size, variant="regular")
        title_x = (612 - title_width) / 2

        ProjectFontManager.insert_text_with_font(
            toc_page, (title_x, title_y), title, fontsize=title_font_size, variant="regular", color=(0, 0, 0)
        )

        # Add separator line under title
        toc_page.draw_line((50, title_y + 10), (562, title_y + 10), width=1, color=(0, 0, 0))

        # Add TOC entries with working links
        entry_start_y = title_y + 40
        line_height = 20
        current_y = entry_start_y

        for idx, pdf_file in enumerate(files):
            if current_y > 700:  # Need new TOC page
                toc_page = output_pdf.new_page(len(toc_pages), width=612, height=792)
                toc_pages.append(toc_page)
                current_y = entry_start_y

            entry_text = f"{idx + 1}. {pdf_file.name}"

            # Get the starting page number for this file
            start_page = file_page_starts.get(pdf_file.name, 1)
            page_text = f"{start_page}"

            # Add entry text (left-aligned)
            ProjectFontManager.insert_text_with_font(
                toc_page, (60, current_y), entry_text, fontsize=12, variant="regular", color=(0, 0, 0)
            )

            # Add page number (LEFT ALIGNED at consistent position)
            page_number_x = 500
            ProjectFontManager.insert_text_with_font(
                toc_page, (page_number_x, current_y), page_text, fontsize=12, variant="regular", color=(0, 0, 0)
            )

            # === CREATE CLICKABLE LINK ===
            # Find the target page index in the output PDF
            # TOC pages are at the beginning, so content starts after TOC
            target_page_index = None
            for page_info in content_pages_info:
                if page_info["file_name"] == pdf_file.name:
                    target_page_index = page_info["output_index"] + len(toc_pages)
                    break

            if target_page_index is not None:
                # Create clickable area for the entire entry
                link_rect = fitz.Rect(50, current_y - 8, 562, current_y + 12)
                toc_page.insert_link(
                    {
                        "kind": fitz.LINK_GOTO,
                        "from": link_rect,
                        "page": target_page_index,
                        "to": fitz.Point(0, 50),  # Start at top of page
                    }
                )

            current_y += line_height

        # Add Roman numerals to TOC pages using the same position as content pages
        roman_numerals = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
        for i, page in enumerate(toc_pages):
            roman_numeral = roman_numerals[i] if i < len(roman_numerals) else str(i + 1)

            # Use the same page number position as content pages
            self._add_roman_page_number(page, roman_numeral)

        print(f"✓ Created {len(toc_pages)} TOC page(s) with working links")
        print(
            f"✓ TOC uses Roman numerals: "
            f"{[roman_numerals[i] if i < len(roman_numerals) else str(i + 1) for i in range(len(toc_pages))]}"
        )
        print(f"✓ TOC page numbers use same position as content: {self.options.page_number_position}")

        return len(toc_pages)

    def _add_roman_page_number(self, page: fitz.Page, page_number: str):
        """Add Roman numeral page number using the same position as content pages"""
        page_text = page_number
        page_width = page.rect.width
        page_height = page.rect.height

        # Use the same position setting as content pages
        safe_position = self.options.page_number_position

        # Calculate coordinates based on UI setting
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
        else:  # Default to top-center
            x = page_width / 2
            y = 25

        # Add semi-transparent background (same as content pages)
        bg_padding = 5
        text_width = ProjectFontManager.get_text_length(
            page_text, fontsize=self.options.page_number_font_size, variant="regular"
        )

        # Create background rectangle based on position
        if safe_position in ["top-center", "bottom-center"]:
            bg_rect = fitz.Rect(
                x - text_width / 2 - bg_padding,
                y - self.options.page_number_font_size - bg_padding,
                x + text_width / 2 + bg_padding,
                y + bg_padding,
            )
        else:  # right-aligned positions
            bg_rect = fitz.Rect(
                x - text_width - bg_padding,
                y - self.options.page_number_font_size - bg_padding,
                x + bg_padding,
                y + bg_padding,
            )

        page.draw_rect(bg_rect, color=(1, 1, 1), fill=(1, 1, 1), fill_opacity=0.7)

        # Insert page number (aligned based on position)
        if safe_position in ["top-center", "bottom-center"]:
            ProjectFontManager.insert_text_with_font(
                page,
                (x - text_width / 2, y),
                page_text,
                fontsize=self.options.page_number_font_size,
                variant="regular",
                color=(0.3, 0.3, 0.3),  # Slightly lighter for TOC pages
            )
        else:  # right-aligned positions
            ProjectFontManager.insert_text_with_font(
                page,
                (x - text_width, y),
                page_text,
                fontsize=self.options.page_number_font_size,
                variant="regular",
                color=(0.3, 0.3, 0.3),  # Slightly lighter for TOC pages
            )

    def _apply_separate_pagination(
        self, output_pdf: fitz.Document, toc_page_count: int, content_pages_info: List[Dict]
    ):
        """
        Apply separate pagination: Roman for TOC, Arabic for content
        """
        # Add Arabic numerals to content pages
        for page_info in content_pages_info:
            # Calculate the actual page index in output PDF (after TOC pages)
            output_page_index = page_info["output_index"] + toc_page_count
            page = output_pdf[output_page_index]

            # Remove any existing page numbers
            self._clear_existing_page_number(page)

            # Add Arabic page number
            self._add_page_number_only(page, page_info["content_page_number"])

        print("✓ Applied separate pagination:")
        print("  - TOC pages: Roman numerals (I, II, III...)")
        print(
            f"  - Content pages: Arabic numerals "
            f"({self.options.page_start}-{self.options.page_start + len(content_pages_info) - 1})"
        )
        print(f"  - Page number position: {self.options.page_number_position}")

    def _clear_existing_page_number(self, page: fitz.Page):
        """Clear any existing page number from the page"""
        # This is a simplified implementation - you might need to adjust based on your page layout
        try:
            # Clear a reasonable area where page numbers might be
            page_height = page.rect.height
            clear_rect_top = fitz.Rect(250, 10, 362, 40)
            clear_rect_bottom = fitz.Rect(250, page_height - 40, 362, page_height - 10)

            page.draw_rect(clear_rect_top, color=(1, 1, 1), fill=(1, 1, 1))
            page.draw_rect(clear_rect_bottom, color=(1, 1, 1), fill=(1, 1, 1))
        except Exception:
            pass  # If clearing fails, continue anyway

    def _process_page_with_headers(
        self,
        output_pdf: fitz.Document,
        source_pdf: fitz.Document,
        page_num: int,
        pdf_file: PDFFile,
        page_number: int,
        page_width: float,
        page_height: float,
    ):
        """Process and add page with headers - ADJUSTED SPACING"""
        new_page = output_pdf.new_page(-1, width=page_width, height=page_height)

        src_page = source_pdf[page_num]
        src_rect = src_page.rect

        # Margins
        margin = min(25, page_width * 0.04)
        footer_space = 20

        # Detect PDF type and apply appropriate spacing
        pdf_type_info = detect_pdf_type(src_page)
        pdf_type = pdf_type_info["type"]
        # print(f"found pdf_type: {pdf_type}")
        has_headers = bool(pdf_file.header_line1 or pdf_file.header_line2)

        if not has_headers:
            header_space = 15
        elif pdf_type == "image":
            # Scanned image PDFs: tight spacing to maximize visible area
            header_space = 43  # Content starts immediately after separator at 43px
        else:
            # Scanned text PDFs: also use tight spacing to be close to separator
            header_space = 10  # Content starts immediately after separator at 43px

        available_width = page_width - 2 * margin
        available_height = page_height - header_space - footer_space

        scale_x = available_width / src_rect.width
        scale_y = available_height / src_rect.height
        scale = min(scale_x, scale_y, self.options.scale_factor)

        scaled_width = src_rect.width * scale
        scaled_height = src_rect.height * scale

        x_offset = (page_width - scaled_width) / 2
        y_offset = header_space  # Content starts based on PDF type detection

        extra_vertical_space = available_height - scaled_height
        if extra_vertical_space > 50 and pdf_type == "image":
            y_offset = header_space + (extra_vertical_space / 2)

        target_rect = fitz.Rect(
            x_offset,
            y_offset,
            x_offset + scaled_width,
            y_offset + scaled_height,
        )

        new_page.show_pdf_page(target_rect, source_pdf, page_num)

        if has_headers:
            self._add_header_without_page_number(new_page, pdf_file)

    def _add_header_without_page_number(self, page: fitz.Page, pdf_file: PDFFile):
        """Add headers without page numbers - INCREASED TOP SPACING"""
        header_notes = [pdf_file.header_line1, pdf_file.header_line2]
        page_width = page.rect.width

        margin = min(25, page_width * 0.04)
        font_size = 9

        # Header positioning - MORE SPACE AT TOP
        header_y_start = 20  # Increased from 15 to 20
        line_height = 10

        # Add header text
        if header_notes[0]:
            ProjectFontManager.insert_text_with_font(
                page, (margin, header_y_start), header_notes[0], fontsize=font_size, variant="regular"
            )

        if header_notes[1]:
            ProjectFontManager.insert_text_with_font(
                page, (margin, header_y_start + line_height), header_notes[1], fontsize=font_size, variant="regular"
            )

        # Add header separator - MORE MARGIN FROM HEADER TEXT
        if header_notes[0] or header_notes[1]:
            # Separator at 43px: gives space after header text (30px + 13px gap)
            separator_y = 43
            page.draw_line(
                (margin, separator_y),
                (page_width - margin, separator_y),
                width=0.5,
                color=(0.7, 0.7, 0.7),
            )

    def _copy_page_directly(
        self,
        output_pdf: fitz.Document,
        source_pdf: fitz.Document,
        page_num: int,
        page_number: int,
        page_width: float,
        page_height: float,
    ):
        """Copy page without modifications - DYNAMIC PAGE SIZE"""
        new_page = output_pdf.new_page(-1, width=page_width, height=page_height)
        src_page = source_pdf[page_num]
        src_rect = src_page.rect

        margin = min(20, page_width * 0.03)
        footer_space = 20

        available_width = page_width - 2 * margin
        available_height = page_height - margin - footer_space

        scale_x = available_width / src_rect.width
        scale_y = available_height / src_rect.height
        scale = min(scale_x, scale_y, self.options.scale_factor)

        scaled_width = src_rect.width * scale
        scaled_height = src_rect.height * scale

        x_offset = (page_width - scaled_width) / 2
        y_offset = margin

        target_rect = fitz.Rect(
            x_offset,
            y_offset,
            x_offset + scaled_width,
            y_offset + scaled_height,
        )

        new_page.show_pdf_page(target_rect, source_pdf, page_num)

    def _add_header_footer(self, page: fitz.Page, pdf_file: PDFFile, page_number: int):
        """Legacy method - not used in two-pass approach"""
        pass

    def _add_page_number_only(self, page: fitz.Page, page_number: int):
        """Add only page number with smart positioning"""
        page_text = f"{page_number}"
        page_width = page.rect.width  # Use actual page dimensions
        page_height = page.rect.height  # Use actual page dimensions

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
        text_width = ProjectFontManager.get_text_length(
            page_text, fontsize=self.options.page_number_font_size, variant="regular"
        )

        # Create background rectangle based on position
        if safe_position in ["top-center", "bottom-center"]:
            bg_rect = fitz.Rect(
                x - text_width / 2 - bg_padding,
                y - self.options.page_number_font_size - bg_padding,
                x + text_width / 2 + bg_padding,
                y + bg_padding,
            )
        else:  # right-aligned positions
            bg_rect = fitz.Rect(
                x - text_width - bg_padding,
                y - self.options.page_number_font_size - bg_padding,
                x + bg_padding,
                y + bg_padding,
            )

        page.draw_rect(bg_rect, color=(1, 1, 1), fill=(1, 1, 1), fill_opacity=0.7)

        # Insert page number (aligned based on position)
        if safe_position in ["top-center", "bottom-center"]:
            ProjectFontManager.insert_text_with_font(
                page, (x - text_width / 2, y), page_text, fontsize=self.options.page_number_font_size, variant="regular"
            )
        else:  # right-aligned positions
            ProjectFontManager.insert_text_with_font(
                page, (x - text_width, y), page_text, fontsize=self.options.page_number_font_size, variant="regular"
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
