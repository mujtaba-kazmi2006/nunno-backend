
import sys
import os
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.news_service import NewsService

def test_news_fallback():
    print("Testing NewsService Fallback...")
    
    # Force API key to be empty to test fallback
    service = NewsService()
    service.news_api_key = "" 
    print("   (Forced API Key to empty)")

    ticker = "BTCUSDT"
    print(f"1. Fetching news for {ticker}...")
    
    try:
        data = service.get_news_sentiment(ticker)
        headlines = data.get("headlines", [])
        
        if headlines:
            print(f"   SUCCESS: Found {len(headlines)} headlines via Fallback.")
            print(f"   Sample: {headlines[0]['title']}")
            print(f"   Source: {headlines[0]['source']}")
        else:
            print("   FAILURE: No headlines found.")
            
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    test_news_fallback()
