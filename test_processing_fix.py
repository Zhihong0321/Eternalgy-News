"""
Test script to verify processing fixes and reprocess existing links
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from news_search import Database, ProcessorWorker
from ai_processing.processor_with_content import ArticleProcessorWithContent
from ai_processing.processor_adapter import ProcessorAdapter


def main():
    print("=" * 70)
    print("Testing Processing Fixes")
    print("=" * 70)
    print()
    
    db = Database()
    
    # Step 1: Check current state
    print("Step 1: Current Database State")
    print("-" * 70)
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Check processed content
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE title IS NOT NULL AND title != '') as has_title,
                COUNT(*) FILTER (WHERE content IS NOT NULL AND content != '') as has_content,
                COUNT(*) FILTER (WHERE translated_content IS NOT NULL AND translated_content != '') as has_translations,
                COUNT(*) FILTER (WHERE tags IS NOT NULL AND array_length(tags, 1) > 0) as has_tags
            FROM processed_content
        """)
        stats = cursor.fetchone()
        
        print(f"Processed Content Records: {stats[0]}")
        print(f"  With Title: {stats[1]}")
        print(f"  With Content: {stats[2]}")
        print(f"  With Translations: {stats[3]}")
        print(f"  With Tags: {stats[4]}")
        print()
        
        # Check completed links
        cursor.execute("SELECT COUNT(*) FROM news_links WHERE status = 'completed'")
        completed = cursor.fetchone()[0]
        print(f"Completed Links: {completed}")
        
        cursor.close()
    
    print()
    
    # Step 2: Initialize AI Processor
    print("Step 2: Initialize AI Processor")
    print("-" * 70)
    
    try:
        ai_processor = ArticleProcessorWithContent.from_env()
        adapter = ProcessorAdapter(ai_processor)
        print("✓ AI Processor initialized successfully")
        print(f"  API URL: {ai_processor.config.api_url}")
        print(f"  Model: {ai_processor.config.model}")
        print(f"  Content Extraction: {ai_processor.extract_content}")
        print()
    except Exception as e:
        print(f"✗ Failed to initialize AI Processor: {e}")
        print("  Make sure API keys are set in .env file")
        return
    
    # Step 3: Reset and reprocess a few links
    print("Step 3: Reprocess Sample Links")
    print("-" * 70)
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Get first 3 completed links
        cursor.execute("""
            SELECT id, url, title 
            FROM news_links 
            WHERE status = 'completed' 
            ORDER BY id 
            LIMIT 3
        """)
        links = cursor.fetchall()
        
        if not links:
            print("No completed links found to reprocess")
            return
        
        print(f"Found {len(links)} links to reprocess")
        print()
        
        # Reset their status
        link_ids = [link[0] for link in links]
        cursor.execute("""
            UPDATE news_links 
            SET status = 'pending' 
            WHERE id = ANY(%s)
        """, (link_ids,))
        conn.commit()
        
        print(f"✓ Reset {len(link_ids)} links to pending")
        cursor.close()
    
    print()
    
    # Step 4: Process with real AI
    print("Step 4: Processing with AI")
    print("-" * 70)
    
    worker = ProcessorWorker(ai_processor=adapter)
    
    try:
        result = worker.process_specific_links(link_ids)
        
        print(f"Processing Results:")
        print(f"  Total: {result['total']}")
        print(f"  Success: {result['success']}")
        print(f"  Failed: {result['failed']}")
        print()
        
    except Exception as e:
        print(f"✗ Processing error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 5: Verify results
    print("Step 5: Verify Processed Content")
    print("-" * 70)
    
    for link_id in link_ids:
        content = db.get_processed_content(link_id)
        
        if content:
            print(f"\nLink ID: {link_id}")
            print(f"  Title: {content.get('title', 'N/A')[:60]}...")
            print(f"  Content Length: {len(content.get('content', ''))} chars")
            print(f"  Has Translations: {'Yes' if content.get('translated_content') else 'No'}")
            print(f"  Tags: {content.get('tags', [])}")
            print(f"  Country: {content.get('country', 'N/A')}")
            print(f"  News Date: {content.get('news_date', 'N/A')}")
            
            # Show content preview
            if content.get('content'):
                lines = content['content'].split('\n')[:3]
                print(f"  Content Preview:")
                for line in lines:
                    print(f"    {line[:70]}")
            
            # Show translations
            if content.get('translated_content'):
                import json
                try:
                    translations = json.loads(content['translated_content'])
                    print(f"  Translations:")
                    print(f"    EN: {translations.get('en', 'N/A')[:50]}...")
                    print(f"    ZH: {translations.get('zh', 'N/A')[:50]}...")
                    print(f"    MS: {translations.get('ms', 'N/A')[:50]}...")
                except:
                    print(f"  Translations: (parse error)")
        else:
            print(f"\nLink ID: {link_id} - No processed content found")
    
    print()
    
    # Step 6: Test frontend format
    print("Step 6: Test Frontend Format")
    print("-" * 70)
    
    frontend_news = db.get_news_for_frontend(limit=3)
    
    if frontend_news:
        print(f"Retrieved {len(frontend_news)} news items in frontend format")
        print()
        
        for news in frontend_news[:1]:  # Show first one
            print(f"Sample News Item:")
            print(f"  ID: {news['id']}")
            print(f"  URL: {news['url'][:60]}...")
            print(f"  Title: {news['title'][:60]}...")
            print(f"  Title (EN): {news['title_en'][:60]}...")
            print(f"  Title (ZH): {news['title_zh'][:60]}...")
            print(f"  Title (MS): {news['title_ms'][:60]}...")
            print(f"  Content: {news['content'][:100]}...")
            print(f"  Tags: {news['tags']}")
            print(f"  Country: {news['country']}")
            print(f"  Date: {news['news_date']}")
            print(f"  Language: {news['detected_language']}")
    else:
        print("No news items found")
    
    print()
    print("=" * 70)
    print("Test Complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
