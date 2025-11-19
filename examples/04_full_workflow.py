"""
Example: Full Workflow

This script demonstrates the complete workflow:
1. Create query task (if not exists)
2. Run search to discover URLs
3. Process discovered links
4. Display results
"""

import sys
import os
# Add parent directory to path (Eternalgy-News-AI root)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from news_search import NewsSearchModule, ProcessorWorker, Database
from ai_processing.processor_with_content import ArticleProcessorWithContent
from ai_processing.processor_adapter import ProcessorAdapter


def main():
    print("=" * 60)
    print("Eternalgy-News-AI - Full Workflow Demo")
    print("=" * 60)
    print()
    
    db = Database()
    
    # Reset status for testing (force reprocessing)
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE news_links SET status = 'pending' WHERE status = 'completed'")
        conn.commit()
        if cursor.rowcount > 0:
            print(f"✓ Reset {cursor.rowcount} links to pending for reprocessing")
    
    # Initialize AI Processor
    try:
        ai_processor = ArticleProcessorWithContent.from_env()
        adapter = ProcessorAdapter(ai_processor)
        worker = ProcessorWorker(ai_processor=adapter)
        print("✓ AI Processor initialized")
    except Exception as e:
        print(f"⚠ AI Processor initialization failed: {e}")
        print("  Falling back to mock processing")
        worker = ProcessorWorker()

    search = NewsSearchModule(processor_worker=worker)
    
    # Step 1: Ensure task exists
    print("Step 1: Check/Create Query Task")
    print("-" * 60)
    
    task_name = "tech_news_demo"
    task = db.get_query_task(task_name)
    
    if not task:
        print(f"Creating new task: {task_name}")
        prompt = """
        Find latest technology and AI news articles.
        Return URLs as JSON array: ["url1", "url2", ...]
        """
        db.create_query_task(task_name, prompt.strip())
        print("✓ Task created")
    else:
        print(f"✓ Task exists: {task_name}")
    
    print()
    
    # Step 2: Run search
    print("Step 2: Run Search Query")
    print("-" * 60)
    
    try:
        result = search.run_task(task_name)
        
        if result['success']:
            print(f"✓ Search completed")
            print(f"  Found: {result['total_found']} URLs")
            print(f"  New: {result['new_links']}")
            print(f"  Duplicates: {result['duplicates']}")
            
            # Check if auto-processing happened
            if 'processing' in result:
                print()
                print("Auto-processing results:")
                proc = result['processing']
                print(f"  Processed: {proc['total']}")
                print(f"  Successful: {proc['success']}")
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
    
    # Step 2.5: Process pending links (in case auto-processing didn't run)
    print("Step 2.5: Process Pending Links")
    print("-" * 60)
    if hasattr(search, 'processor_worker') and search.processor_worker:
        print("Checking for pending links...")
        proc_stats = search.processor_worker.process_pending_links(limit=10)
        print(f"Processed: {proc_stats.get('total', 0)}")
        print(f"Successful: {proc_stats.get('success', 0)}")
        print(f"Failed: {proc_stats.get('failed', 0)}")
    
    print()
    
    # Step 3: Display statistics
    print("Step 3: Database Statistics")
    print("-" * 60)
    
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
    
    # Step 4: Show sample processed content
    print("Step 4: Sample Processed Content")
    print("-" * 60)
    
    # Get a completed link
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT nl.id, nl.url, pc.title, pc.content, pc.metadata
            FROM news_links nl
            JOIN processed_content pc ON nl.id = pc.link_id
            WHERE nl.status = 'completed'
            ORDER BY nl.processed_at DESC
            LIMIT 1
        """)
        row = cursor.fetchone()
        cursor.close()
        
        if row:
            link_id, url, title, content, metadata = row
            print(f"Link ID: {link_id}")
            print(f"URL: {url[:70]}...")
            print(f"Title: {title[:70]}...")
            print(f"Content preview:")
            print(f"  {content[:200]}...")
            
            if metadata:
                import json
                meta = json.loads(metadata) if isinstance(metadata, str) else metadata
                print(f"Metadata:")
                print(f"  Language: {meta.get('detected_language', 'N/A')}")
                print(f"  Translations: {', '.join(meta.get('translations', {}).keys())}")
        else:
            print("No processed content yet.")
            print("Run this script again after processing completes.")
    
    print()
    print("=" * 60)
    print("Workflow Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
