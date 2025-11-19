"""
Example usage of AI Processing Module

This demonstrates how to integrate the module with TrendRadar
"""

from datetime import datetime
from ai_processing import ArticleProcessor, RawArticle


def example_basic_usage():
    """Basic usage example"""
    
    # Initialize processor with your API credentials
    processor = ArticleProcessor(
        api_url="https://api.bltcy.ai/v1/",
        api_key="sk-jW4WLdgCGCshSyFY9VbKXwj8y2YXclFHxw2x2WbXElFkcAlD",
        model="gpt-5-nano-2025-08-07"
    )
    
    # Create sample raw articles (from TrendRadar)
    raw_articles = [
        RawArticle(
            id="zhihu_001",
            title="华为发布新手机！！！点击查看详情>>>",
            platform="zhihu",
            rank=1,
            url="https://example.com/news1",
            timestamp=datetime.now()
        ),
        RawArticle(
            id="weibo_002",
            title="Tesla stock surges after earnings report",
            platform="weibo",
            rank=2,
            url="https://example.com/news2",
            timestamp=datetime.now()
        ),
        RawArticle(
            id="douyin_003",
            title="Kerajaan Malaysia umumkan dasar baharu",
            platform="douyin",
            rank=3,
            url="https://example.com/news3",
            timestamp=datetime.now()
        )
    ]
    
    # Process articles
    processed_articles = processor.process_articles(raw_articles)
    
    # Display results
    for article in processed_articles:
        print("\n" + "="*60)
        print(f"Platform: {article.platform} | Rank: #{article.rank}")
        print(f"Original: {article.title_original}")
        print(f"Cleaned:  {article.title_cleaned}")
        print(f"Language: {article.detected_language}")
        print(f"\nTranslations:")
        print(f"  🇬🇧 EN: {article.title_en}")
        print(f"  🇨🇳 ZH: {article.title_zh}")
        print(f"  🇲🇾 MS: {article.title_ms}")
    
    return processed_articles


def example_with_env_vars():
    """Example using environment variables"""
    
    # Set these environment variables:
    # AI_API_URL=https://api.bltcy.ai/v1/
    # AI_API_KEY=your-key
    # AI_MODEL=gpt-5-nano-2025-08-07
    
    processor = ArticleProcessor.from_env()
    
    # Process articles...
    # (same as above)


def example_integration_with_trendradar():
    """
    Example of how to integrate with TrendRadar main.py
    """
    
    # In TrendRadar's main.py, after filtering news:
    
    # 1. Import the processor
    from ai_processing import ArticleProcessor, RawArticle
    
    # 2. Initialize processor
    processor = ArticleProcessor(
        api_url="https://api.bltcy.ai/v1/",
        api_key="your-api-key",
        model="gpt-5-nano-2025-08-07"
    )
    
    # 3. Convert TrendRadar news to RawArticle format
    # Assuming filtered_news is a list of dicts from TrendRadar
    filtered_news = [
        {"id": "zhihu_001", "title": "华为新手机", "platform": "zhihu", "rank": 1}
    ]
    
    raw_articles = [
        RawArticle(
            id=news['id'],
            title=news['title'],
            platform=news['platform'],
            rank=news['rank'],
            url=news.get('url'),
            timestamp=datetime.now()
        )
        for news in filtered_news
    ]
    
    # 4. Process articles
    processed = processor.process_articles(raw_articles)
    
    # 5. Convert back to dict for saving
    processed_dicts = [article.to_dict() for article in processed]
    
    # 6. Save to Railway DB or output files
    # save_to_database(processed_dicts)
    # save_to_json(processed_dicts)
    
    return processed_dicts


if __name__ == "__main__":
    print("AI Processing Module - Example Usage")
    print("="*60)
    
    # Run basic example
    # Note: Replace API key with your actual key
    # example_basic_usage()
    
    print("\nTo run this example:")
    print("1. Replace the API key with your actual key")
    print("2. Uncomment the example_basic_usage() call")
    print("3. Run: python -m ai_processing.example_usage")
