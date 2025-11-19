# Integration Guide: AI Processing Module + TrendRadar

Step-by-step guide to integrate the AI processing module with TrendRadar.

## Architecture

```
TrendRadar Crawler
    ↓
Filter by Keywords
    ↓
AI Processing Module
    ├─ Clean titles
    ├─ Detect language
    └─ Translate to 3 languages
    ↓
Railway PostgreSQL Database
    ↓
Frontend (Language Filter)
```

## Step 1: Add Environment Variables

Add these to your `.env` or GitHub Secrets:

```bash
# AI Processing
AI_API_URL=https://api.bltcy.ai/v1/
AI_API_KEY=sk-jW4WLdgCGCshSyFY9VbKXwj8y2YXclFHxw2x2WbXElFkcAlD
AI_MODEL=gpt-5-nano-2025-08-07
AI_BATCH_SIZE=10
AI_ENABLE_CLEANING=true
AI_ENABLE_TRANSLATION=true

# Railway Database
DATABASE_URL=postgresql://user:pass@host:port/dbname
```

## Step 2: Modify TrendRadar main.py

### 2.1: Import the Module

Add at the top of `main.py`:

```python
from ai_processing import ArticleProcessor, RawArticle
from datetime import datetime
```

### 2.2: Initialize Processor

After loading config:

```python
# Initialize AI processor
ai_processor = None
if os.getenv('AI_API_KEY'):
    try:
        ai_processor = ArticleProcessor.from_env()
        print("✓ AI Processing enabled")
    except Exception as e:
        print(f"⚠️  AI Processing disabled: {e}")
```

### 2.3: Process Filtered News

After filtering by keywords, before saving:

```python
# Existing code: filter news
filtered_news = filter_by_keywords(all_news)

# NEW: Process with AI if enabled
if ai_processor and filtered_news:
    try:
        # Convert to RawArticle format
        raw_articles = [
            RawArticle(
                id=f"{news['platform']}_{news.get('id', i)}",
                title=news['title'],
                platform=news['platform'],
                rank=news.get('rank', i),
                url=news.get('url'),
                timestamp=datetime.now()
            )
            for i, news in enumerate(filtered_news)
        ]
        
        # Process with AI
        processed_articles = ai_processor.process_articles(raw_articles)
        
        # Convert back to dict
        filtered_news = [article.to_dict() for article in processed_articles]
        
        print(f"✓ AI processed {len(processed_articles)} articles")
    
    except Exception as e:
        print(f"⚠️  AI processing failed: {e}")
        # Continue with original filtered_news

# Continue with existing code: save, notify, etc.
```

## Step 3: Update Data Structure

### 3.1: Modify JSON Output

Update the save function to include translations:

```python
def save_news_to_json(news_list, filename):
    """Save news with translations"""
    output = {
        "generated_at": datetime.now().isoformat(),
        "total_count": len(news_list),
        "news": news_list  # Now includes title_en, title_zh, title_ms
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
```

### 3.2: Update HTML Template

Modify `index.html` to support language filtering:

```html
<!-- Language Filter -->
<div class="language-filter">
    <button class="lang-btn active" data-lang="all">All</button>
    <button class="lang-btn" data-lang="en">English</button>
    <button class="lang-btn" data-lang="zh">中文</button>
    <button class="lang-btn" data-lang="ms">Bahasa</button>
</div>

<!-- News Item -->
<div class="news-item" data-lang="{{ detected_language }}">
    <div class="language-tabs">
        <span class="tab active" data-lang="en">EN</span>
        <span class="tab" data-lang="zh">中文</span>
        <span class="tab" data-lang="ms">MS</span>
    </div>
    
    <h3 class="title" data-lang="en">{{ title_en }}</h3>
    <h3 class="title hidden" data-lang="zh">{{ title_zh }}</h3>
    <h3 class="title hidden" data-lang="ms">{{ title_ms }}</h3>
    
    <p>Platform: {{ platform }} | Rank: #{{ rank }}</p>
</div>
```

## Step 4: Set Up Railway Database

### 4.1: Create Railway Project

1. Go to https://railway.app
2. Create new project
3. Add PostgreSQL database
4. Copy DATABASE_URL

### 4.2: Create Database Schema

```sql
CREATE TABLE news_articles (
    id SERIAL PRIMARY KEY,
    news_id VARCHAR(255) UNIQUE NOT NULL,
    platform VARCHAR(50) NOT NULL,
    rank INTEGER,
    url TEXT,
    
    -- Titles
    title_original TEXT NOT NULL,
    title_cleaned TEXT,
    
    -- Translations
    title_en TEXT,
    title_zh TEXT,
    title_ms TEXT,
    
    -- Metadata
    detected_language VARCHAR(10),
    collected_at TIMESTAMP,
    processed_at TIMESTAMP,
    
    -- Indexes
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_platform ON news_articles(platform);
CREATE INDEX idx_collected_at ON news_articles(collected_at);
CREATE INDEX idx_detected_language ON news_articles(detected_language);
```

### 4.3: Add Database Service

Create `database_service.py`:

```python
import os
import psycopg2
from psycopg2.extras import RealDictCursor

class DatabaseService:
    def __init__(self, database_url=None):
        self.database_url = database_url or os.getenv('DATABASE_URL')
    
    def connect(self):
        return psycopg2.connect(self.database_url)
    
    def save_article(self, article_dict):
        """Save processed article to database"""
        conn = self.connect()
        cur = conn.cursor()
        
        query = """
        INSERT INTO news_articles (
            news_id, platform, rank, url,
            title_original, title_cleaned,
            title_en, title_zh, title_ms,
            detected_language, collected_at, processed_at
        ) VALUES (
            %(news_id)s, %(platform)s, %(rank)s, %(url)s,
            %(title_original)s, %(title_cleaned)s,
            %(title_en)s, %(title_zh)s, %(title_ms)s,
            %(detected_language)s, %(collected_at)s, %(processed_at)s
        )
        ON CONFLICT (news_id) DO UPDATE SET
            title_cleaned = EXCLUDED.title_cleaned,
            title_en = EXCLUDED.title_en,
            title_zh = EXCLUDED.title_zh,
            title_ms = EXCLUDED.title_ms,
            updated_at = NOW()
        """
        
        cur.execute(query, article_dict)
        conn.commit()
        cur.close()
        conn.close()
    
    def save_batch(self, articles):
        """Save multiple articles"""
        for article in articles:
            self.save_article(article)
```

### 4.4: Use Database Service

In `main.py`:

```python
# After AI processing
if os.getenv('DATABASE_URL'):
    try:
        db = DatabaseService()
        db.save_batch(filtered_news)
        print(f"✓ Saved {len(filtered_news)} articles to Railway DB")
    except Exception as e:
        print(f"⚠️  Database save failed: {e}")
```

## Step 5: Update GitHub Actions

Add environment variables to `.github/workflows/crawler.yml`:

```yaml
- name: Run crawler
  env:
    # Existing vars...
    NEWSNOW_API_URL: ${{ secrets.NEWSNOW_API_URL }}
    
    # NEW: AI Processing
    AI_API_URL: ${{ secrets.AI_API_URL }}
    AI_API_KEY: ${{ secrets.AI_API_KEY }}
    AI_MODEL: ${{ secrets.AI_MODEL }}
    
    # NEW: Railway Database
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
  run: python main.py
```

## Step 6: Test the Integration

### 6.1: Test Locally

```bash
# Set environment variables
export AI_API_KEY="your-key"
export AI_API_URL="https://api.bltcy.ai/v1/"
export AI_MODEL="gpt-5-nano-2025-08-07"

# Run TrendRadar
python main.py
```

### 6.2: Check Output

Verify the output includes translations:

```json
{
  "news_id": "zhihu_001",
  "title_original": "华为发布新手机！！！",
  "title_cleaned": "华为发布新手机",
  "detected_language": "zh",
  "title_en": "Huawei Releases New Phone",
  "title_zh": "华为发布新手机",
  "title_ms": "Huawei Melancarkan Telefon Baharu"
}
```

## Step 7: Deploy

1. Push changes to GitHub
2. Add secrets in GitHub Settings
3. Trigger workflow manually or wait for schedule
4. Check Railway database for saved articles

## Troubleshooting

### Issue: AI processing fails

**Check:**
- API key is correct
- API URL is accessible
- Model name is correct
- Network connectivity

### Issue: Database connection fails

**Check:**
- DATABASE_URL is correct
- Railway database is running
- Network allows connections
- Schema is created

### Issue: Translations are same as original

**Check:**
- Function calling is supported by your API
- Model supports the languages
- Check API response format

## Cost Monitoring

Monitor your costs:

**AI API:**
- Check usage at your provider's dashboard
- Expected: ~$0.72/month for 50 articles/hour

**Railway:**
- Free tier: 500 MB storage
- Expected usage: ~36 MB/month
- Free tier is sufficient

## Next Steps

1. Optimize frontend for language filtering
2. Add caching to reduce API calls
3. Implement rate limiting
4. Add monitoring and alerts
5. Create API endpoints for querying translations

## Support

For issues, check:
- `ai_processing/README.md` - Module documentation
- `ai_processing/example_usage.py` - Usage examples
- `ai_processing/test_module.py` - Test suite
