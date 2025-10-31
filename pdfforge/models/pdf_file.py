"""
PDF File Data Model
"""

from dataclasses import dataclass
from typing import Any, Dict
import os


@dataclass
class PDFFile:
    """Represents a PDF file with metadata"""

    path: str
    name: str
    header_line1: str = ""
    header_line2: str = ""

    @property
    def name_without_extension(self) -> str:
        """Get filename without extension"""
        return os.path.splitext(self.name)[0]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PDFFile":
        """Create PDFFile from dictionary"""
        return cls(
            path=data.get("path", ""),
            name=data.get("name", ""),
            header_line1=data.get("header_line1", ""),
            header_line2=data.get("header_line2", "")
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "path": self.path,
            "name": self.name,
            "header_line1": self.header_line1,
            "header_line2": self.header_line2
        }