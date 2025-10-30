"""
Tests for utility functions
"""

import fitz
import pytest

from pdfforge.utils.pdf_utils import detect_pdf_type, has_text_layer
from pdfforge.utils.validation import allowed_file, validate_pdf_files


class TestPDFUtils:
    """Test PDF utility functions"""

    def test_detect_pdf_type(self, sample_pdf):
        """Test PDF type detection"""
        doc = fitz.open(sample_pdf)
        page = doc[0]

        pdf_type = detect_pdf_type(page)

        assert "is_image_based" in pdf_type
        assert "text_length" in pdf_type
        assert "image_count" in pdf_type

        doc.close()

    def test_has_text_layer(self, sample_pdf):
        """Test text layer detection"""
        doc = fitz.open(sample_pdf)
        page = doc[0]

        has_text = has_text_layer(page)

        # Our test PDF has text, so this should be True
        assert has_text is True

        doc.close()


class TestValidation:
    """Test validation functions"""

    def test_validate_pdf_files_success(self, sample_pdf):
        """Test successful PDF file validation"""
        file_configs = [{"path": sample_pdf, "name": "test.pdf"}]

        # Should not raise
        validate_pdf_files(file_configs)

    def test_validate_pdf_files_not_found(self):
        """Test validation with non-existent files"""
        file_configs = [{"path": "/nonexistent/file.pdf", "name": "test.pdf"}]

        with pytest.raises(ValueError):
            validate_pdf_files(file_configs)

    def test_validate_pdf_files_invalid_config(self):
        """Test validation with invalid config"""
        file_configs = [{"invalid": "config"}]

        with pytest.raises(ValueError):
            validate_pdf_files(file_configs)

    def test_allowed_file(self):
        """Test file extension validation"""
        assert allowed_file("document.pdf") is True
        assert allowed_file("DOCUMENT.PDF") is True
        assert allowed_file("file.txt") is False
        assert allowed_file("image.jpg") is False
        assert allowed_file("") is False
