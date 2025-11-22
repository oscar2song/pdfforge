"""
Normalize Options Data Model
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class NormalizeOptions:
    """Configuration options for PDF normalization"""

    page_size: str = "letter"
    orientation: str = "portrait"
    add_ocr: bool = False
    force_ocr: bool = False
    custom_width: float = 612
    custom_height: float = 792
    add_header_footer_space: bool = False

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "NormalizeOptions":
        """Create NormalizeOptions from dictionary"""
        if not data:
            return cls()

        return cls(
            page_size=data.get("page_size", "letter"),
            orientation=data.get("orientation", "portrait"),
            add_ocr=data.get("add_ocr", False),
            force_ocr=data.get("force_ocr", False),
            custom_width=data.get("custom_width", 612),
            custom_height=data.get("custom_height", 792),
            add_header_footer_space=data.get("add_header_footer_space", False),
        )

    def validate(self):
        """Validate options"""
        valid_sizes = ["letter", "legal", "A4", "A3", "A5", "custom"]
        if self.page_size not in valid_sizes:
            raise ValueError(f"Invalid page_size: {self.page_size}")

        valid_orientations = ["portrait", "landscape"]
        if self.orientation not in valid_orientations:
            raise ValueError(f"Invalid orientation: {self.orientation}")

        if self.custom_width <= 0 or self.custom_height <= 0:
            raise ValueError("Custom dimensions must be positive")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "page_size": self.page_size,
            "orientation": self.orientation,
            "add_ocr": self.add_ocr,
            "force_ocr": self.force_ocr,
            "custom_width": self.custom_width,
            "custom_height": self.custom_height,
            "add_header_footer_space": self.add_header_footer_space,
        }
