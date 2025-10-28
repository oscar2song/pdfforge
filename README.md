# 🔨 PDFForge - Professional PDF Tools

A powerful, user-friendly web application for PDF manipulation built with Flask and PyMuPDF. Merge, normalize, and compress your PDFs with professional features like custom headers, batch processing, and smart page detection.

[![Python Version](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.1.2-green.svg)](https://flask.palletsprojects.com/)
[![PyMuPDF](https://img.shields.io/badge/PyMuPDF-1.26.5-orange.svg)](https://pymupdf.readthedocs.io/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## ✨ Features

### 📑 PDF Merge
- **Simple Merge Mode**: Fast merging without modifications
- **Header Mode**: Add professional two-line headers to each page
- **Smart Spacing Detection**: Automatically adjusts for existing headers
- **Custom Page Numbers**: Start numbering from any number (default: 1)
- **Custom Output Filename**: Name your merged file or auto-generate from first file
- **Empty Header Support**: Leave headers empty to merge as-is

### 📋 PDF Normalize
- **Standard Page Sizes**: Convert to Letter, Legal, A4, A3, A5 (portrait/landscape)
- **OCR Support**: Add searchable text layer to scanned documents
- **Batch Processing**: Normalize multiple PDFs at once
- **ZIP Download**: Get all normalized files in one convenient archive
- **Filename Preservation**: Each file keeps its original name with `_normalized` suffix

### 🗜️ PDF Compress
- **Smart Compression**: Automatically detects best compression method
- **Image Optimization**: Downsamples large images intelligently
- **Batch Processing**: Compress multiple files simultaneously
- **Safe Compression**: Never increases file size
- **Size Reporting**: See before/after sizes and compression ratio

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12 (recommended) or Python 3.11
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/pdfforge.git
   cd pdfforge
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   
   # Windows
   .venv\Scripts\activate
   
   # macOS/Linux
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open your browser**
   ```
   http://localhost:5000
   ```

---

## 📦 Requirements

```txt
Flask==3.1.2
pdfplumber==0.11.7
pillow==12.0.0
PyMuPDF==1.26.5
pytesseract==0.3.13
Werkzeug==3.1.3
```

### Optional: Tesseract OCR
For OCR functionality, install Tesseract-OCR:
- **Windows**: [Download installer](https://github.com/UB-Mannheim/tesseract/wiki)
- **macOS**: `brew install tesseract`
- **Linux**: `sudo apt-get install tesseract-ocr`

---

## 📖 Usage Guide

### PDF Merge

#### Simple Merge
1. Navigate to **PDF Merge** from the homepage
2. Upload 2 or more PDF files
3. (Optional) Set custom output filename
4. (Optional) Set starting page number
5. Click **Merge PDFs**

**Example**: Merge `report1.pdf` and `report2.pdf` → Get `report1_merged.pdf`

#### Merge with Headers
1. Navigate to **PDF Merge**
2. Upload PDF files
3. Select **"Add Headers (Two Lines)"** mode
4. Enter header text for each file (or leave empty)
5. (Optional) Customize settings
6. Click **Merge PDFs**

**Example Headers**:
- Line 1: `Project Report - Confidential`
- Line 2: `Internal Use Only - 2024`

### PDF Normalize

#### Single File
1. Navigate to **PDF Normalize**
2. Upload a PDF file
3. Select target page size (default: Letter)
4. Click **Normalize PDF**

**Output**: `document_normalized.pdf`

#### Batch Processing
1. Navigate to **PDF Normalize**
2. Upload multiple PDF files
3. Select target page size
4. Click **Normalize X PDFs**

**Output**: `normalized_pdfs_[timestamp].zip` containing all normalized files

### PDF Compress

#### Single File
1. Navigate to **PDF Compress**
2. Upload a PDF file
3. (Optional) Adjust compression settings
4. Click **Compress PDF**

**Example**: `invoice.pdf` (4.2 MB) → `invoice_compressed.pdf` (1.1 MB)

#### Batch Processing
1. Upload multiple files
2. Click **Compress X PDFs**
3. Download ZIP with all compressed files

---

## ⚙️ Configuration

### Change Server Port
Edit `app.py`, line ~1160:
```python
app.run(debug=True, host='0.0.0.0', port=5000)  # Change port here
```

### Adjust Upload Limits
Edit `app.py`, line ~20:
```python
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB
```

### Compression Settings
Modify compression options in `app.py`:
```python
options = {
    'max_image_size': (1920, 1920),  # Max image dimensions
    'jpeg_quality': 85,               # JPEG quality (0-100)
    'aggressive': False               # Aggressive compression
}
```

---

## 📁 Project Structure

```
pdfforge/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── templates/                  # HTML templates
│   ├── index.html             # Homepage
│   ├── merge.html             # Merge tool page
│   ├── normalize.html         # Normalize tool page
│   └── compress.html          # Compress tool page
└── .venv/                     # Virtual environment (not in repo)
```

---

## 🎯 Advanced Features

### Merge Options Explained

| Option | Description | Default |
|--------|-------------|---------|
| **Mode** | Simple or Headers | Simple |
| **Page Start** | Starting page number | 1 |
| **Output Filename** | Custom output name | First file's name + `_merged` |
| **Smart Spacing** | Auto-adjust for headers | Enabled |
| **Footer Line** | Add footer separator | Disabled |

### Normalize Options

| Option | Description |
|--------|-------------|
| **Letter** | 8.5" × 11" (612 × 792 pt) |
| **Legal** | 8.5" × 14" (612 × 1008 pt) |
| **A4** | 210 × 297 mm (595 × 842 pt) |
| **A3** | 297 × 420 mm (842 × 1191 pt) |
| **A5** | 148 × 210 mm (420 × 595 pt) |
| **OCR** | Add searchable text layer |

### Compress Options

| Setting | Description | Impact |
|---------|-------------|--------|
| **Standard** | Balanced compression | Moderate reduction |
| **Aggressive** | Maximum compression | Larger reduction, may affect quality |
| **Max Image Size** | Downscale large images | Configurable (default: 1920×1920) |

---

## 🔧 Troubleshooting

### Common Issues

#### "No module named 'fitz'"
**Solution**: Reinstall PyMuPDF
```bash
pip install PyMuPDF --force-reinstall
```

#### "Address already in use" (Port 5000)
**Solution**: Change port or kill existing process
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID [PID] /F

# macOS/Linux
lsof -ti:5000 | xargs kill -9
```

#### OCR not working
**Solution**: Install Tesseract-OCR on your system
- Windows: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
- Update path in app.py if needed:
  ```python
  pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
  ```

#### Python 3.13 Installation Issues
**Solution**: Use Python 3.12 instead
```bash
# Download Python 3.12 from python.org
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

---

## 🐛 Known Limitations

- **Max File Size**: 500MB per file (configurable)
- **OCR**: Requires Tesseract-OCR installed separately
- **Header Mode**: Scales pages to Letter size (8.5" × 11")
- **Python 3.13**: Limited package support (use 3.12 recommended)

---

## 🗺️ Roadmap

### Planned Features
- [ ] **PDF Split**: Extract pages or split into multiple files
- [ ] **PDF Watermark**: Add text/image watermarks
- [ ] **PDF to Image**: Convert pages to PNG/JPG
- [ ] **Password Protection**: Encrypt PDFs with passwords
- [ ] **Digital Signatures**: Sign PDFs digitally
- [ ] **Form Filling**: Fill PDF forms programmatically
- [ ] **Bookmark Management**: Add/edit PDF bookmarks
- [ ] **Page Rotation**: Rotate individual pages

### Future Improvements
- [ ] Docker support
- [ ] REST API
- [ ] Batch queue system
- [ ] Cloud storage integration (S3, Drive)
- [ ] User authentication
- [ ] Processing history
- [ ] Custom templates for headers
- [ ] Dark mode UI

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Commit your changes**
   ```bash
   git commit -m 'Add amazing feature'
   ```
4. **Push to the branch**
   ```bash
   git push origin feature/amazing-feature
   ```
5. **Open a Pull Request**

### Development Setup
```bash
# Clone your fork
git clone https://github.com/yourusername/pdfforge.git
cd pdfforge

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Run in debug mode
python app.py
```

### Code Style
- Follow PEP 8 guidelines
- Use meaningful variable names
- Add comments for complex logic
- Update README for new features

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 PDFForge

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🙏 Acknowledgments

### Built With
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [PyMuPDF](https://pymupdf.readthedocs.io/) - PDF manipulation
- [pdfplumber](https://github.com/jsvine/pdfplumber) - PDF text extraction
- [Pillow](https://python-pillow.org/) - Image processing
- [pytesseract](https://github.com/madmaze/pytesseract) - OCR wrapper
- [Werkzeug](https://werkzeug.palletsprojects.com/) - WSGI utilities

### Inspired By
- Adobe Acrobat
- Smallpdf
- PDFtk

### Special Thanks
- MuPDF team for the excellent PDF library
- Flask community for the robust web framework
- All contributors and users

---

## 📧 Contact

- **GitHub Issues**: [Report a bug](https://github.com/yourusername/pdfforge/issues)
- **Email**: oscar2song@gmail.com
- **Website**: https://your-website.com

---

## 📊 Stats

- **Current Version**: 1.0.0 
- **Total Features**: 3 main tools, 15+ options
- **Lines of Code**: ~1,300
- **Python Version**: 3.12+
- **Active Development**: Yes ✅

---

## 📈 Version History

### Version 1.0.0 (2024-10-01) - INITIAL RELEASE
- 🎉 Initial release
- ✨ PDF Merge with headers
- ✨ PDF Normalize with OCR
- ✨ PDF Compress with smart compression
- 🌐 Web interface
- 📱 Responsive design

---

<div align="center">

Made with ❤️ by the PDFForge Team

⭐ Star this repo if you find it useful! ⭐

[Report Bug](https://github.com/yourusername/pdfforge/issues) · 
[Request Feature](https://github.com/yourusername/pdfforge/issues) · 
[Documentation](https://github.com/yourusername/pdfforge/wiki)

</div>
