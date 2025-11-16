# pdfforge/routes/split.py
"""
Split Routes - HTTP endpoints for PDF splitting
"""
from __future__ import annotations

import logging
from pathlib import Path

from flask import Blueprint, jsonify, render_template, request
from werkzeug.utils import secure_filename

from ..services.split_service import SplitService
from ..utils.file_utils import save_uploaded_file
from ..utils.validation import allowed_file

logger = logging.getLogger(__name__)

split_bp = Blueprint("split", __name__, url_prefix="/split")


def get_split_service() -> SplitService:
    return SplitService()


@split_bp.route("/")
def split_page():
    """Optional: render split page if template exists; otherwise return JSON."""
    try:
        # If a template exists, render it; otherwise, return simple info
        return render_template("split.html")
    except Exception:
        return jsonify({
            "success": True,
            "message": "Split API is available. Use POST /split/upload then /split/process."
        })


@split_bp.route("/upload", methods=["POST"])
def upload_file():
    """Handle file upload for splitting"""
    try:
        if "file" not in request.files:
            return jsonify({"success": False, "error": "No file provided"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"success": False, "error": "No file selected"}), 400

        if not allowed_file(file.filename):
            return jsonify({"success": False, "error": "Only PDF files are allowed"}), 400

        file_path = save_uploaded_file(file)
        return jsonify({
            "success": True,
            "file_path": file_path,
            "filename": secure_filename(file.filename),
        })
    except Exception as e:
        logger.exception("Upload error in split")
        return jsonify({"success": False, "error": "Upload failed: " + str(e)}), 500


@split_bp.route("/analyze", methods=["POST"])
def analyze_pdf():
    """Analyze PDF and return recommendations."""
    try:
        data = request.get_json() or {}
        file_path = data.get("file_path")
        if not file_path:
            return jsonify({"success": False, "error": "file_path is required"}), 400

        split_service = get_split_service()
        result = split_service.analyze(file_path)
        return jsonify(result), (200 if result.get("success") else 400)
    except Exception as e:
        logger.exception("Analyze error")
        return jsonify({"success": False, "error": str(e)}), 500


@split_bp.route("/process", methods=["POST"])
def process_split():
    """Execute split with provided options."""
    try:
        data = request.get_json() or {}
        file_path = data.get("file_path")
        options = data.get("options", {})
        if not file_path:
            return jsonify({"success": False, "error": "file_path is required"}), 400

        split_service = get_split_service()
        result = split_service.split(file_path, options)

        if result.get("success"):
            response = {
                "success": True,
                "files_created": result.get("files_created", 0),
                "output_dir": result.get("output_dir"),
                "output_files": result.get("output_files", []),
                "zip_filename": result.get("zip_filename"),
                "download_url": f"/download/{result['zip_filename']}" if result.get("zip_filename") else None,
                "component_download_url": result.get("component_download_url"),
                "file_id": result.get("file_id"),
                "split_type": result.get("split_type"),
            }
            return jsonify(response)
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.exception("Split processing error")
        return jsonify({"success": False, "error": "Split processing failed: " + str(e)}), 500
