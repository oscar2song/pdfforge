# pdfforge/services/word_service.py
"""
Word Service - Business logic for PDF → Word (DOCX) conversion (free path)

Free edition focuses on digital PDFs. Premium OCR/overlay/multi-format handled by SaaS.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..core.convert_word import WordConversionOptions, convert_pdf_to_docx
from ..utils.file_manager import FilePathManager, get_file_manager
from ..utils.file_utils import create_zip_archive
from ..utils.premium_client import PremiumWordClient
from PyPDF2 import PdfReader  # type: ignore

logger = logging.getLogger(__name__)


class WordService:
    """High-level service to convert PDFs to DOCX."""

    def __init__(self) -> None:
        self.file_manager: FilePathManager = get_file_manager("word")
        self.premium = PremiumWordClient()
        logger.info("WordService initialized")

    def analyze(self, file_path: str) -> Dict[str, Any]:
        """Return simple metadata useful for preview (pages, is_scanned_guess)."""
        try:
            if not os.path.exists(file_path):
                return {"success": False, "error": f"File not found: {file_path}"}

            reader = PdfReader(file_path)
            num_pages = len(reader.pages)
            # Heuristic: try extracting text from first few pages
            sample_pages = min(num_pages, 3)
            text_len = 0
            for i in range(sample_pages):
                try:
                    text = reader.pages[i].extract_text() or ""
                    text_len += len(text.strip())
                except Exception:
                    pass
            is_scanned_guess = text_len < 20
            return {
                "success": True,
                "pages": num_pages,
                "is_scanned_guess": is_scanned_guess,
                "recommendation": "Scanned document detected" if is_scanned_guess else "Digital PDF detected",
            }
        except Exception as e:
            logger.exception("Analyze error")
            return {"success": False, "error": str(e)}

    def _is_scanned_guess(self, file_path: str) -> bool:
        try:
            reader = PdfReader(file_path)
            num_pages = len(reader.pages)
            sample_pages = min(num_pages, 3)
            text_len = 0
            for i in range(sample_pages):
                try:
                    text = reader.pages[i].extract_text() or ""
                    text_len += len(text.strip())
                except Exception:
                    pass
            return text_len < 20
        except Exception:
            return False

    def _build_output_path(self, src_path: str) -> str:
        out_dir = self.file_manager.get_component_dir()
        os.makedirs(out_dir, exist_ok=True)
        # Use unified timestamped naming: yyyyMMdd_HHmmss_OriginalFileName_converted.docx
        original_name = Path(src_path).name
        output_name = self.file_manager.generate_output_filename(original_name, "converted", ext_override=".docx")
        return str(out_dir / output_name)

    def _parse_page_range(self, page_range: Optional[str]) -> Optional[Tuple[int, int]]:
        if not page_range:
            return None
        try:
            if "," in page_range:
                # Only support a single continuous range in free mode for now; take first segment
                page_range = page_range.split(",")[0]
            start_s, end_s = [p.strip() for p in page_range.split("-")]
            return int(start_s), int(end_s)
        except Exception:
            return None

    def convert_single(self, file_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if not os.path.exists(file_path):
                return {"success": False, "error": f"File not found: {file_path}"}

            # Decide whether to use premium pipeline
            want_premium = bool(options.get("use_premium") or options.get("force_ocr") or options.get("ocr"))
            auto_on_scanned = bool(options.get("auto_premium_when_scanned", True))
            if not want_premium and auto_on_scanned and self.premium.is_enabled():
                # Light heuristic on PDF to detect scanned docs
                try:
                    if self._is_scanned_guess(file_path):
                        want_premium = True
                except Exception:
                    pass

            if self.premium.is_enabled() and want_premium:
                # Pass through options; SaaS controls OCR/lang/overlay, etc.
                premium_opts: Dict[str, Any] = {
                    "page_range": options.get("page_range"),
                    "languages": options.get("languages", ["eng", "chi_sim", "fra"]),
                    "ocr": bool(options.get("ocr", True) or options.get("force_ocr", False)),
                    "overlay": bool(options.get("overlay", False)),
                    "output_format": options.get("output_format", "docx"),
                    "detect_tables": bool(options.get("detect_tables", True)),
                    "merge_paragraphs": bool(options.get("merge_paragraphs", True)),
                }
                result = self.premium.convert_pdf_to_docx(file_path, premium_opts)
                # Normalize payload to include component-aware download URL if we downloaded the file locally
                if result.get("success") and result.get("output_file"):
                    out_file = str(result.get("output_file"))
                    file_id = Path(out_file).stem
                    result.setdefault("file_id", file_id)
                    result.setdefault("download_url", f"/download/component/word/{file_id}")
                return result

            # Free local path (digital PDFs)
            page_range = self._parse_page_range(options.get("page_range"))
            merge_paragraphs = bool(options.get("merge_paragraphs", True))
            detect_tables = bool(options.get("detect_tables", True))
            keep_text_boxes = bool(options.get("keep_text_boxes", False))
            images_as_background = bool(options.get("images_as_background", False))
            keep_images_original = bool(options.get("keep_images_original", False))
            image_dpi = int(options.get("image_dpi", 150))

            conv_opts = WordConversionOptions(
                page_range=page_range,
                merge_paragraphs=merge_paragraphs,
                detect_tables=detect_tables,
                keep_text_boxes=keep_text_boxes,
                images_as_background=images_as_background,
                keep_images_original=keep_images_original,
                image_dpi=image_dpi,
            )

            output_path = self._build_output_path(file_path)
            result = convert_pdf_to_docx(file_path, output_path, conv_opts)
            if not result.get("success"):
                return result

            out_file = result.get("output_file")
            file_id = Path(out_file).stem if out_file else None
            download_url = f"/download/component/word/{file_id}" if file_id else None

            payload = {
                "success": True,
                "output_file": out_file,
                "pages_converted": result.get("pages_converted", 0),
                "file_id": file_id,
                "download_url": download_url,
            }
            return payload
        except Exception as e:
            logger.exception("Convert single error")
            return {"success": False, "error": f"Conversion failed: {str(e)}"}

    def convert_batch(self, file_paths: List[str], options: Dict[str, Any]) -> Dict[str, Any]:
        try:
            outputs: List[str] = []
            errors: List[Dict[str, Any]] = []
            download_urls: List[str] = []
            for fp in file_paths:
                res = self.convert_single(fp, options)
                if res.get("success") and res.get("output_file"):
                    out_path = str(res["output_file"])
                    outputs.append(out_path)
                    # Prefer the component-aware URL from convert_single if available
                    dl = res.get("download_url") or f"/download/component/word/{Path(out_path).stem}"
                    download_urls.append(dl)
                else:
                    errors.append({"file": fp, "error": res.get("error")})

            files_created = len(outputs)
            zip_path = None
            if files_created > 1:
                files_for_zip = [{"path": f, "filename": Path(f).name} for f in outputs if os.path.exists(f)]
                zip_path = create_zip_archive(files_for_zip, "word_output.zip", component="word")

            return {
                "success": True if files_created > 0 else False,
                "output_files": outputs,
                "download_urls": download_urls,
                "files_created": files_created,
                "zip_filename": Path(zip_path).name if zip_path else None,
                "component_download_url": f"/download/component/word/{Path(zip_path).stem}" if zip_path else None,
                "file_id": Path(zip_path).stem if zip_path else (Path(outputs[0]).stem if outputs else None),
                "errors": errors,
            }
        except Exception as e:
            logger.exception("Convert batch error")
            return {"success": False, "error": f"Batch conversion failed: {str(e)}"}
