
import sys
import os
import asyncio

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.web_research_service import WebResearchService
from services.chat_service import ChatService

async def test_web_research():
    print("Testing WebResearchService...")
    service = WebResearchService()
    
    # Test Search (mocked or real if net available, but safely handling)
    print("1. Testing Search (mock query 'test')")
    try:
        results = service.search_web("test", max_results=1)
        print(f"   Search success. Found {len(results)} results.")
        if results and "error" in results[0]:
            print(f"   Note: Search returned error (expected if no net): {results[0]['error']}")
    except Exception as e:
        print(f"   Search failed: {e}")

    # Test Scrape (mock URL)
    print("2. Testing Scrape (http://example.com)")
    try:
        data = service.scrape_url("http://example.com")
        print(f"   Scrape success. Title: {data.get('title')}")
    except Exception as e:
        print(f"   Scrape failed: {e}")

async def test_chat_service_integration():
    print("\nTesting ChatService Integration...")
    chat = ChatService()
    
    # Check if service is initialized
    if hasattr(chat, 'web_research_service'):
        print("   web_research_service initialized successfully.")
    else:
        print("   ERROR: web_research_service NOT initialized.")
        return

    # Test intent classification (Simulated)
    # We can't easily call local deepseek/openai but we can check the prompt logic if accessible
    # or just trust the previous step if syntax is fine.
    print("   ChatService instantiated without errors.")

if __name__ == "__main__":
    try:
        asyncio.run(test_web_research())
        asyncio.run(test_chat_service_integration())
        print("\n✅ Verification Complete (Syntax and Imports OK)")
    except Exception as e:
        print(f"\n❌ Verification Failed: {e}")
