"""
Example: Create a Query Task

This script demonstrates how to create a reusable search query task.
"""

import sys
sys.path.insert(0, '..')

from news_search import Database


def main():
    print("Creating Query Task...")
    print("=" * 50)
    
    db = Database()
    
    # Example 1: Technology News
    task_name = "tech_news_daily"
    prompt = """
    Find the latest technology news articles from today.
    Focus on: AI, machine learning, software development, tech companies.
    Return only the URLs as a JSON array.
    Example: ["https://example.com/article1", "https://example.com/article2"]
    """
    
    try:
        task_id = db.create_query_task(
            task_name=task_name,
            prompt_template=prompt.strip(),
            schedule="daily"
        )
        
        print(f"✓ Created task: {task_name}")
        print(f"  Task ID: {task_id}")
        print()
        
        # Verify task was created
        task = db.get_query_task(task_name)
        print("Task details:")
        print(f"  Name: {task['task_name']}")
        print(f"  Active: {task['is_active']}")
        print(f"  Schedule: {task['schedule']}")
        print(f"  Total runs: {task['total_runs']}")
        
    except Exception as e:
        print(f"✗ Error creating task: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
