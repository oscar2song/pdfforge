# pdfforge/utils/font_utils.py
import os
import fitz
from typing import Optional, Dict, Any


class ProjectFontManager:
    """Fixed font manager for PyMuPDF 1.26.5 using correct font handling"""

    _fonts_loaded = False
    _available_fonts = {}
    _font_cache = {}  # Cache font objects

    @classmethod
    def get_fonts_directory(cls) -> str:
        """Get the absolute path to fonts directory"""
        hardcoded_path = r"C:\Users\tongq\repo\pdfforge\pdfforge\fonts"
        if os.path.exists(hardcoded_path):
            return hardcoded_path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        pdfforge_root = os.path.dirname(current_dir)
        return os.path.join(pdfforge_root, "fonts")

    @classmethod
    def initialize_fonts(cls) -> bool:
        """Initialize fonts"""
        if cls._fonts_loaded:
            return True

        try:
            fonts_dir = cls.get_fonts_directory()
            print(f"📁 Fonts directory: {fonts_dir}")

            if not os.path.exists(fonts_dir):
                print("⚠ Fonts directory not found")
                cls._available_fonts['default'] = "helv"
                cls._fonts_loaded = True
                return False

            # Check OpenSans availability
            open_sans_files = {
                'regular': "OpenSans-Regular.ttf",
                'bold': "OpenSans-Bold.ttf",
                'italic': "OpenSans-Italic.ttf",
                'bold_italic': "OpenSans-BoldItalic.ttf",
            }

            open_sans_available = True
            for variant, filename in open_sans_files.items():
                path = os.path.join(fonts_dir, "OpenSans", filename)
                if not os.path.exists(path):
                    open_sans_available = False
                    print(f"⚠ OpenSans missing: {filename}")
                    break

            if open_sans_available:
                print("✓ All OpenSans font files found")

                # Store font paths
                for variant, filename in open_sans_files.items():
                    cls._available_fonts[f'path-{variant}'] = os.path.join(fonts_dir, "OpenSans", filename)

                cls._available_fonts['default'] = "opensans"
                print("🎉 Using OpenSans fonts")
            else:
                print("⚠ Using system fonts")
                cls._available_fonts['default'] = "helv"

            cls._fonts_loaded = True
            return True

        except Exception as e:
            print(f"⚠ Font initialization failed: {e}")
            cls._available_fonts['default'] = "helv"
            cls._fonts_loaded = True
            return False

    @classmethod
    def insert_text_with_font(cls, page, pos, text, fontsize=11, variant='regular', **kwargs):
        """Insert text with custom font - use fontfile parameter directly"""
        if cls._available_fonts['default'] == "helv":
            return page.insert_text(pos, text, fontsize=fontsize, fontname="helv", **kwargs)

        font_path = cls._available_fonts.get(f'path-{variant}')

        if font_path and os.path.exists(font_path):
            try:
                # Use fontfile parameter directly - this should work in PyMuPDF 1.26.5
                return page.insert_text(pos, text, fontsize=fontsize, fontfile=font_path, **kwargs)
            except Exception as e:
                print(f"⚠ Custom font failed: {e}, using system font")
                return page.insert_text(pos, text, fontsize=fontsize, fontname="helv", **kwargs)
        else:
            # Fallback to system font
            return page.insert_text(pos, text, fontsize=fontsize, fontname="helv", **kwargs)

    @classmethod
    def get_text_length(cls, text, fontsize=11, variant='regular'):
        """Get text length by inserting and measuring"""
        if cls._available_fonts['default'] == "helv":
            return fitz.get_text_length(text, fontsize=fontsize, fontname="helv")

        # For custom fonts, create a temporary page to measure
        try:
            doc = fitz.open()
            page = doc.new_page(-1, width=1000, height=100)

            # Insert text and get the bounding rectangle
            rect = cls.insert_text_with_font(page, (0, 50), text, fontsize=fontsize, variant=variant)

            doc.close()

            # Return the width of the bounding rectangle
            if hasattr(rect, 'width'):
                return rect.width
            elif hasattr(rect, 'x1') and hasattr(rect, 'x0'):
                return rect.x1 - rect.x0
            else:
                # Fallback estimation
                return len(text) * fontsize * 0.6

        except Exception as e:
            print(f"⚠ Text measurement failed: {e}")
            return len(text) * fontsize * 0.6

    @classmethod
    def get_default_font(cls):
        return cls._available_fonts.get('default', 'helv')

    @classmethod
    def reset(cls):
        cls._fonts_loaded = False
        cls._available_fonts = {}
        cls._font_cache = {}
