from news_search.database import Database

db = Database()
with db.get_connection() as conn:
    cursor = conn.cursor()
    # Reset links that are completed but have no title in processed_content
    # Actually, we want to reset all links for the 'Malaysia Solar PV' task or just recent ones.
    # Let's reset all 'completed' links from today.
    cursor.execute("""
        UPDATE news_links 
        SET status = 'pending', error_message = NULL
        WHERE status = 'completed' 
        AND discovered_at > CURRENT_DATE - INTERVAL '1 day'
    """)
    print(f"Reset {cursor.rowcount} links to pending.")
