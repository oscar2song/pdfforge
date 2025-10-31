"""
Merge Routes - HTTP Request Handlers
"""

import logging
import os

from flask import Blueprint, jsonify, render_template, request, send_file
from werkzeug.utils import secure_filename

from ..services.merge_service import MergeService
from ..utils.file_utils import save_uploaded_file
from ..utils.validation import allowed_file

logger = logging.getLogger(__name__)

# Create blueprint
merge_bp = Blueprint("merge", __name__, url_prefix="/merge")


# Initialize service
def get_merge_service():
    # Use the uploads folder in the project root
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    uploads_folder = os.path.join(project_root, "uploads")
    return MergeService(upload_folder=uploads_folder)  # Pass to constructor


@merge_bp.route("/")
def merge_page():
    """Render merge page"""
    return render_template("merge.html")


@merge_bp.route("/upload", methods=["POST"])
def upload_file():
    """Handle file upload for merging"""
    try:
        if "file" not in request.files:
            return jsonify({"success": False, "error": "No file provided"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"success": False, "error": "No file selected"}), 400

        # Validate file type
        if not allowed_file(file.filename):
            return jsonify({"success": False, "error": "Only PDF files are allowed"}), 400

        # Save file to uploads folder
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        uploads_folder = os.path.join(project_root, "uploads")
        os.makedirs(uploads_folder, exist_ok=True)

        file_path = save_uploaded_file(file, uploads_folder)

        return jsonify({
            "success": True,
            "file_path": file_path,
            "filename": secure_filename(file.filename),
        })

    except Exception as e:
        logger.exception("Upload error in merge")
        return jsonify({"success": False, "error": "Upload failed: " + str(e)}), 500


@merge_bp.route("/process", methods=["POST"])
def merge_pdfs():
    """Process PDF merge request"""
    try:
        data = request.get_json()

        if not data or "files" not in data:
            return jsonify({"success": False, "error": "No files provided"}), 400

        # Validate we have at least 2 files
        if len(data["files"]) < 2:
            return jsonify({"success": False, "error": "Please select at least 2 files to merge"}), 400

        # Process files with service - NO upload_folder parameter needed
        merge_service = get_merge_service()
        result = merge_service.merge_files(data["files"], data.get("options", {}))

        if result["success"]:
            response_data = {
                "success": True,
                "download_url": f"/merge/download/{result['filename']}",
                "output_filename": result["filename"],
                "page_count": result.get("page_count", 0),
                "file_count": result.get("file_count", len(data["files"])),
            }
            return jsonify(response_data)
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.exception("Merge processing error")
        return jsonify({"success": False, "error": "Merge processing failed: " + str(e)}), 500


@merge_bp.route("/download/<filename>")
def download_merged(filename):
    """Download merged file"""
    try:
        # Use the project root uploads folder
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        uploads_folder = os.path.join(project_root, "uploads")
        file_path = os.path.join(uploads_folder, filename)

        logger.info(f"Looking for file at: {file_path}")

        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return jsonify({"success": False, "error": f"File not found: {filename}"}), 404

        logger.info(f"Serving file from: {file_path}")
        return send_file(file_path, as_attachment=True, download_name=filename)

    except Exception as e:
        logger.error(f"Download error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@merge_bp.route("/cleanup/<filename>", methods=["POST"])
def cleanup_file(filename):
    """Clean up temporary files"""
    try:
        # Clean up from uploads folder
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        uploads_folder = os.path.join(project_root, "uploads")
        file_path = os.path.join(uploads_folder, filename)

        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up: {file_path}")
        else:
            logger.warning(f"File not found for cleanup: {file_path}")

        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
