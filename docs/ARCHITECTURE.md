# 🏗️ PDFForge Architecture Documentation

## Overview

PDFForge v2.0 features a **modular, layered architecture** designed for maintainability, testability, and scalability. This document explains the architectural decisions, design patterns, and component relationships.

## 📊 Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                     Presentation Layer                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  Templates  │  │   Static    │  │    Routes   │     │
│  │   (HTML)    │  │  (CSS/JS)   │  │ (Blueprints)│     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                      Service Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │    Merge     │  │  Normalize   │  │   Compress   │  │
│  │   Service    │  │   Service    │  │   Service    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                       Core Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   PDFMerger  │  │PDFNormalizer │  │PDFCompressor │  │
│  │    (Core)    │  │    (Core)    │  │    (Core)    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                      Utility Layer                       │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │
│  │   PDF   │  │   OCR   │  │  Image  │  │  File   │   │
│  │  Utils  │  │  Utils  │  │  Utils  │  │  Utils  │   │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘   │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                    Foundation Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │    Models    │  │  Exceptions  │  │    Config    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## 🎯 Design Principles

### 1. Separation of Concerns
Each layer has a specific responsibility:
- **Routes**: Handle HTTP requests/responses
- **Services**: Business logic and orchestration
- **Core**: PDF processing algorithms
- **Utils**: Reusable helper functions
- **Models**: Data structures and validation

### 2. Single Responsibility Principle
Each module/class has one reason to change:
- `merge.py`: Only handles PDF merging logic
- `normalize.py`: Only handles PDF normalization
- `compress.py`: Only handles PDF compression

### 3. Dependency Injection
Services receive their dependencies via constructor injection:
```python
class MergeService:
    def __init__(self, merger: PDFMerger, validator: FileValidator):
        self.merger = merger
        self.validator = validator
```

### 4. Open/Closed Principle
Code is open for extension but closed for modification:
- New PDF operations can be added without modifying existing code
- New compression strategies can be added via strategy pattern

### 5. Interface Segregation
Clients depend only on interfaces they use:
- Merge operations don't depend on compression logic
- Normalization is independent of OCR if not needed

## 📁 Directory Structure

```
pdfforge/
├── app.py                      # Application entry point
├── config.py                   # Configuration management
├── requirements.txt            # Python dependencies
├── requirements-dev.txt        # Development dependencies
├── .env.example               # Environment template
├── .gitignore                 # Git ignore rules
│
├── pdfforge/                  # Main application package
│   ├── __init__.py           # Package initialization
│   ├── create_app.py         # Flask app factory
│   │
│   ├── core/                  # Core PDF processing
│   │   ├── __init__.py
│   │   ├── merge.py          # PDFMerger class
│   │   ├── normalize.py      # PDFNormalizer class
│   │   └── compress.py       # PDFCompressor class
│   │
│   ├── services/              # Business logic
│   │   ├── __init__.py
│   │   ├── merge_service.py
│   │   ├── normalize_service.py
│   │   ├── compress_service.py
│   │   └── batch_service.py
│   │
│   ├── routes/                # Flask blueprints
│   │   ├── __init__.py
│   │   ├── main.py           # Homepage routes
│   │   ├── merge.py          # Merge endpoints
│   │   ├── normalize.py      # Normalize endpoints
│   │   └── compress.py       # Compress endpoints
│   │
│   ├── models/                # Data models
│   │   ├── __init__.py
│   │   ├── pdf_file.py       # PDFFile model
│   │   ├── merge_options.py  # MergeOptions model
│   │   ├── normalize_options.py
│   │   └── compress_options.py
│   │
│   ├── utils/                 # Utilities
│   │   ├── __init__.py
│   │   ├── pdf_utils.py      # PDF helpers
│   │   ├── ocr_utils.py      # OCR utilities
│   │   ├── image_utils.py    # Image processing
│   │   ├── file_utils.py     # File operations
│   │   └── validation.py     # Input validation
│   │
│   ├── exceptions/            # Custom exceptions
│   │   ├── __init__.py
│   │   ├── pdf_exceptions.py
│   │   └── validation_exceptions.py
│   │
│   ├── templates/             # Jinja2 templates
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── merge.html
│   │   ├── normalize.html
│   │   └── compress.html
│   │
│   ├── static/                # Static assets
│   │   ├── css/
│   │   │   ├── main.css
│   │   │   └── components.css
│   │   ├── js/
│   │   │   ├── main.js
│   │   │   ├── merge.js
│   │   │   ├── normalize.js
│   │   │   └── compress.js
│   │   └── images/
│   │       └── favicon.ico
│   │
│   └── fonts/                 # Custom fonts
│       ├── OpenSans/
│       └── Roboto/
│
├── tests/                     # Test suite
│   ├── __init__.py
│   ├── conftest.py           # Pytest fixtures
│   ├── test_merge.py
│   ├── test_normalize.py
│   ├── test_compress.py
│   ├── test_services.py
│   ├── test_utils.py
│   └── fixtures/             # Test files
│       ├── sample1.pdf
│       └── sample2.pdf
│
├── scripts/                   # Utility scripts
│   ├── setup_dev.sh
│   └── run_tests.sh
│
├── docs/                      # Documentation
│   ├── ARCHITECTURE.md       # This file
│   ├── DEVELOPMENT.md        # Dev guide
│   ├── API.md               # API docs
│   ├── DEPLOYMENT.md        # Deployment guide
│   └── CONTRIBUTING.md      # Contribution guide
│
├── downloads/                 # Output files
│   ├── merge/
│   ├── normalize/
│   └── compress/
│
├── uploads/                   # Temporary uploads
├── temp/                      # Temporary processing
└── logs/                      # Application logs
```

## 🔄 Request Flow

### Example: PDF Merge Request

```
1. User submits form
   ↓
2. Route Handler (routes/merge.py)
   - Validates request
   - Extracts form data
   ↓
3. Service Layer (services/merge_service.py)
   - Validates business rules
   - Coordinates operations
   ↓
4. Core Layer (core/merge.py)
   - Performs PDF operations
   - Uses utilities for helpers
   ↓
5. Utility Layer (utils/pdf_utils.py)
   - PDF detection
   - Header spacing
   - Page manipulation
   ↓
6. Service Layer
   - Saves output file
   - Cleans up temp files
   ↓
7. Route Handler
   - Generates response
   - Returns file to user
```

## 🧩 Layer Details

### 1. Presentation Layer (routes/ + templates/)

**Responsibilities:**
- Handle HTTP requests/responses
- Validate user input
- Render templates
- Return files/JSON

**Example: Merge Route**
```python
@merge_bp.route('/merge', methods=['POST'])
def merge_pdfs():
    # Validate request
    if not request.files:
        return jsonify({'error': 'No files uploaded'}), 400
    
    # Extract data
    files = request.files.getlist('files')
    options = extract_merge_options(request.form)
    
    # Call service
    service = MergeService()
    result = service.merge_pdfs(files, options)
    
    # Return response
    return send_file(result.path, as_attachment=True)
```

### 2. Service Layer (services/)

**Responsibilities:**
- Business logic orchestration
- Transaction management
- File management
- Error handling
- Logging

**Example: Merge Service**
```python
class MergeService:
    def __init__(self):
        self.merger = PDFMerger()
        self.validator = FileValidator()
    
    def merge_pdfs(self, files: List[FileStorage], 
                   options: MergeOptions) -> MergeResult:
        # Validate files
        self.validator.validate_files(files)
        
        # Save uploaded files
        pdf_files = self._save_uploads(files)
        
        try:
            # Perform merge
            output_pdf = self.merger.merge(pdf_files, options)
            
            # Save output
            output_path = self._save_output(output_pdf, options.output_name)
            
            return MergeResult(
                success=True,
                path=output_path,
                page_count=len(output_pdf)
            )
        finally:
            # Cleanup
            self._cleanup_temp_files(pdf_files)
```

### 3. Core Layer (core/)

**Responsibilities:**
- Pure PDF processing logic
- Algorithm implementation
- No file I/O (receives file paths/objects)
- No HTTP concerns

**Example: PDF Merger**
```python
class PDFMerger:
    def merge(self, files: List[PDFFile], 
             options: MergeOptions) -> fitz.Document:
        output_pdf = fitz.open()
        current_page = options.page_start
        
        for pdf_file in files:
            if options.add_headers:
                current_page = self._merge_with_headers(
                    output_pdf, pdf_file, current_page
                )
            else:
                self._merge_simple(output_pdf, pdf_file)
        
        return output_pdf
    
    def _merge_with_headers(self, output_pdf, pdf_file, page_num):
        # Header processing logic
        pass
    
    def _merge_simple(self, output_pdf, pdf_file):
        # Simple merge logic
        pass
```

### 4. Utility Layer (utils/)

**Responsibilities:**
- Reusable helper functions
- PDF utilities (detection, manipulation)
- OCR operations
- Image processing
- File operations
- Validation

**Example: PDF Utils**
```python
def detect_pdf_type(page: fitz.Page) -> str:
    """Detect if page is scanned or digital."""
    text = page.get_text()
    image_count = len(page.get_images())
    
    if len(text.strip()) < 50 and image_count > 0:
        return 'scanned'
    return 'digital'

def has_content_in_header_area(page: fitz.Page, 
                               threshold: int = 100) -> bool:
    """Check if page has content in header area."""
    text_instances = page.get_text("blocks")
    
    for block in text_instances:
        if block[1] < threshold:  # y-coordinate < threshold
            return True
    
    return False
```

### 5. Foundation Layer (models/ + exceptions/)

**Responsibilities:**
- Data structures
- Validation rules
- Custom exceptions
- Type definitions

**Example: Models**
```python
@dataclass
class MergeOptions:
    """Options for PDF merge operation."""
    add_headers: bool = False
    page_start: int = 1
    output_name: Optional[str] = None
    smart_spacing: bool = True
    
    def validate(self) -> None:
        """Validate merge options."""
        if self.page_start < 1:
            raise ValueError("Page start must be >= 1")
        
        if self.output_name and not self.output_name.endswith('.pdf'):
            self.output_name += '.pdf'
```

**Example: Exceptions**
```python
class PDFProcessingError(Exception):
    """Base exception for PDF processing errors."""
    pass

class PDFMergeError(PDFProcessingError):
    """Error during PDF merge operation."""
    pass

class PDFValidationError(PDFProcessingError):
    """Invalid PDF file or parameters."""
    pass
```

## 🔌 Flask Application Factory

The application uses the **Application Factory Pattern** for better testability and configuration management:

```python
def create_app(config_class=Config):
    """Create and configure Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    # ...
    
    # Register blueprints
    from pdfforge.routes import main_bp, merge_bp, normalize_bp, compress_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(merge_bp, url_prefix='/merge')
    app.register_blueprint(normalize_bp, url_prefix='/normalize')
    app.register_blueprint(compress_bp, url_prefix='/compress')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('500.html'), 500
    
    return app
```

## 📝 Configuration Management

Configuration uses environment-based settings:

```python
class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB
    UPLOAD_FOLDER = 'uploads'
    DOWNLOAD_FOLDER = 'downloads'

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    # Override with production settings

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    WTF_CSRF_ENABLED = False
```

## 🧪 Testing Strategy

### Test Layers

1. **Unit Tests**: Test individual components in isolation
   - Core processing logic
   - Utility functions
   - Model validation

2. **Integration Tests**: Test component interactions
   - Service layer operations
   - Route handlers with services

3. **End-to-End Tests**: Test complete workflows
   - Full merge operation
   - Batch processing
   - Error scenarios

### Test Structure

```python
# tests/test_merge.py
class TestPDFMerger:
    """Unit tests for PDFMerger core class."""
    
    def test_merge_two_pdfs(self, sample_pdfs):
        merger = PDFMerger()
        result = merger.merge(sample_pdfs)
        assert len(result) == 2
    
    def test_merge_with_headers(self, sample_pdfs):
        options = MergeOptions(add_headers=True)
        merger = PDFMerger(options)
        result = merger.merge(sample_pdfs)
        # Verify headers added
        assert result is not None

class TestMergeService:
    """Integration tests for merge service."""
    
    def test_merge_service_workflow(self, app, temp_files):
        service = MergeService()
        result = service.merge_pdfs(temp_files, MergeOptions())
        assert result.success
        assert os.path.exists(result.path)

def test_merge_route(client, sample_pdf):
    """End-to-end test for merge route."""
    response = client.post('/merge', data={
        'files': [sample_pdf, sample_pdf],
        'mode': 'simple'
    })
    assert response.status_code == 200
```

## 🔒 Security Considerations

### Input Validation
- File type validation (PDF only)
- File size limits (500MB default)
- Filename sanitization
- Parameter validation

### File Handling
- Secure temporary file creation
- Automatic cleanup of temp files
- Isolated processing directories
- No execution of embedded content

### Error Handling
- No sensitive information in error messages
- Proper exception handling
- Logging without exposing internals

## 🚀 Performance Optimization

### Strategies
1. **Lazy Loading**: Load PDF pages only when needed
2. **Streaming**: Stream large files instead of loading into memory
3. **Caching**: Cache frequently accessed data
4. **Batch Processing**: Process multiple files efficiently
5. **Compression**: Smart image downsampling

### Resource Management
- Automatic cleanup of resources
- Memory-efficient processing
- Connection pooling (if using databases)
- File descriptor management

## 📊 Monitoring & Logging

### Logging Levels
- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error messages for failures
- **CRITICAL**: Critical issues requiring attention

### Logging Example
```python
import logging

logger = logging.getLogger(__name__)

class MergeService:
    def merge_pdfs(self, files, options):
        logger.info(f"Starting merge of {len(files)} files")
        
        try:
            result = self._perform_merge(files, options)
            logger.info(f"Merge successful: {result.path}")
            return result
        except Exception as e:
            logger.error(f"Merge failed: {str(e)}", exc_info=True)
            raise
```

## 🔄 Migration from v1.0

### Changes Summary
- **Before**: 1800+ lines in single `app.py` file
- **After**: Modular structure with ~50 line entry point

### Migration Benefits
- ✅ **80% reduction** in single-file complexity
- ✅ **Improved testability** with unit tests
- ✅ **Better maintainability** with separation of concerns
- ✅ **Easier collaboration** with clear module boundaries
- ✅ **Future-proof** architecture for scaling

## 📚 Further Reading

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [12-Factor App](https://12factor.net/)
- [Python Project Structure](https://docs.python-guide.org/writing/structure/)

## 📞 Questions?

For architecture-related questions:
- Open an issue on GitHub
- Email: oscar2song@gmail.com
- Review the code examples in the repository

---

**Last Updated**: November 2025 
**Version**: 2.0.0  
**Author**: PDFForge Team
