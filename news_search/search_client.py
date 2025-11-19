"""Search client for GPT-4o-mini-search-preview"""
import requests
import json
from typing import List, Optional
from .config import SEARCH_API_URL, SEARCH_API_KEY, SEARCH_MODEL, REQUEST_TIMEOUT


class SearchClient:
    def __init__(self, api_key: str = None, model: str = None):
        self.api_url = SEARCH_API_URL
        self.api_key = api_key or SEARCH_API_KEY
        self.model = model or SEARCH_MODEL
    
    def search(self, prompt: str) -> Optional[List[str]]:
        """
        Execute search query and return list of URLs
        
        Args:
            prompt: Search prompt (should request URLs in array format)
        
        Returns:
            List of URLs or None if error
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Try to use structured output if model supports it
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        # Add response_format for models that support it (not search-preview)
        if "search" not in self.model.lower():
            payload["response_format"] = {
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
                                },
                                "description": "List of news articles with URLs and titles"
                            }
                        },
                        "required": ["results"],
                        "additionalProperties": False
                    }
                }
            }
        
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                result = response.json()
                message = result["choices"][0]["message"]
                content = message.get("content", "")
                
                # Parse structured JSON response
                try:
                    # Try to extract JSON from markdown code blocks
                    json_content = content
                    if "```json" in content:
                        # Extract JSON from markdown code block
                        start = content.find("```json") + 7
                        end = content.find("```", start)
                        if end > start:
                            json_content = content[start:end].strip()
                    elif "```" in content:
                        # Try generic code block
                        start = content.find("```") + 3
                        end = content.find("```", start)
                        if end > start:
                            json_content = content[start:end].strip()
                    
                    data = json.loads(json_content)
                    
                    # Handle array directly (most common format)
                    if isinstance(data, list):
                        cleaned_results = []
                        for item in data:
                            if isinstance(item, dict) and "url" in item:
                                url = item["url"].split("?utm_source=")[0]
                                cleaned_results.append({
                                    "url": url,
                                    "title": item.get("title", "")
                                })
                        if cleaned_results:
                            print(f"Extracted {len(cleaned_results)} results from JSON array")
                            return cleaned_results
                    
                    # Handle both old format (urls list) and new format (results list of dicts)
                    if "results" in data:
                        results = data["results"]
                        cleaned_results = []
                        for item in results:
                            if isinstance(item, dict) and "url" in item:
                                url = item["url"].split("?utm_source=")[0]
                                cleaned_results.append({
                                    "url": url,
                                    "title": item.get("title", "")
                                })
                        print(f"Extracted {len(cleaned_results)} results from structured response")
                        return cleaned_results
                    elif "urls" in data:
                        # Backward compatibility
                        urls = data["urls"]
                        cleaned_results = []
                        for url in urls:
                            if isinstance(url, str):
                                clean_url = url.split("?utm_source=")[0]
                                cleaned_results.append({
                                    "url": clean_url,
                                    "title": ""
                                })
                        print(f"Extracted {len(cleaned_results)} URLs from structured response (legacy)")
                        return cleaned_results
                    
                except json.JSONDecodeError:
                    # Content is not JSON, try annotations fallback
                    pass
                
                # Fallback: Check for annotations (search-preview format)
                annotations = message.get("annotations", [])
                if annotations:
                    results = []
                    for annotation in annotations:
                        if annotation.get("type") == "url_citation":
                            url_data = annotation.get("url_citation", {})
                            url = url_data.get("url", "")
                            title = url_data.get("title", "") # Annotations might have title
                            if url:
                                url = url.split("?utm_source=")[0]
                                results.append({
                                    "url": url,
                                    "title": title
                                })
                    
                    if results:
                        print(f"Extracted {len(results)} results from annotations (fallback)")
                        return results
                
                print(f"Could not extract URLs from response")
                return None
            else:
                print(f"API Error {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            print(f"Request timed out after {REQUEST_TIMEOUT} seconds")
            return None
        except Exception as e:
            print(f"Search error: {str(e)}")
            return None
    
    def get_usage_stats(self, response_data: dict) -> dict:
        """Extract token usage from API response"""
        if "usage" in response_data:
            usage = response_data["usage"]
            return {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0)
            }
        return {}
