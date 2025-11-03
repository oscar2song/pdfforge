# compress_service.py - UPDATED WITH FILE MANAGER
import io
import logging
import os
from datetime import datetime

from PIL import Image

from ..models.compress_options import CompressionOptions
from ..models.pdf_file import PDFFile
from ..utils.file_manager import get_file_manager
from ..utils.file_utils import create_output_filename, create_zip_archive

logger = logging.getLogger(__name__)


class CompressService:
    """Core PDF compression functionality"""

    def __init__(self, options: CompressionOptions | None = None):
        self.options = options or CompressionOptions()
        self.file_manager = get_file_manager(component="compress")

    def compress_file(self, file_config, options):
        """Compress a single file - matches the route expectation"""
        try:
            # Create PDFFile object with proper parameters
            pdf_file = PDFFile(file_config["path"], file_config.get("name"))

            # Generate output filename
            original_name = file_config.get("name", "document.pdf")
            compressed_name = create_output_filename(original_name, "compressed")

            # Use the enhanced compression method
            stats = self.compress_pdf_enhanced(pdf_file.path, compressed_name, original_name, options)

            if not stats.get("success", False):
                return {"success": False, "error": stats.get("error", "Compression failed")}

            # Build output path using file manager
            output_path = str(self.file_manager.get_download_path(compressed_name))

            # Return the expected response format
            return {
                "success": True,
                "filename": compressed_name,
                "file_path": output_path,  # ← Change from "output_path" to "file_path"
                "original_size": stats["original_size"],
                "compressed_size": stats["compressed_size"],
                "compression_ratio": stats["compression_ratio"],
                "reduction_percent": stats.get("reduction_percent", 0),
                "used_compression": True,
                "compression_level": options.get("compression_level", "medium"),
                "images_processed": stats.get("images_processed", 0),
                "images_downsampled": stats.get("images_downsampled", 0),
                "images_skipped": stats.get("images_skipped", 0),
            }

        except Exception as e:
            logger.error(f"File compression failed: {str(e)}")
            return {"success": False, "error": str(e)}

    def compress_batch(self, files, options):
        """Compress multiple files - matches the route expectation"""
        try:
            results = []
            total_savings = 0
            compressed_files = []

            for file_config in files:
                result = self.compress_file(file_config, options)
                if result["success"]:
                    results.append(result)
                    compressed_files.append({"path": result["file_path"], "filename": result["filename"]})  # ← FIX 1
                    # Calculate savings
                    original = result.get("original_size", 0)
                    compressed = result.get("compressed_size", 0)
                    total_savings += original - compressed

            # Create zip file if multiple files were compressed
            if len(compressed_files) > 1:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                zip_filename = f"compressed_pdfs_{timestamp}.zip"

                # Use file_utils to create zip with compress component
                zip_path = create_zip_archive(compressed_files, zip_filename, "compress")

                # Return the zip file path for download
                final_filename = zip_filename
                final_output_path = zip_path
            elif compressed_files:
                # For single file, just use the compressed file
                final_filename = compressed_files[0]["filename"]
                final_output_path = compressed_files[0]["path"]
            else:
                return {"success": False, "error": "No files were successfully compressed"}

            return {
                "success": True,
                "batch": True,
                "total_files": len(files),
                "successful": len(results),
                "total_savings": total_savings,
                "results": results,
                "filename": final_filename,
                "file_path": final_output_path,  # ← FIX 2
            }

        except Exception as e:
            logger.error(f"Batch compression failed: {str(e)}")
            return {"success": False, "error": str(e)}

    def compress_pdf_enhanced(self, input_path, output_filename, original_filename, options=None):
        """
        ENHANCED COMPRESSION: Smart compression that never increases file size
        """
        options = options or {}
        compression_level = options.get("compression_level", "medium")

        # Match the compression levels from the routes
        if compression_level == "low":
            image_quality = 95
            target_dpi = 200
        elif compression_level == "high":
            image_quality = 75
            target_dpi = 120
        else:  # medium
            image_quality = 85
            target_dpi = 150

        downsample = options.get("downsample_images", True)

        print("=" * 80)
        print("ENHANCED PDF COMPRESSION")
        print("=" * 80)
        print(f"\nInput: {os.path.basename(input_path)}")

        original_size = os.path.getsize(input_path)
        original_size_mb = original_size / (1024 * 1024)
        print(f"Original size: {original_size_mb:.2f} MB")

        print(f"\nCompression level: {compression_level.upper()}")
        print(f"Image quality: {image_quality}%")
        print(f"Target DPI: {target_dpi}")
        print(f"Downsample images: {downsample}")

        import fitz

        doc = fitz.open(input_path)
        total_pages = len(doc)

        print(f"\nProcessing {total_pages} pages...")
        print("-" * 80)

        images_processed = 0
        images_downsampled = 0
        images_skipped = 0

        for page_num in range(total_pages):
            page = doc.load_page(page_num)
            image_list = page.get_images(full=True)

            if image_list:
                if page_num < 3:
                    print(f"  Page {page_num + 1}: {len(image_list)} image(s)")

                for img_index, img_info in enumerate(image_list):
                    xref = img_info[0]

                    try:
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        original_img_size = len(image_bytes)

                        # Skip very small images (already compressed)
                        if original_img_size < 10240:  # 10KB
                            images_skipped += 1
                            continue

                        img = Image.open(io.BytesIO(image_bytes))
                        original_width, original_height = img.size

                        # Skip small images
                        if original_width < 200 or original_height < 200:
                            images_skipped += 1
                            continue

                        # DPI calculation
                        current_dpi = max(original_width / 8.5, original_height / 11)
                        should_resize = downsample and current_dpi > target_dpi

                        if should_resize:
                            scale_factor = target_dpi / current_dpi
                            scale_factor = max(scale_factor, 0.5)  # Don't scale below 50%
                            new_width = int(original_width * scale_factor)
                            new_height = int(original_height * scale_factor)

                            # Ensure minimum size
                            if new_width >= 200 and new_height >= 200:
                                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                                images_downsampled += 1

                                if page_num < 3 and img_index < 2:
                                    print(
                                        f"    Image {img_index + 1}: {original_width}x{original_height} → "
                                        f"{new_width}x{new_height} (DPI: {current_dpi:.0f}→{target_dpi})"
                                    )

                        # Compress image
                        img_output = io.BytesIO()

                        # Convert to RGB for JPEG
                        if img.mode in ("RGBA", "LA", "P"):
                            background = Image.new("RGB", img.size, (255, 255, 255))
                            if img.mode == "RGBA":
                                background.paste(img, mask=img.split()[-1])
                            else:
                                background.paste(img)
                            img = background
                        elif img.mode != "RGB":
                            img = img.convert("RGB")

                        # Save as JPEG
                        img.save(img_output, format="JPEG", quality=image_quality, optimize=True)
                        img_bytes = img_output.getvalue()

                        # CRITICAL: Only replace if we got real compression (at least 10% reduction)
                        if len(img_bytes) < original_img_size * 0.9:
                            page.replace_image(xref, stream=img_bytes)
                            images_processed += 1
                            if page_num < 3:
                                size_reduction = (1 - len(img_bytes) / original_img_size) * 100
                                print(
                                    f"    Image {img_index + 1}: {original_img_size / 1024:.1f}KB → "
                                    f"{len(img_bytes) / 1024:.1f}KB ({size_reduction:.1f}% reduction)"
                                )
                        else:
                            if page_num < 3:
                                print(f"    Image {img_index + 1}: Skipped (no significant compression)")
                            images_skipped += 1

                    except Exception as e:
                        if page_num < 3:
                            print(f"    Warning: Could not process image {img_index + 1}: {e}")
                        images_skipped += 1

            elif page_num < 3:
                print(f"  Page {page_num + 1}: No images")

        print("\n" + "-" * 80)
        print(f"Images processed: {images_processed}")
        print(f"Images downsampled: {images_downsampled}")
        print(f"Images skipped: {images_skipped}")

        # Use file manager for output path
        final_output = str(self.file_manager.get_download_path(output_filename))

        # Save with compression only if we actually compressed something
        try:
            # Remove existing file
            if os.path.exists(final_output):
                os.remove(final_output)

            # Save with moderate compression settings
            doc.save(
                final_output,
                garbage=4,
                deflate=True,
                deflate_images=True,
                deflate_fonts=True,
                clean=True,
            )
            doc.close()

            compressed_size = os.path.getsize(final_output)

            # CRITICAL CHECK: If compressed file is larger, use original
            if compressed_size >= original_size:
                print("\n⚠️ Warning: Compressed file is larger than original!")
                print("   Using original file instead...")

                # Copy original to output location
                import shutil

                if os.path.exists(final_output):
                    os.remove(final_output)
                shutil.copy2(input_path, final_output)

                compressed_size = original_size
                compression_ratio = 0

                print("\n" + "=" * 80)
                print("✅ Compression complete (original file used)")
                print(f"📄 File size: {original_size / (1024 * 1024):.2f} MB")
                print("💡 No compression was beneficial for this file")
                print(f"💽 Output: {final_output}")
                print("=" * 80)
            else:
                compression_ratio = (1 - compressed_size / original_size) * 100

                print("\n" + "=" * 80)
                print("✅ Compression complete!")
                print(f"📄 Original size: {original_size / (1024 * 1024):.2f} MB")
                print(f"📦 Final size: {compressed_size / (1024 * 1024):.2f} MB")
                print(
                    f"💾 Space saved: {(original_size - compressed_size) / (1024 * 1024):.2f} MB "
                    f"({compression_ratio:.1f}% reduction)"
                )
                print(f"💽 Output: {final_output}")
                print("=" * 80)

            return {
                "success": True,
                "original_size": original_size,
                "compressed_size": compressed_size,
                "compression_ratio": compression_ratio,
                "reduction_percent": compression_ratio,
                "images_processed": images_processed,
                "images_downsampled": images_downsampled,
                "images_skipped": images_skipped,
            }

        except Exception as e:
            print(f"\n❌ Error during compression: {e}")
            logger.error(f"Compression error: {str(e)}")
            return {"success": False, "error": f"Compression failed: {str(e)}"}
