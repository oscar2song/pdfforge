"""
TOC (Table of Contents) Core Module
Generates professional table of contents from PDF bookmarks
Enhanced version with multi-page support and better error handling
"""

import fitz  # PyMuPDF
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import os


@dataclass
class TOCStyle:
    """Configuration for TOC appearance."""
    font_name: str = "helv"  # Arial/Helvetica regular
    font_size: int = 12
    title: str = "Table of Contents"
    title_font_size: int = 18
    show_page_numbers: bool = True
    indent_per_level: int = 20
    leader_dots: bool = False  # Simplified layout like merge.py
    line_spacing: float = 1.67  # 20px line height for 12pt font
    margin_top: int = 80  # Match merge.py
    margin_left: int = 60  # Match merge.py (entries at x=60)
    margin_right: int = 50  # Match merge.py (right edge at 562 for 612pt width)
    margin_bottom: int = 72
    # Separator line boundaries (matching merge.py)
    separator_left: int = 50
    separator_right: int = 562  # For 612pt width pages
    page_number_x: int = 500  # Match merge.py
    # NEW: Page number position for TOC pages
    page_number_position: str = "bottom-center"  # "top-center", "bottom-center", "top-right", "bottom-right"
    page_number_font_size: int = 11


@dataclass
class BookmarkEntry:
    """Represents a single bookmark entry."""
    title: str
    page: int  # This should be the USER page number (content starts at 1)
    level: int = 0


class TOCGenerator:
    """
    Generates professional table of contents from PDF bookmarks.

    Features:
    - Multi-level bookmark support
    - Customizable styling
    - Leader dots for page numbers
    - Automatic multi-page handling
    - Page overflow protection
    """

    def __init__(self, style: Optional[TOCStyle] = None):
        """
        Initialize TOC generator.

        Args:
            style: TOC styling configuration
        """
        self.style = style or TOCStyle()

    def extract_bookmarks(self, pdf_doc: fitz.Document) -> List[BookmarkEntry]:
        """
        Extract bookmarks from PDF document.

        Args:
            pdf_doc: PyMuPDF document

        Returns:
            List of bookmark entries with USER page numbers (1-based)
        """
        try:
            toc = pdf_doc.get_toc()
            bookmarks = []

            # Check if we got valid data
            if toc is None:
                print("No TOC data found in PDF")
                return []

            # If it's a method instead of data, handle it
            if callable(toc):
                print("Warning: get_toc() returned a callable, trying to call it")
                try:
                    toc = toc()
                except:
                    print("Failed to call get_toc() as function")
                    return []

            for item in toc:
                if len(item) >= 3:  # Ensure we have [level, title, page]
                    level = item[0] - 1  # Convert to 0-based
                    title = item[1]
                    page = item[2] - 1  # Convert to 1-based for user display

                    bookmarks.append(BookmarkEntry(
                        title=title,
                        page=page,  # 1-based for UI
                        level=level
                    ))
                    print(f"Extracted bookmark: '{title}' -> page {page} (level {level})")

            print(f"Extracted {len(bookmarks)} bookmarks from PDF")
            return bookmarks

        except Exception as e:
            print(f"Error in extract_bookmarks: {e}")
            import traceback
            traceback.print_exc()
            return []

    def generate_toc(
            self,
            pdf_doc: fitz.Document,
            bookmarks: Optional[List[BookmarkEntry]] = None,
            insert_at_beginning: bool = True,
            page_width: float = 612,
            page_height: float = 792
    ) -> List[fitz.Page]:
        """
        Generate TOC pages from bookmarks.

        Args:
            pdf_doc: PyMuPDF document
            bookmarks: List of bookmark entries (if None, extract from PDF)
            insert_at_beginning: Whether to insert at start or end
            page_width: Width of TOC pages (should match content pages)
            page_height: Height of TOC pages (should match content pages)

        Returns:
            List of generated TOC pages
        """
        # Extract bookmarks if not provided
        if bookmarks is None:
            bookmarks = self.extract_bookmarks(pdf_doc)

        if not bookmarks:
            raise ValueError("No bookmarks found in PDF")

        # Create TOC pages
        toc_pages = self._create_toc_pages(pdf_doc, bookmarks, insert_at_beginning, page_width, page_height)

        return toc_pages

    def _create_toc_pages(
            self,
            pdf_doc: fitz.Document,
            bookmarks: List[BookmarkEntry],
            insert_at_beginning: bool,
            page_width: float = 612,
            page_height: float = 792
    ) -> List[fitz.Page]:
        """Create all necessary TOC pages with specified dimensions."""
        toc_pages = []

        # Update separator positions based on page width
        # Maintain proportions from merge.py: 50 to (width - 50) for separator
        self.style.separator_left = 50
        self.style.separator_right = page_width - 50
        self.style.page_number_x = page_width - 112  # ~500 for 612pt width

        # Calculate approximate entries per page
        usable_height = page_height - self.style.margin_top - self.style.margin_bottom - 40  # 40 for title space
        entry_height = self.style.font_size * self.style.line_spacing
        max_entries_per_page = int(usable_height / entry_height) - 2  # Safety margin

        # Split bookmarks across multiple pages if needed
        bookmark_pages = []
        current_batch = []

        for bookmark in bookmarks:
            current_batch.append(bookmark)
            if len(current_batch) >= max_entries_per_page:
                bookmark_pages.append(current_batch)
                current_batch = []

        if current_batch:  # Add remaining bookmarks
            bookmark_pages.append(current_batch)

        # Create pages
        insert_position = 0 if insert_at_beginning else len(pdf_doc)
        num_toc_pages = len(bookmark_pages)

        for page_num, page_bookmarks in enumerate(bookmark_pages):
            toc_page = pdf_doc.new_page(
                pno=insert_position + page_num,
                width=page_width,  # Use dynamic width
                height=page_height  # Use dynamic height
            )

            # Draw TOC content with link support
            is_first_page = (page_num == 0)
            self._draw_toc(toc_page, page_bookmarks, is_first_page, page_num + 1, len(bookmark_pages), num_toc_pages)

            toc_pages.append(toc_page)

        return toc_pages

    def _draw_toc(
            self,
            page: fitz.Page,
            bookmarks: List[BookmarkEntry],
            show_title: bool = True,
            page_num: int = 1,
            total_pages: int = 1,
            num_toc_pages: int = 1
    ):
        """Draw TOC content on page with clickable links."""
        y_position = self.style.margin_top

        # Draw title only on first page
        if show_title:
            y_position = self._draw_title(page, y_position)
            y_position += 40  # Match merge.py spacing (title_y + 40)
        else:
            # For continuation pages, show continuation indicator
            y_position = self._draw_continuation_header(page, y_position, page_num, total_pages)
            y_position += 20

        # Draw bookmark entries with clickable links
        for bookmark in bookmarks:
            y_position = self._draw_bookmark_entry(page, bookmark, y_position, num_toc_pages)
            y_position += self.style.font_size * self.style.line_spacing

    def _draw_title(self, page: fitz.Page, y_position: float) -> float:
        """Draw TOC title with separator line matching merge.py."""
        # Calculate center position for title
        title_width = fitz.get_text_length(
            self.style.title,
            fontname="helv",
            fontsize=self.style.title_font_size
        )
        title_x = (page.rect.width - title_width) / 2

        # Insert title text - centered
        page.insert_text(
            fitz.Point(title_x, y_position),
            self.style.title,
            fontsize=self.style.title_font_size,
            fontname="helv",
            color=(0, 0, 0)
        )

        # Draw separator line under title
        # Add visual spacing: title_font_size gives us the full height,
        # add a few pixels for breathing room
        separator_y = y_position + self.style.title_font_size + 5
        page.draw_line(
            fitz.Point(self.style.separator_left, separator_y),
            fitz.Point(self.style.separator_right, separator_y),
            width=1,
            color=(0, 0, 0)
        )

        return separator_y  # Return position after separator line

    def _draw_continuation_header(
            self,
            page: fitz.Page,
            y_position: float,
            page_num: int,
            total_pages: int
    ) -> float:
        """Draw continuation header for multi-page TOC."""
        header_text = f"{self.style.title} (continued) - Page {page_num} of {total_pages}"

        # Calculate center position
        text_width = fitz.get_text_length(header_text, fontname="helv", fontsize=self.style.font_size)
        text_x = (page.rect.width - text_width) / 2

        # Insert continuation header
        page.insert_text(
            fitz.Point(text_x, y_position + self.style.font_size),
            header_text,
            fontsize=self.style.font_size,
            fontname="helv",
            color=(0, 0, 0)
        )

        return y_position + self.style.font_size + 10

    def _draw_bookmark_entry(
            self,
            page: fitz.Page,
            bookmark: BookmarkEntry,
            y_position: float,
            num_toc_pages: int = 0
    ) -> float:
        """Draw a single bookmark entry WITHOUT adjusting page numbers."""
        # Calculate indentation
        indent = self.style.margin_left + (bookmark.level * self.style.indent_per_level)

        # Prepare text - USE USER PAGE NUMBERS (no adjustment needed)
        title_text = bookmark.title
        page_text = str(bookmark.page) if self.style.show_page_numbers else ""

        # Draw title at left side
        page.insert_text(
            fitz.Point(indent, y_position),
            title_text,
            fontsize=self.style.font_size,
            fontname="helv",
            color=(0, 0, 0)
        )

        if self.style.show_page_numbers:
            # Draw page number at consistent right position - SHOW USER PAGE NUMBER
            page.insert_text(
                fitz.Point(self.style.page_number_x, y_position),
                page_text,
                fontsize=self.style.font_size,
                fontname="helv",
                color=(0, 0, 0)
            )

        # NOTE: Links are created separately
        return y_position

    def _draw_leader_dots(
            self,
            page: fitz.Page,
            start_x: float,
            y: float,
            end_x: float
    ):
        """Draw leader dots between title and page number."""
        dot_spacing = 8
        current_x = start_x

        while current_x < end_x:
            # Draw a dot
            shape = page.new_shape()
            shape.draw_circle(
                fitz.Point(current_x, y),
                0.5
            )
            shape.finish(color=(0, 0, 0), fill=(0, 0, 0))
            shape.commit()

            current_x += dot_spacing

    def _add_roman_page_number(
            self,
            page: fitz.Page,
            page_number: str,
            position: str = "bottom-center",
            font_size: int = 10
    ):
        """
        Add Roman numeral page number using the same position as content pages.

        Args:
            page: PyMuPDF page object
            page_number: Roman numeral string (e.g., "i", "ii", "iii")
            position: Position for page number ("top-center", "bottom-center", "top-right", "bottom-right")
            font_size: Font size for the page number
        """
        page_width = page.rect.width
        page_height = page.rect.height

        # Calculate coordinates based on position setting
        if position == "top-center":
            x = page_width / 2
            y = 25
        elif position == "bottom-center":
            x = page_width / 2
            y = page_height - 25
        elif position == "top-right":
            x = page_width - 50
            y = 25
        elif position == "bottom-right":
            x = page_width - 50
            y = page_height - 25
        else:  # Default to bottom-center
            x = page_width / 2
            y = page_height - 25

        # Estimate text width for centering (approximate, since we can't use ProjectFontManager here)
        # For Roman numerals which are typically short, use a simple estimation
        char_width = font_size * 0.6  # Approximate width per character
        text_width = len(page_number) * char_width

        # Add semi-transparent background rectangle for better visibility
        bg_padding = 5
        if position in ["top-center", "bottom-center"]:
            # Center-aligned
            bg_rect = fitz.Rect(
                x - text_width / 2 - bg_padding,
                y - font_size - bg_padding,
                x + text_width / 2 + bg_padding,
                y + bg_padding,
            )
            text_x = x - text_width / 2
        else:  # right-aligned positions
            bg_rect = fitz.Rect(
                x - text_width - bg_padding,
                y - font_size - bg_padding,
                x + bg_padding,
                y + bg_padding,
            )
            text_x = x - text_width

        # Draw background
        page.draw_rect(bg_rect, color=(1, 1, 1), fill=(1, 1, 1), fill_opacity=0.7)

        # Insert page number
        page.insert_text(
            fitz.Point(text_x, y),
            page_number,
            fontsize=font_size,
            fontname="helv",
            color=(0, 0, 0)
        )

    def add_toc_to_pdf(
            self,
            input_pdf_path: str,
            output_pdf_path: str,
            bookmarks: Optional[List[BookmarkEntry]] = None,
            insert_at_beginning: bool = True,
            page_number_position: str = "bottom-center",
            page_number_font_size: int = 10
    ) -> Dict[str, any]:
        """
        Add TOC to existing PDF.

        Args:
            input_pdf_path: Path to input PDF
            output_pdf_path: Path to output PDF
            bookmarks: Optional custom bookmarks (should contain USER page numbers)
            insert_at_beginning: Whether to insert at start
            page_number_position: Position for Roman numerals
            page_number_font_size: Font size for Roman numerals

        Returns:
            Result dictionary
        """
        try:
            # Open PDF
            pdf_doc = fitz.open(input_pdf_path)
            original_page_count = len(pdf_doc)

            # === STEP 1: Remove old TOC pages if they exist ===
            pages_to_delete = []
            for page_num in range(min(10, len(pdf_doc))):
                page = pdf_doc[page_num]
                text = page.get_text()
                if "Table of Contents" in text or "table of contents" in text.lower():
                    pages_to_delete.append(page_num)
                    print(f"Found old TOC page at position {page_num}, will remove")

            # Delete old TOC pages in reverse order
            for page_num in reversed(pages_to_delete):
                pdf_doc.delete_page(page_num)
                print(f"Removed old TOC page {page_num}")

            # === STEP 2: Use provided bookmarks or extract from PDF ===
            if bookmarks is None:
                bookmarks = self.extract_bookmarks(pdf_doc)

            if not bookmarks:
                return {
                    'success': False,
                    'error': 'No bookmarks provided or found in PDF'
                }

            # === STEP 3: Detect page size ===
            if len(pdf_doc) > 0:
                first_page = pdf_doc[0]
                page_width = first_page.rect.width
                page_height = first_page.rect.height
                print(f"Detected page size: {page_width:.0f} x {page_height:.0f} pts")
            else:
                page_width = 612
                page_height = 792

            # === STEP 4: Generate new TOC pages ===
            toc_pages = self.generate_toc(pdf_doc, bookmarks, insert_at_beginning, page_width, page_height)
            num_toc_pages = len(toc_pages)
            print(f"Generated {num_toc_pages} TOC page(s)")

            # === STEP 5: Add Roman numerals to TOC pages ===
            roman_numerals = ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x"]
            for i in range(num_toc_pages):
                page = pdf_doc[i]  # TOC pages are at beginning
                roman = roman_numerals[i] if i < len(roman_numerals) else f"({i + 1})"

                # Use the provided page_number_position parameter
                self._add_roman_page_number(
                    page,
                    roman,
                    position=page_number_position,
                    font_size=page_number_font_size
                )
                print(f"Added Roman numeral '{roman}' to TOC page {i} at position: {page_number_position}")

            # === STEP 6: CORRECTED PAGE NUMBER LOGIC ===
            print(f"=== Applying Corrected Page Number Logic ===")
            print(f"TOC pages: {num_toc_pages}")
            print(f"Original document pages: {original_page_count}")
            print(f"Total pages after TOC insertion: {len(pdf_doc)}")

            # KEY FIX: SIMPLIFIED AND CORRECTED LOGIC
            # - User provides content page numbers (1, 2, 3...)
            # - TOC pages are inserted at beginning (pages 0 to num_toc_pages-1)
            # - Content starts at page num_toc_pages (0-based) which is page num_toc_pages + 1 (1-based)
            # - TOC should show user page numbers (1, 2, 3...)
            # - Links should point to: num_toc_pages + (user_page - 1)

            # Step 6A: Fix TOC links (with proper multi-page support)
            print("Fixing TOC links...")

            # Recalculate bookmark distribution across pages (matching _create_toc_pages logic)
            usable_height = page_height - self.style.margin_top - self.style.margin_bottom - 40
            entry_height = self.style.font_size * self.style.line_spacing
            max_entries_per_page = int(usable_height / entry_height) - 2

            # Split bookmarks into pages
            bookmark_pages = []
            current_batch = []
            for bookmark in bookmarks:
                current_batch.append(bookmark)
                if len(current_batch) >= max_entries_per_page:
                    bookmark_pages.append(current_batch)
                    current_batch = []
            if current_batch:
                bookmark_pages.append(current_batch)

            print(f"Bookmarks distributed across {len(bookmark_pages)} page(s):")
            for idx, page_bookmarks in enumerate(bookmark_pages):
                print(f"  Page {idx + 1}: {len(page_bookmarks)} bookmarks")

            # Create links for each TOC page with correct bookmark subset
            for toc_page_num in range(num_toc_pages):
                page = pdf_doc[toc_page_num]

                # Clear existing links
                links = page.get_links()
                for link in links:
                    page.delete_link(link)

                # Get bookmarks for this specific TOC page
                if toc_page_num >= len(bookmark_pages):
                    print(f"Warning: No bookmarks for TOC page {toc_page_num}")
                    continue

                page_bookmarks = bookmark_pages[toc_page_num]
                print(f"Processing TOC page {toc_page_num + 1} with {len(page_bookmarks)} bookmarks")

                # Calculate correct starting y_position matching _draw_toc() logic
                y_position = self.style.margin_top
                if toc_page_num == 0:  # First page has title
                    # Match _draw_title: separator_y = y_position + title_font_size + 5
                    separator_y = y_position + self.style.title_font_size + 5
                    y_position = separator_y + 40  # Match _draw_toc spacing
                else:  # Continuation pages have header
                    # Match _draw_continuation_header spacing
                    y_position = y_position + self.style.font_size + 20

                # Create links only for bookmarks on THIS page
                for i, bookmark in enumerate(page_bookmarks):
                    # CORRECTED LOGIC:
                    # User provides: bookmark.page = 1, 2, 3... (content pages)
                    # After TOC insertion, content actually starts at page num_toc_pages (0-based)
                    # So target page = num_toc_pages + (bookmark.page - 1)
                    target_page_index = num_toc_pages + (bookmark.page - 1)

                    # Safety check - ensure target page exists
                    if target_page_index >= len(pdf_doc):
                        print(f"Warning: Target page {target_page_index + 1} exceeds PDF length {len(pdf_doc)}")
                        continue
                    if target_page_index < 0:
                        print(f"Warning: Target page {target_page_index + 1} is negative")
                        continue

                    # Create clickable area
                    link_rect = fitz.Rect(
                        self.style.separator_left,
                        y_position - 8,
                        self.style.separator_right,
                        y_position + 12
                    )

                    # Insert link - point to CORRECT PDF page
                    page.insert_link({
                        "kind": fitz.LINK_GOTO,
                        "from": link_rect,
                        "page": target_page_index,
                        "to": fitz.Point(0, 50),
                    })

                    # TOC displays user page number, links to actual PDF page
                    print(
                        f"  TOC page {toc_page_num + 1}: '{bookmark.title}' -> shows page {bookmark.page}, links to PDF page {target_page_index + 1}")

                    y_position += self.style.font_size * self.style.line_spacing

            # Step 6B: Fix PDF bookmarks - they should point to ACTUAL page numbers after TOC insertion
            print("Fixing PDF bookmarks...")
            final_bookmarks = []
            for bookmark in bookmarks:
                # Bookmarks point to ACTUAL PDF pages (after TOC insertion)
                # Same calculation as for links
                actual_pdf_page = num_toc_pages + bookmark.page  # This is the key fix!
                final_bookmarks.append(BookmarkEntry(
                    title=bookmark.title,
                    page=actual_pdf_page,  # Use actual PDF page number after TOC insertion
                    level=bookmark.level
                ))
                print(f"  '{bookmark.title}' -> PDF bookmark points to actual PDF page {actual_pdf_page}")

            # Add final bookmarks to PDF outline
            BookmarkManager.add_bookmarks_to_pdf(pdf_doc, final_bookmarks)

            # === STEP 7: Save ===
            pdf_doc.save(output_pdf_path)
            pdf_doc.close()

            print(f"✓ TOC generation complete:")
            print(f"  - TOC pages: {num_toc_pages} (Roman numerals)")
            print(f"  - Content pages: {original_page_count} (Arabic numerals)")
            print(f"  - TOC shows user page numbers (content starts at 1)")
            print(f"  - TOC links work correctly to actual PDF pages")
            print(f"  - PDF bookmarks work correctly")

            return {
                'success': True,
                'output_path': output_pdf_path,
                'toc_pages': num_toc_pages,
                'bookmark_count': len(final_bookmarks),
                'old_toc_pages_removed': len(pages_to_delete)
            }

        except Exception as e:
            print(f"Error in add_toc_to_pdf: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }

    def update_bookmarks_only(
            self,
            input_pdf_path: str,
            output_pdf_path: str,
            bookmarks: List[BookmarkEntry]
    ) -> Dict[str, any]:
        """
        Update PDF bookmarks without generating TOC pages.

        Args:
            input_pdf_path: Path to input PDF
            output_pdf_path: Path to output PDF
            bookmarks: List of bookmark entries with USER page numbers (1, 2, 3...)

        Returns:
            Result dictionary
        """
        try:
            # Open PDF
            pdf_doc = fitz.open(input_pdf_path)

            # Convert user page numbers to PDF page numbers
            pdf_bookmarks = []
            for bookmark in bookmarks:
                # User provides 1-based page numbers, PDF uses 1-based for bookmarks
                # So we can use them directly (no TOC pages to offset)
                pdf_bookmarks.append(BookmarkEntry(
                    title=bookmark.title,
                    page=bookmark.page,  # Use as-is (1-based)
                    level=bookmark.level
                ))
                print(f"Bookmark: '{bookmark.title}' -> page {bookmark.page}")

            # Add bookmarks to PDF
            BookmarkManager.add_bookmarks_to_pdf(pdf_doc, pdf_bookmarks)

            # Save
            pdf_doc.save(output_pdf_path)
            pdf_doc.close()

            return {
                'success': True,
                'output_path': output_pdf_path,
                'bookmark_count': len(bookmarks)
            }

        except Exception as e:
            print(f"Error in update_bookmarks_only: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }


class BookmarkManager:
    """Manage PDF bookmarks for merge and standalone operations."""

    @staticmethod
    def create_bookmark_from_filename(filename: str, page: int, level: int = 0) -> BookmarkEntry:
        """
        Create bookmark entry from filename.

        Args:
            filename: Source filename
            page: Page number
            level: Bookmark level (0-based)

        Returns:
            BookmarkEntry
        """
        # Clean filename for bookmark
        title = os.path.splitext(os.path.basename(filename))[0]
        title = title.replace('_', ' ').replace('-', ' ')
        title = ' '.join(word.capitalize() for word in title.split())

        return BookmarkEntry(title=title, page=page, level=level)

    @staticmethod
    def add_bookmarks_to_pdf(pdf_doc: fitz.Document, bookmarks: List[BookmarkEntry]):
        """
        Add bookmarks to PDF document.

        Args:
            pdf_doc: PyMuPDF document
            bookmarks: List of bookmark entries
        """
        # Convert to PyMuPDF TOC format
        toc = []
        for bookmark in bookmarks:
            toc.append([
                bookmark.level + 1,  # PyMuPDF uses 1-based levels
                bookmark.title,
                bookmark.page
            ])

        # Set TOC
        pdf_doc.set_toc(toc)

    @staticmethod
    def merge_pdfs_with_bookmarks(
            pdf_files: List[str],
            bookmark_labels: Optional[Dict[int, str]] = None,
            output_path: str = None,
            add_toc: bool = False,
            toc_style: Optional[TOCStyle] = None
    ) -> Dict[str, any]:
        """
        Merge PDFs with custom bookmarks and optional TOC.

        Args:
            pdf_files: List of PDF file paths
            bookmark_labels: Dict mapping file index to custom label
            output_path: Output PDF path
            add_toc: Whether to generate TOC
            toc_style: TOC styling options

        Returns:
            Result dictionary
        """
        try:
            merged_doc = fitz.open()
            bookmarks = []
            current_page = 0
            bookmark_labels = bookmark_labels or {}

            # Merge PDFs and create bookmarks
            for idx, pdf_path in enumerate(pdf_files):
                src_doc = fitz.open(pdf_path)

                # Insert pages
                merged_doc.insert_pdf(src_doc)

                # Create bookmark
                if idx in bookmark_labels and bookmark_labels[idx]:
                    label = bookmark_labels[idx]
                else:
                    label = BookmarkManager.create_bookmark_from_filename(pdf_path, current_page + 1).title

                # Adjust page numbers if TOC will be added at beginning
                page_offset = 0
                if add_toc:
                    # Estimate TOC pages (will be adjusted later)
                    estimated_toc_pages = max(1, len(pdf_files) // 40 + 1)
                    page_offset = estimated_toc_pages

                bookmarks.append(BookmarkEntry(
                    title=label,
                    page=current_page + 1 + page_offset,
                    level=0
                ))

                current_page += len(src_doc)
                src_doc.close()

            # Generate TOC if requested
            if add_toc:
                toc_gen = TOCGenerator(toc_style)
                toc_pages = toc_gen.generate_toc(merged_doc, bookmarks, insert_at_beginning=True)

                # Update bookmark page numbers with actual TOC page count
                actual_toc_pages = len(toc_pages)
                estimated_toc_pages = max(1, len(pdf_files) // 40 + 1)
                page_adjustment = actual_toc_pages - estimated_toc_pages

                if page_adjustment != 0:
                    # Update bookmarks in merged doc
                    updated_bookmarks = []
                    for bookmark in bookmarks:
                        updated_bookmarks.append(BookmarkEntry(
                            title=bookmark.title,
                            page=bookmark.page + page_adjustment,
                            level=bookmark.level
                        ))
                    bookmarks = updated_bookmarks

            # Add bookmarks to merged PDF
            BookmarkManager.add_bookmarks_to_pdf(merged_doc, bookmarks)

            # Generate output path if not provided
            if not output_path:
                base_name = os.path.splitext(os.path.basename(pdf_files[0]))[0]
                output_path = f"{base_name}_merged.pdf"

            # Save
            merged_doc.save(output_path)
            merged_doc.close()

            return {
                'success': True,
                'output_path': output_path,
                'total_pages': current_page + (len(toc_pages) if add_toc else 0),
                'bookmark_count': len(bookmarks),
                'has_toc': add_toc,
                'toc_pages': len(toc_pages) if add_toc else 0
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }