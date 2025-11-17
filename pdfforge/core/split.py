"""
Core PDF splitting logic using PyPDF2.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Tuple

try:
    from PyPDF2 import PdfReader, PdfWriter

    HAS_PDF_DEPS = True
except Exception:
    HAS_PDF_DEPS = False

from ..exceptions.pdf_exceptions import PDFSplitError


def _get_file_size_mb(file_path: str | os.PathLike[str]) -> float:
    return os.path.getsize(file_path) / (1024 * 1024)


class PDFSplitterCore:
    """Pure splitting implementation. Stateless and reusable."""

    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose

    def split(
        self,
        input_path: str,
        output_dir: str | os.PathLike[str],
        split_type: str = "pages",
        pages_per_file: int = 1,
        page_ranges: str | None = None,
        max_size_mb: float = 10.0,
    ) -> Dict[str, Any]:
        if not HAS_PDF_DEPS:
            raise PDFSplitError("PyPDF2 is not installed. Please add PyPDF2 to requirements.txt and install it.")

        try:
            if not os.path.exists(input_path):
                raise PDFSplitError(f"Input file not found: {input_path}")

            os.makedirs(output_dir, exist_ok=True)

            if split_type == "pages" and page_ranges:
                output_files = self._split_by_page_ranges(input_path, str(output_dir), page_ranges)
            elif split_type == "pages":
                output_files = self._split_by_fixed_pages(input_path, str(output_dir), pages_per_file)
            elif split_type == "size":
                output_files = self._split_by_size(input_path, str(output_dir), max_size_mb)
            elif split_type == "bookmarks":
                output_files = self._split_by_bookmarks(input_path, str(output_dir))
            else:
                raise PDFSplitError(f"Unknown split type: {split_type}")

            return {
                "success": True,
                "files_created": len(output_files),
                "output_files": output_files,
                "original_size_mb": _get_file_size_mb(input_path),
                "total_output_size_mb": sum(_get_file_size_mb(f) for f in output_files if os.path.exists(f)),
            }
        except PDFSplitError:
            raise
        except Exception as e:
            raise PDFSplitError(str(e))

    def analyze(self, input_path: str) -> Dict[str, Any]:
        if not HAS_PDF_DEPS:
            raise PDFSplitError("PyPDF2 is not installed. Please add PyPDF2 to requirements.txt and install it.")
        if not os.path.exists(input_path):
            raise PDFSplitError(f"File not found: {input_path}")
        try:
            reader = PdfReader(input_path)
            total_pages = len(reader.pages)
            size_mb = _get_file_size_mb(input_path)
            has_bookmarks = bool(getattr(reader, "outline", None))
            avg_mb_per_page = size_mb / total_pages if total_pages else 0.0
            return {
                "success": True,
                "total_pages": total_pages,
                "size_mb": size_mb,
                "avg_mb_per_page": avg_mb_per_page,
                "has_bookmarks": has_bookmarks,
            }
        except Exception as e:
            raise PDFSplitError(str(e))

    # Internal helpers
    def _split_by_page_ranges(self, input_path: str, output_dir: str, page_ranges: str) -> List[str]:
        reader = PdfReader(input_path)
        total_pages = len(reader.pages)
        base_name = os.path.splitext(os.path.basename(input_path))[0]

        # Special handling: if user provides only comma-separated start pages (e.g., "1,63"),
        # interpret them as segment starts: 1-62, 63-end (and generalized for N starts).
        raw_parts = [p.strip() for p in page_ranges.split(",") if p.strip()]
        only_starts_mode = ("-" not in page_ranges) and (len(raw_parts) >= 2)

        ranges: List[Tuple[int, int]]
        if only_starts_mode:
            # Parse and validate start pages
            try:
                starts = sorted({int(p) for p in raw_parts})
            except ValueError:
                raise PDFSplitError("Invalid page number in start pages list")
            if any(s < 1 or s > total_pages for s in starts):
                raise PDFSplitError(f"Start pages must be within 1..{total_pages}")
            # Build contiguous ranges from each start to one before the next start; last goes to end
            ranges = []
            for i, s in enumerate(starts):
                e = (starts[i + 1] - 1) if i < len(starts) - 1 else total_pages
                if e < s:
                    raise PDFSplitError("Computed range end before start; check start pages order/values")
                ranges.append((s, e))
        else:
            # Default behavior: explicit ranges and single page specs
            ranges = self._parse_page_ranges(page_ranges)

        output_files: List[str] = []
        for start, end in ranges:
            if start < 1 or end > total_pages or end < start:
                raise PDFSplitError(f"Invalid page range {start}-{end} for {total_pages} pages")
            writer = PdfWriter()
            for page_num in range(start - 1, end):
                writer.add_page(reader.pages[page_num])
            output_path = os.path.join(output_dir, f"{base_name}_pages_{start}-{end}.pdf")
            with open(output_path, "wb") as f:
                writer.write(f)
            output_files.append(output_path)
        return output_files

    def _split_by_fixed_pages(self, input_path: str, output_dir: str, pages_per_file: int) -> List[str]:
        if pages_per_file <= 0:
            raise PDFSplitError("pages_per_file must be a positive integer")
        reader = PdfReader(input_path)
        total_pages = len(reader.pages)
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_files: List[str] = []
        file_index = 1
        for start in range(0, total_pages, pages_per_file):
            end = min(start + pages_per_file, total_pages)
            writer = PdfWriter()
            for p in range(start, end):
                writer.add_page(reader.pages[p])
            output_path = os.path.join(output_dir, f"{base_name}_part_{file_index}.pdf")
            with open(output_path, "wb") as f:
                writer.write(f)
            output_files.append(output_path)
            file_index += 1
        return output_files

    def _split_by_size(self, input_path: str, output_dir: str, max_size_mb: float) -> List[str]:
        if max_size_mb <= 0:
            raise PDFSplitError("max_size_mb must be > 0")
        reader = PdfReader(input_path)
        total_pages = len(reader.pages)
        original_size = _get_file_size_mb(input_path)
        if total_pages == 0:
            return []
        avg = max(original_size / total_pages, 0.0001)
        pages_per_file = max(1, int(max_size_mb / avg))
        return self._split_by_fixed_pages(input_path, output_dir, pages_per_file)

    def _split_by_bookmarks(self, input_path: str, output_dir: str) -> List[str]:
        reader = PdfReader(input_path)
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        if not getattr(reader, "outline", None):
            raise PDFSplitError("PDF has no bookmarks to split by")
        bookmarks = self._extract_bookmark_pages(reader)
        if not bookmarks:
            raise PDFSplitError("Could not extract valid bookmark page numbers")
        output_files: List[str] = []
        total_pages = len(reader.pages)
        for i, (title, start_page) in enumerate(bookmarks):
            if i < len(bookmarks) - 1:
                end_page = bookmarks[i + 1][1] - 1
            else:
                end_page = total_pages
            safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "-", "_")).strip()[:50]
            writer = PdfWriter()
            for p in range(start_page - 1, end_page):
                writer.add_page(reader.pages[p])
            output_path = os.path.join(output_dir, f"{base_name}_{i + 1:02d}_{safe_title}.pdf")
            with open(output_path, "wb") as f:
                writer.write(f)
            output_files.append(output_path)
        return output_files

    def _parse_page_ranges(self, page_ranges: str) -> List[Tuple[int, int]]:
        ranges: List[Tuple[int, int]] = []
        for part in page_ranges.split(","):
            part = part.strip()
            if not part:
                continue
            if "-" in part:
                start_s, end_s = part.split("-", 1)
                start, end = int(start_s), int(end_s)
                ranges.append((start, end))
            else:
                p = int(part)
                ranges.append((p, p))
        return ranges

    def _extract_bookmark_pages(self, reader: PdfReader) -> List[Tuple[str, int]]:
        bookmarks: List[Tuple[str, int]] = []

        def walk(outline):
            for item in outline:
                if isinstance(item, list):
                    walk(item)
                else:
                    try:
                        title = item.title if hasattr(item, "title") else str(item)
                        page = reader.get_destination_page_number(item) + 1
                        bookmarks.append((title, page))
                    except Exception:
                        continue

        walk(reader.outline)
        uniq = []
        seen = set()
        for t, p in sorted(bookmarks, key=lambda x: x[1]):
            if p not in seen:
                uniq.append((t, p))
                seen.add(p)
        return uniq
