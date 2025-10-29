# Changelog

All notable changes to PDFForge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- PDF Split functionality
- PDF Watermark feature
- PDF to Image conversion
- REST API
- Docker support
- User authentication
- Cloud storage integration

## [1.1.0] - 2025-10-29

### Added
- **Drag-and-Drop File Reordering**: Interactive reordering of files in merge list
  - Visual drag handles (☰) on each file item
  - Order badges (#1, #2, #3...) showing merge sequence
  - Smooth animations during drag operations
  - Visual feedback with highlight effects
  - Drop zone indicators
- Enhanced merge.html with interactive UI components

### Changed
- Improved file list styling with better visual hierarchy
- Enhanced user experience with intuitive drag-and-drop interface
- Updated README.md with drag-and-drop feature documentation

### Fixed
- Improved file handling stability
- Better error handling for edge cases in file processing

## [1.0.0] - 2025-10-28

### Added
- Initial public release of PDFForge
- **PDF Merge**: Combine multiple PDFs with optional custom headers
  - Simple merge mode (no modifications)
  - Header mode with two-line custom headers
  - Smart spacing detection for existing headers
  - Custom page numbers with configurable starting number
  - Multiple page number positions (top/bottom, left/center/right)
  - Automatic bookmark creation for merged documents
  - Custom output filename support
- **PDF Normalize**: Standardize PDF page sizes
  - Support for Letter, Legal, A4, A3, A5 (portrait/landscape)
  - OCR support for scanned documents
  - Batch processing capability
  - ZIP download for multiple files
  - Filename preservation with `_normalized` suffix
- **PDF Compress**: Reduce PDF file sizes intelligently
  - Smart compression with automatic method detection
  - Image optimization and downsampling
  - Batch compression support
  - Safe compression (never increases file size)
  - Compression ratio reporting
- Web interface with modern, responsive design
- Batch processing for all operations
- File upload with drag-and-drop support
- Real-time progress indicators
- Professional gradient UI design
- Cross-platform compatibility (Windows, macOS, Linux)

### Technical
- Flask 3.1.2 web framework
- PyMuPDF 1.26.5 for PDF manipulation
- pdfplumber 0.11.7 for text extraction
- Pillow 12.0.0 for image processing
- pytesseract 0.3.13 for OCR functionality
- Python 3.11+ support (3.12 recommended)

### Documentation
- Comprehensive README with usage examples
- Installation instructions for all platforms
- Configuration guide
- Troubleshooting section
- Feature comparison table

## [0.9.0] - 2025-10-26 (Beta)

### Added
- Beta release for internal testing
- Core PDF merge functionality
- Basic normalize feature
- Initial web interface

### Known Issues
- Limited browser compatibility testing
- No drag-and-drop reordering
- Basic error handling

---

## Version History Links

- [1.1.0]: https://github.com/oscar2song/pdfforge/compare/v1.0.0...v1.1.0
- [1.0.0]: https://github.com/oscar2song/pdfforge/releases/tag/v1.0.0

## Release Notes

For detailed release information, visit our [Releases page](https://github.com/oscar2song/pdfforge/releases).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project.

## Support

- **Issues**: [GitHub Issues](https://github.com/oscar2song/pdfforge/issues)
- **Email**: oscar2song@gmail.com
