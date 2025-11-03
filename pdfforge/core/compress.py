"""
PDF Compression Core Logic
Handles PDF file size optimization
"""

import io
import os
from typing import Optional

import fitz  # type: ignore  # type: ignore  # type: ignore
from PIL import Image
from PIL.Image import Image as PILImage

from ..exceptions.pdf_exceptions import PDFCompressionError
from ..models.compress_options import CompressionOptions
from ..models.pdf_file import PDFFile


class PDFCompressor:
    """Handles PDF compression operations"""

    def __init__(self, options: Optional[CompressionOptions] = None):
        self.options = options or CompressionOptions()

    def compress(self, pdf_file: PDFFile) -> fitz.Document:
        """
        Compress PDF file

        Args:
            pdf_file: PDFFile object to compress

        Returns:
            fitz.Document: Compressed PDF document

        Raises:
            PDFCompressionError: If compression fails
        """
        try:
            doc = fitz.open(pdf_file.path)
            original_size = os.path.getsize(pdf_file.path)

            print("=" * 80)
            print("PDF COMPRESSION CORE PROCESS")
            print("=" * 80)
            print(f"Input: {pdf_file.name}")
            print(f"Original size: {original_size / (1024 * 1024):.2f} MB")
            print(f"Compression level: {self.options.compression_level}")

            images_processed = 0
            images_downsampled = 0

            for page_num in range(len(doc)):
                page = doc[page_num]
                image_list = page.get_images(full=True)

                if image_list:
                    for img_index, img_info in enumerate(image_list):
                        images_processed += self._process_image(doc, img_info, images_downsampled)

            return doc

        except Exception as e:
            raise PDFCompressionError(f"Failed to compress PDF: {str(e)}")

    def _process_image(self, doc: fitz.Document, img_info: tuple, images_downsampled: int) -> int:
        """Process individual image for compression"""
        xref = img_info[0]

        try:
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            original_img_size = len(image_bytes)

            img: PILImage = Image.open(io.BytesIO(image_bytes))
            original_width, original_height = img.size

            # Skip very small images
            if original_width < 100 or original_height < 100:
                return 0

            # Resize if needed
            current_dpi = original_width / 8.5
            should_resize = self.options.downsample_images and current_dpi > self.options.target_dpi

            if should_resize:
                scale_factor = self.options.target_dpi / current_dpi
                new_width = int(original_width * scale_factor)
                new_height = int(original_height * scale_factor)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)  # type: ignore
                images_downsampled += 1

            # Compress image
            img_output = io.BytesIO()
            if img.mode == "RGBA":
                img = img.convert("RGB")

            img.save(
                img_output,
                format="JPEG",
                quality=self.options.image_quality,
                optimize=True,
            )
            img_bytes = img_output.getvalue()

            # Replace if smaller
            if len(img_bytes) < original_img_size:
                doc.replace_image(xref, stream=img_bytes)
                return 1

            return 0

        except Exception as e:
            print(f"Warning: Could not process image: {e}")
            return 0


def create_output_filename(original_filename: str, suffix: str = "compressed") -> str:
    """
    Create output filename with original name + suffix.
    Example: invoice.pdf -> invoice_compressed.pdf
    """
    name_without_ext = os.path.splitext(original_filename)[0]
    return f"{name_without_ext}_{suffix}.pdf"
