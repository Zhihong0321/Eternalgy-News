from ai_processing.services.jina_reader import JinaReader, JinaReaderConfig
import os

url = "https://apnews.com/article/4e7e5b1a7df946169c72c1df58f90295"
config = JinaReaderConfig(api_key=os.getenv("READER_API_KEY", os.getenv("AI_API_KEY", "")), max_content_length=4000)
reader = JinaReader(config=config)

print(f"Extracting content from: {url}")
result = reader.read_url(url)

if result and result.get('content'):
    print("Extraction successful via reader!")
    print(f"Title: {result.get('title')}")
    print(f"Content Length: {len(result.get('content', ''))}")
    print(f"Excerpt: {result.get('excerpt')}")
else:
    print("Extraction failed.")
    print("Error:", result.get('error') if isinstance(result, dict) else "Unknown")
