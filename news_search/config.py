"""Configuration for news search module"""
import os
from urllib.parse import urlparse, parse_qs

# API Configuration
SEARCH_API_URL = "https://api.bltcy.ai/v1/chat/completions"
SEARCH_API_KEY = os.getenv("SEARCH_API_KEY", "sk-jW4WLdgCGCshSyFY9VbKXwj8y2YXclFHxw2x2WbXElFkcAlD")
SEARCH_MODEL = "gpt-5-search-api-2025-10-14"


def _parse_database_url(db_url: str):
    """Parse a PostgreSQL URL into connection params."""
    parsed = urlparse(db_url)
    query = parse_qs(parsed.query)

    return {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or "5432",
        "database": (parsed.path or "/").lstrip("/") or "postgres",
        "user": parsed.username or "postgres",
        "password": parsed.password or "",
        # Prefer explicit query param, else env override, else default
        "sslmode": (query.get("sslmode", [None])[0] or os.getenv("DB_SSLMODE", "require")),
    }


def _build_db_params():
    """
    Build connection parameters with Railway compatibility.
    Supports:
    - DATABASE_URL / DB_URL
    - DB_HOST starting with postgres:// or postgresql://
    - Individual DB_* parts
    """
    db_url = os.getenv("DATABASE_URL") or os.getenv("DB_URL")
    host_env = os.getenv("DB_HOST", "")

    if db_url:
        return _parse_database_url(db_url)

    if host_env.startswith("postgres://") or host_env.startswith("postgresql://"):
        return _parse_database_url(host_env)

    return {
        "host": host_env or "localhost",
        "port": os.getenv("DB_PORT", "5433"),
        "database": os.getenv("DB_NAME", "news_db"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", "postgres"),
        "sslmode": os.getenv("DB_SSLMODE", "require"),
    }


# Database Configuration
DB_CONFIG = _build_db_params()
DB_HOST = DB_CONFIG["host"]
DB_PORT = DB_CONFIG["port"]
DB_NAME = DB_CONFIG["database"]
DB_USER = DB_CONFIG["user"]
DB_PASSWORD = DB_CONFIG["password"]
DB_SSLMODE = DB_CONFIG.get("sslmode", os.getenv("DB_SSLMODE", "require"))

# Search Configuration
MAX_LINKS_PER_SEARCH = 20
REQUEST_TIMEOUT = 60

# Processing Configuration
SAME_DOMAIN_DELAY = 3  # seconds between requests to same domain
MAX_CONCURRENT_DOMAINS = 3  # process N different domains concurrently
MAX_RETRIES = 2  # retry failed requests
PROCESSING_TIMEOUT = 30  # timeout for single URL processing

# Processing Modes
AUTO_PROCESS_AFTER_SEARCH = True  # Automatically process after search
