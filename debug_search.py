"""Debug search API to see actual response"""
import requests
import json
import os

# Load from .env
from dotenv import load_dotenv
load_dotenv()

SEARCH_API_URL = os.getenv("SEARCH_API_URL", "https://api.bltcy.ai/v1/chat/completions")
SEARCH_API_KEY = os.getenv("SEARCH_API_KEY")
SEARCH_MODEL = os.getenv("SEARCH_MODEL", "gpt-4o-mini-search-preview")

print("=" * 80)
print("DEBUG: Search API Test")
print("=" * 80)
print()
print(f"API URL: {SEARCH_API_URL}")
print(f"Model: {SEARCH_MODEL}")
print(f"API Key: {SEARCH_API_KEY[:20]}..." if SEARCH_API_KEY else "API Key: NOT SET")
print()

prompt = """
Find latest news articles about solar energy in Malaysia.
Return URLs as JSON array.
Example: [{"url": "https://example.com/article1", "title": "Article 1"}]
Limit to 5 articles.
"""

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {SEARCH_API_KEY}"
}

payload = {
    "model": SEARCH_MODEL,
    "messages": [
        {
            "role": "user",
            "content": prompt.strip()
        }
    ]
}

print("Sending request...")
print()

try:
    response = requests.post(
        SEARCH_API_URL,
        headers=headers,
        json=payload,
        timeout=60
    )
    
    print(f"Status Code: {response.status_code}")
    print()
    
    if response.status_code == 200:
        result = response.json()
        
        print("Full Response:")
        print(json.dumps(result, indent=2))
        print()
        
        # Try to extract content
        if "choices" in result and len(result["choices"]) > 0:
            message = result["choices"][0]["message"]
            content = message.get("content", "")
            annotations = message.get("annotations", [])
            
            print("=" * 80)
            print("Message Content:")
            print("=" * 80)
            print(content[:500])
            print()
            
            if annotations:
                print("=" * 80)
                print(f"Annotations ({len(annotations)} found):")
                print("=" * 80)
                for i, ann in enumerate(annotations[:5], 1):
                    print(f"{i}. Type: {ann.get('type')}")
                    if ann.get('type') == 'url_citation':
                        url_data = ann.get('url_citation', {})
                        print(f"   URL: {url_data.get('url')}")
                        print(f"   Title: {url_data.get('title', 'N/A')}")
                    print()
    else:
        print(f"Error Response:")
        print(response.text)
        
except Exception as e:
    print(f"Exception: {e}")
    import traceback
    traceback.print_exc()
