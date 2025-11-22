# ✂️ PDF Split Guide

This guide explains how to use the Split feature in PDFForge via the web UI and programmatically via the web endpoints.

- Split by specific page ranges (e.g., `1-5,10-12,20`)
- Split by start-page shorthand (e.g., `1,63` → `1-62` and `63-end`)
- Split by fixed page count (e.g., 3 pages per file)
- Split by approximate file size (MB)
- Split by bookmarks (top-level) when present

## UI Usage (recommended)

1. Open `/split/` in your browser.
2. Upload a single PDF file.
3. Choose a split method:
   - By Pages → Specific ranges → type ranges like `1-3,7,10-12` (or shorthand like `1,63`).
   - By Pages → Fixed pages per file → enter a positive integer.
   - By File Size → enter a positive MB value (approximate by average MB/page).
   - By Bookmarks → no extra inputs required.
4. Optional: Click Analyze to view page count, size, avg MB/page, and bookmark presence.
5. Click Split PDF. If multiple parts are produced, a ZIP will be generated automatically.

### Output & Downloads

- Results are stored under `downloads/split/<input-stem>/...`
- When there are multiple output files, a ZIP is created under `downloads/split` and exposed via:
  - `/download/<zip_filename>` (direct)
  - `/download/component/split/<file_id>` (component-based)

## Web API Endpoints

These endpoints are available for simple automation from scripts or other services.

Base URL: `http://localhost:5000`

### 1) Upload

POST `/split/upload`

Form-Data:
- `file`: PDF file to upload

Response (200):
```json
{
  "success": true,
  "file_path": "C:/.../uploads/input.pdf",
  "filename": "input.pdf"
}
```

### 2) Analyze (optional)

POST `/split/analyze`

Body (JSON):
```json
{ "file_path": "C:/.../uploads/input.pdf" }
```

Response (200):
```json
{
  "success": true,
  "total_pages": 123,
  "size_mb": 47.32,
  "avg_mb_per_page": 0.385,
  "has_bookmarks": true
}
```

### 3) Process

POST `/split/process`

Body (JSON):
```json
{
  "file_path": "C:/.../uploads/input.pdf",
  "options": {
    "split_type": "pages",
    "page_ranges": "1-5,10-12,20",
    "pages_per_file": 3,
    "max_size_mb": 10.0
  }
}
```

- Shorthand ranges: If `page_ranges` has only comma-separated numbers and no hyphen (e.g., `"1,63"`), they are treated as start pages: `1-62` and `63-end`.

Response (200):
```json
{
  "success": true,
  "files_created": 5,
  "output_dir": "C:/.../downloads/split/input",
  "output_files": [
    "C:/.../downloads/split/input/input_pages_1-5.pdf",
    "C:/.../downloads/split/input/input_pages_6-10.pdf"
  ],
  "zip_filename": "input_split.zip",
  "download_url": "/download/input_split.zip",
  "component_download_url": "/download/component/split/input_split",
  "file_id": "input_split",
  "split_type": "pages"
}
```

## cURL Examples

Upload:
```bash
curl -F "file=@/path/to/input.pdf" http://localhost:5000/split/upload
```

Analyze:
```bash
curl -H "Content-Type: application/json" \
  -d '{"file_path":"C:/.../uploads/input.pdf"}' \
  http://localhost:5000/split/analyze
```

Split by ranges:
```bash
curl -H "Content-Type: application/json" -d '{
  "file_path": "C:/.../uploads/input.pdf",
  "options": {"split_type":"pages", "page_ranges":"1-5,10-12,20"}
}' http://localhost:5000/split/process
```

Split by start pages shorthand (`1,63` → `1-62`, `63-end`):
```bash
curl -H "Content-Type: application/json" -d '{
  "file_path": "C:/.../uploads/input.pdf",
  "options": {"split_type":"pages", "page_ranges":"1,63"}
}' http://localhost:5000/split/process
```

Split by fixed pages:
```bash
curl -H "Content-Type: application/json" -d '{
  "file_path": "C:/.../uploads/input.pdf",
  "options": {"split_type":"pages", "pages_per_file": 3}
}' http://localhost:5000/split/process
```

Split by size (approx.):
```bash
curl -H "Content-Type: application/json" -d '{
  "file_path": "C:/.../uploads/input.pdf",
  "options": {"split_type":"size", "max_size_mb": 10.0}
}' http://localhost:5000/split/process
```

Split by bookmarks:
```bash
curl -H "Content-Type: application/json" -d '{
  "file_path": "C:/.../uploads/input.pdf",
  "options": {"split_type":"bookmarks"}
}' http://localhost:5000/split/process
```

## Troubleshooting

- The Split button stays disabled: Ensure a file is selected and the chosen method inputs are valid. As of the latest update, the button enables live while typing values.
- File rejected on upload: Only PDFs are accepted; size limit is 500MB (configurable in the UI script).
- Bookmarks splitting fails: The PDF must contain top-level bookmarks; otherwise, choose a different method.
- Size-based splitting is approximate: The service estimates pages per file by average MB/page.

## Implementation Notes

- Core logic: `src/src/pdfforge/core/split.py` (`PDFSplitterCore`)
- Service layer: `src/src/pdfforge/services/split_service.py`
- Routes: `src/src/pdfforge/routes/split.py`
- UI: `src/pdfforge/templates/split.html`, `src/pdfforge/static/js/split.js`, `src/pdfforge/static/css/split.css`
- Downloads: managed by `FilePathManager` under `downloads/split/` and download routes in `routes/download.py`
