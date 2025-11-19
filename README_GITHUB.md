# Eternalgy-News

AI-powered news discovery, processing, and translation system for renewable energy news.

![Status](https://img.shields.io/badge/status-production%20ready-brightgreen)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-proprietary-red)

## 🎯 Overview

Eternalgy-News is an intelligent news aggregation system that discovers, processes, and translates news articles using advanced AI models. The system automatically finds news URLs, extracts content, cleans and summarizes it, and translates it into multiple languages.

**Live Demo**: [Frontend running on localhost:3000](http://127.0.0.1:3000)

## ✨ Features

- 🔍 **AI-Powered Search**: GPT-4o-mini-web-search for intelligent news discovery
- 🤖 **Content Processing**: Automated scraping, cleaning, and point-form summarization
- 🌐 **Multi-Language**: Automatic translation to English, Chinese (Simplified), and Malay
- 🗄️ **PostgreSQL Storage**: Deduplication and persistent storage
- 📊 **Structured Output**: Strict JSON format for easy frontend integration
- 🔄 **Automated Workflow**: End-to-end pipeline from discovery to storage
- 📱 **Modern Frontend**: Mobile-first responsive UI with dark mode

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Docker & Docker Compose
- API keys for GPT-4o-mini-web-search and GPT-5-nano

### 1. Clone Repository

```bash
git clone https://github.com/Zhihong0321/Eternalgy-News.git
cd Eternalgy-News
```

### 2. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
# SEARCH_API_KEY=your-search-api-key
# AI_API_KEY=your-ai-api-key
```

### 3. Start Database

```bash
docker-compose up -d
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Run Full Workflow

```bash
# Fresh start with Malaysia solar news
python fresh_start.py

# Or run specific task
python run_malaysia_solar_news.py
```

### 6. Start Frontend

```bash
python frontend/server.py
```

Open http://127.0.0.1:3000 in your browser!

## 📁 Project Structure

```
Eternalgy-News/
├── news_search/              # News discovery module
│   ├── search_client.py      # GPT-4o-mini search client
│   ├── search_module.py      # Search orchestration
│   ├── database.py           # PostgreSQL operations
│   └── processor_worker.py   # Link processing worker
│
├── ai_processing/            # Content processing module
│   ├── processor_with_content.py  # Main processor
│   ├── services/
│   │   ├── content_extractor.py   # HTTP scraping
│   │   ├── content_cleaner.py     # Content cleaning
│   │   └── translator.py          # Multi-language translation
│   └── models/
│       └── article.py        # Data models
│
├── frontend/                 # Web interface
│   ├── server.py            # FastAPI backend
│   └── index.html           # Mobile-first UI
│
├── examples/                 # Usage examples
│   ├── 01_create_query_task.py
│   ├── 02_run_search.py
│   ├── 03_process_links.py
│   └── 04_full_workflow.py
│
├── docs/                     # Documentation
│   ├── WORKFLOW_GUIDE.md
│   ├── API_DOCUMENTATION.md
│   └── DATABASE_SCHEMA.md
│
└── docker-compose.yml        # PostgreSQL setup
```

## 🔧 Available Query Tasks

The system includes 8 predefined query task templates:

1. **malaysia_solar_news** - Malaysia solar energy news
2. **malaysia_renewable_energy** - All renewable energy types in Malaysia
3. **asean_solar_projects** - Solar projects across ASEAN region
4. **global_solar_tech** - Solar technology innovations worldwide
5. **ev_charging_infrastructure** - EV charging infrastructure news
6. **renewable_energy_policy** - Renewable energy policies and regulations
7. **tech_news_daily** - Daily technology news
8. **ai_news** - AI and machine learning news

### Manage Tasks

```bash
# Interactive task manager
python manage_query_tasks.py

# List available templates
python list_tasks.py

# Create all templates
python -c "from manage_query_tasks import create_all_templates; create_all_templates()"
```

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
Stores cleaned and translated articles.

```sql
- id (serial)
- link_id (integer) - foreign key to news_links
- title (text)
- content (text) - point-form summary
- translated_content (text) - JSON with EN/ZH/MS
- tags (text[])
- country (varchar)
- news_date (date)
- metadata (jsonb)
```

### query_tasks
Manages reusable search queries.

```sql
- id (serial)
- task_name (varchar)
- prompt_template (text)
- is_active (boolean)
- last_run (timestamp)
```

## 🌐 Frontend Integration

The system outputs structured JSON ready for any frontend framework:

```json
{
  "id": 123,
  "title": "Original title",
  "title_en": "English title",
  "title_zh": "中文标题",
  "title_ms": "Tajuk Melayu",
  "content": "• Point 1\n• Point 2\n• Point 3",
  "tags": ["Solar", "Tech"],
  "country": "MY",
  "news_date": "2025-11-18",
  "detected_language": "en",
  "url": "https://example.com/article"
}
```

### API Endpoints

- `GET /api/news` - Get list of news articles
- `GET /api/news/{id}` - Get single article details
- `GET /api/tags` - Get available tags
- `POST /api/tasks/execute` - Execute a search task

## 🔄 Workflow

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
Frontend UI (FastAPI + HTML)
```

## 🛠️ Configuration

### Environment Variables

See `.env.example` for all configuration options:

- **Search API**: `SEARCH_API_URL`, `SEARCH_API_KEY`, `SEARCH_MODEL`
- **AI Processing**: `AI_API_URL`, `AI_API_KEY`, `AI_MODEL`
- **Database**: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- **Processing**: `AUTO_PROCESS_AFTER_SEARCH`, `MAX_CONCURRENT_DOMAINS`

## 🧪 Testing

```bash
# Test search module
python examples/02_run_search.py

# Test AI processor
python test_processing_fix.py

# Verify database
python verify_database.py

# Full workflow test
python examples/04_full_workflow.py
```

## 📊 Monitoring

Check processing status:

```python
from news_search import Database

db = Database()
stats = db.get_statistics()

print(f"Total links: {stats['links']['total_links']}")
print(f"Completed: {stats['links']['completed']}")
print(f"Failed: {stats['links']['failed']}")
```

## 🔧 Maintenance

### Flush Database

```bash
python flush_database.py
```

### Reprocess Links

```bash
python test_processing_fix.py
```

### View Logs

```bash
# Database logs
docker-compose logs -f postgres

# Frontend logs
# Check terminal where server is running
```

## 📖 Documentation

- [Quick Start Guide](QUICK_START.md) - Get started in 5 minutes
- [Workflow Guide](docs/WORKFLOW_GUIDE.md) - Complete workflow documentation
- [API Documentation](docs/API_DOCUMENTATION.md) - API reference
- [Database Schema](docs/DATABASE_SCHEMA.md) - Database structure
- [Architecture](docs/ARCHITECTURE.md) - System design
- [Available Query Tasks](AVAILABLE_QUERY_TASKS.md) - Predefined search tasks
- [Frontend Guide](FRONTEND_RUNNING.md) - Frontend setup and usage

## 🤝 Contributing

This is a private project. For questions or issues, contact the development team.

## 📄 License

Proprietary - All rights reserved.

## 🔗 Related Projects

- Original inspiration: [TrendRadar](https://github.com/sansan0/TrendRadar)

## 📞 Support

For support, please contact:
- GitHub: [@Zhihong0321](https://github.com/Zhihong0321)
- Repository: [Eternalgy-News](https://github.com/Zhihong0321/Eternalgy-News)

---

**Version**: 1.0.0  
**Last Updated**: 2025-11-19  
**Status**: Production Ready

**Built with ❤️ for renewable energy news aggregation**
