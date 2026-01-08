"""
Technical Analysis Service
Converted from betterpredictormodule.py to FastAPI service
"""

import sys
import os
# Fix import path to find betterpredictormodule.py in the root folder (Nunno Streamlit)
# Path structure: Nunno Streamlit/NunnoFinance/backend/services/technical_analysis.py
# We need to go up 4 levels to reach Nunno Streamlit
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

# Import the existing TradingAnalyzer class
try:
    from betterpredictormodule import TradingAnalyzer
except Exception as e:
    # Fallback if path is still wrong or module specific issues
    print(f"Warning: Could not import betterpredictormodule: {e}. Using mock.")
    class TradingAnalyzer:
        pass

class TechnicalAnalysisService:
    """
    FastAPI-compatible wrapper for technical analysis
    Returns clean JSON with beginner-friendly explanations
    """
    
    def __init__(self):
        self.analyzer = TradingAnalyzer()
    
    def analyze(self, ticker: str, interval: str = "15m"):
        """
        Perform technical analysis and return beginner-friendly JSON
        
        Args:
            ticker: Trading pair (e.g., BTCUSDT)
            interval: Timeframe (e.g., 15m, 1h, 4h, 1d)
        
        Returns:
            Dict with analysis results and explanations
        """
        try:
            # Fetch and analyze data
            # Fetch and analyze data using the robust fallback method
            df = self.analyzer.fetch_binance_ohlcv_with_fallback(symbol=ticker, interval=interval, limit=500)
            df = self.analyzer.add_comprehensive_indicators(df)
            confluences, latest_row = self.analyzer.generate_comprehensive_analysis(df)
            bias, strength = self.analyzer.calculate_confluence_strength(confluences)
            
            # Check if data is synthetic
            data_source = df.attrs.get('data_source', 'Live Market Data')
            is_synthetic = 'Synthetic' in data_source
            
            # Extract key metrics
            current_price = float(latest_row['Close'])
            rsi = float(latest_row['RSI_14'])
            macd = float(latest_row['MACD'])
            macd_signal = float(latest_row['MACD_Signal'])
            
            # Determine bias
            bias_simple = "bullish" if "Bullish" in bias else "bearish" if "Bearish" in bias else "neutral"
            
            # Extract signals
            signals = []
            if latest_row['EMA_9'] > latest_row['EMA_21'] > latest_row['EMA_50']:
                signals.append("golden_cross")
            if latest_row['EMA_9'] < latest_row['EMA_21'] < latest_row['EMA_50']:
                signals.append("death_cross")
            if rsi < 30:
                signals.append("oversold")
            if rsi > 70:
                signals.append("overbought")
            if macd > macd_signal:
                signals.append("macd_bullish")
            if macd < macd_signal:
                signals.append("macd_bearish")
            
            # Create beginner-friendly explanation
            explanation = self._create_beginner_explanation(
                ticker, bias_simple, rsi, current_price, latest_row, confluences
            )
            
            # Prepare price history for charting (last 50 candles)
            chart_data = df[['Close', 'EMA_9', 'EMA_21']].tail(50)
            price_history = []
            for idx, row in chart_data.iterrows():
                price_history.append({
                    'timestamp': idx.strftime('%Y-%m-%d %H:%M') if hasattr(idx, 'strftime') else str(idx),
                    'price': float(row['Close']),
                    'ema9': float(row['EMA_9']),
                    'ema21': float(row['EMA_21'])
                })
            
            # Build response
            response = {
                "ticker": ticker,
                "interval": interval,
                "current_price": current_price,
                "bias": bias_simple,
                "confidence": round(strength, 1),
                "rsi": round(rsi, 1),
                "signals": signals,
                "explanation": explanation,
                "data_source": data_source,
                "is_synthetic": is_synthetic,
                "price_history": price_history,  # NEW: Price data for charting
                "key_levels": {
                    "support": float(latest_row['S1']),
                    "resistance": float(latest_row['R1']),
                    "pivot": float(latest_row['Pivot']),
                    "bb_upper": float(latest_row['BB_Upper']),
                    "bb_lower": float(latest_row['BB_Lower'])
                },
                "confluences": {
                    "bullish_count": len(confluences['bullish']),
                    "bearish_count": len(confluences['bearish']),
                    "neutral_count": len(confluences['neutral']),
                    "bullish_signals": [self._format_confluence(c) for c in confluences['bullish'][:3]],
                    "bearish_signals": [self._format_confluence(c) for c in confluences['bearish'][:3]]
                },
                "beginner_notes": self._get_beginner_notes(rsi, macd, latest_row)
            }
            
            return response
            
        except Exception as e:
            return {
                "error": str(e),
                "ticker": ticker,
                "message": "Unable to fetch analysis. Please try again."
            }
    
    def _create_beginner_explanation(self, ticker, bias, rsi, price, row, confluences):
        """Create a simple, beginner-friendly explanation"""
        
        explanations = []
        
        # Price context
        explanations.append(f"{ticker} is currently trading at ${price:.2f}.")
        
        # Bias explanation
        if bias == "bullish":
            explanations.append("The market is showing **bullish** signs, which means prices might go up. Think of it like a runner who has momentum going uphill.")
        elif bias == "bearish":
            explanations.append("The market is showing **bearish** signs, which means prices might go down. Think of it like a runner losing steam going downhill.")
        else:
            explanations.append("The market is **neutral** right now, like a runner taking a break. It could go either way.")
        
        # RSI explanation
        if rsi < 30:
            explanations.append(f"The RSI is at {rsi:.1f}, which is **oversold** (like a runner who's been sprinting too long and needs to rest). This often means a bounce might happen soon.")
        elif rsi > 70:
            explanations.append(f"The RSI is at {rsi:.1f}, which is **overbought** (like a runner who's been climbing too fast and might slow down). This could mean a pullback is coming.")
        else:
            explanations.append(f"The RSI is at {rsi:.1f}, which is in the normal range. The market isn't too hot or too cold right now.")
        
        # Confluence count
        bull_count = len(confluences['bullish'])
        bear_count = len(confluences['bearish'])
        
        if bull_count > bear_count:
            explanations.append(f"I found {bull_count} bullish signals and {bear_count} bearish signals, so the bulls (buyers) seem to have the upper hand.")
        elif bear_count > bull_count:
            explanations.append(f"I found {bear_count} bearish signals and {bull_count} bullish signals, so the bears (sellers) seem to be in control.")
        else:
            explanations.append(f"The market is balanced with {bull_count} bullish and {bear_count} bearish signals. It's a tug-of-war right now!")
        
        return " ".join(explanations)
    
    def _format_confluence(self, confluence):
        """Format a confluence signal for JSON response"""
        return {
            "indicator": confluence['indicator'],
            "condition": confluence['condition'],
            "strength": confluence['strength'],
            "timeframe": confluence['timeframe']
        }
    
    def _get_beginner_notes(self, rsi, macd, row):
        """Generate beginner notes for technical terms"""
        notes = {
            "RSI": f"RSI (Relative Strength Index) measures if something is overbought or oversold. It's like a thermometer for market momentum. Current: {rsi:.1f}",
            "MACD": "MACD shows the relationship between two moving averages. When it crosses above the signal line, it's bullish (good for buyers).",
            "EMA": "EMA (Exponential Moving Average) is like a smoothed-out price line that helps spot trends. Newer prices matter more.",
            "Support": f"Support is a price level where buyers usually step in. Think of it as a safety net. Current: ${row['S1']:.2f}",
            "Resistance": f"Resistance is a price level where sellers usually appear. Think of it as a ceiling. Current: ${row['R1']:.2f}",
            "Bollinger Bands": "These bands show if prices are high or low compared to recent averages. Prices usually bounce between them.",
            "Volume": "Volume shows how many people are trading. High volume means strong interest, like a crowded store.",
            "ATR": f"ATR (Average True Range) measures volatility. Higher ATR means bigger price swings. Current: {row['ATR_Percent']:.2f}%"
        }
        return notes
