import sys
import os

# Add root directory to sys.path
root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_path)
print(f"Added root path: {root_path}")

print("--- Testing tokenomics_utils import ---")
try:
    import tokenomics_utils
    print("SUCCESS: tokenomics_utils imported")
    try:
        t = tokenomics_utils.ComprehensiveTokenomics()
        print("SUCCESS: ComprehensiveTokenomics instantiated")
    except Exception as e:
        print(f"FAILURE: Instantiate ComprehensiveTokenomics: {e}")
except Exception as e:
    print(f"FAILURE: Import tokenomics_utils: {e}")

print("\n--- Testing betterpredictormodule import ---")
try:
    import betterpredictormodule
    print("SUCCESS: betterpredictormodule imported")
    try:
        t = betterpredictormodule.TradingAnalyzer()
        print("SUCCESS: TradingAnalyzer instantiated")
    except Exception as e:
        print(f"FAILURE: Instantiate TradingAnalyzer: {e}")
except Exception as e:
    print(f"FAILURE: Import betterpredictormodule: {e}")
