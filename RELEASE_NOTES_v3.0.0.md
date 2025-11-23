# Release v3.0.0 - src/ Layout Migration

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
