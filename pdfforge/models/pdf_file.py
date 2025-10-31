"""
PDF File Data Model
"""
import logging
from dataclasses import dataclass
from typing import Any, Dict
import os

from pdfforge.exceptions.pdf_exceptions import PDFAnalysisError

logger = logging.getLogger(__name__)

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

    @property
    def exists(self) -> bool:
        """Check if file exists"""
        return os.path.exists(self.path)

    def analyze(self):
        """Analyze PDF properties"""
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(self.path)
            self.page_count = len(doc)
            self.original_size = os.path.getsize(self.path)

            # Get page sizes
            self.page_sizes = []
            for page_num in range(self.page_count):
                page = doc[page_num]
                rect = page.rect
                self.page_sizes.append({
                    'width': rect.width,
                    'height': rect.height
                })

            doc.close()

        except Exception as e:
            logging.error(f"Error analyzing PDF {self.path}: {str(e)}")
            raise PDFAnalysisError(f"Could not analyze PDF: {str(e)}")
