"""Configuration for news search module"""
import os

# API Configuration
SEARCH_API_URL = "https://api.bltcy.ai/v1/chat/completions"
SEARCH_API_KEY = os.getenv("SEARCH_API_KEY", "sk-jW4WLdgCGCshSyFY9VbKXwj8y2YXclFHxw2x2WbXElFkcAlD")
SEARCH_MODEL = "gpt-4o-mini-search-preview"

# Database Configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5433")
DB_NAME = os.getenv("DB_NAME", "news_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

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
