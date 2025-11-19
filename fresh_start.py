"""
Fresh Start - Run complete workflow with fixed code
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from news_search import NewsSearchModule, ProcessorWorker, Database
from ai_processing.processor_with_content import ArticleProcessorWithContent
from ai_processing.processor_adapter import ProcessorAdapter


def main():
    print("=" * 70)
    print("FRESH START - Complete Workflow with Fixed Code")
    print("=" * 70)
    print()
    
    db = Database()
    
    # Step 1: Initialize database tables
    print("Step 1: Initialize Database Tables")
    print("-" * 70)
    db.init_tables()
    print("✓ Database tables ready")
    print()
    
    # Step 2: Create query task
    print("Step 2: Create Query Task")
    print("-" * 70)
    
    task_name = "malaysia_solar_news"
    prompt = """
Find latest news articles about solar energy in Malaysia.
Focus on: solar projects, solar installations, renewable energy policies.
Return URLs as JSON array with titles.
Example: [{"url": "https://...", "title": "..."}, ...]
Limit to 10 most relevant articles.
"""
    
    try:
        task_id = db.create_query_task(
            task_name=task_name,
            prompt_template=prompt.strip()
        )
        print(f"✓ Created task: {task_name} (ID: {task_id})")
    except Exception as e:
        if "duplicate key" in str(e).lower():
            print(f"✓ Task already exists: {task_name}")
        else:
            print(f"✗ Error creating task: {e}")
            return
    
    print()
    
    # Step 3: Initialize AI Processor
    print("Step 3: Initialize AI Processor")
    print("-" * 70)
    
    try:
        ai_processor = ArticleProcessorWithContent.from_env()
        adapter = ProcessorAdapter(ai_processor)
        worker = ProcessorWorker(ai_processor=adapter)
        print("✓ AI Processor initialized")
        print(f"  API URL: {ai_processor.config.api_url}")
        print(f"  Model: {ai_processor.config.model}")
        print(f"  Content Extraction: {ai_processor.extract_content}")
    except Exception as e:
        print(f"⚠ AI Processor initialization failed: {e}")
        print("  Falling back to mock processing")
        worker = ProcessorWorker()
    
    print()
    
    # Step 4: Run search
    print("Step 4: Run Search Query")
    print("-" * 70)
    
    search = NewsSearchModule(processor_worker=worker)
    
    try:
        result = search.run_task(task_name)
        
        if result['success']:
            print(f"✓ Search completed")
            print(f"  Found: {result['total_found']} URLs")
            print(f"  New: {result['new_links']}")
            print(f"  Duplicates: {result['duplicates']}")
            
            if result['new_links'] > 0:
                print()
                print("New URLs discovered:")
                for item in result['urls'][:5]:
                    print(f"  [{item['id']}] {item['url'][:60]}...")
                    if item.get('title'):
                        print(f"      {item['title'][:60]}...")
            
            # Check if auto-processing happened
            if 'processing' in result:
                print()
                print("Auto-processing results:")
                proc = result['processing']
                print(f"  Total: {proc['total']}")
                print(f"  Success: {proc['success']}")
                print(f"  Failed: {proc['failed']}")
        else:
            print(f"✗ Search failed: {result.get('error')}")
            return
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print()
    
    # Step 5: Show results
    print("Step 5: View Processed Content")
    print("-" * 70)
    
    try:
        news_items = db.get_news_for_frontend(limit=3)
        
        if not news_items:
            print("No processed content yet.")
            print("Content may still be processing...")
        else:
            print(f"Retrieved {len(news_items)} news items")
            print()
            
            for i, news in enumerate(news_items, 1):
                print(f"News #{i} (ID: {news['id']})")
                print(f"  URL: {news['url'][:65]}...")
                print(f"  Title: {news['title'][:60] if news['title'] else '(processing...)'}...")
                
                if news['content']:
                    lines = news['content'].split('\n')[:2]
                    print(f"  Content:")
                    for line in lines:
                        if line.strip():
                            print(f"    {line[:65]}...")
                
                if news['title_en'] or news['title_zh'] or news['title_ms']:
                    print(f"  Translations:")
                    if news['title_en']:
                        print(f"    EN: {news['title_en'][:50]}...")
                    if news['title_zh']:
                        print(f"    ZH: {news['title_zh'][:50]}...")
                    if news['title_ms']:
                        print(f"    MS: {news['title_ms'][:50]}...")
                
                if news['tags']:
                    print(f"  Tags: {news['tags']}")
                if news['country']:
                    print(f"  Country: {news['country']}")
                if news['news_date']:
                    print(f"  Date: {news['news_date']}")
                
                print()
    
    except Exception as e:
        print(f"Error viewing content: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 6: Statistics
    print("Step 6: Database Statistics")
    print("-" * 70)
    
    stats = db.get_statistics()
    
    print("Links:")
    print(f"  Total: {stats['links']['total_links']}")
    print(f"  Pending: {stats['links']['pending']}")
    print(f"  Processing: {stats['links']['processing']}")
    print(f"  Completed: {stats['links']['completed']}")
    print(f"  Failed: {stats['links']['failed']}")
    
    print()
    print("Tasks:")
    print(f"  Total: {stats['tasks']['total_tasks']}")
    print(f"  Active: {stats['tasks']['active_tasks']}")
    
    print()
    print("=" * 70)
    print("Fresh Start Complete!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  - Check results: python verify_database.py")
    print("  - View in frontend: Use db.get_news_for_frontend()")
    print("  - Add more tasks: Create new query tasks")


if __name__ == "__main__":
    main()
