## Step Nov 19 002 – Handoff notes

### Context summary

- We've switched the pipeline to pull Markdown from `r.jina.ai` and rewritten it through the new `NewsRewriter` prompt/service (`ai_processing/services/news_rewriter_prompt.py` + `ai_processing/services/news_rewriter.py`).  
- The processor now persists translated summaries, tags, country/date metadata, and marks blocked attempts in the `blacklisted_sites` table (`news_search/database.py`).  
- `processor_worker` skips blacklisted domains and records new ones when Jina returns 403/451 so we don't retry the same domain again.  
- `test_extraction.py` demonstrates the current blocked URL path (AP news returning 451) and logs the failure details.

### Next-session task list

1. **Run end-to-end**: Ensure Postgres (`docker-compose up -d`) and valid API keys are set, then execute `REAL_TEST_FROM_ZERO.py` to confirm the entire search → Jina Reader → NewsRewriter → DB workflow works, and inspect `processed_content` to verify BBCode, translations, and metadata are stored.  
2. **Verify blacklist behavior**: Trigger a known blocked URL, then confirm `blacklisted_sites` contains the domain/title/reason and that `ProcessorWorker` skips future items from that domain.  
3. **Document Step 2 plan** (per earlier instruction): once you're ready, implement the 4o-mini-web-search retry for blacklisted titles and wire it to the worker; but don't do this until the core pipeline lands (just note it for now).  
4. **Clean working tree**: After the run, ensure no extraneous temp files remain so the next agent inherits a clear workspace.  
