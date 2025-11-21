"""
Jina AI Reader integration
Fetches Markdown content using the r.jina.ai Reader endpoint.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict
import os

import requests


@dataclass
class JinaReaderConfig:
    """Configuration for the Jina Reader API."""

    reader_base_url: str = "https://r.jina.ai"
    api_key: str = ""
    timeout: int = 60
    max_content_length: int = 5000
    retain_images: str = "none"
    return_format: str = "markdown"
    no_cache: bool = False
    extra_headers: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        # Normalize the base URL to avoid duplicate slashes
        self.reader_base_url = self.reader_base_url.rstrip("/")
        if not self.api_key:
            self.api_key = os.getenv("JINA_API_KEY", "")
        base_url = os.getenv("JINA_READER_BASE_URL")
        if base_url:
            self.reader_base_url = base_url.rstrip("/")


class JinaReader:
    """Wrapper around the Jina Reader REST endpoint."""

    def __init__(self, config: Optional[JinaReaderConfig] = None):
        self.config = config or JinaReaderConfig()
        self.session = requests.Session()

    def read_url(self, url: str) -> Optional[Dict[str, str]]:
        """
        Fetch the Markdown content for a given URL.

        Returns a dict with title, content, excerpt, and the normalized url when available.
        """
        endpoint = f"{self.config.reader_base_url}/{url}"
        headers = {
            "Accept": "application/json",
            "X-Return-Format": self.config.return_format,
            "X-Retain-Images": self.config.retain_images,
        }

        if self.config.no_cache:
            headers["X-No-Cache"] = "true"

        headers.update(self.config.extra_headers)

        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        try:
            response = self.session.get(endpoint, headers=headers, timeout=self.config.timeout)
            response.raise_for_status()
            payload = response.json().get("data", {})

            content = payload.get("content", "").strip()
            if not content:
                return {"error": "empty content", "status_code": response.status_code}

            if len(content) > self.config.max_content_length:
                content = content[: self.config.max_content_length] + "..."

            excerpt = content[:200] + "..." if len(content) > 200 else content
            return {
                "title": payload.get("title", "") or "",
                "description": payload.get("description", ""),
                "content": content,
                "excerpt": excerpt,
                "url": payload.get("url", url),
                "status_code": response.status_code
            }
        except requests.HTTPError as exc:
            status_code = exc.response.status_code if exc.response else None
            blocked = status_code in {403, 451}
            error_message = f"{status_code} {str(exc)}"
            print(f"[JinaReader] Failed to read {url}: {error_message}")
            return {
                "error": error_message,
                "blocked": blocked,
                "status_code": status_code
            }
        except requests.RequestException as exc:
            error_message = str(exc)
            print(f"[JinaReader] Failed to read {url}: {error_message}")
            return {"error": error_message, "status_code": None}
        except ValueError:
            print(f"[JinaReader] Unexpected JSON from Jina Reader for {url}")
            return {"error": "invalid json", "status_code": None}
