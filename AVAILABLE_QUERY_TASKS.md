# Available Query Tasks

This document lists all predefined query task templates available in the system.

---

## Current Tasks in Database

**Status**: Database is empty (just flushed)

Run this to check current tasks:
```bash
python manage_query_tasks.py
# Choose option 1
```

---

## Predefined Task Templates

### 1. **malaysia_solar_news**
**Description**: Malaysia solar energy news  
**Focus**: Solar projects, installations, policies, companies in Malaysia  
**Limit**: 15 articles

**Prompt**:
```
Find latest news articles about solar energy in Malaysia.
Focus on: solar projects, solar installations, renewable energy policies, solar companies.
Return URLs as JSON array with titles.
Limit to 15 most relevant articles.
```

---

### 2. **malaysia_renewable_energy**
**Description**: Malaysia renewable energy (all types)  
**Focus**: Solar, wind, hydroelectric, policies, green energy projects  
**Limit**: 15 articles

**Prompt**:
```
Find latest news about renewable energy in Malaysia.
Focus on: solar, wind, hydroelectric, renewable energy policies, green energy projects.
Return URLs as JSON array with titles.
Limit to 15 articles.
```

---

### 3. **asean_solar_projects**
**Description**: ASEAN region solar projects  
**Focus**: Malaysia, Singapore, Thailand, Indonesia, Philippines, Vietnam  
**Limit**: 20 articles

**Prompt**:
```
Find latest news about solar energy projects in ASEAN countries.
Focus on: Malaysia, Singapore, Thailand, Indonesia, Philippines, Vietnam.
Include: large-scale solar projects, solar installations, solar policies.
Return URLs as JSON array with titles.
Limit to 20 articles.
```

---

### 4. **global_solar_tech**
**Description**: Global solar technology innovations  
**Focus**: New solar panel tech, efficiency, storage, research  
**Limit**: 15 articles

**Prompt**:
```
Find latest news about solar technology innovations and breakthroughs.
Focus on: new solar panel technology, efficiency improvements, solar storage, solar research.
Return URLs as JSON array with titles.
Limit to 15 articles.
```

---

### 5. **ev_charging_infrastructure**
**Description**: EV charging infrastructure news  
**Focus**: Charging stations, networks, projects, technology  
**Limit**: 15 articles

**Prompt**:
```
Find latest news about electric vehicle (EV) charging infrastructure.
Focus on: charging stations, charging networks, EV infrastructure projects, charging technology.
Return URLs as JSON array with titles.
Limit to 15 articles.
```

---

### 6. **renewable_energy_policy**
**Description**: Renewable energy policies and regulations  
**Focus**: Government policies, targets, subsidies, regulations, agreements  
**Limit**: 15 articles

**Prompt**:
```
Find latest news about renewable energy policies and regulations.
Focus on: government policies, renewable energy targets, subsidies, regulations, international agreements.
Return URLs as JSON array with titles.
Limit to 15 articles.
```

---

### 7. **tech_news_daily**
**Description**: Daily technology news  
**Focus**: AI, ML, software, tech companies, innovations  
**Limit**: 20 articles

**Prompt**:
```
Find latest technology news articles from today.
Focus on: AI, machine learning, software development, tech companies, tech innovations.
Return URLs as JSON array with titles.
Limit to 20 articles.
```

---

### 8. **ai_news**
**Description**: AI and machine learning news  
**Focus**: AI breakthroughs, applications, companies, research, ethics  
**Limit**: 15 articles

**Prompt**:
```
Find latest artificial intelligence and machine learning news.
Focus on: AI breakthroughs, AI applications, AI companies, AI research, AI ethics.
Return URLs as JSON array with titles.
Limit to 15 articles.
```

---

## How to Use

### Option 1: Interactive Manager

```bash
python manage_query_tasks.py
```

This provides an interactive menu to:
- List tasks in database
- List available templates
- Create task from template
- Create all template tasks at once
- Create custom task

### Option 2: Create All Templates

```python
from news_search import Database

db = Database()

# Create all predefined tasks
tasks = [
    "malaysia_solar_news",
    "malaysia_renewable_energy",
    "asean_solar_projects",
    "global_solar_tech",
    "ev_charging_infrastructure",
    "renewable_energy_policy",
    "tech_news_daily",
    "ai_news"
]

for task_name in tasks:
    # Use manage_query_tasks.py templates
    pass
```

### Option 3: Create Single Task

```python
from news_search import Database

db = Database()

task_id = db.create_query_task(
    task_name="my_custom_task",
    prompt_template="Your search prompt here..."
)
```

### Option 4: Run Existing Task

```python
from news_search import NewsSearchModule

search = NewsSearchModule()
result = search.run_task("malaysia_solar_news")

print(f"Found: {result['new_links']} new articles")
```

---

## Task Management Commands

### List All Tasks
```bash
python -c "
from news_search import Database
db = Database()
tasks = db.get_active_tasks()
for task in tasks:
    print(f'{task[\"task_name\"]}: {task[\"total_runs\"]} runs, {task[\"total_links_found\"]} links')
"
```

### Check Task Status
```bash
python -c "
from news_search import Database
db = Database()
task = db.get_query_task('malaysia_solar_news')
if task:
    print(f'Task: {task[\"task_name\"]}')
    print(f'Active: {task[\"is_active\"]}')
    print(f'Last Run: {task[\"last_run\"]}')
    print(f'Total Runs: {task[\"total_runs\"]}')
else:
    print('Task not found')
"
```

### Run Task
```bash
python -c "
from news_search import NewsSearchModule
search = NewsSearchModule()
result = search.run_task('malaysia_solar_news')
print(f'Found {result[\"new_links\"]} new articles')
"
```

---

## Creating Custom Tasks

### Template Format

```python
task_name = "your_task_name"
prompt = """
Find latest news about [YOUR TOPIC].
Focus on: [specific aspects, keywords, regions].
Return URLs as JSON array with titles.
Example: [{"url": "https://...", "title": "..."}, ...]
Limit to [N] articles.
"""

db.create_query_task(task_name, prompt.strip())
```

### Best Practices

1. **Be Specific**: Include specific keywords and focus areas
2. **Set Limits**: Specify number of articles (10-20 recommended)
3. **Request Format**: Always ask for JSON array with URLs and titles
4. **Geographic Focus**: Specify regions/countries if relevant
5. **Time Frame**: Mention "latest" or "recent" for current news

### Example Custom Tasks

**Blockchain News**:
```python
prompt = """
Find latest news about blockchain technology and cryptocurrency.
Focus on: blockchain applications, crypto regulations, DeFi, NFTs, major crypto projects.
Return URLs as JSON array with titles.
Limit to 15 articles.
"""
```

**Climate Change News**:
```python
prompt = """
Find latest news about climate change and environmental issues.
Focus on: climate policies, carbon emissions, climate science, environmental activism.
Return URLs as JSON array with titles.
Limit to 15 articles.
```

**Space Technology**:
```python
prompt = """
Find latest news about space exploration and space technology.
Focus on: SpaceX, NASA, satellite technology, space missions, space research.
Return URLs as JSON array with titles.
Limit to 15 articles.
"""
```

---

## Scheduling Tasks (Future)

Tasks can be scheduled to run automatically:

```python
db.create_query_task(
    task_name="daily_solar_news",
    prompt_template="...",
    schedule="daily"  # or "hourly", "weekly", etc.
)
```

Then set up cron job:
```bash
# Run daily at 8 AM
0 8 * * * cd /path/to/project && python run_task.py daily_solar_news
```

---

## Task Statistics

View task performance:

```python
from news_search import Database

db = Database()
stats = db.get_statistics()

print(f"Total Tasks: {stats['tasks']['total_tasks']}")
print(f"Active Tasks: {stats['tasks']['active_tasks']}")

# Get individual task stats
task = db.get_query_task("malaysia_solar_news")
print(f"Total Runs: {task['total_runs']}")
print(f"Links Found: {task['total_links_found']}")
print(f"Avg per Run: {task['total_links_found'] / task['total_runs']}")
```

---

## Summary

- **8 predefined templates** ready to use
- **Interactive manager** for easy task creation
- **Custom tasks** supported
- **Flexible prompts** for any news topic
- **Statistics tracking** for each task

Use `python manage_query_tasks.py` to get started!
