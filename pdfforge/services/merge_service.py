"""
Merge Service - Business Logic Layer
"""

import logging
import os
import tempfile
from typing import Any, Dict, List

from ..core.merge import PDFMerger
from ..models.merge_options import MergeOptions
from ..models.pdf_file import PDFFile
from ..utils.file_utils import cleanup_temp_files

logger = logging.getLogger(__name__)


class MergeService:
    """High-level merge service with business logic"""

    def __init__(self, upload_folder=None):
        """Initialize merge service with optional upload folder"""
        if upload_folder is None:
            # Get the project root directory (where the main app.py is)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            self.upload_folder = os.path.join(project_root, "uploads")
        else:
            self.upload_folder = upload_folder

        # Ensure upload folder exists
        os.makedirs(self.upload_folder, exist_ok=True)
        logger.info(f"MergeService initialized with upload folder: {self.upload_folder}")

    def merge_files(
            self, file_configs: List[Dict[str, Any]], options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge multiple PDF files into a single PDF
        """
        merged_doc = None

        try:
            logger.info(f"Starting merge process for {len(file_configs)} files")

            # Convert to PDFFile objects
            pdf_files = []
            for config in file_configs:
                pdf_file = PDFFile.from_dict(config)
                pdf_files.append(pdf_file)

            # Prepare merge options
            merge_options = MergeOptions.from_dict(options)

            # Perform merge
            merger = PDFMerger(merge_options)
            merged_doc = merger.merge(pdf_files)

            # Get page count BEFORE saving/closing
            page_count = len(merged_doc)
            file_count = len(file_configs)

            # Generate output filename
            output_filename = self._generate_output_filename(pdf_files, merge_options)

            # Save result directly to uploads folder
            final_output_path = os.path.join(self.upload_folder, output_filename)

            # Save the merged document
            merged_doc.save(final_output_path, garbage=4, deflate=True)
            merged_doc.close()
            merged_doc = None

            logger.info(f"Merge completed: {output_filename} with {page_count} pages")
            logger.info(f"File saved to: {final_output_path}")

            return {
                "success": True,
                "file_path": final_output_path,
                "filename": output_filename,
                "page_count": page_count,
                "file_count": file_count,
            }

        except Exception as e:
            logger.exception(f"Error during merge: {str(e)}")
            return {
                "success": False,
                "error": f"Merge failed: {str(e)}",
            }
        finally:
            # Always close the document if it's still open
            if merged_doc:
                try:
                    merged_doc.close()
                except:
                    pass

            # Cleanup source files
            if "file_configs" in locals():
                source_paths = [fc.get("path") for fc in file_configs if fc.get("path")]
                cleanup_temp_files(source_paths)

    def _generate_output_filename(self, pdf_files: List[PDFFile], options: MergeOptions) -> str:
        """Generate output filename"""
        if options.output_filename:
            filename = options.output_filename
            if not filename.endswith(".pdf"):
                filename += ".pdf"
            return filename

        # Use first file's name with merged suffix
        if pdf_files:
            first_filename = pdf_files[0].name
            # Remove any existing extensions and add _merged.pdf
            base_name = os.path.splitext(first_filename)[0]
            return f"{base_name}_merged.pdf"
        else:
            return "merged.pdf"