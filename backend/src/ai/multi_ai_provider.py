"""
Multi-AI Provider Service
Supports multiple AI providers: OpenAI, Gemini, Claude, Groq, etc.
"""
import os
import json
from typing import Dict, List, Optional, Any
from enum import Enum
import aiohttp
import asyncio
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AIProvider(Enum):
    """Supported AI providers"""
    OPENAI = "openai"
    GEMINI = "gemini"
    CLAUDE = "claude"
    LLAMA = "llama"
    GROQ = "groq"  # Free and very fast!
    HUGGINGFACE = "huggingface"  # Free tier available


@dataclass
class AIResponse:
    """Standardized AI response"""
    provider: AIProvider
    content: str
    model: str
    tokens_used: int
    confidence: float
    metadata: Dict[str, Any]


class MultiAIProvider:
    """
    Multi-AI Provider Service
    Manages multiple AI providers and routes requests intelligently
    """
    
    def __init__(self):
        self.providers = {
            AIProvider.OPENAI: {
                "api_key": os.getenv("OPENAI_API_KEY", ""),
                "base_url": "https://api.openai.com/v1",
                "models": ["gpt-4", "gpt-3.5-turbo"],
                "enabled": bool(os.getenv("OPENAI_API_KEY"))
            },
            AIProvider.GEMINI: {
                "api_key": os.getenv("GEMINI_API_KEY", ""),
                "base_url": "https://generativelanguage.googleapis.com/v1beta",
                "models": ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-2.5-pro"],
                "enabled": bool(os.getenv("GEMINI_API_KEY"))
            },
            AIProvider.CLAUDE: {
                "api_key": os.getenv("ANTHROPIC_API_KEY", ""),
                "base_url": "https://api.anthropic.com/v1",
                "models": ["claude-3-opus", "claude-3-sonnet"],
                "enabled": bool(os.getenv("ANTHROPIC_API_KEY"))
            },
            AIProvider.GROQ: {
                "api_key": os.getenv("GROQ_API_KEY", ""),
                "base_url": "https://api.groq.com/openai/v1",
                "models": ["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "gemma2-9b-it"],
                "enabled": bool(os.getenv("GROQ_API_KEY"))
            },
            AIProvider.HUGGINGFACE: {
                "api_key": os.getenv("HUGGINGFACE_API_KEY", ""),
                "base_url": "https://router.huggingface.co/models",
                "models": ["meta-llama/Llama-3.2-3B-Instruct", "mistralai/Mistral-7B-Instruct-v0.3"],
                "enabled": bool(os.getenv("HUGGINGFACE_API_KEY"))
            }
        }
        
        # Default provider priority (free providers first!)
        self.provider_priority = [
            AIProvider.GROQ,      # FREE and FAST!
            AIProvider.HUGGINGFACE,  # FREE tier
            AIProvider.GEMINI,    # Good for analysis
            AIProvider.OPENAI,    # Reliable fallback
            AIProvider.CLAUDE     # High quality
        ]
    
    def get_available_providers(self) -> List[AIProvider]:
        """Get list of enabled providers"""
        return [
            provider for provider, config in self.providers.items()
            if config["enabled"]
        ]
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        provider: Optional[AIProvider] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> AIResponse:
        """
        Get chat completion from AI provider
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            provider: Specific provider to use (auto-select if None)
            model: Specific model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        
        Returns:
            AIResponse object
        """
        # Auto-select provider if not specified
        if provider is None:
            provider = self._select_best_provider()
        
        if not self.providers[provider]["enabled"]:
            raise ValueError(f"Provider {provider.value} is not enabled")
        
        # Route to appropriate provider
        if provider == AIProvider.OPENAI:
            return await self._openai_completion(messages, model, temperature, max_tokens)
        elif provider == AIProvider.GEMINI:
            return await self._gemini_completion(messages, model, temperature, max_tokens)
        elif provider == AIProvider.CLAUDE:
            return await self._claude_completion(messages, model, temperature, max_tokens)
        elif provider == AIProvider.GROQ:
            return await self._groq_completion(messages, model, temperature, max_tokens)
        elif provider == AIProvider.HUGGINGFACE:
            return await self._huggingface_completion(messages, model, temperature, max_tokens)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    async def analyze_market(
        self,
        market_data: Dict[str, Any],
        use_ensemble: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze market data using multiple AI providers
        
        Args:
            market_data: Market data to analyze
            use_ensemble: Use multiple providers for ensemble analysis
        
        Returns:
            Analysis results with consensus
        """
        prompt = self._create_market_analysis_prompt(market_data)
        messages = [
            {"role": "system", "content": "You are an expert crypto market analyst."},
            {"role": "user", "content": prompt}
        ]
        
        if use_ensemble:
            # Get predictions from multiple providers
            tasks = []
            for provider in self.get_available_providers()[:3]:  # Use top 3
                tasks.append(self.chat_completion(messages, provider=provider))
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine responses
            valid_responses = [r for r in responses if isinstance(r, AIResponse)]
            return self._ensemble_analysis(valid_responses)
        else:
            # Single provider analysis
            response = await self.chat_completion(messages)
            return self._parse_market_analysis(response.content)
    
    async def generate_trading_signal(
        self,
        token: str,
        timeframe: str,
        indicators: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate trading signal using AI analysis
        
        Args:
            token: Token symbol
            timeframe: Timeframe for analysis
            indicators: Technical indicators
        
        Returns:
            Trading signal with confidence
        """
        prompt = f"""
        Analyze the following trading data for {token} on {timeframe} timeframe:
        
        Indicators:
        {json.dumps(indicators, indent=2)}
        
        Provide a trading signal (BUY/SELL/HOLD) with:
        1. Signal strength (0-100)
        2. Confidence level (0-1)
        3. Key reasons
        4. Risk assessment
        5. Suggested entry/exit points
        
        Format as JSON.
        """
        
        messages = [
            {"role": "system", "content": "You are an expert crypto trading analyst."},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.chat_completion(messages, temperature=0.3)
        return self._parse_trading_signal(response.content)
    
    async def _openai_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> AIResponse:
        """OpenAI API completion"""
        config = self.providers[AIProvider.OPENAI]
        model = model or config["models"][0]
        
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {config['api_key']}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            async with session.post(
                f"{config['base_url']}/chat/completions",
                headers=headers,
                json=payload
            ) as resp:
                data = await resp.json()
                
                return AIResponse(
                    provider=AIProvider.OPENAI,
                    content=data["choices"][0]["message"]["content"],
                    model=model,
                    tokens_used=data["usage"]["total_tokens"],
                    confidence=0.9,
                    metadata={"finish_reason": data["choices"][0]["finish_reason"]}
                )
    
    async def _gemini_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> AIResponse:
        """Google Gemini API completion"""
        config = self.providers[AIProvider.GEMINI]
        model = model or "gemini-2.5-flash"  # Use 2.5 flash by default
        
        # Convert messages to Gemini format
        prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        
        async with aiohttp.ClientSession() as session:
            url = f"{config['base_url']}/models/{model}:generateContent?key={config['api_key']}"
            
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens
                }
            }
            
            async with session.post(url, json=payload) as resp:
                data = await resp.json()
                
                # Extract content from response
                content = ""
                if "candidates" in data and len(data["candidates"]) > 0:
                    candidate = data["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        parts = candidate["content"]["parts"]
                        if len(parts) > 0 and "text" in parts[0]:
                            content = parts[0]["text"]
                
                # If no content, try alternative structure
                if not content and "candidates" in data:
                    content = str(data["candidates"])
                
                return AIResponse(
                    provider=AIProvider.GEMINI,
                    content=content,
                    model=model,
                    tokens_used=data.get("usageMetadata", {}).get("totalTokenCount", 0),
                    confidence=0.88,
                    metadata={"safety_ratings": data.get("candidates", [{}])[0].get("safetyRatings", [])}
                )
    
    async def _claude_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> AIResponse:
        """Anthropic Claude API completion"""
        config = self.providers[AIProvider.CLAUDE]
        model = model or config["models"][0]
        
        async with aiohttp.ClientSession() as session:
            headers = {
                "x-api-key": config['api_key'],
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            async with session.post(
                f"{config['base_url']}/messages",
                headers=headers,
                json=payload
            ) as resp:
                data = await resp.json()
                
                return AIResponse(
                    provider=AIProvider.CLAUDE,
                    content=data["content"][0]["text"],
                    model=model,
                    tokens_used=data["usage"]["input_tokens"] + data["usage"]["output_tokens"],
                    confidence=0.92,
                    metadata={"stop_reason": data["stop_reason"]}
                )
    
    async def _groq_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> AIResponse:
        """Groq API completion (FREE and FAST!)"""
        config = self.providers[AIProvider.GROQ]
        model = model or config["models"][0]
        
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {config['api_key']}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            async with session.post(
                f"{config['base_url']}/chat/completions",
                headers=headers,
                json=payload
            ) as resp:
                data = await resp.json()
                
                return AIResponse(
                    provider=AIProvider.GROQ,
                    content=data["choices"][0]["message"]["content"],
                    model=model,
                    tokens_used=data.get("usage", {}).get("total_tokens", 0),
                    confidence=0.87,
                    metadata={"finish_reason": data["choices"][0].get("finish_reason")}
                )
    
    async def _huggingface_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> AIResponse:
        """Hugging Face API completion (FREE tier available)"""
        config = self.providers[AIProvider.HUGGINGFACE]
        model = model or config["models"][0]
        
        # Convert messages to prompt
        prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {config['api_key']}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "temperature": temperature,
                    "max_new_tokens": max_tokens,
                    "return_full_text": False
                }
            }
            
            async with session.post(
                f"{config['base_url']}/{model}",
                headers=headers,
                json=payload
            ) as resp:
                data = await resp.json()
                
                # Handle different response formats
                if isinstance(data, list) and len(data) > 0:
                    content = data[0].get("generated_text", "")
                elif isinstance(data, dict):
                    content = data.get("generated_text", data.get("text", ""))
                else:
                    content = str(data)
                
                return AIResponse(
                    provider=AIProvider.HUGGINGFACE,
                    content=content,
                    model=model,
                    tokens_used=0,  # HF doesn't always return token count
                    confidence=0.80,
                    metadata={"model": model}
                )
    
    def _select_best_provider(self) -> AIProvider:
        """Select best available provider based on priority"""
        for provider in self.provider_priority:
            if self.providers[provider]["enabled"]:
                return provider
        
        raise ValueError("No AI providers are enabled")
    
    def _create_market_analysis_prompt(self, market_data: Dict[str, Any]) -> str:
        """Create prompt for market analysis"""
        return f"""
        Analyze the following cryptocurrency market data:
        
        {json.dumps(market_data, indent=2)}
        
        Provide:
        1. Market sentiment (bullish/bearish/neutral)
        2. Key trends and patterns
        3. Risk factors
        4. Trading opportunities
        5. Price predictions (short-term and long-term)
        
        Format as JSON with clear structure.
        """
    
    def _ensemble_analysis(self, responses: List[AIResponse]) -> Dict[str, Any]:
        """Combine multiple AI responses into ensemble analysis"""
        if not responses:
            return {"error": "No valid responses"}
        
        # Extract sentiments and predictions
        sentiments = []
        predictions = []
        
        for response in responses:
            try:
                analysis = json.loads(response.content)
                sentiments.append(analysis.get("sentiment", "neutral"))
                predictions.append(analysis.get("prediction", {}))
            except:
                continue
        
        # Consensus sentiment
        sentiment_counts = {}
        for s in sentiments:
            sentiment_counts[s] = sentiment_counts.get(s, 0) + 1
        
        consensus_sentiment = max(sentiment_counts, key=sentiment_counts.get) if sentiment_counts else "neutral"
        
        return {
            "consensus_sentiment": consensus_sentiment,
            "confidence": len(responses) / 3.0,  # Normalized by max providers
            "individual_analyses": [r.content for r in responses],
            "providers_used": [r.provider.value for r in responses]
        }
    
    def _parse_market_analysis(self, content: str) -> Dict[str, Any]:
        """Parse market analysis from AI response"""
        try:
            return json.loads(content)
        except:
            return {
                "raw_analysis": content,
                "sentiment": "neutral",
                "confidence": 0.5
            }
    
    def _parse_trading_signal(self, content: str) -> Dict[str, Any]:
        """Parse trading signal from AI response"""
        try:
            return json.loads(content)
        except:
            return {
                "signal": "HOLD",
                "strength": 50,
                "confidence": 0.5,
                "raw_response": content
            }


# Global instance
multi_ai_provider = MultiAIProvider()
