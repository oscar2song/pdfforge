"""
Download Routes
"""

import os
from flask import Blueprint, send_file, current_app, abort, jsonify

download_bp = Blueprint('download', __name__)


@download_bp.route('/download/<filename>')
def download_file(filename):
    """Download a processed file"""
    current_app.logger.info("🎯 MAIN DOWNLOAD ROUTE EXECUTING!")
    current_app.logger.info(f"Requested filename: {filename}")

    try:
        # Security check - prevent directory traversal
        if '..' in filename or filename.startswith('/'):
            current_app.logger.error("Security check failed")
            abort(400, "Invalid filename")

        # Use the current working directory + downloads
        downloads_folder = os.path.join(os.getcwd(), 'downloads')
        file_path = os.path.join(downloads_folder, filename)

        current_app.logger.info(f"Looking for file at: {file_path}")
        current_app.logger.info(f"Downloads folder exists: {os.path.exists(downloads_folder)}")

        if os.path.exists(downloads_folder):
            files = os.listdir(downloads_folder)
            current_app.logger.info(f"Files in downloads folder: {files}")

        # Check if file exists
        if not os.path.exists(file_path):
            current_app.logger.error(f"File not found: {file_path}")
            abort(404, f"File not found: {filename}")

        current_app.logger.info(f"✅ File found, sending: {file_path}")

        # Send file
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        current_app.logger.error(f"Download error: {str(e)}")
        abort(500, "Download failed")

# Test route to verify the simple approach works
@download_bp.route('/test-simple/<filename>')
def test_simple_download(filename):
    """Test the simple download approach"""
    try:
        downloads_folder = os.path.join(os.getcwd(), 'downloads')
        file_path = os.path.join(downloads_folder, filename)

        current_app.logger.info(f"Test simple - File path: {file_path}")
        current_app.logger.info(f"Test simple - File exists: {os.path.exists(file_path)}")

        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True, download_name=filename)
        else:
            return f"File not found at: {file_path}", 404

    except Exception as e:
        return f"Error: {str(e)}", 500


@download_bp.route('/debug/current-state')
def debug_current_state():
    """Get the current state of downloads folder and paths"""
    downloads_folder = os.path.join(os.getcwd(), 'downloads')

    result = {
        'current_working_directory': os.getcwd(),
        'downloads_folder_path': downloads_folder,
        'downloads_folder_exists': os.path.exists(downloads_folder),
    }

    if os.path.exists(downloads_folder):
        files = os.listdir(downloads_folder)
        result['files'] = files
        result['file_details'] = {}

        for file in files:
            file_path = os.path.join(downloads_folder, file)
            result['file_details'][file] = {
                'size': os.path.getsize(file_path),
                'readable': os.access(file_path, os.R_OK),
                'full_path': file_path
            }

    return jsonify(result)

@download_bp.route('/debug/routes')
def debug_routes():
    """Show all registered routes"""
    import flask
    routes = []
    for rule in current_app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods),
            'path': str(rule)
        })
    return jsonify(routes)
