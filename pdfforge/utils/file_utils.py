# pdfforge/utils/file_utils.py (updated)
"""
File Utility Functions - Updated with File Manager Integration
"""

import logging
import os
import zipfile
from pathlib import Path
from typing import Dict, List
from werkzeug.utils import secure_filename

# Import the file manager
from .file_manager import get_file_manager


def save_uploaded_file(file, upload_folder: str = None) -> str:
    """Save uploaded file to appropriate location."""
    filename = secure_filename(file.filename)

    if upload_folder:
        # Use specified upload folder (backward compatibility)
        filepath = os.path.join(upload_folder, filename)
    else:
        # Use file manager for uploads
        file_manager = get_file_manager()
        filepath = str(file_manager.get_upload_path(filename))

    file.save(filepath)
    return filepath


def create_output_filename(original_filename: str, suffix: str) -> str:
    """Create output filename with suffix."""
    name_without_ext = os.path.splitext(original_filename)[0]
    return f"{name_without_ext}_{suffix}.pdf"


def save_pdf(pdf_bytes, filename: str, component: str = "merge") -> str:
    """
    Save PDF bytes to appropriate download location

    Args:
        pdf_bytes: PDF bytes or BytesIO object
        filename: Output filename
        component: Component type (merge, normalize, compress)

    Returns:
        Path to the saved file
    """
    file_manager = get_file_manager(component)
    file_path = file_manager.get_download_path(filename)

    try:
        if hasattr(pdf_bytes, 'getbuffer'):
            # It's a BytesIO object
            with open(file_path, 'wb') as f:
                f.write(pdf_bytes.getbuffer())
        else:
            # It's bytes
            with open(file_path, 'wb') as f:
                f.write(pdf_bytes)

        logging.info(f"PDF saved to: {file_path}")
        return str(file_path)

    except Exception as e:
        logging.error(f"Error saving PDF: {str(e)}")
        raise


def cleanup_temp_files(file_paths: List[str]):
    """Clean up temporary files."""
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Warning: Could not remove file {file_path}: {e}")


def create_zip_archive(files: List[Dict[str, str]], zip_filename: str, component: str = "merge") -> str:
    """
    Create a zip archive from multiple files

    Args:
        files: List of dicts with 'path' and 'filename' keys
        zip_filename: Name for the zip file
        component: Component type for download location

    Returns:
        Path to the created zip file
    """
    file_manager = get_file_manager(component)
    zip_path = file_manager.get_download_path(zip_filename)

    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_info in files:
                file_path = file_info['path']
                arcname = file_info['filename']

                # Ensure the file exists before adding to zip
                if os.path.exists(file_path):
                    zipf.write(file_path, arcname)
                    logging.info(f"Added {arcname} to zip archive")
                else:
                    logging.warning(f"File not found, skipping: {file_path}")

        logging.info(f"Zip archive created: {zip_path}")

        # Verify the zip file was created
        if os.path.exists(zip_path):
            file_size = os.path.getsize(zip_path)
            logging.info(f"Zip file verified: {zip_path} ({file_size} bytes)")
        else:
            logging.error(f"Zip file was not created: {zip_path}")

        return str(zip_path)

    except Exception as e:
        logging.error(f"Error creating zip archive: {str(e)}")
        raise


# Backward compatibility functions
def get_downloads_folder() -> str:
    """Get downloads folder path (backward compatibility)"""
    file_manager = get_file_manager()
    return str(file_manager.downloads_dir)


def get_uploads_folder() -> str:
    """Get uploads folder path (backward compatibility)"""
    file_manager = get_file_manager()
    return str(file_manager.uploads_dir)
