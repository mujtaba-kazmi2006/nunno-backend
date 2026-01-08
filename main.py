"""
Nunno Finance - FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)
print("DEBUG: Successfully loaded environment variables")
print("DEBUG: Starting Nunno Finance Backend...")

# Import services
from services.technical_analysis import TechnicalAnalysisService
from services.chat_service import ChatService
from services.tokenomics_service import TokenomicsService
from services.news_service import NewsService

app = FastAPI(
    title="Nunno Finance API",
    description="Empathetic AI Financial Educator for Beginners",
    version="1.0.0"
)

# CORS configuration for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services with error handling
try:
    technical_service = TechnicalAnalysisService()
except Exception as e:
    print(f"Failed to initialize TechnicalAnalysisService: {e}")
    technical_service = None

try:
    chat_service = ChatService()
except Exception as e:
    print(f"Failed to initialize ChatService: {e}")
    chat_service = None

try:
    tokenomics_service = TokenomicsService()
except Exception as e:
    print(f"Failed to initialize TokenomicsService: {e}")
    tokenomics_service = None

try:
    news_service = NewsService()
except Exception as e:
    print(f"Failed to initialize NewsService: {e}")
    news_service = None

# Request/Response Models
class ChatRequest(BaseModel):
    message: str
    user_name: str = "User"
    user_age: int = 18
    conversation_history: Optional[List[Dict[str, str]]] = []

class ChatResponse(BaseModel):
    response: str
    tool_calls: Optional[List[str]] = []
    data_used: Optional[Dict[str, Any]] = {}

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "Nunno Finance API",
        "version": "1.0.0"
    }

@app.get("/api/v1/technical/{ticker}")
async def get_technical_analysis(ticker: str, interval: str = "15m"):
    """
    Get technical analysis for a cryptocurrency
    
    Args:
        ticker: Trading pair (e.g., BTCUSDT)
        interval: Timeframe (e.g., 15m, 1h, 4h, 1d)
    
    Returns:
        Technical analysis with beginner-friendly explanations
    """
    try:
        result = technical_service.analyze(ticker, interval)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/tokenomics/{coin_id}")
async def get_tokenomics(coin_id: str, investment_amount: float = 1000):
    """
    Get comprehensive tokenomics analysis
    
    Args:
        coin_id: CoinGecko coin ID (e.g., bitcoin, ethereum)
        investment_amount: Investment amount for calculations
    
    Returns:
        Tokenomics data with beginner explanations
    """
    try:
        result = tokenomics_service.analyze(coin_id, investment_amount)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/news/{ticker}")
async def get_news(ticker: str):
    """
    Get market news and sentiment
    
    Args:
        ticker: Cryptocurrency ticker
    
    Returns:
        News and sentiment analysis
    """
    try:
        result = news_service.get_news_sentiment(ticker)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/price-history/{ticker}")
async def get_price_history(ticker: str, timeframe: str = "24H"):
    """
    Get price history for charts with selectable timeframe
    Timeframes: 24H (default), 7D, 30D, 1Y
    """
    try:
        # Use existing technical service to fetch data
        if not technical_service:
            raise HTTPException(status_code=503, detail="Technical service unavailable")
            
        # Map timeframe to Binance interval and limit
        # Binance max limit is usually 1000. We want a decent resolution.
        timeframe_map = {
            "24H": {"interval": "15m", "limit": 96},   # 96 * 15m = 24 hours
            "7D":  {"interval": "1h",  "limit": 168},  # 168 * 1h = 7 days
            "30D": {"interval": "4h",  "limit": 180},  # 180 * 4h = 30 days
            "1Y":  {"interval": "1d",  "limit": 365}   # 365 * 1d = 1 year
        }
        
        config = timeframe_map.get(timeframe, timeframe_map["24H"])
        
        df = technical_service.analyzer.fetch_binance_ohlcv_with_fallback(
            symbol=ticker, 
            interval=config["interval"], 
            limit=config["limit"]
        )
        
        # Format for recharts [ { time: '...', price: 123 } ]
        history = []
        for index, row in df.iterrows():
            # Format time label based on timeframe
            if timeframe == "24H":
                time_label = index.strftime("%H:%M")
            elif timeframe == "7D":
                time_label = index.strftime("%a %H:%M")
            elif timeframe == "30D":
                time_label = index.strftime("%b %d")
            else: # 1Y
                time_label = index.strftime("%b %d %Y")

            history.append({
                "time": time_label,
                "price": float(row['Close']),
                "date": index.isoformat() # Full ISO date for tooltips
            })
            
        # Calculate percent change
        if len(df) > 0:
            current_price = float(df.iloc[-1]['Close'])
            open_price = float(df.iloc[0]['Close']) 
            percent_change = ((current_price - open_price) / open_price) * 100
            
            # Additional stats
            high_price = float(df['High'].max())
            low_price = float(df['Low'].min())
        else:
            current_price = 0
            percent_change = 0
            high_price = 0
            low_price = 0

        return {
            "ticker": ticker,
            "current_price": current_price,
            "percent_change": percent_change,
            "high_price": high_price,
            "low_price": low_price,
            "history": history,
            "timeframe": timeframe
        }
    except Exception as e:
        print(f"Error fetching price history: {e}")
        # Return mock data on failure to prevent UI crash
        import random
        points = 20
        mock_history = [{"time": str(i), "price": 50000 + random.randint(-1000, 1000)} for i in range(points)]
        return {
            "ticker": ticker,
            "current_price": 50000,
            "percent_change": 2.5,
            "high_price": 52000,
            "low_price": 48000,
            "history": mock_history,
            "is_mock": True
        }

@app.post("/api/v1/chat")
async def chat(request: ChatRequest):
    """
    Chat with Nunno AI - The Empathetic Financial Educator
    
    This endpoint orchestrates tool calls and provides beginner-friendly responses
    """
    if not chat_service:
        raise HTTPException(status_code=503, detail="Chat service unavailable (initialization failed)")
    try:
        response = await chat_service.process_message(
            message=request.message,
            user_name=request.user_name,
            user_age=request.user_age,
            conversation_history=request.conversation_history
        )
        return response
    except Exception as e:
        print(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint for real-time responses
    """
    if not chat_service:
        raise HTTPException(status_code=503, detail="Chat service unavailable")
    try:
        return StreamingResponse(
            chat_service.stream_message(
                message=request.message,
                user_name=request.user_name,
                user_age=request.user_age,
                conversation_history=request.conversation_history
            ),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Use import string for reload to work correctly and avoid warnings
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
