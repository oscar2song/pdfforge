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

    def __init__(self, options: CompressionOptions = None):
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
                "output_path": output_path,
                "original_size": stats["original_size"],
                "compressed_size": stats["compressed_size"],
                "compression_ratio": stats["compression_ratio"],
                "reduction_percent": stats.get("reduction_percent", 0),
                "used_compression": True,
                "compression_level": options.get("compression_level", "medium"),
                "images_processed": stats.get("images_processed", 0),
                "images_downsampled": stats.get("images_downsampled", 0),
                "images_skipped": stats.get("images_skipped", 0)
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
                    compressed_files.append({
                        'path': result['output_path'],
                        'filename': result['filename']
                    })
                    # Calculate savings
                    original = result.get("original_size", 0)
                    compressed = result.get("compressed_size", 0)
                    total_savings += (original - compressed)

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
                final_filename = compressed_files[0]['filename']
                final_output_path = compressed_files[0]['path']
            else:
                return {
                    "success": False,
                    "error": "No files were successfully compressed"
                }

            return {
                "success": True,
                "batch": True,
                "total_files": len(files),
                "successful": len(results),
                "total_savings": total_savings,
                "results": results,
                "filename": final_filename,
                "output_path": final_output_path
            }

        except Exception as e:
            logger.error(f"Batch compression failed: {str(e)}")
            return {"success": False, "error": str(e)}

    def compress_pdf_enhanced(self, input_path, output_filename, original_filename, options=None):
        """
        ENHANCED COMPRESSION: Updated to match route compression levels
        """
        options = options or {}
        compression_level = options.get('compression_level', 'medium')

        # Match the compression levels from the routes
        if compression_level == 'low':
            image_quality = 95  # Matches route definition
            target_dpi = 200  # Matches route definition
            deflate = True
        elif compression_level == 'high':
            image_quality = 75  # Matches route definition
            target_dpi = 120  # Matches route definition
            deflate = True
        else:  # medium
            image_quality = 85  # Matches route definition
            target_dpi = 150  # Matches route definition
            deflate = True

        downsample = options.get('downsample_images', True)

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
        print(f"Deflate compression: {deflate}")

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

                        # Skip very small images
                        if original_img_size < 5120:  # 5KB
                            images_skipped += 1
                            continue

                        img = Image.open(io.BytesIO(image_bytes))
                        original_width, original_height = img.size

                        # DPI calculation and reduction
                        current_dpi = max(original_width / 8.5, original_height / 11)

                        should_resize = downsample and current_dpi > target_dpi

                        if should_resize:
                            scale_factor = target_dpi / current_dpi
                            scale_factor = min(scale_factor, 0.7)  # Don't scale below 70%
                            new_width = int(original_width * scale_factor)
                            new_height = int(original_height * scale_factor)

                            # Ensure minimum reasonable size
                            if new_width > 300 and new_height > 300:
                                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                                images_downsampled += 1

                                if page_num < 3 and img_index < 2:
                                    print(
                                        f"      Image {img_index + 1}: {original_width}x{original_height} → {new_width}x{new_height} (DPI: {current_dpi:.0f}→{target_dpi})")

                        img_output = io.BytesIO()

                        # Convert to RGB for better JPEG compression
                        if img.mode in ('RGBA', 'LA', 'P'):
                            # Create white background for transparent images
                            background = Image.new('RGB', img.size, (255, 255, 255))
                            if img.mode == 'RGBA':
                                background.paste(img, mask=img.split()[-1])
                            else:
                                background.paste(img)
                            img = background
                        elif img.mode != 'RGB':
                            img = img.convert('RGB')

                        # Use JPEG for all images
                        img.save(img_output, format='JPEG', quality=image_quality, optimize=True)
                        img_bytes = img_output.getvalue()

                        # Always replace if we resized, otherwise only if smaller
                        if should_resize or len(img_bytes) < original_img_size * 0.95:
                            page.replace_image(xref, stream=img_bytes)
                            images_processed += 1
                            if page_num < 3:
                                size_reduction = (1 - len(img_bytes) / original_img_size) * 100
                                print(
                                    f"      Image {img_index + 1}: {original_img_size / 1024:.1f}KB → {len(img_bytes) / 1024:.1f}KB ({size_reduction:.1f}% reduction)")
                        else:
                            if page_num < 3:
                                print(f"      Image {img_index + 1}: Skipped (minimal size reduction)")
                            images_skipped += 1

                    except Exception as e:
                        if page_num < 3:
                            print(f"      Warning: Could not process image {img_index + 1}: {e}")
                        images_skipped += 1

            elif page_num < 3:
                print(f"  Page {page_num + 1}: No images")

        print("\n" + "-" * 80)
        print(f"Images processed: {images_processed}")
        print(f"Images downsampled: {images_downsampled}")
        print(f"Images skipped: {images_skipped}")

        print(f"\nSaving compressed PDF...")

        # Use file manager for output path
        final_output = str(self.file_manager.get_download_path(output_filename))

        try:
            # Remove existing file to avoid conflicts
            if os.path.exists(final_output):
                os.remove(final_output)

            doc.save(
                final_output,
                garbage=4,
                deflate=True,
                deflate_images=True,
                deflate_fonts=True,
                clean=True,
                pretty=False,
                ascii=False
            )

            doc.close()

            compressed_size = os.path.getsize(final_output)
            compression_ratio = (1 - compressed_size / original_size) * 100

            print("\n" + "=" * 80)
            print(f"✅ Compression complete!")
            print(f"📄 Original size: {original_size / (1024 * 1024):.2f} MB")
            print(f"📦 Final size: {compressed_size / (1024 * 1024):.2f} MB")

            if compression_ratio > 0:
                print(
                    f"💾 Space saved: {(original_size - compressed_size) / (1024 * 1024):.2f} MB ({compression_ratio:.1f}% reduction)")
            else:
                print(f"📈 File size increased by: {abs(compression_ratio):.1f}%")

            print(f"💽 Output: {final_output}")
            print("=" * 80)

            return {
                'success': True,
                'original_size': original_size,
                'compressed_size': compressed_size,
                'compression_ratio': compression_ratio,
                'reduction_percent': compression_ratio,
                'images_processed': images_processed,
                'images_downsampled': images_downsampled,
                'images_skipped': images_skipped
            }

        except Exception as e:
            print(f"\n❌ Error during compression: {e}")
            # Fallback: save without compression
            try:
                doc.close()
                # Create a simple compressed version as fallback
                doc = fitz.open(input_path)
                doc.save(final_output, garbage=3, deflate=True)
                doc.close()

                compressed_size = os.path.getsize(final_output)
                compression_ratio = (1 - compressed_size / original_size) * 100

                print(f"🔄 Using fallback compression")
                print(f"📦 Final size: {compressed_size / (1024 * 1024):.2f} MB")
                print(f"💾 Reduction: {compression_ratio:.1f}%")

                return {
                    'success': True,
                    'original_size': original_size,
                    'compressed_size': compressed_size,
                    'compression_ratio': compression_ratio,
                    'reduction_percent': compression_ratio,
                    'images_processed': images_processed,
                    'images_downsampled': images_downsampled,
                    'images_skipped': images_skipped,
                    'error': f'Used fallback compression: {str(e)}'
                }
            except Exception as fallback_error:
                print(f"❌ Fallback also failed: {fallback_error}")
                return {
                    'success': False,
                    'error': f'Compression failed: {str(e)}'
                }
