"""
Pytest Configuration and Fixtures
"""

import os
import shutil
import tempfile
from pathlib import Path

import pytest

from config import TestingConfig
from pdfforge.create_app import create_app


@pytest.fixture
def app():
    """Create and configure test app"""
    # Use testing config directly
    app = create_app(TestingConfig())

    # Create upload folder
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    yield app

    # Cleanup
    if Path(app.config["UPLOAD_FOLDER"]).exists():
        shutil.rmtree(app.config["UPLOAD_FOLDER"])


@pytest.fixture
def client(app):
    """Test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Test CLI runner"""
    return app.test_cli_runner()


@pytest.fixture
def sample_pdf():
    """Create a sample PDF for testing"""
    import fitz

    # Create a simple PDF with some content
    pdf = fitz.open()
    page = pdf.new_page(width=612, height=792)

    # Add some text
    page.insert_text((100, 100), "Test PDF Document")
    page.insert_text((100, 120), "This is a test PDF file for unit testing.")

    # Add a simple rectangle
    page.draw_rect((50, 150, 200, 200), color=(1, 0, 0), fill=(1, 0, 0))

    # Save to temporary file
    temp_path = tempfile.mktemp(suffix=".pdf")
    pdf.save(temp_path)
    pdf.close()

    yield temp_path

    # Cleanup
    if Path(temp_path).exists():
        Path(temp_path).unlink()


@pytest.fixture
def sample_pdf_with_images():
    """Create a sample PDF with images for testing"""
    import io

    import fitz
    from PIL import Image

    pdf = fitz.open()
    page = pdf.new_page(width=612, height=792)

    # Create a simple image
    img = Image.new("RGB", (100, 100), color="red")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    # Add image to PDF
    page.insert_image((100, 100, 200, 200), stream=img_bytes.getvalue())

    temp_path = tempfile.mktemp(suffix=".pdf")
    pdf.save(temp_path)
    pdf.close()

    yield temp_path

    if Path(temp_path).exists():
        Path(temp_path).unlink()


@pytest.fixture
def upload_folder(app):
    """Get upload folder path"""
    return app.config["UPLOAD_FOLDER"]
