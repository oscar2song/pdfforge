# pdfforge/services/split_service.py
"""
Split Service - Business Logic for PDF splitting
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List

from ..core.split import PDFSplitterCore
from ..utils.file_manager import FilePathManager, get_file_manager
from ..utils.file_utils import create_zip_archive

logger = logging.getLogger(__name__)


class SplitService:
    """High-level service to split PDFs using core splitter and file manager."""

    def __init__(self) -> None:
        self.file_manager: FilePathManager = get_file_manager("split")
        self.splitter = PDFSplitterCore(verbose=False)
        logger.info("SplitService initialized")

    def analyze(self, file_path: str) -> Dict[str, Any]:
        try:
            return self.splitter.analyze(file_path)
        except Exception as e:
            logger.exception("Analyze error")
            return {"success": False, "error": str(e)}

    def split(self, file_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform split according to options.
        Options:
          - split_type: 'pages' | 'size' | 'bookmarks'
          - page_ranges: str (for pages mode)
          - pages_per_file: int (for pages mode without ranges)
          - max_size_mb: float (for size mode)
        """
        try:
            split_type = options.get("split_type", "pages")
            pages_per_file = int(options.get("pages_per_file", 1))
            page_ranges = options.get("page_ranges")
            max_size_mb = float(options.get("max_size_mb", 10.0))

            # Output directory per original file name under component dir
            base_name = Path(file_path).stem
            out_dir = self.file_manager.get_component_dir() / base_name
            os.makedirs(out_dir, exist_ok=True)

            result = self.splitter.split(
                input_path=file_path,
                output_dir=str(out_dir),
                split_type=split_type,
                pages_per_file=pages_per_file,
                page_ranges=page_ranges,
                max_size_mb=max_size_mb,
            )

            if not result.get("success"):
                return result

            output_files: List[str] = result.get("output_files", [])
            files_created = len(output_files)

            # Create a ZIP archive for convenience if multiple files
            zip_filename = f"{base_name}_split.zip"
            zip_path = None
            if files_created > 1:
                files_for_zip = [{"path": f, "filename": Path(f).name} for f in output_files if os.path.exists(f)]
                zip_path = create_zip_archive(files_for_zip, zip_filename, component="split")

            payload: Dict[str, Any] = {
                "success": True,
                "files_created": files_created,
                "output_dir": str(out_dir),
                "output_files": output_files,
                "zip_filename": Path(zip_path).name if zip_path else None,
                "zip_download_url": f"/download/{Path(zip_path).name}" if zip_path else None,
                "component_download_url": f"/download/component/split/{Path(zip_path).stem}" if zip_path else None,
                "file_id": Path(zip_path).stem if zip_path else Path(output_files[0]).stem if output_files else None,
                "split_type": split_type,
            }
            return payload
        except Exception as e:
            logger.exception("Split error")
            return {"success": False, "error": f"Split failed: {str(e)}"}
