import sys
import os
from typing import Optional, List, Dict
import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Add parent directory to path to import news_search
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from news_search.database import Database
from news_search.search_client import SearchClient
from ai_processing.services.news_rewriter_prompt import NEWS_REWRITER_TEMPLATE

app = FastAPI()

# Initialize database
db = Database()
# Ensure tables exist (creates tables if missing)
try:
    db.init_tables()
except Exception as e:
    print(f"Warning: database init_tables failed: {e}")

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


def _check_database() -> Dict[str, str]:
    """Validate DB connectivity with a lightweight select."""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1;")
            cursor.fetchone()
            cursor.close()
        return {"status": "ok"}
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}


def _check_ai_api() -> Dict[str, str]:
    """
    Validate the AI API key by issuing a minimal chat completion.
    If no key is set, report as skipped.
    """
    ai_config = AIConfig.from_env()
    if not ai_config.api_key:
        return {"status": "skipped", "reason": "AI_API_KEY not set"}

    try:
        client = AIClient(
            api_url=ai_config.api_url,
            api_key=ai_config.api_key,
            model=ai_config.model,
            timeout=min(ai_config.timeout, 10),
            max_retries=1,
        )
        response = client.chat_completion(
            messages=[{"role": "user", "content": "healthcheck"}],
            temperature=0.0,
            max_tokens=8,
        )
        preview = client.extract_content(response)[:80]
        return {"status": "ok", "model": ai_config.model, "preview": preview}
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}


def _check_reader() -> Dict[str, str]:
    """
    Validate the search-based reader is configured.
    We treat missing credentials as skipped; no live call to avoid token burn.
    """
    config = JinaReaderConfig()  # alias for ReaderConfig
    if not config.api_key:
        return {"status": "skipped", "reason": "READER_API_KEY/SEARCH_API_KEY not set"}
    return {"status": "ok", "model": config.model}


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
from ai_processing.config import AIConfig
from ai_processing.services.ai_client import AIClient
from ai_processing.services.jina_reader import JinaReader, JinaReaderConfig

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


@app.get("/api/tasks/{task_name}/recent")
def recent_processed(task_name: str, limit: int = 5):
    """Return recent processed/attempted items for a task."""
    try:
        return db.get_recent_processed(task_name, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tasks/{task_name}/reprocess")
def reprocess_task_links(task_name: str, limit: int = 50):
    """
    Reprocess pending/failed links for a task.
    """
    try:
        links = db.get_links_by_status(task_name, ["pending", "failed"], limit=limit)
        if not links:
            return {"success": True, "processed": 0, "message": "No pending/failed links"}

        if not processor_worker or not getattr(processor_worker, "ai_processor", None):
            raise HTTPException(status_code=400, detail="AI processor is not configured")

        link_ids = [item["id"] for item in links]
        result = processor_worker.process_specific_links(link_ids)
        return {
            "success": True,
            "requested": len(link_ids),
            "result": result,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rewriter/prompt")
def get_rewriter_prompt():
    """Return the stored News Rewriter prompt and model."""
    try:
        settings = db.get_rewriter_prompt()
        # Fallbacks to env/template if none saved yet
        prompt = settings.get("prompt") or NEWS_REWRITER_TEMPLATE
        model = settings.get("model") or os.getenv("AI_MODEL", "")
        return {"prompt": prompt or "", "model": model}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class RewriterPromptUpdateRequest(BaseModel):
    prompt: str
    model: Optional[str] = None


@app.put("/api/rewriter/prompt")
def set_rewriter_prompt(request: RewriterPromptUpdateRequest):
    """Save the News Rewriter prompt and model."""
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")
    try:
        db.set_rewriter_prompt(request.prompt, request.model.strip() if request.model else None)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
# Pipeline Reveal (no DB writes)
# -----------------------------

def _wrap_search_prompt(user_intent: str) -> str:
    return f"""
You are a news URL selector. Based on the user intent, return ONLY a JSON array (no Markdown/code fences/text) of up to 10 objects:
[{{"url": "https://...", "title": "Story title"}}]
Rules:
- Output must be valid JSON: an array of objects with keys "url" and "title" only.
- Strip tracking params; use canonical article URLs when possible.
- Deduplicate URLs; prefer recent, source-matched results.
- Exclude social media, video shorts, ads, nav pages, or homepages.
- Do not include explanations or any text before/after the JSON array.

User intent: {user_intent}
""".strip()


@app.post("/api/pipeline/search")
def pipeline_search(body: Dict):
    """Run search with strict wrapper; no DB writes."""
    intent = (body or {}).get("prompt", "").strip()
    if not intent:
        raise HTTPException(status_code=400, detail="prompt is required")
    wrapped = _wrap_search_prompt(intent)
    client = SearchClient()
    raw_response = None
    try:
        resp = requests.post(
            client.api_url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {client.api_key}"
            },
            json={
                "model": client.model,
                "messages": [{"role": "user", "content": wrapped}],
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "news_results",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "results": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "url": {"type": "string"},
                                            "title": {"type": "string"}
                                        },
                                        "required": ["url", "title"],
                                        "additionalProperties": False
                                    }
                                }
                            },
                            "required": ["results"],
                            "additionalProperties": False
                        }
                    }
                }
            },
            timeout=60
        )
        raw_response = resp.text
        resp.raise_for_status()
        data = resp.json()
        message = data["choices"][0]["message"]
        content = message.get("content", "")
        parsed = []
        try:
            from json import loads
            payload = content
            if "```" in content:
                start = content.find("```")
                end = content.find("```", start + 3)
                if end > start:
                    payload = content[start + 3:end].strip()
            payload_json = loads(payload)
            if isinstance(payload_json, dict) and "results" in payload_json:
                for item in payload_json["results"]:
                    if isinstance(item, dict) and item.get("url"):
                        parsed.append({"url": item["url"], "title": item.get("title", "")})
            elif isinstance(payload_json, list):
                for item in payload_json:
                    if isinstance(item, dict) and item.get("url"):
                        parsed.append({"url": item["url"], "title": item.get("title", "")})
        except Exception:
            parsed = []
        return {
            "success": True,
            "wrapped_prompt": wrapped,
            "parsed": parsed,
            "raw": raw_response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)} | raw={raw_response}")


@app.post("/api/pipeline/jina")
def pipeline_jina(body: Dict):
    """Fetch a URL via the search-based reader and return parsed content."""
    url = (body or {}).get("url", "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="url is required")
    reader = JinaReader()
    result = reader.read_url(url)
    if not result or result.get("error"):
        raise HTTPException(status_code=500, detail=result.get("error", "Reader failed"))
    return {"success": True, "parsed": result}


@app.post("/api/pipeline/rewrite")
def pipeline_rewrite(body: Dict):
    """Run the news rewriter with user-provided prompt/model on provided content."""
    title = (body or {}).get("title", "")
    date = (body or {}).get("date", "")
    url = (body or {}).get("url", "")
    content = (body or {}).get("content", "")
    prompt_template = (body or {}).get("prompt", "")
    model = (body or {}).get("model", "") or os.getenv("REWRITER_MODEL", os.getenv("AI_MODEL", "openai/gpt-oss-20b:free"))
    api_key = os.getenv("REWRITER_API_KEY") or os.getenv("AI_API_KEY", "")
    api_url = os.getenv("REWRITER_API_URL") or os.getenv("AI_API_URL", "https://openrouter.ai/api/v1")
    if not prompt_template:
        raise HTTPException(status_code=400, detail="prompt is required")
    if not content:
        raise HTTPException(status_code=400, detail="content is required")
    if not api_key:
        raise HTTPException(status_code=500, detail="REWRITER_API_KEY/AI_API_KEY is not configured on the server")
    if not api_url:
        raise HTTPException(status_code=500, detail="REWRITER_API_URL/AI_API_URL is not configured on the server")

    # Substitute placeholders if present
    prompt = prompt_template.replace("{title}", title).replace("{date}", date).replace("{url}", url).replace("{content}", content)

    client = AIClient(
        api_url=api_url,
        api_key=api_key,
        model=model or os.getenv("AI_MODEL", ""),
        timeout=60,
        max_retries=2
    )
    raw_response = None
    try:
        resp = client.chat_completion(
            messages=[
                {"role": "system", "content": "You are a careful, neutral news rewriter."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=800
        )
        raw_response = resp
        text = client.extract_content(resp)
        parsed = None
        error = None
        try:
            import json
            parsed = json.loads(text)
        except Exception as exc:
            error = f"parse error: {exc}"
        return {
            "success": True,
            "raw_text": text,
            "raw_response": raw_response,
            "parsed": parsed,
            "error": error
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rewrite failed: {str(e)} | raw={raw_response}")


@app.post("/api/tasks/{task_name}/reprocess-missing")
def reprocess_completed_missing(task_name: str, limit: int = 50):
    """
    Reprocess links marked completed but without processed_content rows.
    """
    try:
        links = db.get_completed_missing_content(task_name, limit=limit)
        if not links:
            return {"success": True, "processed": 0, "message": "No completed links missing content"}

        if not processor_worker or not getattr(processor_worker, "ai_processor", None):
            raise HTTPException(status_code=400, detail="AI processor is not configured")

        link_ids = [item["id"] for item in links]
        result = processor_worker.process_specific_links(link_ids)
        return {
            "success": True,
            "requested": len(link_ids),
            "result": result,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    """
    Health check endpoint that validates:
    - Database connectivity
    - AI API token handshake when a key is provided
    - Jina Reader handshake when a key is provided
    """
    checks = {
        "database": _check_database(),
        "ai_api": _check_ai_api(),
        "reader": _check_reader(),
    }

    overall_status = "ok"
    for check in checks.values():
        if check.get("status") == "failed":
            overall_status = "failed"
            break
        if overall_status == "ok" and check.get("status") == "skipped":
            overall_status = "degraded"

    return {
        "status": overall_status,
        "checks": checks,
        "region": os.getenv("REGION", "unknown"),
        "version": os.getenv("RAILWAY_GIT_COMMIT_SHA") or os.getenv("COMMIT_SHA"),
    }

# Serve static files
# We'll serve the current directory as static
app.mount("/", StaticFiles(directory="frontend", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "3000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
