"""
Tests for PDF Normalization Functionality
"""

import pytest

from pdfforge.core.normalize import PDFNormalizer
from pdfforge.models.normalize_options import NormalizeOptions
from pdfforge.models.pdf_file import PDFFile
from pdfforge.services.normalize_service import NormalizeService


class TestPDFNormalizer:
    """Test PDFNormalizer class"""

    def test_normalize_pdf(self, sample_pdf):
        """Test PDF normalization"""
        pdf_file = PDFFile(path=sample_pdf, name="test.pdf").analyze()

        normalizer = PDFNormalizer()
        result = normalizer.normalize(pdf_file)

        assert result is not None
        assert len(result) == 1
        result.close()

    def test_normalize_with_ocr_option(self, sample_pdf):
        """Test normalization with OCR option"""
        pdf_file = PDFFile(path=sample_pdf, name="test.pdf").analyze()

        options = NormalizeOptions(add_ocr=True)
        normalizer = PDFNormalizer(options)
        result = normalizer.normalize(pdf_file)

        assert result is not None
        result.close()

    def test_normalize_options_validation(self):
        """Test validation of normalize options"""
        options = NormalizeOptions(page_size="letter")
        options.validate()  # Should not raise

        with pytest.raises(ValueError):
            options = NormalizeOptions(page_size="invalid-size")
            options.validate()

        with pytest.raises(ValueError):
            options = NormalizeOptions(orientation="invalid-orientation")
            options.validate()


class TestNormalizeService:
    """Test NormalizeService class"""

    def test_normalize_service_initialization(self):
        """Test service initialization"""
        service = NormalizeService()
        assert service is not None

    def test_normalize_file_success(self, sample_pdf):
        """Test successful file normalization"""
        service = NormalizeService()

        file_config = {"path": sample_pdf, "name": "test.pdf"}
        options = {"page_size": "A4"}

        result = service.normalize_file(file_config, options)

        assert result["success"] is True
        assert "file_path" in result
        assert result["page_count"] == 1

    def test_normalize_file_not_found(self):
        """Test normalization with non-existent file"""
        service = NormalizeService()

        file_config = {"path": "/nonexistent/file.pdf", "name": "test.pdf"}

        result = service.normalize_file(file_config, {})

        assert result["success"] is False
        assert result["error_type"] == "validation"
