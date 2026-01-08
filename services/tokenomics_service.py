"""
Tokenomics Analysis Service
"""

import sys
import os

class TokenomicsService:
    """
    Tokenomics analysis service with beginner explanations
    """
    
    def __init__(self):
        # Try to import existing tokenomics utilities
        try:
            # Go up 4 levels to reach Nunno Streamlit folder
            root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            if root_path not in sys.path:
                sys.path.append(root_path)
                
            from tokenomics_utils import ComprehensiveTokenomics
            self.tokenomics = ComprehensiveTokenomics()
            self.available = True
        except Exception as e:
            print(f"Warning: Could not import tokenomics_utils: {e}. Tokenomics disabled.")
            self.tokenomics = None
            self.available = False
    
    def analyze(self, coin_id: str, investment_amount: float = 1000):
        """
        Analyze tokenomics for a cryptocurrency
        
        Args:
            coin_id: CoinGecko coin ID (e.g., bitcoin, ethereum)
            investment_amount: Investment amount for calculations
        
        Returns:
            Tokenomics analysis with beginner explanations
        """
        if not self.available:
            return {
                "error": "Tokenomics analysis not available",
                "message": "The tokenomics module is not configured. This feature will be available soon!"
            }
        
        try:
            # Fetch comprehensive data
            print(f"DEBUG: Fetching tokenomics for {coin_id}...")
            data = self.tokenomics.fetch_comprehensive_token_data(coin_id, investment_amount)
            
            if not data:
                print(f"DEBUG: Tokenomics data is None/Empty for {coin_id}")
                return {
                    "error": "Data not found",
                    "message": f"Could not find tokenomics data for {coin_id}"
                }
            print(f"DEBUG: Successfully fetched tokenomics for {coin_id}")
            
            # Format for beginner-friendly response
            # Return the full comprehensive data directly
            # The AI will handle the formatting and beginner explanations
            return data
            
            return response
            
        except Exception as e:
            return {
                "error": str(e),
                "message": "Unable to fetch tokenomics data. Please try again."
            }
    
    def _create_beginner_analysis(self, data: dict) -> str:
        """Create beginner-friendly analysis text"""
        name = data.get("Token_Name", "This token")
        price = data.get("Current_Price", 0)
        rank = data.get("Market_Cap_Rank", 0)
        supply_model = data.get("Supply_Model", "Unknown")
        risk = data.get("Risk_Level", "Unknown")
        
        analysis = f"{name} is currently ranked #{rank} by market cap, trading at ${price}. "
        
        if supply_model == "Deflationary":
            analysis += "It has a deflationary supply model (Beginner's Note: This means the number of coins decreases over time, like Bitcoin, which can make each coin more valuable). "
        elif supply_model == "Inflationary":
            analysis += "It has an inflationary supply model (Beginner's Note: This means new coins are created over time, which can dilute value but fund development). "
        
        analysis += f"The risk level is assessed as {risk}. "
        
        return analysis
