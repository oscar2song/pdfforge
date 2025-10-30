"""
PDF File Data Model
"""
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import fitz  # type: ignore  # type: ignore  # type: ignore

from ..exceptions.pdf_exceptions import PDFAnalysisError


@dataclass
class PDFFile:
    """Represents a PDF file for processing"""

    path: str
    name: str
    header_line1: str = ""
    header_line2: str = ""
    size_bytes: Optional[int] = None
    page_count: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __init__(self, path: str, name: Optional[str] = None, **kwargs):
        self.path = path
        self.name = name or os.path.basename(path)

        # Set optional attributes from kwargs
        self.header_line1 = kwargs.get('header_line1', '')
        self.header_line2 = kwargs.get('header_line2', '')
        self.size_bytes = kwargs.get('size_bytes')
        self.page_count = kwargs.get('page_count')
        self.metadata = kwargs.get('metadata', {})

    def get_file_size(self):
        return os.path.getsize(self.path)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PDFFile":
        """Create PDFFile from dictionary"""
        return cls(
            path=data["path"],
            name=data.get("name"),
            header_line1=data.get("header_line1", ""),
            header_line2=data.get("header_line2", ""),
            size_bytes=data.get("size_bytes"),
            page_count=data.get("page_count"),
            metadata=data.get("metadata", {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "path": self.path,
            "name": self.name,
            "header_line1": self.header_line1,
            "header_line2": self.header_line2,
            "size_bytes": self.size_bytes,
            "page_count": self.page_count,
            "metadata": self.metadata,
        }

    @property
    def name_without_extension(self) -> str:
        """Get filename without extension."""
        return os.path.splitext(self.name)[0]

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

    def __repr__(self):
        return f"PDFFile(name='{self.name}', pages={self.page_count})"