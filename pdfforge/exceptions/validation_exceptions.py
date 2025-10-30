"""
Validation exceptions
"""


class ValidationError(Exception):
    """Base exception for validation errors"""


class FileValidationError(ValidationError):
    """Raised when file validation fails"""


class OptionsValidationError(ValidationError):
    """Raised when options validation fails"""


class SizeLimitExceededError(ValidationError):
    """Raised when file size limits are exceeded"""


class UnsupportedFormatError(ValidationError):
    """Raised when an unsupported file format is encountered"""
