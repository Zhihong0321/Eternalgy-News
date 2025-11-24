"""
Search-based Reader integration using gpt-5-search-api.
Replaces the legacy Jina reader.
"""

import json
import os
from dataclasses import dataclass
from typing import Optional, Dict

import requests


@dataclass
class ReaderConfig:
    """Configuration for the search-powered reader."""

    api_url: str = "https://api.bltcy.ai/v1/chat/completions"
    api_key: str = ""
    model: str = "gpt-5-search-api-2025-10-14"
    timeout: int = 60
    max_content_length: int = 900  # keep body compact

    def __post_init__(self):
        # Prefer dedicated reader/search credentials; avoid rewriter/AI defaults
        if not self.api_key:
            self.api_key = (
                os.getenv("READER_API_KEY")
                or os.getenv("SEARCH_API_KEY")
                or os.getenv("AI_API_KEY", "")
            )
        env_url = os.getenv("READER_API_URL") or os.getenv("SEARCH_API_URL")
        if env_url:
            self.api_url = env_url.rstrip("/")
            if not self.api_url.endswith("/chat/completions"):
                self.api_url = f"{self.api_url}/chat/completions"
        env_model = os.getenv("READER_MODEL") or os.getenv("SEARCH_MODEL")
        if env_model:
            self.model = env_model


class ArticleReader:
    """Lightweight article reader backed by gpt-5-search-api."""

    def __init__(self, config: Optional[ReaderConfig] = None):
        self.config = config or ReaderConfig()
        self.session = requests.Session()

    def _build_prompt(self, url: str) -> str:
        return (
            "You are a lean news reader. Fetch the URL and return a single JSON object only "
            "(no markdown, no code fences, no citations, no links). Keys: "
            "title (string), news_date (ISO date or null), content (plain text, <=450 characters, "
            "only the core article body; no ads/boilerplate). Keep the entire response under 550 characters. "
            "If fetch fails, set title='error' and content to a short error reason.\nURL: "
            f"{url}"
        )

    def read_url(self, url: str) -> Optional[Dict[str, str]]:
        """
        Fetch article content using the search API.
        Returns a dict with title, content, excerpt, and optional news_date.
        """
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": self._build_prompt(url)},
                {"role": "user", "content": url},
            ],
        }

        try:
            response = self.session.post(
                self.config.api_url, headers=headers, json=payload, timeout=self.config.timeout
            )
            response.raise_for_status()
            data = response.json()
            message = data.get("choices", [{}])[0].get("message", {})
            content_text = message.get("content", "") or ""

            raw = content_text
            if "```" in raw:
                start = raw.find("```")
                end = raw.find("```", start + 3)
                if end > start:
                    raw = raw[start + 3 : end].strip()
            try:
                parsed = json.loads(raw)
            except Exception:
                return {"error": "reader parse error", "status_code": response.status_code}

            title = parsed.get("title", "") or ""
            news_date = parsed.get("news_date") or parsed.get("date")
            body = parsed.get("content") or ""
            if body and len(body) > self.config.max_content_length:
                body = body[: self.config.max_content_length] + "..."
            excerpt = body[:200] + "..." if len(body) > 200 else body
            return {
                "title": title,
                "news_date": news_date,
                "content": body,
                "excerpt": excerpt,
                "url": parsed.get("url") or url,
                "status_code": response.status_code,
            }
        except requests.HTTPError as exc:
            status_code = exc.response.status_code if exc.response else None
            error_message = f"{status_code} {str(exc)}"
            return {"error": error_message, "blocked": False, "status_code": status_code}
        except requests.RequestException as exc:
            return {"error": str(exc), "status_code": None}


# Backward-compatible aliases so existing imports still work
JinaReaderConfig = ReaderConfig
JinaReader = ArticleReader
