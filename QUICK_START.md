# Quick Start Guide

Get Eternalgy-News-AI up and running in 5 minutes.

## Prerequisites

- ✅ Python 3.10+
- ✅ Docker & Docker Compose
- ✅ API keys for GPT-4o-mini-web-search and GPT-5-nano

---

## Step 1: Start Database (30 seconds)

```bash
cd Eternalgy-News-AI
docker-compose up -d
```

Wait for PostgreSQL to start:
```bash
docker-compose ps
```

You should see `news_search_db` running on port 5433.

---

## Step 2: Install Dependencies (1 minute)

```bash
pip install -r requirements.txt
```

---

## Step 3: Configure Environment (1 minute)

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```bash
# Required: Add your API keys
SEARCH_API_KEY=your-search-api-key-here
AI_API_KEY=your-ai-api-key-here
JINA_API_KEY=your-jina-api-key-here

# Optional: Adjust if needed
DB_HOST=localhost
DB_PORT=5433
DB_NAME=news_db
DB_USER=postgres
DB_PASSWORD=postgres
```

---

## Step 4: Initialize Database (10 seconds)

```bash
python examples/00_init_database.py
```

Expected output:
```
Initializing Eternalgy-News-AI Database...
==================================================
✓ Database tables created successfully!

Tables created:
  - news_links
  - processed_content
  - query_tasks

Database is ready to use!
```

---

## Step 5: Run Full Workflow (2 minutes)

```bash
python examples/04_full_workflow.py
```

This will:
1. Create a demo query task
2. Search for news URLs using GPT-4o-mini
3. Process discovered links (fetch Markdown via Jina Reader, clean, translate)
4. Display results

Expected output:
```
============================================================
Eternalgy-News-AI - Full Workflow Demo
============================================================

Step 1: Check/Create Query Task
------------------------------------------------------------
✓ Task exists: tech_news_demo

Step 2: Run Search Query
------------------------------------------------------------
✓ Search completed
  Found: 15 URLs
  New: 12
  Duplicates: 3

Auto-processing results:
  Processed: 12
  Successful: 10
  Failed: 2

Step 3: Database Statistics
------------------------------------------------------------
Links:
  Total: 12
  Pending: 0
  Processing: 0
  Completed: 10
  Failed: 2

Tasks:
  Total: 1
  Active: 1

Step 4: Sample Processed Content
------------------------------------------------------------
Link ID: 1
URL: https://example.com/article...
Title: AI Breakthrough in Natural Language Processing...
Content preview:
  • New AI model achieves 95% accuracy
  • Researchers from MIT and Stanford collaborate
  • Applications in healthcare and education
  ...

============================================================
Workflow Complete!
============================================================
```

---

## Verify Everything Works

### Check Database

```bash
# Connect to database
docker exec -it news_search_db psql -U postgres -d news_db

# Run queries
SELECT COUNT(*) FROM news_links;
SELECT COUNT(*) FROM processed_content;
SELECT COUNT(*) FROM query_tasks;

# Exit
\q
```

### Check Processed Content

```python
from news_search import Database

db = Database()
stats = db.get_statistics()
print(stats)
```

---

## Next Steps

### Run Individual Steps

```bash
# Create a custom query task
python examples/01_create_query_task.py

# Run search only
python examples/02_run_search.py

# Process links only
python examples/03_process_links.py
```

### Customize Query Task

Edit `examples/01_create_query_task.py` to create your own search queries:

```python
task_name = "my_custom_news"
prompt = """
Find news articles about [YOUR TOPIC].
Return URLs as JSON array.
"""

db.create_query_task(task_name, prompt)
```

### Query Processed News

```python
from news_search import Database

db = Database()

# Get all completed links
with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT nl.id, nl.url, pc.title, pc.content
        FROM news_links nl
        JOIN processed_content pc ON nl.id = pc.link_id
        WHERE nl.status = 'completed'
        ORDER BY nl.processed_at DESC
        LIMIT 10
    """)
    
    for row in cursor.fetchall():
        print(f"ID: {row[0]}")
        print(f"URL: {row[1]}")
        print(f"Title: {row[2]}")
        print(f"Content: {row[3][:100]}...")
        print("-" * 60)
```

---

## Troubleshooting

### Database Connection Error

```
Error: could not connect to server
```

**Solution**: Make sure PostgreSQL is running:
```bash
docker-compose ps
docker-compose up -d
```

### API Key Error

```
Error: 401 Unauthorized
```

**Solution**: Check your API keys in `.env`:
```bash
cat .env | grep API_KEY
```

### Import Error

```
ModuleNotFoundError: No module named 'news_search'
```

**Solution**: Make sure you're in the right directory:
```bash
cd Eternalgy-News-AI
python examples/04_full_workflow.py
```

Or add parent directory to path:
```python
import sys
sys.path.insert(0, '..')
```

### Processing Timeout

```
Error: Request timed out
```

**Solution**: Increase timeout in `.env`:
```bash
REQUEST_TIMEOUT=120
PROCESSING_TIMEOUT=60
```

---

## Configuration Tips

### Adjust Processing Speed

In `.env`:
```bash
# Process more domains concurrently
MAX_CONCURRENT_DOMAINS=5

# Reduce delay between requests
SAME_DOMAIN_DELAY=1
```

### Disable Auto-Processing

In `.env`:
```bash
# Manually control when to process
AUTO_PROCESS_AFTER_SEARCH=false
```

Then run processing separately:
```bash
python examples/03_process_links.py
```

### Change Database Port

If port 5433 is in use, edit `docker-compose.yml`:
```yaml
ports:
  - "5434:5432"  # Change 5433 to 5434
```

And update `.env`:
```bash
DB_PORT=5434
```

---

## Monitoring

### Check Logs

```bash
# Database logs
docker-compose logs -f postgres

# Python logs (if running as service)
tail -f logs/app.log
```

### Database Statistics

```python
from news_search import Database

db = Database()
stats = db.get_statistics()

print(f"Total links: {stats['links']['total_links']}")
print(f"Completed: {stats['links']['completed']}")
print(f"Failed: {stats['links']['failed']}")
print(f"Success rate: {stats['links']['completed'] / stats['links']['total_links'] * 100:.1f}%")
```

---

## Stopping

```bash
# Stop database (keeps data)
docker-compose stop

# Stop and remove (deletes data)
docker-compose down -v
```

---

## Getting Help

1. Check documentation:
   - `README.md` - Project overview
   - `docs/WORKFLOW_GUIDE.md` - Detailed workflow
   - `docs/API_DOCUMENTATION.md` - API reference
   - `docs/DATABASE_SCHEMA.md` - Database structure

2. Check examples:
   - `examples/` folder has 5 working examples

3. Check logs:
   - Database: `docker-compose logs`
   - Application: Check console output

---

## Ready for Frontend!

Once you have processed news in the database, you're ready to integrate a frontend.

See `frontend/README.md` for integration plan.

---

**You're all set!** 🎉

Your independent news processing system is now running.
