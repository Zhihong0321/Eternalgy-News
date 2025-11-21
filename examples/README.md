# Examples

Usage examples for Eternalgy-News-AI.

## Getting Started

Run examples in order:

### 1. Initialize Database
```bash
python 00_init_database.py
```
Creates all necessary database tables.

### 2. Create Query Task
```bash
python 01_create_query_task.py
```
Creates a reusable search query task.

### 3. Run Search
```bash
python 02_run_search.py
```
Discovers news URLs using AI search.

### 4. Process Links
```bash
python 03_process_links.py
```
Processes discovered links (fetch Markdown via Jina Reader, clean, translate).

### 5. Full Workflow
```bash
python 04_full_workflow.py
```
Runs the complete end-to-end workflow.

## Configuration

Make sure to configure `.env` file before running examples:
```bash
cp ../.env.example ../.env
# Edit .env with your API keys
```

## Requirements

- PostgreSQL running (via docker-compose)
- API keys configured in .env
- Python dependencies installed
