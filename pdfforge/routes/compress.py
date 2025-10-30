"""
Compress Routes - HTTP Request Handlers
"""

import logging

from flask import Blueprint, current_app, jsonify, render_template, request
from werkzeug.utils import secure_filename

from ..services.compress_service import CompressService
from ..utils.file_utils import save_uploaded_file
from ..utils.validation import allowed_file

logger = logging.getLogger(__name__)

# Create blueprint
compress_bp = Blueprint("compress", __name__, url_prefix="/compress")

# Initialize service
compress_service = CompressService()


@compress_bp.route("/")
def compress_page():
    """Render compress page"""
    return render_template("compress.html")


@compress_bp.route("/upload", methods=["POST"])
def upload_file():
    """Handle file upload for compression"""
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
        logger.exception("Upload error in compress")
        return (
            jsonify({"success": False, "error": "Upload failed: " + str(e)}),
            500,
        )


@compress_bp.route("/upload-multiple", methods=["POST"])
def upload_multiple_files():
    """Handle multiple file uploads for compression"""
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
        logger.exception("Multiple upload error in compress")
        return (
            jsonify({"success": False, "error": "Upload failed: " + str(e)}),
            500,
        )


@compress_bp.route("/process", methods=["POST"])
def compress_pdf():
    """Process PDF compression request"""
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

            result = compress_service.compress_batch(data["files"], data.get("options", {}))
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

            result = compress_service.compress_file(file_config, data.get("options", {}))

        if result["success"]:
            response_data = {
                "success": True,
                "download_url": f"/download/{result['filename']}",
                "output_filename": result["filename"],
            }

            # Add compression stats if available (use get() to avoid KeyError)
            if "original_size" in result and "compressed_size" in result:
                response_data["compression_stats"] = {
                    "original_size_mb": result["original_size"] / (1024 * 1024),
                    "compressed_size_mb": result["compressed_size"] / (1024 * 1024),
                    "compression_ratio": result.get("compression_ratio", 0),
                    "used_compression": result.get("used_compression", False),
                    "compression_level": result.get("compression_level", "medium"),
                    "reduction_percent": result.get("reduction_percent", 0),
                }

            # Add batch-specific data
            if result.get("batch"):
                response_data["batch"] = True
                response_data["total_files"] = result["total_files"]
                response_data["successful"] = result["successful"]
                if "total_savings" in result:
                    response_data["total_savings_mb"] = result["total_savings"] / (1024 * 1024)
                if "results" in result:
                    response_data["results"] = result["results"]

            return jsonify(response_data)
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.exception("Compression processing error")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Compression processing failed: " + str(e),
                }
            ),
            500,
        )

@compress_bp.route("/compression-levels", methods=["GET"])
def get_compression_levels():
    """Get available compression levels and their settings"""
    return jsonify(
        {
            "compression_levels": {
                "low": {
                    "description": "Minimal compression, best quality",
                    "image_quality": 95,
                    "target_dpi": 200,
                    "recommended_for": "Documents with important images",
                },
                "medium": {
                    "description": "Balanced compression and quality",
                    "image_quality": 85,
                    "target_dpi": 150,
                    "recommended_for": "General documents",
                },
                "high": {
                    "description": "Maximum compression, smaller files",
                    "image_quality": 75,
                    "target_dpi": 120,
                    "recommended_for": "Web publishing, email attachments",
                },
            }
        }
    )
