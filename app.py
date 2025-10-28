"""
PDFForge - Professional PDF Tools Web Application
Landing page + Enhanced Merge (two-line headers, smart scaling) + Enhanced Normalize (with OCR)
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
    'Letter': (612, 792),
    'Legal': (612, 1008),
}


# ============================================================================
# ENHANCED MERGE FUNCTIONS (Two-line headers, Smart Scaling)
# ============================================================================

def has_content_in_header_area(page, threshold_y=60):
    """
    Detect if page has traditional header that needs extra space.
    Returns True: has header (metadata, labels) - needs extra space
    Returns False: no header, content starts from top - can optimize space
    """
    try:
        # Define small top area to detect real headers
        header_rect = fitz.Rect(0, 0, page.rect.width, 40)

        # Check text content
        text = page.get_text("text", clip=header_rect).strip()

        if not text:
            # No text, check for small graphics/lines (header lines)
            drawings = page.get_drawings()
            for drawing in drawings:
                if drawing["rect"].y0 < 40 and drawing["rect"].height < 2:
                    return True
            return False

        # Has text, check characteristics to determine if it's a real header
        lines = text.split('\n')

        # Heuristic rules:
        header_keywords = ['confidential', 'secret', 'internal', 'draft',
                           'proprietary', 'classified', 'restricted']

        # Short text with header keywords
        if len(text) < 100:
            text_lower = text.lower()
            if any(keyword in text_lower for keyword in header_keywords):
                return True

        # Only 1-2 short lines at very top
        if len(lines) <= 2 and all(len(line.strip()) < 50 for line in lines):
            return True

        # Otherwise, consider it main content starting from top
        return False

    except:
        return False


def has_small_top_margin(page, threshold=80):
    """
    Detect if page has very small top margin (content too close to top).
    Returns True if content starts within threshold points from top.
    This requires MORE aggressive scaling to make room for headers.
    """
    try:
        # Check where actual content starts
        text_dict = page.get_text("dict")

        if not text_dict or 'blocks' not in text_dict:
            return False

        # Find the first text block's position
        min_y = float('inf')
        for block in text_dict['blocks']:
            if block.get('type') == 0:  # Text block
                # Get the y-coordinate of the first line
                if 'lines' in block and block['lines']:
                    first_line = block['lines'][0]
                    y_pos = first_line.get('bbox', [0, 0, 0, 0])[1]  # y0 position
                    min_y = min(min_y, y_pos)

        # Also check for graphics/images at the top
        drawings = page.get_drawings()
        for drawing in drawings:
            if drawing["rect"].height > 5:  # Only significant graphics
                min_y = min(min_y, drawing["rect"].y0)

        if min_y < threshold:
            print(f"      → Small top margin detected: content starts at y={min_y:.1f}")
            return True

        return False

    except Exception as e:
        print(f"      Warning: Could not detect top margin - {e}")
        return False


def add_page_number_only(page, page_number, position="top-center", font_size=10):
    """Add only page number to page"""
    page_width = page.rect.width
    page_height = page.rect.height
    page_text = f"{page_number}"
    text_width = fitz.get_text_length(page_text, fontsize=font_size, fontname="helv")

    # Determine coordinates based on position
    if position == "top-center":
        x = (page_width - text_width) / 2
        y = 25
    elif position == "bottom-center":
        x = (page_width - text_width) / 2
        y = page_height - 25
    else:
        x = (page_width - text_width) / 2
        y = 25

    # Add semi-transparent white background
    bg_padding = 5
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
        fontname="helv"
    )


def add_header_and_footer(page, header_notes, page_number, page_width,
                          page_height, add_footer_line, add_page_numbers):
    """Add header (two lines) and optional footer line"""
    margin = 30
    font_size = 10

    # === Header ===
    header_y = 25
    line_height = 12

    # Top left - first line
    page.insert_text(
        (margin, header_y),
        header_notes[0],
        fontsize=font_size,
        fontname="helv"
    )

    # Top left - second line
    page.insert_text(
        (margin, header_y + line_height),
        header_notes[1],
        fontsize=font_size,
        fontname="helv"
    )

    # Page number (centered) - optional
    if add_page_numbers:
        page_text = f"{page_number}"
        text_width = fitz.get_text_length(page_text, fontsize=font_size, fontname="helv")
        page.insert_text(
            ((page_width - text_width) / 2, header_y),
            page_text,
            fontsize=font_size,
            fontname="helv"
        )

    # Header separator line
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
                         add_footer_line, smart_spacing, add_page_numbers):
    """Process single page: scale, position, and add header/footer"""
    # Create new letter-size page
    new_page = output_pdf.new_page(width=letter_width, height=letter_height)

    # Get source page
    src_page = source_pdf[page_num]
    src_rect = src_page.rect

    # Smart header space detection with top margin check
    if smart_spacing:
        has_header_content = has_content_in_header_area(src_page)
        has_tiny_margin = has_small_top_margin(src_page, threshold=80)

        # Determine scale factor based on detection
        if has_tiny_margin:
            # VERY aggressive scaling for pages with content too close to top
            current_scale_factor = 0.88  # More aggressive!
            header_space = 75  # More space for breathing room!
            content_offset = 0
            status_msg = "TINY top margin - very aggressive scale 0.88"
        elif has_header_content:
            # Standard scaling for pages with existing headers
            current_scale_factor = scale_factor
            header_space = 50
            content_offset = 0
            status_msg = f"has header, scale {current_scale_factor}"
        else:
            # Optimized scaling for clean pages
            current_scale_factor = scale_factor_optimized
            header_space = 50
            content_offset = 30
            status_msg = f"no header-optimized, scale {current_scale_factor}"
    else:
        header_space = 50
        content_offset = 0
        current_scale_factor = scale_factor
        status_msg = "standard"

    print(
        f"  Processing page {final_page_num}, original size: {src_rect.width:.1f} x {src_rect.height:.1f} [{status_msg}]")

    # Calculate scaling and position
    footer_space = 30 if add_footer_line else 20
    margin = 20

    available_width = letter_width - 2 * margin
    available_height = letter_height - header_space - footer_space + content_offset

    # Calculate best scale ratio
    scale_x = available_width / src_rect.width
    scale_y = available_height / src_rect.height
    scale = min(scale_x, scale_y, current_scale_factor)

    # Calculate scaled dimensions
    scaled_width = src_rect.width * scale
    scaled_height = src_rect.height * scale

    # Calculate centered position
    x_offset = (letter_width - scaled_width) / 2
    y_offset = header_space + (available_height - scaled_height) / 2 - content_offset

    # Define target rectangle
    target_rect = fitz.Rect(
        x_offset,
        y_offset,
        x_offset + scaled_width,
        y_offset + scaled_height
    )

    # Insert source page content
    new_page.show_pdf_page(target_rect, source_pdf, page_num)

    # Add header and footer
    add_header_and_footer(new_page, header_notes, final_page_num,
                          letter_width, letter_height, add_footer_line, add_page_numbers)


def copy_page_directly(output_pdf, source_pdf, page_num, page_number, add_page_numbers):
    """Copy page directly without transformation, optionally add page number"""
    # Directly insert original page
    output_pdf.insert_pdf(source_pdf, from_page=page_num, to_page=page_num)

    # If needed, add page number on original page
    if add_page_numbers:
        new_page = output_pdf[-1]
        add_page_number_only(new_page, page_number)

    print(f"  Copied page {page_number} (kept as-is)")


def merge_pdfs_enhanced(file_configs, options=None):
    """
    Enhanced merge PDFs with two-line headers and smart scaling.

    Args:
        file_configs: List of dicts with keys:
            - path: PDF file path
            - name: filename
            - header_line1: first header line (optional)
            - header_line2: second header line (optional)
            - transform: True/False (add headers or not)
        options: Dict with keys:
            - add_headers: Enable header mode (True/False)
            - page_start: Starting page number (default 1)
            - output_filename: Custom output filename (optional)
            - scale_factor: Scale for pages with headers (default 0.96)
            - scale_factor_optimized: Scale for pages without headers (default 0.99)
            - add_footer_line: Add footer separator line (default False)
            - smart_spacing: Enable smart spacing detection (default True)
            - add_page_numbers: Add page numbers (default True)
    """
    options = options or {}
    add_headers = options.get('add_headers', False)
    page_start = options.get('page_start', 1)  # NEW: starting page number
    custom_filename = options.get('output_filename', '')  # NEW: custom filename
    scale_factor = options.get('scale_factor', 0.96)
    scale_factor_optimized = options.get('scale_factor_optimized', 0.99)
    add_footer_line = options.get('add_footer_line', False)
    smart_spacing = options.get('smart_spacing', True)
    add_page_numbers = options.get('add_page_numbers', True)

    output_pdf = fitz.open()
    total_page_number = page_start  # Start from specified page number
    total_pages_processed = 0

    print("=" * 80)
    print("ENHANCED PDF MERGE - Two-line headers, Smart Scaling")
    print("=" * 80)
    print(f"Add headers: {add_headers}")
    print(f"Smart spacing: {smart_spacing}")
    print(f"Page numbers: {add_page_numbers}")
    print(f"Starting page number: {page_start}")
    print()

    # NEW: Check if all headers are empty - if so, disable header mode
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

        # Determine if this file should be transformed
        if add_headers:
            header_line1 = config.get('header_line1', '')
            header_line2 = config.get('header_line2', '')
            header_notes = [header_line1, header_line2]
            should_transform = True
        else:
            should_transform = False

        pdf = fitz.open(file_path)
        page_count = len(pdf)

        transform_status = "Transform (add headers)" if should_transform else "Direct merge"
        print(f"Processing PDF {idx + 1}: {os.path.basename(file_path)} ({page_count} pages) - {transform_status}")

        for page_num in range(page_count):
            if should_transform:
                # Transform: add header, scale
                process_and_add_page(
                    output_pdf, pdf, page_num,
                    header_notes, total_page_number,
                    LETTER_WIDTH, LETTER_HEIGHT,
                    scale_factor, scale_factor_optimized,
                    add_footer_line, smart_spacing, add_page_numbers
                )
            else:
                # No transform: copy directly
                copy_page_directly(
                    output_pdf, pdf, page_num,
                    total_page_number, add_page_numbers
                )

            total_page_number += 1

        pdf.close()
        total_pages_processed += page_count

    # Save output
    if total_pages_processed > 0:
        # NEW: Use custom filename or default
        if custom_filename:
            # Use provided custom filename
            if not custom_filename.endswith('.pdf'):
                custom_filename += '.pdf'
            output_filename = custom_filename
        else:
            # Use first file's name as default
            first_filename = os.path.basename(file_configs[0]['name'])
            output_filename = create_output_filename(first_filename, 'merged')
        
        output_path = os.path.join(tempfile.gettempdir(), output_filename)
        output_pdf.save(output_path, garbage=4, deflate=True)
        output_pdf.close()

        print("\n" + "=" * 80)
        print(f"✓ Merge complete!")
        print(f"✓ Processed {len(file_configs)} PDF files")
        print(f"✓ Total {total_pages_processed} pages")
        print(f"✓ Output: {output_path}")
        print("=" * 80)
        return output_path
    else:
        print("\n✗ Error: No pages processed successfully")
        return None


# ============================================================================
# ENHANCED NORMALIZE FUNCTIONS (with OCR)
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
    """Enhanced normalize PDF to standard page size with optional OCR."""
    options = options or {}
    page_size = options.get('page_size', 'letter')
    orientation = options.get('orientation', 'portrait')
    add_ocr = options.get('add_ocr', False)
    force_ocr = options.get('force_ocr', False)

    print("=" * 80)
    print("ENHANCED PDF NORMALIZER - WITH OCR SUPPORT")
    print("=" * 80)

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
# FLASK ROUTES
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


@app.route('/upload', methods=['POST'])
def upload():
    """Handle file upload - supports single or multiple files."""
    try:
        # Handle single file
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
        
        # Handle multiple files
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
    """Handle PDF merge request with two-line headers."""
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
    """Handle PDF normalize request - supports single or batch."""
    try:
        data = request.json
        
        # Check if it's batch or single file
        if 'files' in data and isinstance(data['files'], list):
            # Batch normalization
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
            
            # Normalize batch
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
            # Single file normalization
            file_path = data.get('file_path')
            original_filename = data.get('filename', 'document.pdf')
            options = data.get('options', {})

            if not file_path or not os.path.exists(file_path):
                return jsonify({'error': 'File not found'}), 400

            # Create output filename with original name
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


def normalize_batch(file_paths, filenames, options=None):
    """
    Normalize multiple PDF files and create a zip archive.
    
    Args:
        file_paths: List of input file paths
        filenames: List of original filenames
        options: Normalization options dict
    
    Returns:
        Path to zip file containing all normalized PDFs
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
            # Create output filename
            output_filename = create_output_filename(original_filename, 'normalized')
            output_path = os.path.join(tempfile.gettempdir(), output_filename)
            
            # Normalize the PDF
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
    
    # Create zip file
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
    
    # Clean up individual normalized files
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





@app.route('/download/<filename>')
def download(filename):
    """Handle file download."""
    filepath = os.path.join(tempfile.gettempdir(), filename)
    if not os.path.exists(filepath):
        return "File not found", 404
    return send_file(filepath, as_attachment=True, download_name=filename, mimetype='application/pdf')


# ============================================================================
# IMPROVED PDF COMPRESSION FUNCTIONS
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
    
    Args:
        input_path: Input PDF path
        output_path: Output PDF path  
        original_filename: Original filename to use in output
        options: Dict with keys:
            - compression_level: 'low', 'medium', 'high' (default: 'medium')
            - image_quality: 1-100 (default: 85 for medium)
            - downsample_images: True/False (default: True)
            - target_dpi: DPI for images (default: 150 for medium)
    
    Returns:
        Dict with compression stats
    """
    options = options or {}
    compression_level = options.get('compression_level', 'medium')
    
    # Set compression parameters based on level
    if compression_level == 'low':
        image_quality = options.get('image_quality', 95)
        target_dpi = options.get('target_dpi', 200)
        deflate = False
    elif compression_level == 'high':
        image_quality = options.get('image_quality', 75)
        target_dpi = options.get('target_dpi', 120)
        deflate = True
    else:  # medium (default)
        image_quality = options.get('image_quality', 85)
        target_dpi = options.get('target_dpi', 150)
        deflate = True
    
    downsample = options.get('downsample_images', True)
    
    print("=" * 80)
    print("SMART PDF COMPRESSION")
    print("=" * 80)
    print(f"\nInput: {os.path.basename(input_path)}")
    
    # Get original file size
    original_size = os.path.getsize(input_path)
    original_size_mb = original_size / (1024*1024)
    print(f"Original size: {original_size_mb:.2f} MB")
    
    # For very small files, use lighter compression to avoid size increase
    if original_size_mb < 0.5:  # Less than 500KB
        print("⚠️  Small file detected - using minimal compression")
        image_quality = max(image_quality, 90)
        target_dpi = max(target_dpi, 200)
        deflate = False
    elif original_size_mb < 2.0:  # Less than 2MB
        print("⚠️  Medium-small file detected - using careful compression")
        image_quality = max(image_quality, 85)
        target_dpi = max(target_dpi, 150)
    
    print(f"\nCompression level: {compression_level.upper()}")
    print(f"Image quality: {image_quality}%")
    print(f"Target DPI: {target_dpi}")
    print(f"Downsample images: {downsample}")
    print(f"Deflate compression: {deflate}")
    
    # Open PDF
    doc = fitz.open(input_path)
    total_pages = len(doc)
    
    print(f"\nProcessing {total_pages} pages...")
    print("-" * 80)
    
    images_processed = 0
    images_downsampled = 0
    images_skipped = 0
    
    # Process each page
    for page_num in range(total_pages):
        page = doc.load_page(page_num)
        
        # Get all images on the page
        image_list = page.get_images(full=True)
        
        if image_list:
            if page_num < 3:  # Show details for first 3 pages
                print(f"  Page {page_num + 1}: {len(image_list)} image(s)")
            
            for img_index, img_info in enumerate(image_list):
                xref = img_info[0]
                
                try:
                    # Get image properties
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    original_img_size = len(image_bytes)
                    
                    # Convert to PIL Image
                    img = Image.open(io.BytesIO(image_bytes))
                    original_width, original_height = img.size
                    
                    # Calculate current DPI (estimate)
                    current_dpi = original_width / 8.5
                    
                    # Skip very small images (likely logos/icons)
                    if original_width < 100 or original_height < 100:
                        images_skipped += 1
                        continue
                    
                    # Downsample if needed
                    should_resize = downsample and current_dpi > target_dpi
                    
                    if should_resize:
                        scale_factor = target_dpi / current_dpi
                        new_width = int(original_width * scale_factor)
                        new_height = int(original_height * scale_factor)
                        
                        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                        images_downsampled += 1
                        
                        if page_num < 3 and img_index < 2:
                            print(f"      Image {img_index + 1}: {original_width}x{original_height} → {new_width}x{new_height}")
                    
                    # Compress image
                    img_output = io.BytesIO()
                    
                    # Save with compression
                    if img.mode == 'RGBA':
                        img = img.convert('RGB')
                    
                    img.save(img_output, format='JPEG', quality=image_quality, optimize=True)
                    img_bytes = img_output.getvalue()
                    
                    # Only replace if compression actually reduced size
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
    
    # Save with compression to temporary file first
    print(f"\nSaving compressed PDF...")
    temp_output = output_path + ".tmp"
    
    if deflate:
        doc.save(temp_output, garbage=4, deflate=True, clean=True)
    else:
        doc.save(temp_output, garbage=3, clean=True)
    
    doc.close()
    
    # Check if compression actually reduced file size
    compressed_size = os.path.getsize(temp_output)
    
    if compressed_size >= original_size:
        # Compression didn't help or made it worse - use original
        print("\n⚠️  WARNING: Compression didn't reduce file size!")
        print("   Using original file instead.")
        shutil.copy2(input_path, output_path)
        os.remove(temp_output)
        compressed_size = original_size
        compression_ratio = 0.0
    else:
        # Compression worked - use compressed file
        os.rename(temp_output, output_path)
        compression_ratio = (1 - compressed_size / original_size) * 100
    
    print("\n" + "=" * 80)
    print(f"✅ Compression complete!")
    print(f"📄 Original size: {original_size / (1024*1024):.2f} MB")
    print(f"📦 Final size: {compressed_size / (1024*1024):.2f} MB")
    
    if compression_ratio > 0:
        print(f"💾 Space saved: {(original_size - compressed_size) / (1024*1024):.2f} MB ({compression_ratio:.1f}% reduction)")
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
    
    Args:
        file_paths: List of input file paths
        filenames: List of original filenames
        options: Compression options dict
    
    Returns:
        Path to zip file containing all compressed PDFs
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
            # Create output filename
            output_filename = create_output_filename(original_filename)
            output_path = os.path.join(tempfile.gettempdir(), output_filename)
            
            # Compress the PDF
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
    
    # Create zip file
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
    
    # Clean up individual compressed files
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
# FLASK ROUTES (continued)
# ============================================================================

@app.route('/compress')
def compress_page():
    """PDF compress tool page."""
    return render_template('compress.html')


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


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("🔨 PDFFORGE - Professional PDF Tools (IMPROVED)")
    print("=" * 70)
    print("\n🚀 Starting web server...")
    print("\n📱 Open your browser:")
    print("   http://localhost:5000")
    print("\n✨ Available Features:")
    print("   • PDF Merge (enhanced with two-line headers)")
    print("   • Smart scaling (detects page headers)")
    print("   • PDF Normalize (enhanced with OCR support)")
    print("   • PDF Compress (IMPROVED!) ⭐⭐⭐")
    print("\n🎉 NEW Compression Improvements:")
    print("   ✓ Smart compression (never increases file size)")
    print("   ✓ Original filename preservation + timestamp")
    print("   ✓ Batch processing (compress multiple files at once)")
    print("   ✓ ZIP download for batch operations")
    print("   ✓ Adaptive compression for small files")
    print("\n💡 Tips:")
    print("   • Upload single or multiple PDFs")
    print("   • Small files won't get bigger")
    print("   • Output names keep original filename")
    print("   • Batch download as convenient ZIP")
    print("\n⏹️  Press Ctrl+C to stop")
    print("=" * 70 + "\n")

    os.makedirs('templates', exist_ok=True)

    app.run(debug=True, host='0.0.0.0', port=5000)