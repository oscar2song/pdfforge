"""
Input Validation Functions
"""

import os
from typing import Any, Dict, List


def validate_pdf_files(file_configs: List[Dict[str, Any]]):
    """Validate PDF file configurations."""
    if not file_configs:
        raise ValueError("No files provided")

    for config in file_configs:
        if "path" not in config or "name" not in config:
            raise ValueError("Invalid file configuration")

        if not os.path.exists(config["path"]):
            raise ValueError(f"File not found: {config['path']}")


def validate_merge_options(options: Dict[str, Any]):
    """Validate merge options."""
    if "page_start" in options and options["page_start"] < 1:
        raise ValueError("page_start must be >= 1")

    if "scale_factor" in options and not (0 < options["scale_factor"] <= 1):
        raise ValueError("scale_factor must be between 0 and 1")

    valid_positions = [
        "top-center",
        "bottom-center",
        "top-right",
        "bottom-right",
    ]
    if "page_number_position" in options and options["page_number_position"] not in valid_positions:
        raise ValueError(f"Invalid page_number_position: {options['page_number_position']}")


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in {"pdf"}
