"""
Chat Service with OpenRouter Integration
Orchestrates Claude Opus 4.5 with tool calling
"""

import os
import json
import requests
from typing import List, Dict, Optional, AsyncGenerator
import asyncio
from openai import AsyncOpenAI

class ChatService:
    """
    Chat orchestration service using Claude Opus 4.5 via OpenRouter
    Implements the "Empathetic Expert" persona with automatic beginner notes
    """
    
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.model = os.getenv("AI_MODEL", "openai/gpt-4o-mini")
        self.base_url = "https://openrouter.ai/api/v1"
        
        # Initialize OpenAI Async Client for OpenRouter
        self.client = AsyncOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )
        
        # Import services for tool calling
        from services.technical_analysis import TechnicalAnalysisService
        from services.tokenomics_service import TokenomicsService
        from services.news_service import NewsService
        from services.web_research_service import WebResearchService
        
        self.technical_service = TechnicalAnalysisService()
        self.tokenomics_service = TokenomicsService()
        self.news_service = NewsService()
        self.web_research_service = WebResearchService()
    
    def _get_system_prompt(self, user_name: str, user_age: int) -> str:
        """Condensed system prompt for token efficiency"""
        return f"""You are Nunno, an empathetic financial educator for beginners.
Rules:
- Explain jargon in parentheses: e.g. "RSI at 70 (RSI is a market thermometer - 70 means overbought)".
- Persona: {user_name}, Age {user_age}. Helpful, use analogies, be concise (2-3 paragraphs).
- Output: Use headings, bullets, emojis. No financial advice, just education.
- Founder: Mujtaba Kazmi."""
    
    async def process_message(
        self,
        message: str,
        user_name: str = "User",
        user_age: int = 18,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict:
        """
        Process a chat message with tool calling orchestration (Non-streaming)
        """
        if not self.api_key:
            return {
                "response": "⚠️ OpenRouter API key not configured. Please add OPENROUTER_API_KEY to your .env file.",
                "tool_calls": [],
                "data_used": {}
            }
        
        # Build messages
        messages = [{"role": "system", "content": self._get_system_prompt(user_name, user_age)}]
        
        if conversation_history:
            messages.extend(conversation_history[-2:]) # Aggressive history trimming
        
        messages.append({"role": "user", "content": message})
        
        # Detect tools
        tools_to_call = self._classify_intent_and_extract_entities(message)
        tool_data = {}
        
        # Execute tool calls
        if tools_to_call:
            for tool_name, params in tools_to_call:
                if tool_name == "technical_analysis":
                    tool_data["technical"] = self.technical_service.analyze(params["ticker"], params.get("interval", "15m"))
                elif tool_name == "tokenomics":
                    coin_id = params["coin_id"].lower()
                    tool_data["tokenomics"] = self.tokenomics_service.analyze(coin_id, params.get("amount", 1000))
                elif tool_name == "news":
                    tool_data["news"] = self.news_service.get_news_sentiment(params["ticker"])
                elif tool_name == "web_research":
                    if "url" in params:
                        tool_data["web_research"] = self.web_research_service.scrape_url(params["url"])
                    else:
                        tool_data["web_research"] = self.web_research_service.search_web(params["query"])
            
            tool_context = self._format_tool_context(tool_data)
            messages.append({
                "role": "user",
                "content": f"Here's the data from my analysis tools:\n\n{tool_context}\n\nPlease synthesize this information and explain it in beginner-friendly terms. Remember to add Beginner's Notes for all technical terms!"
            })
        
        # Call OpenRouter via OpenAI SDK
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=2000,
                temperature=0.7,
                extra_headers={
                    "HTTP-Referer": "https://nunno.finance",
                    "X-Title": "Nunno Finance"
                }
            )
            
            ai_response = response.choices[0].message.content
            
            return {
                "response": ai_response,
                "tool_calls": [tool[0] for tool in tools_to_call] if tools_to_call else [],
                "data_used": tool_data
            }
            
        except Exception as e:
            return {
                "response": f"I'm having trouble connecting to my brain right now. Error: {str(e)}",
                "tool_calls": [],
                "data_used": {}
            }
    
    async def stream_message(
        self,
        message: str,
        user_name: str = "User",
        user_age: int = 18,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat responses for real-time display using AsyncOpenAI
        """
        if not self.api_key:
            yield f"data: {json.dumps({'response': '⚠️ OpenRouter API key not configured.'})}\n\n"
            return
            
        # 1. Detect and run tools
        print(f"[CHAT] Classifying intent for: {message[:50]}...")
        tools_to_call = self._classify_intent_and_extract_entities(message)
        print(f"[CHAT] Tools detected: {tools_to_call}")
        tool_data = {}
        
        # 2. Yield status and run tools
        if tools_to_call:
            for tool_name, params in tools_to_call:
                try:
                    if tool_name == "technical_analysis":
                        yield f"data: {json.dumps({'type': 'status', 'content': f'📊 Analyzing chart for {params.get("ticker", "market")}...'})}\n\n"
                        tool_data["technical"] = self.technical_service.analyze(params["ticker"])
                    elif tool_name == "tokenomics":
                        coin_id = params.get("coin_id", "").lower()
                        yield f"data: {json.dumps({'type': 'status', 'content': f'🪙 Checking tokenomics for {coin_id}...'})}\n\n"
                        tool_data["tokenomics"] = self.tokenomics_service.analyze(coin_id)
                    elif tool_name == "news":
                        yield f"data: {json.dumps({'type': 'status', 'content': f'📰 Reading news for {params.get("ticker", "market")}...'})}\n\n"
                        tool_data["news"] = self.news_service.get_news_sentiment(params["ticker"])
                    elif tool_name == "web_research":
                        if "url" in params:
                            yield f"data: {json.dumps({'type': 'status', 'content': '🔗 Reading website content...'})}\n\n"
                            tool_data["web_research"] = self.web_research_service.scrape_url(params["url"])
                        else:
                            yield f"data: {json.dumps({'type': 'status', 'content': f'🔍 Searching the web for \"{params.get("query", "info")}\"...'})}\n\n"
                            tool_data["web_research"] = self.web_research_service.search_web(params["query"])
                except Exception as e:
                    print(f"Tool error: {e}")
            
            # Send tool data
            yield f"data: {json.dumps({'type': 'data', 'tool_calls': [t[0] for t in tools_to_call], 'data_used': tool_data})}\n\n"

        # 3. Build messages
        messages = [{"role": "system", "content": self._get_system_prompt(user_name, user_age)}]
        if conversation_history:
            messages.extend(conversation_history[-2:]) # Aggressive history trimming
        
        if tool_data:
            tool_context = self._format_tool_context(tool_data)
            messages.append({"role": "user", "content": message})
            messages.append({
                "role": "user", 
                "content": f"Here is the data found:\n\n{tool_context}\n\nPlease explain this simply with tables and beginner notes."
            })
        else:
            messages.append({"role": "user", "content": message})

        # 3. Stream from OpenRouter using AsyncOpenAI
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=1500,
                temperature=0.7,
                stream=True,
                extra_headers={
                    "HTTP-Referer": "https://nunno.finance",
                    "X-Title": "Nunno Finance"
                }
            )
            
            async for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield f"data: {json.dumps({'type': 'text', 'content': content})}\n\n"
                                
        except Exception as e:
            error_msg = str(e)
            if "402" in error_msg:
                error_msg = "⚠️ Your OpenRouter account balance is too low for this request. Please top up at https://openrouter.ai/settings/credits or try a shorter message."
            elif "401" in error_msg:
                error_msg = "🔑 Invalid API Key. Please check your OPENROUTER_API_KEY in the .env file and ensure it is correct."
            yield f"data: {json.dumps({'type': 'error', 'content': error_msg})}\n\n"
    
    def _classify_intent_and_extract_entities(self, message: str) -> List[tuple]:
        """
        Use keyword detection first, then LLM if needed for tool calling
        This saves API credits by avoiding unnecessary calls for simple chat
        """
        # First, try keyword-based detection (FREE!)
        fallback_tools = self._detect_tools_needed_fallback(message)
        
        # Check if LLM is needed
        needs_llm = any(tool[0] == "_needs_llm" for tool in fallback_tools)
        has_tools = any(tool[0] != "_needs_llm" for tool in fallback_tools)
        
        # If keyword detection found tools OR detected intent keywords, use LLM to refine
        # If no tools and no intent found by keywords, skip API call entirely (it's just chat)
        if not fallback_tools:
            print("[INTENT] No tools needed, skipping API call")
            return []
        
        if has_tools and not needs_llm:
            print(f"[INTENT] Keywords successfully extracted tools: {fallback_tools}")
            return fallback_tools
        
        print(f"[INTENT] LLM refinement needed for message...")
        
        try:
            # Reduced ticker map for credit efficiency
            ticker_map_str = "BTC: BTCUSDT, ETH: ETHUSDT, SOL: SOLUSDT, BNB: BNBUSDT, ADA: ADAUSDT, MATIC: MATICUSDT"
            
            system_prompt = f"""You are an intent classification system for a crypto AI.
            Your job is to map user queries to tool calls.
            
            Available Tools:
            1. technical_analysis(ticker): For price predictions, chart analysis, buy/sell signals, outlook.
            2. tokenomics(coin_id): For fundamental analysis, supply, market cap, utility, "what is X?".
            3. news(ticker): For market sentiment, "what's happening?", "why is it moving?".
            4. web_research(query): For general questions, "who is X?", "latest news on Y", non-crypto topics.
            5. web_research(url): For "read this link", "summarize this article".
            
            Rules:
            - Extract tickers (e.g., "BTC" -> "BTCUSDT") and coin_ids (e.g., "Bitcoin" -> "bitcoin").
            - Use the comprehensive ticker map: {ticker_map_str}
            - For coins not in the map, construct ticker as: COINUSDT (e.g., "XYZ" -> "XYZUSDT")
            - For coin_ids, use lowercase full name (e.g., "Cardano" -> "cardano", "Polygon" -> "polygon")
            - Return JSON ONLY: {{"tools": [{{"name": "tool_name", "params": {{...}}}}]}}
            - If no tool needed (general chat), return {{"tools": []}}
            - Support multiple name formats: full name, ticker, common abbreviations
            
            Examples:
            - "Predict Cardano" -> {{"tools": [{{"name": "technical_analysis", "params": {{"ticker": "ADAUSDT"}}}}]}}
            - "What is Polygon?" -> {{"tools": [{{"name": "tokenomics", "params": {{"coin_id": "polygon"}}}}]}}
            - "AVAX price prediction" -> {{"tools": [{{"name": "technical_analysis", "params": {{"ticker": "AVAXUSDT"}}}}]}}
            - "Should I buy PEPE?" -> {{"tools": [{{"name": "technical_analysis", "params": {{"ticker": "PEPEUSDT"}}}}, {{"name": "news", "params": {{"ticker": "PEPEUSDT"}}}}]}}
            """
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://nunno.finance",
                "X-Title": "Nunno Finance Intent"
            }
            
            payload = {
                "model": "openai/gpt-4o-mini", # Fast model for routing
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                "temperature": 0.0,
                "max_tokens": 30,  # Reduced from 50
                "response_format": {"type": "json_object"}
            }
            
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=5)
            if response.status_code != 200:
                print(f"Intent detection failed: {response.text}")
                # Return keyword results, filtering out the marker
                return [t for t in fallback_tools if t[0] != "_needs_llm"]
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            tool_plan = json.loads(content)
            
            tools = []
            for tool in tool_plan.get("tools", []):
                tools.append((tool["name"], tool["params"]))
            
            # If LLM didn't find tools but keywords did, use keyword results (excluding marker)
            if not tools and has_tools:
                return [t for t in fallback_tools if t[0] != "_needs_llm"]
            
            return tools

        except Exception as e:
            print(f"Intent routing error: {e}")
            # Return keyword results, filtering out the marker
            return [t for t in fallback_tools if t[0] != "_needs_llm"]

    def _detect_tools_needed_fallback(self, message: str) -> List[tuple]:
        """Legacy keyword-based detection as fallback"""
        message_lower = message.lower()
        tools = []
        
        # Check if this message likely needs analysis tools (even if we can't extract the coin)
        has_prediction_intent = any(w in message_lower for w in [
            "price", "chart", "predict", "prediction", "analysis", "analyze", 
            "outlook", "should i", "buy", "sell", "forecast", "trend"
        ])
        has_tokenomics_intent = any(w in message_lower for w in [
            "tokenomics", "supply", "market cap", "what is", "tell me about"
        ])
        has_news_intent = any(w in message_lower for w in [
            "news", "sentiment", "what's happening", "why is it moving"
        ])
        
        # Comprehensive fallback ticker mapping (100+ coins)
        common_tickers = {
            # Top Market Cap
            "bitcoin": "BTCUSDT", "btc": "BTCUSDT",
            "ethereum": "ETHUSDT", "eth": "ETHUSDT",
            "solana": "SOLUSDT", "sol": "SOLUSDT",
            "binance": "BNBUSDT", "bnb": "BNBUSDT",
            "ripple": "XRPUSDT", "xrp": "XRPUSDT",
            "cardano": "ADAUSDT", "ada": "ADAUSDT",
            "avalanche": "AVAXUSDT", "avax": "AVAXUSDT",
            "dogecoin": "DOGEUSDT", "doge": "DOGEUSDT",
            "polkadot": "DOTUSDT", "dot": "DOTUSDT",
            "polygon": "MATICUSDT", "matic": "MATICUSDT",
            "shiba": "SHIBUSDT", "shib": "SHIBUSDT", "shiba inu": "SHIBUSDT",
            "tron": "TRXUSDT", "trx": "TRXUSDT",
            "chainlink": "LINKUSDT", "link": "LINKUSDT",
            "uniswap": "UNIUSDT", "uni": "UNIUSDT",
            "cosmos": "ATOMUSDT", "atom": "ATOMUSDT",
            "litecoin": "LTCUSDT", "ltc": "LTCUSDT",
            "ethereum classic": "ETCUSDT", "etc": "ETCUSDT",
            "stellar": "XLMUSDT", "xlm": "XLMUSDT",
            "near": "NEARUSDT", "near protocol": "NEARUSDT",
            "aptos": "APTUSDT", "apt": "APTUSDT",
            "arbitrum": "ARBUSDT", "arb": "ARBUSDT",
            "optimism": "OPUSDT", "op": "OPUSDT",
            "filecoin": "FILUSDT", "fil": "FILUSDT",
            "hedera": "HBARUSDT", "hbar": "HBARUSDT",
            "vechain": "VETUSDT", "vet": "VETUSDT",
            "algorand": "ALGOUSDT", "algo": "ALGOUSDT",
            "internet computer": "ICPUSDT", "icp": "ICPUSDT",
            
            # DeFi Tokens
            "aave": "AAVEUSDT",
            "curve": "CRVUSDT", "crv": "CRVUSDT",
            "maker": "MKRUSDT", "mkr": "MKRUSDT",
            "sushiswap": "SUSHIUSDT", "sushi": "SUSHIUSDT",
            "compound": "COMPUSDT", "comp": "COMPUSDT",
            "synthetix": "SNXUSDT", "snx": "SNXUSDT",
            "graph": "GRTUSDT", "grt": "GRTUSDT", "the graph": "GRTUSDT",
            "yearn": "YFIUSDT", "yfi": "YFIUSDT", "yearn finance": "YFIUSDT",
            "1inch": "1INCHUSDT",
            "loopring": "LRCUSDT", "lrc": "LRCUSDT",
            "thorchain": "RUNEUSDT", "rune": "RUNEUSDT",
            "lido": "LDOUSDT", "ldo": "LDOUSDT",
            "rocket pool": "RPLUSDT", "rpl": "RPLUSDT",
            "gmx": "GMXUSDT",
            "radiant": "RDNTUSDT", "rdnt": "RDNTUSDT",
            "pendle": "PENDLEUSDT",
            "dydx": "DYDXUSDT",
            
            # Gaming & Metaverse
            "sandbox": "SANDUSDT", "sand": "SANDUSDT", "the sandbox": "SANDUSDT",
            "decentraland": "MANAUSDT", "mana": "MANAUSDT",
            "axie": "AXSUSDT", "axs": "AXSUSDT", "axie infinity": "AXSUSDT",
            "enjin": "ENJUSDT", "enj": "ENJUSDT",
            "gala": "GALAUSDT", "gala games": "GALAUSDT",
            "immutable": "IMXUSDT", "imx": "IMXUSDT",
            "magic": "MAGICUSDT", "treasure": "MAGICUSDT",
            "apecoin": "APEUSDT", "ape": "APEUSDT",
            "stepn": "GMTUSDT", "gmt": "GMTUSDT",
            "illuvium": "ILVUSDT", "ilv": "ILVUSDT",
            "alien worlds": "TLMUSDT", "tlm": "TLMUSDT",
            "smooth love potion": "SLPUSDT", "slp": "SLPUSDT",
            "myneighboralice": "ALICEUSDT", "alice": "ALICEUSDT",
            
            # Meme Coins
            "pepe": "PEPEUSDT",
            "floki": "FLOKIUSDT", "floki inu": "FLOKIUSDT",
            "bonk": "BONKUSDT",
            "dogwifhat": "WIFUSDT", "wif": "WIFUSDT",
            "book of meme": "BOMEUSDT", "bome": "BOMEUSDT",
            "memecoin": "MEMEUSDT", "meme": "MEMEUSDT",
            
            # Layer 2 & Scaling
            "starknet": "STRKUSDT", "strk": "STRKUSDT",
            "blur": "BLURUSDT",
            "jito": "JTOUSDT", "jto": "JTOUSDT",
            "jupiter": "JUPUSDT", "jup": "JUPUSDT",
            
            # AI & Data
            "fetch.ai": "FETUSDT", "fet": "FETUSDT", "fetch": "FETUSDT",
            "singularitynet": "AGIXUSDT", "agix": "AGIXUSDT",
            "ocean": "OCEANUSDT", "ocean protocol": "OCEANUSDT",
            "render": "RNDRUSDT", "rndr": "RNDRUSDT", "render token": "RENDERUSDT",
            "worldcoin": "WLDUSDT", "wld": "WLDUSDT",
            "pyth": "PYTHUSDT", "pyth network": "PYTHUSDT",
            
            # Infrastructure
            "fantom": "FTMUSDT", "ftm": "FTMUSDT",
            "harmony": "ONEUSDT", "one": "ONEUSDT",
            "elrond": "EGLDUSDT", "egld": "EGLDUSDT", "multiversx": "EGLDUSDT",
            "theta": "THETAUSDT", "theta network": "THETAUSDT",
            "tezos": "XTZUSDT", "xtz": "TEZOSUSDT",
            "eos": "EOSUSDT",
            "flow": "FLOWUSDT",
            "injective": "INJUSDT", "inj": "INJUSDT",
            "sui": "SUIUSDT",
            "sei": "SEIUSDT",
            "celestia": "TIAUSDT", "tia": "TIAUSDT",
            "stacks": "STXUSDT", "stx": "STXUSDT",
            "kaspa": "KASUSDT", "kas": "KASUSDT",
            "arweave": "ARUSDT", "ar": "ARUSDT",
            "storj": "STORJUSDT",
            "klaytn": "KLAYUSDT", "klay": "KLAYUSDT",
            "mina": "MINAUSDT", "mina protocol": "MINAUSDT",
            "conflux": "CFXUSDT", "cfx": "CFXUSDT",
            "celo": "CELOUSDT",
            "oasis": "ROSEUSDT", "rose": "ROSEUSDT",
            
            # Privacy Coins
            "zcash": "ZECUSDT", "zec": "ZECUSDT",
            "dash": "DASHUSDT",
            "monero": "XMRUSDT", "xmr": "XMRUSDT",
            
            # Other Notable
            "waves": "WAVESUSDT",
            "neo": "NEOUSDT",
            "kava": "KAVAUSDT",
            "zilliqa": "ZILUSDT", "zil": "ZILUSDT",
            "qtum": "QTUMUSDT",
            "basic attention": "BATUSDT", "bat": "BATUSDT",
            "0x": "ZRXUSDT", "zrx": "ZRXUSDT",
            "omg": "OMGUSDT", "omg network": "OMGUSDT",
            "terra": "LUNAUSDT", "luna": "LUNAUSDT",
            "luna classic": "LUNCUSDT", "lunc": "LUNCUSDT",
            "chiliz": "CHZUSDT", "chz": "CHZUSDT",
            "ens": "ENSUSDT", "ens domains": "ENSUSDT",
            "ssv": "SSVUSDT", "ssv network": "SSVUSDT",
            "looksrare": "LOOKSUSDT", "looks": "LOOKSUSDT",
            "woo": "WOOUSDT", "woo network": "WOOUSDT",
            "jasmycoin": "JASMYUSDT", "jasmy": "JASMYUSDT",
            "mask": "MASKUSDT", "mask network": "MASKUSDT",
            "perpetual": "PERPUSDT", "perp": "PERPUSDT",
        }
        
        # Try to extract coin for predictions
        if has_prediction_intent:
             for name, ticker in common_tickers.items():
                if name in message_lower:
                    tools.append(("technical_analysis", {"ticker": ticker}))
                    break
        
        # Try to extract coin for tokenomics
        if has_tokenomics_intent:
             # CoinGecko ID mapping for tokenomics
             coingecko_map = {
                 "bitcoin": "bitcoin", "btc": "bitcoin", "ethereum": "ethereum", "eth": "ethereum",
                 "solana": "solana", "sol": "solana", "binance": "binancecoin", "bnb": "binancecoin",
                 "ripple": "ripple", "xrp": "ripple", "cardano": "cardano", "ada": "cardano",
                 "avalanche": "avalanche-2", "avax": "avalanche-2", "dogecoin": "dogecoin", "doge": "dogecoin",
                 "polkadot": "polkadot", "dot": "polkadot", "polygon": "matic-network", "matic": "matic-network",
                 "shiba": "shiba-inu", "shib": "shiba-inu", "shiba inu": "shiba-inu",
                 "tron": "tron", "trx": "tron", "chainlink": "chainlink", "link": "chainlink",
                 "uniswap": "uniswap", "uni": "uniswap", "cosmos": "cosmos", "atom": "cosmos",
                 "litecoin": "litecoin", "ltc": "litecoin", "ethereum classic": "ethereum-classic", "etc": "ethereum-classic",
                 "stellar": "stellar", "xlm": "stellar", "near": "near", "near protocol": "near",
                 "aptos": "aptos", "apt": "aptos", "arbitrum": "arbitrum", "arb": "arbitrum",
                 "optimism": "optimism", "op": "optimism", "filecoin": "filecoin", "fil": "filecoin",
                 "hedera": "hedera-hashgraph", "hbar": "hedera-hashgraph", "vechain": "vechain", "vet": "vechain",
                 "algorand": "algorand", "algo": "algorand", "internet computer": "internet-computer", "icp": "internet-computer",
                 "aave": "aave", "curve": "curve-dao-token", "crv": "curve-dao-token",
                 "maker": "maker", "mkr": "maker", "sushiswap": "sushi", "sushi": "sushi",
                 "compound": "compound-governance-token", "comp": "compound-governance-token",
                 "synthetix": "havven", "snx": "havven", "graph": "the-graph", "grt": "the-graph", "the graph": "the-graph",
                 "yearn": "yearn-finance", "yfi": "yearn-finance", "1inch": "1inch",
                 "loopring": "loopring", "lrc": "loopring", "thorchain": "thorchain", "rune": "thorchain",
                 "lido": "lido-dao", "ldo": "lido-dao", "rocket pool": "rocket-pool", "rpl": "rocket-pool",
                 "gmx": "gmx", "radiant": "radiant-capital", "rdnt": "radiant-capital",
                 "pendle": "pendle", "dydx": "dydx",
                 "sandbox": "the-sandbox", "sand": "the-sandbox", "the sandbox": "the-sandbox",
                 "decentraland": "decentraland", "mana": "decentraland",
                 "axie": "axie-infinity", "axs": "axie-infinity", "axie infinity": "axie-infinity",
                 "enjin": "enjincoin", "enj": "enjincoin", "gala": "gala", "gala games": "gala",
                 "immutable": "immutable-x", "imx": "immutable-x", "magic": "magic",
                 "apecoin": "apecoin", "ape": "apecoin", "stepn": "stepn", "gmt": "stepn",
                 "illuvium": "illuvium", "ilv": "illuvium", "alien worlds": "alien-worlds", "tlm": "alien-worlds",
                 "smooth love potion": "smooth-love-potion", "slp": "smooth-love-potion",
                 "myneighboralice": "my-neighbor-alice", "alice": "my-neighbor-alice",
                 "pepe": "pepe", "floki": "floki", "floki inu": "floki", "bonk": "bonk",
                 "dogwifhat": "dogwifcoin", "wif": "dogwifcoin", "book of meme": "book-of-meme", "bome": "book-of-meme",
                 "memecoin": "memecoin", "meme": "memecoin", "starknet": "starknet", "strk": "starknet",
                 "blur": "blur", "jito": "jito-governance-token", "jto": "jito-governance-token",
                 "jupiter": "jupiter-exchange-solana", "jup": "jupiter-exchange-solana",
                 "fetch.ai": "fetch-ai", "fet": "fetch-ai", "fetch": "fetch-ai",
                 "singularitynet": "singularitynet", "agix": "singularitynet",
                 "ocean": "ocean-protocol", "ocean protocol": "ocean-protocol",
                 "render": "render-token", "rndr": "render-token", "worldcoin": "worldcoin-wld", "wld": "worldcoin-wld",
                 "pyth": "pyth-network", "fantom": "fantom", "ftm": "fantom",
                 "harmony": "harmony", "one": "harmony", "elrond": "elrond-erd-2", "egld": "elrond-erd-2", "multiversx": "elrond-erd-2",
                 "theta": "theta-token", "tezos": "tezos", "xtz": "tezos", "eos": "eos", "flow": "flow",
                 "injective": "injective-protocol", "inj": "injective-protocol", "sui": "sui", "sei": "sei-network",
                 "celestia": "celestia", "tia": "celestia", "stacks": "blockstack", "stx": "blockstack",
                 "kaspa": "kaspa", "kas": "kaspa", "arweave": "arweave", "ar": "arweave", "storj": "storj",
                 "klaytn": "klay-token", "klay": "klay-token", "mina": "mina-protocol",
                 "conflux": "conflux-token", "cfx": "conflux-token", "celo": "celo",
                 "oasis": "oasis-network", "rose": "oasis-network", "zcash": "zcash", "zec": "zcash",
                 "dash": "dash", "monero": "monero", "xmr": "monero", "waves": "waves", "neo": "neo",
                 "kava": "kava", "zilliqa": "zilliqa", "zil": "zilliqa", "qtum": "qtum",
                 "basic attention": "basic-attention-token", "bat": "basic-attention-token",
                 "0x": "0x", "zrx": "0x", "omg": "omisego", "omg network": "omisego",
                 "terra": "terra-luna-2", "luna": "terra-luna-2", "luna classic": "terra-luna", "lunc": "terra-luna",
                 "chiliz": "chiliz", "chz": "chiliz", "ens": "ethereum-name-service",
                 "ssv": "ssv-network", "looksrare": "looksrare", "looks": "looksrare",
                 "woo": "woo-network", "jasmycoin": "jasmycoin", "jasmy": "jasmycoin",
                 "mask": "mask-network", "perpetual": "perpetual-protocol", "perp": "perpetual-protocol",
             }
             for name in coingecko_map:
                if name in message_lower:
                    tools.append(("tokenomics", {"coin_id": coingecko_map[name]}))
                    break
        
        # IMPORTANT: If we found intent keywords but couldn't extract the coin, 
        # add a marker to signal the LLM should be called
        if (has_prediction_intent or has_tokenomics_intent or has_news_intent) and not tools:
            tools.append(("_needs_llm", {}))  # Special marker
                    
        return tools

    def _format_tool_context(self, tool_data: Dict) -> str:
        """Minified context for token efficiency"""
        context_parts = []
        if "technical" in tool_data:
            tech = tool_data["technical"].copy()
            for k in ["explanation", "signals", "data_source", "is_synthetic"]: tech.pop(k, None)
            context_parts.append(f"TECH:{json.dumps(tech)}")
        if "tokenomics" in tool_data:
            t = tool_data["tokenomics"]
            if isinstance(t, dict):
                s = {k: t.get(v) for k, v in {"name": "Token_Name", "price": "Current_Price", "rank": "Market_Cap_Rank"}.items()}
                context_parts.append(f"TOKEN:{json.dumps(s)}")
        if "news" in tool_data:
            n = tool_data["news"].copy()
            for k in ["explanation", "beginner_notes", "headlines"]: n.pop(k, None)
            context_parts.append(f"NEWS:{json.dumps(n)}")
        if "web_research" in tool_data:
            context_parts.append(f"WEB:{json.dumps(tool_data['web_research'][:2])}")
        return "|".join(context_parts)
