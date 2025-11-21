"""Main search module for news discovery"""
from typing import List, Dict
from datetime import datetime
from .search_client import SearchClient
from .database import Database, hash_url
from .url_normalizer import normalize_url, is_valid_url
from .config import AUTO_PROCESS_AFTER_SEARCH


class NewsSearchModule:
    def __init__(self, processor_worker=None):
        self.search_client = SearchClient()
        self.db = Database()
        self.processor_worker = processor_worker

    def _build_search_prompt(self, user_intent: str) -> str:
        """
        Wrap the user-provided intent in a strict schema so the model always
        returns a predictable JSON array of URL/title pairs.
        """
        return f"""
You are a news URL selector. Based on the user intent, return ONLY a JSON array (no Markdown/code fences/text) of up to 10 objects:
[{{"url": "https://...", "title": "Story title"}}]
Rules:
- Output must be valid JSON: an array of objects with keys "url" and "title" only.
- Strip tracking params; use canonical article URLs when possible.
- Deduplicate URLs; prefer recent, source-relevant results that match time/location/topic hints.
- Exclude social media, video shorts, ads, nav pages, or site front pages.
- Do not include explanations or any text before/after the JSON array.

User intent: {user_intent}
""".strip()
    
    def execute_search(self, prompt: str, task_name: str, model_override: str = None) -> Dict:
        """
        Execute a search query and save results to database
        
        Args:
            prompt: Search prompt
            task_name: Name of the query task
            model_override: Optional model name to use for this task
        
        Returns:
            Dictionary with search results and statistics
        """
        print(f"Executing search for task: {task_name}")
        print(f"Prompt: {prompt}")

        # Build a client with per-task model if provided
        search_client = SearchClient(model=model_override) if model_override else self.search_client

        wrapped_prompt = self._build_search_prompt(prompt)
        
        # Execute search
        urls = search_client.search(wrapped_prompt)
        
        if urls is None:
            error_reason = search_client.last_error or "unknown error"
            return {
                "success": False,
                "error": f"Search failed: {error_reason}",
                "task_name": task_name
            }
        
        print(f"Found {len(urls)} URLs")
        
        # Process and save URLs
        results = self._process_urls(urls, task_name)
        
        # Update task statistics
        self.db.update_task_run_stats(task_name, results["new_links"])
        
        search_result = {
            "success": True,
            "task_name": task_name,
            "total_found": len(urls),
            "new_links": results["new_links"],
            "duplicates": results["duplicates"],
            "invalid": results["invalid"],
            "urls": results["urls"]
        }
        
        processing_result = None
        # Auto-process new links if enabled and processor is available
        if (
            AUTO_PROCESS_AFTER_SEARCH
            and self.processor_worker
            and getattr(self.processor_worker, "ai_processor", None)
            and results["new_links"] > 0
        ):
            print(f"\nAuto-processing {results['new_links']} new links...")
            new_link_ids = [item["id"] for item in results["urls"]]
            processing_result = self.processor_worker.process_specific_links(new_link_ids)
            search_result["processing"] = processing_result
        elif AUTO_PROCESS_AFTER_SEARCH and not getattr(self.processor_worker, "ai_processor", None):
            print("Auto-processing skipped: AI processor not configured.")
            processing_result = {
                "status": "skipped",
                "reason": "AI processor not configured",
                "details": [],
                "total": results["new_links"],
                "success": 0,
                "failed": 0,
                "skipped": results["new_links"],
            }
            search_result["processing"] = processing_result
        
        # Persist a run summary for UI visibility
        search_summary = {
            "total_urls": len(urls) if urls else 0,
            "new_links": results["new_links"],
            "duplicates": results["duplicates"],
            "invalid": results["invalid"],
            "urls": results["urls"][:20],
        }

        processing_summary = processing_result or {}
        run_summary = {
            "task_name": task_name,
            "executed_at": datetime.utcnow().isoformat() + "Z",
            "search": search_summary,
            "processing": processing_summary,
        }

        try:
            self.db.record_task_run(task_name, run_summary)
        except Exception as e:
            print(f"Warning: failed to record task run summary: {e}")

        return search_result
    
    def _process_urls(self, results: List[any], task_name: str) -> Dict:
        """Process and save URLs to database"""
        new_links = 0
        duplicates = 0
        invalid = 0
        processed_urls = []
        
        for item in results:
            # Handle both dict (new format) and str (old format)
            if isinstance(item, dict):
                url = item.get("url")
                title = item.get("title")
            else:
                url = item
                title = None
                
            # Validate URL
            if not is_valid_url(url):
                print(f"Invalid URL: {url}")
                invalid += 1
                continue
            
            # Normalize URL
            normalized_url = normalize_url(url)
            url_hash_value = hash_url(normalized_url)
            
            # Check if exists
            if self.db.url_exists(url_hash_value):
                print(f"Duplicate: {normalized_url}")
                # Update title if we have one and the existing one might be missing
                if title:
                    self.db.update_news_link_title(url_hash_value, title)
                duplicates += 1
                continue
            
            # Insert new link
            link_id = self.db.insert_news_link(normalized_url, url_hash_value, task_name, title)
            
            if link_id:
                print(f"New link saved (ID: {link_id}): {normalized_url}")
                new_links += 1
                processed_urls.append({
                    "id": link_id,
                    "url": normalized_url,
                    "original_url": url,
                    "title": title
                })
        
        return {
            "new_links": new_links,
            "duplicates": duplicates,
            "invalid": invalid,
            "urls": processed_urls
        }
    
    def run_task(self, task_name: str) -> Dict:
        """
        Run a query task by name
        
        Args:
            task_name: Name of the task to run
        
        Returns:
            Dictionary with execution results
        """
        # Get task from database
        task = self.db.get_query_task(task_name)
        
        if not task:
            return {
                "success": False,
                "error": f"Task '{task_name}' not found"
            }
        
        if not task["is_active"]:
            return {
                "success": False,
                "error": f"Task '{task_name}' is not active"
            }
        
        # Execute search with task's prompt and optional model
        return self.execute_search(task["prompt_template"], task_name, model_override=task.get("model"))
    
    def get_pending_links(self, limit: int = 100) -> List[Dict]:
        """Get pending news links for processing"""
        return self.db.get_pending_links(limit)
