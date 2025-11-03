"""
Cleanup Routes - File cleanup after download
"""

import logging
import os

from flask import Blueprint, jsonify
from werkzeug.utils import secure_filename

from ..utils.file_manager import get_file_manager

logger = logging.getLogger(__name__)

cleanup_bp = Blueprint("cleanup", __name__, url_prefix="/cleanup")


@cleanup_bp.route("/<component>/<filename>", methods=["POST"])
def cleanup_file(component, filename):
    """
    Cleanup downloaded file after user has downloaded it

    Args:
        component: Component name (compress, merge, normalize)
        filename: Name of file to cleanup
    """
    try:
        # Secure the filename
        safe_filename = secure_filename(filename)

        # Validate component
        valid_components = ["compress", "merge", "normalize"]
        if component not in valid_components:
            return (
                jsonify(
                    {"success": False, "error": f"Invalid component. Must be one of: {', '.join(valid_components)}"}
                ),
                400,
            )

        # Get file manager for the component
        file_manager = get_file_manager(component=component)
        file_path = file_manager.get_download_path(safe_filename)

        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"🧹 Cleaned up {component} file: {safe_filename}")
            return (
                jsonify(
                    {
                        "success": True,
                        "message": "File cleaned up successfully",
                        "component": component,
                        "filename": safe_filename,
                    }
                ),
                200,
            )
        else:
            logger.warning(f"⚠️ File not found for cleanup: {file_path}")
            return jsonify({"success": False, "message": "File not found or already cleaned up"}), 404

    except Exception as e:
        logger.error(f"❌ Cleanup error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
