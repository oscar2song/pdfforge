"""
Batch Processing Service
Handles operations on multiple files
"""

import os
import tempfile
from typing import Any, Dict, List

from ..utils.file_utils import cleanup_temp_files, create_zip_archive


class BatchService:
    """Service for batch processing operations"""

    @staticmethod
    def create_results_zip(results: List[Dict[str, Any]], operation: str) -> Dict[str, Any]:
        """
        Create ZIP archive from successful processing results

        Args:
            results: List of processing results
            operation: Type of operation (merge, normalize, compress)

        Returns:
            Dict with zip file info
        """
        successful_files = [
            {"path": result["file_path"], "filename": result["filename"]}
            for result in results
            if result.get("success", False)
        ]

        if not successful_files:
            return {
                "success": False,
                "error": "No successful files to package",
            }

        # Create zip archive
        import datetime

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"{operation}_results_{timestamp}.zip"
        zip_path = create_zip_archive(successful_files, zip_filename)

        # Cleanup individual files
        cleanup_temp_files([f["path"] for f in successful_files])

        return {
            "success": True,
            "file_path": zip_path,
            "filename": zip_filename,
            "total_files": len(successful_files),
        }

    @staticmethod
    def process_file_list(files: List) -> List[Dict[str, Any]]:
        """
        Process list of uploaded files into standardized format

        Args:
            files: List of uploaded file objects

        Returns:
            List of file info dicts
        """
        from ..utils.file_utils import save_uploaded_file
        from ..utils.validation import allowed_file

        processed_files = []

        for file in files:
            if file and file.filename and allowed_file(file.filename):
                try:
                    file_path = save_uploaded_file(file, tempfile.gettempdir())
                    processed_files.append(
                        {
                            "path": file_path,
                            "filename": file.filename,
                            "size": os.path.getsize(file_path),
                        }
                    )
                except Exception as e:
                    processed_files.append(
                        {
                            "filename": file.filename,
                            "error": str(e),
                            "success": False,
                        }
                    )

        return processed_files
