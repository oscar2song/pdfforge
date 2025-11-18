### PDFForge ↔ pdf-saas-platform — Integration Guide (Word + TOC) and playbook for next features

This guide captures the architecture, contracts, env setup, flows, and hard‑won lessons from integrating Premium Word (PDF→DOCX) and TOC Generator. Use it as the reference for adding future premium endpoints with the same pattern.

---

### 1) Architecture overview
- Repos
  - OSS app: `pdfforge` (Flask; public) — hosts UI, owns UX, proxies downloads
  - Private SaaS: `pdf-saas-platform` (Flask; private) — processes premium jobs
- Boundary: HTTP only
  - pdfforge calls SaaS via server‑to‑server HTTP with `X-API-Key` auth
  - SaaS returns JSON describing the artifact and serves the artifact via `GET /download/<file>`
  - pdfforge proxies the download to users via `/premium/download/<file>` (keeps SaaS base URL and key hidden)
- Observability
  - Add `X-Request-ID` to all client calls; log on both sides

---

### 2) Environment variables and defaults

#### pdfforge (client)
- Preferred unified envs (falls back to legacy `WORD_PREMIUM_*`):
  - `PREMIUM_ENABLED=true|false`
  - `PREMIUM_BASE_URL=http://localhost:5003`
  - `PREMIUM_API_KEY=dev-123456`
  - `PREMIUM_TIMEOUT_SECONDS=60`
  - `PREMIUM_RETRIES=0` (no retry by default)
  - `PREMIUM_DOWNLOAD_PROXY=true` (proxy artifacts via pdfforge)

Legacy (still supported internally): `WORD_PREMIUM_ENABLED`, `WORD_PREMIUM_BASE_URL`, `WORD_PREMIUM_API_KEY`, etc.

#### pdf-saas-platform (server)
- `PREMIUM_API_KEY=dev-123456` (must match pdfforge)
- `UPLOAD_FOLDER=C:\tmp\pdf_uploads` (absolute path recommended on Windows)
- `ARTIFACTS_DIR=C:\tmp\pdf_artifacts` (otherwise defaults to `<UPLOAD_FOLDER>\artifacts`)
- Optional: `CORS_ORIGINS=http://localhost:3000` (default already set)

Hard‑won lesson: Use absolute paths on Windows for `UPLOAD_FOLDER` and `ARTIFACTS_DIR` to avoid 404s when writing/reading artifacts from different working dirs.

---

### 3) Health endpoints
- SaaS
  - `GET /healthz` → `{ "status": "ok", "service": "pdf-saas-platform", "version": "1.0.0" }`
  - `GET /api/health` → `{ "status": "healthy", "version": "1.0.0" }`
- pdfforge
  - `GET /premium/health` → returns SaaS health (via client call)

Client is tolerant: tries `/healthz` then `/api/health`.

---

### 4) Premium Word integration (contract)
- Endpoint (SaaS): `POST /api/word/convert`
  - Headers: `X-API-Key: <token>`, `X-Request-ID: <uuid>`
  - Form: 
    - `file` → PDF (required)
    - `options` → JSON string with keys like `ocr`, `languages`, `detect_tables`, `merge_paragraphs`, `output_format: "docx"`, `page_range`, `overlay` (tolerant to missing keys)
  - Success (200 JSON):
    ```json
    {
      "success": true,
      "file_id": "20251116_154915_MyDoc_converted",
      "output_filename": "20251116_154915_MyDoc_converted.docx",
      "output_file_url": "/download/20251116_154915_MyDoc_converted.docx",
      "message": "Converted (placeholder)"
    }
    ```
  - Errors: 400 (invalid options), 401 (bad/missing API key), 413 (too large), 422 (conversion failure), 5xx
- Artifact download (SaaS): `GET /download/<file>.docx`
- pdfforge routes
  - `POST /premium/word/convert` → forwards to SaaS, then redirects to `/premium/download/<file>.docx`
  - `GET /premium/download/<file>` → proxies `GET {BASE}/download/<file>` preserving `Content-Disposition`

Note: Word conversion uses a placeholder now; swap in the real converter later with the same contract.

---

### 5) Premium TOC integration (contract)
- Endpoint (SaaS): `POST /api/toc/generate`
  - Headers: `X-API-Key`, `X-Request-ID`
  - Form fields:
    - `file` → PDF (optional; can generate standalone TOC when omitted)
    - `options` → JSON string (simple toggles): `{ levels, include_page_numbers, style, bookmarks_only }`
    - `entries` → JSON string (list of entries) [optional]
    - `config` → JSON string (fine‑grained config) [optional]
  - Success (200 JSON):
    ```json
    {
      "success": true,
      "file_id": "toc_1763427278",
      "output_filename": "toc_1763427278.pdf",
      "output_file_url": "/download/toc_1763427278.pdf",
      "message": "TOC generated"
    }
    ```
  - Errors: 400 (bad JSON), 401, 413, 422 (generation failed), 5xx
- Artifact download (SaaS): `GET /download/<file>.pdf`
- pdfforge routes
  - `POST /premium/toc/generate` → accepts `file`, `options`, and (optionally) `entries`, `config`; on success:
    - If XHR/`?ajax=1`/`Accept: application/json`: return JSON `{ success, file_id, output_file_url }`
    - Else: 302 redirect to `/premium/download/<file>.pdf`
  - `GET /premium/toc/builder` → renders premium UI (namespaced external template)

SaaS adapter prioritizes caller’s `entries`/`config` when provided; falls back to package defaults or CLI.

---

### 6) Client submission details (lessons learned)
- Always use `file` as the file field name for premium endpoints (server accepts some aliases, but `file` is canonical)
- Include JSON strings for `options`, and when using custom TOC input, also `entries`, `config`
- For XHR from the premium builder page:
  - Request JSON by adding `?ajax=1` to the submit URL or `Accept: application/json`
  - Handle both JSON and redirect (302) server responses; we standardized on JSON for XHR
- Avoid spinner deadlocks by not navigating the page during generation; use a hidden iframe to trigger downloads

---

### 7) Template namespacing to avoid collisions
- We load external premium templates via a Jinja `PrefixLoader` and render with the explicit prefix `premium/`:
  - Premium page route renders `render_template("premium/toc.html", ...)`
  - This prevents collision with the built‑in `toc.html` in pdfforge

---

### 8) JSON schemas for TOC

#### entries (list)
Each item can be one of:
- Blank line:
  ```json
  { "title": "", "is_blank_line": true }
  ```
- Centered heading (no page number required):
  ```json
  { "title": "Volume 1", "is_centered": true, "level": 0 }
  ```
- Description‑only (no page number required):
  ```json
  { "title": "CHAPTER 1: INTRODUCTION", "is_description_only": true, "level": 0 }
  ```
- Normal entry (page number required):
  ```json
  { "title": "1. Background", "page_number": 1, "level": 1, "is_bold": false, "underline_char": "" }
  ```

Supported fields per entry: `title, page_number, level, notes, is_bold, font_size, is_centered, is_description_only, underline_char, is_blank_line` (extra fields are tolerated and ignored server‑side).

#### config (object)
Example:
```json
{
  "title": "TABLE OF CONTENTS",
  "subtitle": null,
  "left_header": "Document Name",
  "right_header": "Page",
  "font_size": 11,
  "title_font_size": 16,
  "use_roman_page_numbers": true,
  "roman_with_dashes": true,
  "title_underline_char": ""
}
```

---

### 9) Error mapping and UX
- 400 → Invalid JSON (entries/config/options): show message from body
- 401/403 → Premium access required → show enable instructions/upsell (pdfforge renders `premium_info.html` when disabled)
- 413 → File too large → show current limit
- 422 → Generation/conversion failed → show details if present
- 5xx/timeouts → “Service temporarily unavailable — try again later”

All client calls include `X-Request-ID` for correlation. Log `{endpoint, duration_ms, status, request_id}`.

---

### 10) Known pitfalls and fixes
- Double `/download/` in redirect paths → Normalize path by stripping leading `/download/` when building proxy URLs
- 404 when downloading artifacts → Ensure SaaS `ARTIFACTS_DIR` and writer use the same absolute path
- Spinner stuck in UI → Use JSON mode for XHR and trigger downloads via hidden iframe; always clear loading state on success/error with a timeout failsafe
- Template collisions (`toc.html`) → Use Jinja prefix (`premium/`) for external templates
- Scope mismatch for `entries` in the builder → When reading entries in JS, support both `let entries` and `window.entries`

---

### 11) Developer quickstart

#### Start SaaS (PowerShell)
```powershell
$env:PREMIUM_API_KEY = "dev-123456"
$env:UPLOAD_FOLDER   = "C:\\tmp\\pdf_uploads"
$env:ARTIFACTS_DIR   = "C:\\tmp\\pdf_artifacts"
python external\pdf-saas-platform\pdf-saas-platform\backend\app.py
# Health: curl -sS http://localhost:5003/healthz
```

#### Start pdfforge
```powershell
$env:PREMIUM_ENABLED = "true"
$env:PREMIUM_BASE_URL = "http://localhost:5003"
$env:PREMIUM_API_KEY = "dev-123456"
python app.py
# Health: curl -sS http://localhost:5000/premium/health
```

#### Word conversion (via pdfforge)
```bash
curl -i -X POST http://localhost:5000/premium/word/convert \
  -F "file=@C:/path/to/sample.pdf" \
  -F "options={\"ocr\":true,\"languages\":[\"eng\"],\"detect_tables\":true,\"merge_paragraphs\":true,\"output_format\":\"docx\"}"
```

#### TOC generation (via pdfforge)
```bash
curl -i -X POST http://localhost:5000/premium/toc/generate \
  -F "file=@C:/path/to/sample.pdf" \
  -F "options={\"levels\":3,\"include_page_numbers\":true}" \
  -F "entries=$(cat entries.json)" \
  -F "config=$(cat config.json)"
```

---

### 12) Playbook for adding the next premium feature
1) Define endpoint in SaaS under `/api/<feature>/<action>`
   - Auth: `X-API-Key`
   - Input: `multipart/form-data` with `file` (if needed) + `options` (JSON string)
   - Output: `200` JSON with `{ success, file_id, output_filename, output_file_url, message }`
   - Artifact serving: `GET /download/<file>`
2) Implement SaaS adapter (Python API or CLI wrapper)
   - Prefer Python import; fallback to CLI via `subprocess.run` with timeout
   - Write artifact to `ARTIFACTS_DIR`; return the path; log errors clearly
3) Extend pdfforge client
   - Add `SaasClient.<feature_method>(file_path, options, ...)` mapping to the endpoint
4) Add pdfforge route(s)
   - `POST /premium/<feature>/<action>`: forward form fields, map success to JSON or 302 redirect to `/premium/download/...`
5) UI/UX
   - Add a page or a button; if premium disabled, render the upsell page
6) Observability
   - Include `X-Request-ID` and minimal structured logs
7) Verify with cURL and through the UI (happy path + error cases)

---

### 13) Suggestions for immediate improvements
- Replace Word placeholder with real converter
  - Use `pdf2docx` (already in requirements) with optional OCR fallback for scanned PDFs
  - Keep the same artifact contract and error mapping
- Strengthen import/export in premium builder
  - Normalize import function to accept both array-only and `{ entries, config }`; assign to both `entries` and `window.entries`; populate UI from config; show “Imported N entries”
  - Add a visible “Download last result” link to the success banner
- Add basic unit tests
  - SaaS: mock adapter to test `/api/word/convert` and `/api/toc/generate` status mapping and JSON
  - pdfforge: test redirect vs JSON mode for `/premium/toc/generate` and header preservation in proxy
- Add `.env` loading (optional)
  - Use `python-dotenv` to auto‑load env for local dev convenience
- Docker/dev UX
  - Provide a `docker-compose.override.yml` to run both services with a single command and shared volume for artifacts
- Security/limits
  - Enforce size/type checks; rate limits if exposed beyond local dev; continue to proxy downloads only (no direct SaaS exposure)

---

### 14) Troubleshooting quick hits
- 401 Unauthorized → ensure `PREMIUM_API_KEY` matches on both sides; restart both apps
- 404 on `/premium/download/<file>` → verify direct SaaS download works; check absolute `ARTIFACTS_DIR` paths and filenames
- Spinner stuck → use JSON mode (`?ajax=1`); ensure the page clears loading state on both success/error with failsafe timeout
- “Please add at least one entry” after import → ensure the builder reads the same `entries` array (support both `let entries` and `window.entries`)

---

### 15) What I can improve next (pick what you want prioritized)
- Implement real PDF→DOCX in SaaS `/api/word/convert` (with OCR, table detection, paragraph merging)
- Harden the premium builder import/export tooling (format tolerance, UI feedback, sample JSON templates)
- Add compact telemetry logs on both sides with `X-Request-ID` for faster debugging
- Provide a single‑command local stack via Docker Compose with mounted volumes for artifacts
- Write smoke tests to guard the contracts and prevent regressions (redirect vs JSON mode, proxy headers, error mapping)
