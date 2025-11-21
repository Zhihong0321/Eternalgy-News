# Eternalgy-News-AI

AI-powered news discovery, processing, and translation system.

## 🎯 Overview

Eternalgy-News-AI is an intelligent news aggregation system that discovers, processes, and translates news articles using advanced AI models. The system automatically finds news URLs, extracts content, cleans and summarizes it, and translates it into multiple languages.

## ✨ Features

- 🔍 **AI-Powered Search**: GPT-4o-mini-web-search for intelligent news discovery
- 🤖 **Content Processing**: Automated scraping, cleaning, and point-form summarization
- 🌐 **Multi-Language**: Automatic translation to English, Chinese (Simplified), and Malay
- 🗄️ **PostgreSQL Storage**: Deduplication and persistent storage
- 📊 **Structured Output**: Strict JSON format for easy frontend integration
- 🔄 **Automated Workflow**: End-to-end pipeline from discovery to storage

## 🏗️ Architecture

```
Query Task → GPT-4o-mini Search → News URLs
    ↓
PostgreSQL (news_links table)
    ↓ [Deduplication]
AI Processor → HTTP Scrape → Extract Content
    ↓
GPT-5-nano → Clean & Summarize (Point Form)
    ↓
GPT-5-nano → Translate (EN, ZH, MS)
    ↓
PostgreSQL (processed_content table)
    ↓
[Frontend UI - Ready for Integration]
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Docker & Docker Compose
- API keys for:
  - GPT-4o-mini-web-search
  - GPT-5-nano (or compatible OpenAI API)

### 1. Setup Database

```bash
docker-compose up -d
```

This starts PostgreSQL on port 5433.

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your API keys:
```bash
SEARCH_API_KEY=your-search-api-key
AI_API_KEY=your-ai-api-key
```

### 4. Initialize Database

```bash
python examples/00_init_database.py
```

### 5. Run Full Workflow

```bash
python examples/04_full_workflow.py
```

## 📁 Project Structure

```
Eternalgy-News-AI/
├── news_search/           # News discovery module
│   ├── search_client.py   # GPT-4o-mini search client
│   ├── search_module.py   # Search orchestration
│   ├── database.py        # PostgreSQL operations
│   └── processor_worker.py # Link processing worker
│
├── ai_processing/         # Content processing module
│   ├── processor_with_content.py  # Main processor
│   ├── services/
│   │   ├── content_extractor.py   # HTTP scraping
│   │   ├── content_cleaner.py     # Content cleaning
│   │   └── translator.py          # Multi-language translation
│   └── models/
│       └── article.py     # Data models
│
├── examples/              # Usage examples
│   ├── 01_create_query_task.py
│   ├── 02_run_search.py
│   ├── 03_process_links.py
│   └── 04_full_workflow.py
│
├── docs/                  # Documentation
│   ├── WORKFLOW_GUIDE.md
│   ├── API_DOCUMENTATION.md
│   └── DATABASE_SCHEMA.md
│
└── frontend/              # Frontend integration (coming soon)
```

## 📖 Documentation

- [Workflow Guide](docs/WORKFLOW_GUIDE.md) - Complete workflow documentation
- [API Documentation](docs/API_DOCUMENTATION.md) - API reference
- [Database Schema](docs/DATABASE_SCHEMA.md) - Database structure
- [Architecture](docs/ARCHITECTURE.md) - System design

## 🔧 Modules

### news_search

News discovery using GPT-4o-mini-web-search with PostgreSQL deduplication.

**Key Features**:
- AI-powered web search
- URL normalization and deduplication
- Query task management
- Automatic processing trigger

### ai_processing

Content extraction, cleaning, and multi-language translation.

**Key Features**:
- HTTP content scraping
- Readability-based extraction
- Point-form summarization
- 3-language translation (EN, ZH, MS)
- Language detection

## 💾 Database Schema

### news_links
Stores discovered news URLs with deduplication.

```sql
- id (serial)
- url (text)
- url_hash (varchar) - for deduplication
- title (text)
- discovered_at (timestamp)
- source_task (varchar)
- status (varchar) - pending/processing/completed/failed
```

### processed_content
Stores cleaned, translated, and localized headlines.

```sql
- id (serial)
- link_id (integer) - foreign key to `news_links`
- title (text) - fallback/raw headline
- title_en (text) - cleaned English headline used for the UI
- title_zh (text) - Simplified Chinese headline
- title_ms (text) - Malay headline
- content (text) - point-form summary (BBCode preserved here)
- translated_content (text) - JSON blob with EN/ZH/MS bullet summaries
- metadata (jsonb) - detected language, source, timestamps, etc.
```
### Environment Variables

See `.env.example` for all configuration options:

- **Search API**: `SEARCH_API_URL`, `SEARCH_API_KEY`, `SEARCH_MODEL`
- **AI Processing**: `AI_API_URL`, `AI_API_KEY`, `AI_MODEL`
- **Database**: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- **Processing**: `AUTO_PROCESS_AFTER_SEARCH`, `MAX_CONCURRENT_DOMAINS`

## 🧪 Testing

```bash
# Test search module
python tests/test_search.py

# Test AI processor
python tests/test_processor.py

# Test database
python tests/test_database.py
```

## 📊 Monitoring

Check processing status:

```python
from news_search import Database

db = Database()
stats = db.get_statistics()

print(f"Total links: {stats['links']['total_links']}")
print(f"Pending: {stats['links']['pending']}")
print(f"Completed: {stats['links']['completed']}")
print(f"Failed: {stats['links']['failed']}")
```

## 🤝 Contributing

This is a private project. For questions or issues, contact the development team.

## 📄 License

Proprietary - All rights reserved.

## 🔗 Related Projects

- [TrendRadar](https://github.com/sansan0/TrendRadar) - Original inspiration (now independent)

---

**Version**: 1.0.0  
**Last Updated**: 2025-11-18  
**Status**: Production Ready (Backend) | Frontend Integration Pending

