"""
PDFForge - Professional PDF Tools Web Application
Enhanced with OCR, Smart Page Numbers, Bookmarks, and More
"""

from flask import Flask, render_template, request, send_file, jsonify
import fitz  # PyMuPDF
import pdfplumber
import os
import tempfile
from werkzeug.utils import secure_filename
from datetime import datetime
import pytesseract
from PIL import Image
import io
import zipfile
import shutil
import re

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB for batch processing
app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()

# Constants
LETTER_WIDTH = 612  # 8.5 inches
LETTER_HEIGHT = 792  # 11 inches

# Standard page sizes (width x height in points, 72 points = 1 inch)
PAGE_SIZES = {
    'letter': (612, 792),
    'letter-landscape': (792, 612),
    'legal': (612, 1008),
    'legal-landscape': (1008, 612),
    'A4': (595, 842),
    'a4': (595, 842),
    'a4-landscape': (842, 595),
    'A3': (842, 1191),
    'a3': (842, 1191),
    'a3-landscape': (1191, 842),
    'A5': (420, 595),
    'a5': (420, 595),
    'custom': (612, 792),  # Default to letter
}


# ============================================================================
# ENHANCED MERGE FUNCTIONS (With OCR, Smart Page Numbers, Bookmarks)
# ============================================================================

def detect_pdf_type(page):
    """
    Detect if PDF page is image-based (scanned) or text-based.
    Returns dict with detection results.
    """
    try:
        text_content = page.get_text().strip()

        image_count = 0
        if '/Resources' in page and '/XObject' in page['/Resources']:
            xObject = page['/Resources']['/XObject'].get_object()
            for obj in xObject:
                if xObject[obj]['/Subtype'] == '/Image':
                    image_count += 1

        is_image_based = len(text_content) < 100 and image_count > 0

        return {
            'is_image_based': is_image_based,
            'text_length': len(text_content),
            'image_count': image_count,
            'has_content': len(text_content) > 0 or image_count > 0
        }
    except Exception as e:
        return {
            'is_image_based': True,
            'text_length': 0,
            'image_count': 0,
            'has_content': False
        }


def has_content_in_header_area(page, threshold_y=60):
    """Detect if page has traditional header that needs extra space."""
    try:
        pdf_type = detect_pdf_type(page)

        if pdf_type['is_image_based']:
            return True

        header_rect = fitz.Rect(0, 0, page.rect.width, 40)
        text = page.get_text("text", clip=header_rect).strip()

        if not text:
            drawings = page.get_drawings()
            for drawing in drawings:
                if drawing["rect"].y0 < 40 and drawing["rect"].height < 2:
                    return True
            return False

        lines = text.split('\n')
        header_keywords = ['confidential', 'secret', 'internal', 'draft',
                           'proprietary', 'classified', 'restricted']

        if len(text) < 100:
            text_lower = text.lower()
            if any(keyword in text_lower for keyword in header_keywords):
                return True

        if len(lines) <= 2 and all(len(line.strip()) < 50 for line in lines):
            return True

        return False

    except:
        return True


def has_small_top_margin(page, threshold=80):
    """Detect if page has very small top margin."""
    try:
        pdf_type = detect_pdf_type(page)

        if pdf_type['is_image_based']:
            print(f"      → Image-based PDF detected - assuming small top margin")
            return True

        text_dict = page.get_text("dict")
        if not text_dict or 'blocks' not in text_dict:
            return False

        min_y = float('inf')
        for block in text_dict['blocks']:
            if block.get('type') == 0:
                if 'lines' in block and block['lines']:
                    first_line = block['lines'][0]
                    y_pos = first_line.get('bbox', [0, 0, 0, 0])[1]
                    min_y = min(min_y, y_pos)

        drawings = page.get_drawings()
        for drawing in drawings:
            if drawing["rect"].height > 5:
                min_y = min(min_y, drawing["rect"].y0)

        if min_y < threshold:
            print(f"      → Small top margin detected: content starts at y={min_y:.1f}")
            return True

        return False

    except Exception as e:
        print(f"      Warning: Could not detect top margin - {e}")
        return True


def detect_existing_page_numbers(page, position, font_size):
    """
    Detect if there are existing page numbers at the target position.
    Returns True if conflict detected.
    """
    try:
        page_width = page.rect.width
        page_height = page.rect.height

        # Define detection areas based on position
        if position == "top-center":
            detect_rect = fitz.Rect(page_width / 2 - 50, 10, page_width / 2 + 50, 40)
        elif position == "bottom-center":
            detect_rect = fitz.Rect(page_width / 2 - 50, page_height - 40, page_width / 2 + 50, page_height - 10)
        elif position == "top-right":
            detect_rect = fitz.Rect(page_width - 100, 10, page_width - 10, 40)
        elif position == "bottom-right":
            detect_rect = fitz.Rect(page_width - 100, page_height - 40, page_width - 10, page_height - 10)
        else:  # top-center as default
            detect_rect = fitz.Rect(page_width / 2 - 50, 10, page_width / 2 + 50, 40)

        # Extract text from detection area
        text = page.get_text("text", clip=detect_rect).strip()

        # Look for page number patterns
        page_number_patterns = [
            r'\b\d{1,3}\b',  # 1-3 digit numbers
            r'\bpage\s*\d+\b',  # "page 1" etc.
            r'\b\d+\s*of\s*\d+\b',  # "1 of 10" etc.
        ]

        for pattern in page_number_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                print(f"      → Existing page number detected at {position}")
                return True

        # Also check for numbers using OCR for image-based PDFs
        pdf_type = detect_pdf_type(page)
        if pdf_type['is_image_based']:
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))

            # Crop to detection area
            img_width, img_height = img.size
            crop_box = (
                int(detect_rect.x0 * img_width / page_width),
                int(detect_rect.y0 * img_height / page_height),
                int(detect_rect.x1 * img_width / page_width),
                int(detect_rect.y1 * img_height / page_height)
            )
            cropped_img = img.crop(crop_box)

            # OCR the cropped area
            ocr_text = pytesseract.image_to_string(cropped_img)
            for pattern in page_number_patterns:
                if re.search(pattern, ocr_text, re.IGNORECASE):
                    print(f"      → Existing page number detected via OCR at {position}")
                    return True

        return False

    except Exception as e:
        print(f"      Warning: Could not detect existing page numbers - {e}")
        return False


def get_safe_page_number_position(page, preferred_position, font_size):
    """
    Find a safe position for page number that doesn't conflict with existing content.
    """
    positions_to_try = [
        preferred_position,
        "top-right",
        "bottom-right",
        "bottom-center",
        "top-center"  # Fallback to original
    ]

    for position in positions_to_try:
        if not detect_existing_page_numbers(page, position, font_size):
            if position != preferred_position:
                print(f"      → Using alternative position: {position}")
            return position

    # If all positions have conflicts, use top-right as default
    print(f"      → All positions conflicted, using top-right")
    return "top-right"


def add_page_number_only(page, page_number, position="top-center", font_size=12, font_name="helv"):
    """Add only page number to page with smart positioning"""
    page_width = page.rect.width
    page_height = page.rect.height
    page_text = f"{page_number}"

    # Get safe position
    safe_position = get_safe_page_number_position(page, position, font_size)

    # Calculate coordinates based on position
    if safe_position == "top-center":
        x = (page_width - fitz.get_text_length(page_text, fontsize=font_size, fontname=font_name)) / 2
        y = 25
    elif safe_position == "bottom-center":
        x = (page_width - fitz.get_text_length(page_text, fontsize=font_size, fontname=font_name)) / 2
        y = page_height - 25
    elif safe_position == "top-right":
        x = page_width - fitz.get_text_length(page_text, fontsize=font_size, fontname=font_name) - 25
        y = 25
    elif safe_position == "bottom-right":
        x = page_width - fitz.get_text_length(page_text, fontsize=font_size, fontname=font_name) - 25
        y = page_height - 25
    else:
        x = (page_width - fitz.get_text_length(page_text, fontsize=font_size, fontname=font_name)) / 2
        y = 25

    # Add semi-transparent background
    bg_padding = 5
    text_width = fitz.get_text_length(page_text, fontsize=font_size, fontname=font_name)
    bg_rect = fitz.Rect(
        x - bg_padding,
        y - font_size - bg_padding,
        x + text_width + bg_padding,
        y + bg_padding
    )
    page.draw_rect(bg_rect, color=(1, 1, 1), fill=(1, 1, 1), fill_opacity=0.7)

    # Insert page number
    page.insert_text(
        (x, y),
        page_text,
        fontsize=font_size,
        fontname=font_name
    )


def add_header_and_footer(page, header_notes, page_number, page_width,
                          page_height, add_footer_line, add_page_numbers,
                          page_number_position="top-center", page_number_font_size=12):
    """Add header (two lines) and optional footer line with smart page numbers"""
    margin = 30
    font_size = 10

    # === Header ===
    header_y = 25
    line_height = 12

    # Top left - first line
    if header_notes[0]:
        page.insert_text(
            (margin, header_y),
            header_notes[0],
            fontsize=font_size,
            fontname="helv"
        )

    # Top left - second line
    if header_notes[1]:
        page.insert_text(
            (margin, header_y + line_height),
            header_notes[1],
            fontsize=font_size,
            fontname="helv"
        )

    # Page number with smart positioning
    if add_page_numbers:
        add_page_number_only(page, page_number, page_number_position, page_number_font_size)

    # Header separator line
    if header_notes[0] or header_notes[1]:
        header_line_y = 45
        page.draw_line(
            (margin, header_line_y),
            (page_width - margin, header_line_y),
            width=0.5
        )

    # === Footer (optional) ===
    if add_footer_line:
        footer_line_y = page_height - 25
        page.draw_line(
            (margin, footer_line_y),
            (page_width - margin, footer_line_y),
            width=0.5
        )


def process_and_add_page(output_pdf, source_pdf, page_num, header_notes,
                         final_page_num, letter_width, letter_height,
                         scale_factor, scale_factor_optimized,
                         add_footer_line, smart_spacing, add_page_numbers,
                         page_number_position="top-center", page_number_font_size=12):
    """Process single page with enhanced features"""
    new_page = output_pdf.new_page(width=letter_width, height=letter_height)

    src_page = source_pdf[page_num]
    src_rect = src_page.rect

    pdf_type = detect_pdf_type(src_page)

    # IMPROVED FLEXIBLE SCALING LOGIC - MUCH LESS AGGRESSIVE
    if smart_spacing:
        has_header_content = has_content_in_header_area(src_page)
        has_tiny_margin = has_small_top_margin(src_page, threshold=80)

        # Check if headers are empty - if so, use minimal scaling
        headers_empty = not header_notes[0] and not header_notes[1]

        if headers_empty:
            # No headers provided - VERY minimal scaling and space
            if pdf_type['is_image_based']:
                current_scale_factor = 0.99  # Almost no scaling for image PDFs without headers
                header_space = 20  # Minimal header space
                content_offset = 0
                status_msg = "IMAGE-BASED PDF (no headers) - scale 0.99"
            elif has_tiny_margin:
                current_scale_factor = 0.995
                header_space = 20
                content_offset = 0
                status_msg = "TINY margin (no headers) - scale 0.995"
            elif has_header_content:
                current_scale_factor = 0.98  # Very slight reduction for PDFs with existing headers
                header_space = 30
                content_offset = 0
                status_msg = "has header (no custom) - scale 0.98"
            else:
                current_scale_factor = 0.998  # Almost full size for clean PDFs
                header_space = 20
                content_offset = 15
                status_msg = "clean PDF (no headers) - optimized scale 0.998"
        else:
            # Headers provided - use moderate scaling
            if pdf_type['is_image_based']:
                current_scale_factor = 0.95  # Moderate scaling for image PDFs with headers
                header_space = 50  # Reasonable header space
                content_offset = 0
                status_msg = "IMAGE-BASED PDF (with headers) - scale 0.95"
            elif has_tiny_margin:
                current_scale_factor = 0.97
                header_space = 40
                content_offset = 0
                status_msg = "TINY margin (with headers) - scale 0.97"
            elif has_header_content:
                current_scale_factor = 0.98  # Very slight reduction for PDFs with existing headers
                header_space = 35
                content_offset = 0
                status_msg = "has header (with custom) - scale 0.98"
            else:
                current_scale_factor = 0.985  # Minimal reduction for clean PDFs with headers
                header_space = 35
                content_offset = 0
                status_msg = "clean PDF (with headers) - scale 0.985"
    else:
        header_space = 35
        content_offset = 0
        current_scale_factor = scale_factor
        status_msg = "standard"

    print(
        f"  Processing page {final_page_num}, original size: {src_rect.width:.1f} x {src_rect.height:.1f} [{status_msg}]")

    # Calculate scaling and position
    footer_space = 15 if add_footer_line else 5  # Minimal footer space
    margin = 10  # Minimal margin

    available_width = letter_width - 2 * margin
    available_height = letter_height - header_space - footer_space + content_offset

    scale_x = available_width / src_rect.width
    scale_y = available_height / src_rect.height
    scale = min(scale_x, scale_y, current_scale_factor)

    scaled_width = src_rect.width * scale
    scaled_height = src_rect.height * scale

    x_offset = (letter_width - scaled_width) / 2
    y_offset = header_space + (available_height - scaled_height) / 2 - content_offset

    target_rect = fitz.Rect(
        x_offset,
        y_offset,
        x_offset + scaled_width,
        y_offset + scaled_height
    )

    # Insert source page content
    new_page.show_pdf_page(target_rect, source_pdf, page_num)

    # Add header and footer with enhanced page numbers
    add_header_and_footer(new_page, header_notes, final_page_num,
                          letter_width, letter_height, add_footer_line, add_page_numbers,
                          page_number_position, page_number_font_size)


def copy_page_directly(output_pdf, source_pdf, page_num, page_number, add_page_numbers,
                       page_number_position="top-center", page_number_font_size=12):
    """Copy page directly with optional smart page numbers"""
    output_pdf.insert_pdf(source_pdf, from_page=page_num, to_page=page_num)

    if add_page_numbers:
        new_page = output_pdf[-1]
        add_page_number_only(new_page, page_number, page_number_position, page_number_font_size)

    print(f"  Copied page {page_number} (kept as-is)")


def create_bookmarks(pdf_doc, file_info: List[Dict[str, any]]):
    """
    Create bookmarks/table of contents for merged PDF
    file_info: [{'name': 'doc1.pdf', 'start_page': 0, 'page_count': 10}, ...]
    """
    toc = []

    for info in file_info:
        # Create bookmark entry: [level, title, page_number]
        toc.append([1, info['name'], info['start_page'] + 1])

    pdf_doc.set_toc(toc)


def merge_pdfs_enhanced(file_configs, options=None):
    """
    Enhanced merge PDFs with all new features.
    """
    options = options or {}
    add_headers = options.get('add_headers', False)
    page_start = options.get('page_start', 1)
    custom_filename = options.get('output_filename', '')
    scale_factor = options.get('scale_factor', 0.96)
    scale_factor_optimized = options.get('scale_factor_optimized', 0.99)
    add_footer_line = options.get('add_footer_line', False)
    smart_spacing = options.get('smart_spacing', True)
    add_page_numbers = options.get('add_page_numbers', True)
    page_number_position = options.get('page_number_position', 'top-center')
    page_number_font_size = options.get('page_number_font_size', 12)
    add_bookmarks = options.get('add_bookmarks', True)

    output_pdf = fitz.open()
    total_page_number = page_start
    total_pages_processed = 0
    file_info = []
    current_page = 0

    print("=" * 80)
    print("ENHANCED PDF MERGE - With OCR, Smart Page Numbers, Bookmarks")
    print("=" * 80)
    print(f"Add headers: {add_headers}")
    print(f"Smart spacing: {smart_spacing}")
    print(f"Page numbers: {add_page_numbers}")
    print(f"Page number position: {page_number_position}")
    print(f"Page number font size: {page_number_font_size}")
    print(f"Add bookmarks: {add_bookmarks}")
    print(f"Starting page number: {page_start}")
    print()

    if add_headers:
        all_headers_empty = all(
            not config.get('header_line1', '').strip() and
            not config.get('header_line2', '').strip()
            for config in file_configs
        )
        if all_headers_empty:
            print("📝 Note: All headers are empty - merging as-is (simple merge)")
            add_headers = False

    for idx, config in enumerate(file_configs):
        file_path = config['path']

        if not os.path.exists(file_path):
            print(f"⚠ Warning: File not found - {file_path}")
            continue

        if add_headers:
            header_line1 = config.get('header_line1', '')
            header_line2 = config.get('header_line2', '')
            header_notes = [header_line1, header_line2]
            should_transform = True
        else:
            should_transform = False

        pdf = fitz.open(file_path)
        page_count = len(pdf)
        filename = os.path.splitext(config['name'])[0]

        start_page_idx = current_page

        transform_status = "Transform (add headers)" if should_transform else "Direct merge"
        print(f"Processing PDF {idx + 1}: {os.path.basename(file_path)} ({page_count} pages) - {transform_status}")

        for page_num in range(page_count):
            if should_transform:
                process_and_add_page(
                    output_pdf, pdf, page_num,
                    header_notes, total_page_number,
                    LETTER_WIDTH, LETTER_HEIGHT,
                    scale_factor, scale_factor_optimized,
                    add_footer_line, smart_spacing, add_page_numbers,
                    page_number_position, page_number_font_size
                )
            else:
                copy_page_directly(
                    output_pdf, pdf, page_num,
                    total_page_number, add_page_numbers,
                    page_number_position, page_number_font_size
                )

            total_page_number += 1
            current_page += 1

        # Track file info for bookmarks
        file_info.append({
            'name': filename,
            'start_page': start_page_idx,
            'page_count': page_count
        })

        pdf.close()
        total_pages_processed += page_count

    # Add bookmarks if requested
    if add_bookmarks and len(file_info) > 1:
        create_bookmarks(output_pdf, file_info)

    if total_pages_processed > 0:
        if custom_filename:
            if not custom_filename.endswith('.pdf'):
                custom_filename += '.pdf'
            output_filename = custom_filename
        else:
            first_filename = os.path.basename(file_configs[0]['name'])
            output_filename = create_output_filename(first_filename, 'merged')

        output_path = os.path.join(tempfile.gettempdir(), output_filename)
        # if add_bookmarks:
        #     debug_bookmarks(output_pdf)
        output_pdf.save(output_path, garbage=4, deflate=True)
        output_pdf.close()

        print("\n" + "=" * 80)
        print(f"✓ Merge complete!")
        print(f"✓ Processed {len(file_configs)} PDF files")
        print(f"✓ Total {total_pages_processed} pages")
        print(f"✓ Bookmarks: {len(file_configs) if add_bookmarks else 0} files")
        print(f"✓ Output: {output_path}")
        print("=" * 80)
        return output_path
    else:
        print("\n✗ Error: No pages processed successfully")
        return None


# ============================================================================
# ENHANCED NORMALIZE FUNCTIONS (with Custom Page Sizes)
# ============================================================================

def has_text_layer(page):
    """Check if a PDF page has a text layer."""
    try:
        text = page.get_text().strip()
        return len(text) > 10
    except:
        return False


def perform_ocr_on_page(page):
    """Perform OCR on a PDF page to extract text."""
    try:
        pix = page.get_pixmap(matrix=fitz.Matrix(300 / 72, 300 / 72))
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        text = pytesseract.image_to_string(img)
        return text
    except Exception as e:
        print(f"      Warning: OCR failed - {e}")
        return ""


def add_text_layer_ocr(page, text):
    """Add invisible text layer to a PDF page for searchability."""
    if not text or len(text.strip()) < 5:
        return

    rect = page.rect
    try:
        page.insert_textbox(
            rect,
            text,
            fontsize=1,
            color=(1, 1, 1),
            align=fitz.TEXT_ALIGN_LEFT
        )
    except:
        pass


def normalize_pdf_enhanced(input_path, output_path, options=None):
    """Enhanced normalize PDF with custom page sizes and OCR."""
    options = options or {}
    page_size = options.get('page_size', 'letter')
    orientation = options.get('orientation', 'portrait')
    add_ocr = options.get('add_ocr', False)
    force_ocr = options.get('force_ocr', False)
    custom_width = options.get('custom_width', 612)
    custom_height = options.get('custom_height', 792)

    print("=" * 80)
    print("ENHANCED PDF NORMALIZER - WITH CUSTOM SIZES & OCR")
    print("=" * 80)

    # Handle custom page size
    if page_size == 'custom':
        target_width = float(custom_width)
        target_height = float(custom_height)
        if orientation.lower() == 'landscape':
            target_width, target_height = target_height, target_width
        size_name = f"Custom {target_width}x{target_height} pts"
    else:
        page_size_lower = page_size.lower()
        if orientation.lower() == 'landscape':
            page_size_key = f"{page_size_lower}-landscape"
        else:
            page_size_key = page_size_lower

        if page_size_key in PAGE_SIZES:
            target_width, target_height = PAGE_SIZES[page_size_key]
        elif page_size in PAGE_SIZES:
            target_width, target_height = PAGE_SIZES[page_size]
        else:
            target_width, target_height = PAGE_SIZES['A4']

        size_name = f"{page_size.upper()} {orientation}"

    doc = fitz.open(input_path)
    total_pages = len(doc)

    print(f"\nInput: {os.path.basename(input_path)}")
    print(f"Total pages: {total_pages}")
    print(f"Target size: {size_name} ({int(target_width)}x{int(target_height)} pts)")
    print(f"OCR enabled: {add_ocr}")

    output_doc = fitz.open()

    print("\nProcessing pages...")
    print("-" * 80)

    pages_with_ocr = 0
    pages_with_text = 0

    for page_num in range(total_pages):
        source_page = doc.load_page(page_num)

        original_rotation = source_page.rotation
        page_rect = source_page.rect

        has_text = has_text_layer(source_page)

        new_page = output_doc.new_page(width=target_width, height=target_height)

        if original_rotation != 0:
            source_page.set_rotation(0)
            derotated_rect = source_page.rect
        else:
            derotated_rect = page_rect

        if original_rotation in [90, 270]:
            content_width = derotated_rect.height
            content_height = derotated_rect.width

            scale_x = target_width / content_width
            scale_y = target_height / content_height
            scale = min(scale_x, scale_y)

            scaled_width = content_width * scale
            scaled_height = content_height * scale
            x_offset = (target_width - scaled_width) / 2
            y_offset = (target_height - scaled_height) / 2

            target_rect = fitz.Rect(
                x_offset,
                y_offset,
                x_offset + scaled_width,
                y_offset + scaled_height
            )

            new_page.show_pdf_page(target_rect, doc, page_num, rotate=90)

        else:
            scale_x = target_width / derotated_rect.width
            scale_y = target_height / derotated_rect.height
            scale = min(scale_x, scale_y)

            scaled_width = derotated_rect.width * scale
            scaled_height = derotated_rect.height * scale
            x_offset = (target_width - scaled_width) / 2
            y_offset = (target_height - scaled_height) / 2

            target_rect = fitz.Rect(
                x_offset,
                y_offset,
                x_offset + scaled_width,
                y_offset + scaled_height
            )

            new_page.show_pdf_page(target_rect, doc, page_num)

        if add_ocr and (force_ocr or not has_text):
            if page_num < 3 or (not has_text and pages_with_ocr < 5):
                print(f"  Page {page_num + 1}: Performing OCR... ", end='')

            ocr_text = perform_ocr_on_page(source_page)
            if ocr_text:
                add_text_layer_ocr(new_page, ocr_text)
                pages_with_ocr += 1
                if page_num < 3 or pages_with_ocr <= 5:
                    print(f"✓ ({len(ocr_text)} chars)")
            else:
                if page_num < 3:
                    print("⚠ No text detected")

        elif has_text:
            pages_with_text += 1
            if page_num < 3:
                print(f"  Page {page_num + 1}: Text layer present ✓")
        else:
            if page_num < 3:
                print(f"  Page {page_num + 1}: No text (OCR disabled)")

    doc.close()

    print("\n" + "=" * 80)
    print(f"Saving normalized PDF...")
    output_doc.save(output_path, garbage=4, deflate=True)
    output_doc.close()

    print(f"\n✅ Successfully normalized {total_pages} pages!")
    print(f"📄 All pages now: {int(target_width)} x {int(target_height)} pts ({size_name})")
    if add_ocr:
        print(f"🔍 OCR performed on: {pages_with_ocr} pages")
        print(f"📝 Text already present: {pages_with_text} pages")
        print(f"🔎 Total searchable pages: {pages_with_ocr + pages_with_text}")
    print(f"💾 Output: {output_path}")
    print("=" * 80)

    return {
        'total_pages': total_pages,
        'pages_with_ocr': pages_with_ocr,
        'pages_with_text': pages_with_text,
        'target_size': size_name
    }


# ============================================================================
# COMPRESSION FUNCTIONS
# ============================================================================

def create_output_filename(original_filename, suffix="compressed"):
    """
    Create output filename with original name + suffix.
    Example: invoice.pdf -> invoice_compressed.pdf
    """
    name_without_ext = os.path.splitext(original_filename)[0]
    return f"{name_without_ext}_{suffix}.pdf"


def compress_pdf_smart(input_path, output_path, original_filename, options=None):
    """
    IMPROVED: Smart compression that won't increase file size.
    """
    options = options or {}
    compression_level = options.get('compression_level', 'medium')

    if compression_level == 'low':
        image_quality = options.get('image_quality', 95)
        target_dpi = options.get('target_dpi', 200)
        deflate = False
    elif compression_level == 'high':
        image_quality = options.get('image_quality', 75)
        target_dpi = options.get('target_dpi', 120)
        deflate = True
    else:
        image_quality = options.get('image_quality', 85)
        target_dpi = options.get('target_dpi', 150)
        deflate = True

    downsample = options.get('downsample_images', True)

    print("=" * 80)
    print("SMART PDF COMPRESSION")
    print("=" * 80)
    print(f"\nInput: {os.path.basename(input_path)}")

    original_size = os.path.getsize(input_path)
    original_size_mb = original_size / (1024 * 1024)
    print(f"Original size: {original_size_mb:.2f} MB")

    if original_size_mb < 0.5:
        print("⚠️  Small file detected - using minimal compression")
        image_quality = max(image_quality, 90)
        target_dpi = max(target_dpi, 200)
        deflate = False
    elif original_size_mb < 2.0:
        print("⚠️  Medium-small file detected - using careful compression")
        image_quality = max(image_quality, 85)
        target_dpi = max(target_dpi, 150)

    print(f"\nCompression level: {compression_level.upper()}")
    print(f"Image quality: {image_quality}%")
    print(f"Target DPI: {target_dpi}")
    print(f"Downsample images: {downsample}")
    print(f"Deflate compression: {deflate}")

    doc = fitz.open(input_path)
    total_pages = len(doc)

    print(f"\nProcessing {total_pages} pages...")
    print("-" * 80)

    images_processed = 0
    images_downsampled = 0
    images_skipped = 0

    for page_num in range(total_pages):
        page = doc.load_page(page_num)

        image_list = page.get_images(full=True)

        if image_list:
            if page_num < 3:
                print(f"  Page {page_num + 1}: {len(image_list)} image(s)")

            for img_index, img_info in enumerate(image_list):
                xref = img_info[0]

                try:
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    original_img_size = len(image_bytes)

                    img = Image.open(io.BytesIO(image_bytes))
                    original_width, original_height = img.size

                    current_dpi = original_width / 8.5

                    if original_width < 100 or original_height < 100:
                        images_skipped += 1
                        continue

                    should_resize = downsample and current_dpi > target_dpi

                    if should_resize:
                        scale_factor = target_dpi / current_dpi
                        new_width = int(original_width * scale_factor)
                        new_height = int(original_height * scale_factor)

                        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                        images_downsampled += 1

                        if page_num < 3 and img_index < 2:
                            print(
                                f"      Image {img_index + 1}: {original_width}x{original_height} → {new_width}x{new_height}")

                    img_output = io.BytesIO()

                    if img.mode == 'RGBA':
                        img = img.convert('RGB')

                    img.save(img_output, format='JPEG', quality=image_quality, optimize=True)
                    img_bytes = img_output.getvalue()

                    if len(img_bytes) < original_img_size:
                        page.replace_image(xref, stream=img_bytes)
                        images_processed += 1
                    else:
                        if page_num < 3:
                            print(f"      Image {img_index + 1}: Skipped (would increase size)")
                        images_skipped += 1

                except Exception as e:
                    if page_num < 3:
                        print(f"      Warning: Could not process image {img_index + 1}: {e}")
                    images_skipped += 1

        elif page_num < 3:
            print(f"  Page {page_num + 1}: No images")

    print("\n" + "-" * 80)
    print(f"Images processed: {images_processed}")
    print(f"Images downsampled: {images_downsampled}")
    print(f"Images skipped: {images_skipped}")

    print(f"\nSaving compressed PDF...")
    temp_output = output_path + ".tmp"

    if deflate:
        doc.save(temp_output, garbage=4, deflate=True, clean=True)
    else:
        doc.save(temp_output, garbage=3, clean=True)

    doc.close()

    compressed_size = os.path.getsize(temp_output)

    if compressed_size >= original_size:
        print("\n⚠️  WARNING: Compression didn't reduce file size!")
        print("   Using original file instead.")
        shutil.copy2(input_path, output_path)
        os.remove(temp_output)
        compressed_size = original_size
        compression_ratio = 0.0
    else:
        os.rename(temp_output, output_path)
        compression_ratio = (1 - compressed_size / original_size) * 100

    print("\n" + "=" * 80)
    print(f"✅ Compression complete!")
    print(f"📄 Original size: {original_size / (1024 * 1024):.2f} MB")
    print(f"📦 Final size: {compressed_size / (1024 * 1024):.2f} MB")

    if compression_ratio > 0:
        print(
            f"💾 Space saved: {(original_size - compressed_size) / (1024 * 1024):.2f} MB ({compression_ratio:.1f}% reduction)")
    else:
        print(f"💡 No compression applied (would have increased size)")

    print(f"💽 Output: {output_path}")
    print("=" * 80)

    return {
        'original_size': original_size,
        'compressed_size': compressed_size,
        'compression_ratio': compression_ratio,
        'images_processed': images_processed,
        'images_downsampled': images_downsampled,
        'images_skipped': images_skipped
    }


def compress_batch(file_paths, filenames, options=None):
    """
    Compress multiple PDF files and create a zip archive.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"compressed_pdfs_{timestamp}.zip"
    zip_path = os.path.join(tempfile.gettempdir(), zip_filename)

    results = []
    compressed_files = []

    print("\n" + "=" * 80)
    print(f"BATCH COMPRESSION - {len(file_paths)} FILES")
    print("=" * 80 + "\n")

    for i, (file_path, original_filename) in enumerate(zip(file_paths, filenames), 1):
        print(f"\n[{i}/{len(file_paths)}] Processing: {original_filename}")
        print("-" * 80)

        try:
            output_filename = create_output_filename(original_filename)
            output_path = os.path.join(tempfile.gettempdir(), output_filename)

            stats = compress_pdf_smart(file_path, output_path, original_filename, options)

            compressed_files.append({
                'path': output_path,
                'filename': output_filename
            })

            results.append({
                'filename': original_filename,
                'output_filename': output_filename,
                'success': True,
                'stats': stats
            })

        except Exception as e:
            print(f"\n❌ Error processing {original_filename}: {e}")
            results.append({
                'filename': original_filename,
                'success': False,
                'error': str(e)
            })

    print("\n" + "=" * 80)
    print("Creating ZIP archive...")
    print("-" * 80)

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_info in compressed_files:
            zipf.write(file_info['path'], file_info['filename'])
            print(f"  ✓ Added: {file_info['filename']}")

    print("\n✅ ZIP archive created!")
    print(f"📦 Location: {zip_path}")
    print(f"📊 Total files: {len(compressed_files)}/{len(file_paths)}")
    print("=" * 80 + "\n")

    for file_info in compressed_files:
        try:
            os.remove(file_info['path'])
        except:
            pass

    return {
        'zip_path': zip_path,
        'zip_filename': zip_filename,
        'results': results,
        'total_files': len(file_paths),
        'successful': len(compressed_files),
        'failed': len(file_paths) - len(compressed_files)
    }


# ============================================================================
# BATCH NORMALIZE FUNCTION
# ============================================================================

def normalize_batch(file_paths, filenames, options=None):
    """
    Normalize multiple PDF files and create a zip archive.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"normalized_pdfs_{timestamp}.zip"
    zip_path = os.path.join(tempfile.gettempdir(), zip_filename)

    results = []
    normalized_files = []

    print("\n" + "=" * 80)
    print(f"BATCH NORMALIZATION - {len(file_paths)} FILES")
    print("=" * 80 + "\n")

    for i, (file_path, original_filename) in enumerate(zip(file_paths, filenames), 1):
        print(f"\n[{i}/{len(file_paths)}] Processing: {original_filename}")
        print("-" * 80)

        try:
            output_filename = create_output_filename(original_filename, 'normalized')
            output_path = os.path.join(tempfile.gettempdir(), output_filename)

            stats = normalize_pdf_enhanced(file_path, output_path, options)

            normalized_files.append({
                'path': output_path,
                'filename': output_filename
            })

            results.append({
                'filename': original_filename,
                'output_filename': output_filename,
                'success': True,
                'stats': stats
            })

        except Exception as e:
            print(f"\n❌ Error processing {original_filename}: {e}")
            results.append({
                'filename': original_filename,
                'success': False,
                'error': str(e)
            })

    print("\n" + "=" * 80)
    print("Creating ZIP archive...")
    print("-" * 80)

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_info in normalized_files:
            zipf.write(file_info['path'], file_info['filename'])
            print(f"  ✓ Added: {file_info['filename']}")

    print("\n✅ ZIP archive created!")
    print(f"📦 Location: {zip_path}")
    print(f"📊 Total files: {len(normalized_files)}/{len(file_paths)}")
    print("=" * 80 + "\n")

    for file_info in normalized_files:
        try:
            os.remove(file_info['path'])
        except:
            pass

    return {
        'zip_path': zip_path,
        'zip_filename': zip_filename,
        'results': results,
        'total_files': len(file_paths),
        'successful': len(normalized_files),
        'failed': len(file_paths) - len(normalized_files)
    }


# ============================================================================
# FLASK ROUTES (Updated with new options)
# ============================================================================

@app.route('/')
def index():
    """Landing page showing all features."""
    return render_template('index.html')


@app.route('/merge')
def merge_page():
    """PDF merge tool page."""
    return render_template('merge.html')


@app.route('/normalize')
def normalize_page():
    """PDF normalize tool page."""
    return render_template('normalize.html')


@app.route('/compress')
def compress_page():
    """PDF compress tool page."""
    return render_template('compress.html')


@app.route('/upload', methods=['POST'])
def upload():
    """Handle file upload - supports single or multiple files."""
    try:
        if 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400

            if not file.filename.lower().endswith('.pdf'):
                return jsonify({'error': 'Only PDF files are allowed'}), 400

            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            return jsonify({
                'success': True,
                'file_path': filepath,
                'filename': filename
            })

        elif 'files' in request.files:
            files = request.files.getlist('files')
            if not files or all(f.filename == '' for f in files):
                return jsonify({'error': 'No files selected'}), 400

            uploaded_files = []
            for file in files:
                if file and file.filename and file.filename.lower().endswith('.pdf'):
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    uploaded_files.append({
                        'path': filepath,
                        'filename': filename
                    })

            if not uploaded_files:
                return jsonify({'error': 'No valid PDF files uploaded'}), 400

            return jsonify({
                'success': True,
                'files': uploaded_files
            })

        else:
            return jsonify({'error': 'No file uploaded'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/merge-pdfs', methods=['POST'])
def merge():
    """Handle PDF merge request with enhanced options."""
    try:
        data = request.json
        file_configs = data.get('files', [])
        options = data.get('options', {})

        if not file_configs:
            return jsonify({'error': 'No files to merge'}), 400

        output_path = merge_pdfs_enhanced(file_configs, options)

        if output_path:
            return jsonify({
                'success': True,
                'download_url': f'/download/{os.path.basename(output_path)}'
            })
        else:
            return jsonify({'error': 'Merge failed'}), 500

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': f'Merge failed: {str(e)}'}), 500


@app.route('/normalize-pdf', methods=['POST'])
def normalize():
    """Handle PDF normalize request with custom page sizes."""
    try:
        data = request.json

        if 'files' in data and isinstance(data['files'], list):
            files_data = data['files']
            options = data.get('options', {})

            if not files_data:
                return jsonify({'error': 'No files provided'}), 400

            file_paths = [f['path'] for f in files_data]
            filenames = [f['filename'] for f in files_data]

            for file_path in file_paths:
                if not os.path.exists(file_path):
                    return jsonify({'error': f'File not found: {file_path}'}), 400

            result = normalize_batch(file_paths, filenames, options)

            return jsonify({
                'success': True,
                'batch': True,
                'download_url': f'/download/{result["zip_filename"]}',
                'results': result['results'],
                'total_files': result['total_files'],
                'successful': result['successful'],
                'failed': result['failed']
            })

        else:
            file_path = data.get('file_path')
            original_filename = data.get('filename', 'document.pdf')
            options = data.get('options', {})

            if not file_path or not os.path.exists(file_path):
                return jsonify({'error': 'File not found'}), 400

            output_filename = create_output_filename(original_filename, 'normalized')
            output_path = os.path.join(tempfile.gettempdir(), output_filename)

            stats = normalize_pdf_enhanced(file_path, output_path, options)

            return jsonify({
                'success': True,
                'batch': False,
                'download_url': f'/download/{output_filename}',
                'output_filename': output_filename,
                'stats': stats
            })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': f'Normalization failed: {str(e)}'}), 500


@app.route('/compress-pdf', methods=['POST'])
def compress():
    """Handle PDF compression request - supports single or batch."""
    try:
        data = request.json

        # Check if it's batch or single file
        if 'files' in data and isinstance(data['files'], list):
            # Batch compression
            files_data = data['files']
            options = data.get('options', {})

            if not files_data:
                return jsonify({'error': 'No files provided'}), 400

            file_paths = [f['path'] for f in files_data]
            filenames = [f['filename'] for f in files_data]

            # Verify all files exist
            for file_path in file_paths:
                if not os.path.exists(file_path):
                    return jsonify({'error': f'File not found: {file_path}'}), 400

            # Compress batch
            result = compress_batch(file_paths, filenames, options)

            return jsonify({
                'success': True,
                'batch': True,
                'download_url': f'/download/{result["zip_filename"]}',
                'results': result['results'],
                'total_files': result['total_files'],
                'successful': result['successful'],
                'failed': result['failed']
            })

        else:
            # Single file compression
            file_path = data.get('file_path')
            original_filename = data.get('filename', 'document.pdf')
            options = data.get('options', {})

            if not file_path or not os.path.exists(file_path):
                return jsonify({'error': 'File not found'}), 400

            # Create output filename with original name
            output_filename = create_output_filename(original_filename)
            output_path = os.path.join(tempfile.gettempdir(), output_filename)

            stats = compress_pdf_smart(file_path, output_path, original_filename, options)

            return jsonify({
                'success': True,
                'batch': False,
                'download_url': f'/download/{output_filename}',
                'output_filename': output_filename,
                'stats': stats
            })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': f'Compression failed: {str(e)}'}), 500


@app.route('/download/<filename>')
def download(filename):
    """Handle file download."""
    filepath = os.path.join(tempfile.gettempdir(), filename)
    if not os.path.exists(filepath):
        return "File not found", 404
    return send_file(filepath, as_attachment=True, download_name=filename, mimetype='application/pdf')


def debug_bookmarks(pdf_doc):
    """Debug function to check current bookmarks in PDF"""
    try:
        toc = pdf_doc.get_toc()
        if toc:
            print("  Current bookmarks in PDF:")
            for item in toc:
                level, title, page = item
                print(f"    Level {level}: '{title}' -> Page {page + 1}")
        else:
            print("  No bookmarks found in PDF")
    except Exception as e:
        print(f"  Could not read bookmarks: {e}")

if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("🔨 PDFFORGE - Professional PDF Tools (ENHANCED)")
    print("=" * 70)
    print("\n🚀 Starting web server...")
    print("\n📱 Open your browser:")
    print("   http://localhost:5000")
    print("\n✨ NEW Enhanced Features:")
    print("   • Smart page number positioning (no conflicts)")
    print("   • OCR text layer addition for scanned PDFs")
    print("   • Automatic bookmarks for merged files")
    print("   • Custom page sizes for normalization")
    print("   • Page number font size customization")
    print("   • Multiple page number positions")
    print("   • Smart PDF compression")
    print("\n⏹️  Press Ctrl+C to stop")
    print("=" * 70 + "\n")

    os.makedirs('templates', exist_ok=True)

    app.run(debug=True, host='0.0.0.0', port=5000)