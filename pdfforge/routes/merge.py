# pdfforge/routes/merge.py
"""
Merge Routes - HTTP Request Handlers - UPDATED with File Manager
"""

import logging
from pathlib import Path

from flask import Blueprint, jsonify, render_template, request, send_file
from werkzeug.utils import secure_filename

from ..services.merge_service import MergeService
from ..utils.file_manager import get_file_manager
from ..utils.file_utils import save_uploaded_file
from ..utils.validation import allowed_file

logger = logging.getLogger(__name__)

# Create blueprint
merge_bp = Blueprint("merge", __name__, url_prefix="/merge")


# Initialize service
def get_merge_service():
    return MergeService()  # No need to pass upload folder anymore


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

        # Save file using file_utils (which now uses file manager)
        file_path = save_uploaded_file(file)  # No upload_folder needed

        return jsonify(
            {
                "success": True,
                "file_path": file_path,
                "filename": secure_filename(file.filename),
            }
        )

    except Exception as e:
        logger.exception("Upload error in merge")
        return jsonify({"success": False, "error": "Upload failed: " + str(e)}), 500


# pdfforge/routes/merge.py (update the process route)
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

        # Process files with service
        merge_service = get_merge_service()
        result = merge_service.merge_files(data["files"], data.get("options", {}))

        if result["success"]:
            response_data = {
                "success": True,
                "download_url": f"/download/component/merge/{result['file_id']}",
                "output_filename": result["filename"],
                "page_count": result.get("page_count", 0),
                "file_count": result.get("file_count", len(data["files"])),
                "file_id": result.get("file_id"),
            }
            return jsonify(response_data)
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.exception("Merge processing error")
        return jsonify({"success": False, "error": "Merge processing failed: " + str(e)}), 500


@merge_bp.route("/download/<file_id>")
def download_merged(file_id):
    """Download merged file - UPDATED with file manager"""
    try:
        file_manager = get_file_manager("merge")

        # Look for file in merge directory first
        merge_dir = file_manager.get_component_dir()
        file_path = None

        # Search for file with the file_id in the filename
        for file_in_dir in merge_dir.glob(f"*{file_id}*"):
            if file_in_dir.is_file():
                file_path = file_in_dir
                break

        # Fallback: check old uploads directory for backward compatibility
        if not file_path or not file_path.exists():
            old_uploads = Path(__file__).parent.parent.parent / "uploads"
            if old_uploads.exists():
                for file_in_dir in old_uploads.glob(f"*{file_id}*"):
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


@merge_bp.route("/cleanup/<file_id>", methods=["POST"])
def cleanup_file(file_id):
    """Clean up temporary files - UPDATED with file manager"""
    try:
        file_manager = get_file_manager("merge")
        files_cleaned = 0

        # Clean up from merge directory
        merge_dir = file_manager.get_component_dir()
        for file_path in merge_dir.glob(f"*{file_id}*"):
            if file_path.is_file():
                file_path.unlink()
                files_cleaned += 1
                logger.info(f"Cleaned up from merge dir: {file_path}")

        # Also clean up from old uploads directory for backward compatibility
        old_uploads = Path(__file__).parent.parent.parent / "uploads"
        if old_uploads.exists():
            for file_path in old_uploads.glob(f"*{file_id}*"):
                if file_path.is_file():
                    file_path.unlink()
                    files_cleaned += 1
                    logger.info(f"Cleaned up from old uploads: {file_path}")

        return jsonify(
            {"success": True, "message": f"Cleaned up {files_cleaned} files", "files_cleaned": files_cleaned}
        )

    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
