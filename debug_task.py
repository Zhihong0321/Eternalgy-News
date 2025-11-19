from news_search.search_module import NewsSearchModule
from news_search.processor_worker import ProcessorWorker
from ai_processing.processor_with_content import ArticleProcessorWithContent
from ai_processing.processor_adapter import ProcessorAdapter
import traceback

try:
    print("Initializing components...")
    ai_processor = ArticleProcessorWithContent.from_env()
    adapter = ProcessorAdapter(ai_processor)
    processor_worker = ProcessorWorker(ai_processor=adapter)
    search_module = NewsSearchModule(processor_worker=processor_worker)
    
    print("Running task...")
    result = search_module.run_task("Malaysia Solar PV")
    print("Result:", result)

except Exception as e:
    print("Error:")
    traceback.print_exc()
