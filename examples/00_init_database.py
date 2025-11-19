"""
Initialize Database Tables

Run this script first to create all necessary database tables.
"""

import sys
sys.path.insert(0, '..')

from news_search import Database


def main():
    print("Initializing Eternalgy-News-AI Database...")
    print("=" * 50)
    
    try:
        db = Database()
        db.init_tables()
        
        print("✓ Database tables created successfully!")
        print()
        print("Tables created:")
        print("  - news_links")
        print("  - processed_content")
        print("  - query_tasks")
        print()
        print("Database is ready to use!")
        
    except Exception as e:
        print(f"✗ Error initializing database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
