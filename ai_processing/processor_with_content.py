"""
Enhanced Article Processor with Content Extraction
Orchestrates content extraction, cleaning, and translation pipeline
"""

from datetime import datetime
from typing import List, Optional
from .config import AIConfig
from .models.article import RawArticle, ProcessedArticle
from .services.ai_client import AIClient
from .services.cleaner import ArticleCleaner
from .services.content_extractor import ContentExtractor
from .services.content_cleaner import ContentCleaner
from .services.translator import ArticleTranslator
from .services.language_detector import LanguageDetector


class ArticleProcessorWithContent:
    """
    Enhanced processor for TrendRadar articles with full content extraction
    
    Pipeline:
    1. Take raw articles from TrendRadar (with URLs)
    2. Extract full article content from URLs
    3. Clean content with AI (remove ads, summarize)
    4. Detect language
    5. Translate to 3 languages (EN, ZH, MS)
    6. Return processed articles with summaries
    """
    
    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        config: Optional[AIConfig] = None,
        extract_content: bool = True,
        max_content_length: int = 3000
    ):
        """
        Initialize enhanced processor
        
        Args:
            api_url: OpenAI-compatible API URL
            api_key: API key
            model: Model name
            config: AIConfig object (overrides individual params)
            extract_content: Whether to extract full content from URLs
            max_content_length: Maximum content length to extract
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
        
        self.extract_content = extract_content
        self.max_content_length = max_content_length
        
        # Initialize services
        self.ai_client = AIClient(
            api_url=self.config.api_url,
            api_key=self.config.api_key,
            model=self.config.model,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries
        )
        
        self.language_detector = LanguageDetector()
        
        # Title cleaner (for backward compatibility)
        self.title_cleaner = ArticleCleaner(
            ai_client=self.ai_client,
            batch_size=self.config.batch_size
        )
        
        # Content extractor
        self.content_extractor = ContentExtractor(
            timeout=self.config.timeout,
            max_content_length=max_content_length
        )
        
        # Content cleaner (for full articles)
        self.content_cleaner = ContentCleaner(
            ai_client=self.ai_client,
            batch_size=self.config.batch_size,
            max_content_length=max_content_length
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
            List of ProcessedArticle objects with translations and summaries
        """
        if not raw_articles:
            return []
        
        print(f"Processing {len(raw_articles)} articles with content extraction...")
        
        # Convert to dict format for processing
        articles_dict = [self._raw_to_dict(article) for article in raw_articles]
        
        # Step 1: Extract content from URLs (if enabled)
        if self.extract_content and self.config.enable_cleaning:
            print("Step 1/4: Extracting article content from URLs...")
            articles_dict = self._extract_content_batch(articles_dict)
        else:
            print("Step 1/4: Skipping content extraction (using titles only)...")
            for article in articles_dict:
                article['content'] = article['title']
                article['excerpt'] = article['title']
        
        # Step 2: Clean content with AI
        if self.config.enable_cleaning:
            print("Step 2/4: Cleaning and summarizing content...")
            articles_dict = self._clean_content_batch(articles_dict)
        else:
            # If cleaning disabled, use title as summary
            for article in articles_dict:
                article['title_cleaned'] = article['title']
                article['summary'] = article.get('content', article['title'])
        
        # Step 3: Translate summaries
        if self.config.enable_translation:
            print("Step 3/4: Translating summaries to 3 languages...")
            articles_dict = self._translate_summaries(articles_dict)
        else:
            # If translation disabled, use summary for all languages
            for article in articles_dict:
                summary = article.get('summary', article['title'])
                article['title_en'] = summary
                article['title_zh'] = summary
                article['title_ms'] = summary
                article['detected_language'] = 'unknown'
        
        # Step 4: Convert to ProcessedArticle objects
        print("Step 4/4: Finalizing...")
        processed = [self._dict_to_processed(article) for article in articles_dict]
        
        print(f"✓ Successfully processed {len(processed)} articles with content")
        return processed
    
    def _extract_content_batch(self, articles: List[dict]) -> List[dict]:
        """Extract content from URLs for all articles"""
        for article in articles:
            url = article.get('url')
            if url:
                print(f"  Extracting: {url[:60]}...")
                extracted = self.content_extractor.extract_with_fallback(
                    url,
                    fallback_title=article['title']
                )
                
                article['content'] = extracted.get('content', article['title'])
                article['excerpt'] = extracted.get('excerpt', article['title'])
                article['extracted_title'] = extracted.get('title', article['title'])
            else:
                # No URL, use title as content
                article['content'] = article['title']
                article['excerpt'] = article['title']
        
        return articles
    
    def _clean_content_batch(self, articles: List[dict]) -> List[dict]:
        """Clean and summarize article content"""
        # Prepare articles for content cleaning
        articles_for_cleaning = []
        for article in articles:
            articles_for_cleaning.append({
                'title': article['title'],
                'content': article.get('content', article['title']),
                'url': article.get('url')
            })
        
        # Clean in batches
        cleaned = self.content_cleaner.clean_articles_with_content(
            articles_for_cleaning,
            extract_content=False  # Already extracted
        )
        
        # Merge cleaned data back
        for article, cleaned_data in zip(articles, cleaned):
            article['title_cleaned'] = cleaned_data.get('title', article['title'])
            article['summary'] = cleaned_data.get('summary', article['title'])
            article['tags'] = cleaned_data.get('tags', [])
            article['country'] = cleaned_data.get('country', 'XX')
            article['news_date'] = cleaned_data.get('news_date', None)
        
        return articles
    
    def _translate_summaries(self, articles: List[dict]) -> List[dict]:
        """Translate article summaries to 3 languages"""
        # Use summary as the text to translate
        for article in articles:
            article['title'] = article.get('summary', article['title'])
        
        # Use existing translator
        translated = self.translator.translate_articles(articles)
        
        return translated
    
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
            metadata={
                **article_dict.get('metadata', {}),
                'content': article_dict.get('content', ''),
                'excerpt': article_dict.get('excerpt', ''),
                'summary': article_dict.get('summary', ''),
                'extracted_title': article_dict.get('extracted_title', ''),
                'tags': article_dict.get('tags', []),
                'country': article_dict.get('country', 'XX'),
                'news_date': article_dict.get('news_date', None)
            }
        )
    
    @classmethod
    def from_env(cls) -> "ArticleProcessorWithContent":
        """Create processor from environment variables"""
        config = AIConfig.from_env()
        return cls(config=config)
