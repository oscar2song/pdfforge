# pdfforge/routes/download.py
"""
Download Routes - UPDATED with File Manager
"""

import logging
import os
from pathlib import Path

from flask import Blueprint, abort, current_app, jsonify, send_file
from werkzeug.exceptions import HTTPException

from ..utils.file_manager import get_file_manager

logger = logging.getLogger(__name__)

download_bp = Blueprint("download", __name__)


def find_file_anywhere(filename: str):
    """
    Search for file in all possible locations with priority:
    1. Component-specific download directories (downloads/merge/, downloads/toc/, etc.)
    2. Old downloads directory
    3. Old uploads directory
    """
    # Security check - prevent directory traversal
    if ".." in filename or filename.startswith("/"):
        current_app.logger.error("Security check failed")
        return None

    # Try component-specific download directories first
    components = ["merge", "normalize", "compress", "toc", "split", "word"]  # include split + word
    for component in components:
        file_manager = get_file_manager(component)
        # Get the downloads directory for this component
        component_download_dir = file_manager.get_component_dir()  # This will be downloads/toc/
        file_path = component_download_dir / filename
        if file_path.exists():
            current_app.logger.info(f"✅ Found file in {component} downloads: {file_path}")
            return file_path

    # Fallback: Search in main downloads directory
    old_downloads = Path(os.getcwd()) / "downloads"
    file_path = old_downloads / filename
    if file_path.exists():
        current_app.logger.info(f"✅ Found file in old downloads directory: {file_path}")
        return file_path

    # Fallback: Search in uploads directory
    old_uploads = Path(os.getcwd()) / "uploads"
    file_path = old_uploads / filename
    if file_path.exists():
        current_app.logger.info(f"✅ Found file in old uploads directory: {file_path}")
        return file_path

    return None


def find_file_by_id(file_id: str, component: str | None = None):
    """
    Find file by ID (partial filename match) in all locations
    """
    # Try component-specific directories first
    if component:
        file_manager = get_file_manager(component)
        component_dir = file_manager.get_component_dir()
        for file_path in component_dir.glob(f"*{file_id}*"):
            if file_path.is_file():
                current_app.logger.info(f"✅ Found file by ID in {component} directory: {file_path}")
                return file_path
    else:
        # Search all component directories
        components = ["merge", "normalize", "compress", "toc", "split", "word"]
        for comp in components:
            file_manager = get_file_manager(comp)
            component_dir = file_manager.get_component_dir()
            for file_path in component_dir.glob(f"*{file_id}*"):
                if file_path.is_file():
                    current_app.logger.info(f"✅ Found file by ID in {comp} directory: {file_path}")
                    return file_path

    # Fallback: Search old directories
    old_directories = [Path(os.getcwd()) / "downloads", Path(os.getcwd()) / "uploads"]
    for directory in old_directories:
        if directory.exists():
            for file_path in directory.glob(f"*{file_id}*"):
                if file_path.is_file():
                    current_app.logger.info(f"✅ Found file by ID in {directory}: {file_path}")
                    return file_path

    return None


@download_bp.route("/download/<filename>")
def download_file(filename):
    """Download a processed file - UPDATED with file manager"""
    current_app.logger.info("🎯 MAIN DOWNLOAD ROUTE EXECUTING!")
    current_app.logger.info(f"Requested filename: {filename}")
    current_app.logger.warning("Legacy download route '/download/<filename>' used. Prefer '/download/component/<component>/<file_id>'")

    try:
        file_path = find_file_anywhere(filename)

        if not file_path:
            current_app.logger.error(f"File not found: {filename}")
            abort(404, f"File not found: {filename}")

        current_app.logger.info(f"✅ File found, sending: {file_path}")

        # Send file
        return send_file(str(file_path), as_attachment=True, download_name=filename)

    except HTTPException as e:
        # Preserve intended HTTP status (e.g., 404)
        raise e
    except Exception as e:
        current_app.logger.error(f"Download error: {str(e)}")
        abort(500, "Download failed")


@download_bp.route("/download/component/<component>/<file_id>")
def download_component_file(component, file_id):
    """Download file from specific component directory"""
    current_app.logger.info(f"🎯 COMPONENT DOWNLOAD: {component}/{file_id}")

    try:
        valid_components = ["merge", "normalize", "compress", "toc", "split", "word"]
        if component not in valid_components:
            abort(400, f"Invalid component. Must be one of: {', '.join(valid_components)}")

        file_path = find_file_by_id(file_id, component)

        if not file_path:
            current_app.logger.error(f"File not found for {component} ID: {file_id}")
            abort(404, f"File not found: {file_id}")

        current_app.logger.info(f"✅ Component file found, sending: {file_path}")

        return send_file(str(file_path), as_attachment=True, download_name=file_path.name)

    except HTTPException as e:
        raise e
    except Exception as e:
        current_app.logger.error(f"Component download error: {str(e)}")
        abort(500, "Download failed")


@download_bp.route("/download/id/<file_id>")
def download_file_by_id(file_id):
    """Download file by ID (searches all locations)"""
    current_app.logger.info(f"🎯 DOWNLOAD BY ID: {file_id}")

    try:
        file_path = find_file_by_id(file_id)

        if not file_path:
            current_app.logger.error(f"File not found for ID: {file_id}")
            abort(404, f"File not found: {file_id}")

        current_app.logger.info(f"✅ File found by ID, sending: {file_path}")

        return send_file(str(file_path), as_attachment=True, download_name=file_path.name)

    except Exception as e:
        current_app.logger.error(f"Download by ID error: {str(e)}")
        abort(500, "Download failed")


@download_bp.route("/cleanup/<component>/<filename>", methods=["POST"])
def cleanup_file(component, filename):
    """Cleanup downloaded file after user has downloaded it"""
    try:
        import os

        from werkzeug.utils import secure_filename

        from ..utils.file_manager import get_file_manager

        # Secure the filename
        safe_filename = secure_filename(filename)

        # Validate component
        valid_components = ["compress", "merge", "normalize", "toc", "split", "word"]
        if component not in valid_components:
            return jsonify({"success": False, "error": "Invalid component"}), 400

        # Get file manager for the component
        file_manager = get_file_manager(component=component)
        file_path = file_manager.get_download_path(safe_filename)

        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"🧹 Cleaned up {component} file: {safe_filename}")
            return (
                jsonify({"success": True, "message": f"File {safe_filename} cleaned up", "component": component}),
                200,
            )
        else:
            logger.warning(f"⚠️ File not found for cleanup: {file_path}")
            return jsonify({"success": False, "message": "File not found"}), 404

    except Exception as e:
        logger.error(f"❌ Cleanup error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


# Test route to verify the simple approach works
@download_bp.route("/test-simple/<filename>")
def test_simple_download(filename):
    """Test the simple download approach"""
    try:
        file_path = find_file_anywhere(filename)

        current_app.logger.info(f"Test simple - File path: {file_path}")
        current_app.logger.info(f"Test simple - File exists: {file_path.exists() if file_path else False}")

        if file_path and file_path.exists():
            return send_file(str(file_path), as_attachment=True, download_name=filename)
        else:
            return f"File not found: {filename}", 404

    except Exception as e:
        return f"Error: {str(e)}", 500


@download_bp.route("/debug/current-state")
def debug_current_state():
    """Get the current state of all download locations"""
    result = {"current_working_directory": os.getcwd(), "file_manager_locations": {}, "old_locations": {}}

    # Check file manager locations
    components = ["merge", "normalize", "compress", "toc", "split", "word"]
    for component in components:
        file_manager = get_file_manager(component)
        component_dir = file_manager.get_component_dir()
        result["file_manager_locations"][component] = {
            "path": str(component_dir),
            "exists": component_dir.exists(),
            "files": [],
        }

        if component_dir.exists():
            files = list(component_dir.glob("*"))
            result["file_manager_locations"][component]["files"] = [f.name for f in files if f.is_file()]

    # Check old locations
    old_locations = {"downloads": Path(os.getcwd()) / "downloads", "uploads": Path(os.getcwd()) / "uploads"}

    for name, path in old_locations.items():
        result["old_locations"][name] = {"path": str(path), "exists": path.exists(), "files": []}

        if path.exists():
            files = list(path.glob("*"))
            result["old_locations"][name]["files"] = [f.name for f in files if f.is_file()]

    return jsonify(result)


@download_bp.route("/debug/routes")
def debug_routes():
    """Show all registered routes"""

    routes = []
    for rule in current_app.url_map.iter_rules():
        routes.append({"endpoint": rule.endpoint, "methods": list(rule.methods), "path": str(rule)})
    return jsonify(routes)
