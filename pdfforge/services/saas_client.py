"""
SaaS client for premium features (Word conversion, etc.)
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Dict, Optional

import requests
from requests import Response

logger = logging.getLogger(__name__)


class SaasClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout_seconds: int = 60,
        retries: int = 0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout_seconds
        self.retries = max(0, retries)

    def _headers(self) -> Dict[str, str]:
        return {
            "X-API-Key": self.api_key,
            "X-Request-ID": str(uuid.uuid4()),
        }

    def health_check(self) -> Dict[str, Any]:
        """Check health of SaaS backend. Prefer /healthz, fallback to /api/health."""
        for path in ("/healthz", "/api/health"):
            try:
                url = f"{self.base_url}{path}"
                r: Response = requests.get(url, headers=self._headers(), timeout=self.timeout)
                if r.ok:
                    return {"ok": True, "status": r.status_code, "json": r.json()}
            except requests.RequestException as e:
                logger.warning("SaaS health check failed at %s: %s", path, e)
        return {"ok": False}

    def convert_word(self, file_path: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """POST /api/word/convert and return parsed result or error mapping."""
        options = options or {}
        url = f"{self.base_url}/api/word/convert"
        headers = self._headers()
        files = {"file": open(file_path, "rb")}
        data = {"options": json.dumps(options)}
        try:
            r: Response = requests.post(url, headers=headers, files=files, data=data, timeout=self.timeout)
        finally:
            files["file"].close()

        if r.status_code == 200:
            try:
                body = r.json()
            except ValueError:
                return {"ok": False, "error": "Invalid JSON from SaaS", "status": r.status_code}
            return {"ok": True, **body}

        # Error mapping
        mapped = {
            400: "Invalid request",
            401: "Unauthorized (premium access required)",
            403: "Forbidden (premium access required)",
            413: "File too large",
            422: "Conversion failed",
        }
        message = mapped.get(r.status_code, f"Service error ({r.status_code})")
        return {"ok": False, "error": message, "status": r.status_code, "body": r.text}

    def generate_toc(self, file_path: str, options: Optional[Dict[str, Any]] = None, entries: Optional[Dict[str, Any]] = None, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """POST /api/toc/generate and return parsed result or error mapping.
        Accepts optional `entries` (list/dict) and `config` (dict) which will be JSON-encoded.
        """
        options = options or {}
        url = f"{self.base_url}/api/toc/generate"
        headers = self._headers()
        files = {"file": open(file_path, "rb")}
        data = {"options": json.dumps(options)}
        if entries is not None:
            data["entries"] = json.dumps(entries)
        if config is not None:
            data["config"] = json.dumps(config)
        try:
            r: Response = requests.post(url, headers=headers, files=files, data=data, timeout=self.timeout)
        finally:
            files["file"].close()

        if r.status_code == 200:
            try:
                body = r.json()
            except ValueError:
                return {"ok": False, "error": "Invalid JSON from SaaS", "status": r.status_code}
            return {"ok": True, **body}

        mapped = {
            400: "Invalid request",
            401: "Unauthorized (premium access required)",
            403: "Forbidden (premium access required)",
            413: "File too large",
            422: "TOC generation failed",
        }
        message = mapped.get(r.status_code, f"Service error ({r.status_code})")
        return {"ok": False, "error": message, "status": r.status_code, "body": r.text}

    def proxy_download(self, download_path: str) -> Response:
        """
        Request the artifact from SaaS and return the raw Response for streaming.
        `download_path` should be a path like "/download/<file>.docx".
        """
        url = f"{self.base_url}{download_path}"
        r = requests.get(url, headers=self._headers(), stream=True, timeout=self.timeout)
        return r
