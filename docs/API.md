# 🔌 PDFForge API Documentation

## Overview

PDFForge provides both a web interface and a programmatic API for PDF manipulation. This document describes how to interact with PDFForge programmatically.

> **Note**: REST API endpoints are planned for v2.1. Currently, PDFForge is primarily a web application with internal Python API.

## 📋 Table of Contents

- [Python API (Current)](#python-api-current)
- [REST API (Planned)](#rest-api-planned)
- [Authentication](#authentication)
- [Rate Limiting](#rate-limiting)
- [Error Handling](#error-handling)
- [Examples](#examples)

## 🐍 Python API (Current)

### Core APIs

#### PDF Merge

```python
from pdfforge.core.merge import PDFMerger
from pdfforge.models.merge_options import MergeOptions
from pdfforge.models.pdf_file import PDFFile

# Create merger instance
merger = PDFMerger()

# Prepare PDF files
files = [
    PDFFile(
        path="document1.pdf",
        name="Document 1",
        header_line1="Confidential",
        header_line2="Internal Use Only"
    ),
    PDFFile(
        path="document2.pdf",
        name="Document 2"
    )
]

# Configure options
options = MergeOptions(
    add_headers=True,
    page_start=1,
    smart_spacing=True,
    output_name="merged.pdf"
)

# Perform merge
result = merger.merge(files, options)

# Save result
result.save("output/merged.pdf")
result.close()
```

#### PDF Normalize

```python
from pdfforge.core.normalize import PDFNormalizer
from pdfforge.models.normalize_options import NormalizeOptions

# Create normalizer instance
normalizer = PDFNormalizer()

# Configure options
options = NormalizeOptions(
    page_size="letter",  # letter, legal, a4, a3, a5
    orientation="portrait",  # portrait, landscape
    ocr=False,
    preserve_annotations=True
)

# Perform normalization
result = normalizer.normalize("input.pdf", options)

# Save result
result.save("output/normalized.pdf")
```

#### PDF Compress

```python
from pdfforge.core.compress import PDFCompressor
from pdfforge.models.compress_options import CompressOptions

# Create compressor instance
compressor = PDFCompressor()

# Configure options
options = CompressOptions(
    max_image_size=(1920, 1920),
    jpeg_quality=85,
    aggressive=False
)

# Perform compression
result = compressor.compress("input.pdf", options)

# Get compression stats
print(f"Original size: {result.original_size} bytes")
print(f"Compressed size: {result.compressed_size} bytes")
print(f"Compression ratio: {result.ratio:.2%}")

# Save result
result.save("output/compressed.pdf")
```

### Service APIs

Higher-level APIs with additional features:

```python
from pdfforge.services.merge_service import MergeService
from werkzeug.datastructures import FileStorage

# Create service instance
service = MergeService()

# Prepare files (from Flask upload)
files = request.files.getlist('files')

# Or create FileStorage objects
with open('file1.pdf', 'rb') as f1:
    file1 = FileStorage(f1, filename='file1.pdf')
    files = [file1]

# Merge with service (includes validation, cleanup, etc.)
result = service.merge_pdfs(
    files=files,
    options=MergeOptions(add_headers=True)
)

print(f"Success: {result.success}")
print(f"Output: {result.path}")
print(f"Pages: {result.page_count}")
```

### Utility APIs

```python
from pdfforge.utils.pdf_utils import (
    detect_pdf_type,
    has_content_in_header_area,
    get_pdf_info
)
from pdfforge.utils.validation import validate_pdf_file
import fitz

# Detect PDF type
doc = fitz.open("document.pdf")
page = doc[0]
pdf_type = detect_pdf_type(page)  # 'scanned' or 'digital'

# Check header area
has_header = has_content_in_header_area(page, threshold=100)

# Get PDF info
info = get_pdf_info("document.pdf")
print(f"Pages: {info['page_count']}")
print(f"Size: {info['file_size']}")
print(f"Title: {info['title']}")

# Validate PDF
try:
    validate_pdf_file("document.pdf")
    print("PDF is valid")
except ValidationError as e:
    print(f"Invalid PDF: {e}")
```

## 🌐 REST API (Planned for v2.1)

### Base URL

```
http://localhost:5000/api/v1
```

### Authentication

```http
POST /api/v1/auth/token
Content-Type: application/json

{
  "api_key": "your-api-key"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

### Endpoints

#### Merge PDFs

```http
POST /api/v1/merge
Authorization: Bearer {token}
Content-Type: multipart/form-data

files: [file1.pdf, file2.pdf]
options: {
  "add_headers": true,
  "page_start": 1,
  "output_name": "merged.pdf"
}
```

**Response:**
```json
{
  "success": true,
  "job_id": "abc123",
  "download_url": "/api/v1/download/abc123",
  "expires_at": "2024-11-04T12:00:00Z"
}
```

#### Normalize PDF

```http
POST /api/v1/normalize
Authorization: Bearer {token}
Content-Type: multipart/form-data

file: document.pdf
options: {
  "page_size": "letter",
  "orientation": "portrait",
  "ocr": false
}
```

**Response:**
```json
{
  "success": true,
  "job_id": "def456",
  "download_url": "/api/v1/download/def456",
  "pages": 10,
  "size_before": 5242880,
  "size_after": 4194304
}
```

#### Compress PDF

```http
POST /api/v1/compress
Authorization: Bearer {token}
Content-Type: multipart/form-data

file: document.pdf
options: {
  "max_image_size": [1920, 1920],
  "jpeg_quality": 85,
  "aggressive": false
}
```

**Response:**
```json
{
  "success": true,
  "job_id": "ghi789",
  "download_url": "/api/v1/download/ghi789",
  "compression_ratio": 0.45,
  "size_before": 10485760,
  "size_after": 4718592
}
```

#### Download Result

```http
GET /api/v1/download/{job_id}
Authorization: Bearer {token}
```

**Response:**
- Binary PDF file
- Content-Type: application/pdf
- Content-Disposition: attachment; filename="output.pdf"

#### Check Job Status

```http
GET /api/v1/jobs/{job_id}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "job_id": "abc123",
  "status": "completed",
  "progress": 100,
  "created_at": "2024-11-03T10:00:00Z",
  "completed_at": "2024-11-03T10:05:00Z",
  "download_url": "/api/v1/download/abc123"
}
```

### Batch Operations

```http
POST /api/v1/batch/normalize
Authorization: Bearer {token}
Content-Type: multipart/form-data

files: [file1.pdf, file2.pdf, file3.pdf]
options: {
  "page_size": "a4",
  "orientation": "portrait"
}
```

**Response:**
```json
{
  "success": true,
  "batch_id": "batch_xyz",
  "jobs": [
    {"file": "file1.pdf", "job_id": "job1"},
    {"file": "file2.pdf", "job_id": "job2"},
    {"file": "file3.pdf", "job_id": "job3"}
  ],
  "download_url": "/api/v1/batch/download/batch_xyz"
}
```

## 🔐 Authentication

### API Key Authentication (Planned)

Generate API key:
```http
POST /api/v1/auth/key
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password"
}
```

Use API key:
```http
GET /api/v1/jobs
X-API-Key: your-api-key-here
```

### OAuth 2.0 (Future)

Future versions may support OAuth 2.0 for enhanced security.

## ⏱️ Rate Limiting

**Current limits (Planned):**
- 100 requests per hour (free tier)
- 1000 requests per hour (premium tier)
- 10,000 requests per hour (enterprise tier)

**Response headers:**
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1699027200
```

**Rate limit exceeded:**
```json
{
  "error": "rate_limit_exceeded",
  "message": "Rate limit exceeded. Try again in 30 minutes.",
  "retry_after": 1800
}
```

## ❌ Error Handling

### Error Response Format

```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "details": {
    "field": "specific_field",
    "reason": "detailed_reason"
  },
  "request_id": "req_12345"
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `invalid_request` | 400 | Invalid request parameters |
| `unauthorized` | 401 | Authentication required |
| `forbidden` | 403 | Insufficient permissions |
| `not_found` | 404 | Resource not found |
| `rate_limit_exceeded` | 429 | Too many requests |
| `validation_error` | 422 | Validation failed |
| `processing_error` | 500 | PDF processing failed |
| `internal_error` | 500 | Internal server error |

### Example Error Responses

**Invalid file:**
```json
{
  "error": "validation_error",
  "message": "Invalid PDF file",
  "details": {
    "file": "document.pdf",
    "reason": "File is corrupted or not a valid PDF"
  }
}
```

**File too large:**
```json
{
  "error": "validation_error",
  "message": "File size exceeds limit",
  "details": {
    "max_size": 524288000,
    "actual_size": 600000000,
    "file": "large_document.pdf"
  }
}
```

## 💡 Examples

### Python Examples

#### Example 1: Simple Merge

```python
import requests

# Upload and merge
files = [
    ('files', open('doc1.pdf', 'rb')),
    ('files', open('doc2.pdf', 'rb'))
]

response = requests.post(
    'http://localhost:5000/api/v1/merge',
    files=files,
    data={'output_name': 'merged.pdf'},
    headers={'X-API-Key': 'your-api-key'}
)

result = response.json()
print(f"Job ID: {result['job_id']}")

# Download result
download_response = requests.get(
    f"http://localhost:5000{result['download_url']}",
    headers={'X-API-Key': 'your-api-key'}
)

with open('output.pdf', 'wb') as f:
    f.write(download_response.content)
```

#### Example 2: Batch Normalization

```python
import requests
import time

# Upload multiple files
files = [
    ('files', open(f'doc{i}.pdf', 'rb'))
    for i in range(1, 6)
]

response = requests.post(
    'http://localhost:5000/api/v1/batch/normalize',
    files=files,
    json={'options': {'page_size': 'letter'}},
    headers={'X-API-Key': 'your-api-key'}
)

batch = response.json()
batch_id = batch['batch_id']

# Poll for completion
while True:
    status_response = requests.get(
        f'http://localhost:5000/api/v1/batch/{batch_id}',
        headers={'X-API-Key': 'your-api-key'}
    )
    
    status = status_response.json()
    
    if status['status'] == 'completed':
        break
    elif status['status'] == 'failed':
        print("Batch processing failed")
        break
    
    print(f"Progress: {status['progress']}%")
    time.sleep(5)

# Download batch results
download_response = requests.get(
    f"http://localhost:5000{status['download_url']}",
    headers={'X-API-Key': 'your-api-key'}
)

with open('normalized_batch.zip', 'wb') as f:
    f.write(download_response.content)
```

### JavaScript Examples

#### Example 1: Using Fetch API

```javascript
// Merge PDFs
async function mergePDFs(files) {
    const formData = new FormData();
    
    files.forEach(file => {
        formData.append('files', file);
    });
    
    formData.append('options', JSON.stringify({
        add_headers: true,
        page_start: 1
    }));
    
    const response = await fetch('http://localhost:5000/api/v1/merge', {
        method: 'POST',
        body: formData,
        headers: {
            'X-API-Key': 'your-api-key'
        }
    });
    
    const result = await response.json();
    
    // Download result
    const downloadResponse = await fetch(
        `http://localhost:5000${result.download_url}`,
        {
            headers: {
                'X-API-Key': 'your-api-key'
            }
        }
    );
    
    const blob = await downloadResponse.blob();
    
    // Trigger download
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'merged.pdf';
    a.click();
}

// Usage
const fileInput = document.querySelector('#file-input');
mergePDFs(Array.from(fileInput.files));
```

#### Example 2: Using Axios

```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

async function compressPDF(filePath) {
    const formData = new FormData();
    formData.append('file', fs.createReadStream(filePath));
    formData.append('options', JSON.stringify({
        jpeg_quality: 80,
        aggressive: false
    }));
    
    try {
        const response = await axios.post(
            'http://localhost:5000/api/v1/compress',
            formData,
            {
                headers: {
                    ...formData.getHeaders(),
                    'X-API-Key': 'your-api-key'
                }
            }
        );
        
        const { job_id, download_url } = response.data;
        
        // Download compressed file
        const downloadResponse = await axios.get(
            `http://localhost:5000${download_url}`,
            {
                headers: {
                    'X-API-Key': 'your-api-key'
                },
                responseType: 'arraybuffer'
            }
        );
        
        fs.writeFileSync('compressed.pdf', downloadResponse.data);
        console.log('File compressed successfully!');
        
    } catch (error) {
        console.error('Error:', error.response?.data || error.message);
    }
}

compressPDF('large_document.pdf');
```

### cURL Examples

#### Merge PDFs

```bash
curl -X POST http://localhost:5000/api/v1/merge \
  -H "X-API-Key: your-api-key" \
  -F "files=@document1.pdf" \
  -F "files=@document2.pdf" \
  -F 'options={"add_headers":true,"page_start":1}'
```

#### Normalize PDF

```bash
curl -X POST http://localhost:5000/api/v1/normalize \
  -H "X-API-Key: your-api-key" \
  -F "file=@document.pdf" \
  -F 'options={"page_size":"letter","ocr":false}'
```

#### Download Result

```bash
curl -X GET http://localhost:5000/api/v1/download/abc123 \
  -H "X-API-Key: your-api-key" \
  -o output.pdf
```

## 📚 SDK Support

Official SDKs planned for:
- Python
- JavaScript/TypeScript
- PHP
- Ruby
- Java
- Go

## 📞 Support

For API support:
- Email: oscar2song@gmail.com
- GitHub Issues: https://github.com/oscar2song/pdfforge/issues
- Documentation: https://pdfforge.readthedocs.io (planned)

## 🔄 Changelog

### v2.1 (Planned)
- REST API endpoints
- API key authentication
- Rate limiting
- Batch operations

### v2.0 (Current)
- Python API with modular architecture
- Service layer APIs
- Comprehensive error handling

---

**Last Updated**: November 2025
**Version**: 2.0.0  
**Status**: Python API available, REST API planned
