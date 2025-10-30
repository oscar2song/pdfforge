"""
Normalize Routes - HTTP Request Handlers
"""

import logging

from flask import Blueprint, current_app, jsonify, render_template, request
from werkzeug.utils import secure_filename

from ..services.normalize_service import NormalizeService
from ..utils.file_utils import save_uploaded_file
from ..utils.validation import allowed_file

logger = logging.getLogger(__name__)

# Create blueprint
normalize_bp = Blueprint("normalize", __name__, url_prefix="/normalize")

# Initialize service
normalize_service = NormalizeService()


@normalize_bp.route("/")
def normalize_page():
    """Render normalize page"""
    return render_template("normalize.html")


@normalize_bp.route("/upload", methods=["POST"])
def upload_file():
    """Handle file upload for normalization"""
    try:
        if "file" not in request.files:
            return (
                jsonify({"success": False, "error": "No file provided"}),
                400,
            )

        file = request.files["file"]

        if file.filename == "":
            return (
                jsonify({"success": False, "error": "No file selected"}),
                400,
            )

        if not allowed_file(file.filename):
            return (
                jsonify({"success": False, "error": "Only PDF files are allowed"}),
                400,
            )

        # Save file
        file_path = save_uploaded_file(file, current_app.config["UPLOAD_FOLDER"])

        return jsonify(
            {
                "success": True,
                "file_path": file_path,
                "filename": secure_filename(file.filename),
            }
        )

    except Exception as e:
        logger.exception("Upload error in normalize")
        return (
            jsonify({"success": False, "error": "Upload failed: " + str(e)}),
            500,
        )


@normalize_bp.route("/upload-multiple", methods=["POST"])
def upload_multiple_files():
    """Handle multiple file uploads for normalization"""
    try:
        if "files" not in request.files:
            return (
                jsonify({"success": False, "error": "No files provided"}),
                400,
            )

        files = request.files.getlist("files")
        if not files or all(f.filename == "" for f in files):
            return (
                jsonify({"success": False, "error": "No files selected"}),
                400,
            )

        uploaded_files = []

        for file in files:
            if file and file.filename and allowed_file(file.filename):
                file_path = save_uploaded_file(file, current_app.config["UPLOAD_FOLDER"])
                uploaded_files.append(
                    {
                        "path": file_path,
                        "name": secure_filename(file.filename),
                        "filename": secure_filename(file.filename),
                    }
                )

        if not uploaded_files:
            return (
                jsonify({"success": False, "error": "No valid PDF files uploaded"}),
                400,
            )

        return jsonify({"success": True, "files": uploaded_files})

    except Exception as e:
        logger.exception("Multiple upload error in normalize")
        return (
            jsonify({"success": False, "error": "Upload failed: " + str(e)}),
            500,
        )


@normalize_bp.route("/process", methods=["POST"])
def normalize_pdf():
    """Process PDF normalization request"""
    try:
        data = request.get_json()

        if not data:
            return (
                jsonify({"success": False, "error": "No data provided"}),
                400,
            )

        # Check if it's batch or single file processing
        if "files" in data and isinstance(data["files"], list):
            # Batch processing
            if not data["files"]:
                return (
                    jsonify({"success": False, "error": "No files provided"}),
                    400,
                )

            result = normalize_service.normalize_batch(data["files"], data.get("options", {}))
        else:
            # Single file processing
            if "file_path" not in data:
                return (
                    jsonify({"success": False, "error": "No file provided"}),
                    400,
                )

            file_config = {
                "path": data["file_path"],
                "name": data.get("filename", "document.pdf"),
            }

            result = normalize_service.normalize_file(file_config, data.get("options", {}))

        if result["success"]:
            response_data = {
                "success": True,
                "download_url": f"/download/{result['filename']}",
                "output_filename": result["filename"],
            }

            # Add batch-specific data
            if result.get("batch"):
                response_data["batch"] = True
                response_data["total_files"] = result["total_files"]
                response_data["successful"] = result["successful"]
                if "results" in result:
                    response_data["results"] = result["results"]
            else:
                # Add single file metadata
                response_data["page_count"] = result.get("page_count")
                response_data["target_size"] = result.get("target_size")
                response_data["ocr_performed"] = result.get("ocr_performed", False)

            return jsonify(response_data)
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.exception("Normalization processing error")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Normalization processing failed: " + str(e),
                }
            ),
            500,
        )


@normalize_bp.route("/page-sizes", methods=["GET"])
def get_page_sizes():
    """Get available page sizes"""
    from config import Config

    return jsonify(
        {
            "page_sizes": list(Config.PAGE_SIZES.keys()),
            "default_sizes": ["letter", "legal", "A4", "A3", "A5"],
        }
    )
