"""
Adapter to make ArticleProcessorWithContent compatible with ProcessorWorker
"""

from .processor_with_content import ArticleProcessorWithContent
from .models.article import RawArticle
from datetime import datetime


class ProcessorAdapter:
    """
    Adapter that wraps ArticleProcessorWithContent to provide
    the process(url) interface expected by ProcessorWorker
    """
    
    def __init__(self, processor: ArticleProcessorWithContent):
        self.processor = processor
    
    def process(self, url: str, title: str = "") -> dict:
        """
        Process a URL and return result in format expected by ProcessorWorker
        
        Args:
            url: URL to process
            title: Optional title from search result
        
        Returns:
            Dictionary with success, title, content, translated_content, metadata
        """
        try:
            # Create a RawArticle object
            raw_article = RawArticle(
                id=0,  # Will be set by database
                title=title or "",  # Use provided title
                platform="web",
                rank=1,
                url=url,
                timestamp=datetime.now()
            )
            
            # Process through the full pipeline
            results = self.processor.process_articles([raw_article])
            
            if not results:
                return {"success": False, "error": "No result returned"}
            
            result = results[0]
            
            # Convert to expected format
            metadata = result.metadata
            
            # Get content - prefer summary (bullet points), fall back to full content
            content = metadata.get('summary', '') or metadata.get('content', '')
            
            # Extract other fields
            tags = metadata.get('tags', [])
            country = metadata.get('country', 'XX')
            news_date = metadata.get('news_date')
            
            # Build translated_content JSON string with summary translations (fallback to title translations)
            import json
            summary_translations = metadata.get('summary_translations')

            if summary_translations and isinstance(summary_translations, dict):
                translated_content_dict = {
                    "en": summary_translations.get('en', ''),
                    "zh": summary_translations.get('zh', ''),
                    "ms": summary_translations.get('ms', '')
                }
            else:
                translated_content_dict = {
                    "en": result.title_en or "",
                    "zh": result.title_zh or "",
                    "ms": result.title_ms or ""
                }

            translated_content = json.dumps(translated_content_dict, ensure_ascii=False)
            
            return {
                "success": True,
                "title": result.title_original or title,
                "content": content,
                "translated_content": translated_content,
                "title_en": translated_content_dict.get("en", ""),
                "title_zh": translated_content_dict.get("zh", ""),
                "title_ms": translated_content_dict.get("ms", ""),
                "tags": tags,
                "country": country,
                "news_date": news_date,
                "blocked": metadata.get('blocked', False),
                "block_reason": metadata.get('block_reason'),
                "metadata": {
                    "detected_language": result.detected_language,
                    "translations": translated_content_dict,
                    "source": url.split('/')[2] if '/' in url else url,
                    "content_length": len(content),
                    "summary": metadata.get('summary', ''),
                    "bullets": metadata.get('bullets', ''),
                    "full_content": metadata.get('content', ''),
                    "blocked": metadata.get('blocked', False),
                    "block_reason": metadata.get('block_reason')
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
