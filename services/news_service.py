"""
News and Sentiment Service
"""

import requests
import os
from datetime import datetime
from duckduckgo_search import DDGS

class NewsService:
    """
    Market news and sentiment analysis service
    """
    
    def __init__(self):
        try:
            self.news_api_key = os.getenv("NEWS_API_KEY", "")
            self.fear_greed_url = "https://api.alternative.me/fng/"
        except Exception as e:
            print(f"Error initializing NewsService: {e}")
            self.news_api_key = ""
            self.fear_greed_url = "https://api.alternative.me/fng/"
    
    def get_news_sentiment(self, ticker: str):
        """
        Get market news and sentiment
        
        Args:
            ticker: Cryptocurrency ticker
        
        Returns:
            News and sentiment data with beginner explanations
        """
        try:
            # Get Fear & Greed Index
            fear_greed = self._get_fear_greed_index()
            
            # Get news headlines (try API or fallback)
            headlines = self._get_news_headlines(ticker)
            
            # Determine overall sentiment
            sentiment = self._determine_sentiment(fear_greed, headlines)
            
            response = {
                "ticker": ticker,
                "timestamp": datetime.now().isoformat(),
                "fear_greed_index": fear_greed,
                "sentiment": sentiment,
                "headlines": headlines[:5],  # Top 5 headlines
                "explanation": self._create_sentiment_explanation(fear_greed, sentiment),
                "beginner_notes": {
                    "Fear & Greed Index": "This index measures market emotions from 0 (Extreme Fear) to 100 (Extreme Greed). It's like a mood ring for the crypto market!",
                    "Sentiment": "Sentiment is the overall feeling or mood of the market. Positive sentiment means people are optimistic, negative means they're worried.",
                    "News Impact": "News can move markets quickly. Good news often pushes prices up, bad news can cause panic selling."
                }
            }
            
            return response
            
        except Exception as e:
            return {
                "error": str(e),
                "message": "Unable to fetch news and sentiment data."
            }
    
    def _get_fear_greed_index(self):
        """Fetch the crypto Fear & Greed Index"""
        try:
            response = requests.get(self.fear_greed_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            value = int(data["data"][0]["value"])
            classification = data["data"][0]["value_classification"]
            
            return {
                "value": value,
                "classification": classification,
                "description": self._explain_fear_greed(value)
            }
        except Exception:
            return {
                "value": 50,
                "classification": "Neutral",
                "description": "Unable to fetch current Fear & Greed data"
            }
    
    def _explain_fear_greed(self, value: int) -> str:
        """Explain Fear & Greed value in beginner terms"""
        if value <= 25:
            return "Extreme Fear - People are very worried and selling. This can sometimes be a buying opportunity (like a sale at a store)."
        elif value <= 45:
            return "Fear - The market is nervous. Prices might be lower than usual."
        elif value <= 55:
            return "Neutral - The market is balanced. No strong emotions either way."
        elif value <= 75:
            return "Greed - People are getting excited and buying. Prices might be getting high."
        else:
            return "Extreme Greed - Everyone is very excited and buying. This can be risky (like buying something when it's most expensive)."
    
    def _get_news_headlines(self, ticker: str):
        """Fetch news headlines (uses NewsAPI with DDG fallback)"""
        headlines = []
        
        # Try NewsAPI first if key exists
        if self.news_api_key:
            try:
                # Extract coin name from ticker
                coin_name = ticker.replace("USDT", "").replace("USD", "")
                
                url = f"https://newsapi.org/v2/everything?q={coin_name}+cryptocurrency&sortBy=publishedAt&language=en&apiKey={self.news_api_key}"
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                
                articles = response.json().get("articles", [])
                headlines = [
                    {
                        "title": article["title"],
                        "source": article["source"]["name"],
                        "published": article["publishedAt"],
                        "url": article["url"]
                    }
                    for article in articles[:5]
                ]
                return headlines
            except Exception as e:
                print(f"NewsAPI failed: {e}")
                # Fall through to DDG
        
        # Fallback to DuckDuckGo
        try:
            print(f"Fetching news via DuckDuckGo for {ticker}...")
            # Clean ticker for better search
            search_term = ticker.replace("USDT", "").replace("USD", "") + " crypto news"
            
            with DDGS() as ddgs:
                results = list(ddgs.text(search_term, max_results=5))
                
            headlines = [
                {
                    "title": r.get("title", ""),
                    "source": "Web Search",
                    "published": datetime.now().isoformat(), # DDG doesn't always give date, use current
                    "url": r.get("href", "")
                }
                for r in results
            ]
            return headlines
        except Exception as e:
            print(f"DDG News Search failed: {e}")
            return []
    
    def _determine_sentiment(self, fear_greed: dict, headlines: list) -> str:
        """Determine overall sentiment"""
        fg_value = fear_greed.get("value", 50)
        
        if fg_value <= 30:
            return "Bearish"
        elif fg_value <= 45:
            return "Slightly Bearish"
        elif fg_value <= 55:
            return "Neutral"
        elif fg_value <= 70:
            return "Slightly Bullish"
        else:
            return "Bullish"
    
    def _create_sentiment_explanation(self, fear_greed: dict, sentiment: str) -> str:
        """Create beginner-friendly sentiment explanation"""
        fg_value = fear_greed.get("value", 50)
        fg_class = fear_greed.get("classification", "Neutral")
        
        explanation = f"The market sentiment is currently **{sentiment}**. "
        explanation += f"The Fear & Greed Index is at {fg_value}/100 ({fg_class}). "
        explanation += fear_greed.get("description", "")
        
        return explanation
