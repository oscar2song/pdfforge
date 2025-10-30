"""
Tests for PDF Merge Functionality
"""

import json

import pytest

from pdfforge.core.merge import PDFMerger
from pdfforge.models.merge_options import MergeOptions
from pdfforge.models.pdf_file import PDFFile
from pdfforge.services.merge_service import MergeService


class TestPDFMerger:
    """Test PDFMerger class"""

    def test_merge_two_pdfs(self, sample_pdf):
        """Test merging two PDF files"""
        files = [
            PDFFile(path=sample_pdf, name="test1.pdf").analyze(),
            PDFFile(path=sample_pdf, name="test2.pdf").analyze(),
        ]

        merger = PDFMerger()
        result = merger.merge(files)

        assert result is not None
        assert len(result) == 2
        result.close()

    def test_merge_with_headers(self, sample_pdf):
        """Test merging with headers"""
        files = [
            PDFFile(
                path=sample_pdf,
                name="test1.pdf",
                header_line1="Header 1",
                header_line2="Header 2",
            ).analyze()
        ]

        options = MergeOptions(add_headers=True)
        merger = PDFMerger(options)
        result = merger.merge(files)

        assert result is not None
        assert len(result) == 1
        result.close()

    def test_merge_options_validation(self):
        """Test validation of merge options"""
        options = MergeOptions(page_start=1)
        options.validate()  # Should not raise

        with pytest.raises(ValueError):
            options = MergeOptions(page_start=0)
            options.validate()

        with pytest.raises(ValueError):
            options = MergeOptions(scale_factor=1.5)
            options.validate()

        with pytest.raises(ValueError):
            options = MergeOptions(page_number_position="invalid-position")
            options.validate()


class TestMergeService:
    """Test MergeService class"""

    def test_merge_service_initialization(self):
        """Test service initialization"""
        service = MergeService()
        assert service is not None
        assert service.merger is None

    def test_merge_files_success(self, sample_pdf):
        """Test successful file merging"""
        service = MergeService()

        file_configs = [
            {"path": sample_pdf, "name": "test1.pdf"},
            {"path": sample_pdf, "name": "test2.pdf"},
        ]

        options = {"add_bookmarks": True}

        result = service.merge_files(file_configs, options)

        assert result["success"] is True
        assert "file_path" in result
        assert result["file_count"] == 2
        assert result["page_count"] == 2

    def test_merge_files_validation_error(self):
        """Test merge with validation error"""
        service = MergeService()

        # Invalid file configs
        file_configs = [{"invalid": "config"}]

        result = service.merge_files(file_configs, {})

        assert result["success"] is False
        assert result["error_type"] == "validation"

    def test_merge_files_no_files(self):
        """Test merge with no files"""
        service = MergeService()

        result = service.merge_files([], {})

        assert result["success"] is False
        assert result["error_type"] == "validation"


class TestMergeRoutes:
    """Test merge routes"""

    def test_merge_page_loads(self, client):
        """Test merge page loads successfully"""
        response = client.get("/merge/")
        assert response.status_code == 200
        assert b"Merge PDFs" in response.data

    def test_upload_file_success(self, client, sample_pdf):
        """Test successful file upload"""
        with open(sample_pdf, "rb") as f:
            response = client.post("/merge/upload", data={"file": (f, "test.pdf")})

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert "file_path" in data

    def test_upload_invalid_file(self, client):
        """Test upload of invalid file type"""
        response = client.post("/merge/upload", data={"file": (b"fake content", "test.txt")})

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False

    def test_merge_process_invalid_data(self, client):
        """Test merge process with invalid data"""
        response = client.post(
            "/merge/process",
            data=json.dumps({}),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
