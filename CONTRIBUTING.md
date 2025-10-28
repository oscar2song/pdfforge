# Contributing to PDFForge

First off, thank you for considering contributing to PDFForge! 🎉

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Style Guidelines](#style-guidelines)
- [Issue Guidelines](#issue-guidelines)

---

## 🤝 Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code:

- Be respectful and inclusive
- Welcome newcomers and beginners
- Accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

---

## 🎯 How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce** the issue
- **Expected behavior** vs actual behavior
- **Screenshots** if applicable
- **Environment details**: OS, Python version, browser
- **Error messages** or logs

**Example Bug Report:**
```markdown
**Title**: Merge fails with PDFs containing form fields

**Description**: When merging PDFs that contain interactive form fields, 
the merge process fails with an error.

**Steps to Reproduce**:
1. Upload PDF with form fields
2. Upload another PDF
3. Click Merge
4. Error occurs

**Expected**: PDFs merge successfully
**Actual**: Error message "Cannot process form fields"

**Environment**:
- OS: Windows 11
- Python: 3.12.7
- Browser: Chrome 119
```

### Suggesting Features

Feature suggestions are welcome! Please:

- **Check existing feature requests** first
- **Describe the problem** you're trying to solve
- **Describe the solution** you'd like
- **Describe alternatives** you've considered
- **Explain use cases** with examples

### Contributing Code

1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes
4. **Test** thoroughly
5. **Submit** a pull request

---

## 🔧 Development Setup

### 1. Fork and Clone

```bash
# Fork on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/pdfforge.git
cd pdfforge
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate it
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt

# Install development dependencies (optional)
pip install pytest black flake8 mypy
```

### 4. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 5. Make Changes

Edit code, add features, fix bugs...

### 6. Test Your Changes

```bash
# Run the application
python app.py

# Test manually in browser
# http://localhost:5000

# Run tests (if available)
pytest
```

### 7. Commit Changes

```bash
git add .
git commit -m "Add feature: your feature description"
```

Use clear, descriptive commit messages:
- ✅ "Add batch processing for normalize"
- ✅ "Fix header alignment issue in merge"
- ❌ "Fixed stuff"
- ❌ "Update"

---

## 📤 Pull Request Process

### Before Submitting

- [ ] Code follows project style guidelines
- [ ] All tests pass (if applicable)
- [ ] Updated documentation if needed
- [ ] Added comments for complex logic
- [ ] No unnecessary files or changes
- [ ] Tested on multiple browsers/platforms (if UI changes)

### Submitting PR

1. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create Pull Request on GitHub**
   - Use clear, descriptive title
   - Reference related issues
   - Describe changes in detail
   - Add screenshots if UI changes

3. **PR Template**
   ```markdown
   ## Description
   Brief description of changes
   
   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update
   
   ## Related Issues
   Fixes #123
   
   ## Testing
   Describe how you tested this
   
   ## Screenshots (if applicable)
   Add screenshots here
   
   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Self-review completed
   - [ ] Comments added for complex code
   - [ ] Documentation updated
   - [ ] No new warnings
   ```

### After Submitting

- Respond to feedback promptly
- Make requested changes
- Keep PR up to date with main branch
- Be patient and respectful

---

## 🎨 Style Guidelines

### Python Code Style

Follow **PEP 8** guidelines:

```python
# ✅ Good
def merge_pdfs(file_paths, options=None):
    """
    Merge multiple PDF files.
    
    Args:
        file_paths (list): List of PDF file paths
        options (dict): Optional merge settings
        
    Returns:
        str: Path to merged PDF
    """
    if options is None:
        options = {}
    
    # Process files...
    return output_path


# ❌ Bad
def mergePDFS(files,opts):
    if opts==None:
        opts={}
    return output
```

### Key Rules

- **Indentation**: 4 spaces (no tabs)
- **Line Length**: Max 100 characters
- **Naming**:
  - Functions/variables: `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPER_SNAKE_CASE`
- **Imports**: Grouped and sorted
  ```python
  # Standard library
  import os
  import sys
  
  # Third party
  import flask
  import fitz
  
  # Local
  from app import utils
  ```

### Documentation

- Add docstrings for all functions/classes
- Use clear, concise comments
- Update README for new features
- Include examples in docstrings

```python
def compress_pdf(input_path, output_path, quality=85):
    """
    Compress a PDF file by optimizing images.
    
    Args:
        input_path (str): Path to input PDF
        output_path (str): Path for compressed PDF
        quality (int, optional): JPEG quality 0-100. Defaults to 85.
        
    Returns:
        dict: Statistics including original size, compressed size, and ratio
        
    Example:
        >>> stats = compress_pdf('input.pdf', 'output.pdf', quality=80)
        >>> print(f"Saved {stats['compression_ratio']:.1f}%")
    """
    # Implementation...
```

### HTML/CSS Style

- **Indentation**: 2 spaces
- **Class naming**: kebab-case
- **IDs**: camelCase
- **Semantic HTML**: Use appropriate tags
- **Accessibility**: Include ARIA labels

---

## 📝 Issue Guidelines

### Creating Issues

Use appropriate issue templates:

**Bug Report Template:**
```markdown
**Describe the bug**
Clear description of the bug

**To Reproduce**
1. Step 1
2. Step 2
3. See error

**Expected behavior**
What should happen

**Screenshots**
If applicable

**Environment**
- OS: [e.g., Windows 11]
- Python: [e.g., 3.12.7]
- Browser: [e.g., Chrome 119]

**Additional context**
Any other relevant information
```

**Feature Request Template:**
```markdown
**Is your feature request related to a problem?**
Description of the problem

**Describe the solution you'd like**
Clear description of desired feature

**Describe alternatives you've considered**
Other solutions you've thought about

**Additional context**
Screenshots, mockups, examples
```

### Issue Labels

We use the following labels:

- `bug` - Something isn't working
- `enhancement` - New feature or request
- `documentation` - Documentation improvements
- `good first issue` - Good for newcomers
- `help wanted` - Extra attention needed
- `question` - Further information requested
- `wontfix` - This will not be worked on
- `duplicate` - This issue already exists

---

## 🧪 Testing Guidelines

### Manual Testing Checklist

Before submitting PR, test:

- [ ] All features work as expected
- [ ] No console errors in browser
- [ ] Responsive design (mobile, tablet, desktop)
- [ ] File uploads work correctly
- [ ] Downloads work correctly
- [ ] Edge cases handled (large files, special characters, etc.)

### Automated Testing (Future)

When we add automated tests, ensure:

- [ ] All existing tests pass
- [ ] New tests added for new features
- [ ] Test coverage maintained or improved

---

## 🌟 Recognition

Contributors will be:

- Added to CONTRIBUTORS.md
- Mentioned in release notes
- Credited in README (for major contributions)

---

## 📞 Getting Help

Need help contributing?

- **Discord**: [Join our server](#) (if available)
- **GitHub Discussions**: Ask questions
- **Email**: maintainer@example.com
- **Documentation**: Check the wiki

---

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

## 🙏 Thank You!

Your contributions make PDFForge better for everyone. We appreciate your time and effort! 💙

Happy coding! 🚀
