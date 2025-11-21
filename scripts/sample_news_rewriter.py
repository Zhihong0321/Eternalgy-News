"""
Quick tool to replay a saved Jina Reader response and exercise the NewsRewriter -> GPT-5-nano call.
"""

import json
from datetime import datetime
from pathlib import Path

from ai_processing.config import AIConfig
from ai_processing.services.ai_client import AIClient
from ai_processing.services.news_rewriter import NewsRewriter
from ai_processing.services.news_rewriter_prompt import NewsRewriterPrompt


def main() -> None:
    sample_path = Path("samples/jina/jina_sample_1.json")
    if not sample_path.is_file():
        raise SystemExit(f"Sample file not found: {sample_path.resolve()}")

    sample = json.loads(sample_path.read_text(encoding="utf-8"))
    title = sample.get("title") or "Untitled Story"
    content = sample.get("content") or ""
    url = sample.get("url") or "https://example.com/placeholder"
    date = sample.get("date") or datetime.utcnow().strftime("%Y-%m-%d")

    config = AIConfig.from_env()

    class LoggingAIClient(AIClient):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.last_response = None

        def chat_completion(self, *args, **kwargs):
            response = super().chat_completion(*args, **kwargs)
            self.last_response = response
            return response

    ai_client = LoggingAIClient(
        api_url=config.api_url,
        api_key=config.api_key,
        model=config.model,
        timeout=config.timeout,
        max_retries=config.max_retries,
    )

    print(f"Using model {config.model} at {config.api_url}")
    print(f"Title: {title}")
    print(f"URL: {url}")
    print(f"Excerpt: {content[:120].replace(chr(10), ' ')}...\n")

    rewriter = NewsRewriter(ai_client=ai_client)
    result = rewriter.rewrite(title=title, date=date, url=url, content=content)

    raw_response = ""
    if getattr(ai_client, "last_response", None):
        raw_response = ai_client.extract_content(ai_client.last_response)

    print("Received JSON response from GPT-5-nano:")
    if result:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("(parsed JSON missing)")

    if raw_response:
        print("\nRaw response text for debugging:")
        print(raw_response)


if __name__ == "__main__":
    main()
