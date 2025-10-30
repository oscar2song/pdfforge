@download_bp.route('/cleanup/<file_type>/<filename>', methods=['POST'])
def cleanup_file(file_type, filename):
    """Clean up temporary files after download"""
    try:
        downloads_folder = current_app.config.get('DOWNLOAD_FOLDER', 'downloads')
        file_path = os.path.join(downloads_folder, filename)

        # Security check
        if '..' in filename or filename.startswith('/'):
            abort(400, "Invalid filename")

        if os.path.exists(file_path):
            os.remove(file_path)
            current_app.logger.info(f"Cleaned up file: {filename}")

        return {"success": True, "message": "File cleaned up"}

    except Exception as e:
        current_app.logger.error(f"Cleanup error: {str(e)}")
        return {"success": False, "error": str(e)}, 500