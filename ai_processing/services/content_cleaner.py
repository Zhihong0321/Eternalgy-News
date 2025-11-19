"""
Content Cleaning Service
Cleans full article content (not just titles)
"""

from typing import List, Dict, Optional
from .ai_client import AIClient


class ContentCleaner:
    """
    Clean and summarize full article content using AI
    
    This service processes the full article text extracted from URLs,
    not just the title. It can:
    - Remove ads and promotional content
    - Extract key information
    - Create summaries
    - Clean up formatting
    """
    
    # Function calling schema for structured output
    CLEANING_FUNCTION_SCHEMA = {
        "name": "clean_news_article",
        "description": "Clean and structure a news article with tags, country, date, and bullet points",
        "parameters": {
            "type": "object",
            "properties": {
                "tags": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["Solar", "Wind", "EV", "Big Project", "Tech", "Policy", "Finance", "Storage"]
                    },
                    "description": "Select up to 3 most relevant tags",
                    "maxItems": 3
                },
                "country": {
                    "type": "string",
                    "description": "2-letter country code of news origin (e.g., MY, SG, CN, US, TH, ID, PH)",
                    "pattern": "^[A-Z]{2}$"
                },
                "news_date": {
                    "type": "string",
                    "description": "Date of the news in YYYY-MM-DD format. Extract from article content or metadata.",
                    "pattern": "^\\d{4}-\\d{2}-\\d{2}$"
                },
                "bullets": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "3-5 clean bullet points, each containing ONE clear factual statement. No ads, filler, or promotional content.",
                    "minItems": 3,
                    "maxItems": 5
                }
            },
            "required": ["tags", "country", "news_date", "bullets"]
        }
    }
    
    CONTENT_CLEANING_PROMPT = """You are a professional news editor for a clean, ad-free news portal.

Article Title: {title}

Article Content:
{content}

Your tasks:
1. Remove ALL ads, promotional content, filler text, clickbait, and irrelevant information
2. Extract ONLY the core facts and news information
3. Create 3-5 clean bullet points, each with ONE clear factual statement
4. Select up to 3 most relevant tags from: Solar, Wind, EV, Big Project, Tech, Policy, Finance, Storage
5. Identify the origin country (2-letter code: MY, SG, CN, US, TH, ID, PH, etc.)
6. Extract the news date from the article (YYYY-MM-DD format). Look for dates in the content.
7. Maintain the original language

Return in this EXACT format:
TAGS: [tag1, tag2, tag3]
COUNTRY: [XX]
NEWS_DATE: [YYYY-MM-DD]
BULLETS:
• [First key fact]
• [Second key fact]
• [Third key fact]

Focus on facts only. No fluff, no repetition, no promotional language."""
    
    BATCH_CLEANING_PROMPT = """You are a professional news editor for a clean, ad-free news portal. Process these articles:

{articles}

For EACH article:
1. Remove ALL ads, promotional content, filler text, clickbait
2. Extract ONLY core facts into 3-5 bullet points
3. Each bullet = ONE clear factual statement
4. Select up to 3 tags from: Solar, Wind, EV, Big Project, Tech, Policy, Finance, Storage
5. Identify origin country (2-letter code: MY, SG, CN, US, TH, ID, PH, etc.)
6. Extract news date (YYYY-MM-DD format). Look for dates in content and convert them.
7. Maintain original language

Return in this EXACT format for each article:

ARTICLE 1:
TAGS: [tag1, tag2, tag3]
COUNTRY: [XX]
NEWS_DATE: [YYYY-MM-DD]
BULLETS:
• [Fact 1]
• [Fact 2]
• [Fact 3]

ARTICLE 2:
TAGS: [tag1, tag2]
COUNTRY: [XX]
NEWS_DATE: [YYYY-MM-DD]
BULLETS:
• [Fact 1]
• [Fact 2]"""
    
    def __init__(
        self,
        ai_client: AIClient,
        batch_size: int = 5,
        max_content_length: int = 3000
    ):
        """
        Initialize content cleaner
        
        Args:
            ai_client: AI client for API calls
            batch_size: Number of articles to process in one batch
            max_content_length: Max content length to send to AI (chars)
        """
        self.ai_client = ai_client
        self.batch_size = batch_size
        self.max_content_length = max_content_length
    
    def clean_single(
        self,
        title: str,
        content: str,
        url: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Clean a single article's content
        
        Args:
            title: Article title
            content: Article content
            url: Article URL (optional)
        
        Returns:
            Dict with 'title', 'summary', 'original_content'
        """
        # Truncate content if too long
        truncated_content = content[:self.max_content_length]
        if len(content) > self.max_content_length:
            truncated_content += "..."
        
        prompt = self.CONTENT_CLEANING_PROMPT.format(
            title=title,
            content=truncated_content
        )
        
        messages = [
            {"role": "system", "content": "You are a professional news editor for a clean, ad-free news portal."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            # Use function calling for structured output
            response = self.ai_client.chat_completion_with_functions(
                messages=messages,
                functions=[self.CLEANING_FUNCTION_SCHEMA],
                function_call={"name": "clean_news_article"},
                temperature=0.3
            )
            
            # Extract function call arguments (structured JSON)
            parsed = self.ai_client.extract_function_arguments(response)
            
            if not parsed:
                # Fallback to regular parsing if function calling not supported
                response_text = self.ai_client.extract_content(response).strip()
                parsed = self._parse_enhanced_response(response_text)
            
            # Format bullets as text
            bullets_list = parsed.get('bullets', [])
            bullets_text = '\n'.join([f"• {b}" for b in bullets_list])
            
            return {
                'title': title,
                'summary': bullets_text,
                'tags': parsed.get('tags', []),
                'country': parsed.get('country', 'XX'),
                'news_date': parsed.get('news_date', None),
                'bullets': bullets_text,
                'original_content': content,
                'url': url
            }
        
        except Exception as e:
            print(f"Error cleaning content: {e}")
            # Fallback: return title as summary
            return {
                'title': title,
                'summary': title,
                'original_content': content,
                'url': url
            }
    
    def clean_batch(self, articles: List[Dict]) -> List[Dict]:
        """
        Clean multiple articles' content
        
        Args:
            articles: List of dicts with 'title' and 'content' keys
        
        Returns:
            List of dicts with 'summary' added
        """
        if not articles:
            return []
        
        # Format articles for batch processing
        articles_text = []
        for i, article in enumerate(articles, 1):
            title = article.get('title', 'Untitled')
            content = article.get('content', '')
            
            # Truncate content
            truncated = content[:self.max_content_length]
            if len(content) > self.max_content_length:
                truncated += "..."
            
            articles_text.append(
                f"Article {i}:\nTitle: {title}\nContent: {truncated}\n"
            )
        
        prompt = self.BATCH_CLEANING_PROMPT.format(
            articles="\n".join(articles_text)
        )
        
        messages = [
            {"role": "system", "content": "You are a professional news editor."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            # Try function calling first (more reliable)
            response = self.ai_client.chat_completion_with_functions(
                messages=messages,
                functions=[self.CLEANING_FUNCTION_SCHEMA],
                function_call={"name": "clean_news_article"},
                temperature=0.3
            )
            
            # Check if function calling worked
            parsed_data = self.ai_client.extract_function_arguments(response)
            
            if parsed_data:
                # Function calling succeeded - use structured data
                bullets_list = parsed_data.get('bullets', [])
                bullets_text = '\n'.join([f"• {b}" for b in bullets_list])
                
                parsed_articles = [{
                    'tags': parsed_data.get('tags', []),
                    'country': parsed_data.get('country', 'XX'),
                    'news_date': parsed_data.get('news_date', None),
                    'bullets': bullets_text
                }]
            else:
                # Fallback to text parsing
                content = self.ai_client.extract_content(response)
                parsed_articles = self._parse_batch_response(content, len(articles))
            
            # Add parsed data to articles
            for article, parsed in zip(articles, parsed_articles):
                article['summary'] = parsed['bullets']
                article['tags'] = parsed['tags']
                article['country'] = parsed['country']
                article['news_date'] = parsed.get('news_date', None)
                article['bullets'] = parsed['bullets']
            
            return articles
        
        except Exception as e:
            print(f"Error cleaning batch: {e}")
            # Fallback: use titles as summaries
            for article in articles:
                article['summary'] = article.get('title', '')
            return articles
    
    def _parse_enhanced_response(self, content: str) -> Dict:
        """Parse enhanced response with tags, country, date, and bullets"""
        lines = content.strip().split('\n')
        
        tags = []
        country = ''
        news_date = None
        bullets = []
        
        in_bullets = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('TAGS:'):
                # Extract tags
                tags_str = line.replace('TAGS:', '').strip()
                tags_str = tags_str.strip('[]')
                tags = [t.strip() for t in tags_str.split(',') if t.strip()]
            
            elif line.startswith('COUNTRY:'):
                # Extract country
                country = line.replace('COUNTRY:', '').strip().strip('[]').upper()
            
            elif line.startswith('NEWS_DATE:') or line.startswith('DATE:'):
                # Extract date
                date_str = line.replace('NEWS_DATE:', '').replace('DATE:', '').strip().strip('[]')
                if date_str and date_str != 'Not available':
                    news_date = date_str
            
            elif line.startswith('BULLETS:'):
                in_bullets = True
            
            elif in_bullets and (line.startswith('•') or line.startswith('-') or line.startswith('*')):
                # Extract bullet point
                bullet = line.lstrip('•-* ').strip()
                if bullet:
                    bullets.append(bullet)
        
        # Format bullets as text
        bullets_text = '\n'.join([f"• {b}" for b in bullets]) if bullets else content
        
        return {
            'tags': tags[:3],  # Max 3 tags
            'country': country[:2] if country else 'XX',  # 2-letter code
            'news_date': news_date,
            'bullets': bullets_text
        }
    
    def _parse_batch_response(self, content: str, expected_count: int) -> List[Dict]:
        """Parse batch response with multiple articles"""
        articles = []
        current_article = None
        in_bullets = False
        
        lines = content.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for article marker
            if line.startswith('ARTICLE'):
                if current_article:
                    articles.append(current_article)
                current_article = {'tags': [], 'country': 'XX', 'news_date': None, 'bullets': []}
                in_bullets = False
            
            elif current_article:
                if line.startswith('TAGS:'):
                    tags_str = line.replace('TAGS:', '').strip().strip('[]')
                    current_article['tags'] = [t.strip() for t in tags_str.split(',') if t.strip()][:3]
                
                elif line.startswith('COUNTRY:'):
                    current_article['country'] = line.replace('COUNTRY:', '').strip().strip('[]').upper()[:2]
                
                elif line.startswith('NEWS_DATE:') or line.startswith('DATE:'):
                    date_str = line.replace('NEWS_DATE:', '').replace('DATE:', '').strip().strip('[]')
                    if date_str and date_str != 'Not available' and date_str != 'N/A':
                        current_article['news_date'] = date_str
                
                elif line.startswith('BULLETS:'):
                    in_bullets = True
                
                elif in_bullets and (line.startswith('•') or line.startswith('-') or line.startswith('*')):
                    bullet = line.lstrip('•-* ').strip()
                    if bullet:
                        current_article['bullets'].append(bullet)
        
        # Add last article
        if current_article:
            articles.append(current_article)
        
        # Format bullets as text for each article
        for article in articles:
            bullets_list = article.get('bullets', [])
            article['bullets'] = '\n'.join([f"• {b}" for b in bullets_list]) if bullets_list else ''
        
        # Ensure we have the right number
        while len(articles) < expected_count:
            articles.append({'tags': [], 'country': 'XX', 'news_date': None, 'bullets': ''})
        
        return articles[:expected_count]
    
    def _parse_summaries(self, content: str, expected_count: int) -> List[str]:
        """Parse AI response to extract summaries (legacy method)"""
        lines = [line.strip() for line in content.strip().split('\n') if line.strip()]
        
        summaries = []
        for line in lines:
            # Remove numbering if present (e.g., "1. Summary" -> "Summary")
            if '. ' in line:
                parts = line.split('. ', 1)
                if len(parts) == 2 and parts[0].isdigit():
                    summaries.append(parts[1])
                else:
                    summaries.append(line)
            else:
                summaries.append(line)
        
        # Ensure we have the right number of summaries
        while len(summaries) < expected_count:
            summaries.append("")
        
        return summaries[:expected_count]
    
    def clean_articles_with_content(
        self,
        articles: List[Dict],
        extract_content: bool = True
    ) -> List[Dict]:
        """
        Clean articles with full content extraction
        
        Args:
            articles: List of article dicts with 'title', 'content', 'url'
            extract_content: Whether to extract content from URLs
        
        Returns:
            List of articles with 'summary' and 'content_cleaned' added
        """
        # Process in batches
        all_results = []
        
        for i in range(0, len(articles), self.batch_size):
            batch = articles[i:i + self.batch_size]
            
            print(f"Cleaning content batch {i//self.batch_size + 1}...")
            cleaned_batch = self.clean_batch(batch)
            all_results.extend(cleaned_batch)
        
        return all_results
