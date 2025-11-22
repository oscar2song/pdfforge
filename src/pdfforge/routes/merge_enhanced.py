"""
Enhanced Merge Routes - HTTP Request Handlers
Merge PDFs with TOC support using PDFForge file management
"""

import logging
from pathlib import Path

from flask import Blueprint, jsonify, render_template, request, send_file

from ..services.toc_service import MergeWithTOCService
from ..utils.file_manager import get_file_manager
from ..utils.file_utils import save_uploaded_file
from ..utils.validation import allowed_file

logger = logging.getLogger(__name__)

# Create blueprint
merge_enhanced_bp = Blueprint("merge_enhanced", __name__, url_prefix="/merge-enhanced")


def get_merge_service():
    """Get merge service instance."""
    return MergeWithTOCService()


@merge_enhanced_bp.route("/")
def merge_page():
    """Render enhanced merge page."""
    return render_template("merge_enhanced.html")


@merge_enhanced_bp.route("/upload", methods=["POST"])
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

        # Save file using file_utils
        file_path = save_uploaded_file(file)
        logger.info(f"Saved file for merging: {file_path}")

        return jsonify({"success": True, "file_path": file_path, "filename": file.filename})

    except Exception as e:
        logger.exception("Upload error in enhanced merge")
        return jsonify({"success": False, "error": str(e)}), 500


@merge_enhanced_bp.route("/preview", methods=["POST"])
def merge_preview():
    """
    Get preview of merge operation with suggested bookmarks.

    Expects JSON with:
        - files: List of {file_path, filename} objects

    Returns:
        JSON with file info and suggested bookmarks
    """
    try:
        data = request.get_json()

        if not data or "files" not in data:
            return jsonify({"success": False, "error": "No files provided"}), 400

        files = data["files"]

        if not files or len(files) < 2:
            return jsonify({"success": False, "error": "At least 2 PDF files required"}), 400

        # Extract file paths and filenames
        file_paths = [f["file_path"] for f in files]
        filenames = [f["filename"] for f in files]

        # Validate all files exist and are PDFs
        for file_path, filename in zip(file_paths, filenames):
            path = Path(file_path)
            if not path.exists():
                return jsonify({"success": False, "error": f"File not found: {filename}"}), 400

            if not allowed_file(filename):
                return jsonify({"success": False, "error": f"Invalid file type: {filename} (must be PDF)"}), 400

        # Get preview
        merge_service = get_merge_service()
        result = merge_service.get_merge_preview(file_paths, filenames)

        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.exception("Merge preview error")
        return jsonify({"success": False, "error": str(e)}), 500


@merge_enhanced_bp.route("/execute", methods=["POST"])
def execute_merge():
    """
    Execute PDF merge with optional TOC generation.

    Expects JSON with:
        - files: List of {file_path, filename} objects
        - bookmark_labels: Optional dict mapping file index to custom label
        - output_filename: Optional custom output filename
        - add_toc: Boolean (default: false)
        - toc_style: Optional TOC style config dict

    Returns:
        JSON with file_id for download
    """
    try:
        data = request.get_json()

        if not data or "files" not in data:
            return jsonify({"success": False, "error": "No files provided"}), 400

        files = data["files"]

        if not files or len(files) < 2:
            return jsonify({"success": False, "error": "At least 2 PDF files required"}), 400

        # Extract parameters
        file_paths = [f["file_path"] for f in files]
        filenames = [f["filename"] for f in files]
        bookmark_labels = data.get("bookmark_labels", {})
        output_filename = data.get("output_filename", None)
        add_toc = data.get("add_toc", False)
        toc_style_config = data.get("toc_style", None)

        # Convert string keys to integers for bookmark_labels
        if bookmark_labels:
            bookmark_labels = {int(k): v for k, v in bookmark_labels.items()}

        # Execute merge
        merge_service = get_merge_service()
        result = merge_service.merge_pdfs_with_toc(
            file_paths=file_paths,
            filenames=filenames,
            bookmark_labels=bookmark_labels,
            output_filename=output_filename,
            add_toc=add_toc,
            toc_style_config=toc_style_config,
        )

        if result["success"]:
            response_data = {
                "success": True,
                "download_url": f"/download/component/merge/{result['file_id']}",
                "output_filename": result["filename"],
                "file_id": result["file_id"],
                "total_pages": result.get("total_pages", 0),
                "bookmark_count": result.get("bookmark_count", 0),
                "has_toc": result.get("has_toc", False),
                "toc_pages": result.get("toc_pages", 0),
            }
            return jsonify(response_data), 200
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.exception("Merge execution error")
        return jsonify({"success": False, "error": str(e)}), 500


@merge_enhanced_bp.route("/download/<file_id>")
def download_merged(file_id):
    """Download merged file"""
    try:
        file_manager = get_file_manager("merge")

        # Look for file in merge directory
        merge_dir = file_manager.get_component_dir()
        file_path = None

        # Search for file with the file_id in the filename
        for file_in_dir in merge_dir.glob(f"*{file_id}*"):
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


@merge_enhanced_bp.route("/cleanup/<file_id>", methods=["POST"])
def cleanup_file(file_id):
    """Clean up temporary files"""
    try:
        file_manager = get_file_manager("merge")
        files_cleaned = 0

        # Clean up from merge directory
        merge_dir = file_manager.get_component_dir()
        for file_path in merge_dir.glob(f"*{file_id}*"):
            if file_path.is_file():
                file_path.unlink()
                files_cleaned += 1
                logger.info(f"Cleaned up: {file_path}")

        return jsonify(
            {"success": True, "message": f"Cleaned up {files_cleaned} files", "files_cleaned": files_cleaned}
        )

    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
