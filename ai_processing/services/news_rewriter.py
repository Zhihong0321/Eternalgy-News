"""
News Rewriter Service
Calls GPT-5-nano with the News Rewriter prompt to produce the BBcode/JSON output.
"""

import json
from typing import Dict

from .ai_client import AIClient
from .news_rewriter_prompt import NewsRewriterPrompt


class NewsRewriter:
    """
    Uses the News Rewriter prompt to transform a raw article into translated summaries.
    """

    def __init__(self, ai_client: AIClient, temperature: float = 0.3, max_tokens: int = 1200):
        self.ai_client = ai_client
        self.temperature = temperature
        self.max_tokens = max_tokens

    def rewrite(self, title: str, date: str, url: str, content: str) -> Dict[str, str]:
        """
        Run the News Rewriter prompt and return the parsed JSON result.
        """
        prompt = NewsRewriterPrompt(
            title=title,
            date=date,
            url=url,
            content=content
        ).build_prompt()

        messages = [
            {"role": "system", "content": "You are an expert News Analyst and Multilingual Content Specialist."},
            {"role": "user", "content": prompt}
        ]

        response = self.ai_client.chat_completion(
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )

        text = self.ai_client.extract_content(response).strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            print(f"[NewsRewriter] Failed to parse JSON output: {exc}")
            return {}
