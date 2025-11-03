# 🤝 Contributing to PDFForge

Thank you for your interest in contributing to PDFForge! This document provides guidelines and instructions for contributing.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Process](#development-process)
- [Style Guidelines](#style-guidelines)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)

## 📜 Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards

**Positive behavior includes:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Unacceptable behavior includes:**
- Trolling, insulting/derogatory comments, and personal attacks
- Public or private harassment
- Publishing others' private information without permission
- Other conduct which could reasonably be considered inappropriate

### Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be reported by contacting the project team at oscar2song@gmail.com.

## 🚀 Getting Started

### Prerequisites

- Python 3.11+ (3.12 recommended)
- Git
- Basic understanding of Flask and Python
- Familiarity with PDF manipulation concepts (helpful but not required)

### Initial Setup

1. **Fork the Repository**
   - Visit https://github.com/oscar2song/pdfforge
   - Click "Fork" button in the top right

2. **Clone Your Fork**
```bash
git clone https://github.com/YOUR_USERNAME/pdfforge.git
cd pdfforge
```

3. **Add Upstream Remote**
```bash
git remote add upstream https://github.com/oscar2song/pdfforge.git
```

4. **Set Up Development Environment**
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

5. **Verify Setup**
```bash
# Run tests
pytest

# Start development server
python app.py
```

## 🛠️ How to Contribute

### Types of Contributions

We welcome the following types of contributions:

1. **Bug Fixes**
   - Fix existing issues
   - Improve error handling
   - Fix documentation errors

2. **New Features**
   - Add new PDF operations
   - Improve existing functionality
   - Add new utilities

3. **Documentation**
   - Improve README
   - Add code examples
   - Write tutorials
   - Translate documentation

4. **Tests**
   - Add missing tests
   - Improve test coverage
   - Add integration tests

5. **Performance**
   - Optimize algorithms
   - Improve memory usage
   - Speed improvements

6. **Code Quality**
   - Refactor code
   - Improve readability
   - Add type hints

## 🔄 Development Process

### 1. Find or Create an Issue

- Check [existing issues](https://github.com/oscar2song/pdfforge/issues)
- Comment on an issue you'd like to work on
- Create a new issue for new features or bugs
- Wait for approval before starting major work

### 2. Create a Branch

```bash
# Update your main branch
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/bug-description
```

**Branch naming conventions:**
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions/improvements

### 3. Make Changes

- Write clean, readable code
- Follow style guidelines
- Add/update tests
- Update documentation
- Keep commits focused and atomic

### 4. Test Your Changes

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pdfforge --cov-report=html

# Run specific tests
pytest tests/test_merge.py

# Check code style
black pdfforge/ tests/
isort pdfforge/ tests/
flake8 pdfforge/ tests/
mypy pdfforge/
```

### 5. Commit Changes

Follow commit message guidelines (see below)

```bash
git add .
git commit -m "feat: add PDF split functionality"
```

### 6. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

### 7. Create Pull Request

- Go to your fork on GitHub
- Click "New Pull Request"
- Fill out the PR template
- Link related issues

## 📝 Style Guidelines

### Python Code Style

We follow **PEP 8** with Black formatting:

```python
# ✅ Good
def merge_pdfs(
    files: List[PDFFile], 
    options: MergeOptions
) -> fitz.Document:
    """
    Merge multiple PDF files into one.
    
    Args:
        files: List of PDFFile objects to merge
        options: Merge configuration options
        
    Returns:
        Merged PDF document
    """
    logger.info(f"Merging {len(files)} PDF files")
    return perform_merge(files, options)


# ❌ Bad
def MergePdfs(files,options):
    # No docstring, inconsistent naming
    return perform_merge(files,options)
```

### Docstring Style

Use **Google-style docstrings**:

```python
def process_pdf(
    file_path: Path,
    options: dict,
    output_dir: Optional[Path] = None
) -> ProcessResult:
    """
    Process a PDF file with specified options.
    
    This function performs comprehensive PDF processing including
    validation, transformation, and output generation.
    
    Args:
        file_path: Path to the PDF file to process
        options: Processing options dictionary containing:
            - mode: Processing mode ('simple' or 'advanced')
            - quality: Output quality (1-10)
            - compress: Whether to compress output
        output_dir: Optional output directory. If None, uses default.
    
    Returns:
        ProcessResult object containing:
            - success: Boolean indicating success
            - output_path: Path to processed file
            - stats: Processing statistics dictionary
    
    Raises:
        FileNotFoundError: If file_path doesn't exist
        ValidationError: If options are invalid
        ProcessingError: If processing fails
    
    Example:
        >>> result = process_pdf(
        ...     Path("input.pdf"),
        ...     {"mode": "simple", "quality": 8},
        ...     Path("output/")
        ... )
        >>> print(result.success)
        True
    """
    pass
```

### Type Hints

Always use type hints:

```python
from typing import List, Dict, Optional, Union
from pathlib import Path

def save_files(
    files: List[bytes],
    directory: Path,
    prefix: str = "output",
    overwrite: bool = False
) -> List[Path]:
    """Save multiple files to directory."""
    pass
```

### Import Order

Use `isort` for import organization:

```python
# Standard library imports
import os
import sys
from pathlib import Path
from typing import List, Optional

# Third-party imports
import fitz
from flask import Flask, request, jsonify

# Local imports
from pdfforge.core.merge import PDFMerger
from pdfforge.models.options import MergeOptions
from pdfforge.utils.validation import validate_pdf
```

## 💬 Commit Guidelines

### Commit Message Format

We follow the **Conventional Commits** specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `build`: Build system changes
- `ci`: CI/CD changes
- `chore`: Other changes (maintenance, etc.)

### Examples

```bash
# Feature
git commit -m "feat(merge): add support for bookmark preservation"

# Bug fix
git commit -m "fix(compress): prevent file size increase on compression"

# Documentation
git commit -m "docs(readme): update installation instructions"

# With body
git commit -m "feat(split): add PDF split functionality

- Implement core split logic
- Add split service layer
- Create split routes
- Add tests for split operation

Closes #123"
```

### Commit Best Practices

- Keep commits focused and atomic
- Write clear, descriptive messages
- Reference issues when applicable
- Break large changes into smaller commits

## 🔍 Pull Request Process

### Before Submitting

Ensure your PR:
- [ ] Passes all tests
- [ ] Has no linting errors
- [ ] Includes tests for new features
- [ ] Updates documentation
- [ ] Follows code style guidelines
- [ ] Has descriptive commit messages
- [ ] Is up to date with main branch

### PR Template

When creating a PR, include:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe how you tested your changes

## Screenshots (if applicable)
Add screenshots for UI changes

## Checklist
- [ ] Tests pass
- [ ] Documentation updated
- [ ] Code follows style guidelines
- [ ] Self-review completed

## Related Issues
Closes #123
```

### Review Process

1. **Automated Checks**
   - Tests must pass
   - Linting must pass
   - Coverage should not decrease

2. **Code Review**
   - At least one maintainer approval required
   - Address review comments
   - Make requested changes

3. **Merge**
   - Squash and merge (default)
   - Maintainer will merge after approval

## 🐛 Reporting Bugs

### Before Reporting

1. Check [existing issues](https://github.com/oscar2song/pdfforge/issues)
2. Verify it's reproducible in the latest version
3. Collect relevant information

### Bug Report Template

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '....'
3. Upload file '...'
4. See error

**Expected behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
 - OS: [e.g., Windows 10]
 - Python Version: [e.g., 3.12]
 - PDFForge Version: [e.g., 2.0.0]

**Additional context**
Any other relevant information.

**Sample Files**
If possible, attach sample PDF files (if not sensitive).
```

## 💡 Suggesting Features

### Before Suggesting

1. Check [existing feature requests](https://github.com/oscar2song/pdfforge/issues?q=is%3Aissue+is%3Aopen+label%3Aenhancement)
2. Consider if it aligns with project goals
3. Think about implementation approach

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
A clear description of the problem.

**Describe the solution you'd like**
Clear description of what you want to happen.

**Describe alternatives you've considered**
Any alternative solutions or features.

**Use cases**
Describe who would benefit and how.

**Additional context**
Mockups, examples, or other context.

**Implementation ideas**
If you have ideas about implementation.
```

## 🧪 Testing Guidelines

### Writing Tests

```python
import pytest
from pdfforge.core.merge import PDFMerger

class TestPDFMerger:
    """Test suite for PDF merger."""
    
    @pytest.fixture
    def merger(self):
        """Create merger instance."""
        return PDFMerger()
    
    def test_merge_basic(self, merger, sample_pdfs):
        """Test basic merge functionality."""
        result = merger.merge(sample_pdfs)
        assert result is not None
        assert len(result) == len(sample_pdfs)
    
    def test_merge_invalid_input(self, merger):
        """Test merge with invalid input."""
        with pytest.raises(ValidationError):
            merger.merge([])
```

### Test Coverage

- Aim for 80%+ coverage
- Test happy paths
- Test error cases
- Test edge cases

### Running Tests

```bash
# All tests
pytest

# Specific file
pytest tests/test_merge.py

# Specific test
pytest tests/test_merge.py::TestPDFMerger::test_merge_basic

# With coverage
pytest --cov=pdfforge --cov-report=html
```

## 📚 Documentation

### Types of Documentation

1. **Code Comments**
   - Explain complex logic
   - Document non-obvious decisions
   - Keep comments up to date

2. **Docstrings**
   - All public functions/classes
   - Use Google style
   - Include examples

3. **README Updates**
   - New features
   - Changed behavior
   - New dependencies

4. **Tutorial/Guides**
   - Step-by-step guides
   - Use cases
   - Best practices

## 🏅 Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Recognized in project README

## 📞 Getting Help

### Resources

- [Documentation](docs/)
- [GitHub Discussions](https://github.com/oscar2song/pdfforge/discussions)
- [Issue Tracker](https://github.com/oscar2song/pdfforge/issues)

### Contact

- Email: oscar2song@gmail.com
- GitHub: [@oscar2song](https://github.com/oscar2song)

## 📝 Additional Notes

### First-Time Contributors

Welcome! Here are some good first issues:
- Documentation improvements
- Test additions
- Bug fixes labeled "good first issue"
- Code comment additions

### Questions?

Don't hesitate to ask questions! We're here to help:
- Comment on the issue
- Ask in GitHub Discussions
- Email the maintainers

## 🙏 Thank You!

Thank you for contributing to PDFForge! Your efforts help make PDF processing better for everyone.

---

**Last Updated**: November 2025
**Version**: 2.0.0
