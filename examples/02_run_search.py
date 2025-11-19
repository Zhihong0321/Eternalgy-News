"""
Example: Run Search Query

This script demonstrates how to run a search query and discover news URLs.
"""

import sys
sys.path.insert(0, '..')

from news_search import NewsSearchModule


def main():
    print("Running Search Query...")
    print("=" * 50)
    
    # Initialize search module
    search = NewsSearchModule()
    
    # Option 1: Run existing task
    task_name = "tech_news_daily"
    
    try:
        print(f"Running task: {task_name}")
        result = search.run_task(task_name)
        
        if result['success']:
            print(f"✓ Search completed!")
            print()
            print("Results:")
            print(f"  Total URLs found: {result['total_found']}")
            print(f"  New links: {result['new_links']}")
            print(f"  Duplicates: {result['duplicates']}")
            print(f"  Invalid: {result['invalid']}")
            print()
            
            if result['new_links'] > 0:
                print("New URLs:")
                for item in result['urls'][:5]:  # Show first 5
                    print(f"  [{item['id']}] {item['url']}")
                
                if len(result['urls']) > 5:
                    print(f"  ... and {len(result['urls']) - 5} more")
        else:
            print(f"✗ Search failed: {result.get('error')}")
            
    except Exception as e:
        print(f"✗ Error running search: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
