# Quick Fix Guide - Get Your News Working

**TL;DR**: Code is fixed, but data needs reprocessing with valid API key.

---

## 🎯 Your 3 Questions - Quick Answers

### 1. News has title but no content?
**Answer**: Mock processing was used. Content extraction code is now fixed.  
**Action**: Reprocess with real AI (see below)

### 2. Are translations saved in PostgreSQL?
**Answer**: YES, in `translated_content` column as JSON: `{"en":"...", "zh":"...", "ms":"..."}`  
**Action**: Use `db.get_news_for_frontend()` to get parsed translations

### 3. Does DB capture all 3 versions?
**Answer**: YES, all 3 languages in one JSON field  
**Action**: Already working, just need to reprocess data

---

## 🔧 Quick Fix (3 Steps)

### Step 1: Check API Key (30 seconds)

```bash
# Check if API key is set
cat .env | grep AI_API_KEY

# Should show:
# AI_API_KEY=sk-your-key-here
```

If empty or getting 401 errors, update your API key in `.env`

### Step 2: Reprocess Links (2-5 minutes)

```bash
# Reprocess sample links to test
python test_processing_fix.py

# Or reprocess ALL links
python -c "
from news_search import Database, ProcessorWorker
from ai_processing.processor_with_content import ArticleProcessorWithContent
from ai_processing.processor_adapter import ProcessorAdapter

db = Database()
with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute(\"UPDATE news_links SET status = 'pending' WHERE status = 'completed'\")
    conn.commit()
    print(f'Reset {cursor.rowcount} links')

ai_processor = ArticleProcessorWithContent.from_env()
adapter = ProcessorAdapter(ai_processor)
worker = ProcessorWorker(ai_processor=adapter)
result = worker.process_pending_links(limit=100)
print(f'Processed: {result[\"success\"]}/{result[\"total\"]}')
"
```

### Step 3: Verify Results (10 seconds)

```bash
python verify_database.py
```

Should show:
```
Total Records: 15
  With Content: 15 (100%)  ✅
  With Translations: 15 (100%)  ✅
  With Tags: 15 (100%)  ✅
```

---

## 📱 Frontend Integration

### Old Way (Broken)
```python
# DON'T USE THIS
news = db.get_recent_news(limit=20)
# Returns: title, content, translated_content (as JSON string)
# Problem: Need to manually parse JSON
```

### New Way (Fixed)
```python
# USE THIS
from news_search import Database

db = Database()
news = db.get_news_for_frontend(limit=20)

# Returns ready-to-use format:
for item in news:
    print(f"Title (EN): {item['title_en']}")  # Already parsed!
    print(f"Title (ZH): {item['title_zh']}")  # Already parsed!
    print(f"Title (MS): {item['title_ms']}")  # Already parsed!
    print(f"Content: {item['content']}")      # Bullet points
    print(f"Tags: {item['tags']}")            # Array
    print(f"Country: {item['country']}")      # 2-letter code
```

---

## 🐛 Troubleshooting

### Problem: "401 Unauthorized"
**Cause**: Invalid or missing API key  
**Fix**: 
```bash
# Update .env file
AI_API_KEY=your-valid-key-here
```

### Problem: "Empty content after processing"
**Cause**: API authentication failed  
**Fix**: Check API key, then reprocess

### Problem: "403 Forbidden" for some URLs
**Cause**: Website blocks scraping  
**Fix**: Normal behavior, system uses fallback (title only)

### Problem: "No translations"
**Cause**: AI translation API failed  
**Fix**: Check API key and quota

---

## 📊 Check Current Status

```bash
# Quick check
python verify_database.py

# Detailed check
python -c "
from news_search import Database
db = Database()
stats = db.get_statistics()
print(f\"Total links: {stats['links']['total_links']}\")
print(f\"Completed: {stats['links']['completed']}\")
print(f\"Failed: {stats['links']['failed']}\")
"
```

---

## 🎯 What Was Fixed

### Code Changes (Already Done ✅)
1. ✅ `processor_adapter.py` - Proper translation JSON format
2. ✅ `processor_worker.py` - Pass all fields to database
3. ✅ `database.py` - New `get_news_for_frontend()` method

### What You Need to Do
1. ⏳ Verify API key is valid
2. ⏳ Reprocess existing links
3. ⏳ Update frontend to use new method

---

## 📝 Files Created for You

1. **test_processing_fix.py** - Test reprocessing
2. **verify_database.py** - Check database state
3. **PROCESSING_FIXES.md** - Technical details
4. **ISSUE_RESOLUTION_SUMMARY.md** - Complete analysis
5. **FINAL_SUMMARY.md** - Comprehensive summary
6. **QUICK_FIX_GUIDE.md** - This file

---

## 🚀 One-Command Fix

If your API key is valid, run this:

```bash
# Reset and reprocess everything
python test_processing_fix.py && python verify_database.py
```

---

## ✅ Success Criteria

After fixing, you should see:

```
✅ Content: Full article text (1000-3000 chars)
✅ Translations: All 3 languages (EN, ZH, MS)
✅ Tags: ["Solar", "Wind", etc.]
✅ Country: 2-letter code (MY, SG, etc.)
✅ News Date: YYYY-MM-DD format
✅ Frontend: All fields display correctly
```

---

**Need Help?** Check FINAL_SUMMARY.md for complete details.
