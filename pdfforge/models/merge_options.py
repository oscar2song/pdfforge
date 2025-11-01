"""
Merge Options Data Model
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class MergeOptions:
    """Configuration options for PDF merging"""

    add_headers: bool = False
    page_start: int = 1
    output_filename: str = ""
    scale_factor: float = 0.96
    scale_factor_optimized: float = 0.99
    add_footer_line: bool = False
    smart_spacing: bool = True
    add_page_numbers: bool = True
    page_number_position: str = "bottom-center"
    page_number_font_size: int = 12
    add_bookmarks: bool = True
    add_toc: bool = True

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "MergeOptions":
        """Create MergeOptions from dictionary"""
        if not data:
            return cls()

        return cls(
            add_headers=data.get("add_headers", False),
            page_start=data.get("page_start", 1),
            output_filename=data.get("output_filename", ""),
            scale_factor=data.get("scale_factor", 0.96),
            scale_factor_optimized=data.get("scale_factor_optimized", 0.99),
            add_footer_line=data.get("add_footer_line", False),
            smart_spacing=data.get("smart_spacing", True),
            add_page_numbers=data.get("add_page_numbers", True),
            page_number_position=data.get("page_number_position", "bottom-center"),
            page_number_font_size=data.get("page_number_font_size", 12),
            add_bookmarks=data.get("add_bookmarks", True),
            add_toc=data.get("add_toc", True),
        )

    def validate(self):
        """Validate options"""
        if self.page_start < 1:
            raise ValueError("page_start must be >= 1")

        if not 0 < self.scale_factor <= 1:
            raise ValueError("scale_factor must be between 0 and 1")

        if not 0 < self.scale_factor_optimized <= 1:
            raise ValueError("scale_factor_optimized must be between 0 and 1")

        valid_positions = [
            "top-center",
            "bottom-center",
            "top-right",
            "bottom-right",
        ]
        if self.page_number_position not in valid_positions:
            raise ValueError(f"Invalid page_number_position: {self.page_number_position}")

        if self.page_number_font_size < 6 or self.page_number_font_size > 72:
            raise ValueError("page_number_font_size must be between 6 and 72")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "add_headers": self.add_headers,
            "page_start": self.page_start,
            "output_filename": self.output_filename,
            "scale_factor": self.scale_factor,
            "scale_factor_optimized": self.scale_factor_optimized,
            "add_footer_line": self.add_footer_line,
            "smart_spacing": self.smart_spacing,
            "add_page_numbers": self.add_page_numbers,
            "page_number_position": self.page_number_position,
            "page_number_font_size": self.page_number_font_size,
            "add_bookmarks": self.add_bookmarks,
            "add_toc": self.add_toc,

        }