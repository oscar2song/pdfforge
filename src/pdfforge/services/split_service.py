# pdfforge/services/split_service.py
"""
Split Service - Business Logic for PDF splitting
"""
from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List

from PyPDF2 import PdfReader  # type: ignore

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

            # Rename part files to preferred suffix with page ranges:
            # yyyyMMdd_HHmmss_OriginalFileName_split_pages_start-end.pdf
            renamed_files: List[str] = []

            def _extract_range_from_core_name(path: str) -> tuple[int, int] | None:
                try:
                    name = Path(path).name
                    # core _split_by_page_ranges pattern: <base>_pages_<start>-<end>.pdf
                    m = re.search(r"_pages_(\d+)-(\d+)\.pdf$", name)
                    if m:
                        return int(m.group(1)), int(m.group(2))
                    return None
                except Exception:
                    return None

            ranges: List[tuple[int, int]] = []
            if split_type == "pages" and page_ranges:
                # Try to parse ranges from core filenames
                for p in output_files:
                    rng = _extract_range_from_core_name(p)
                    if rng:
                        ranges.append(rng)
                    else:
                        ranges.append((0, 0))  # placeholder; will fix below if needed
            else:
                # Compute contiguous ranges by counting pages per output file
                start = 1
                for p in output_files:
                    try:
                        reader = PdfReader(p)
                        count = len(reader.pages)
                    except Exception:
                        count = 0
                    end = start + max(count, 0) - 1 if count > 0 else start - 1
                    ranges.append((start, end))
                    start = end + 1 if count > 0 else start

            for p, (start, end) in zip(output_files, ranges):
                try:
                    # If we failed to extract/compute range, fall back to sequential estimation
                    if start <= 0 or end <= 0 or end < start:
                        # Fallback compute by page count only
                        try:
                            reader = PdfReader(p)
                            count = len(reader.pages)
                        except Exception:
                            count = 0
                        # Try to infer start from previous renamed_files last range
                        if renamed_files:
                            prev_name = Path(renamed_files[-1]).name
                            m2 = re.search(r"_split_pages_(\d+)-(\d+)\.pdf$", prev_name)
                            prev_end = int(m2.group(2)) if m2 else 0
                            start = prev_end + 1 if prev_end > 0 else 1
                        else:
                            start = 1
                        end = start + max(count, 1) - 1

                    suffix = f"split_pages_{start}-{end}"
                    new_name = self.file_manager.generate_output_filename(
                        f"{base_name}.pdf", operation="split", suffix=suffix
                    )
                    new_path = str((Path(p).parent / new_name))
                    os.replace(p, new_path)
                    renamed_files.append(new_path)
                except Exception:
                    # If rename fails, keep original
                    renamed_files.append(p)

            output_files = renamed_files

            # Create a ZIP archive for convenience if multiple files
            # Use unified timestamped naming for ZIP: yyyyMMdd_HHmmss_OriginalFileName_split.zip
            zip_filename = self.file_manager.generate_output_filename(f"{base_name}.pdf", "split", ext_override=".zip")
            zip_path = None
            if files_created > 1:
                files_for_zip = [{"path": f, "filename": Path(f).name} for f in output_files if os.path.exists(f)]
                zip_path = create_zip_archive(files_for_zip, zip_filename, component="split")

            # Build per-file component-aware download URLs
            download_urls: List[str] = [f"/download/component/split/{Path(f).stem}" for f in output_files]

            payload: Dict[str, Any] = {
                "success": True,
                "files_created": files_created,
                "output_dir": str(out_dir),
                "output_files": output_files,
                "download_urls": download_urls,
                "zip_filename": Path(zip_path).name if zip_path else None,
                # Legacy zip_download_url removed from primary usage; keep for backward compatibility if needed
                # "zip_download_url": f"/download/{Path(zip_path).name}" if zip_path else None,
                "component_download_url": f"/download/component/split/{Path(zip_path).stem}" if zip_path else None,
                "file_id": Path(zip_path).stem if zip_path else (Path(output_files[0]).stem if output_files else None),
                "split_type": split_type,
            }
            return payload
        except Exception as e:
            logger.exception("Split error")
            return {"success": False, "error": f"Split failed: {str(e)}"}
