"""
Tests for PDF Compression Functionality
"""

import pytest

from pdfforge.core.compress import PDFCompressor
from pdfforge.models.compress_options import CompressionOptions
from pdfforge.models.pdf_file import PDFFile
from pdfforge.services.compress_service import CompressService


class TestPDFCompressor:
    """Test PDFCompressor class"""

    def test_compress_pdf(self, sample_pdf_with_images):
        """Test PDF compression"""
        pdf_file = PDFFile(path=sample_pdf_with_images, name="test.pdf").analyze()

        compressor = PDFCompressor()
        result = compressor.compress(pdf_file)

        assert result is not None
        result.close()

    def test_compress_options_validation(self):
        """Test validation of compress options"""
        options = CompressionOptions(compression_level="medium")
        options.validate()  # Should not raise

        with pytest.raises(ValueError):
            options = CompressionOptions(compression_level="invalid-level")
            options.validate()

        with pytest.raises(ValueError):
            options = CompressionOptions(image_quality=150)
            options.validate()


class TestCompressService:
    """Test CompressService class"""

    def test_compress_service_initialization(self):
        """Test service initialization"""
        service = CompressService()
        assert service is not None

    def test_compress_file_success(self, sample_pdf_with_images):
        """Test successful file compression"""
        service = CompressService()

        file_config = {"path": sample_pdf_with_images, "name": "test.pdf"}
        options = {"compression_level": "medium"}

        result = service.compress_file(file_config, options)

        assert result["success"] is True
        assert "file_path" in result
        assert "compression_ratio" in result
