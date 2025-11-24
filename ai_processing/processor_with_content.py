"""
Enhanced Article Processor with Content Extraction
Orchestrates content extraction, cleaning, and translation pipeline
"""

from datetime import datetime
from typing import List, Optional
import os
from .config import AIConfig
from .models.article import RawArticle, ProcessedArticle
from .services.ai_client import AIClient
from .services.cleaner import ArticleCleaner
from .services.formatting import strip_bbcode
from .services.jina_reader import JinaReader, JinaReaderConfig
from .services.news_rewriter import NewsRewriter
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
        max_content_length: int = 3000,
        jina_reader_config: Optional[JinaReaderConfig] = None,
        jina_api_key: Optional[str] = None
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

        # Separate client for rewrites (default to OpenRouter free model unless overridden)
        rewriter_api_url = os.getenv("REWRITER_API_URL", "https://openrouter.ai/api/v1")
        rewriter_api_key = os.getenv("REWRITER_API_KEY") or os.getenv("AI_API_KEY", "")
        rewriter_model = os.getenv("REWRITER_MODEL", "openai/gpt-oss-20b:free")
        self.rewriter_client = AIClient(
            api_url=rewriter_api_url,
            api_key=rewriter_api_key,
            model=rewriter_model,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries
        )
        
        self.language_detector = LanguageDetector()
        
        # Title cleaner (for backward compatibility)
        self.title_cleaner = ArticleCleaner(
            ai_client=self.ai_client,
            batch_size=self.config.batch_size
        )
        
        # Reader for fetching article copy
        if jina_reader_config:
            self.jina_reader_config = jina_reader_config
        else:
            self.jina_reader_config = JinaReaderConfig(
                api_key=jina_api_key or "",
                timeout=self.config.timeout,
                max_content_length=max_content_length
            )

        self.jina_reader = JinaReader(config=self.jina_reader_config)
        
        # News Rewriter (handles BBcode summary + translations)
        self.news_rewriter = NewsRewriter(
            ai_client=self.rewriter_client,
            temperature=0.3,
            max_tokens=1200
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

        articles_dict = self._apply_rewriter_titles(articles_dict)
        
        # Step 4: Convert to ProcessedArticle objects
        print("Step 4/4: Finalizing...")
        processed = [self._dict_to_processed(article) for article in articles_dict]
        
        print(f"✓ Successfully processed {len(processed)} articles with content")
        return processed
    
    def _get_domain(self, url: str) -> str:
        """Extract domain from URL using urllib."""
        from urllib.parse import urlparse
        parsed = urlparse(url or "")
        domain = parsed.netloc.lower().replace("www.", "")
        return domain

    def _extract_content_batch(self, articles: List[dict]) -> List[dict]:
        """Extract content from URLs for all articles using the search-backed reader."""
        for article in articles:
            url = article.get('url')
            metadata = article.get('metadata') or {}
            article['metadata'] = metadata

            if url:
                print(f"  Extracting via reader: {url[:60]}...")
                extracted = self.jina_reader.read_url(url)

                if extracted and extracted.get('content'):
                    article['content'] = extracted.get('content')
                    article['excerpt'] = extracted.get('excerpt')
                    article['extracted_title'] = extracted.get('title', article['title'])
                    article['source_description'] = extracted.get('description')
                else:
                    article['content'] = article.get('title', '')
                    article['excerpt'] = article.get('title', '')
                    metadata['blocked'] = extracted.get('blocked', False) if isinstance(extracted, dict) else False
                    metadata['block_reason'] = extracted.get('error') if isinstance(extracted, dict) else "Reader failed"
                    metadata['block_status'] = extracted.get('status_code') if isinstance(extracted, dict) else None
                    metadata['block_domain'] = self._get_domain(url)
                    metadata['original_url'] = url
            else:
                article['content'] = article.get('title', '')
                article['excerpt'] = article.get('title', '')

        return articles
    
    def _clean_content_batch(self, articles: List[dict]) -> List[dict]:
        """Rewrite article content via the Jina Reader + News Rewriter prompt."""
        for article in articles:
            original_content = article.get('content', '')
            title = article.get('title', '')
            url = article.get('url', '')
            date_str = self._format_article_date(article)

            if not original_content:
                article['summary'] = title
                article['translated_summary'] = {
                    'en': title,
                    'zh': title,
                    'ms': title
                }
                article['tags'] = article.get('tags', [])
                article['news_date'] = date_str or article.get('news_date')
                continue

            rewrite_result = self.news_rewriter.rewrite(
                title=title,
                date=date_str or "N/A",
                url=url,
                content=original_content
            )

            english_summary = rewrite_result.get('news content (en)', original_content)
            chinese_summary = rewrite_result.get('news content (zh-cn)', '')
            malay_summary = rewrite_result.get('news content (my)', '')
            tags = rewrite_result.get('tags (pick 3)', [])
            news_date = rewrite_result.get('news date') or date_str

            article['summary'] = english_summary
            article['content'] = english_summary
            article['summary_plain'] = strip_bbcode(english_summary)
            article['translated_summary'] = {
                'en': english_summary,
                'zh': chinese_summary or english_summary,
                'ms': malay_summary or english_summary
            }
            article['tags'] = tags
            article['news_date'] = news_date
            rewriter_titles = {
                'en': rewrite_result.get('title_en'),
                'zh': rewrite_result.get('title_zh'),
                'ms': rewrite_result.get('title_ms')
            }
            english_title = rewriter_titles['en'] or strip_bbcode(english_summary)
            chinese_title = rewriter_titles['zh'] or strip_bbcode(chinese_summary or english_summary)
            malay_title = rewriter_titles['ms'] or strip_bbcode(malay_summary or english_summary)
            article['title_en'] = english_title
            article['title_zh'] = chinese_title
            article['title_ms'] = malay_title
            article['rewriter_titles'] = {
                'en': english_title,
                'zh': chinese_title,
                'ms': malay_title
            }
            metadata_existing = article.get('metadata', {})
            metadata_existing.update({
                'translated_summary': article['translated_summary'],
                'summary': english_summary,
                'summary_plain': article.get('summary_plain', strip_bbcode(english_summary)),
                'excerpt': article.get('excerpt', ''),
                'tags': tags,
                'country': article.get('country', metadata_existing.get('country', 'XX')),
                'news_date': news_date,
                'rewriter_titles': article['rewriter_titles']
            })
            article['metadata'] = metadata_existing

        return articles
    
    def _translate_summaries(self, articles: List[dict]) -> List[dict]:
        """Translate article summaries to 3 languages"""
        original_titles = []

        # Use summary as the text to translate, but preserve original title
        for article in articles:
            original_titles.append(article.get('title', ''))
            article['title'] = article.get('summary', article.get('title', ''))

        # Use existing translator
        translated = self.translator.translate_articles(articles)

        # Restore original title so downstream logic sees the real headline
        for article, original in zip(translated, original_titles):
            article['title'] = original

        return translated

    def _apply_rewriter_titles(self, articles: List[dict]) -> List[dict]:
        """Ensure any titles provided by the News Rewriter take precedence."""
        for article in articles:
            rewriter_titles = article.get('rewriter_titles')
            if not rewriter_titles:
                continue

            en_title = rewriter_titles.get('en')
            if en_title:
                article['title_en'] = en_title
                article['title_cleaned'] = en_title
            zh_title = rewriter_titles.get('zh')
            if zh_title:
                article['title_zh'] = zh_title
            ms_title = rewriter_titles.get('ms')
            if ms_title:
                article['title_ms'] = ms_title

        return articles

    def _format_article_date(self, article: dict) -> str:
        """Return ISO date string from article timestamp if available."""
        timestamp = article.get('timestamp')
        if hasattr(timestamp, "isoformat"):
            return timestamp.isoformat()
        if isinstance(timestamp, str):
            return timestamp
        return ""
    
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
                'news_date': article_dict.get('news_date', None),
                'summary_translations': article_dict.get('translated_summary', {})
            }
        )
    
    @classmethod
    def from_env(cls) -> "ArticleProcessorWithContent":
        """Create processor from environment variables"""
        config = AIConfig.from_env()
        return cls(config=config)
