import sys
import os
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Add parent directory to path to import news_search
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from news_search.database import Database

app = FastAPI()

# Initialize database
db = Database()

class NewsItem(BaseModel):
    id: int
    url: str
    title: Optional[str]
    content: Optional[str]
    tags: Optional[List[str]]
    country: Optional[str]
    news_date: Optional[str]
    discovered_at: str
    source: Optional[str]

class QueryTaskCreateRequest(BaseModel):
    task_name: str
    prompt_template: str
    schedule: Optional[str] = None
    is_active: Optional[bool] = True


class QueryTaskUpdateRequest(BaseModel):
    prompt_template: Optional[str]
    schedule: Optional[str]
    is_active: Optional[bool]


def _run_task_by_name(task_name: str):
    """Shared helper to execute a query task"""
    return search_module.run_task(task_name)


@app.get("/api/news")
def get_news(
    limit: int = 20, 
    offset: int = 0, 
    tag: Optional[str] = None
):
    try:
        # Use the new get_news_for_frontend method which handles all formatting
        news = db.get_news_for_frontend(limit=limit, offset=offset, tag=tag)
        
        # Add source extraction for each item
        from urllib.parse import urlparse
        for item in news:
            if item.get('url'):
                try:
                    source = urlparse(item['url']).netloc.replace('www.', '')
                    item['source'] = source
                except:
                    item['source'] = "Unknown"
            else:
                item['source'] = "Unknown"
            
        return news
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/news/{id}")
def get_news_detail(id: int):
    try:
        item = db.get_processed_content(id)
        if not item:
            raise HTTPException(status_code=404, detail="News not found")
        
        # Get URL from news_links table if not in processed_content
        # Actually get_processed_content only returns processed_content table fields
        # We need to join with news_links to get the URL
        # Let's assume the frontend passes the URL or we fetch it here.
        # Ideally get_processed_content should probably join, but let's check database.py
        # database.py's get_processed_content only selects from processed_content.
        # We should probably update database.py or do a separate query.
        # For now, let's just return what we have, and maybe the frontend can use the URL it already has from the list.
        # Wait, the user wants to "expand" the article. The list view already has the content.
        # But let's provide a dedicated endpoint for cleanliness and potential future expansion (e.g. full text vs summary).
        
        # Let's do a quick join here or just return the item.
        # Actually, let's fetch the URL too.
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT url FROM news_links WHERE id = %s", (item['link_id'],))
            result = cursor.fetchone()
            url = result[0] if result else None
            
        # Extract source
        source = "Unknown"
        if url:
            from urllib.parse import urlparse
            try:
                source = urlparse(url).netloc.replace('www.', '')
            except:
                pass
                
        return {
            "id": item['link_id'], # Use link_id as the ID exposed to frontend
            "url": url,
            "title": item['title'],
            "content": item['content'],
            "translated_content": item['translated_content'],
            "tags": item['tags'] or [],
            "country": item['country'],
            "news_date": str(item['news_date']) if item['news_date'] else None,
            "source": source,
            "metadata": item['metadata']
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tags")
def get_tags():
    # Get unique tags from database
    # This is a simple implementation, ideally we'd have a tags table or cached stats
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT unnest(tags) as tag 
                FROM processed_content 
                LIMIT 50
            """)
            tags = [row[0] for row in cursor.fetchall()]
            return tags
    except Exception as e:
        print(f"Error fetching tags: {e}")
        return ["Tech", "AI", "Business", "World"] # Fallback

@app.get("/api/status")
def get_status():
    try:
        latest = db.get_latest_task_run()
        if not latest:
            return {"task_name": None, "last_run": None}
        last_run = latest.get("last_run")
        if hasattr(last_run, "isoformat"):
            last_run = last_run.isoformat()
        return {
            "task_name": latest.get("task_name"),
            "last_run": last_run
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Initialize search module
from news_search.search_module import NewsSearchModule
from news_search.processor_worker import ProcessorWorker
from ai_processing.processor_with_content import ArticleProcessorWithContent
from ai_processing.processor_adapter import ProcessorAdapter

# Try to initialize AI processor
try:
    ai_processor = ArticleProcessorWithContent.from_env()
    adapter = ProcessorAdapter(ai_processor)
    processor_worker = ProcessorWorker(ai_processor=adapter)
    search_module = NewsSearchModule(processor_worker=processor_worker)
except Exception as e:
    print(f"Warning: AI processor initialization failed: {e}")
    # Fallback to mock processor
    processor_worker = ProcessorWorker()
    search_module = NewsSearchModule(processor_worker=processor_worker)

class TaskExecutionRequest(BaseModel):
    task_name: str

@app.post("/api/tasks/execute")
def execute_task(request: TaskExecutionRequest):
    try:
        result = _run_task_by_name(request.task_name)
        
        # If search found new links, ensure they are processed
        # The search_module.run_task already calls auto-process if configured,
        # but let's be explicit if we want to force it or if auto-process is off.
        # For now, we rely on search_module's logic which checks AUTO_PROCESS_AFTER_SEARCH.
        
        # However, we might want to trigger processing for pending links regardless
        # just in case.
        if result.get('success'):
             # Process any pending links (including ones just found if auto-process didn't catch them)
             # Note: This might take time, so ideally background task.
             # For this demo, we'll do a quick check.
             pass
             
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tasks")
def list_query_tasks():
    try:
        tasks = db.get_all_tasks()
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tasks")
def create_query_task(request: QueryTaskCreateRequest):
    if not request.task_name.strip():
        raise HTTPException(status_code=400, detail="Task name is required.")
    if not request.prompt_template.strip():
        raise HTTPException(status_code=400, detail="Prompt template is required.")

    try:
        task_id = db.create_query_task(
            task_name=request.task_name.strip(),
            prompt_template=request.prompt_template.strip(),
            schedule=request.schedule,
            is_active=request.is_active if request.is_active is not None else True
        )
        return {"success": True, "task_id": task_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/tasks/{task_name}")
def update_query_task(task_name: str, request: QueryTaskUpdateRequest):
    if not any([request.prompt_template is not None, request.schedule is not None, request.is_active is not None]):
        raise HTTPException(status_code=400, detail="No update fields provided.")

    try:
        updated = db.update_query_task(
            task_name,
            prompt_template=(request.prompt_template.strip() if request.prompt_template is not None else None),
            schedule=(request.schedule.strip() if request.schedule is not None else None),
            is_active=request.is_active
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Task not found.")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/tasks/{task_name}")
def delete_query_task(task_name: str):
    try:
        deleted = db.delete_query_task(task_name)
        if not deleted:
            raise HTTPException(status_code=404, detail="Task not found.")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tasks/{task_name}/run")
def run_query_task(task_name: str):
    try:
        return _run_task_by_name(task_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Serve static files
# We'll serve the current directory as static
app.mount("/", StaticFiles(directory="frontend", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "3000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
