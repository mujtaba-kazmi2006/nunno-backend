import sys
import os
from dotenv import load_dotenv
import json

# Setup paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_path)

# Load env
load_dotenv()

from services.technical_analysis import TechnicalAnalysisService

def test_analysis():
    print("Initializing TechnicalAnalysisService...")
    service = TechnicalAnalysisService()
    
    print("\nRequesting analysis for BTCUSDT...")
    result = service.analyze("BTCUSDT", "15m")
    
    print("\n--- Analysis Result ---")
    print(f"Ticker: {result.get('ticker')}")
    print(f"Current Price: {result.get('current_price')}")
    print(f"Data Source: {result.get('data_source')}")
    print(f"Is Synthetic: {result.get('is_synthetic')}")
    print(f"Signals: {result.get('signals')}")
    
    # Check if price is realistic (BTC > 10000)
    price = result.get('current_price', 0)
    if price > 10000 and not result.get('is_synthetic'):
        print("\n✅ Valid Realtime Data Detected")
    else:
        print("\n❌ SYNTHETIC or INVALID Data Detected")

if __name__ == "__main__":
    test_analysis()
