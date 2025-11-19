"""
Article Translation Service with Function Calling
"""

from typing import List, Dict, Optional
from .ai_client import AIClient
from .language_detector import LanguageDetector


class ArticleTranslator:
    """
    Translate articles to multiple languages using AI function calling
    Supports: English, Chinese, Malay
    """
    
    # Function definition for OpenAI function calling
    TRANSLATION_FUNCTION = {
        "name": "translate_article",
        "description": "Translate a news article title to English, Chinese, and Malay",
        "parameters": {
            "type": "object",
            "properties": {
                "title_en": {
                    "type": "string",
                    "description": "English translation of the title"
                },
                "title_zh": {
                    "type": "string",
                    "description": "Chinese (Simplified) translation of the title"
                },
                "title_ms": {
                    "type": "string",
                    "description": "Malay (Bahasa Melayu) translation of the title"
                },
                "detected_language": {
                    "type": "string",
                    "enum": ["en", "zh", "ms", "other"],
                    "description": "Detected original language of the title"
                }
            },
            "required": ["title_en", "title_zh", "title_ms", "detected_language"]
        }
    }
    
    TRANSLATION_PROMPT = """Translate this news title to English, Chinese (Simplified), and Malay.

Title: {title}

Requirements:
1. Keep translations accurate and natural
2. Maintain the news tone (professional, factual)
3. Preserve key information (names, numbers, dates)
4. Use proper terminology for each language
5. If the title is already in one of the target languages, keep it as-is for that language

Call the translate_article function with all three translations."""
    
    def __init__(
        self,
        ai_client: AIClient,
        language_detector: LanguageDetector,
        skip_same_language: bool = True
    ):
        self.ai_client = ai_client
        self.language_detector = language_detector
        self.skip_same_language = skip_same_language
    
    def translate_single(self, title: str, detected_lang: Optional[str] = None) -> Dict[str, str]:
        """
        Translate a single title to all target languages
        
        Args:
            title: Title to translate
            detected_lang: Pre-detected language (optional)
        
        Returns:
            Dict with keys: title_en, title_zh, title_ms, detected_language
        """
        # Detect language if not provided
        if not detected_lang:
            detected_lang = self.language_detector.detect(title)
        
        prompt = self.TRANSLATION_PROMPT.format(title=title)
        
        messages = [
            {"role": "system", "content": "You are a professional translator specializing in news translation."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.ai_client.chat_completion(
                messages=messages,
                temperature=0.3,
                functions=[self.TRANSLATION_FUNCTION],
                function_call={"name": "translate_article"}
            )
            
            function_call = self.ai_client.extract_function_call(response)
            
            if function_call and function_call["name"] == "translate_article":
                translations = function_call["arguments"]
                
                # If skip_same_language is enabled, use original for detected language
                if self.skip_same_language and detected_lang in ["en", "zh", "ms"]:
                    translations[f"title_{detected_lang}"] = title
                
                translations["detected_language"] = detected_lang
                return translations
            
            # Fallback if function calling fails
            return self._fallback_translation(title, detected_lang)
        
        except Exception as e:
            print(f"Error translating title: {e}")
            return self._fallback_translation(title, detected_lang)
    
    def _fallback_translation(self, title: str, detected_lang: str) -> Dict[str, str]:
        """Fallback when translation fails - use original for all"""
        return {
            "title_en": title,
            "title_zh": title,
            "title_ms": title,
            "detected_language": detected_lang
        }
    
    def translate_batch(self, titles: List[str]) -> List[Dict[str, str]]:
        """
        Translate multiple titles
        
        Args:
            titles: List of titles to translate
        
        Returns:
            List of translation dicts
        """
        results = []
        
        for title in titles:
            translation = self.translate_single(title)
            results.append(translation)
        
        return results
    
    def translate_articles(self, articles: List[Dict]) -> List[Dict]:
        """
        Translate titles for multiple articles
        
        Args:
            articles: List of article dicts with 'title_cleaned' key
        
        Returns:
            List of articles with translation fields added
        """
        for article in articles:
            title = article.get('title_cleaned', article.get('title', ''))
            
            if not title:
                continue
            
            # Detect language
            detected_lang = self.language_detector.detect(title)
            article['detected_language'] = detected_lang
            
            # Translate
            translations = self.translate_single(title, detected_lang)
            
            # Add translations to article
            article['title_en'] = translations['title_en']
            article['title_zh'] = translations['title_zh']
            article['title_ms'] = translations['title_ms']
        
        return articles
