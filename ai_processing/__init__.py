"""
AI Processing Module for TrendRadar

This independent module processes news articles through:
1. Content extraction from URLs (using readability)
2. AI-powered cleaning/editing and summarization
3. Multi-language translation (EN, ZH, MS)
4. Language detection with smart skipping

Usage:
    # Basic processor (titles only)
    from ai_processing import ArticleProcessor
    
    processor = ArticleProcessor(
        api_url="https://api.bltcy.ai/v1/",
        api_key="your-key",
        model="gpt-5-nano-2025-08-07"
    )
    
    processed = processor.process_articles(raw_articles)
    
    # Enhanced processor (with content extraction)
    from ai_processing import ArticleProcessorWithContent
    
    processor = ArticleProcessorWithContent(
        api_url="https://api.bltcy.ai/v1/",
        api_key="your-key",
        model="gpt-5-nano-2025-08-07",
        extract_content=True
    )
    
    processed = processor.process_articles(raw_articles)
"""

from .processor import ArticleProcessor
from .processor_with_content import ArticleProcessorWithContent
from .models.article import RawArticle, ProcessedArticle

__version__ = "1.1.0"
__all__ = [
    "ArticleProcessor",
    "ArticleProcessorWithContent", 
    "RawArticle",
    "ProcessedArticle"
]
