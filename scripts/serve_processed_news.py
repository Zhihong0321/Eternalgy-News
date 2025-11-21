import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from html import escape
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import urlparse
import json

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from news_search import Database
from ai_processing.services.formatting import strip_bbcode

PORT = 8080


def fetch_processed_entries(limit: int = 20):
    db = Database()
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT n.id, n.url, n.processed_at, p.title, p.content, p.translated_content, p.metadata
            FROM news_links n
            JOIN processed_content p ON p.link_id = n.id
            ORDER BY n.processed_at DESC NULLS LAST
            LIMIT %s
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        cursor.close()
    return rows


def parse_translations(raw: Optional[str], metadata: Optional[Dict]) -> Dict[str, str]:
    if not raw:
        return metadata.get("translations", {}) if metadata else {}

    try:
        decoded = json.loads(raw)
        if isinstance(decoded, dict):
            return decoded
    except json.JSONDecodeError:
        pass
    return {"en": raw}


def format_translated_text(text: Optional[str]) -> str:
    if not text:
        return "<p><em>(empty)</em></p>"
    cleaned = strip_bbcode(text)
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    html_parts = []
    in_list = False

    for line in lines:
        if line.startswith(("-", "*")):
            if not in_list:
                html_parts.append("<ul>")
                in_list = True
            html_parts.append(f"<li>{escape(line.lstrip('-* ').strip())}</li>")
            continue

        if in_list:
            html_parts.append("</ul>")
            in_list = False

        html_parts.append(f"<p>{escape(line)}</p>")

        if in_list:
            html_parts.append("</ul>")

    return "".join(html_parts) or "<p><em>(empty)</em></p>"


class ProcessedNewsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urlparse(self.path)
        if url.path not in ["/", "/index.html"]:
            self.send_error(404)
            return

        rows = fetch_processed_entries()
        html_body = self.build_html(rows)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(html_body.encode("utf-8"))))
        self.end_headers()
        self.wfile.write(html_body.encode("utf-8"))

    @staticmethod
    def build_html(rows):
        parts = [
            "<!doctype html>",
            "<html><head><meta charset='utf-8'><title>Processed News</title>",
            "<style>",
            "body{font-family:Segoe UI,Arial,sans-serif;margin:0;padding:1rem;background:#111;color:#eef;}",
            "article{border:1px solid #444;border-radius:8px;padding:1rem;margin-bottom:1rem;background:#1b1b1b;}",
            "h1{color:#f7c948;margin-top:0;}",
            "h2 a{color:#5ed9ff;}",
            ".summary{margin:0.5rem 0;padding:0.5rem;border-radius:6px;background:#0f0f0f;}",
            ".translations{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:0.75rem;margin-top:1rem;}",
            ".translations h4{margin-bottom:0.25rem;color:#82cfff;}",
            "ul{margin:0 1rem 0.75rem 1rem;padding-left:1rem;}",
            "p{margin:0 0 0.4rem 0;}",
            "details{margin-top:0.5rem;}",
            "</style></head><body>",
            "<h1>Processed News (latest entries)</h1>",
        ]

        if not rows:
            parts.append("<p>No processed news yet.</p>")

        for idx, (link_id, url, processed_at, title, content, translated, metadata) in enumerate(rows, start=1):
            translations = parse_translations(translated, metadata or {})

            parts.append("<article>")
            parts.append(f"<h2>{idx}. <a href='{escape(url)}' target='_blank'>{escape(url)}</a></h2>")
            parts.append(f"<p><strong>ID:</strong> {link_id} | <strong>Processed at:</strong> {escape(str(processed_at))}</p>")

            summary_plain = metadata.get("summary_plain") or translations.get("en") or metadata.get("summary") or title or ""
            if summary_plain:
                parts.append("<h3>Cleaned Summary</h3>")
                parts.append(f"<div class='summary'>{format_translated_text(summary_plain)}</div>")

            if translations:
                parts.append("<div class='translations'>")
                for lang_code, label in [("en", "English"), ("zh", "简体中文"), ("ms", "Bahasa Melayu")]:
                    value = translations.get(lang_code)
                    if not value:
                        continue
                    parts.append(f"<div><h4>{label}</h4>{format_translated_text(value)}</div>")
                parts.append("</div>")

            if metadata:
                parts.append("<details><summary>Metadata (raw)</summary>")
                parts.append(f"<pre>{escape(json.dumps(metadata, ensure_ascii=False, indent=2))}</pre>")
                parts.append("</details>")
            parts.append("</article>")

        parts.append("</body></html>")
        return "".join(parts)


def run_server():
    print(f"Serving processed news on http://localhost:{PORT}/")
    server = HTTPServer(("localhost", PORT), ProcessedNewsHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
    finally:
        server.server_close()


if __name__ == "__main__":
    run_server()
