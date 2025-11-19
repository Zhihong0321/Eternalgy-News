"""
REAL WORKFLOW TEST - NO MOCKS!

This script tests the complete workflow with REAL:
- HTTP scraping
- Content extraction
- AI cleaning
- AI translation (EN, ZH, MS)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from news_search import Database, ProcessorWorker
from ai_processing.processor_with_content import ArticleProcessorWithContent
from ai_processing.config import AIConfig

print("=" * 80)
print("🔥 REAL WORKFLOW TEST - NO MOCKS!")
print("=" * 80)
print()

# Step 1: Get a pending link
print("Step 1: Getting pending link from database...")
db = Database()
pending = db.get_pending_links(limit=1)

if not pending:
    print("✗ No pending links found!")
    print("  Run examples/02_run_search.py first to discover URLs")
    sys.exit(1)

link = pending[0]
print(f"✓ Found link ID: {link['id']}")
print(f"  URL: {link['url']}")
print()

# Step 2: Initialize REAL AI processor
print("Step 2: Initializing REAL AI processor...")
config = AIConfig.from_env()
print(f"  API URL: {config.api_url}")
print(f"  Model: {config.model}")
print(f"  API Key: {config.api_key[:20]}...")
print()

processor = ArticleProcessorWithContent(config=config)
print("✓ AI processor initialized")
print()

# Step 3: Process the link with REAL HTTP scraping
print("Step 3: Processing link (REAL HTTP + AI)...")
print(f"  URL: {link['url']}")
print()

try:
    # Update status to processing
    db.update_link_status(link['id'], 'processing')
    
    # REAL processing - create a RawArticle object
    from ai_processing.models.article import RawArticle
    
    raw_article = RawArticle(
        id=link['id'],
        title="",  # Will be extracted from URL
        platform="web",
        rank=1,
        url=link['url'],
        timestamp=link['discovered_at']
    )
    
    results = processor.process_articles([raw_article])
    result = results[0] if results else None
    
    if result:
        print("✓ Processing successful!")
        print()
        print("=" * 80)
        print("📄 EXTRACTED CONTENT")
        print("=" * 80)
        print(f"Title: {result.title[:100]}...")
        print(f"Content length: {len(result.content)} characters")
        print()
        print("Content preview:")
        print(result.content[:500])
        print("...")
        print()
        
        print("=" * 80)
        print("🧹 CLEANED CONTENT")
        print("=" * 80)
        print(f"Cleaned title: {result.title_cleaned[:100]}...")
        print()
        print("Cleaned content preview:")
        print(result.content_cleaned[:500] if result.content_cleaned else "N/A")
        print("...")
        print()
        
        print("=" * 80)
        print("🌐 TRANSLATIONS")
        print("=" * 80)
        print(f"Detected language: {result.detected_language}")
        print()
        print(f"English (EN):")
        print(f"  {result.title_en[:100]}...")
        print()
        print(f"Chinese (ZH):")
        print(f"  {result.title_zh[:100]}...")
        print()
        print(f"Malay (MS):")
        print(f"  {result.title_ms[:100]}...")
        print()
        
        # Save to database
        print("=" * 80)
        print("💾 SAVING TO DATABASE")
        print("=" * 80)
        
        metadata = {
            "detected_language": result.detected_language,
            "translations": {
                "en": result.title_en,
                "zh": result.title_zh,
                "ms": result.title_ms
            },
            "source": link['url'].split('/')[2],
            "content_length": len(result.content),
            "cleaned_content_length": len(result.content_cleaned) if result.content_cleaned else 0
        }
        
        db.save_processed_content(
            link_id=link['id'],
            title=result.title_cleaned,
            content=result.content_cleaned or result.content,
            translated_content=None,  # Stored in metadata
            metadata=metadata
        )
        
        db.update_link_status(link['id'], 'completed')
        
        print(f"✓ Saved to database (link_id: {link['id']})")
        print()
        
        # Verify saved data
        print("=" * 80)
        print("✅ VERIFICATION")
        print("=" * 80)
        
        saved = db.get_processed_content(link['id'])
        if saved:
            print("✓ Data retrieved from database:")
            print(f"  Title: {saved['title'][:60]}...")
            print(f"  Content length: {len(saved['content'])} chars")
            print(f"  Metadata keys: {list(saved['metadata'].keys())}")
            print(f"  Translations: {list(saved['metadata']['translations'].keys())}")
        else:
            print("✗ Failed to retrieve saved data")
        
        print()
        print("=" * 80)
        print("🎉 REAL TEST COMPLETE - SUCCESS!")
        print("=" * 80)
        
    else:
        print("✗ Processing failed - no result returned")
        db.update_link_status(link['id'], 'failed', 'No result returned')
        
except Exception as e:
    print(f"✗ Error during processing: {e}")
    import traceback
    traceback.print_exc()
    db.update_link_status(link['id'], 'failed', str(e))
    sys.exit(1)
