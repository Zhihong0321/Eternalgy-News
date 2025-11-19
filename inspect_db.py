from news_search.database import Database
import json
import psycopg2.extras

db = Database()
with db.get_connection() as conn:
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("""
        SELECT pc.*, nl.url, nl.title as original_title
        FROM processed_content pc
        JOIN news_links nl ON pc.link_id = nl.id
        ORDER BY pc.updated_at DESC
        LIMIT 3
    """)
    results = cursor.fetchall()
    
    for res in results:
        print(f"\nID: {res['id']}")
        print(f"URL: {res['url']}")
        print(f"Original Title: {res['original_title']}")
        print(f"Processed Title: {res['title']}")
        print(f"Content Length: {len(res['content']) if res['content'] else 0}")
        print(f"Content Preview: {res['content'][:100] if res['content'] else 'None'}")
        print(f"Translated Content: {res['translated_content']}")
        print("Metadata Keys:", res['metadata'].keys() if res['metadata'] else 'None')
        if res['metadata'] and 'translations' in res['metadata']:
            print("Translations:", json.dumps(res['metadata']['translations'], indent=2, ensure_ascii=False))
