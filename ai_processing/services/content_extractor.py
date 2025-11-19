"""
Content Extractor Service
Extracts article content from URLs using readability
"""

import requests
from typing import Optional, Dict
from readability import Document
from bs4 import BeautifulSoup


class ContentExtractor:
    """
    Extract article content from URLs
    
    Uses readability-lxml (Python port of Mozilla's Readability)
    to extract clean article content from web pages
    """
    
    def __init__(
        self,
        timeout: int = 10,
        max_content_length: int = 5000,
        user_agent: str = None
    ):
        """
        Initialize content extractor
        
        Args:
            timeout: Request timeout in seconds
            max_content_length: Maximum content length to extract (characters)
            user_agent: Custom user agent string
        """
        self.timeout = timeout
        self.max_content_length = max_content_length
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )
    
    def extract_content(self, url: str) -> Optional[Dict[str, str]]:
        """
        Extract article content from URL
        
        Args:
            url: Article URL
        
        Returns:
            Dict with 'title', 'content', 'excerpt' or None if failed
        """
        try:
            # Fetch the page
            headers = {
                'User-Agent': self.user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }
            
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            # Use readability to extract content
            # Pass text instead of bytes to avoid regex issues
            doc = Document(response.text)
            
            # Get title
            title = doc.title()
            
            # Get content HTML
            content_html = doc.summary()
            
            # Convert HTML to plain text
            soup = BeautifulSoup(content_html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text
            content_text = soup.get_text(separator=' ', strip=True)
            
            # Clean up whitespace
            content_text = ' '.join(content_text.split())
            
            # Truncate if too long
            if len(content_text) > self.max_content_length:
                content_text = content_text[:self.max_content_length] + "..."
            
            # Create excerpt (first 200 chars)
            excerpt = content_text[:200] + "..." if len(content_text) > 200 else content_text
            
            return {
                'title': title,
                'content': content_text,
                'excerpt': excerpt,
                'url': url
            }
            
        except requests.RequestException as e:
            print(f"Failed to fetch URL {url}: {e}")
            return None
        except Exception as e:
            print(f"Failed to extract content from {url}: {e}")
            return None
    
    def extract_batch(self, urls: list) -> Dict[str, Optional[Dict]]:
        """
        Extract content from multiple URLs
        
        Args:
            urls: List of URLs
        
        Returns:
            Dict mapping URL to extracted content (or None if failed)
        """
        results = {}
        
        for url in urls:
            print(f"Extracting content from: {url}")
            results[url] = self.extract_content(url)
        
        return results
    
    def extract_with_fallback(self, url: str, fallback_title: str = "") -> Dict[str, str]:
        """
        Extract content with fallback to title only
        
        Args:
            url: Article URL
            fallback_title: Title to use if extraction fails
        
        Returns:
            Dict with content (or just title if extraction failed)
        """
        extracted = self.extract_content(url)
        
        if extracted:
            return extracted
        
        # Fallback: return just the title
        return {
            'title': fallback_title,
            'content': fallback_title,
            'excerpt': fallback_title,
            'url': url
        }
