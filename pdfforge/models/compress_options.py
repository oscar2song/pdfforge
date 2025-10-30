"""
Compression Options Data Model
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class CompressionOptions:
    """Configuration options for PDF compression"""

    compression_level: str = "medium"
    image_quality: int = 85
    target_dpi: int = 150
    downsample_images: bool = True

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "CompressionOptions":
        """Create CompressionOptions from dictionary"""
        if not data:
            return cls()

        compression_level = data.get("compression_level", "medium")

        # Use preset values for compression levels
        if compression_level == "low":
            quality = data.get("image_quality", 95)
            dpi = data.get("target_dpi", 200)
        elif compression_level == "high":
            quality = data.get("image_quality", 75)
            dpi = data.get("target_dpi", 120)
        else:  # medium
            quality = data.get("image_quality", 85)
            dpi = data.get("target_dpi", 150)

        return cls(
            compression_level=compression_level,
            image_quality=quality,
            target_dpi=dpi,
            downsample_images=data.get("downsample_images", True),
        )

    def validate(self):
        """Validate options"""
        valid_levels = ["low", "medium", "high"]
        if self.compression_level not in valid_levels:
            raise ValueError(f"Invalid compression_level: {self.compression_level}")

        if not 1 <= self.image_quality <= 100:
            raise ValueError("image_quality must be between 1 and 100")

        if self.target_dpi < 72:
            raise ValueError("target_dpi must be at least 72")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "compression_level": self.compression_level,
            "image_quality": self.image_quality,
            "target_dpi": self.target_dpi,
            "downsample_images": self.downsample_images,
        }
