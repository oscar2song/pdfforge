"""
Custom exceptions for PDF processing
"""

from .pdf_exceptions import (
    PDFCompressionError,
    PDFCorruptionError,
    PDFError,
    PDFMergeError,
    PDFNormalizationError,
    PDFOCRError,
    PDFPermissionError,
    PDFValidationError,
    PDFSplitError,
)
from .validation_exceptions import (
    FileValidationError,
    OptionsValidationError,
    SizeLimitExceededError,
    UnsupportedFormatError,
    ValidationError,
)

__all__ = [
    # PDF exceptions
    "PDFError",
    "PDFMergeError",
    "PDFNormalizationError",
    "PDFCompressionError",
    "PDFOCRError",
    "PDFValidationError",
    "PDFPermissionError",
    "PDFCorruptionError",
    "PDFSplitError",
    # Validation exceptions
    "ValidationError",
    "FileValidationError",
    "OptionsValidationError",
    "SizeLimitExceededError",
    "UnsupportedFormatError",
]
