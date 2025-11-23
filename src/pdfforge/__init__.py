"""
PDFForge - Open Source PDF Processing Library
"""

__version__ = "3.0.0"

# Export service classes
from .services.merge_service import MergeService
from .services.compress_service import CompressService
from .services.normalize_service import NormalizeService

# Aliases for backward compatibility with plugin expectations
PDFMerger = MergeService
PDFCompressor = CompressService
PDFNormalizer = NormalizeService

__all__ = [
    'MergeService',
    'CompressService',
    'NormalizeService',
    'PDFMerger',
    'PDFCompressor',
    'PDFNormalizer',
]
