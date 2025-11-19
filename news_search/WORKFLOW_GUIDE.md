# Complete Workflow Guide

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      COMPLETE WORKFLOW                          │
└─────────────────────────────────────────────────────────────────┘

1. SEARCH QUERY (GPT-4o-mini-search-preview)
   ↓
   - Execute search with prompt
   - Get 20 URLs in JSON array
   - Cost: ~$0.00016 per search
   
2. URL PROCESSING
   ↓
   - Normalize URLs (remove tracking params)
   - Generate SHA256 hash
   - Check for duplicates
   - Save new URLs to DB (status='pending')
   
3. DOMAIN GROUPING
   ↓
   - Group URLs by domain
   - Example: thestar.com.my (5), reuters.com (3), etc.
   
4. CONCURRENT PROCESSING (with rate limiting)
   ↓
   ┌─────────────┬─────────────┬─────────────┐
   │  Domain 1   │  Domain 2   │  Domain 3   │  (MAX_CONCURRENT_DOMAINS=3)
   │             │             │             │
   │  URL 1      │  URL 1      │  URL 1      │
   │  ↓ 3s      │  ↓ 3s      │  ↓ 3s      │  (SAME_DOMAIN_DELAY=3s)
   │  URL 2      │  URL 2      │  URL 2      │
   │  ↓ 3s      │  ↓ 3s      │  ↓ 3s      │
   │  URL 3      │  URL 3      │  URL 3      │
   └─────────────┴─────────────┴─────────────┘
   
5. AI PROCESSING (per URL)
   ↓
   - HTTP scrape content
   - Clean HTML
   - Extract article text
   - Translate to target language
   - Save to processed_content table
   - Update status='completed'
   
6. ERROR HANDLING
   ↓
   - Retry failed requests (MAX_RETRIES=2)
   - Exponential backoff
   - Save error message
   - Update status='failed'
```

## Database Schema

### news_links
```sql
id                  SERIAL PRIMARY KEY
url                 TEXT NOT NULL
url_hash            VARCHAR(64) UNIQUE NOT NULL  -- SHA256 for deduplication
title               TEXT
discovered_at       TIMESTAMP
source_task         VARCHAR(255)                 -- Which task found it
status              VARCHAR(50)                  -- pending/processing/completed/failed
error_message       TEXT
processed_at        TIMESTAMP
last_checked        TIMESTAMP
created_at          TIMESTAMP
```

### processed_content
```sql
id                  SERIAL PRIMARY KEY
link_id             INTEGER REFERENCES news_links(id)
title               TEXT
content             TEXT                         -- Original content
translated_content  TEXT                         -- Translated content
metadata            JSONB                        -- Additional data
created_at          TIMESTAMP
updated_at          TIMESTAMP
```

### query_tasks
```sql
id                  SERIAL PRIMARY KEY
task_name           VARCHAR(255) UNIQUE
prompt_template     TEXT                         -- Search prompt
is_active           BOOLEAN
schedule            VARCHAR(100)                 -- Cron expression
last_run            TIMESTAMP
total_runs          INTEGER
total_links_found   INTEGER
created_at          TIMESTAMP
updated_at          TIMESTAMP
```

## Configuration

### config.py

```python
# Search API
SEARCH_API_URL = "https://api.bltcy.ai/v1/chat/completions"
SEARCH_API_KEY = "your-api-key"
SEARCH_MODEL = "gpt-4o-mini-search-preview"

# Database
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "news_db"
DB_USER = "postgres"
DB_PASSWORD = "postgres"

# Processing
SAME_DOMAIN_DELAY = 3           # seconds between same-domain requests
MAX_CONCURRENT_DOMAINS = 3      # process N domains concurrently
MAX_RETRIES = 2                 # retry failed requests
PROCESSING_TIMEOUT = 30         # timeout per URL

# Workflow
AUTO_PROCESS_AFTER_SEARCH = True  # Auto-process after search
```

## Usage Examples

### 1. Basic Usage (Mock Processing)

```python
from news_search import NewsSearchModule, ProcessorWorker, Database

# Setup
db = Database()
db.init_tables()

# Create processor (mock mode for testing)
processor = ProcessorWorker(ai_processor=None)

# Create search module with processor
search = NewsSearchModule(processor_worker=processor)

# Run task
result = search.run_task("malaysia_solar_pv_daily")

print(f"Found: {result['new_links']} new links")
print(f"Processed: {result['processing']['success']} successfully")
```

### 2. With Your AI Processor

```python
from news_search import NewsSearchModule, ProcessorWorker
from ai_processing.processor_with_content import NewsProcessor

# Create adapter for your AI processor
class AIProcessorAdapter:
    def __init__(self):
        self.news_processor = NewsProcessor()
    
    def process(self, url: str) -> dict:
        result = self.news_processor.process_url(url)
        return {
            'success': result.get('success'),
            'title': result.get('title'),
            'content': result.get('content'),
            'translated_content': result.get('translated_content'),
            'metadata': result.get('metadata')
        }

# Use it
ai_processor = AIProcessorAdapter()
processor = ProcessorWorker(ai_processor=ai_processor)
search = NewsSearchModule(processor_worker=processor)

result = search.run_task("malaysia_solar_pv_daily")
```

### 3. Manual Processing (Separate Steps)

```python
from news_search import NewsSearchModule, ProcessorWorker

# Step 1: Search only (no auto-processing)
search = NewsSearchModule(processor_worker=None)
result = search.run_task("malaysia_solar_pv_daily")

print(f"Saved {result['new_links']} new links")

# Step 2: Process later
processor = ProcessorWorker(ai_processor=your_processor)
processing_result = processor.process_pending_links(limit=50)

print(f"Processed {processing_result['success']} links")
```

### 4. Process Specific Links

```python
from news_search import ProcessorWorker

processor = ProcessorWorker(ai_processor=your_processor)

# Process specific link IDs
link_ids = [1, 2, 3, 4, 5]
result = processor.process_specific_links(link_ids)

print(f"Success: {result['success']}/{result['total']}")
```

## Rate Limiting Behavior

### Example: 20 URLs from 4 domains

```
Domain A: 8 URLs
Domain B: 6 URLs  
Domain C: 4 URLs
Domain D: 2 URLs

With MAX_CONCURRENT_DOMAINS=3, SAME_DOMAIN_DELAY=3s:

Time 0s:  Domain A URL1 | Domain B URL1 | Domain C URL1
Time 3s:  Domain A URL2 | Domain B URL2 | Domain C URL2
Time 6s:  Domain A URL3 | Domain B URL3 | Domain C URL3
Time 9s:  Domain A URL4 | Domain B URL4 | Domain C URL4
Time 12s: Domain A URL5 | Domain B URL5 | Domain D URL1
Time 15s: Domain A URL6 | Domain B URL6 | Domain D URL2
Time 18s: Domain A URL7 | (done)       | (done)
Time 21s: Domain A URL8 | (done)       | (done)
Time 24s: (done)        | (done)       | (done)

Total time: ~24 seconds for 20 URLs
```

### Benefits:
- **Fast**: Different domains process concurrently
- **Safe**: Same domain respects 3s delay
- **Polite**: Doesn't overwhelm any single site

## Cron Job Setup

### Daily at 8 AM

```bash
# crontab -e
0 8 * * * cd /path/to/project && python -c "from news_search import NewsSearchModule, ProcessorWorker; processor = ProcessorWorker(); search = NewsSearchModule(processor); search.run_task('malaysia_solar_pv_daily')"
```

### Multiple Tasks

```bash
# Malaysia solar PV - daily at 8 AM
0 8 * * * cd /path/to/project && python run_task.py malaysia_solar_pv_daily

# Renewable energy - weekly on Monday at 9 AM
0 9 * * 1 cd /path/to/project && python run_task.py renewable_energy_weekly

# Global energy news - twice daily
0 8,20 * * * cd /path/to/project && python run_task.py global_energy_news
```

### run_task.py
```python
import sys
from news_search import NewsSearchModule, ProcessorWorker
from your_ai_processor import YourAIProcessor

task_name = sys.argv[1]

processor = ProcessorWorker(ai_processor=YourAIProcessor())
search = NewsSearchModule(processor_worker=processor)
result = search.run_task(task_name)

print(f"Task {task_name}: {result['new_links']} new, {result['processing']['success']} processed")
```

## Monitoring & Statistics

```python
from news_search import Database

db = Database()
stats = db.get_statistics()

print(f"Total links: {stats['links']['total_links']}")
print(f"Pending: {stats['links']['pending']}")
print(f"Completed: {stats['links']['completed']}")
print(f"Failed: {stats['links']['failed']}")
```

## Cost Estimation

### Search API
- Cost per search: ~$0.00016 (376 tokens @ $0.00042/1K)
- Daily: 1 search = $0.00016/day = $0.0048/month
- 10 searches/day = $0.048/month

### Processing
- Depends on your AI processor costs
- HTTP scraping: Free (just bandwidth)
- Translation API: Varies by provider

## Error Handling

### Automatic Retries
- Failed requests retry up to MAX_RETRIES times
- Exponential backoff: 2^attempt seconds
- Error messages saved to database

### Status Tracking
- `pending`: Waiting to be processed
- `processing`: Currently being processed
- `completed`: Successfully processed
- `failed`: Processing failed after retries

### Query Failed Links
```python
from news_search import Database

db = Database()
conn = db.get_connection()
cursor = conn.cursor()

cursor.execute("""
    SELECT url, error_message, processed_at
    FROM news_links
    WHERE status = 'failed'
    ORDER BY processed_at DESC
""")

failed = cursor.fetchall()
for url, error, timestamp in failed:
    print(f"{url}: {error}")
```

## Best Practices

1. **Start with mock processing** to test workflow
2. **Monitor failed links** and adjust retry logic
3. **Adjust delays** based on target site behavior
4. **Use specific prompts** for better search results
5. **Set up monitoring** for cron jobs
6. **Backup database** regularly
7. **Rotate User-Agent** if needed
8. **Respect robots.txt** of target sites

## Troubleshooting

### No URLs returned
- Check search prompt specificity
- Verify API key is valid
- Check date range in prompt

### High failure rate
- Increase SAME_DOMAIN_DELAY
- Check target site availability
- Verify AI processor is working

### Slow processing
- Increase MAX_CONCURRENT_DOMAINS
- Decrease SAME_DOMAIN_DELAY (carefully)
- Optimize AI processor

### Duplicates not filtered
- Check URL normalization
- Verify url_hash uniqueness
- Check database constraints
