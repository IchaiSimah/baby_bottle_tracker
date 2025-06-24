#!/usr/bin/env python3
"""
Test script for PDF translation optimization
"""
import os
import asyncio
from dotenv import load_dotenv
from handlers.pdf import translate_multiple_texts_with_ai, translate_text_with_ai

# Load environment variables
load_dotenv()

async def test_single_translation():
    """Test single text translation"""
    print("🧪 Testing single text translation...")
    
    test_text = "Bébé a fait un gros caca"
    result = await translate_text_with_ai(test_text, 'en')
    
    print(f"Original: {test_text}")
    print(f"Translated: {result}")
    print()

async def test_multiple_translation():
    """Test multiple texts translation"""
    print("🧪 Testing multiple texts translation...")
    
    test_texts = [
        "Bébé a fait un gros caca",
        "Bébé a bien mangé",
        "Bébé a dormi toute la nuit",
        "Bébé a fait pipi",
        "Bébé a vomi un peu"
    ]
    
    print(f"Original texts ({len(test_texts)}):")
    for i, text in enumerate(test_texts, 1):
        print(f"  {i}. {text}")
    
    print(f"\n🌍 Translating to English...")
    result = await translate_multiple_texts_with_ai(test_texts, 'en')
    
    print(f"\nTranslated texts:")
    for i, text in enumerate(result, 1):
        print(f"  {i}. {text}")
    print()

async def test_hebrew_translation():
    """Test Hebrew translation"""
    print("🧪 Testing Hebrew translation...")
    
    test_texts = [
        "Bébé a fait un gros caca",
        "Bébé a bien mangé"
    ]
    
    print(f"Original texts:")
    for i, text in enumerate(test_texts, 1):
        print(f"  {i}. {text}")
    
    print(f"\n🌍 Translating to Hebrew...")
    result = await translate_multiple_texts_with_ai(test_texts, 'he')
    
    print(f"\nTranslated texts:")
    for i, text in enumerate(result, 1):
        print(f"  {i}. {text}")
    print()

async def test_performance_comparison():
    """Compare performance between single and multiple translation"""
    print("⚡ Performance comparison...")
    
    test_texts = [
        "Bébé a fait un gros caca",
        "Bébé a bien mangé",
        "Bébé a dormi toute la nuit"
    ]
    
    # Test multiple translation (optimized)
    print("Testing multiple translation (1 API call)...")
    start_time = asyncio.get_event_loop().time()
    result_multiple = await translate_multiple_texts_with_ai(test_texts, 'en')
    multiple_time = asyncio.get_event_loop().time() - start_time
    
    print(f"Multiple translation took: {multiple_time:.2f} seconds")
    print(f"Results: {result_multiple}")
    
    # Test individual translations (old method)
    print("\nTesting individual translations (3 API calls)...")
    start_time = asyncio.get_event_loop().time()
    result_individual = []
    for text in test_texts:
        translated = await translate_text_with_ai(text, 'en')
        result_individual.append(translated)
    individual_time = asyncio.get_event_loop().time() - start_time
    
    print(f"Individual translations took: {individual_time:.2f} seconds")
    print(f"Results: {result_individual}")
    
    print(f"\n📊 Performance improvement:")
    print(f"  Multiple: {multiple_time:.2f}s")
    print(f"  Individual: {individual_time:.2f}s")
    print(f"  Speedup: {individual_time/multiple_time:.1f}x faster")
    print(f"  API calls saved: {len(test_texts) - 1}")

async def main():
    """Main test function"""
    print("🚀 PDF Translation Optimization Test")
    print("=" * 50)
    
    # Check if API key is available
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment variables")
        return
    
    print(f"✅ GEMINI_API_KEY found: {api_key[:10]}...")
    print()
    
    # Run tests
    await test_single_translation()
    await test_multiple_translation()
    await test_hebrew_translation()
    await test_performance_comparison()
    
    print("🎉 All tests completed!")

if __name__ == "__main__":
    asyncio.run(main()) 