"""
TOC Routes - HTTP Request Handlers
Uses PDFForge file management utilities
"""

import logging
import json
import os
from pathlib import Path

from flask import Blueprint, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename

from ..services.toc_service import TOCService
from ..utils.file_manager import get_file_manager
from ..utils.file_utils import save_uploaded_file
from ..utils.validation import allowed_file

logger = logging.getLogger(__name__)

# Create blueprint
toc_bp = Blueprint('toc', __name__, url_prefix='/toc')


def get_toc_service():
    """Get TOC service instance."""
    return TOCService()


@toc_bp.route('/')
def toc_page():
    """Render TOC management page."""
    return render_template('toc.html')


@toc_bp.route('/extract', methods=['POST'])
def extract_bookmarks():
    """
    Extract bookmarks from uploaded PDF.

    Returns:
        JSON with bookmarks and page count
    """
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400

        pdf_file = request.files['file']

        if pdf_file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        if not allowed_file(pdf_file.filename):
            return jsonify({'success': False, 'error': 'File must be a PDF'}), 400

        # Save file using file_utils
        file_path = save_uploaded_file(pdf_file)
        logger.info(f"Saved file for bookmark extraction: {file_path}")

        # Extract bookmarks
        toc_service = get_toc_service()
        result = toc_service.extract_bookmarks_from_file(file_path, pdf_file.filename)

        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.exception("Extract bookmarks error")
        return jsonify({'success': False, 'error': str(e)}), 500


@toc_bp.route('/generate', methods=['POST'])
def generate_toc():
    """Generate TOC with bookmarks"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'})

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})

        # Get form data
        bookmarks_json = request.form.get('bookmarks')
        toc_style_json = request.form.get('toc_style', '{}')

        if not bookmarks_json:
            return jsonify({'success': False, 'error': 'No bookmarks provided'})

        import json
        try:
            bookmarks_data = json.loads(bookmarks_json)
            toc_style_config = json.loads(toc_style_json)
        except json.JSONDecodeError as e:
            return jsonify({'success': False, 'error': f'Invalid JSON: {e}'})

        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        temp_dir = "temp"
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, f"upload_{filename}")
        file.save(temp_path)

        # Generate TOC
        result = get_toc_service().add_toc_to_file(
            temp_path,
            filename,
            bookmarks_data,
            toc_style_config
        )

        if result['success']:
            # Use component-specific download URL
            download_url = f"/download/component/toc/{result['file_id']}"
            return jsonify({
                'success': True,
                'download_url': download_url,
                'filename': result['filename'],
                'file_id': result['file_id']
            })
        else:
            return jsonify(result)

    except Exception as e:
        logger.error(f"Error generating TOC: {e}")
        return jsonify({'success': False, 'error': str(e)})


@toc_bp.route('/update-bookmarks', methods=['POST'])
def update_bookmarks():
    """
    Update PDF bookmarks without generating TOC page.

    Expects:
        - file: PDF file
        - bookmarks: JSON string of bookmark list

    Returns:
        JSON with file_id for download
    """
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400

        pdf_file = request.files['file']

        if pdf_file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        if not allowed_file(pdf_file.filename):
            return jsonify({'success': False, 'error': 'File must be a PDF'}), 400

        # Get bookmarks from form data
        try:
            bookmarks_json = request.form.get('bookmarks', '[]')
            bookmarks_data = json.loads(bookmarks_json)

            if not bookmarks_data:
                return jsonify({'success': False, 'error': 'No bookmarks provided'}), 400
        except json.JSONDecodeError:
            return jsonify({'success': False, 'error': 'Invalid bookmarks format'}), 400

        # Save uploaded file
        input_file_path = save_uploaded_file(pdf_file)
        logger.info(f"Saved input file: {input_file_path}")

        # Update bookmarks
        toc_service = get_toc_service()
        result = toc_service.update_pdf_bookmarks_in_file(
            input_file_path,
            pdf_file.filename,
            bookmarks_data
        )

        if result['success']:
            # Return file_id for download
            response_data = {
                'success': True,
                'download_url': f"/download/component/toc/{result['file_id']}",
                'output_filename': result['filename'],
                'file_id': result['file_id'],
                'bookmark_count': result.get('bookmark_count', 0)
            }
            return jsonify(response_data), 200
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.exception("Update bookmarks error")
        return jsonify({'success': False, 'error': str(e)}), 500


@toc_bp.route('/download/<file_id>')
def download_toc(file_id):
    """Download TOC-generated file"""
    try:
        file_manager = get_file_manager("toc")

        # Look for file in toc directory
        toc_dir = file_manager.get_component_dir()
        file_path = None

        # Search for file with the file_id in the filename
        for file_in_dir in toc_dir.glob(f"*{file_id}*"):
            if file_in_dir.is_file():
                file_path = file_in_dir
                break

        if not file_path or not file_path.exists():
            logger.error(f"File not found for ID: {file_id}")
            return jsonify({"success": False, "error": f"File not found: {file_id}"}), 404

        logger.info(f"Serving file from: {file_path}")
        return send_file(str(file_path), as_attachment=True, download_name=file_path.name)

    except Exception as e:
        logger.error(f"Download error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@toc_bp.route('/cleanup/<file_id>', methods=['POST'])
def cleanup_file(file_id):
    """Clean up temporary files"""
    try:
        file_manager = get_file_manager("toc")
        files_cleaned = 0

        # Clean up from toc directory
        toc_dir = file_manager.get_component_dir()
        for file_path in toc_dir.glob(f"*{file_id}*"):
            if file_path.is_file():
                file_path.unlink()
                files_cleaned += 1
                logger.info(f"Cleaned up: {file_path}")

        return jsonify({
            'success': True,
            'message': f'Cleaned up {files_cleaned} files',
            'files_cleaned': files_cleaned
        })

    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@toc_bp.route('/test')
def test_endpoint():
    """Test endpoint to verify routes are working"""
    return jsonify({
        'success': True,
        'message': 'TOC routes are working!',
        'component': 'toc',
        'test': True
    }), 200


@toc_bp.route('/debug/paths')
def debug_paths():
    """Debug file paths for TOC component"""
    file_manager = get_file_manager("toc")

    debug_info = {
        'base_data_dir': str(file_manager.base_data_dir),  # FIXED: base_data_dir
        'uploads_dir': str(file_manager.uploads_dir),
        'downloads_dir': str(file_manager.downloads_dir),
        'toc_dir': str(file_manager.toc_dir),
        'component_dir': str(file_manager.get_component_dir()),
        'downloads_dir_exists': file_manager.downloads_dir.exists(),
        'toc_dir_exists': file_manager.toc_dir.exists(),
        'files_in_downloads': [],
        'files_in_toc': []
    }

    if file_manager.downloads_dir.exists():
        debug_info['files_in_downloads'] = [f.name for f in file_manager.downloads_dir.glob('*') if f.is_file()]

    if file_manager.toc_dir.exists():
        debug_info['files_in_toc'] = [f.name for f in file_manager.toc_dir.glob('*') if f.is_file()]

    return jsonify(debug_info)