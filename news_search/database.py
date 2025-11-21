"""Database models and connection"""
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from contextlib import contextmanager
from datetime import datetime
import hashlib
from typing import Optional, List, Dict
from .config import DB_CONFIG
from .url_normalizer import normalize_url, is_valid_url, extract_domain


class Database:
    def __init__(self):
        self.connection_params = {
            "host": DB_CONFIG["host"],
            "port": DB_CONFIG["port"],
            "database": DB_CONFIG["database"],
            "user": DB_CONFIG["user"],
            "password": DB_CONFIG["password"],
        }

        # Optional SSL mode for managed Postgres (e.g., Railway)
        sslmode = DB_CONFIG.get("sslmode")
        if sslmode:
            self.connection_params["sslmode"] = sslmode
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = psycopg2.connect(**self.connection_params)
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def init_tables(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create news_links table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS news_links (
                    id SERIAL PRIMARY KEY,
                    url TEXT NOT NULL,
                    url_hash VARCHAR(64) UNIQUE NOT NULL,
                    title TEXT,
                    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    source_task VARCHAR(255),
                    status VARCHAR(50) DEFAULT 'pending',
                    error_message TEXT,
                    processed_at TIMESTAMP,
                    last_checked TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_news_links_url_hash ON news_links(url_hash);
                CREATE INDEX IF NOT EXISTS idx_news_links_status ON news_links(status);
                CREATE INDEX IF NOT EXISTS idx_news_links_source_task ON news_links(source_task);
            """)
            
            # Create processed_content table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processed_content (
                    id SERIAL PRIMARY KEY,
                    link_id INTEGER UNIQUE REFERENCES news_links(id) ON DELETE CASCADE,
                    title TEXT,
                    title_en TEXT,
                    title_zh TEXT,
                    title_ms TEXT,
                    content TEXT,
                    translated_content TEXT,
                    tags TEXT[],
                    country VARCHAR(2),
                    news_date DATE,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_processed_content_link_id ON processed_content(link_id);
                CREATE INDEX IF NOT EXISTS idx_processed_content_tags ON processed_content USING GIN(tags);
                CREATE INDEX IF NOT EXISTS idx_processed_content_country ON processed_content(country);
                CREATE INDEX IF NOT EXISTS idx_processed_content_news_date ON processed_content(news_date);
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS blacklisted_sites (
                    id SERIAL PRIMARY KEY,
                    domain VARCHAR(255) UNIQUE NOT NULL,
                    url TEXT NOT NULL,
                    title TEXT,
                    reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_blacklisted_sites_domain ON blacklisted_sites(domain);
            """)
            
            # Create query_tasks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS query_tasks (
                    id SERIAL PRIMARY KEY,
                    task_name VARCHAR(255) UNIQUE NOT NULL,
                    prompt_template TEXT NOT NULL,
                    model VARCHAR(255),
                    is_active BOOLEAN DEFAULT true,
                    schedule VARCHAR(100),
                    last_run TIMESTAMP,
                    total_runs INTEGER DEFAULT 0,
                    total_links_found INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_query_tasks_task_name ON query_tasks(task_name);
                CREATE INDEX IF NOT EXISTS idx_query_tasks_is_active ON query_tasks(is_active);
            """)
            cursor.execute("""
                ALTER TABLE query_tasks
                ADD COLUMN IF NOT EXISTS model VARCHAR(255);
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rewriter_prompts (
                    id SERIAL PRIMARY KEY,
                    prompt TEXT NOT NULL,
                    model VARCHAR(255),
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Store per-run summaries for visibility in the UI
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS query_task_runs (
                    id SERIAL PRIMARY KEY,
                    task_name VARCHAR(255) NOT NULL,
                    summary JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_query_task_runs_task_name ON query_task_runs(task_name);
                CREATE INDEX IF NOT EXISTS idx_query_task_runs_created_at ON query_task_runs(created_at DESC);
            """)
            
            cursor.close()
    
    def insert_news_link(self, url: str, url_hash: str, source_task: str, title: str = None) -> Optional[int]:
        """Insert a news link if it doesn't exist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO news_links (url, url_hash, source_task, title)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (url_hash) DO NOTHING
                    RETURNING id
                """, (url, url_hash, source_task, title))
                
                result = cursor.fetchone()
                cursor.close()
                return result[0] if result else None
            except Exception as e:
                cursor.close()
                raise e

    def url_exists(self, url_hash: str) -> bool:
        """Check if URL already exists"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM news_links WHERE url_hash = %s", (url_hash,))
            exists = cursor.fetchone() is not None
            cursor.close()
            return exists
            
    def update_news_link_title(self, url_hash: str, title: str):
        """Update the title of an existing news link"""
        if not title:
            return
            
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE news_links 
                SET title = %s 
                WHERE url_hash = %s AND (title IS NULL OR title = '')
            """, (title, url_hash))
            cursor.close()

    def get_pending_links(self, limit: int = 100) -> List[Dict]:
        """Get pending news links for processing"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT id, url, source_task, discovered_at, title
                FROM news_links
                WHERE status = 'pending'
                ORDER BY discovered_at DESC
                LIMIT %s
            """, (limit,))
            results = cursor.fetchall()
            cursor.close()
            return [dict(row) for row in results]

    def is_domain_blacklisted(self, domain: str) -> bool:
        """Check if a domain is blacklisted for Jina Reader failures"""
        if not domain:
            return False

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM blacklisted_sites WHERE domain = %s", (domain,))
            exists = cursor.fetchone() is not None
            cursor.close()
            return exists

    def add_blacklisted_site(self, domain: str, url: str, title: str, reason: str):
        """Insert or update a blacklisted domain entry"""
        if not domain:
            domain = url

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO blacklisted_sites (domain, url, title, reason)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (domain) DO UPDATE
                SET url = EXCLUDED.url,
                    title = EXCLUDED.title,
                    reason = EXCLUDED.reason,
                    updated_at = CURRENT_TIMESTAMP
            """, (domain, url, title, reason))
            cursor.close()
    
    def get_links_by_ids(self, link_ids: List[int]) -> List[Dict]:
        """Get links by IDs"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT id, url, source_task, discovered_at, status
                FROM news_links
                WHERE id = ANY(%s)
            """, (link_ids,))
            results = cursor.fetchall()
            cursor.close()
            return [dict(row) for row in results]
    
    def update_link_status(self, link_id: int, status: str, error_message: str = None):
        """Update news link status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if status in ['completed', 'failed']:
                cursor.execute("""
                    UPDATE news_links
                    SET status = %s, 
                        error_message = %s,
                        processed_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (status, error_message, link_id))
            else:
                cursor.execute("""
                    UPDATE news_links
                    SET status = %s,
                        error_message = %s
                    WHERE id = %s
                """, (status, error_message, link_id))
            cursor.close()
    
    def save_processed_content(self, link_id: int, title: str = None, 
                               title_en: str = None, title_zh: str = None, title_ms: str = None,
                               content: str = None, translated_content: str = None,
                               tags: list = None, country: str = None, news_date: str = None,
                               metadata: dict = None):
        """Save processed content for a link"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO processed_content 
                (link_id, title, title_en, title_zh, title_ms, content, translated_content, tags, country, news_date, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (link_id) DO UPDATE
                SET title = EXCLUDED.title,
                    title_en = EXCLUDED.title_en,
                    title_zh = EXCLUDED.title_zh,
                    title_ms = EXCLUDED.title_ms,
                    content = EXCLUDED.content,
                    translated_content = EXCLUDED.translated_content,
                    tags = EXCLUDED.tags,
                    country = EXCLUDED.country,
                    news_date = EXCLUDED.news_date,
                    metadata = EXCLUDED.metadata,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                link_id,
                title,
                title_en,
                title_zh,
                title_ms,
                content,
                translated_content,
                tags,
                country,
                news_date,
                Json(metadata) if metadata else None
            ))
            cursor.close()
    
    def get_processed_content(self, link_id: int) -> Optional[Dict]:
        """Get processed content for a link"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT * FROM processed_content WHERE link_id = %s
            """, (link_id,))
            result = cursor.fetchone()
            cursor.close()
            return dict(result) if result else None
    
    def create_query_task(self, task_name: str, prompt_template: str, schedule: str = None, is_active: bool = True, model: str = None) -> int:
        """Create a new query task"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO query_tasks (task_name, prompt_template, schedule, is_active, model)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (task_name, prompt_template, schedule, is_active, model))
            task_id = cursor.fetchone()[0]
            cursor.close()
            return task_id
    
    def get_query_task(self, task_name: str) -> Optional[Dict]:
        """Get query task by name"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT * FROM query_tasks WHERE task_name = %s
            """, (task_name,))
            result = cursor.fetchone()
            cursor.close()
            return dict(result) if result else None
    
    def get_active_tasks(self) -> List[Dict]:
        """Get all active query tasks"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT * FROM query_tasks WHERE is_active = true
                ORDER BY task_name
            """)
            results = cursor.fetchall()
            cursor.close()
            return [dict(row) for row in results]

    def get_all_tasks(self) -> List[Dict]:
        """List all query tasks with their latest run summary and basic link stats."""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT 
                    qt.*,
                    latest.summary AS latest_run_summary,
                    latest.created_at AS latest_run_at,
                    COALESCE(stats.total_links, 0) AS total_links,
                    COALESCE(stats.completed_links, 0) AS completed_links,
                    COALESCE(stats.pending_links, 0) AS pending_links,
                    COALESCE(stats.failed_links, 0) AS failed_links,
                    COALESCE(stats.blocked_links, 0) AS blocked_links,
                    COALESCE(stats.processed_rows, 0) AS processed_rows
                FROM query_tasks qt
                LEFT JOIN LATERAL (
                    SELECT summary, created_at
                    FROM query_task_runs
                    WHERE task_name = qt.task_name
                    ORDER BY created_at DESC
                    LIMIT 1
                ) AS latest ON TRUE
                LEFT JOIN LATERAL (
                    SELECT
                        COUNT(*) AS total_links,
                        COUNT(*) FILTER (WHERE status = 'completed') AS completed_links,
                        COUNT(*) FILTER (WHERE status = 'pending') AS pending_links,
                        COUNT(*) FILTER (WHERE status = 'failed') AS failed_links,
                        COUNT(*) FILTER (WHERE status = 'blocked') AS blocked_links,
                        (
                            SELECT COUNT(*) FROM processed_content pc
                            JOIN news_links nl2 ON nl2.id = pc.link_id
                            WHERE nl2.source_task = qt.task_name
                        ) AS processed_rows
                    FROM news_links nl
                    WHERE nl.source_task = qt.task_name
                ) AS stats ON TRUE
                ORDER BY qt.task_name
            """)
            results = cursor.fetchall()
            cursor.close()
            return [dict(row) for row in results]

    def update_query_task(self, task_name: str, prompt_template: Optional[str] = None,
                          schedule: Optional[str] = None, is_active: Optional[bool] = None,
                          model: Optional[str] = None) -> bool:
        """Update fields of an existing query task"""
        updates = []
        params = []

        if prompt_template is not None:
            updates.append("prompt_template = %s")
            params.append(prompt_template)
        if schedule is not None:
            updates.append("schedule = %s")
            params.append(schedule)
        if is_active is not None:
            updates.append("is_active = %s")
            params.append(is_active)
        if model is not None:
            updates.append("model = %s")
            params.append(model)

        if not updates:
            return False

        params.append(task_name)
        query = f"""
            UPDATE query_tasks
            SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP
            WHERE task_name = %s
            RETURNING id
        """

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            result = cursor.fetchone()
            cursor.close()
            return result is not None

    def delete_query_task(self, task_name: str) -> bool:
        """Delete a query task by name"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM query_tasks
                WHERE task_name = %s
                RETURNING id
            """, (task_name,))
            result = cursor.fetchone()
            cursor.close()
            return result is not None

    def get_latest_task_run(self) -> Optional[Dict]:
        """Return the most recent query task run timestamp."""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT task_name, last_run
                FROM query_tasks
                WHERE last_run IS NOT NULL
                ORDER BY last_run DESC
                LIMIT 1
            """)
            result = cursor.fetchone()
            cursor.close()
            return dict(result) if result else None
    
    def update_task_run_stats(self, task_name: str, links_found: int):
        """Update task statistics after a run"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE query_tasks
                SET last_run = CURRENT_TIMESTAMP,
                    total_runs = total_runs + 1,
                    total_links_found = total_links_found + %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE task_name = %s
            """, (links_found, task_name))
            cursor.close()

    def record_task_run(self, task_name: str, summary: Dict):
        """Persist a single run summary for later inspection."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO query_task_runs (task_name, summary)
                VALUES (%s, %s)
            """, (task_name, Json(summary)))
            cursor.close()

    def get_recent_task_runs(self, task_name: str, limit: int = 5) -> List[Dict]:
        """Fetch recent run summaries for a given task."""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT summary, created_at
                FROM query_task_runs
                WHERE task_name = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (task_name, limit))
            rows = cursor.fetchall()
            cursor.close()
            return [dict(row) for row in rows]

    def get_recent_processed(self, task_name: str, limit: int = 5) -> List[Dict]:
        """Fetch recent processed items (title/url/status/content) for a task."""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT 
                    nl.id AS link_id,
                    nl.url,
                    nl.status,
                    nl.error_message,
                    nl.processed_at,
                    pc.title,
                    pc.translated_content,
                    pc.content
                FROM news_links nl
                LEFT JOIN processed_content pc ON pc.link_id = nl.id
                WHERE nl.source_task = %s
                ORDER BY nl.processed_at DESC NULLS LAST, nl.discovered_at DESC
                LIMIT %s
            """, (task_name, limit))
            rows = cursor.fetchall()
            cursor.close()
            return [dict(row) for row in rows]

    def get_links_by_status(self, task_name: str, statuses: List[str], limit: int = 50) -> List[Dict]:
        """Fetch links for a task filtered by status."""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT id, url, title, status
                FROM news_links
                WHERE source_task = %s AND status = ANY(%s)
                ORDER BY discovered_at DESC
                LIMIT %s
            """, (task_name, statuses, limit))
            rows = cursor.fetchall()
            cursor.close()
            return [dict(row) for row in rows]

    def get_completed_missing_content(self, task_name: str, limit: int = 50) -> List[Dict]:
        """Find completed links that have no processed_content to allow reprocessing."""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT nl.id, nl.url, nl.title, nl.status
                FROM news_links nl
                LEFT JOIN processed_content pc ON pc.link_id = nl.id
                WHERE nl.source_task = %s
                  AND nl.status = 'completed'
                  AND pc.link_id IS NULL
                ORDER BY nl.processed_at DESC NULLS LAST, nl.discovered_at DESC
                LIMIT %s
            """, (task_name, limit))
            rows = cursor.fetchall()
            cursor.close()
            return [dict(row) for row in rows]

    def get_rewriter_prompt(self) -> Dict:
        """Return the stored rewriter prompt/model or defaults."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT prompt FROM rewriter_prompts
                ORDER BY updated_at DESC
                LIMIT 1
            """)
            row_prompt = cursor.fetchone()
            # model may be NULL; reuse same row if present
            cursor.execute("""
                SELECT model FROM rewriter_prompts
                ORDER BY updated_at DESC
                LIMIT 1
            """)
            row_model = cursor.fetchone()
            cursor.close()
            prompt_val = row_prompt[0] if row_prompt else ""
            model_val = row_model[0] if row_model else None
            return {"prompt": prompt_val, "model": model_val}

    def set_rewriter_prompt(self, prompt: str, model: Optional[str] = None):
        """Save or update the rewriter prompt/model."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO rewriter_prompts (prompt, model)
                VALUES (%s, %s)
            """, (prompt, model))
            cursor.close()

    def get_completed_missing_content(self, task_name: str, limit: int = 50) -> List[Dict]:
        """Find completed links that have no processed_content to allow reprocessing."""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT nl.id, nl.url, nl.title, nl.status
                FROM news_links nl
                LEFT JOIN processed_content pc ON pc.link_id = nl.id
                WHERE nl.source_task = %s
                  AND nl.status = 'completed'
                  AND pc.link_id IS NULL
                ORDER BY nl.processed_at DESC NULLS LAST, nl.discovered_at DESC
                LIMIT %s
            """, (task_name, limit))
            rows = cursor.fetchall()
            cursor.close()
            return [dict(row) for row in rows]
    
    def get_statistics(self) -> Dict:
        """Get overall statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Link statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_links,
                    COUNT(*) FILTER (WHERE status = 'pending') as pending,
                    COUNT(*) FILTER (WHERE status = 'processing') as processing,
                    COUNT(*) FILTER (WHERE status = 'completed') as completed,
                    COUNT(*) FILTER (WHERE status = 'failed') as failed
                FROM news_links
            """)
            link_stats = dict(cursor.fetchone())
            
            # Task statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_tasks,
                    COUNT(*) FILTER (WHERE is_active = true) as active_tasks
                FROM query_tasks
            """)
            task_stats = dict(cursor.fetchone())
            
            cursor.close()
            
            return {
                "links": link_stats,
                "tasks": task_stats
            }

    def get_recent_news(self, limit: int = 20, offset: int = 0, tag: str = None) -> List[Dict]:
        """Get recent processed news with optional tag filtering"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                SELECT 
                    nl.id, nl.url, nl.discovered_at,
                    pc.title, pc.title_en, pc.title_zh, pc.title_ms,
                    pc.content, pc.tags, pc.country, pc.news_date, pc.metadata,
                    pc.translated_content
                FROM news_links nl
                JOIN processed_content pc ON nl.id = pc.link_id
                WHERE nl.status = 'completed'
            """
            
            params = []
            
            if tag:
                query += " AND %s = ANY(pc.tags)"
                params.append(tag)
                
            query += " ORDER BY nl.discovered_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            cursor.execute(query, tuple(params))
            results = cursor.fetchall()
            cursor.close()
            return [dict(row) for row in results]
    
    def get_news_for_frontend(self, limit: int = 20, offset: int = 0, tag: str = None) -> List[Dict]:
        """
        Get news formatted for frontend display with all translations
        
        Returns news with structure:
        {
            "id": 123,
            "url": "https://...",
            "title": "Original title",
            "title_en": "English title",
            "title_zh": "中文标题", 
            "title_ms": "Tajuk Melayu",
            "content": "• Bullet point 1\n• Bullet point 2",
            "tags": ["Solar", "Tech"],
            "country": "MY",
            "news_date": "2025-11-18",
            "detected_language": "en",
            "discovered_at": "2025-11-18T10:30:00"
        }
        """
        import json
        
        news_items = self.get_recent_news(limit=limit, offset=offset, tag=tag)
        
        formatted_news = []
        for item in news_items:
            # Parse translated_content JSON
            translations = {}
            if item.get('translated_content'):
                try:
                    translations = json.loads(item['translated_content'])
                except:
                    translations = {"en": "", "zh": "", "ms": ""}
            
            # Get detected language from metadata
            detected_lang = "unknown"
            if item.get('metadata'):
                detected_lang = item['metadata'].get('detected_language', 'unknown')
            
            title_en_value = item.get('title_en') or translations.get('en', '')
            title_zh_value = item.get('title_zh') or translations.get('zh', '')
            title_ms_value = item.get('title_ms') or translations.get('ms', '')

            metadata = item.get('metadata') or {}
            summary_translations = metadata.get('translated_summary') or {
                "en": translations.get('en', ''),
                "zh": translations.get('zh', ''),
                "ms": translations.get('ms', '')
            }

            formatted_news.append({
                "id": item['id'],
                "url": item['url'],
                "title": item.get('title', ''),
                "title_en": title_en_value,
                "title_zh": title_zh_value,
                "title_ms": title_ms_value,
                "content": item.get('content', ''),
                "tags": item.get('tags', []),
                "country": item.get('country', 'XX'),
                "news_date": str(item['news_date']) if item.get('news_date') else None,
                "detected_language": detected_lang,
                "discovered_at": str(item['discovered_at']) if item.get('discovered_at') else None,
                "summary_translations": summary_translations
            })
        
        return formatted_news


def hash_url(url: str) -> str:
    """Generate SHA256 hash of URL"""
    return hashlib.sha256(url.encode('utf-8')).hexdigest()
