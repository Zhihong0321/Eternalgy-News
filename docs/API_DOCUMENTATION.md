# NewsNow API Documentation

This document explains how to call the NewsNow API to fetch news feeds from all sources.

## Base URL

```
http://localhost:3000/api  (Development)
https://eternalgy-newsnow-production.up.railway.app/api  (Production)
```

---

## API Endpoints

### 1. Fetch Single Source

**Endpoint**: `GET /api/s`

**Description**: Fetch news from a single source by ID.

**Query Parameters**:
- `id` (required): Source ID (e.g., `pvmagazine`, `thestar`, `cleantechnica`)
- `latest` (optional): Set to `true` to force fetch latest data (bypasses cache)

**Example Requests**:

```bash
# Fetch PV Magazine news (Development)
curl "http://localhost:3000/api/s?id=pvmagazine"

# Fetch PV Magazine news (Production)
curl "https://eternalgy-newsnow-production.up.railway.app/api/s?id=pvmagazine"

# Fetch The Star Online news (Production)
curl "https://eternalgy-newsnow-production.up.railway.app/api/s?id=thestar"

# Force fetch latest (requires authentication)
curl "https://eternalgy-newsnow-production.up.railway.app/api/s?id=cleantechnica&latest=true" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response Format**:

```json
{
  "status": "success",  // or "cache"
  "id": "pvmagazine",
  "updatedTime": 1705567890000,
  "items": [
    {
      "id": "https://www.pv-magazine.com/article-123",
      "title": "Solar panel efficiency reaches new record",
      "url": "https://www.pv-magazine.com/article-123",
      "pubDate": 1705567800000,
      "extra": {
        "date": 1705567800000,
        "hover": "Additional info on hover"
      }
    }
    // ... up to 30 items
  ]
}
```

---

### 2. Fetch Multiple Sources (Batch)

**Endpoint**: `POST /api/s/entire`

**Description**: Fetch news from multiple sources in a single request. This is the most efficient way to get all your sources.

**Request Body**:

```json
{
  "sources": ["pvmagazine", "thestar", "cleantechnica", "malaysiakini"]
}
```

**Example Request**:

```bash
# Development
curl -X POST "http://localhost:3000/api/s/entire" \
  -H "Content-Type: application/json" \
  -d '{
    "sources": ["pvmagazine", "thestar", "cleantechnica", "malaysiakini"]
  }'

# Production
curl -X POST "https://eternalgy-newsnow-production.up.railway.app/api/s/entire" \
  -H "Content-Type: application/json" \
  -d '{
    "sources": ["pvmagazine", "thestar", "cleantechnica", "malaysiakini"]
  }'
```

**Response Format**:

```json
[
  {
    "status": "cache",
    "id": "pvmagazine",
    "updatedTime": 1705567890000,
    "items": [
      {
        "id": "https://www.pv-magazine.com/article-123",
        "title": "Solar panel efficiency reaches new record",
        "url": "https://www.pv-magazine.com/article-123",
        "pubDate": 1705567800000
      }
      // ... more items
    ]
  },
  {
    "status": "cache",
    "id": "thestar",
    "updatedTime": 1705567890000,
    "items": [
      // ... items
    ]
  }
  // ... more sources
]
```

---

## Available Source IDs

### Renewable Energy Sources (18)

```javascript
const renewableSources = [
  "pvmagazine",
  "solarpowerworld",
  "cleantechnica",
  "renewableenergyworld",
  "rechargenews",
  "utilitydive",
  "renewablesnow",
  "canarymedia",
  "solarindustrymag",
  "irena",
  "eia",
  "energystoragenews",
  "pvtech",
  "renewableenergyindustry",
  "solarbuildermag",
  "europeanenergyinnovation",
  "solarquarter",
  "renewableenergyfocus"
]
```

### Malaysian News Sources (8)

```javascript
const malaysiaSources = [
  "thestar",
  "malaysiakini",
  "freemalaysiatoday",
  "malaymail",
  "nst",
  "astroawani",
  "theedgemarkets",
  "bernama"
]
```

### All 26 New Sources

```javascript
const allNewSources = [
  ...renewableSources,
  ...malaysiaSources
]
```

---

## Fetching All 26 Sources at Once

**JavaScript/TypeScript Example**:

```typescript
async function fetchAllNewsSources() {
  const allSources = [
    // Renewable Energy
    "pvmagazine", "solarpowerworld", "cleantechnica", 
    "renewableenergyworld", "rechargenews", "utilitydive",
    "renewablesnow", "canarymedia", "solarindustrymag",
    "irena", "eia", "energystoragenews", "pvtech",
    "renewableenergyindustry", "solarbuildermag",
    "europeanenergyinnovation", "solarquarter", "renewableenergyfocus",
    
    // Malaysian News
    "thestar", "malaysiakini", "freemalaysiatoday",
    "malaymail", "nst", "astroawani", "theedgemarkets", "bernama"
  ]

  const response = await fetch('https://eternalgy-newsnow-production.up.railway.app/api/s/entire', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ sources: allSources })
  })

  const data = await response.json()
  return data
}

// Usage
fetchAllNewsSources().then(sources => {
  sources.forEach(source => {
    console.log(`${source.id}: ${source.items.length} articles`)
  })
})
```

**Python Example**:

```python
import requests
import json

def fetch_all_news_sources():
    all_sources = [
        # Renewable Energy
        "pvmagazine", "solarpowerworld", "cleantechnica",
        "renewableenergyworld", "rechargenews", "utilitydive",
        "renewablesnow", "canarymedia", "solarindustrymag",
        "irena", "eia", "energystoragenews", "pvtech",
        "renewableenergyindustry", "solarbuildermag",
        "europeanenergyinnovation", "solarquarter", "renewableenergyfocus",
        
        # Malaysian News
        "thestar", "malaysiakini", "freemalaysiatoday",
        "malaymail", "nst", "astroawani", "theedgemarkets", "bernama"
    ]
    
    response = requests.post(
        'https://eternalgy-newsnow-production.up.railway.app/api/s/entire',
        headers={'Content-Type': 'application/json'},
        json={'sources': all_sources}
    )
    
    return response.json()

# Usage
sources = fetch_all_news_sources()
for source in sources:
    print(f"{source['id']}: {len(source['items'])} articles")
```

**cURL Example**:

```bash
curl -X POST "https://eternalgy-newsnow-production.up.railway.app/api/s/entire" \
  -H "Content-Type: application/json" \
  -d '{
    "sources": [
      "pvmagazine", "solarpowerworld", "cleantechnica",
      "renewableenergyworld", "rechargenews", "utilitydive",
      "renewablesnow", "canarymedia", "solarindustrymag",
      "irena", "eia", "energystoragenews", "pvtech",
      "renewableenergyindustry", "solarbuildermag",
      "europeanenergyinnovation", "solarquarter", "renewableenergyfocus",
      "thestar", "malaysiakini", "freemalaysiatoday",
      "malaymail", "nst", "astroawani", "theedgemarkets", "bernama"
    ]
  }'
```

---

## Caching Behavior

### Cache Strategy

The API implements intelligent caching:

1. **Interval-based Cache**: Each source has an update interval (30-60 minutes)
   - If data was fetched within the interval, cached data is returned
   - Status will be `"success"` if data is fresh

2. **TTL Cache**: Time-To-Live cache (default configuration)
   - Even if content updates, cache is used within TTL
   - Status will be `"cache"` when serving cached data

3. **Force Latest**: Use `?latest=true` parameter
   - Bypasses cache and fetches fresh data
   - Requires authentication (JWT token)

### Cache Response Status

- `"success"`: Fresh data just fetched
- `"cache"`: Serving cached data (still valid)

---

## Response Fields

### SourceResponse Object

```typescript
{
  status: "success" | "cache",
  id: string,              // Source ID
  updatedTime: number,     // Unix timestamp (milliseconds)
  items: NewsItem[]        // Array of news items (max 30)
}
```

### NewsItem Object

```typescript
{
  id: string | number,     // Unique identifier (usually URL)
  title: string,           // Article title
  url: string,             // Article URL
  mobileUrl?: string,      // Mobile-optimized URL (optional)
  pubDate?: number,        // Publication date (Unix timestamp)
  extra?: {
    hover?: string,        // Tooltip text
    date?: number,         // Alternative date field
    info?: string,         // Additional info
    diff?: number,         // Ranking change (for "hottest" type)
    icon?: string | {      // Icon URL or object
      url: string,
      scale: number
    }
  }
}
```

---

## Rate Limiting & Best Practices

### Recommendations

1. **Use Batch Endpoint**: Always prefer `/api/s/entire` over multiple `/api/s` calls
   - More efficient
   - Reduces server load
   - Faster response time

2. **Respect Cache Intervals**: 
   - Don't poll more frequently than every 30 minutes
   - The sources themselves update at these intervals

3. **Handle Errors Gracefully**:
   ```javascript
   try {
     const data = await fetchAllNewsSources()
   } catch (error) {
     console.error('Failed to fetch news:', error)
     // Use cached data or retry with exponential backoff
   }
   ```

4. **Store Locally**: Cache responses on your end to reduce API calls

---

## Authentication (Optional)

For `?latest=true` requests, include JWT token:

```bash
# Development
curl "http://localhost:3000/api/s?id=pvmagazine&latest=true" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Production
curl "https://eternalgy-newsnow-production.up.railway.app/api/s?id=pvmagazine&latest=true" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

JWT tokens are obtained through the login flow (see `/api/login` endpoint).

---

## Error Handling

### Error Response Format

```json
{
  "statusCode": 500,
  "message": "Invalid source id"
}
```

### Common Errors

- `400`: Invalid source ID
- `401`: Unauthorized (for `?latest=true` without valid JWT)
- `500`: Internal server error (RSS feed unavailable, parsing error, etc.)

---

## Complete Integration Example

```typescript
// Complete example with error handling and caching
class NewsNowClient {
  private baseUrl: string
  private cache: Map<string, any> = new Map()
  private cacheTimeout = 30 * 60 * 1000 // 30 minutes

  constructor(baseUrl: string = 'https://eternalgy-newsnow-production.up.railway.app/api') {
    this.baseUrl = baseUrl
  }

  async fetchSources(sourceIds: string[]) {
    const cacheKey = sourceIds.sort().join(',')
    const cached = this.cache.get(cacheKey)
    
    if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
      console.log('Returning cached data')
      return cached.data
    }

    try {
      const response = await fetch(`${this.baseUrl}/s/entire`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sources: sourceIds })
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()
      
      this.cache.set(cacheKey, {
        data,
        timestamp: Date.now()
      })

      return data
    } catch (error) {
      console.error('Failed to fetch sources:', error)
      
      // Return cached data if available, even if expired
      if (cached) {
        console.log('Returning stale cached data due to error')
        return cached.data
      }
      
      throw error
    }
  }

  async fetchAllNewSources() {
    const allSources = [
      "pvmagazine", "solarpowerworld", "cleantechnica",
      "renewableenergyworld", "rechargenews", "utilitydive",
      "renewablesnow", "canarymedia", "solarindustrymag",
      "irena", "eia", "energystoragenews", "pvtech",
      "renewableenergyindustry", "solarbuildermag",
      "europeanenergyinnovation", "solarquarter", "renewableenergyfocus",
      "thestar", "malaysiakini", "freemalaysiatoday",
      "malaymail", "nst", "astroawani", "theedgemarkets", "bernama"
    ]
    
    return this.fetchSources(allSources)
  }
}

// Usage
const client = new NewsNowClient()

// Fetch all 26 sources
const allNews = await client.fetchAllNewSources()
console.log(`Fetched ${allNews.length} sources`)

// Fetch specific sources
const renewableNews = await client.fetchSources([
  "pvmagazine", "cleantechnica", "renewableenergyworld"
])
```

---

## Summary

**Yes, you can get all 26 sources in a single API call!**

Use the `/api/s/entire` POST endpoint with all source IDs in the request body. This will return an array of all sources with their latest news items (up to 30 per source).

The API handles caching automatically, so you'll get fast responses while still receiving fresh data when available.
