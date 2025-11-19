"""
Article Cleaning Service
"""

from typing import List, Dict
from .ai_client import AIClient


class ArticleCleaner:
    """
    Clean and edit article titles using AI
    Removes clickbait, ads, excessive punctuation, etc.
    """
    
    CLEANING_PROMPT = """You are a professional news editor. Clean these news titles by:
1. Remove clickbait phrases (e.g., "你不会相信", "震惊", "必看")
2. Remove excessive punctuation (!!!, ???, >>>)
3. Remove promotional text (e.g., "点击查看", "立即购买", "Click here")
4. Remove emojis and special symbols
5. Keep it factual and professional
6. Maintain the original language
7. Keep the core news information

Return ONLY the cleaned titles, one per line, in the same order.

Titles to clean:
{titles}

Cleaned titles:"""
    
    def __init__(self, ai_client: AIClient, batch_size: int = 10):
        self.ai_client = ai_client
        self.batch_size = batch_size
    
    def clean_single(self, title: str) -> str:
        """
        Clean a single title
        
        Args:
            title: Original title
        
        Returns:
            Cleaned title
        """
        return self.clean_batch([title])[0]
    
    def clean_batch(self, titles: List[str]) -> List[str]:
        """
        Clean multiple titles in one API call
        
        Args:
            titles: List of original titles
        
        Returns:
            List of cleaned titles
        """
        if not titles:
            return []
        
        # Join titles with numbering for clarity
        numbered_titles = "\n".join([f"{i+1}. {title}" for i, title in enumerate(titles)])
        
        prompt = self.CLEANING_PROMPT.format(titles=numbered_titles)
        
        messages = [
            {"role": "system", "content": "You are a professional news editor."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.ai_client.chat_completion(
                messages=messages,
                temperature=0.3,  # Lower temperature for consistent cleaning
                max_tokens=500
            )
            
            content = self.ai_client.extract_content(response)
            
            # Parse cleaned titles
            cleaned = self._parse_cleaned_titles(content, len(titles))
            
            # Fallback: if parsing fails, return originals
            if len(cleaned) != len(titles):
                return titles
            
            return cleaned
        
        except Exception as e:
            print(f"Error cleaning titles: {e}")
            # Fallback: return original titles
            return titles
    
    def _parse_cleaned_titles(self, content: str, expected_count: int) -> List[str]:
        """Parse AI response to extract cleaned titles"""
        lines = [line.strip() for line in content.strip().split('\n') if line.strip()]
        
        cleaned = []
        for line in lines:
            # Remove numbering if present (e.g., "1. Title" -> "Title")
            if '. ' in line:
                parts = line.split('. ', 1)
                if len(parts) == 2 and parts[0].isdigit():
                    cleaned.append(parts[1])
                else:
                    cleaned.append(line)
            else:
                cleaned.append(line)
        
        return cleaned[:expected_count]
    
    def clean_articles(self, articles: List[Dict]) -> List[Dict]:
        """
        Clean titles for multiple articles
        
        Args:
            articles: List of article dicts with 'title' key
        
        Returns:
            List of articles with 'title_cleaned' added
        """
        titles = [article['title'] for article in articles]
        
        # Process in batches
        all_cleaned = []
        for i in range(0, len(titles), self.batch_size):
            batch = titles[i:i + self.batch_size]
            cleaned_batch = self.clean_batch(batch)
            all_cleaned.extend(cleaned_batch)
        
        # Add cleaned titles to articles
        for article, cleaned_title in zip(articles, all_cleaned):
            article['title_cleaned'] = cleaned_title
        
        return articles
