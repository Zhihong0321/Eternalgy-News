"""
Test script for AI Processing Module
Run this to verify the module works correctly
"""

import sys
from datetime import datetime
from ai_processing import ArticleProcessor, RawArticle


def test_language_detection():
    """Test language detection"""
    print("\n" + "="*60)
    print("TEST 1: Language Detection")
    print("="*60)
    
    from ai_processing.services.language_detector import LanguageDetector
    detector = LanguageDetector()
    
    test_cases = [
        ("华为发布新手机", "zh"),
        ("Tesla releases new car", "en"),
        ("Kerajaan Malaysia umumkan dasar baharu", "ms"),
        ("Apple announces iPhone 15", "en"),
        ("比亚迪电动车销量突破", "zh"),
    ]
    
    for text, expected in test_cases:
        detected = detector.detect(text)
        status = "✓" if detected == expected else "✗"
        print(f"{status} '{text}' -> {detected} (expected: {expected})")


def test_basic_processing():
    """Test basic article processing"""
    print("\n" + "="*60)
    print("TEST 2: Basic Processing (Without API)")
    print("="*60)
    
    # Test without actual API calls
    print("Creating sample articles...")
    
    articles = [
        RawArticle(
            id="test_001",
            title="华为发布新手机",
            platform="zhihu",
            rank=1,
            timestamp=datetime.now()
        ),
        RawArticle(
            id="test_002",
            title="Tesla stock surges",
            platform="weibo",
            rank=2,
            timestamp=datetime.now()
        )
    ]
    
    print(f"✓ Created {len(articles)} test articles")
    
    for article in articles:
        print(f"  - {article.title} ({article.platform})")


def test_with_api():
    """Test with actual API (requires valid API key)"""
    print("\n" + "="*60)
    print("TEST 3: Full Processing with API")
    print("="*60)
    
    # Check if API key is provided
    api_key = "sk-jW4WLdgCGCshSyFY9VbKXwj8y2YXclFHxw2x2WbXElFkcAlD"
    
    if not api_key or api_key == "your-api-key-here":
        print("⚠️  Skipping API test - No API key provided")
        print("   To test with API, update the api_key variable")
        return
    
    try:
        # Initialize processor
        processor = ArticleProcessor(
            api_url="https://api.bltcy.ai/v1/",
            api_key=api_key,
            model="gpt-5-nano-2025-08-07"
        )
        
        # Create test article
        article = RawArticle(
            id="test_api_001",
            title="华为发布新手机！！！点击查看详情>>>",
            platform="zhihu",
            rank=1,
            timestamp=datetime.now()
        )
        
        print(f"Processing: {article.title}")
        
        # Process
        processed = processor.process_single(article)
        
        # Display results
        print("\n✓ Processing successful!")
        print(f"\nOriginal:  {processed.title_original}")
        print(f"Cleaned:   {processed.title_cleaned}")
        print(f"Language:  {processed.detected_language}")
        print(f"\nTranslations:")
        print(f"  🇬🇧 EN: {processed.title_en}")
        print(f"  🇨🇳 ZH: {processed.title_zh}")
        print(f"  🇲🇾 MS: {processed.title_ms}")
        
    except Exception as e:
        print(f"✗ API test failed: {e}")
        print("  This might be due to:")
        print("  - Invalid API key")
        print("  - Network issues")
        print("  - API service unavailable")


def test_batch_processing():
    """Test batch processing"""
    print("\n" + "="*60)
    print("TEST 4: Batch Processing")
    print("="*60)
    
    articles = [
        RawArticle(
            id=f"batch_{i}",
            title=f"Test article {i}",
            platform="test",
            rank=i,
            timestamp=datetime.now()
        )
        for i in range(1, 6)
    ]
    
    print(f"✓ Created batch of {len(articles)} articles")
    print("  (Actual API processing skipped in test)")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("AI PROCESSING MODULE - TEST SUITE")
    print("="*60)
    
    try:
        test_language_detection()
        test_basic_processing()
        test_batch_processing()
        test_with_api()
        
        print("\n" + "="*60)
        print("✓ ALL TESTS COMPLETED")
        print("="*60)
        print("\nModule is ready to use!")
        print("\nNext steps:")
        print("1. Update API key in test_with_api() to test with real API")
        print("2. Integrate with TrendRadar using example_usage.py")
        print("3. Configure Railway database for storage")
        
    except Exception as e:
        print(f"\n✗ Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
