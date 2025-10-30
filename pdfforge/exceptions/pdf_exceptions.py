"""
PDF-specific exceptions
"""


class PDFError(Exception):
    """Base exception for PDF-related errors"""


class PDFMergeError(PDFError):
    """Raised when PDF merging fails"""


class PDFNormalizationError(PDFError):
    """Raised when PDF normalization fails"""


class PDFCompressionError(PDFError):
    """Raised when PDF compression fails"""


class PDFOCRError(PDFError):
    """Raised when OCR processing fails"""


class PDFValidationError(PDFError):
    """Raised when PDF validation fails"""


class PDFPermissionError(PDFError):
    """Raised when there are permission issues with PDF files"""


class PDFCorruptionError(PDFError):
    """Raised when a PDF file is corrupted"""


class PDFAnalysisError:
    """Raised when a PDF file is Analysis"""