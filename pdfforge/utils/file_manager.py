# pdfforge/utils/file_manager.py
import os
from pathlib import Path
from typing import Optional  # ADD THIS IMPORT


class FilePathManager:
    """
    Unified file path manager for all PDF operations that works with existing structure
    """

    def __init__(self, base_data_dir: Optional[Path] = None, component: str = "merge"):
        # Priority: Custom dir > Environment variable > Default location (existing behavior)
        if base_data_dir:
            self.base_data_dir = Path(base_data_dir)
        else:
            env_dir = os.getenv("PDF_APP_DATA_DIR")
            if env_dir:
                self.base_data_dir = Path(env_dir)
            else:
                # DEFAULT: Use existing project structure (uploads/, downloads/)
                self.base_data_dir = Path(__file__).parent.parent.parent  # Project root

        self.component = component
        self.ensure_directories()

        print(f"📁 [{component.upper()}] Using base directory: {self.base_data_dir}")

    def ensure_directories(self):
        """Create necessary directories using existing structure"""
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.downloads_dir.mkdir(parents=True, exist_ok=True)

        # Component-specific subdirectories within downloads
        self.merge_dir.mkdir(parents=True, exist_ok=True)
        self.normalize_dir.mkdir(parents=True, exist_ok=True)
        self.compress_dir.mkdir(parents=True, exist_ok=True)
        self.toc_dir.mkdir(parents=True, exist_ok=True)  # ADD TOC DIRECTORY

    @property
    def uploads_dir(self) -> Path:
        """Uploads directory - maintains existing location"""
        return self.base_data_dir / "uploads"

    @property
    def downloads_dir(self) -> Path:
        """Downloads directory - maintains existing location"""
        return self.base_data_dir / "downloads"

    @property
    def temp_dir(self) -> Path:
        """Temporary directory"""
        return self.base_data_dir / "temp"

    # Component-specific directories within downloads
    @property
    def merge_dir(self) -> Path:
        return self.downloads_dir / "merge"

    @property
    def normalize_dir(self) -> Path:
        return self.downloads_dir / "normalize"

    @property
    def compress_dir(self) -> Path:
        return self.downloads_dir / "compress"

    @property
    def toc_dir(self) -> Path:  # ADD TOC DIRECTORY
        return self.downloads_dir / "toc"

    def get_component_dir(self) -> Path:
        """Get the appropriate directory for the current component"""
        if self.component == "normalize":
            return self.normalize_dir
        elif self.component == "compress":
            return self.compress_dir
        elif self.component == "toc":  # ADD TOC SUPPORT
            return self.toc_dir
        else:  # merge or default
            return self.merge_dir

    def get_upload_path(self, filename: str) -> Path:
        return self.uploads_dir / filename

    def get_download_path(self, filename: str) -> Path:
        component_dir = self.get_component_dir()
        return component_dir / filename

    def get_temp_path(self, filename: str) -> Path:
        return self.temp_dir / filename

    def generate_output_filename(self, original_name: str, operation: str, suffix: str = "") -> str:
        """Generate consistent output filenames across all components"""
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        name_without_ext = Path(original_name).stem
        extension = Path(original_name).suffix or ".pdf"

        if suffix:
            return f"{timestamp}_{name_without_ext}_{suffix}{extension}"
        else:
            return f"{timestamp}_{name_without_ext}_{operation}{extension}"

    def is_external_path(self) -> bool:
        """Check if using external paths (for containers)"""
        project_root = Path(__file__).parent.parent.parent
        return not self.base_data_dir.is_relative_to(project_root)

    def cleanup_component_files(self, max_age_hours=2):
        """Clean up old files for this specific component"""
        try:
            import time

            current_time = time.time()
            max_age_seconds = max_age_hours * 3600

            component_dir = self.get_component_dir()
            if component_dir.exists():
                for file_path in component_dir.glob("*"):
                    if file_path.is_file():
                        file_age = current_time - file_path.stat().st_mtime
                        if file_age > max_age_seconds:
                            try:
                                file_path.unlink()
                                print(f"🧹 Cleaned up {self.component} file: {file_path.name}")
                            except Exception as e:
                                print(f"Error cleaning up {file_path}: {e}")
        except Exception as e:
            print(f"Cleanup operation skipped for {self.component}: {e}")


# Factory function for easy component creation
def get_file_manager(component: str = "merge") -> FilePathManager:
    """Get file manager for specific component"""
    return FilePathManager(component=component)