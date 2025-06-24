#!/usr/bin/env python3
"""
Detailed test script for Gemini API - check available models and test 2.5 Flash-Lite
"""
import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def list_available_models():
    """List all available models for the API key"""
    print("🔍 Listing available Gemini models...")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found")
        return []
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            
            print(f"✅ Found {len(models)} available models:")
            for model in models:
                name = model.get('name', 'Unknown')
                display_name = model.get('displayName', 'Unknown')
                description = model.get('description', 'No description')
                print(f"  📋 {name}")
                print(f"     Display: {display_name}")
                print(f"     Description: {description}")
                print()
            
            return [model.get('name', '').split('/')[-1] for model in models]
        else:
            print(f"❌ Error listing models: {response.status_code}")
            print(f"Response: {response.text}")
            return []
            
    except Exception as e:
        print(f"❌ Exception listing models: {e}")
        return []

def test_specific_model(model_name):
    """Test a specific model with a simple request"""
    print(f"\n🧪 Testing model: {model_name}")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found")
        return False
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
    params = {"key": api_key}
    
    request_data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": "Bonjour, peux-tu me dire 'Test réussi' en français ?"
                    }
                ]
            }
        ]
    }
    
    try:
        response = requests.post(
            url,
            params=params,
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                candidate = result['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    parts = candidate['content']['parts']
                    if len(parts) > 0 and 'text' in parts[0]:
                        ai_text = parts[0]['text'].strip()
                        print(f"✅ Success! Response: {ai_text}")
                        return True
            
            print(f"❌ Unexpected response format: {result}")
            return False
            
        elif response.status_code == 429:
            print("❌ Quota exceeded")
            return False
            
        elif response.status_code == 404:
            print("❌ Model not found")
            return False
            
        elif response.status_code == 400:
            print("❌ Bad request")
            print(f"Response: {response.text}")
            return False
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Gemini API Detailed Test")
    print("=" * 50)
    
    # List available models
    available_models = list_available_models()
    
    # Test specific models we're interested in
    models_to_test = [
        "gemini-2.5-flash-lite-preview-06-17",
        "gemini-2.5-flash-latest", 
        "gemini-1.5-pro",
        "gemini-1.5-flash-latest",
        "gemini-1.5-flash"
    ]
    
    print("\n" + "=" * 50)
    print("🧪 Testing specific models...")
    
    working_models = []
    for model in models_to_test:
        if test_specific_model(model):
            working_models.append(model)
    
    print("\n" + "=" * 50)
    print("📊 Summary:")
    print(f"Available models: {len(available_models)}")
    print(f"Working models from our list: {len(working_models)}")
    
    if working_models:
        print("✅ Working models:")
        for model in working_models:
            print(f"  - {model}")
    else:
        print("❌ No working models found")
    
    # Check if 2.5 models are available
    models_25 = [m for m in available_models if "2.5" in m]
    if models_25:
        print(f"\n🎉 Found 2.5 models: {models_25}")
    else:
        print("\n❌ No 2.5 models found in available models list")

if __name__ == "__main__":
    main() 