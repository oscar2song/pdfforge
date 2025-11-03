from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class MergeOptions:
    """Options for PDF merging"""

    add_bookmarks: bool = True
    add_toc: bool = True
    add_headers: bool = False
    add_footer_line: bool = False
    add_page_numbers: bool = True
    page_start: int = 1
    page_number_position: str = "bottom-center"
    page_number_font_size: int = 11
    scale_factor: float = 0.95
    output_filename: str = ""

    # NEW: Page size settings
    target_page_size: str = "letter"  # letter, a4, legal, tabloid, or "auto" to detect
    target_orientation: str = "portrait"  # portrait or landscape

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MergeOptions":
        """Create MergeOptions from dictionary"""
        return cls(
            add_bookmarks=data.get("add_bookmarks", True),
            add_toc=data.get("add_toc", True),
            add_headers=data.get("add_headers", False),
            add_footer_line=data.get("add_footer_line", False),
            add_page_numbers=data.get("add_page_numbers", True),
            page_start=data.get("page_start", 1),
            page_number_position=data.get("page_number_position", "bottom-center"),
            page_number_font_size=data.get("page_number_font_size", 11),
            scale_factor=data.get("scale_factor", 0.95),
            output_filename=data.get("output_filename", ""),
            target_page_size=data.get("target_page_size", "letter"),
            target_orientation=data.get("target_orientation", "portrait"),
        )

    def get_page_dimensions(self) -> tuple[float, float]:
        """
        Get page dimensions in points based on size and orientation
        Returns: (width, height) in points
        """
        # Standard page sizes in points (72 points = 1 inch)
        page_sizes = {
            "letter": (612, 792),  # 8.5" x 11"
            "a4": (595, 842),  # 210mm x 297mm
            "legal": (612, 1008),  # 8.5" x 14"
            "tabloid": (792, 1224),  # 11" x 17"
        }

        size = page_sizes.get(self.target_page_size.lower(), (612, 792))

        # Apply orientation
        if self.target_orientation == "landscape":
            return (size[1], size[0])  # Swap width and height
        return size
