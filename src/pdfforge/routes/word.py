# pdfforge/routes/word.py
"""
Word Routes - HTTP endpoints for PDF → Word (DOCX) conversion

Free path focuses on digital PDFs. Premium OCR/overlay/multi-format handled separately.
"""
from __future__ import annotations

import logging

from flask import Blueprint, jsonify, render_template, request
from werkzeug.utils import secure_filename

from ..services.word_service import WordService
from ..utils.file_utils import save_uploaded_file
from ..utils.validation import allowed_file

logger = logging.getLogger(__name__)

word_bp = Blueprint("word", __name__, url_prefix="/word")


def get_word_service() -> WordService:
    return WordService()


@word_bp.route("/")
def word_page():
    """Optional: render word page if template exists; otherwise return JSON."""
    try:
        return render_template("word.html")
    except Exception:
        return jsonify({"success": True, "message": "Word API is available. Use POST /word/upload then /word/process."})


@word_bp.route("/upload", methods=["POST"])
def upload_file():
    """Handle file upload for conversion"""
    try:
        if "file" not in request.files:
            return jsonify({"success": False, "error": "No file provided"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"success": False, "error": "No file selected"}), 400

        if not allowed_file(file.filename):
            return jsonify({"success": False, "error": "Only PDF files are allowed"}), 400

        file_path = save_uploaded_file(file)
        return jsonify(
            {
                "success": True,
                "file_path": file_path,
                "filename": secure_filename(file.filename),
            }
        )
    except Exception as e:
        logger.exception("Upload error in word")
        return jsonify({"success": False, "error": "Upload failed: " + str(e)}), 500


@word_bp.route("/analyze", methods=["POST"])
def analyze_pdf():
    """Analyze PDF and return basic info (pages, scanned guess)."""
    try:
        data = request.get_json() or {}
        file_path = data.get("file_path")
        if not file_path:
            return jsonify({"success": False, "error": "file_path is required"}), 400

        service = get_word_service()
        result = service.analyze(file_path)
        return jsonify(result), (200 if result.get("success") else 400)
    except Exception as e:
        logger.exception("Analyze error (word)")
        return jsonify({"success": False, "error": str(e)}), 500


@word_bp.route("/process", methods=["POST"])
def process_word():
    """Execute conversion with provided options."""
    try:
        data = request.get_json() or {}
        file_path = data.get("file_path")
        options = data.get("options", {})
        batch_files = data.get("file_paths")  # optional: list of file paths for batch

        if not file_path and not batch_files:
            return jsonify({"success": False, "error": "file_path or file_paths is required"}), 400

        service = get_word_service()
        if batch_files and isinstance(batch_files, list) and len(batch_files) > 0:
            result = service.convert_batch(batch_files, options)
        else:
            result = service.convert_single(file_path, options)

        if result.get("success"):
            response = {
                "success": True,
                "output_files": result.get("output_files")
                or ([result.get("output_file")] if result.get("output_file") else []),
                "files_created": result.get("files_created", 1 if result.get("output_file") else 0),
                "zip_filename": result.get("zip_filename"),
                # Component-aware URL for ZIP (canonical)
                "download_url": result.get("component_download_url"),
                "component_download_url": result.get("component_download_url"),
                # Per-file component-aware URLs if available
                "download_urls": result.get("download_urls")
                or ([result.get("download_url")] if result.get("download_url") else None),
                "file_id": result.get("file_id"),
            }
            return jsonify(response)
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.exception("Word processing error")
        return jsonify({"success": False, "error": "Word processing failed: " + str(e)}), 500
