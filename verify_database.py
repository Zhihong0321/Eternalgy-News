"""
Quick script to verify database content and translations
"""

import sys
import json
sys.path.insert(0, '.')

from news_search import Database


def main():
    print("=" * 80)
    print("DATABASE VERIFICATION - Content & Translations")
    print("=" * 80)
    print()
    
    db = Database()
    
    # Check overall stats
    print("1. OVERALL STATISTICS")
    print("-" * 80)
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE title IS NOT NULL AND title != '') as has_title,
                COUNT(*) FILTER (WHERE content IS NOT NULL AND content != '') as has_content,
                COUNT(*) FILTER (WHERE translated_content IS NOT NULL AND translated_content != '') as has_translations,
                COUNT(*) FILTER (WHERE tags IS NOT NULL AND array_length(tags, 1) > 0) as has_tags,
                COUNT(*) FILTER (WHERE country IS NOT NULL AND country != '') as has_country
            FROM processed_content
        """)
        
        stats = cursor.fetchone()
        total, has_title, has_content, has_trans, has_tags, has_country = stats
        
        print(f"Total Records: {total}")
        print(f"  With Title: {has_title} ({has_title/total*100 if total > 0 else 0:.1f}%)")
        print(f"  With Content: {has_content} ({has_content/total*100 if total > 0 else 0:.1f}%)")
        print(f"  With Translations: {has_trans} ({has_trans/total*100 if total > 0 else 0:.1f}%)")
        print(f"  With Tags: {has_tags} ({has_tags/total*100 if total > 0 else 0:.1f}%)")
        print(f"  With Country: {has_country} ({has_country/total*100 if total > 0 else 0:.1f}%)")
        
        cursor.close()
    
    print()
    
    # Show sample records
    print("2. SAMPLE RECORDS (with content)")
    print("-" * 80)
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                pc.id,
                nl.url,
                pc.title,
                LENGTH(pc.content) as content_length,
                pc.translated_content,
                pc.tags,
                pc.country,
                pc.news_date
            FROM processed_content pc
            JOIN news_links nl ON pc.link_id = nl.id
            WHERE pc.content IS NOT NULL AND pc.content != ''
            ORDER BY pc.id DESC
            LIMIT 3
        """)
        
        records = cursor.fetchall()
        
        if not records:
            print("No records with content found.")
        else:
            for i, record in enumerate(records, 1):
                rec_id, url, title, content_len, trans_json, tags, country, news_date = record
                
                print(f"\nRecord #{i} (ID: {rec_id})")
                print(f"  URL: {url[:70]}...")
                print(f"  Title: {title[:70] if title else '(empty)'}...")
                print(f"  Content Length: {content_len} characters")
                
                # Parse translations
                if trans_json:
                    try:
                        translations = json.loads(trans_json)
                        print(f"  Translations:")
                        print(f"    EN: {translations.get('en', '(empty)')[:60]}...")
                        print(f"    ZH: {translations.get('zh', '(empty)')[:60]}...")
                        print(f"    MS: {translations.get('ms', '(empty)')[:60]}...")
                    except:
                        print(f"  Translations: (parse error)")
                else:
                    print(f"  Translations: (none)")
                
                print(f"  Tags: {tags if tags else '(none)'}")
                print(f"  Country: {country if country else '(none)'}")
                print(f"  Date: {news_date if news_date else '(none)'}")
        
        cursor.close()
    
    print()
    
    # Test frontend format
    print("3. FRONTEND FORMAT TEST")
    print("-" * 80)
    
    try:
        news_items = db.get_news_for_frontend(limit=2)
        
        if not news_items:
            print("No news items available.")
        else:
            for i, news in enumerate(news_items, 1):
                print(f"\nNews Item #{i}")
                print(f"  ID: {news['id']}")
                print(f"  URL: {news['url'][:70]}...")
                print(f"  Title: {news['title'][:60] if news['title'] else '(empty)'}...")
                print(f"  Title (EN): {news['title_en'][:60] if news['title_en'] else '(empty)'}...")
                print(f"  Title (ZH): {news['title_zh'][:60] if news['title_zh'] else '(empty)'}...")
                print(f"  Title (MS): {news['title_ms'][:60] if news['title_ms'] else '(empty)'}...")
                print(f"  Content: {news['content'][:100] if news['content'] else '(empty)'}...")
                print(f"  Tags: {news['tags']}")
                print(f"  Country: {news['country']}")
                print(f"  Date: {news['news_date']}")
                print(f"  Language: {news['detected_language']}")
    except Exception as e:
        print(f"Error testing frontend format: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # Check for issues
    print("4. ISSUE DETECTION")
    print("-" * 80)
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Empty content
        cursor.execute("""
            SELECT COUNT(*) 
            FROM processed_content 
            WHERE content IS NULL OR content = ''
        """)
        empty_content = cursor.fetchone()[0]
        
        # Empty translations
        cursor.execute("""
            SELECT COUNT(*) 
            FROM processed_content 
            WHERE translated_content IS NULL OR translated_content = ''
        """)
        empty_trans = cursor.fetchone()[0]
        
        # Missing tags
        cursor.execute("""
            SELECT COUNT(*) 
            FROM processed_content 
            WHERE tags IS NULL OR array_length(tags, 1) IS NULL
        """)
        missing_tags = cursor.fetchone()[0]
        
        cursor.close()
        
        issues = []
        if empty_content > 0:
            issues.append(f"⚠️  {empty_content} records with empty content")
        if empty_trans > 0:
            issues.append(f"⚠️  {empty_trans} records with empty translations")
        if missing_tags > 0:
            issues.append(f"⚠️  {missing_tags} records with missing tags")
        
        if issues:
            print("Issues found:")
            for issue in issues:
                print(f"  {issue}")
            print()
            print("💡 Recommendation: Reprocess these links with real AI processing")
            print("   Run: python test_processing_fix.py")
        else:
            print("✅ No issues found! All records have content and translations.")
    
    print()
    print("=" * 80)
    print("Verification Complete")
    print("=" * 80)


if __name__ == "__main__":
    main()
