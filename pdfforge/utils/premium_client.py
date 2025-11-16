"""
Premium client for calling external pdf-saas-platform (private repo)

- Keeps OSS and private repos separate by using HTTP integration only
- Reads configuration from Flask app config if available, otherwise environment
- Currently implements Word (PDF->DOCX) premium conversion call

Endpoint contract (expected on SaaS, default base http://localhost:5003):
  POST {BASE}/api/word/convert
    Form-Data (multipart):
      - file: uploaded PDF file
      - options: JSON string of options (page_range, languages, ocr, overlay, etc.)
    Headers:
      - X-API-Key: <api key>
    Returns JSON:
      {
        "success": true,
        "output_file_url": "/download/<id>.docx" | "http(s)://...",
        "output_filename": "<name>.docx",
        "file_id": "...",
        "message": "..."
      }

This client downloads the resulting DOCX into downloads/word when a relative URL is returned.
"""
from __future__ import annotations

import io
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests
from flask import current_app

from .file_manager import get_file_manager


@dataclass
class PremiumConfig:
    enabled: bool
    base_url: str
    api_key: str
    timeout_ms: int

    @staticmethod
    def from_env_or_app() -> "PremiumConfig":
        try:
            cfg = current_app.config  # type: ignore[attr-defined]
        except Exception:
            cfg = {}
        enabled = bool(
            str(cfg.get("WORD_PREMIUM_ENABLED", os.environ.get("WORD_PREMIUM_ENABLED", "false"))).lower()
            in ("1", "true", "yes")
        )
        base_url = str(cfg.get("WORD_PREMIUM_BASE_URL", os.environ.get("WORD_PREMIUM_BASE_URL", "http://localhost:5003")))
        api_key = str(cfg.get("WORD_PREMIUM_API_KEY", os.environ.get("WORD_PREMIUM_API_KEY", "")))
        timeout_ms = int(cfg.get("WORD_PREMIUM_TIMEOUT_MS", os.environ.get("WORD_PREMIUM_TIMEOUT_MS", "60000")))
        return PremiumConfig(enabled=enabled, base_url=base_url, api_key=api_key, timeout_ms=timeout_ms)


class PremiumWordClient:
    def __init__(self, config: Optional[PremiumConfig] = None) -> None:
        self.config = config or PremiumConfig.from_env_or_app()
        self.session = requests.Session()

    def is_enabled(self) -> bool:
        return self.config.enabled and bool(self.config.base_url)

    def convert_pdf_to_docx(self, file_path: str, options: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_enabled():
            return {"success": False, "error": "Premium is not enabled"}

        url = self._join(self.config.base_url, "/api/word/convert")
        headers = {}
        if self.config.api_key:
            headers["X-API-Key"] = self.config.api_key

        # Prepare multipart form
        files = {
            "file": (os.path.basename(file_path), open(file_path, "rb"), "application/pdf"),
        }
        data = {
            "options": json.dumps(options or {}),
        }

        try:
            resp = self.session.post(
                url,
                headers=headers,
                files=files,
                data=data,
                timeout=self.config.timeout_ms / 1000.0,
            )
            resp.raise_for_status()
            payload = resp.json()
            if not payload.get("success"):
                return payload

            output_url = payload.get("output_file_url")
            if not output_url:
                return {"success": False, "error": "SaaS response missing output_file_url"}

            # If absolute URL, try downloading; if relative, construct from base
            if output_url.startswith("http://") or output_url.startswith("https://"):
                download_url = output_url
            else:
                download_url = self._join(self.config.base_url, output_url)

            # Determine unified output filename using original PDF name
            fm = get_file_manager("word")
            original_pdf_name = os.path.basename(file_path)
            unified_name = fm.generate_output_filename(original_pdf_name, "converted", ext_override=".docx")

            # Download DOCX into downloads/word
            out_path = fm.get_download_path(unified_name)
            os.makedirs(os.path.dirname(out_path), exist_ok=True)

            with self.session.get(download_url, headers=headers, stream=True, timeout=self.config.timeout_ms / 1000.0) as r:
                r.raise_for_status()
                with open(out_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

            return {
                "success": True,
                "output_file": str(out_path),
                "downloaded_from": download_url,
                "file_id": payload.get("file_id"),
                "message": payload.get("message"),
            }
        except requests.HTTPError as e:
            return {"success": False, "error": f"Premium HTTP error: {e} - {getattr(e.response, 'text', '')}"}
        except Exception as e:
            return {"success": False, "error": f"Premium request failed: {e}"}

    @staticmethod
    def _join(base: str, path: str) -> str:
        if base.endswith("/"):
            base = base[:-1]
        if not path.startswith("/"):
            path = "/" + path
        return base + path
