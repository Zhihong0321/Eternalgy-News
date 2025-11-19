"""
Article data models
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict


@dataclass
class RawArticle:
    """
    Raw article from TrendRadar
    
    Input format from TrendRadar crawler
    """
    id: str
    title: str
    platform: str
    rank: int
    url: Optional[str] = None
    timestamp: Optional[datetime] = None
    metadata: Dict = field(default_factory=dict)


@dataclass
class ProcessedArticle:
    """
    Processed article with translations
    
    Output format after AI processing
    """
    # Original data
    news_id: str
    platform: str
    rank: int
    url: Optional[str]
    
    # Original title
    title_original: str
    
    # Cleaned title
    title_cleaned: str
    
    # Detected language
    detected_language: str
    
    # Translations (3 languages)
    title_en: str
    title_zh: str
    title_ms: str
    
    # Timestamps
    collected_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    
    # Metadata
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "news_id": self.news_id,
            "platform": self.platform,
            "rank": self.rank,
            "url": self.url,
            "title_original": self.title_original,
            "title_cleaned": self.title_cleaned,
            "detected_language": self.detected_language,
            "title_en": self.title_en,
            "title_zh": self.title_zh,
            "title_ms": self.title_ms,
            "collected_at": self.collected_at.isoformat() if self.collected_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "metadata": self.metadata
        }
