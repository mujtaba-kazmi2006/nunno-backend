
from duckduckgo_search import DDGS
import json

print("Testing DuckDuckGo Search...")
try:
    with DDGS() as ddgs:
        results = list(ddgs.text('crypto news', max_results=3))
        if results:
            print(f"SUCCESS: Found {len(results)} results.")
            print(json.dumps(results, indent=2))
        else:
            print("FAILURE: Found 0 results (Empty List).")
except Exception as e:
    print(f"CRITICAL ERROR: {e}")
