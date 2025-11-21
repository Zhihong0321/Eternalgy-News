"""
Example: Process News Links

This script demonstrates how to process discovered news links:
1. Fetch Markdown via the Jina Reader API
2. Clean and summarize (point form)
3. Translate to 3 languages
4. Store in database
"""

import sys
sys.path.insert(0, '..')

from news_search import ProcessorWorker, Database


def main():
    print("Processing News Links...")
    print("=" * 50)
    
    # Initialize
    processor = ProcessorWorker()
    db = Database()
    
    # Get pending links
    pending = db.get_pending_links(limit=5)
    
    if not pending:
        print("No pending links to process.")
        print("Run 02_run_search.py first to discover news URLs.")
        return
    
    print(f"Found {len(pending)} pending links")
    print()
    
    # Process links
    try:
        result = processor.process_pending_links(limit=5)
        
        print("Processing Results:")
        print(f"  Total processed: {result['total_processed']}")
        print(f"  Successful: {result['successful']}")
        print(f"  Failed: {result['failed']}")
        print()
        
        if result['successful'] > 0:
            print("Successfully processed articles:")
            for item in result['results'][:3]:  # Show first 3
                if item['status'] == 'completed':
                    print(f"\n  Link ID: {item['link_id']}")
                    print(f"  URL: {item['url'][:60]}...")
                    
                    # Get processed content
                    content = db.get_processed_content(item['link_id'])
                    if content:
                        print(f"  Title (EN): {content.get('title', 'N/A')[:60]}...")
                        print(f"  Content length: {len(content.get('content', ''))} chars")
        
        if result['failed'] > 0:
            print("\nFailed articles:")
            for item in result['results']:
                if item['status'] == 'failed':
                    print(f"  [{item['link_id']}] {item.get('error', 'Unknown error')}")
                    
    except Exception as e:
        print(f"✗ Error processing links: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
