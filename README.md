# 🔨 PDFForge

**Professional PDF Tools - Merge, Normalize, and Compress PDFs with Batch Processing**

[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.1.2-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A powerful, user-friendly web application for PDF manipulation built with Flask and PyMuPDF. Features a modular architecture with clean separation of concerns, comprehensive testing, and professional-grade PDF processing capabilities.

## ✨ Features

### 📑 PDF Merge
- **Simple Merge Mode**: Fast merging without modifications
- **Header Mode**: Add professional two-line headers to each page
- **Smart Spacing Detection**: Automatically adjusts for existing headers
- **Custom Page Numbers**: Start numbering from any number (default: 1)
- **Custom Output Filename**: Name your merged file or auto-generate from first file
- **Empty Header Support**: Leave headers empty to merge as-is

### 📏 PDF Normalize
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

## 🏗️ Architecture

PDFForge v2.0 features a **modular, maintainable architecture** with clean separation of concerns:

```
pdfforge/
├── app.py                  # Application entry point (~50 lines)
├── config.py               # Configuration management
├── requirements.txt        # Python dependencies
│
├── pdfforge/              # Main application package
│   ├── core/              # Core PDF processing logic
│   │   ├── merge.py       # PDF merging
│   │   ├── normalize.py   # PDF normalization
│   │   └── compress.py    # PDF compression
│   │
│   ├── services/          # Business logic layer
│   ├── routes/            # Flask blueprints/routes
│   ├── models/            # Data models
│   ├── utils/             # Utility functions
│   ├── exceptions/        # Custom exceptions
│   ├── templates/         # HTML templates
│   ├── static/            # CSS, JS, images
│   └── fonts/             # Custom fonts
│
├── tests/                 # Comprehensive test suite
├── scripts/               # Utility scripts
└── docs/                  # Additional documentation
```

**Key Improvements from v1.0:**
- 🎯 **Modular Design**: Clean separation of concerns (was 1800+ lines in single file)
- 🧪 **Testable**: Comprehensive unit and integration tests
- 📚 **Maintainable**: Each component has a single responsibility
- 🚀 **Scalable**: Easy to add new features and functionality
- 🔧 **Configurable**: Environment-based configuration management

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed architecture documentation.

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** (Python 3.12 recommended)
- **pip** (Python package manager)
- **Tesseract-OCR** (optional, for OCR functionality)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/oscar2song/pdfforge.git
cd pdfforge
```

2. **Create and activate virtual environment**
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment (optional)**
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
# Defaults work fine for most users
```

5. **Run the application**
```bash
python app.py
```

6. **Open your browser**
```
http://localhost:5000
```

### OCR Setup (Optional)

For OCR functionality, install Tesseract-OCR:

**Windows:**
- Download installer from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
- Update path in `.env` if needed:
  ```
  TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
  ```

**macOS:**
```bash
brew install tesseract
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

## 📖 Usage Guide

### PDF Merge

#### Simple Merge
1. Navigate to **PDF Merge** from the homepage
2. Upload 2 or more PDF files
3. (Optional) Set custom output filename
4. Click **Merge PDFs**

**Example:** Merge `report1.pdf` and `report2.pdf` → Get `report1_merged.pdf`

#### Merge with Headers
1. Navigate to **PDF Merge**
2. Upload PDF files
3. Select **"Add Headers (Two Lines)"** mode
4. Enter header text for each file (or leave empty)
5. (Optional) Customize settings
6. Click **Merge PDFs**

**Example Headers:**
- Line 1: `Project Report - Confidential`
- Line 2: `Internal Use Only - 2024`

### PDF Normalize

#### Single File
1. Navigate to **PDF Normalize**
2. Upload a PDF file
3. Select target page size (default: Letter)
4. Click **Normalize PDF**

**Output:** `document_normalized.pdf`

#### Batch Processing
1. Navigate to **PDF Normalize**
2. Upload multiple PDF files
3. Select target page size
4. Click **Normalize X PDFs**

**Output:** `normalized_pdfs_[timestamp].zip` containing all normalized files

### PDF Compress

#### Single File
1. Navigate to **PDF Compress**
2. Upload a PDF file
3. (Optional) Adjust compression settings
4. Click **Compress PDF**

**Example:** `invoice.pdf` (4.2 MB) → `invoice_compressed.pdf` (1.1 MB)

#### Batch Processing
1. Upload multiple files
2. Click **Compress X PDFs**
3. Download ZIP with all compressed files

## ⚙️ Configuration

### Application Settings

Edit `config.py` or set environment variables in `.env`:

```python
# Server Configuration
HOST = '0.0.0.0'
PORT = 5000
DEBUG = True

# Upload Settings
MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB
ALLOWED_EXTENSIONS = {'pdf'}

# Processing Settings
UPLOAD_FOLDER = 'uploads'
DOWNLOAD_FOLDER = 'downloads'
TEMP_FOLDER = 'temp'

# OCR Settings (optional)
TESSERACT_CMD = '/usr/bin/tesseract'  # Adjust for your system
```

### Compression Options

Modify compression settings in your code or via the API:

```python
options = {
    'max_image_size': (1920, 1920),  # Max image dimensions
    'jpeg_quality': 85,               # JPEG quality (0-100)
    'aggressive': False               # Aggressive compression
}
```

## 🧪 Development

### Running Tests

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=pdfforge --cov-report=html

# Run specific test file
pytest tests/test_merge.py

# Run specific test
pytest tests/test_merge.py::TestPDFMerger::test_merge_two_pdfs
```

### Code Quality

```bash
# Format code
black pdfforge/

# Sort imports
isort pdfforge/

# Lint code
flake8 pdfforge/
pylint pdfforge/

# Type checking
mypy pdfforge/
```

### Project Structure

See [DEVELOPMENT.md](docs/DEVELOPMENT.md) for detailed development guidelines.

## 📊 Technical Specifications

### Dependencies

```
Flask==3.1.2              # Web framework
PyMuPDF==1.26.5          # PDF manipulation
pdfplumber==0.11.7       # PDF text extraction
Pillow==12.0.0           # Image processing
pytesseract==0.3.13      # OCR wrapper
Werkzeug==3.1.3          # WSGI utilities
python-dotenv==1.0.0     # Environment management
```

### Page Size Reference

| Size | Dimensions | Points (Width × Height) |
|------|------------|------------------------|
| Letter | 8.5" × 11" | 612 × 792 pt |
| Legal | 8.5" × 14" | 612 × 1008 pt |
| A4 | 210 × 297 mm | 595 × 842 pt |
| A3 | 297 × 420 mm | 842 × 1191 pt |
| A5 | 148 × 210 mm | 420 × 595 pt |

### Processing Options

| Feature | Options | Default |
|---------|---------|---------|
| Merge Mode | Simple, Headers | Simple |
| Page Start | 1+ | 1 |
| Smart Spacing | On/Off | On |
| OCR | On/Off | Off |
| Compression | Standard, Aggressive | Standard |

## 🔧 Troubleshooting

### Common Issues

**Issue: "Module not found" error**
```bash
# Solution: Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**Issue: Port already in use**
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID [PID] /F

# macOS/Linux
lsof -ti:5000 | xargs kill -9
```

**Issue: OCR not working**
- Install Tesseract-OCR on your system
- Update `TESSERACT_CMD` in `.env` with correct path

**Issue: Python version compatibility**
- Use Python 3.12 (recommended)
- Python 3.11+ is required
- Python 3.13 has limited package support

## 🎯 Roadmap

### Planned Features

- [ ] **PDF Split**: Extract pages or split into multiple files
- [ ] **PDF Watermark**: Add text/image watermarks
- [ ] **PDF to Image**: Convert pages to PNG/JPG
- [ ] **Password Protection**: Encrypt PDFs with passwords
- [ ] **Digital Signatures**: Sign PDFs digitally
- [ ] **Form Filling**: Fill PDF forms programmatically
- [ ] **Bookmark Management**: Add/edit PDF bookmarks
- [ ] **Page Rotation**: Rotate individual pages

### Infrastructure Improvements

- [ ] Docker support
- [ ] REST API with OpenAPI documentation
- [ ] Batch queue system with job tracking
- [ ] Cloud storage integration (S3, Google Drive)
- [ ] User authentication and authorization
- [ ] Processing history and analytics
- [ ] Custom templates for headers
- [ ] Dark mode UI

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
   - Follow code style guidelines
   - Add tests for new features
   - Update documentation
4. **Commit your changes**
   ```bash
   git commit -m 'Add amazing feature'
   ```
5. **Push to the branch**
   ```bash
   git push origin feature/amazing-feature
   ```
6. **Open a Pull Request**

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for detailed contribution guidelines.

### Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/pdfforge.git
cd pdfforge

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Start development server
python app.py
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 PDFForge

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

## 🙏 Acknowledgments

- **[Flask](https://flask.palletsprojects.com/)** - Web framework
- **[PyMuPDF](https://pymupdf.readthedocs.io/)** - PDF manipulation
- **[pdfplumber](https://github.com/jsvine/pdfplumber)** - PDF text extraction
- **[Pillow](https://python-pillow.org/)** - Image processing
- **[pytesseract](https://github.com/madmaze/pytesseract)** - OCR wrapper
- **[Werkzeug](https://werkzeug.palletsprojects.com/)** - WSGI utilities

Special thanks to all contributors and users of PDFForge!

## 📞 Support & Contact

- **GitHub Issues**: [Report a bug](https://github.com/oscar2song/pdfforge/issues)
- **Email**: [oscar2song@gmail.com](mailto:oscar2song@gmail.com)
- **Documentation**: [docs/](docs/)

## 📈 Project Stats

- **Current Version**: 2.0.0
- **Total Features**: 3 main tools, 15+ options
- **Architecture**: Modular (from 1800+ line monolith)
- **Python Version**: 3.11+
- **Test Coverage**: 80%+
- **Active Development**: ✅ Yes


## 📝 Changelog

### v2.1 (Planned)
- Enhance TOC
- PDF split
- REST API endpoints
- API key authentication
- Rate limiting
- Batch operations

### Version 2.0.0 (Current - November 2025)
- 🏗️ **Major Restructure**: Modular architecture with clean separation of concerns
- 📦 **Package Structure**: Organized into core, services, routes, models, utils
- 🧪 **Testing**: Comprehensive test suite with 80%+ coverage
- 📚 **Documentation**: Complete documentation overhaul
- ⚡ **Performance**: Improved processing speed and memory usage
- 🔧 **Configuration**: Environment-based configuration management
- 🎨 **Frontend**: Extracted CSS/JS to separate files
- 🔒 **Security**: Enhanced input validation and error handling

### Version 1.0.0 (October 2025)
- 🎉 Initial release
- ✨ PDF Merge with headers
- ✨ PDF Normalize with OCR
- ✨ PDF Compress with smart compression
- 🌐 Web interface
- 📱 Responsive design

---

**Made with ❤️ by the PDFForge Team**

⭐ **Star this repo if you find it useful!** ⭐
