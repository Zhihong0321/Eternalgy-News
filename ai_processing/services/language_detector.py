"""
Language Detection Service
"""

import re
from typing import Optional


class LanguageDetector:
    """
    Fast heuristic-based language detection
    Supports: English, Chinese, Malay
    """
    
    # Character ranges
    CHINESE_PATTERN = re.compile(r'[\u4e00-\u9fff]')
    
    # Common Malay words
    MALAY_WORDS = {
        'yang', 'dan', 'untuk', 'dengan', 'ini', 'itu', 'adalah', 'pada',
        'akan', 'dari', 'ke', 'di', 'oleh', 'tidak', 'ada', 'juga',
        'kerana', 'atau', 'tetapi', 'jika', 'sebagai', 'dalam', 'telah'
    }
    
    def detect(self, text: str) -> str:
        """
        Detect language of text
        
        Args:
            text: Input text
        
        Returns:
            Language code: 'en', 'zh', 'ms', or 'unknown'
        """
        if not text or not text.strip():
            return 'unknown'
        
        text = text.lower().strip()
        
        # Check for Chinese characters
        chinese_chars = len(self.CHINESE_PATTERN.findall(text))
        if chinese_chars > 0:
            # If more than 30% Chinese characters, it's Chinese
            if chinese_chars / len(text) > 0.3:
                return 'zh'
        
        # Check for Malay words
        words = set(re.findall(r'\b\w+\b', text.lower()))
        malay_matches = len(words & self.MALAY_WORDS)
        
        if malay_matches >= 2:  # At least 2 Malay words
            return 'ms'
        
        # Default to English
        return 'en'
    
    def detect_batch(self, texts: list) -> list:
        """Detect language for multiple texts"""
        return [self.detect(text) for text in texts]
    
    def is_language(self, text: str, language: str) -> bool:
        """Check if text is in specific language"""
        return self.detect(text) == language
