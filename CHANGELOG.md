# Changelog

All notable changes to PDFForge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2025-11-03

### Planned
- Enhance TOC
- PDF Split functionality
- PDF Watermark feature
- PDF to Image conversion
- REST API
- Docker support
- User authentication
- Cloud storage integration

### 🎉 Major Release - Complete Architecture Overhaul

This release represents a complete rewrite of PDFForge with a modern, modular architecture.

### Added

#### Architecture & Structure
- Complete modular architecture with 5 layers (Presentation, Service, Core, Utility, Foundation)
- Service layer for business logic orchestration
- Core layer with pure PDF processing logic
- Model classes with dataclasses for type safety
- Custom exception hierarchy for better error handling
- Flask application factory pattern
- Blueprint-based route organization
- Environment-based configuration management
- Comprehensive type hints throughout codebase
- Google-style docstrings for all public APIs

#### Testing & Quality Assurance
- Comprehensive test suite with pytest framework
- Unit tests for core functionality
- Integration tests for service layer
- End-to-end tests for complete workflows
- Test fixtures for reusable test data
- 80%+ code coverage
- Automated testing setup with pytest-cov
- Mock support with pytest-mock

#### Documentation
- Complete README.md overhaul with architecture overview
- ARCHITECTURE.md - Technical architecture guide (21KB)
- DEVELOPMENT.md - Comprehensive developer guide (18KB)
- CONTRIBUTING.md - Contribution guidelines (14KB)
- API.md - API reference documentation (14KB)
- DEPLOYMENT.md - Production deployment guide (16KB)
- Code examples for all major features
- Architecture diagrams and flow charts
- Configuration examples
- Deployment templates

#### Developer Experience
- Development dependencies in requirements-dev.txt
- Code formatting with Black
- Import sorting with isort
- Linting with flake8 and pylint
- Type checking with mypy
- Git hooks setup examples
- VS Code and PyCharm configuration examples
- Environment variable support with python-dotenv
- Example .env.example file

#### Configuration
- Environment-based configuration classes (Development, Production, Testing)
- .env file support for local development
- Configurable upload/download/temp directories
- Configurable logging levels and formats
- Separate configuration for testing

### Changed

#### Architecture
- **Breaking**: Transformed from monolithic 1,800+ line app.py to modular structure
- **Breaking**: Import paths changed due to new package structure
- **Breaking**: Configuration moved from hardcoded values to environment variables
- Entry point app.py reduced from 1,800+ lines to ~50 lines
- Separated PDF processing logic into dedicated core modules
- Extracted business logic into service layer
- Organized routes into Flask blueprints
- Moved utilities into dedicated utils package

#### Code Quality
- Added type hints to all functions and methods
- Improved error handling with custom exceptions
- Better separation of concerns across modules
- Removed code duplication through refactoring
- Improved naming conventions for better clarity
- Enhanced docstrings with examples and type information

#### Performance
- Optimized PDF processing with better memory management
- Improved resource cleanup with context managers
- Better handling of large files
- Lazy loading of components

#### Security
- Enhanced input validation
- Improved file upload security
- Better error message sanitization
- Secure defaults for production

### Fixed

- Memory leaks in PDF processing workflows
- Error handling for corrupted PDF files
- Large file upload timeouts
- Header spacing calculation issues
- OCR failures on certain PDF types
- File descriptor leaks
- Race conditions in batch processing
- Temporary file cleanup issues

### Improved

- Code maintainability with modular structure
- Testability with dependency injection
- Developer onboarding with comprehensive documentation
- Debugging with better error messages and logging
- Extensibility with open/closed principle
- Collaboration with clear module boundaries

### Deprecated

- Direct imports from old app.py (use new module structure)
- Hardcoded configuration (use environment variables)

### Security

- Added security headers in example Nginx configuration
- Implemented secure session cookie settings
- Added rate limiting examples
- Improved input validation and sanitization
- Added file type validation
- Implemented secure filename handling

### Performance

- Reduced memory footprint in PDF processing
- Optimized batch processing workflows
- Improved file handling efficiency
- Better resource management with proper cleanup

## [1.0.0] - 2025-10-28

### Initial Release

#### Added

- PDF Merge functionality
  - Simple merge mode
  - Header mode with two-line headers
  - Smart spacing detection
  - Custom page numbering
  - Custom output filenames
  - Empty header support

- PDF Normalize functionality
  - Multiple page size support (Letter, Legal, A4, A3, A5)
  - Portrait and landscape orientation
  - OCR support for scanned documents
  - Batch processing
  - ZIP download for multiple files
  - Filename preservation with suffix

- PDF Compress functionality
  - Smart compression algorithm
  - Image optimization
  - Quality-preserving compression
  - Batch processing
  - Size reporting before/after
  - Safe compression (never increases size)

- Web Interface
  - Responsive design
  - Modern UI
  - Drag-and-drop file upload
  - Real-time progress indication
  - Error handling and user feedback

- Core Features
  - PyMuPDF integration for PDF manipulation
  - Tesseract OCR support
  - Pillow for image processing
  - Flask web framework
  - File upload handling
  - Temporary file management

- Documentation
  - Basic README with installation instructions
  - Usage examples
  - Feature list
  - Troubleshooting guide

[2.1.0]: https://github.com/oscar2song/pdfforge/compare/v1.0.0...v2.1.0
[1.0.0]: https://github.com/oscar2song/pdfforge/releases/tag/v1.0.0


## [2.2.0] - 2025-11-15

### Added
- Navigation: “TOC Manager” added to the top menu for quick access (`pdfforge/templates/base.html`).
- CI/CD: Manual Release workflow with safety checks (`.github/workflows/release.yml`).
  - Requires `tag` input and `confirm=YES` to proceed
  - Validates SemVer tag format and verifies the tag exists
  - Runs smoke tests with `pytest -q` before releasing
  - Idempotency guard: skips if a Release for the tag already exists
  - Draft by default; `prerelease` auto-detected if tag contains `-`
- Docs: New Releasing guide `docs/RELEASING.md` and README “Releasing” section summarizing the flow.

### Changed
- Homepage: Removed links and UI for the deprecated “Enhanced Merge with TOC” and consolidated to the standard Merge flow (`main.merge_page`).
- Ports: Documentation now recommends using allowed browser ports (e.g., 8080 or 5000). Note about Chromium’s unsafe port policy (6000 is blocked) added.
- Docker: Binds to 8080 and uses the current app factory path `pdfforge.create_app:create_app()` in `Dockerfile` and `docker-compose.yml`.

### Removed
- Enhanced Merge feature references (blueprint unregistered, homepage cards removed). Files remain in repo for now but are unused.

### Notes
- If you still need the Enhanced Merge code, consider archiving files under `docs/_archive/` before removal.


## [2.2.1] - 2025-11-15

### Fixed
- Type checking errors in `pdfforge/core/toc.py` (replaced `any` with `typing.Any`, corrected numeric field types, accurate return annotations).
- Linting issues in `pdfforge/core/toc.py` and `pdfforge/services/toc_service.py` (removed unused imports, replaced bare `except:`, wrapped long debug line).

### Internal
- Ensured all quality checks pass: tests, mypy, flake8, black, and isort.
- Minor refactors to keep style consistent (explicit `float` arithmetic for positions; clarified optional types).


## [2.2.2] - 2025-11-15

### Added
- Unit tests for TOC detection helper and bookmark extraction normalization (`tests/test_toc_core.py`).
- Integration tests for multi-page TOC generation, old TOC removal, link target and outline mapping (`tests/test_toc_integration.py`).
- Documentation section "Existing TOC detection & normalization" explaining behavior and calculations (`docs/TOC.md`).

### Fixed
- Correct handling when PDFs already contain TOC pages: extracted bookmarks in the UI now start from 1 (body pages only). Defensive normalization in `add_toc_to_pdf(...)` ensures incoming pages are adjusted if offset by existing TOC pages.

### Internal
- Ensured tests are lightweight and use in-memory/synthetic PDFs via PyMuPDF for reliability.


## [2.2.3] - 2025-11-15

### Added
- Three-column TOC layout with automatic title wrapping so long titles never overflow margins.
- Functional leader dots option between titles and page numbers; page numbers are right-aligned with a fixed reserve width.
- Documentation updates describing the new layout and `TOCStyle` fields (`docs/TOC.md`).
- Targeted tests for wrapping, column computation, and leader dots behavior (`tests/test_toc_layout.py`).

### Changed
- TOC link rectangles now span the full wrapped entry block, improving clickability for multi-line entries.

### Internal
- Minor refactors in `pdfforge/core/toc.py` to support wrapping and layout helpers; no breaking API changes.
