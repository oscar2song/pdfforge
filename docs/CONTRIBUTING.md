# 🤝 Contributing to PDFForge (Updated for src/ layout)

Thank you for contributing to PDFForge! This guide has been updated for our new `src/` layout structure.

## 🚀 Getting Started

### Initial Setup

```bash
# 1. Fork and clone
git clone https://github.com/oscar2song/pdfforge.git
cd pdfforge

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install in editable mode (REQUIRED!)
pip install -e .

# 4. Install dev dependencies
pip install -r requirements-dev.txt

# 5. Verify setup
pytest  # Should pass
python -m pdfforge.app  # Should start
```

## 📁 Understanding the src/ Layout

### Directory Structure

```
pdfforge/
├── src/                       # All source code here
│   └── pdfforge/             # Package directory
│       ├── core/             # Edit: src/src/pdfforge/core/
│       ├── services/         # Edit: src/src/pdfforge/services/
│       └── ...
├── tests/                    # Test files
├── docs/                     # Documentation
└── pyproject.toml           # Knows about src/
```

### Key Concepts

**✅ File Paths (Where to Edit)**
```bash
# Edit these files:
src/src/pdfforge/core/merge.py
src/src/pdfforge/services/merge_service.py
src/src/pdfforge/routes/merge_routes.py
```

**✅ Import Paths (In Your Code)**
```python
# Import like this (no 'src' in imports):
from pdfforge.core.merge import PDFMerger
from pdfforge.services.merge_service import MergeService
```

**✅ Running Code**
```bash
# Both work:
python -m pdfforge.app
python src/pdfforge/app.py
```

## 🛠️ Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/my-feature
```

### 2. Make Changes

**Edit source files in `src/pdfforge/`:**

```bash
# Example: Adding a new feature
vim src/src/pdfforge/core/watermark.py

# Add corresponding service
vim src/src/pdfforge/services/watermark_service.py

# Add routes
vim src/src/pdfforge/routes/watermark_routes.py
```

### 3. Add Tests

```bash
# Create test file
vim tests/test_watermark.py
```

**Test file example:**
```python
# tests/test_watermark.py
import pytest
from pdfforge.core.watermark import WatermarkCore  # Import works!

class TestWatermark:
    def test_apply_watermark(self):
        core = WatermarkCore()
        result = core.apply_watermark(...)
        assert result.success
```

### 4. Run Quality Checks

```bash
# Format code (targets src/)
black src/pdfforge/ tests/
isort src/pdfforge/ tests/

# Lint (targets src/)
flake8 src/pdfforge/ tests/
pylint src/pdfforge/

# Type check (targets src/)
mypy src/pdfforge/

# Run all checks
python scripts/run_quality_checks.py
```

### 5. Run Tests

```bash
# Tests import from installed package
pytest

# With coverage
pytest --cov=pdfforge --cov-report=html

# Specific test
pytest tests/test_watermark.py
```

### 6. Commit and Push

```bash
git add src/pdfforge/ tests/
git commit -m "feat(watermark): add PDF watermark feature"
git push origin feature/my-feature
```

## 📝 Style Guidelines

### File Locations

**✅ Correct:**
```python
# When editing, use src/ paths:
# - src/src/pdfforge/core/merge.py
# - src/src/pdfforge/services/merge_service.py
# - src/src/pdfforge/routes/merge_routes.py

# When importing, NO src/:
from pdfforge.core.merge import PDFMerger
from pdfforge.services import MergeService
```

**❌ Incorrect:**
```python
# DON'T import with 'src':
from src.pdfforge.core.merge import PDFMerger  # Wrong!

# DON'T use old paths in docs:
# Edit src/pdfforge/core/merge.py  # Old, wrong
```

### Code Style (Unchanged)

```python
# Style rules remain the same
from typing import List, Optional
from pathlib import Path

def process_pdf(
    file_path: Path,
    options: dict
) -> ProcessResult:
    """
    Process PDF file.
    
    Args:
        file_path: Path to PDF
        options: Processing options
        
    Returns:
        Processing result
    """
    pass
```

## 🧪 Testing Guidelines

### Writing Tests

```python
# tests/test_feature.py
import pytest
from pdfforge.core.feature import FeatureCore  # Imports work!

@pytest.fixture
def sample_pdf(tmp_path):
    """Create sample PDF."""
    pdf_path = tmp_path / "test.pdf"
    # Create PDF
    return pdf_path

def test_feature(sample_pdf):
    """Test feature functionality."""
    core = FeatureCore()
    result = core.process(sample_pdf)
    assert result.success
```

### Running Tests

```bash
# All tests (imports from src/)
pytest

# Specific module
pytest tests/test_merge.py

# With output
pytest -v -s

# Coverage (covers src/pdfforge/)
pytest --cov=pdfforge --cov-report=html
```

## 🐛 Debugging Tips

### Import Issues

```bash
# If imports don't work:
pip install -e .  # Reinstall in editable mode

# Verify installation:
pip list | grep pdfforge
# Should show: pdfforge 2.x.x /path/to/pdfforge/src

# Check imports:
python -c "import pdfforge; print(pdfforge.__file__)"
# Should show: /path/to/pdfforge/src/pdfforge/__init__.py
```

### Common Mistakes

**❌ Mistake 1: Editing wrong location**
```bash
# Wrong - editing non-existent old location
vim src/pdfforge/core/merge.py  # This doesn't exist!

# Right - editing in src/
vim src/src/pdfforge/core/merge.py  # Correct!
```

**❌ Mistake 2: Wrong import**
```python
# Wrong
from src.pdfforge.core import PDFMerger  # Don't include 'src'

# Right
from pdfforge.core import PDFMerger  # Correct!
```

**❌ Mistake 3: Not installing**
```bash
# Wrong - running tests without install
cd pdfforge
pytest  # Imports may fail!

# Right - install first
pip install -e .
pytest  # Works!
```

## 📚 Documentation Updates

When updating docs, use correct paths:

**In documentation (file paths):**
```markdown
Edit the merge core logic in `src/src/pdfforge/core/merge.py`
```

**In code examples (imports):**
```python
from pdfforge.core.merge import PDFMerger
```

## 🔄 Migration Notes for Contributors

If you have an old checkout:

```bash
# Update your fork
git pull upstream main

# Your working directory changes:
# OLD: src/pdfforge/core/merge.py
# NEW: src/src/pdfforge/core/merge.py

# BUT imports stay the same:
from pdfforge.core.merge import PDFMerger  # Still works!

# Reinstall
pip install -e .
```

## ✅ Pre-Commit Checklist

Before submitting PR:

- [ ] Changes in `src/pdfforge/` (not old location)
- [ ] Tests in `tests/` (use correct imports)
- [ ] Ran `pip install -e .`
- [ ] Tests pass: `pytest`
- [ ] Code formatted: `black src/pdfforge/ tests/`
- [ ] Imports sorted: `isort src/pdfforge/ tests/`
- [ ] Linting passes: `flake8 src/pdfforge/`
- [ ] Type checks: `mypy src/pdfforge/`
- [ ] Docs updated (use `src/` paths)

## 🎓 Learning Resources

- [Why use src/ layout?](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)
- [Python Packaging Guide](https://packaging.python.org/)
- [PDFForge Architecture](docs/ARCHITECTURE.md)

## 📞 Getting Help

- Check [DEVELOPMENT.md](docs/DEVELOPMENT.md)
- Ask in GitHub Discussions
- Email: oscar2song@gmail.com

## 🙏 Thank You!

Thank you for contributing to PDFForge! The src/ layout makes our codebase more maintainable and professional.

---

**Key Takeaways:**
- ✅ Edit: `src/pdfforge/` (file paths)
- ✅ Import: `from pdfforge.X` (no 'src')
- ✅ Install: `pip install -e .` (required!)
- ✅ Test: `pytest` (works after install)

**Last Updated**: November 2025