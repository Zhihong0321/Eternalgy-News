# Database Schema

PostgreSQL database schema for Eternalgy-News-AI.

## Tables

### 1. news_links

Stores discovered news URLs with deduplication.

```sql
CREATE TABLE news_links (
    id SERIAL PRIMARY KEY,
    url TEXT NOT NULL,
    url_hash VARCHAR(64) UNIQUE NOT NULL,
    title TEXT,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_task VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    error_message TEXT,
    processed_at TIMESTAMP,
    last_checked TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_news_links_url_hash ON news_links(url_hash);
CREATE INDEX idx_news_links_status ON news_links(status);
CREATE INDEX idx_news_links_source_task ON news_links(source_task);
```

**Fields**:
- `id`: Unique identifier
- `url`: Full URL of the news article
- `url_hash`: SHA256 hash for deduplication
- `title`: Article title (if available)
- `discovered_at`: When the URL was first discovered
- `source_task`: Which query task discovered this URL
- `status`: Processing status (pending/processing/completed/failed)
- `error_message`: Error details if processing failed
- `processed_at`: When processing completed
- `last_checked`: Last time this URL was checked
- `created_at`: Record creation timestamp

**Status Values**:
- `pending`: Waiting to be processed
- `processing`: Currently being processed
- `completed`: Successfully processed
- `failed`: Processing failed

---

### 2. processed_content

Stores cleaned and translated article content and localized headlines.

```sql
CREATE TABLE processed_content (
    id SERIAL PRIMARY KEY,
    link_id INTEGER UNIQUE REFERENCES news_links(id) ON DELETE CASCADE,
    title TEXT,
    title_en TEXT,
    title_zh TEXT,
    title_ms TEXT,
    content TEXT,
    translated_content TEXT,
    tags TEXT[],
    country VARCHAR(2),
    news_date DATE,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_processed_content_link_id ON processed_content(link_id);
CREATE INDEX idx_processed_content_tags ON processed_content USING GIN(tags);
CREATE INDEX idx_processed_content_country ON processed_content(country);
CREATE INDEX idx_processed_content_news_date ON processed_content(news_date);
```

**Fields**:
- `id`: Unique identifier
- `link_id`: References `news_links`
- `title`: Raw or fallback headline
- `title_en`: Cleaned English headline for the UI
- `title_zh`: Simplified Chinese headline
- `title_ms`: Malay headline
- `content`: Point-form summary (BBCode is preserved for now)
- `translated_content`: JSON object with `en`, `zh`, and `ms` bullet summaries
- `tags`: GIN-indexed arrays of relevant tags
- `metadata`: Detection info, source domain, and other stats (JSONB)
- `country`: Two-letter country code
- `news_date`: Publication date
- `created_at` / `updated_at`: Timestamps
### 3. blacklisted_sites

Tracks domains that block the Jina Reader API so we stop retrying them.

```sql
CREATE TABLE blacklisted_sites (
    id SERIAL PRIMARY KEY,
    domain VARCHAR(255) UNIQUE NOT NULL,
    url TEXT NOT NULL,
    title TEXT,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_blacklisted_sites_domain ON blacklisted_sites(domain);
```

**Fields**:
- `id`: Unique identifier
- `domain`: Lowercased domain name (e.g., `malaymail.com`)
- `url`: Last blocked URL we attempted
- `title`: Title derived from the news link (fetched from the original search hit)
- `reason`: HTTP status and error message reported by Jina
- `created_at`: When the domain was first blacklisted
- `updated_at`: Last time we recorded another block

This table is consulted during processing to skip any links from blocked domains.

---

### 4. query_tasks

Manages reusable search query tasks.

```sql
CREATE TABLE query_tasks (
    id SERIAL PRIMARY KEY,
    task_name VARCHAR(255) UNIQUE NOT NULL,
    prompt_template TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    schedule VARCHAR(100),
    last_run TIMESTAMP,
    total_runs INTEGER DEFAULT 0,
    total_links_found INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_query_tasks_task_name ON query_tasks(task_name);
CREATE INDEX idx_query_tasks_is_active ON query_tasks(is_active);
```

**Fields**:
- `id`: Unique identifier
- `task_name`: Unique task name
- `prompt_template`: Search prompt for AI
- `is_active`: Whether task is active
- `schedule`: Schedule description (e.g., "daily", "hourly")
- `last_run`: Last execution timestamp
- `total_runs`: Total number of executions
- `total_links_found`: Total URLs discovered
- `created_at`: Record creation timestamp
- `updated_at`: Last update timestamp

---

## Relationships

```
query_tasks (1) -----> (N) news_links
                         |
                         | (1:1)
                         |
                         v
                  processed_content
```

- One query task can discover many news links
- Each news link has one processed content record
- Processed content is deleted if news link is deleted (CASCADE)

---

## Common Queries

### Get Pending Links
```sql
SELECT id, url, source_task, discovered_at
FROM news_links
WHERE status = 'pending'
ORDER BY discovered_at DESC
LIMIT 100;
```

### Get Processed Content with Link Info
```sql
SELECT 
    nl.id,
    nl.url,
    nl.discovered_at,
    pc.title,
    pc.content,
    pc.metadata
FROM news_links nl
JOIN processed_content pc ON nl.id = pc.link_id
WHERE nl.status = 'completed'
ORDER BY nl.processed_at DESC;
```

### Get Statistics
```sql
SELECT 
    COUNT(*) as total_links,
    COUNT(*) FILTER (WHERE status = 'pending') as pending,
    COUNT(*) FILTER (WHERE status = 'processing') as processing,
    COUNT(*) FILTER (WHERE status = 'completed') as completed,
    COUNT(*) FILTER (WHERE status = 'failed') as failed
FROM news_links;
```

### Get Active Tasks
```sql
SELECT *
FROM query_tasks
WHERE is_active = true
ORDER BY task_name;
```

---

## Indexes

All tables have appropriate indexes for:
- Primary keys (automatic)
- Foreign keys
- Frequently queried fields (status, task_name, url_hash)

---

## Maintenance

### Clean Old Failed Links
```sql
DELETE FROM news_links
WHERE status = 'failed'
AND processed_at < NOW() - INTERVAL '30 days';
```

### Reset Stuck Processing
```sql
UPDATE news_links
SET status = 'pending',
    error_message = 'Reset from stuck processing state'
WHERE status = 'processing'
AND last_checked < NOW() - INTERVAL '1 hour';
```

### Vacuum and Analyze
```sql
VACUUM ANALYZE news_links;
VACUUM ANALYZE processed_content;
VACUUM ANALYZE query_tasks;
```

---

## Backup

### Backup Database
```bash
pg_dump -h localhost -p 5433 -U postgres news_db > backup.sql
```

### Restore Database
```bash
psql -h localhost -p 5433 -U postgres news_db < backup.sql
```

---

## Migration

When schema changes are needed:

1. Create migration script
2. Test on development database
3. Backup production database
4. Apply migration
5. Verify data integrity

Example migration:
```sql
-- Add new column
ALTER TABLE news_links ADD COLUMN priority INTEGER DEFAULT 0;

-- Create index
CREATE INDEX idx_news_links_priority ON news_links(priority);

-- Update existing records
UPDATE news_links SET priority = 1 WHERE source_task = 'urgent_news';
```


