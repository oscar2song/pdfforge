"""
Normalize Service - Business Logic Layer
"""

import logging
from typing import Any, Dict, List

from ..core.normalize import PDFNormalizer
from ..exceptions.pdf_exceptions import PDFNormalizationError
from ..exceptions.validation_exceptions import ValidationError
from ..models.normalize_options import NormalizeOptions
from ..models.pdf_file import PDFFile
from ..utils.file_utils import cleanup_temp_files, create_output_filename, save_pdf
from ..utils.validation import validate_pdf_files

logger = logging.getLogger(__name__)


class NormalizeService:
    """High-level normalization service with business logic"""

    def __init__(self):
        self.normalizer = None

    def normalize_file(
            self, file_config: Dict[str, Any], options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Normalize a single PDF file
        """
        try:
            logger.info("Starting normalization process")

            # Validate and prepare
            pdf_file = self._validate_and_prepare_file(file_config)
            normalize_options = NormalizeOptions.from_dict(options)
            normalize_options.validate()

            # Perform normalization
            self.normalizer = PDFNormalizer(normalize_options)
            normalized_doc = self.normalizer.normalize(pdf_file)

            # Generate output filename
            output_filename = create_output_filename(pdf_file.name, "normalized")

            # Convert Document to bytes and save
            import io
            pdf_bytes = io.BytesIO()
            normalized_doc.save(pdf_bytes)
            normalized_doc.close()

            # Save result using the utility function
            output_path = save_pdf(pdf_bytes, output_filename)

            logger.info(f"Normalization completed: {output_filename}")
            logger.info(f"File saved to: {output_path}")

            return {
                "success": True,
                "file_path": output_path,
                "filename": output_filename,
                "page_count": pdf_file.page_count,
                "target_size": (
                    f"{normalize_options.page_size} "
                    f"{normalize_options.orientation}"
                ),
                "ocr_performed": normalize_options.add_ocr,
            }

        except (ValidationError, ValueError) as e:
            logger.error(f"Validation error in normalization: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "validation",
            }

        except PDFNormalizationError as e:
            logger.error(f"Normalization error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "normalization",
            }

        except Exception as e:
            logger.exception(
                f"Unexpected error during normalization:{str(e)}"
            )
            return {
                "success": False,
                "error": "An unexpected error occurred during normalization",
                "error_type": "internal",
            }
        finally:
            # Cleanup source file
            if "file_config" in locals():
                cleanup_temp_files([file_config["path"]])

    def normalize_batch(
        self, file_configs: List[Dict[str, Any]], options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Normalize multiple PDF files and create zip archive
        """
        try:
            logger.info(
                f"Starting batch normalization for {len(file_configs)} files"
            )

            normalized_files = []
            results = []

            for file_config in file_configs:
                result = self.normalize_file(file_config, options)
                if result["success"]:
                    normalized_files.append(
                        {
                            "path": result["file_path"],
                            "filename": result["filename"],
                        }
                    )
                results.append(result)

            # Create zip archive if multiple files
            if len(normalized_files) > 1:
                import datetime

                from ..utils.file_utils import create_zip_archive

                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                zip_filename = f"normalized_pdfs_{timestamp}.zip"
                zip_path = create_zip_archive(normalized_files, zip_filename)

                # Don't cleanup individual files immediately - let download handle it
                # cleanup_temp_files([f["path"] for f in normalized_files])

                return {
                    "success": True,
                    "batch": True,
                    "file_path": zip_path,
                    "filename": zip_filename,
                    "results": results,
                    "total_files": len(file_configs),
                    "successful": len(normalized_files),
                    "files_to_cleanup": [f["path"] for f in normalized_files],  # Track files for later cleanup
                }
            elif normalized_files:
                # Single file result - don't cleanup source
                single_result = results[0]
                single_result["file_to_cleanup"] = file_configs[0]["path"]  # Track for cleanup
                return single_result
            else:
                return {
                    "success": False,
                    "error": "No files were successfully normalized",
                    "error_type": "processing",
                }

        except Exception as e:
            logger.exception(f"Error during batch normalization:{str(e)}")
            return {
                "success": False,
                "error": "Error occurred during batch normalization",
                "error_type": "internal",
            }

    def _validate_and_prepare_file(
        self, file_config: Dict[str, Any]
    ) -> PDFFile:
        """Validate and convert file config to PDFFile object"""
        validate_pdf_files([file_config])
        pdf_file = PDFFile.from_dict(file_config)
        pdf_file.analyze()
        return pdf_file
