"""
Configuration for AI Processing Module
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


def _load_dotenv(env_path: Optional[Path] = None) -> None:
    """
    Load environment variables from a .env file located at the repo root.
    Existing variables are preserved to avoid overwriting manual overrides.
    """
    if env_path is None:
        env_path = Path(__file__).resolve().parents[1] / ".env"

    if not env_path.is_file():
        return

    with env_path.open("r", encoding="utf-8") as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('\'"')

            if not key or key in os.environ:
                continue

            os.environ[key] = value


_load_dotenv()


@dataclass
class AIConfig:
    """AI API Configuration"""
    
    # API Settings
    api_url: str = "https://api.bltcy.ai/v1/"
    api_key: str = ""
    model: str = "gpt-5-nano-2025-08-07"
    
    # Processing Settings
    batch_size: int = 10
    max_retries: int = 3
    timeout: int = 60
    
    # Target Languages
    target_languages: List[str] = None
    
    # Feature Flags
    enable_cleaning: bool = True
    enable_translation: bool = True
    skip_same_language: bool = True
    
    # Cache Settings
    enable_cache: bool = True
    cache_ttl: int = 86400  # 24 hours
    
    # Rate Limiting
    max_requests_per_minute: int = 60
    
    def __post_init__(self):
        if self.target_languages is None:
            self.target_languages = ["en", "zh", "ms"]
        
        # Load from environment variables if not set
        if not self.api_key:
            self.api_key = os.getenv("AI_API_KEY", "")
        
        if not self.api_url:
            self.api_url = os.getenv("AI_API_URL", "https://api.bltcy.ai/v1/")
        
        if not self.model:
            self.model = os.getenv("AI_MODEL", "gpt-5-nano-2025-08-07")

        timeout_override = os.getenv("AI_TIMEOUT")
        if timeout_override:
            try:
                self.timeout = int(timeout_override)
            except ValueError:
                pass
    
    @classmethod
    def from_env(cls) -> "AIConfig":
        """Create config from environment variables"""
        return cls(
            api_url=os.getenv("AI_API_URL", "https://api.bltcy.ai/v1/"),
            api_key=os.getenv("AI_API_KEY", ""),
            model=os.getenv("AI_MODEL", "gpt-5-nano-2025-08-07"),
            batch_size=int(os.getenv("AI_BATCH_SIZE", "10")),
            enable_cleaning=os.getenv("AI_ENABLE_CLEANING", "true").lower() == "true",
            enable_translation=os.getenv("AI_ENABLE_TRANSLATION", "true").lower() == "true",
            timeout=int(os.getenv("AI_TIMEOUT", "60")),
        )
