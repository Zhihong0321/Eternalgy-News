"""
Main Article Processor
Orchestrates cleaning and translation pipeline
"""

from datetime import datetime
from typing import List, Optional
from .config import AIConfig
from .models.article import RawArticle, ProcessedArticle
from .services.ai_client import AIClient
from .services.cleaner import ArticleCleaner
from .services.translator import ArticleTranslator
from .services.language_detector import LanguageDetector


class ArticleProcessor:
    """
    Main processor for TrendRadar articles
    
    Pipeline:
    1. Take raw articles from TrendRadar
    2. Clean titles with AI
    3. Detect language
    4. Translate to 3 languages (EN, ZH, MS)
    5. Return processed articles
    """
    
    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        config: Optional[AIConfig] = None
    ):
        """
        Initialize processor
        
        Args:
            api_url: OpenAI-compatible API URL
            api_key: API key
            model: Model name
            config: AIConfig object (overrides individual params)
        """
        # Use provided config or create new one
        if config:
            self.config = config
        else:
            self.config = AIConfig(
                api_url=api_url or "https://api.bltcy.ai/v1/",
                api_key=api_key or "",
                model=model or "gpt-5-nano-2025-08-07"
            )
        
        # Initialize services
        self.ai_client = AIClient(
            api_url=self.config.api_url,
            api_key=self.config.api_key,
            model=self.config.model,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries
        )
        
        self.language_detector = LanguageDetector()
        
        self.cleaner = ArticleCleaner(
            ai_client=self.ai_client,
            batch_size=self.config.batch_size
        )
        
        self.translator = ArticleTranslator(
            ai_client=self.ai_client,
            language_detector=self.language_detector,
            skip_same_language=self.config.skip_same_language
        )
    
    def process_articles(self, raw_articles: List[RawArticle]) -> List[ProcessedArticle]:
        """
        Process multiple articles through the full pipeline
        
        Args:
            raw_articles: List of RawArticle objects from TrendRadar
        
        Returns:
            List of ProcessedArticle objects with translations
        """
        if not raw_articles:
            return []
        
        print(f"Processing {len(raw_articles)} articles...")
        
        # Convert to dict format for processing
        articles_dict = [self._raw_to_dict(article) for article in raw_articles]
        
        # Step 1: Clean titles
        if self.config.enable_cleaning:
            print("Step 1/3: Cleaning titles...")
            articles_dict = self.cleaner.clean_articles(articles_dict)
        else:
            # If cleaning disabled, use original as cleaned
            for article in articles_dict:
                article['title_cleaned'] = article['title']
        
        # Step 2: Translate
        if self.config.enable_translation:
            print("Step 2/3: Translating to 3 languages...")
            articles_dict = self.translator.translate_articles(articles_dict)
        else:
            # If translation disabled, use cleaned title for all languages
            for article in articles_dict:
                title = article.get('title_cleaned', article['title'])
                article['title_en'] = title
                article['title_zh'] = title
                article['title_ms'] = title
                article['detected_language'] = 'unknown'
        
        # Step 3: Convert to ProcessedArticle objects
        print("Step 3/3: Finalizing...")
        processed = [self._dict_to_processed(article) for article in articles_dict]
        
        print(f"✓ Successfully processed {len(processed)} articles")
        return processed
    
    def process_single(self, raw_article: RawArticle) -> ProcessedArticle:
        """Process a single article"""
        return self.process_articles([raw_article])[0]
    
    def _raw_to_dict(self, raw: RawArticle) -> dict:
        """Convert RawArticle to dict for processing"""
        return {
            'id': raw.id,
            'title': raw.title,
            'platform': raw.platform,
            'rank': raw.rank,
            'url': raw.url,
            'timestamp': raw.timestamp,
            'metadata': raw.metadata
        }
    
    def _dict_to_processed(self, article_dict: dict) -> ProcessedArticle:
        """Convert processed dict to ProcessedArticle"""
        return ProcessedArticle(
            news_id=article_dict['id'],
            platform=article_dict['platform'],
            rank=article_dict['rank'],
            url=article_dict.get('url'),
            title_original=article_dict['title'],
            title_cleaned=article_dict.get('title_cleaned', article_dict['title']),
            detected_language=article_dict.get('detected_language', 'unknown'),
            title_en=article_dict.get('title_en', article_dict['title']),
            title_zh=article_dict.get('title_zh', article_dict['title']),
            title_ms=article_dict.get('title_ms', article_dict['title']),
            collected_at=article_dict.get('timestamp'),
            processed_at=datetime.now(),
            metadata=article_dict.get('metadata', {})
        )
    
    @classmethod
    def from_env(cls) -> "ArticleProcessor":
        """Create processor from environment variables"""
        config = AIConfig.from_env()
        return cls(config=config)
