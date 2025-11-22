# PDFForge - Updated README.md

Professional PDF processing toolkit with modular architecture and comprehensive features.

## 📦 Project Structure (Updated with src/ layout)

```
pdfforge/
├── src/                       # Source code (src layout)
│   └── pdfforge/             # Main package
│       ├── __init__.py
│       ├── app.py            # Flask application
│       ├── create_app.py     # Application factory
│       ├── config.py         # Configuration
│       ├── core/             # Core PDF processing
│       ├── services/         # Business logic
│       ├── routes/           # API endpoints
│       ├── models/           # Data models
│       ├── utils/            # Utilities
│       ├── exceptions/       # Custom exceptions
│       ├── static/           # Static assets
│       └── templates/        # HTML templates
├── tests/                    # Test suite
├── docs/                     # Documentation
├── scripts/                  # Development scripts
├── pyproject.toml           # Package configuration
├── requirements.txt         # Dependencies
└── README.md
```

## 🚀 Quick Start

### Installation (No Changes Needed!)

```bash
# Clone repository
git clone https://github.com/oscar2song/pdfforge.git
cd pdfforge

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install package (works with src/ layout)
pip install -e .
```

### Development Setup

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests (imports work correctly)
pytest

# Start server
python -m pdfforge.app
# OR
python src/pdfforge/app.py
```

## 💡 Key Points About src/ Layout

### ✅ What Changed
- **File paths**: Source code moved from `pdfforge/` to `src/pdfforge/`
- **Development**: Edit files in `src/pdfforge/` directory

### ✅ What Stayed the Same
- **Import paths**: Still `from pdfforge.core import ...`
- **Installation**: Still `pip install -e .`
- **Usage**: Still `import pdfforge`

### Examples

**Editing files:**
```bash
# Edit source code
vim src/src/pdfforge/core/merge.py
vim src/src/pdfforge/services/merge_service.py
```

**Imports (unchanged!):**
```python
# Still works exactly the same
from pdfforge.core.merge import PDFMerger
from pdfforge.services.merge_service import MergeService
from pdfforge.models.merge import MergeOptions
```

**Running modules:**
```bash
# Both work
python -m pdfforge.app
python src/pdfforge/app.py
```

## 📚 Updated File Paths in Documentation

When referring to source files in docs, use:
- ✅ `src/src/pdfforge/core/merge.py`
- ❌ `src/src/pdfforge/core/merge.py` (old)

When referring to imports in code:
- ✅ `from pdfforge.core.merge import ...` (unchanged!)

## 🧪 Testing

```bash
# Tests import from installed package
pytest

# Coverage
pytest --cov=pdfforge --cov-report=html

# Tests automatically use src/pdfforge/ after pip install -e .
```

## 🔧 Development Workflow

```bash
# 1. Edit source files
vim src/src/pdfforge/core/new_feature.py

# 2. Add tests
vim tests/test_new_feature.py

# 3. Run quality checks
python scripts/run_quality_checks.py

# 4. Run tests (imports work via editable install)
pytest

# 5. Commit changes
git add src/pdfforge/ tests/
git commit -m "feat: add new feature"
```

## 📦 Package Building

```bash
# Build (pyproject.toml knows about src/)
python -m build

# Result: dist/pdfforge-*.whl
# When installed: imports still work as 'pdfforge'
pip install dist/pdfforge-*.whl
```

## 🎯 Benefits of src/ Layout

1. **Prevents Import Accidents**
   - Can't accidentally import from working directory
   - Forces proper package installation

2. **Better Testing**
   - Tests run against installed package
   - Catches packaging issues early

3. **Industry Standard**
   - Modern Python packaging best practice
   - Used by major projects

4. **Clean Separation**
   - Source code in `src/`
   - Tests in `tests/`
   - Docs in `docs/`

## 🤝 Contributing

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

**Important for contributors:**
- Edit files in `src/pdfforge/`
- Imports remain `from pdfforge.X`
- Must run `pip install -e .` before testing

## 📄 License

MIT License - see [LICENSE](LICENSE)

---

**Made with ❤️ by Oscar Song**