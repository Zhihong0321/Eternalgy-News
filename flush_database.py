"""
Flush database - Clean start
Deletes all data from all tables
"""

import sys
sys.path.insert(0, '.')

from news_search import Database


def main():
    print("=" * 70)
    print("DATABASE FLUSH - Clean Start")
    print("=" * 70)
    print()
    
    db = Database()
    
    # Show current state
    print("Current Database State:")
    print("-" * 70)
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM news_links")
        links_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM processed_content")
        content_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM query_tasks")
        tasks_count = cursor.fetchone()[0]
        
        print(f"  news_links: {links_count} records")
        print(f"  processed_content: {content_count} records")
        print(f"  query_tasks: {tasks_count} records")
        
        cursor.close()
    
    print()
    
    # Confirm
    response = input("⚠️  Delete ALL data? This cannot be undone! (yes/no): ")
    
    if response.lower() != 'yes':
        print("Cancelled. No data deleted.")
        return
    
    print()
    print("Flushing database...")
    print("-" * 70)
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Delete in correct order (respecting foreign keys)
        print("  Deleting processed_content...")
        cursor.execute("DELETE FROM processed_content")
        deleted_content = cursor.rowcount
        
        print("  Deleting news_links...")
        cursor.execute("DELETE FROM news_links")
        deleted_links = cursor.rowcount
        
        print("  Deleting query_tasks...")
        cursor.execute("DELETE FROM query_tasks")
        deleted_tasks = cursor.rowcount
        
        # Reset sequences
        print("  Resetting ID sequences...")
        cursor.execute("ALTER SEQUENCE news_links_id_seq RESTART WITH 1")
        cursor.execute("ALTER SEQUENCE processed_content_id_seq RESTART WITH 1")
        cursor.execute("ALTER SEQUENCE query_tasks_id_seq RESTART WITH 1")
        
        conn.commit()
        cursor.close()
    
    print()
    print("✓ Database flushed successfully!")
    print()
    print(f"  Deleted {deleted_links} news_links")
    print(f"  Deleted {deleted_content} processed_content")
    print(f"  Deleted {deleted_tasks} query_tasks")
    print(f"  Reset all ID sequences")
    
    print()
    
    # Verify
    print("Verification:")
    print("-" * 70)
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM news_links")
        links_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM processed_content")
        content_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM query_tasks")
        tasks_count = cursor.fetchone()[0]
        
        print(f"  news_links: {links_count} records ✓")
        print(f"  processed_content: {content_count} records ✓")
        print(f"  query_tasks: {tasks_count} records ✓")
        
        cursor.close()
    
    print()
    print("=" * 70)
    print("Database is now clean and ready for fresh data!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  1. Run: python examples/04_full_workflow.py")
    print("  2. Or create your own query task and run search")


if __name__ == "__main__":
    main()
