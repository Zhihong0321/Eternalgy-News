import json
from pathlib import Path

from ai_processing.config import AIConfig
from ai_processing.services.ai_client import AIClient
from ai_processing.services.news_rewriter_prompt import NewsRewriterPrompt


def main() -> None:
    sample_path = Path("samples/jina/jina_sample_1.json")
    if not sample_path.exists():
        raise SystemExit(f"Sample not found: {sample_path}")

    sample = json.loads(sample_path.read_text(encoding="utf-8"))
    title = sample.get("title") or "Untitled"
    content = sample.get("content") or ""
    url = sample.get("url") or "https://example.com/"
    date = sample.get("date") or "2025-11-19"

    config = AIConfig.from_env()
    ai_client = AIClient(
        api_url=config.api_url,
        api_key=config.api_key,
        model=config.model,
        timeout=config.timeout,
        max_retries=config.max_retries,
    )

    prompt_text = NewsRewriterPrompt(title=title, date=date, url=url, content=content).build_prompt()
    response = ai_client.chat_completion(
        messages=[
            {"role": "system", "content": "You are an expert News Analyst and Multilingual Content Specialist."},
            {"role": "user", "content": prompt_text},
        ],
        temperature=0.3,
        max_tokens=1200,
    )

    raw_text = ""
    try:
        raw_text = ai_client.extract_content(response)
    except Exception:
        raw_text = ""

    parsed = {}
    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        parsed = {}

    dest = Path("artifacts")
    dest.mkdir(exist_ok=True)

    output = {
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        "title": title,
        "url": url,
        "prompt": prompt_text,
        "raw_response": response,
        "raw_text": raw_text,
        "parsed_json": parsed,
    }

    target = dest / "latest_rewriter_response.json"
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved response to {target}")


if __name__ == "__main__":
    main()
