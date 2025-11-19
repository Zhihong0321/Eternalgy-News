# Frontend Integration

This folder is reserved for frontend UI integration.

## Status

🚧 **Coming Soon** - Waiting for frontend template

## Integration Plan

Once frontend template is provided:

### 1. Backend API

Create REST API endpoints:

```python
# api/routes.py

@app.get("/api/news")
def get_news(
    language: str = "en",
    limit: int = 20,
    offset: int = 0
):
    """Get processed news articles"""
    db = Database()
    # Query processed_content table
    # Return JSON array

@app.get("/api/news/{id}")
def get_news_detail(id: int):
    """Get single news article"""
    # Return full article with all translations

@app.get("/api/stats")
def get_stats():
    """Get system statistics"""
    # Return processing stats
```

### 2. Data Format

Frontend will receive:

```json
{
  "id": 123,
  "url": "https://example.com/article",
  "title": "Original title",
  "title_en": "English title",
  "title_zh": "中文标题",
  "title_ms": "Tajuk Melayu",
  "content": "• Point 1\n• Point 2\n• Point 3",
  "detected_language": "en",
  "source": "example.com",
  "processed_at": "2025-11-18T10:30:00",
  "metadata": {
    "word_count": 500,
    "translations": ["en", "zh", "ms"]
  }
}
```

### 3. Features to Implement

- [ ] News list view (with pagination)
- [ ] Language filter (EN/ZH/MS)
- [ ] Search functionality
- [ ] Article detail view
- [ ] Source filter
- [ ] Date range filter
- [ ] Responsive design (mobile/desktop)

### 4. Technology Stack

To be determined based on provided template:
- React / Vue / Angular / Next.js?
- Tailwind / Bootstrap / Material UI?
- State management?

## Current Backend Status

✅ **Ready for Integration**:
- PostgreSQL database with structured data
- All articles cleaned and translated
- Point-form summaries generated
- Multi-language support (EN, ZH, MS)
- Metadata available

## Next Steps

1. Receive frontend template
2. Create REST API layer
3. Wire backend data to frontend
4. Test integration
5. Deploy

---

**Contact**: Waiting for frontend template delivery
