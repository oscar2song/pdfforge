# 🎉 PDFForge v1.1.0 - Drag-and-Drop File Reordering

## ✨ New Features

### 🔗 Drag-and-Drop File Reordering
**The most requested feature is finally here!**

- **Interactive File Ordering**: Easily reorder PDF files before merging by dragging them in the list
- **Visual Feedback**: 
  - 🎯 Drag handle (☰) on each file item for easy grabbing
  - 🏷️ Order badges (#1, #2, #3...) showing the exact merge sequence
  - ✨ Highlight effect when dragging files
  - 🎨 Visual indicators showing where files will be dropped
  - 🎬 Smooth animations during drag operations
- **Intuitive UX**: Simply click and drag any file to reorder the merge sequence

**How to use:**
1. Upload your PDF files
2. Click and drag any file using the ☰ handle
3. Drop it in the desired position
4. The order badges update automatically
5. Files merge in the order shown (#1, #2, #3...)

## 🎨 UI Improvements

- Added visual drag handles for better user experience
- Order badge indicators for clarity on merge sequence
- Smooth CSS animations during drag operations
- Improved file list styling with better contrast
- Enhanced drop zone visual feedback

## 🐛 Bug Fixes

- Improved file handling stability during upload
- Better error messages for file validation
- Fixed edge cases in drag-and-drop on different browsers

## 📦 Installation

### Quick Start
```bash
git clone https://github.com/oscar2song/pdfforge.git
cd pdfforge
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
python app.py
```

Open your browser to `http://localhost:5000`

### Requirements
- Python 3.11+ (Python 3.12 recommended)
- See `requirements.txt` for package dependencies

### Docker (Coming Soon)
Docker support is planned for v1.2.0!

## 🔄 Upgrade Guide

### Upgrading from v1.0.0

**Good news**: This release is 100% backward compatible! No breaking changes.

```bash
# 1. Backup your current installation (optional)
cp -r pdfforge pdfforge-backup

# 2. Pull latest changes
cd pdfforge
git pull origin main

# 3. No new dependencies, but you can upgrade existing ones
pip install -r requirements.txt --upgrade

# 4. Restart the application
python app.py
```

**What's changed:**
- ✅ All existing features work exactly as before
- ✅ New drag-and-drop feature is automatically available
- ✅ No configuration changes needed
- ✅ No database migrations required

## 📖 Documentation

- **README**: [View updated README](https://github.com/oscar2song/pdfforge/blob/main/README.md)
- **Restructuring Guide**: [View restructuring proposal](https://github.com/oscar2song/pdfforge/blob/main/RESTRUCTURING.md)
- **Changelog**: [View full changelog](https://github.com/oscar2song/pdfforge/blob/main/CHANGELOG.md)

## 📊 Project Stats

- **Total Features**: 3 main tools (Merge, Normalize, Compress)
- **Feature Options**: 20+ customization options
- **Lines of Code**: ~1,850
- **Files Modified in v1.1.0**: `merge.html`
- **Python Version**: 3.11+ (3.12 recommended)
- **Active Development**: ✅ Yes
- **Test Coverage**: Improving (see roadmap)

## 🎯 What's Next?

Check out our [roadmap](https://github.com/oscar2song/pdfforge#-roadmap) for exciting upcoming features:

### v1.2.0 (Planned - Q4 2024)
- 📄 **PDF Split**: Extract specific pages or split into multiple files
- 🐳 **Docker Support**: Easy deployment with Docker
- 🔐 **Password Protection**: Encrypt PDFs

### v1.3.0 (Planned - Q1 2025)
- 🏷️ **PDF Watermark**: Add text/image watermarks
- 🖼️ **PDF to Image**: Convert pages to PNG/JPG
- 📝 **Form Filling**: Fill PDF forms programmatically

### v2.0.0 (Planned - Q2 2025)
- 🌐 **REST API**: Full API access for automation
- 👤 **User Authentication**: Multi-user support
- ☁️ **Cloud Storage**: Integration with S3, Google Drive
- 📊 **Processing History**: Track your operations

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Report Bugs**: [Open an issue](https://github.com/oscar2song/pdfforge/issues/new?template=bug_report.md)
2. **Suggest Features**: [Request a feature](https://github.com/oscar2song/pdfforge/issues/new?template=feature_request.md)
3. **Submit PRs**: Fork, code, and submit a pull request
4. **Improve Docs**: Help us improve documentation
5. **Spread the Word**: Star ⭐ and share the project

## 🙏 Acknowledgments

### Special Thanks
- To all users who requested the drag-and-drop feature! 🎉
- To the Flask and PyMuPDF communities for excellent tools
- To everyone who starred and shared the project

### Built With
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [PyMuPDF](https://pymupdf.readthedocs.io/) - PDF manipulation
- [pdfplumber](https://github.com/jsvine/pdfplumber) - Text extraction
- [Pillow](https://python-pillow.org/) - Image processing
- [pytesseract](https://github.com/madmaze/pytesseract) - OCR

## 📞 Support & Contact

### Need Help?
- 📋 **Issues**: [GitHub Issues](https://github.com/oscar2song/pdfforge/issues)
- 📧 **Email**: oscar2song@gmail.com
- 💬 **Discussions**: [GitHub Discussions](https://github.com/oscar2song/pdfforge/discussions)

### Found a Bug?
Please report it with:
- Steps to reproduce
- Expected behavior
- Actual behavior
- Screenshots (if applicable)
- System information (OS, Python version)

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/oscar2song/pdfforge/blob/main/LICENSE) file for details.

## 🌟 Show Your Support

If you find PDFForge useful, please:
- ⭐ Star the repository
- 🐛 Report bugs
- 💡 Suggest features
- 📢 Share with others
- 🤝 Contribute code

---

**Full Changelog**: [v1.0.0...v1.1.0](https://github.com/oscar2song/pdfforge/compare/v1.0.0...v1.1.0)

**Download**: [Source code (zip)](https://github.com/oscar2song/pdfforge/archive/refs/tags/v1.1.0.zip) | [Source code (tar.gz)](https://github.com/oscar2song/pdfforge/archive/refs/tags/v1.1.0.tar.gz)

---

Made with ❤️ by the PDFForge Team

*Released on: October 29, 2024*
