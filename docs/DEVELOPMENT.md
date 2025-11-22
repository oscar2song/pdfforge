# 👨‍💻 PDFForge Development Guide

Complete guide for developers contributing to or extending PDFForge.

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+** (Python 3.12 recommended)
- **Git** for version control
- **IDE** (VS Code, PyCharm, or similar)
- **Tesseract-OCR** (optional, for OCR features)

### Initial Setup

1. **Fork and Clone**
```bash
# Fork the repository on GitHub first
git clone https://github.com/yourusername/pdfforge.git
cd pdfforge

# Add upstream remote
git remote add upstream https://github.com/oscar2song/pdfforge.git
```

2. **Create Virtual Environment**
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

3. **Install Dependencies**
```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

4. **Setup Environment**
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your local settings (optional)
nano .env  # or your preferred editor
```

5. **Verify Installation**
```bash
# Run tests
pytest

# Start development server
python app.py
```

## 📁 Project Structure

```
pdfforge/
├── pdfforge/              # Main package
│   ├── core/             # Core PDF processing
│   ├── services/         # Business logic
│   ├── routes/           # Flask blueprints
│   ├── models/           # Data models
│   ├── utils/            # Utilities
│   ├── exceptions/       # Custom exceptions
│   ├── templates/        # HTML templates
│   └── static/           # CSS/JS/images
├── tests/                # Test suite
├── docs/                 # Documentation
└── scripts/              # Utility scripts
```

### Key Files

- `app.py` - Application entry point (~50 lines)
- `config.py` - Configuration management
- `src/pdfforge/create_app.py` - Flask app factory
- `requirements.txt` - Production dependencies
- `requirements-dev.txt` - Development dependencies

## 🔨 Development Workflow

### 1. Create Feature Branch

```bash
# Update main branch
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name
```

### 2. Make Changes

Follow the coding standards and architecture patterns described below.

### 3. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pdfforge --cov-report=html

# Run specific test file
pytest tests/test_merge.py

# Run specific test
pytest tests/test_merge.py::TestPDFMerger::test_merge_two_pdfs

# Run in verbose mode
pytest -v

# Run and show print statements
pytest -s
```

### 4. Code Quality Checks

```bash
# Format code with Black
black src/pdfforge/ tests/

# Sort imports with isort
isort src/pdfforge/ tests/

# Lint with flake8
flake8 src/pdfforge/ tests/

# Type check with mypy
mypy src/pdfforge/

# Lint with pylint
pylint src/pdfforge/
```

### 5. Commit Changes

```bash
# Add files
git add .

# Commit with descriptive message
git commit -m "feat: add new PDF split functionality"

# Follow conventional commits format:
# feat: New feature
# fix: Bug fix
# docs: Documentation changes
# style: Code style changes (formatting, etc.)
# refactor: Code refactoring
# test: Adding or updating tests
# chore: Maintenance tasks
```

### 6. Push and Create PR

```bash
# Push to your fork
git push origin feature/your-feature-name

# Create Pull Request on GitHub
# Provide clear description of changes
```

## 📝 Coding Standards

### Python Style Guide

Follow **PEP 8** with these specifics:

```python
# Line length: 88 characters (Black default)
# Indentation: 4 spaces
# Quotes: Double quotes for strings
# Imports: Sorted with isort

# Good
def merge_pdfs(files: List[PDFFile], options: MergeOptions) -> fitz.Document:
    """
    Merge multiple PDF files into one.
    
    Args:
        files: List of PDFFile objects to merge
        options: Merge configuration options
        
    Returns:
        Merged PDF document
        
    Raises:
        PDFMergeError: If merge fails
    """
    pass

# Bad
def MergePdfs(files,options):
    # No docstring, bad naming, no type hints
    pass
```

### Docstring Format

Use **Google Style** docstrings:

```python
def process_page(page: fitz.Page, header: str, options: dict) -> fitz.Page:
    """
    Process a PDF page by adding header and adjusting layout.
    
    This function adds a header to the page and adjusts the content
    to accommodate the header space. It handles both scanned and
    digital PDFs differently.
    
    Args:
        page: The PDF page to process
        header: Header text to add
        options: Processing options including:
            - font_size: Font size for header (default: 12)
            - spacing: Space between header and content (default: 20)
            - color: Header text color (default: black)
    
    Returns:
        The processed PDF page with header added
    
    Raises:
        PDFProcessingError: If page processing fails
        ValueError: If invalid options provided
    
    Example:
        >>> page = doc[0]
        >>> options = {"font_size": 14, "spacing": 25}
        >>> processed_page = process_page(page, "Confidential", options)
    """
    pass
```

### Type Hints

Use type hints everywhere:

```python
from typing import List, Dict, Optional, Union, Tuple
from pathlib import Path

def save_file(
    content: bytes,
    filename: str,
    directory: Path,
    overwrite: bool = False
) -> Optional[Path]:
    """Save file with type-checked parameters."""
    pass
```

### Naming Conventions

```python
# Classes: PascalCase
class PDFMerger:
    pass

# Functions and methods: snake_case
def merge_pdfs():
    pass

# Constants: UPPER_SNAKE_CASE
MAX_FILE_SIZE = 500 * 1024 * 1024

# Private methods: _leading_underscore
def _internal_helper():
    pass

# Module-level "private" vars: _leading_underscore
_internal_cache = {}
```

## 🏗️ Architecture Patterns

### 1. Service Pattern

Services coordinate business logic:

```python
class MergeService:
    """Service for PDF merge operations."""
    
    def __init__(self):
        self.merger = PDFMerger()
        self.validator = FileValidator()
        self.file_manager = FileManager()
    
    def merge_pdfs(
        self, 
        files: List[FileStorage], 
        options: MergeOptions
    ) -> MergeResult:
        """
        Merge PDF files with validation and error handling.
        
        This method orchestrates the entire merge workflow:
        1. Validate input files
        2. Save uploaded files temporarily
        3. Perform merge operation
        4. Save output file
        5. Cleanup temporary files
        """
        # Validate
        self.validator.validate_files(files)
        
        # Save uploads
        pdf_files = self.file_manager.save_uploads(files)
        
        try:
            # Perform merge
            output_pdf = self.merger.merge(pdf_files, options)
            
            # Save output
            output_path = self.file_manager.save_output(
                output_pdf, 
                options.output_name
            )
            
            return MergeResult(
                success=True,
                path=output_path,
                page_count=len(output_pdf)
            )
        finally:
            # Always cleanup
            self.file_manager.cleanup(pdf_files)
```

### 2. Blueprint Pattern

Use Flask blueprints for routes:

```python
from flask import Blueprint, request, jsonify, send_file

merge_bp = Blueprint('merge', __name__)

@merge_bp.route('/upload', methods=['POST'])
def upload_files():
    """Handle file uploads."""
    pass

@merge_bp.route('/merge', methods=['POST'])
def merge_pdfs():
    """Execute merge operation."""
    try:
        # Get service
        service = MergeService()
        
        # Process request
        files = request.files.getlist('files')
        options = extract_merge_options(request.form)
        
        # Execute
        result = service.merge_pdfs(files, options)
        
        # Return
        return send_file(result.path, as_attachment=True)
    except ValidationError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Merge failed: {e}", exc_info=True)
        return jsonify({'error': 'Merge failed'}), 500
```

### 3. Model Pattern

Use dataclasses for models:

```python
from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class MergeOptions:
    """Options for PDF merge operation."""
    
    add_headers: bool = False
    page_start: int = 1
    output_name: Optional[str] = None
    smart_spacing: bool = True
    header_configs: List['HeaderConfig'] = field(default_factory=list)
    
    def validate(self) -> None:
        """Validate merge options."""
        if self.page_start < 1:
            raise ValueError("Page start must be >= 1")
        
        if self.output_name:
            if not self.output_name.endswith('.pdf'):
                self.output_name += '.pdf'
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MergeOptions':
        """Create from dictionary."""
        return cls(**{
            k: v for k, v in data.items() 
            if k in cls.__dataclass_fields__
        })
```

### 4. Exception Handling

Use custom exceptions:

```python
# Define exceptions
class PDFForgeError(Exception):
    """Base exception for PDFForge."""
    pass

class PDFProcessingError(PDFForgeError):
    """Error during PDF processing."""
    pass

class ValidationError(PDFForgeError):
    """Validation error."""
    pass

# Use in code
def process_pdf(file: Path) -> Document:
    """Process PDF file."""
    if not file.exists():
        raise ValidationError(f"File not found: {file}")
    
    try:
        doc = fitz.open(file)
        return doc
    except Exception as e:
        raise PDFProcessingError(f"Failed to open PDF: {e}") from e
```

## 🧪 Testing Guidelines

### Test Structure

```python
# tests/test_merge.py
import pytest
from pdfforge.core.merge import PDFMerger
from pdfforge.models.merge_options import MergeOptions

class TestPDFMerger:
    """Test suite for PDFMerger class."""
    
    @pytest.fixture
    def merger(self):
        """Create merger instance."""
        return PDFMerger()
    
    @pytest.fixture
    def sample_pdfs(self, tmp_path):
        """Create sample PDF files."""
        # Create test PDFs
        pass
    
    def test_merge_two_pdfs(self, merger, sample_pdfs):
        """Test merging two PDF files."""
        result = merger.merge(sample_pdfs)
        
        assert result is not None
        assert len(result) == 2
    
    def test_merge_with_invalid_input(self, merger):
        """Test merge with invalid input."""
        with pytest.raises(ValidationError):
            merger.merge([])
    
    @pytest.mark.parametrize("page_start", [1, 5, 10])
    def test_merge_with_different_page_starts(
        self, merger, sample_pdfs, page_start
    ):
        """Test merge with different starting page numbers."""
        options = MergeOptions(page_start=page_start)
        result = merger.merge(sample_pdfs, options)
        
        assert result is not None
```

### Test Coverage

Aim for **80%+ coverage**:

```bash
# Run with coverage
pytest --cov=pdfforge --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Mocking

Use pytest-mock for mocking:

```python
def test_merge_with_file_error(mocker, merger):
    """Test merge when file operations fail."""
    # Mock file operations
    mock_open = mocker.patch('fitz.open')
    mock_open.side_effect = IOError("File not found")
    
    # Test error handling
    with pytest.raises(PDFProcessingError):
        merger.merge(sample_pdfs)
```

## 🔧 Development Tools

### VS Code Setup

Create `.vscode/settings.json`:

```json
{
    "python.defaultInterpreterPath": ".venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "editor.rulers": [88],
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false
}
```

### PyCharm Setup

1. Set Python interpreter to `.venv`
2. Enable pytest as test runner
3. Configure Black as code formatter
4. Enable type checking

### Git Hooks (Optional)

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash
# Run before each commit

# Format code
black src/pdfforge/ tests/
isort src/pdfforge/ tests/

# Run linters
flake8 src/pdfforge/ tests/ || exit 1

# Run tests
pytest || exit 1
```

## 📊 Debugging

### Logging

Use structured logging:

```python
import logging

logger = logging.getLogger(__name__)

def merge_pdfs(files, options):
    logger.info(
        "Starting merge",
        extra={
            'file_count': len(files),
            'has_headers': options.add_headers
        }
    )
    
    try:
        result = perform_merge(files, options)
        logger.info(
            "Merge successful",
            extra={'output_path': result.path}
        )
        return result
    except Exception as e:
        logger.error(
            "Merge failed",
            exc_info=True,
            extra={'error': str(e)}
        )
        raise
```

### Debug Mode

Run Flask in debug mode:

```python
# app.py
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

Or use environment variable:

```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
python app.py
```

### Interactive Debugging

Use `pdb` for debugging:

```python
def complex_function():
    # ... some code ...
    
    import pdb; pdb.set_trace()  # Debugger stops here
    
    # ... more code ...
```

Or use VS Code/PyCharm breakpoints.

## 🚀 Performance Optimization

### Profiling

Profile code performance:

```python
import cProfile
import pstats

def profile_function():
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Run code to profile
    result = expensive_operation()
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)  # Top 10 functions
```

### Memory Profiling

Use `memory_profiler`:

```python
from memory_profiler import profile

@profile
def memory_intensive_function():
    large_list = [i for i in range(1000000)]
    return large_list
```

## 📚 Adding New Features

### Step-by-Step Guide

1. **Plan the Feature**
   - Define requirements
   - Design API/interface
   - Consider edge cases

2. **Create Models** (if needed)
```python
# src/pdfforge/models/split_options.py
@dataclass
class SplitOptions:
    """Options for PDF split operation."""
    split_at_pages: List[int]
    output_prefix: str
```

3. **Implement Core Logic**
```python
# src/pdfforge/core/split.py
class PDFSplitter:
    """Core PDF splitting logic."""
    
    def split(self, pdf: Document, options: SplitOptions):
        """Split PDF at specified pages."""
        pass
```

4. **Create Service Layer**
```python
# src/pdfforge/services/split_service.py
class SplitService:
    """Service for PDF split operations."""
    
    def __init__(self):
        self.splitter = PDFSplitter()
    
    def split_pdf(self, file, options):
        """Split PDF with validation and error handling."""
        pass
```

5. **Add Routes**
```python
# src/pdfforge/routes/split.py
split_bp = Blueprint('split', __name__)

@split_bp.route('/split', methods=['POST'])
def split_pdf():
    """Split PDF endpoint."""
    pass
```

6. **Add Templates**
```html
<!-- pdfforge/templates/split.html -->
{% extends "base.html" %}
{% block content %}
<!-- Split UI here -->
{% endblock %}
```

7. **Write Tests**
```python
# tests/test_split.py
class TestPDFSplitter:
    """Test suite for PDF splitter."""
    pass
```

8. **Update Documentation**
   - Update README.md
   - Add usage examples
   - Update API documentation

## 🐛 Common Issues

### Import Errors

**Problem**: `ModuleNotFoundError`

**Solution**:
```bash
# Ensure package is installed in editable mode
pip install -e .

# Or add project root to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Test Failures

**Problem**: Tests fail locally but pass in CI

**Solution**:
- Check Python version (CI uses 3.12)
- Verify dependencies match `requirements.txt`
- Check for absolute paths in tests

### PDF Processing Issues

**Problem**: PDFs not processing correctly

**Solution**:
- Check PDF is not corrupted
- Verify PyMuPDF version
- Test with simple PDF first
- Check logs for detailed errors

## 📖 Resources

### Documentation
- [Flask Documentation](https://flask.palletsprojects.com/)
- [PyMuPDF Documentation](https://pymupdf.readthedocs.io/)
- [pytest Documentation](https://docs.pytest.org/)

### Style Guides
- [PEP 8](https://pep8.org/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Type Hints](https://docs.python.org/3/library/typing.html)

### Tools
- [Black](https://black.readthedocs.io/)
- [isort](https://pycqa.github.io/isort/)
- [flake8](https://flake8.pycqa.org/)
- [mypy](http://mypy-lang.org/)

## 🤝 Getting Help

- **GitHub Issues**: Report bugs or request features
- **Discussions**: Ask questions or share ideas
- **Email**: oscar2song@gmail.com
- **Documentation**: Check `docs/` directory

## ✅ Checklist for PRs

Before submitting a Pull Request:

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] Type hints added
- [ ] Docstrings complete
- [ ] No linting errors
- [ ] Commit messages follow conventions
- [ ] Branch is up to date with main

---

**Happy Coding! 🎉**

Last Updated: November 2025 
Version: 2.0.0
