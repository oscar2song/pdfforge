"""
File Utility Functions
"""

import logging
import os
from typing import Dict, List

from werkzeug.utils import secure_filename


def save_uploaded_file(file, upload_folder: str) -> str:
    """Save uploaded file to temporary location."""
    filename = secure_filename(file.filename)
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)
    return filepath


def create_output_filename(original_filename: str, suffix: str) -> str:
    """Create output filename with suffix."""
    name_without_ext = os.path.splitext(original_filename)[0]
    return f"{name_without_ext}_{suffix}.pdf"


def save_pdf(pdf_bytes, filename: str) -> str:
    """
    Save PDF bytes to a file in the downloads folder

    Args:
        pdf_bytes: PDF bytes or BytesIO object
        filename: Output filename

    Returns:
        Path to the saved file
    """
    import os

    # Create downloads folder if it doesn't exist
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    downloads_folder = os.path.join(base_dir, 'downloads')
    os.makedirs(downloads_folder, exist_ok=True)

    file_path = os.path.join(downloads_folder, filename)

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
        return file_path

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


def create_zip_archive(files: List[Dict[str, str]], zip_filename: str) -> str:
    """
    Create a zip archive from multiple files

    Args:
        files: List of dicts with 'path' and 'filename' keys
        zip_filename: Name for the zip file

    Returns:
        Path to the created zip file
    """
    import os
    import zipfile

    # Create downloads folder in the project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    downloads_folder = os.path.join(project_root, 'downloads')
    os.makedirs(downloads_folder, exist_ok=True)

    zip_path = os.path.join(downloads_folder, zip_filename)

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

        return zip_path

    except Exception as e:
        logging.error(f"Error creating zip archive: {str(e)}")
        raise
