# AI Processing Module for TrendRadar

Independent module for processing news articles with AI-powered cleaning and multi-language translation.

## Features

- ✅ **AI-Powered Cleaning**: Remove clickbait, ads, excessive punctuation
- ✅ **Multi-Language Translation**: Translate to English, Chinese, Malay
- ✅ **Smart Language Detection**: Heuristic-based, fast and accurate
- ✅ **Function Calling**: Structured output using OpenAI function calling
- ✅ **Skip Same Language**: Don't re-translate if already in target language
- ✅ **Batch Processing**: Process multiple articles efficiently
- ✅ **Error Handling**: Robust fallback mechanisms
- ✅ **Independent**: Can be used standalone or with TrendRadar

## Installation

```bash
pip install requests
```

## Quick Start

```python
from ai_processing import ArticleProcessor, RawArticle
from datetime import datetime

# Initialize processor
processor = ArticleProcessor(
    api_url="https://api.bltcy.ai/v1/",
    api_key="your-api-key",
    model="gpt-5-nano-2025-08-07"
)

# Create raw article
article = RawArticle(
    id="news_001",
    title="华为发布新手机！！！点击查看>>>",
    platform="zhihu",
    rank=1,
    timestamp=datetime.now()
)

# Process
processed = processor.process_single(article)

# Access results
print(processed.title_cleaned)  # "华为发布新手机"
print(processed.title_en)       # "Huawei Releases New Phone"
print(processed.title_zh)       # "华为发布新手机"
print(processed.title_ms)       # "Huawei Melancarkan Telefon Baharu"
```

## Configuration

### Method 1: Direct Initialization

```python
processor = ArticleProcessor(
    api_url="https://api.bltcy.ai/v1/",
    api_key="your-key",
    model="gpt-5-nano-2025-08-07"
)
```

### Method 2: Environment Variables

```bash
export AI_API_URL="https://api.bltcy.ai/v1/"
export AI_API_KEY="your-key"
export AI_MODEL="gpt-5-nano-2025-08-07"
```

```python
processor = ArticleProcessor.from_env()
```

### Method 3: Config Object

```python
from ai_processing.config import AIConfig

config = AIConfig(
    api_url="https://api.bltcy.ai/v1/",
    api_key="your-key",
    model="gpt-5-nano-2025-08-07",
    batch_size=10,
    enable_cleaning=True,
    enable_translation=True,
    skip_same_language=True
)

processor = ArticleProcessor(config=config)
```

## Integration with TrendRadar

### Step 1: Import Module

```python
from ai_processing import ArticleProcessor, RawArticle
```

### Step 2: Initialize in main.py

```python
# After loading config
processor = ArticleProcessor(
    api_url=os.getenv("AI_API_URL"),
    api_key=os.getenv("AI_API_KEY"),
    model=os.getenv("AI_MODEL")
)
```

### Step 3: Process Filtered News

```python
# After filtering by keywords
filtered_news = filter_by_keywords(all_news)

# Convert to RawArticle format
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

# Process with AI
processed_articles = processor.process_articles(raw_articles)

# Convert to dict for saving
processed_dicts = [article.to_dict() for article in processed_articles]
```

### Step 4: Save to Railway DB

```python
# Save to database
for article in processed_dicts:
    save_to_railway_db(article)
```

## API Reference

### ArticleProcessor

Main processor class.

**Methods:**
- `process_articles(raw_articles: List[RawArticle]) -> List[ProcessedArticle]`
- `process_single(raw_article: RawArticle) -> ProcessedArticle`
- `from_env() -> ArticleProcessor` (class method)

### RawArticle

Input data model.

**Fields:**
- `id: str` - Unique identifier
- `title: str` - Original title
- `platform: str` - Platform name
- `rank: int` - Ranking position
- `url: Optional[str]` - Article URL
- `timestamp: Optional[datetime]` - Collection time
- `metadata: Dict` - Additional data

### ProcessedArticle

Output data model.

**Fields:**
- `news_id: str`
- `platform: str`
- `rank: int`
- `url: Optional[str]`
- `title_original: str` - Original title
- `title_cleaned: str` - AI-cleaned title
- `detected_language: str` - Detected language code
- `title_en: str` - English translation
- `title_zh: str` - Chinese translation
- `title_ms: str` - Malay translation
- `collected_at: Optional[datetime]`
- `processed_at: Optional[datetime]`
- `metadata: Dict`

**Methods:**
- `to_dict() -> Dict` - Convert to dictionary

## Pipeline Flow

```
Raw Article
    ↓
[AI Cleaning]
    ↓
Cleaned Title
    ↓
[Language Detection]
    ↓
Detected Language
    ↓
[AI Translation with Function Calling]
    ↓
3 Language Translations
    ↓
Processed Article
```

## Cost Estimation

Based on 50 filtered articles per hour:

**Cleaning:**
- 5 API calls (batch of 10)
- ~500 tokens
- Cost: $0.00025

**Translation:**
- 10 API calls (batch of 5, skip same language)
- ~1,500 tokens
- Cost: $0.00075

**Total per hour:** ~$0.001
**Daily:** ~$0.024
**Monthly:** ~$0.72

Very affordable! ✅

## Error Handling

The module includes robust error handling:

- **API Failures**: Automatic retry with exponential backoff
- **Parsing Errors**: Fallback to original title
- **Translation Errors**: Use cleaned title for all languages
- **Network Issues**: Retry up to 3 times

## Examples

See `example_usage.py` for complete examples.

## Requirements

- Python 3.7+
- requests

## License

Same as TrendRadar (GPL-3.0)

## Support

For issues or questions, please refer to the main TrendRadar repository.
