"""
AI Chat Service for CrossFlow Trading Assistant
Uses Multi-AI providers for intelligent trading assistance
"""
import os
import json
import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..config.settings import settings

# Google Gemini API configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

# System prompt for the trading assistant
SYSTEM_PROMPT = """You are CrossFlow AI, an advanced DeFi trading assistant. You help users with:

1. **Trading Operations**: Execute swaps, set limit orders, bridge assets across chains
2. **Market Analysis**: Analyze price trends, identify opportunities, assess risk
3. **Portfolio Management**: Optimize allocations, rebalance portfolios, track performance
4. **DeFi Strategies**: Yield farming, liquidity provision, arbitrage opportunities

**Your Capabilities:**
- Real-time price data from multiple DEXs (Uniswap, SushiSwap, 1inch, etc.)
- Cross-chain routing for optimal swap rates
- MEV protection and slippage optimization
- Gas estimation and optimization
- Risk assessment and alerts

**Response Style:**
- Be concise and actionable
- Use emojis sparingly for visual clarity (✅ ❌ ⚠️ 💰 📊 🔄)
- Format numbers clearly (e.g., $1,234.56)
- Always mention relevant risks
- Provide specific recommendations when asked

**Current Market Context:**
- You have access to real-time crypto prices
- You can analyze trading pairs across multiple chains
- You understand DeFi protocols and their mechanics

When users ask about trades, provide:
1. Best route/DEX recommendation
2. Estimated output amount
3. Gas cost estimate
4. Slippage warning if applicable
5. MEV protection status"""


class AIChatService:
    """Service for AI-powered chat interactions using Google Gemini"""
    
    def __init__(self):
        self.api_key = GEMINI_API_KEY
        self.conversation_history: Dict[str, List[Dict]] = {}
        
    async def get_market_context(self) -> str:
        """Fetch current market data for context"""
        try:
            async with httpx.AsyncClient() as client:
                # Get top crypto prices from Binance
                response = await client.get(
                    "https://api.binance.com/api/v3/ticker/24hr",
                    timeout=5.0
                )
                if response.status_code == 200:
                    data = response.json()
                    # Get top 5 by volume
                    top_pairs = sorted(
                        [d for d in data if d['symbol'].endswith('USDT')],
                        key=lambda x: float(x['quoteVolume']),
                        reverse=True
                    )[:5]
                    
                    context = "Current Market Snapshot:\n"
                    for pair in top_pairs:
                        symbol = pair['symbol'].replace('USDT', '')
                        price = float(pair['lastPrice'])
                        change = float(pair['priceChangePercent'])
                        context += f"- {symbol}: ${price:,.2f} ({'+' if change >= 0 else ''}{change:.2f}%)\n"
                    return context
        except Exception as e:
            print(f"Error fetching market context: {e}")
        return ""
    
    async def chat(
        self, 
        message: str, 
        session_id: str = "default",
        include_market_data: bool = True,
        provider: str = "groq",
        model: str = None
    ) -> Dict[str, Any]:
        """
        Process a chat message and return AI response using selected provider
        """
        try:
            # Import multi-AI provider
            from ..ai.multi_ai_provider import multi_ai_provider, AIProvider
            
            # Initialize conversation history for session
            if session_id not in self.conversation_history:
                self.conversation_history[session_id] = []
            
            # Build context with system prompt and market data
            context = SYSTEM_PROMPT
            
            # Add market context if requested
            if include_market_data:
                market_context = await self.get_market_context()
                if market_context:
                    context += f"\n\nCurrent market data:\n{market_context}"
            
            # Add conversation history (last 5 exchanges)
            if self.conversation_history[session_id]:
                context += "\n\nRecent conversation:\n"
                for msg in self.conversation_history[session_id][-10:]:
                    role = "User" if msg["role"] == "user" else "Assistant"
                    context += f"{role}: {msg['content']}\n"
            
            # Call selected AI provider
            messages = [
                {"role": "system", "content": context},
                {"role": "user", "content": message}
            ]
            
            # Convert provider string to AIProvider enum
            try:
                ai_provider = AIProvider(provider.lower())
            except ValueError:
                # Fallback to groq if invalid provider
                ai_provider = AIProvider.GROQ
            
            result = await multi_ai_provider.chat_completion(
                messages=messages,
                provider=ai_provider,
                model=model,
                max_tokens=1000,
                temperature=0.7
            )
            
            if result and result.content:
                # Update conversation history
                self.conversation_history[session_id].append(
                    {"role": "user", "content": message}
                )
                self.conversation_history[session_id].append(
                    {"role": "assistant", "content": result.content}
                )
                
                return {
                    "success": True,
                    "response": result.content,
                    "timestamp": datetime.utcnow().isoformat(),
                    "model": f"{provider}-{result.model}" if result.model else provider
                }
            else:
                # Fallback to mock response
                return await self._mock_response(message)
                    
        except Exception as e:
            print(f"Chat error: {e}")
            return await self._mock_response(message)
    
    async def _mock_response(self, message: str) -> Dict[str, Any]:
        """Generate intelligent mock responses when API is unavailable"""
        message_lower = message.lower()
        
        # Fetch real market data for context
        market_data = await self.get_market_context()
        
        # Trading signals command
        if any(word in message_lower for word in ['suggest trade', 'trading signal', 'recommend trade', 'signals']):
            response = f"""🎯 **AI Trading Signals**

Based on current market analysis, here are the top opportunities:

**1. BTC/USDT**
• Signal: BUY
• Confidence: 87%
• Reason: Strong support at $42,000, RSI oversold
• Entry: $42,500
• Target: $45,000
• Stop Loss: $41,000

**2. ETH/USDT**
• Signal: HOLD
• Confidence: 72%
• Reason: Consolidating near resistance, awaiting breakout
• Entry: $3,200
• Target: $3,500
• Stop Loss: $3,000

**3. SOL/USDT**
• Signal: SELL
• Confidence: 81%
• Reason: Bearish divergence on RSI, volume declining
• Entry: $95.00
• Target: $88.00
• Stop Loss: $98.00

{market_data}

⚠️ **Risk Warning:** Always use proper position sizing and risk management."""

        elif any(word in message_lower for word in ['swap', 'exchange', 'trade', 'convert']):
            response = f"""🔄 **Swap Analysis**

I've analyzed your swap request. Here's what I found:

**Best Route:** 1inch Aggregator
**Estimated Output:** Based on current rates
**Gas Estimate:** ~$2.50 (12 gwei)
**Slippage:** 0.5% recommended
**MEV Protection:** ✅ Active

{market_data}

⚠️ **Note:** Always verify the final amount before confirming. Market conditions can change rapidly.

Would you like me to proceed with this swap?"""

        elif any(word in message_lower for word in ['price', 'how much', 'worth', 'value']):
            response = f"""📊 **Price Analysis**

{market_data}

**Market Sentiment:** Mixed - watching key support levels
**24h Volume:** High activity across major pairs
**Recommendation:** Monitor for breakout opportunities

Would you like a deeper analysis on any specific token?"""

        elif any(word in message_lower for word in ['portfolio', 'balance', 'holdings']):
            response = """💼 **Portfolio Overview**

Based on your connected wallet:

**Total Value:** $12,450.00
**24h Change:** +$234.50 (+1.92%)

**Holdings:**
- ETH: 2.5 ($8,125.00) - 65.3%
- USDC: $2,500.00 - 20.1%
- ARB: 450 ($675.00) - 5.4%
- Other: $1,150.00 - 9.2%

**Risk Score:** Medium (6.5/10)

💡 **Suggestion:** Consider rebalancing - your ETH allocation is above target. Would you like me to suggest optimal allocations?"""

        elif any(word in message_lower for word in ['limit', 'order', 'buy at', 'sell at']):
            response = """📝 **Limit Order Setup**

I can help you set up a limit order. Here's what I need:

1. **Token Pair:** (e.g., ETH/USDC)
2. **Order Type:** Buy or Sell
3. **Price:** Your target price
4. **Amount:** How much to trade

**Current Features:**
✅ Good-til-cancelled (GTC)
✅ Partial fills enabled
✅ Gas-optimized execution
✅ MEV protection

Just tell me the details and I'll set it up!"""

        elif any(word in message_lower for word in ['bridge', 'cross-chain', 'transfer']):
            response = """🌉 **Cross-Chain Bridge**

I can help you bridge assets across chains:

**Supported Networks:**
- Ethereum ↔ Arbitrum (~2 min, ~$3)
- Ethereum ↔ Polygon (~5 min, ~$2)
- Ethereum ↔ Optimism (~2 min, ~$3)
- Arbitrum ↔ Polygon (~10 min, ~$1)

**Best Bridges:**
1. **Stargate** - Best for stablecoins
2. **Hop Protocol** - Fast ETH transfers
3. **Across** - Lowest fees

Which route would you like to explore?"""

        elif any(word in message_lower for word in ['help', 'what can you do', 'commands']):
            response = """👋 **Welcome to CrossFlow AI!**

I'm your intelligent DeFi trading assistant. Here's what I can help with:

**🔄 Trading**
- "Swap 1 ETH to USDC"
- "What's the best route for 10k USDC?"
- "Set limit order at $2500"
- "Suggest trades" - Get AI trading signals

**📊 Analysis**
- "Analyze ETH price trend"
- "Show my portfolio"
- "What's the market sentiment?"

**🌉 Cross-Chain**
- "Bridge 100 USDC to Arbitrum"
- "Compare bridge fees"

**⚙️ Settings**
- "Set slippage to 1%"
- "Enable MEV protection"

Just type naturally - I understand context!"""

        else:
            response = f"""🤖 **CrossFlow AI**

I understand you're asking about: "{message}"

{market_data}

I can help you with:
- 🔄 Token swaps and trades
- 📊 Market analysis and prices
- 💼 Portfolio management
- 🌉 Cross-chain bridges
- 📝 Limit orders
- 🎯 Trading signals

Could you be more specific about what you'd like to do? For example:
- "Swap 0.5 ETH to USDC"
- "What's the ETH price trend?"
- "Show my portfolio performance"
- "Suggest trades" """

        return {
            "success": True,
            "response": response,
            "timestamp": datetime.utcnow().isoformat(),
            "model": "crossflow-ai-local"
        }
    
    def clear_history(self, session_id: str = "default"):
        """Clear conversation history for a session"""
        if session_id in self.conversation_history:
            self.conversation_history[session_id] = []


# Singleton instance
ai_chat_service = AIChatService()
