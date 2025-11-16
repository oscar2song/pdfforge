"""
TOC Service - Business Logic Layer
Updated to match merge_service.py patterns and use fixed TOCGenerator
"""

import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import fitz

from ..core.toc import BookmarkEntry, BookmarkManager, TOCGenerator, TOCStyle
from ..utils.file_manager import FilePathManager, get_file_manager
from ..utils.file_utils import cleanup_temp_files

logger = logging.getLogger(__name__)


class TOCService:
    """Service for TOC operations using PDFForge file management."""

    def __init__(self, upload_folder: str | None = None) -> None:
        """Initialize TOC service with file manager"""
        self.file_manager: FilePathManager = get_file_manager("toc")
        self.toc_generator = TOCGenerator()

        # For backward compatibility - use file manager's upload directory
        self.upload_folder = self.file_manager.uploads_dir

        logger.info(f"TOCService initialized with upload folder: {self.upload_folder}")

    def extract_bookmarks_from_file(self, input_path, original_filename):
        """
        Extract bookmarks and return user-friendly page numbers using TOCGenerator.
        """
        pdf_doc = None
        try:
            # Use PyMuPDF (fitz) for better compatibility
            pdf_doc = fitz.open(input_path)

            # Detect existing TOC pages at the very beginning (for UI context)
            try:
                old_toc_pages_detected = self.toc_generator._detect_existing_toc_pages(pdf_doc)
            except Exception:
                old_toc_pages_detected = 0

            # Extract bookmarks using TOCGenerator (already normalized to exclude old TOC pages)
            bookmarks = self.toc_generator.extract_bookmarks(pdf_doc)

            # Convert to dictionary format for JSON response
            bookmarks_dict = [
                {"title": bm.title, "page": bm.page, "level": bm.level}  # Already 1-based from TOCGenerator
                for bm in bookmarks
            ]

            page_count = len(pdf_doc)

            # Close document before returning
            pdf_doc.close()
            pdf_doc = None

            logger.info(f"Extracted {len(bookmarks_dict)} bookmarks from {original_filename}")

            return {
                "success": True,
                "filename": original_filename,
                "page_count": page_count,
                "bookmarks": bookmarks_dict,
                "old_toc_pages_detected": int(old_toc_pages_detected),
            }

        except Exception as e:
            logger.error(f"Error extracting bookmarks: {e}")
            # Ensure document is closed even on error
            if pdf_doc:
                try:
                    pdf_doc.close()
                except Exception:
                    pass
            return {"success": False, "error": str(e)}

    def add_toc_to_file(self, input_path, original_filename, bookmarks_data, toc_style_config):
        """
        Add TOC pages and update bookmarks with proper page offset using TOCGenerator.
        """
        try:
            # Convert bookmarks data to BookmarkEntry objects
            bookmarks = []
            for bm_data in bookmarks_data:
                bookmarks.append(
                    BookmarkEntry(
                        title=bm_data["title"],
                        page=bm_data["page"],  # User provides 1-based page numbers
                        level=bm_data.get("level", 0),
                    )
                )

            # Create TOC style from config
            toc_style = TOCStyle(
                title=toc_style_config.get("title", "Table of Contents"),
                show_page_numbers=toc_style_config.get("show_page_numbers", True),
                leader_dots=toc_style_config.get("leader_dots", True),
                page_number_position=toc_style_config.get("page_number_position", "bottom-center"),
                page_number_font_size=toc_style_config.get("page_number_font_size", 10),
            )

            # Set the style
            self.toc_generator.style = toc_style

            # Generate output filename
            output_filename = f"{Path(original_filename).stem}_with_toc.pdf"
            output_path = self.file_manager.get_download_path(output_filename)

            # Add TOC to PDF using TOCGenerator
            result = self.toc_generator.add_toc_to_pdf(
                input_pdf_path=input_path,
                output_pdf_path=str(output_path),
                bookmarks=bookmarks,
                page_number_position=toc_style.page_number_position,
                page_number_font_size=toc_style.page_number_font_size,
            )

            if result["success"]:
                # Generate file_id for download
                file_id = self._save_to_component_dir(str(output_path), output_filename)

                logger.info(f"TOC generation successful: {output_filename}")

                return {
                    "success": True,
                    "file_id": file_id,
                    "filename": output_filename,
                    "toc_pages": result.get("toc_pages", 0),
                    "bookmark_count": result.get("bookmark_count", 0),
                }
            else:
                return result

        except Exception as e:
            logger.error(f"Error adding TOC: {e}")
            return {"success": False, "error": str(e)}

    def update_pdf_bookmarks_in_file(self, input_path, original_filename, bookmarks_data):
        """
        Update PDF bookmarks without adding TOC pages using TOCGenerator.
        Uses page numbers as provided by user.
        """
        try:
            # Convert bookmarks data to BookmarkEntry objects
            bookmarks = []
            for bm_data in bookmarks_data:
                bookmarks.append(
                    BookmarkEntry(
                        title=bm_data["title"],
                        page=bm_data["page"],  # User provides 1-based page numbers
                        level=bm_data.get("level", 0),
                    )
                )

            # Generate output filename
            output_filename = f"{Path(original_filename).stem}_with_bookmarks.pdf"
            output_path = self.file_manager.get_download_path(output_filename)

            # Update bookmarks only using TOCGenerator
            result = self.toc_generator.update_bookmarks_only(
                input_pdf_path=input_path, output_pdf_path=str(output_path), bookmarks=bookmarks
            )

            if result["success"]:
                # Generate file_id for download
                file_id = self._save_to_component_dir(str(output_path), output_filename)

                logger.info(f"Bookmarks update successful: {output_filename}")

                return {
                    "success": True,
                    "file_id": file_id,
                    "filename": output_filename,
                    "bookmark_count": len(bookmarks),
                }
            else:
                return result

        except Exception as e:
            logger.error(f"Error updating bookmarks: {e}")
            return {"success": False, "error": str(e)}

    def _save_to_component_dir(self, file_path: str, filename: str) -> str:
        """
        Save file to component directory and return file_id.

        Args:
            file_path: Source file path
            filename: Target filename

        Returns:
            File ID for download
        """
        try:
            # Generate unique file ID
            file_id = str(uuid.uuid4())[:8]

            # Get component directory
            component_dir = self.file_manager.get_component_dir()

            # Ensure component directory exists
            component_dir.mkdir(parents=True, exist_ok=True)

            # Create output filename with file_id
            name_without_ext = Path(filename).stem
            extension = Path(filename).suffix
            output_filename = f"{name_without_ext}_{file_id}{extension}"
            output_path = component_dir / output_filename

            # Copy file to component directory
            import shutil

            shutil.copy2(file_path, output_path)

            logger.info(f"Saved file to component directory: {output_path}")
            return file_id

        except Exception as e:
            logger.error(f"Error saving to component directory: {e}")
            # Fallback: return the original filename without ID
            return Path(filename).stem


class MergeWithTOCService:
    """Service for merging PDFs with TOC generation."""

    def __init__(self, upload_folder: str | None = None) -> None:
        """Initialize merge with TOC service with file manager"""
        self.file_manager: FilePathManager = get_file_manager("merge")

        # For backward compatibility - use file manager's upload directory
        self.upload_folder = self.file_manager.uploads_dir

        logger.info(f"MergeWithTOCService initialized with upload folder: {self.upload_folder}")

    def get_merge_preview(self, file_paths: List[str], filenames: List[str]) -> Dict[str, Any]:
        """
        Get preview information for PDF merge operation.

        Args:
            file_paths: List of uploaded file paths
            filenames: List of original filenames

        Returns:
            Preview data with page counts and suggested bookmarks
        """
        try:
            logger.info(f"Generating merge preview for {len(file_paths)} files")

            file_info = []
            total_pages = 0
            current_page = 1

            for idx, (file_path, filename) in enumerate(zip(file_paths, filenames)):
                file_path_obj = Path(file_path)

                if not file_path_obj.exists():
                    logger.warning(f"File not found: {file_path}")
                    continue

                # Get page count
                pdf_doc = fitz.open(str(file_path_obj))
                page_count = len(pdf_doc)
                pdf_doc.close()

                # Generate suggested bookmark
                suggested_bookmark = BookmarkManager.create_bookmark_from_filename(filename, current_page)

                file_info.append(
                    {
                        "index": idx,
                        "filename": filename,
                        "page_count": page_count,
                        "start_page": current_page,
                        "end_page": current_page + page_count - 1,
                        "suggested_bookmark": suggested_bookmark.title,
                    }
                )

                total_pages += page_count
                current_page += page_count

            logger.info(f"Preview generated: {len(file_info)} files, {total_pages} total pages")

            return {"success": True, "files": file_info, "total_pages": total_pages, "file_count": len(file_paths)}

        except Exception as e:
            logger.exception("Error generating merge preview")
            return {"success": False, "error": str(e)}

    def merge_pdfs_with_toc(
        self,
        file_paths: List[str],
        filenames: List[str],
        bookmark_labels: Optional[Dict[int, str]] = None,
        output_filename: Optional[str] = None,
        add_toc: bool = False,
        toc_style_config: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Merge multiple PDFs with optional TOC generation.

        Args:
            file_paths: List of uploaded file paths
            filenames: List of original filenames
            bookmark_labels: Dict mapping file index to custom bookmark label
            output_filename: Custom output filename
            add_toc: Whether to generate TOC page
            toc_style_config: Optional TOC styling configuration

        Returns:
            Result dictionary with file_id
        """
        try:
            logger.info(f"Starting merge with TOC for {len(file_paths)} files")

            # Validate file paths
            valid_paths = []
            for file_path in file_paths:
                path = Path(file_path)
                if path.exists():
                    valid_paths.append(str(path))
                else:
                    logger.warning(f"File not found: {file_path}")

            if len(valid_paths) < 2:
                return {"success": False, "error": "At least 2 valid PDF files required"}

            # Generate output filename using file manager
            if output_filename:
                if not output_filename.endswith(".pdf"):
                    output_filename += ".pdf"
                # Use file manager to ensure unique filename
                base_name = Path(output_filename).stem
                output_filename = self.file_manager.generate_output_filename(base_name, "merged")
            else:
                # Use first file as base
                base_name = Path(filenames[0]).stem
                output_filename = self.file_manager.generate_output_filename(base_name, "merged")

            # Get output path in component directory
            output_path = self.file_manager.get_download_path(output_filename)

            logger.info(f"Output will be saved to: {output_path}")

            # Create TOC style
            toc_style = None
            if toc_style_config:
                toc_style = TOCStyle(**toc_style_config)

            # Merge with bookmarks and TOC
            result = BookmarkManager.merge_pdfs_with_bookmarks(
                pdf_files=valid_paths,
                bookmark_labels=bookmark_labels,
                output_path=str(output_path),
                add_toc=add_toc,
                toc_style=toc_style,
            )

            # Cleanup source files
            cleanup_temp_files(file_paths)

            if result["success"]:
                # Extract file_id from output path
                file_id = Path(output_path).stem

                logger.info(f"Merge completed: {output_filename}")
                logger.info(f"File saved to: {output_path}")

                if add_toc:
                    logger.info("Table of Contents created in merged PDF")

                return {
                    "success": True,
                    "file_id": file_id,
                    "filename": output_filename,
                    "file_path": str(output_path),
                    "total_pages": result.get("total_pages", 0),
                    "bookmark_count": result.get("bookmark_count", 0),
                    "has_toc": result.get("has_toc", False),
                    "toc_pages": result.get("toc_pages", 0),
                }
            else:
                return result

        except Exception as e:
            logger.exception("Error merging PDFs with TOC")

            # Cleanup on error
            cleanup_temp_files(file_paths)

            return {"success": False, "error": str(e)}
