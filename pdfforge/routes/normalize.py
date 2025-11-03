# pdfforge/routes/normalize.py
"""
Normalize Routes - HTTP Request Handlers - UPDATED with File Manager
"""

import logging
from pathlib import Path

from flask import Blueprint, jsonify, render_template, request, send_file
from werkzeug.utils import secure_filename

from ..services.normalize_service import NormalizeService
from ..utils.file_manager import get_file_manager
from ..utils.file_utils import save_uploaded_file
from ..utils.validation import allowed_file

logger = logging.getLogger(__name__)

# Create blueprint
normalize_bp = Blueprint("normalize", __name__, url_prefix="/normalize")


# Initialize service
def get_normalize_service():
    return NormalizeService()


@normalize_bp.route("/")
def normalize_page():
    """Render normalize page"""
    return render_template("normalize.html")


@normalize_bp.route("/upload", methods=["POST"])
def upload_file():
    """Handle file upload for normalization"""
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
        file_path = save_uploaded_file(file)

        return jsonify(
            {
                "success": True,
                "file_path": file_path,
                "filename": secure_filename(file.filename),
            }
        )

    except Exception as e:
        logger.exception("Upload error in normalize")
        return jsonify({"success": False, "error": "Upload failed: " + str(e)}), 500


@normalize_bp.route("/process", methods=["POST"])
def normalize_pdf():
    """Process PDF normalization request"""
    try:
        data = request.get_json()

        if not data or "files" not in data:
            return jsonify({"success": False, "error": "No files provided"}), 400

        # Process files with service
        normalize_service = get_normalize_service()

        if len(data["files"]) > 1:
            # Batch processing
            result = normalize_service.normalize_batch(data["files"], data.get("options", {}))
        else:
            # Single file processing
            result = normalize_service.normalize_file(data["files"][0], data.get("options", {}))

        if result["success"]:
            response_data = {
                "success": True,
                "download_url": f"/download/component/normalize/{result['file_id']}",
                "download_url_legacy": f"/download/{result['filename']}",  # Backward compatibility
                "output_filename": result["filename"],
                "page_count": result.get("page_count", 0),
                "target_size": result.get("target_size", ""),
                "ocr_performed": result.get("ocr_performed", False),
                "file_id": result.get("file_id"),
                "batch": result.get("batch", False),
            }

            # Add batch-specific info
            if result.get("batch"):
                response_data.update(
                    {
                        "total_files": result.get("total_files", 0),
                        "successful": result.get("successful", 0),
                    }
                )

            return jsonify(response_data)
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.exception("Normalization processing error")
        return jsonify({"success": False, "error": "Normalization processing failed: " + str(e)}), 500


@normalize_bp.route("/download/<file_id>")
def download_normalized(file_id):
    """Download normalized file - UPDATED with file manager"""
    try:
        file_manager = get_file_manager("normalize")

        # Look for file in normalize directory first
        normalize_dir = file_manager.get_component_dir()
        file_path = None

        # Search for file with the file_id in the filename
        for file_in_dir in normalize_dir.glob(f"*{file_id}*"):
            if file_in_dir.is_file():
                file_path = file_in_dir
                break

        # Fallback: check old locations for backward compatibility
        if not file_path or not file_path.exists():
            old_downloads = Path(__file__).parent.parent.parent / "downloads"
            if old_downloads.exists():
                for file_in_dir in old_downloads.glob(f"*{file_id}*"):
                    if file_in_dir.is_file():
                        file_path = file_in_dir
                        break

        if not file_path or not file_path.exists():
            logger.error(f"File not found for ID: {file_id}")
            return jsonify({"success": False, "error": f"File not found: {file_id}"}), 404

        logger.info(f"Serving normalized file from: {file_path}")
        return send_file(str(file_path), as_attachment=True, download_name=file_path.name)

    except Exception as e:
        logger.error(f"Download error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@normalize_bp.route("/cleanup/<file_id>", methods=["POST"])
def cleanup_file(file_id):
    """Clean up temporary files - UPDATED with file manager"""
    try:
        file_manager = get_file_manager("normalize")
        files_cleaned = 0

        # Clean up from normalize directory
        normalize_dir = file_manager.get_component_dir()
        for file_path in normalize_dir.glob(f"*{file_id}*"):
            if file_path.is_file():
                file_path.unlink()
                files_cleaned += 1
                logger.info(f"Cleaned up from normalize dir: {file_path}")

        # Also clean up from old downloads directory for backward compatibility
        old_downloads = Path(__file__).parent.parent.parent / "downloads"
        if old_downloads.exists():
            for file_path in old_downloads.glob(f"*{file_id}*"):
                if file_path.is_file():
                    file_path.unlink()
                    files_cleaned += 1
                    logger.info(f"Cleaned up from old downloads: {file_path}")

        return jsonify(
            {"success": True, "message": f"Cleaned up {files_cleaned} files", "files_cleaned": files_cleaned}
        )

    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@normalize_bp.route("/preview", methods=["POST"])
def preview_normalization():
    """Preview normalization settings"""
    try:
        data = request.get_json()

        if not data or "file" not in data:
            return jsonify({"success": False, "error": "No file provided"}), 400

        # Analyze the PDF and return preview information
        from ..utils.pdf_utils import analyze_pdf

        analysis = analyze_pdf(data["file"]["path"])

        return jsonify(
            {
                "success": True,
                "analysis": analysis,
                "suggested_settings": {
                    "page_size": "letter" if analysis.get("size_category") == "standard" else "a4",
                    "orientation": analysis.get("orientation", "portrait"),
                },
            }
        )

    except Exception as e:
        logger.error(f"Preview error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
