"""
Run Malaysia Solar News Task
Complete workflow: Create task → Search → Process → Display results
"""

import sys
sys.path.insert(0, '.')

from news_search import NewsSearchModule, ProcessorWorker, Database
from ai_processing.processor_with_content import ArticleProcessorWithContent
from ai_processing.processor_adapter import ProcessorAdapter


def main():
    print("=" * 80)
    print("RUNNING: malaysia_solar_news")
    print("=" * 80)
    print()
    
    db = Database()
    
    # Step 1: Create/Check Task
    print("Step 1: Create/Check Query Task")
    print("-" * 80)
    
    task_name = "malaysia_solar_news"
    prompt = """
Find latest news articles about solar energy in Malaysia.
Focus on: solar projects, solar installations, renewable energy policies, solar companies.
Return URLs as JSON array with titles.
Example: [{"url": "https://...", "title": "..."}, ...]
Limit to 15 most relevant articles.
"""
    
    task = db.get_query_task(task_name)
    
    if not task:
        print(f"Creating task: {task_name}")
        task_id = db.create_query_task(
            task_name=task_name,
            prompt_template=prompt.strip()
        )
        print(f"✓ Task created (ID: {task_id})")
    else:
        print(f"✓ Task exists: {task_name}")
        print(f"  Total runs: {task['total_runs']}")
        print(f"  Links found: {task['total_links_found']}")
    
    print()
    
    # Step 2: Initialize AI Processor
    print("Step 2: Initialize AI Processor")
    print("-" * 80)
    
    try:
        ai_processor = ArticleProcessorWithContent.from_env()
        adapter = ProcessorAdapter(ai_processor)
        worker = ProcessorWorker(ai_processor=adapter)
        print("✓ AI Processor initialized")
        print(f"  API URL: {ai_processor.config.api_url}")
        print(f"  Model: {ai_processor.config.model}")
        print(f"  Content Extraction: Enabled")
        print(f"  Translation: Enabled (EN/ZH/MS)")
    except Exception as e:
        print(f"⚠ AI Processor initialization failed: {e}")
        print("  Falling back to mock processing")
        worker = ProcessorWorker()
    
    print()
    
    # Step 3: Run Search
    print("Step 3: Run Search Query")
    print("-" * 80)
    print("Searching for Malaysia solar energy news...")
    print()
    
    search = NewsSearchModule(processor_worker=worker)
    
    try:
        result = search.run_task(task_name)
        
        if result['success']:
            print(f"✓ Search completed!")
            print(f"  Total URLs found: {result['total_found']}")
            print(f"  New links: {result['new_links']}")
            print(f"  Duplicates: {result['duplicates']}")
            
            if result['new_links'] > 0:
                print()
                print("New URLs discovered:")
                for i, item in enumerate(result['urls'][:10], 1):
                    print(f"  {i}. [{item['id']}] {item['url'][:65]}...")
                    if item.get('title'):
                        print(f"      {item['title'][:70]}...")
                
                if len(result['urls']) > 10:
                    print(f"  ... and {len(result['urls']) - 10} more")
            
            # Check if auto-processing happened
            if 'processing' in result:
                print()
                print("Auto-Processing Results:")
                print("-" * 80)
                proc = result['processing']
                print(f"  Total processed: {proc['total']}")
                print(f"  Successful: {proc['success']}")
                print(f"  Failed: {proc['failed']}")
                
                if proc.get('by_domain'):
                    print()
                    print("  By Domain:")
                    for domain, stats in proc['by_domain'].items():
                        print(f"    {domain}: {stats['success']}/{stats['total']} success")
        else:
            print(f"✗ Search failed: {result.get('error')}")
            return
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print()
    
    # Step 4: Display Processed Content
    print("Step 4: View Processed Content")
    print("-" * 80)
    
    try:
        news_items = db.get_news_for_frontend(limit=5)
        
        if not news_items:
            print("No processed content available yet.")
            print("Content may still be processing or API authentication failed.")
        else:
            print(f"Retrieved {len(news_items)} processed articles")
            print()
            
            for i, news in enumerate(news_items, 1):
                print("=" * 80)
                print(f"ARTICLE #{i} (ID: {news['id']})")
                print("=" * 80)
                print(f"URL: {news['url']}")
                print()
                
                if news['title']:
                    print(f"Title (Original):")
                    print(f"  {news['title']}")
                    print()
                
                # Show translations
                has_translations = news['title_en'] or news['title_zh'] or news['title_ms']
                if has_translations:
                    print("Translations:")
                    if news['title_en']:
                        print(f"  🇬🇧 EN: {news['title_en']}")
                    if news['title_zh']:
                        print(f"  🇨🇳 ZH: {news['title_zh']}")
                    if news['title_ms']:
                        print(f"  🇲🇾 MS: {news['title_ms']}")
                    print()
                
                # Show content
                if news['content']:
                    print("Content (Bullet Points):")
                    lines = news['content'].split('\n')[:5]
                    for line in lines:
                        if line.strip():
                            print(f"  {line}")
                    if len(news['content'].split('\n')) > 5:
                        print("  ...")
                    print()
                
                # Show metadata
                metadata_items = []
                if news['tags']:
                    metadata_items.append(f"Tags: {', '.join(news['tags'])}")
                if news['country']:
                    metadata_items.append(f"Country: {news['country']}")
                if news['news_date']:
                    metadata_items.append(f"Date: {news['news_date']}")
                if news['detected_language']:
                    metadata_items.append(f"Language: {news['detected_language']}")
                
                if metadata_items:
                    print("Metadata:")
                    for item in metadata_items:
                        print(f"  {item}")
                    print()
    
    except Exception as e:
        print(f"Error viewing content: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # Step 5: Statistics
    print("Step 5: Database Statistics")
    print("-" * 80)
    
    stats = db.get_statistics()
    
    print("Links:")
    print(f"  Total: {stats['links']['total_links']}")
    print(f"  Pending: {stats['links']['pending']}")
    print(f"  Processing: {stats['links']['processing']}")
    print(f"  Completed: {stats['links']['completed']}")
    print(f"  Failed: {stats['links']['failed']}")
    
    if stats['links']['total_links'] > 0:
        success_rate = (stats['links']['completed'] / stats['links']['total_links']) * 100
        print(f"  Success Rate: {success_rate:.1f}%")
    
    print()
    print("Tasks:")
    print(f"  Total: {stats['tasks']['total_tasks']}")
    print(f"  Active: {stats['tasks']['active_tasks']}")
    
    print()
    print("=" * 80)
    print("Task Complete!")
    print("=" * 80)
    print()
    
    if stats['links']['completed'] > 0:
        print("✅ Success! Articles processed and ready for frontend.")
        print()
        print("Next steps:")
        print("  - View all: python verify_database.py")
        print("  - Query in code: db.get_news_for_frontend(limit=20)")
    else:
        print("⚠️  No articles fully processed yet.")
        print()
        print("Possible reasons:")
        print("  - API authentication issue (check .env)")
        print("  - Processing still in progress")
        print("  - URLs blocked by websites (403 errors)")


if __name__ == "__main__":
    main()
