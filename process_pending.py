from news_search.processor_worker import ProcessorWorker
from ai_processing.processor_with_content import ArticleProcessorWithContent
from ai_processing.processor_adapter import ProcessorAdapter

print("Initializing processor...")
try:
    ai_processor = ArticleProcessorWithContent.from_env()
    adapter = ProcessorAdapter(ai_processor)
    worker = ProcessorWorker(ai_processor=adapter)
except Exception as e:
    print(f"Error initializing AI processor: {e}")
    worker = ProcessorWorker()

print("Processing pending links...")
stats = worker.process_pending_links(limit=50)
print("Processing stats:", stats)
