"""
Premium Routes - Integrate with private SaaS for Word DOCX conversion (proxy downloads)
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from typing import Any, Dict

from flask import Blueprint, Response, current_app, jsonify, redirect, request, stream_with_context, url_for, render_template

from pdfforge.services.saas_client import SaasClient

premium_bp = Blueprint("premium", __name__, url_prefix="/premium")
logger = logging.getLogger(__name__)


def _client() -> SaasClient:
    cfg = current_app.config
    return SaasClient(
        base_url=cfg.get("WORD_PREMIUM_BASE_URL"),
        api_key=cfg.get("WORD_PREMIUM_API_KEY"),
        timeout_seconds=int(cfg.get("WORD_PREMIUM_TIMEOUT_SECONDS", 60)),
        retries=int(cfg.get("WORD_PREMIUM_RETRIES", 0)),
    )


@premium_bp.route("/health", methods=["GET"])  # quick surface to check connectivity
def saas_health():
    if not current_app.config.get("WORD_PREMIUM_ENABLED", False):
        return jsonify({"ok": False, "error": "Premium Word is disabled"}), 404
    result = _client().health_check()
    status = 200 if result.get("ok") else 502
    return jsonify(result), status


@premium_bp.route("/word/convert", methods=["POST"])
def word_convert():
    """
    Accepts multipart/form-data with 'file' and optional 'options' (JSON string),
    calls SaaS /api/word/convert, and on success redirects to our proxy download route.
    """
    if not current_app.config.get("WORD_PREMIUM_ENABLED", False):
        return jsonify({"success": False, "error": "Premium Word is disabled"}), 404

    if "file" not in request.files:
        return jsonify({"success": False, "error": "Missing file"}), 400

    f = request.files["file"]
    if f.filename == "":
        return jsonify({"success": False, "error": "Empty filename"}), 400

    # Parse options if provided
    options_str = request.form.get("options")
    options: Dict[str, Any] = {}
    if options_str:
        try:
            options = json.loads(options_str)
        except json.JSONDecodeError:
            return jsonify({"success": False, "error": "Invalid options JSON"}), 400

    # Save to a temporary file
    tmp_dir = tempfile.mkdtemp(prefix="pdfforge_premium_")
    tmp_path = os.path.join(tmp_dir, f.filename)
    f.save(tmp_path)

    client = _client()
    try:
        result = client.convert_word(tmp_path, options)
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    if result.get("ok"):
        # Expect output_file_url like /download/<id>.docx from SaaS
        download_url = result.get("output_file_url") or result.get("download_url")
        if not download_url:
            return jsonify({"success": False, "error": "SaaS missing output_file_url"}), 502

        # Normalize to artifact name expected by our proxy endpoint:
        # 1) Strip base URL if SaaS returned a full URL
        if download_url.startswith(client.base_url):
            path_only = download_url[len(client.base_url):]
        else:
            path_only = download_url if download_url.startswith("/") else f"/{download_url}"

        # 2) Remove leading "/download/" prefix if present, so we pass only the artifact part
        #    Example: "/download/2025_..._converted.docx" -> "2025_..._converted.docx"
        artifact = path_only.lstrip("/")
        if artifact.startswith("download/"):
            artifact = artifact[len("download/"):]

        # Build redirect using url_for to avoid manual string concatenation issues
        return redirect(url_for("premium.proxy_download", artifact=artifact), code=302)

    # Error mapping
    status = int(result.get("status") or 502)
    message = result.get("error") or "Service error"
    return jsonify({"success": False, "error": message, "details": result.get("body")}), status


@premium_bp.route("/toc/generate", methods=["POST"])
def toc_generate():
    """
    Accepts multipart/form-data with 'file' and optional JSON strings: 'options', 'entries', 'config'.
    Forwards them to SaaS /api/toc/generate, and on success redirects to our proxy download route.
    """
    if not current_app.config.get("WORD_PREMIUM_ENABLED", False):
        return jsonify({"success": False, "error": "Premium TOC is disabled"}), 404

    # Accept common alternative keys from external premium UI
    f = None
    if "file" in request.files:
        f = request.files["file"]
    else:
        for alt in ("pdf_file", "pdf", "upload", "document", "input_pdf"):
            if alt in request.files:
                f = request.files[alt]
                break
    if f is None:
        return jsonify({"success": False, "error": "Missing file"}), 400
    if f.filename == "":
        return jsonify({"success": False, "error": "Empty filename"}), 400

    # Parse options
    options_str = request.form.get("options")
    options: Dict[str, Any] = {}
    if options_str:
        try:
            options = json.loads(options_str)
        except json.JSONDecodeError:
            return jsonify({"success": False, "error": "Invalid options JSON"}), 400

    # Optional entries and config JSONs
    entries = None
    entries_str = request.form.get("entries")
    if entries_str:
        try:
            entries = json.loads(entries_str)
        except json.JSONDecodeError:
            return jsonify({"success": False, "error": "Invalid entries JSON"}), 400

    config = None
    config_str = request.form.get("config")
    if config_str:
        try:
            config = json.loads(config_str)
        except json.JSONDecodeError:
            return jsonify({"success": False, "error": "Invalid config JSON"}), 400

    tmp_dir = tempfile.mkdtemp(prefix="pdfforge_premium_")
    tmp_path = os.path.join(tmp_dir, f.filename)
    f.save(tmp_path)

    client = _client()
    try:
        result = client.generate_toc(tmp_path, options, entries=entries, config=config)
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    if result.get("ok"):
        download_url = result.get("output_file_url") or result.get("download_url")
        if not download_url:
            return jsonify({"success": False, "error": "SaaS missing output_file_url"}), 502

        if download_url.startswith(client.base_url):
            path_only = download_url[len(client.base_url):]
        else:
            path_only = download_url if download_url.startswith("/") else f"/{download_url}"

        artifact = path_only.lstrip("/")
        if artifact.startswith("download/"):
            artifact = artifact[len("download/"):]

        # If the caller expects JSON (AJAX), return a JSON payload instead of 302
        accept = (request.headers.get("Accept") or "").lower()
        wants_json = ("application/json" in accept) or (request.args.get("ajax") == "1") or (
            (request.headers.get("X-Requested-With") or "").lower() in ("xmlhttprequest", "fetch")
        )
        proxy_url = url_for("premium.proxy_download", artifact=artifact)
        if wants_json:
            return jsonify({
                "success": True,
                "file_id": result.get("file_id") or os.path.splitext(os.path.basename(artifact))[0],
                "output_filename": result.get("output_filename") or os.path.basename(artifact),
                "output_file_url": proxy_url,
                "message": result.get("message") or "TOC generated"
            }), 200

        # Default: redirect for normal form submissions
        return redirect(proxy_url, code=302)

    status = int(result.get("status") or 502)
    message = result.get("error") or "Service error"
    return jsonify({"success": False, "error": message, "details": result.get("body")}), status


@premium_bp.route("/download/<path:artifact>", methods=["GET"])  # artifact includes extension
def proxy_download(artifact: str):
    """
    Proxy download from SaaS. Example: GET /premium/download/20251116_154915_MyDoc_converted.docx
    """
    if not current_app.config.get("WORD_PREMIUM_ENABLED", False):
        return jsonify({"error": "Premium Word is disabled"}), 404

    client = _client()
    saas_path = f"/download/{artifact}"
    try:
        upstream = client.proxy_download(saas_path)
    except Exception as e:  # requests exceptions
        logger.exception("Proxy download failed: %s", e)
        return jsonify({"error": "Failed to fetch artifact from service"}), 502

    def generate():
        try:
            for chunk in upstream.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk
        finally:
            upstream.close()

    # Build response with important headers from upstream
    headers = {}
    cd = upstream.headers.get("Content-Disposition")
    if cd:
        headers["Content-Disposition"] = cd
    ct = upstream.headers.get("Content-Type", "application/octet-stream")

    return Response(stream_with_context(generate()), status=upstream.status_code, headers=headers, mimetype=ct)



@premium_bp.route("/toc/builder", methods=["GET"])  # Premium TOC Builder UI (reuses external toc_generator template)
def toc_builder():
    if not current_app.config.get("WORD_PREMIUM_ENABLED", False):
        # Show an upsell/landing page instead of raw 404 for unpaid users
        return render_template(
            "premium_info.html",
            feature_name="Custom TOC Builder",
            feature_slug="toc",
            health_url=url_for("premium.saas_health"),
            enable_instructions="Set PREMIUM_ENABLED=true, PREMIUM_BASE_URL=http://localhost:5003, PREMIUM_API_KEY=<your-key> in your environment and restart the app.",
        ), 200

    return render_template(
        "premium/toc.html",
        premium_enabled=True,
        submit_url=url_for("premium.toc_generate") + "?ajax=1",
        download_prefix=url_for("premium.proxy_download", artifact="").rstrip("/"),
        health_url=url_for("premium.saas_health"),
    )
