# pdfforge/services/merge_service.py
"""
Merge Service - Business Logic Layer - UPDATED with File Manager
"""

import logging
from pathlib import Path
from typing import Any, Dict, List

from ..core.merge import PDFMerger
from ..models.merge_options import MergeOptions
from ..models.pdf_file import PDFFile
from ..utils.file_manager import get_file_manager
from ..utils.file_utils import cleanup_temp_files

logger = logging.getLogger(__name__)


class MergeService:
    """High-level merge service with business logic"""

    def __init__(self, upload_folder=None):
        """Initialize merge service with file manager"""
        self.file_manager = get_file_manager("merge")

        # For backward compatibility - use file manager's upload directory
        self.upload_folder = self.file_manager.uploads_dir

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

            # Convert to PDFFile objects - IMPORTANT: Preserve individual headers
            pdf_files = []
            for config in file_configs:
                pdf_file = PDFFile.from_dict(config)
                pdf_files.append(pdf_file)

            # Prepare merge options
            merge_options = MergeOptions.from_dict(options)

            # Use the fixed PDFMerger (NOT LegacyPDFMerger)
            merger = PDFMerger(merge_options)
            merged_doc = merger.merge(pdf_files)

            # Get page count BEFORE saving/closing
            page_count = len(merged_doc)
            file_count = len(file_configs)

            # Generate output filename using file manager
            output_filename = self._generate_output_filename(pdf_files, merge_options)

            # Save result to merge-specific downloads directory
            final_output_path = self.file_manager.get_download_path(output_filename)

            # Save the merged document
            merged_doc.save(final_output_path, garbage=4, deflate=True)
            merged_doc.close()
            merged_doc = None

            # Log TOC creation if enabled
            if merge_options.add_toc:
                logger.info(f"Table of Contents created in merged PDF")

            logger.info(f"Merge completed: {output_filename} with {page_count} pages")
            logger.info(f"File saved to: {final_output_path}")

            return {
                "success": True,
                "file_path": str(final_output_path),
                "filename": output_filename,
                "page_count": page_count,
                "file_count": file_count,
                "add_bookmarks": merge_options.add_bookmarks,
                "add_toc": merge_options.add_toc,  # Add TOC status to response
                "file_id": Path(final_output_path).stem,  # Add file ID for download
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
        """Generate output filename using file manager"""
        if options.output_filename:
            filename = options.output_filename
            if not filename.endswith(".pdf"):
                filename += ".pdf"
            return filename

        # Use file manager's naming convention
        if pdf_files:
            first_filename = pdf_files[0].name
            return self.file_manager.generate_output_filename(first_filename, "merged")
        else:
            return self.file_manager.generate_output_filename("documents", "merged")
