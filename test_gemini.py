#!/usr/bin/env python3
"""
Test script for Gemini API integration
"""
import os
import asyncio
from dotenv import load_dotenv
from handlers.stats import generate_ai_summary

# Load environment variables
load_dotenv()

async def test_gemini():
    """Test the Gemini API integration"""
    print("Testing Gemini API integration...")
    
    # Check if API key is available
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment variables")
        return False
    
    print(f"✅ GEMINI_API_KEY found: {api_key[:10]}...")
    
    # Create test stats data
    test_stats = {
        "01-01-2024": {
            "bottles": 5,
            "total_ml": 750,
            "poops": 3,
            "date": "2024-01-01"
        },
        "02-01-2024": {
            "bottles": 6,
            "total_ml": 900,
            "poops": 2,
            "date": "2024-01-02"
        }
    }
    
    try:
        print("Sending test request to Gemini...")
        result = await generate_ai_summary(test_stats)
        
        if result:
            print(f"✅ Gemini API test successful!")
            print(f"Response: {result}")
            return True
        else:
            print("❌ Gemini API returned None")
            return False
            
    except Exception as e:
        print(f"❌ Gemini API test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_gemini())
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n💥 Tests failed!") 