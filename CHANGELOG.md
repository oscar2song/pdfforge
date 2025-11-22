# Changelog

All notable changes to PDFForge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## 🎉 Major Version - Project Structure Modernization

PDFForge v3.0.0 represents a significant milestone in project maturity, adopting modern Python packaging best practices with the src/ layout structure.

## 📦 What Changed

### Project Structure
```
# OLD (v2.x)
pdfforge/
├── pdfforge/
│   ├── core/
│   └── services/

# NEW (v3.0.0)
pdfforge/
├── src/
│   └── pdfforge/
│       ├── core/
│       └── services/
```

### For End Users: ✅ NO BREAKING CHANGES

**Everything still works the same:**
```python
# Imports - UNCHANGED
from pdfforge.core import PDFMerger
from pdfforge.services import MergeService
import pdfforge

# Installation - UNCHANGED
pip install pdfforge
pip install -e .

# Usage - UNCHANGED
python -m pdfforge.app
```

### For Contributors: ⚠️ Workflow Updates Required

**File locations changed:**
```bash
# Edit files in new location
vim src/pdfforge/core/merge.py  # NEW
# (was: pdfforge/core/merge.py)

# Must install in editable mode
pip install -e .

# Tests still work the same
pytest
```

## 🎯 Why v3.0.0?

This is a **MAJOR** version bump because:

1. **Significant Structural Change** - Adopting src/ layout is a major architectural decision
2. **Developer Workflow Impact** - Contributors must update their development processes
3. **Project Maturity Signal** - Shows adoption of modern Python best practices
4. **Clear Milestone** - Marks the evolution and maturation of the project

## ✨ Benefits of src/ Layout

### 1. **Better Testing**
- Prevents accidental imports of uninstalled code
- Tests run against installed package (not source directory)
- Catches packaging issues before release

### 2. **Cleaner Namespace**
- Source code isolated from project files
- No confusion between package and project root
- Prevents namespace pollution

### 3. **Industry Standard**
- Used by major Python projects (pytest, requests, etc.)
- Recommended by Python Packaging Authority
- Better compatibility with modern build tools

### 4. **Professional Structure**
```
pdfforge/
├── src/                    # All source code here
│   └── pdfforge/
├── tests/                  # Tests separate from source
├── docs/                   # Documentation
├── scripts/                # Utilities
└── pyproject.toml          # Modern packaging
```

## 🔧 Technical Details

### Files Modified
- **pyproject.toml**: Updated package discovery
- **pytest configuration**: Updated paths
- **Coverage settings**: Updated source paths
- **All documentation**: Updated import examples

### Files Moved
- `pdfforge/` → `src/pdfforge/`
- All core modules relocated
- All service modules relocated
- Package structure preserved

### Configuration Updates
```toml
# pyproject.toml
[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]

[tool.coverage.run]
source = ["src"]
```

## 📊 Compatibility Matrix

| Aspect | v2.x | v3.0.0 | Breaking? |
|--------|------|--------|-----------|
| Import statements | ✅ | ✅ | ❌ No |
| CLI usage | ✅ | ✅ | ❌ No |
| API methods | ✅ | ✅ | ❌ No |
| Installation | ✅ | ✅ | ❌ No |
| File locations | ✅ | ⚠️ | ⚠️ Contributors only |
| Dev workflow | ✅ | ⚠️ | ⚠️ Contributors only |

## 🚀 Migration Guide

### For End Users
**No action required!** Just update:
```bash
pip install --upgrade pdfforge
```

### For Contributors

**1. Pull latest changes:**
```bash
git pull origin main
```

**2. Reinstall in development mode:**
```bash
pip install -e .
```

**3. Update your editor/IDE:**
- Source code now in: `src/pdfforge/`
- Update file paths in your editor
- Update any custom scripts

**4. Continue as normal:**
```bash
# Edit files in src/
vim src/pdfforge/core/merge.py

# Tests work the same
pytest

# Code quality checks work the same
pylint src/pdfforge
mypy src/pdfforge
```

## 📈 Project Status

### Code Quality: EXCELLENT ✅
- ✅ All tests passing (26/26)
- ✅ 100% type coverage (mypy)
- ✅ Pylint score: 10/10
- ✅ All files formatted (black)

### Documentation: UPDATED ✅
- ✅ README.md updated
- ✅ CONTRIBUTING.md updated
- ✅ API documentation updated
- ✅ Architecture docs updated

### Git Status: CLEAN ✅
- ✅ All changes committed
- ✅ Working directory clean
- ✅ Ready for release

## 🔄 Changelog Summary

### Added
- src/ layout structure for better packaging practices
- Enhanced project organization
- Improved testing isolation

### Changed
- Source code location: `pdfforge/` → `src/pdfforge/`
- Package discovery configuration in pyproject.toml
- Test and coverage paths updated

### Maintained
- All import statements (backward compatible)
- All CLI commands (unchanged)
- All API methods (unchanged)
- All functionality (100% preserved)

## 🎓 Learning Resources

Understanding src/ layout:
- [Python Packaging Guide](https://packaging.python.org/en/latest/tutorials/packaging-projects/)
- [pytest Good Integration Practices](https://docs.pytest.org/en/stable/goodpractices.html)
- [Hynek Schlawack - Testing & Packaging](https://hynek.me/articles/testing-packaging/)

## 🙏 Acknowledgments

This release adopts best practices from the Python community and follows recommendations from:
- Python Packaging Authority (PyPA)
- pytest documentation
- Modern Python project templates

## 📅 Release Timeline

- **Development Start**: November 20, 2025
- **Migration Complete**: November 22, 2025
- **Testing Complete**: November 22, 2025
- **Release Date**: November 22, 2025

## 🔮 Future Plans

With this structural foundation in place, v3.x series will focus on:
- Enhanced TOC generation features
- Advanced compression algorithms
- Batch processing improvements
- Performance optimizations

## 📞 Support

If you encounter any issues:
1. Check [Migration Guide](#-migration-guide) above
2. Review [Documentation](https://github.com/oscar2song/pdfforge/tree/main/docs)
3. Open an issue on [GitHub](https://github.com/oscar2song/pdfforge/issues)

## 🎊 Conclusion

v3.0.0 marks a significant step forward in PDFForge's evolution. While the changes are primarily structural, they establish a solid foundation for future development and demonstrate our commitment to Python best practices.

**Thank you for using PDFForge!** 🚀

---

**Version**: 3.0.0  
**Release Date**: November 22, 2025  
**Previous Version**: 2.4.0  
**Breaking Changes**: None (for end users)  
**Migration Required**: Yes (for contributors only)

## [2.4.0] - 2025-11-16

### Added
- New PDF → Word (DOCX) converter (free/local path) with options: page range, merge paragraphs, table detection, keep text boxes, images as background, image DPI/original handling.
- Word UI page with upload, analyze, and convert flows; drag & drop and single-click upload.
- Premium integration shim (optional) to call external SaaS at `http://localhost:5003` using `X-API-Key` for scanned PDFs (OCR) and advanced options; results are downloaded into `downloads/word`.
- Component-aware download scheme across all tools: canonical URLs are now `/download/component/<component>/<file_id>`.
- Home page Word tool card; TOC tool refactor into separate HTML/JS/CSS.

### Changed
- Unified output filename convention for all tools: `yyyyMMdd_HHmmss_OriginalFileName_ACTION.ext` (.pdf for PDF tools, .docx for Word, .zip for archives).
- Split outputs now use range-based suffixes (e.g., `split_pages_1-62.pdf`, `split_pages_63-207.pdf`).
- TOC page restyled to match other tools (clean white header, centered title/subtitle, neutral Upload button).
- Standardized API responses to include component-aware `download_url(s)` and, when applicable, `component_download_url` for ZIPs.

### Fixed
- Word conversion: corrected `pdf2docx.Converter` usage (no context manager) to prevent runtime error.
- Resolved `PyMuPDF` compatibility for `pdf2docx` by pinning `PyMuPDF==1.23.7`.
- Word downloads no longer 404: links now target the component route and search within `downloads/word`.

### Removed
- Legacy download fields removed from API responses:
  - Normalize: `download_url_legacy` (old `/download/<filename>`)
  - Merge: `download_url_legacy` (old `/download/<filename>`)
  - Word (batch): removed `zip_download_url` (use `component_download_url`)
- Frontend fallbacks that constructed legacy `/download/<filename>` links have been removed or are no longer used; UIs use server-provided component URLs exclusively.

### Notes
- Legacy route `/download/<filename>` remains available for backward compatibility, but it now logs a deprecation warning. All first-party pages use component-aware URLs.
- TOC template consolidated; please remove `src/pdfforge/templates/toc2.html` from the repo if still present (the app renders `toc.html`).

## [2.3.0] - 2025-11-15

### Added
- PDF Split feature with multiple methods: by page ranges, fixed page count, approximate max file size, and bookmarks.
- Web UI for Split at `/split/` with live validation and analysis.
- Dedicated stylesheet `static/css/split.css` and front-end logic in `static/js/split.js`.
- Backend service `SplitService`, core logic `PDFSplitterCore`, and routes under `/split`.
- Download routes updated to recognize the `split` component; ZIP auto-creation for multi-part results.
- Home page `tool-card` for Split.

### Changed
- Navigation updated to include Split tool.
- `FilePathManager` now provisions a `downloads/split` directory and supports component-based paths.
- Documentation expanded: `docs/SPLIT.md`, Split API section in `docs/API.md`, README features.

### Fixed
- UI: “Split PDF” button now enables immediately when inputs become valid (no extra click needed).
- Split ranges: Accept shorthand start-pages like "1,63" → contiguous ranges (`1-62`, `63-end`).

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
- Navigation: “TOC Manager” added to the top menu for quick access (`src/pdfforge/templates/base.html`).
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
- Type checking errors in `src/src/pdfforge/core/toc.py` (replaced `any` with `typing.Any`, corrected numeric field types, accurate return annotations).
- Linting issues in `src/src/pdfforge/core/toc.py` and `src/src/pdfforge/services/toc_service.py` (removed unused imports, replaced bare `except:`, wrapped long debug line).

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
- Minor refactors in `src/src/pdfforge/core/toc.py` to support wrapping and layout helpers; no breaking API changes.
