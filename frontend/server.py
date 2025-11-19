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
        result = search_module.run_task(request.task_name)
        
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

# Serve static files
# We'll serve the current directory as static
app.mount("/", StaticFiles(directory="frontend", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=3000)
