# News Search Module

AI-powered news discovery using GPT-4o-mini-search-preview with PostgreSQL storage and deduplication.

## Features

- 🔍 AI-powered web search using OpenAI-compatible API
- 🗄️ PostgreSQL storage with automatic deduplication
- 🔗 URL normalization (removes tracking params, standardizes format)
- 📋 Query task management (create reusable search queries)
- ⏰ Cron-ready for scheduled execution
- 📊 Statistics tracking (runs, links found, duplicates)

## Installation

```bash
pip install -r requirements.txt
```

## Database Setup

```bash
# Create PostgreSQL database
createdb news_db

# Initialize tables (automatic on first run)
python sample_query_task.py
```

## Configuration

Edit `config.py` or set environment variables:

```bash
# API Configuration
export SEARCH_API_KEY="your-api-key"

# Database Configuration
export DB_HOST="localhost"
export DB_PORT="5432"
export DB_NAME="news_db"
export DB_USER="postgres"
export DB_PASSWORD="your-password"
```

## Usage

### Run Sample Task

```bash
python sample_query_task.py
```

### Create Custom Task

```python
from news_search import Database

db = Database()
db.create_query_task(
    task_name="renewable_energy_weekly",
    prompt_template="Search for renewable energy news from the last 7 days. Return only URLs in JSON array, maximum 20 links.",
    schedule="0 9 * * 1"  # Every Monday at 9 AM
)
```

### Execute Task

```python
from news_search import NewsSearchModule

search = NewsSearchModule()
result = search.run_task("renewable_energy_weekly")
print(result)
```

### Get Pending Links

```python
from news_search import Database

db = Database()
pending = db.get_pending_links(limit=50)

for link in pending:
    print(f"{link['url']} - {link['source_task']}")
```

## Database Schema

### news_links
- `id`: Primary key
- `url`: Full URL
- `url_hash`: SHA256 hash (unique constraint)
- `title`: Article title (nullable)
- `discovered_at`: When URL was found
- `source_task`: Which task found it
- `status`: pending/processing/completed/failed
- `processed_at`: When processing completed
- `last_checked`: Last verification time

### query_tasks
- `id`: Primary key
- `task_name`: Unique task identifier
- `prompt_template`: Search prompt
- `is_active`: Enable/disable task
- `schedule`: Cron expression
- `last_run`: Last execution time
- `total_runs`: Execution count
- `total_links_found`: Total links discovered

## API Integration

The module integrates with your existing AI processing pipeline:

```python
# 1. Discover news links
search = NewsSearchModule()
search.run_task("malaysia_solar_pv_daily")

# 2. Get pending links
db = Database()
pending = db.get_pending_links()

# 3. Process with your Jina Reader-powered pipeline
from ai_processing.processor_with_content import ArticleProcessorWithContent
from ai_processing.processor_adapter import ProcessorAdapter

ai_processor = ArticleProcessorWithContent.from_env()
adapter = ProcessorAdapter(ai_processor)

for link in pending:
    processed = adapter.process(link['url'], title=link.get('title', ''))
    status = 'completed' if processed.get('success') else 'failed'
    db.update_link_status(link['id'], status)
```

## Cost Tracking

Average cost per search: ~$0.00016 (376 tokens @ $0.00042/1K)

For 10 daily searches: ~$0.048/month

## Cron Setup

```bash
# Add to crontab
0 8 * * * cd /path/to/project && python -c "from news_search import NewsSearchModule; NewsSearchModule().run_task('malaysia_solar_pv_daily')"
```
