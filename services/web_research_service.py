"""
Web Research and Scraping Service
Uses DuckDuckGo for search and BeautifulSoup for scraping
"""

import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
import json

class WebResearchService:
    """
    Service for web searching and content scraping
    """
    
    def __init__(self):
        self.ddgs = DDGS()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def search_web(self, query: str, max_results: int = 5):
        """
        Search the web using DuckDuckGo
        """
        try:
            results = list(self.ddgs.text(query, max_results=max_results))
            return [
                {
                    "title": r.get("title"),
                    "href": r.get("href"),
                    "body": r.get("body")
                }
                for r in results
            ]
        except Exception as e:
            print(f"Search error: {e}")
            return [{"error": str(e)}]

    def scrape_url(self, url: str):
        """
        Scrape text content from a URL
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove scripts and styles
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
                
            # Get text
            text = soup.get_text()
            
            # Clean text (remove extra whitespace)
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            clean_text = '\n'.join(chunk for chunk in chunks if chunk)
            
            # Limit length to avoid context overflow (approx 4000 chars)
            return {
                "url": url,
                "title": soup.title.string if soup.title else "No Title",
                "content": clean_text[:4000] + "..." if len(clean_text) > 4000 else clean_text
            }
            
        except Exception as e:
            return {
                "url": url,
                "error": str(e),
                "content": "Could not scrape content."
            }
