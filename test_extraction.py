from ai_processing.services.content_extractor import ContentExtractor
import json

url = "https://apnews.com/article/4e7e5b1a7df946169c72c1df58f90295"
extractor = ContentExtractor()
print(f"Extracting content from: {url}")
result = extractor.extract_content(url)

if result:
    print("Extraction successful!")
    print(f"Title: {result.get('title')}")
    print(f"Content Length: {len(result.get('content', ''))}")
    print(f"Excerpt: {result.get('excerpt')}")
else:
    print("Extraction failed.")
