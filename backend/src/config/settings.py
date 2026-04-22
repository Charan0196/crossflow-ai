"""
Application settings and configuration
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://trading_user:password@localhost/ai_trading_platform"
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Blockchain RPCs
    ethereum_rpc: str = "https://eth-mainnet.g.alchemy.com/v2/your-api-key"
    polygon_rpc: str = "https://polygon-mainnet.g.alchemy.com/v2/your-api-key"
    arbitrum_rpc: str = "https://arb-mainnet.g.alchemy.com/v2/your-api-key"
    optimism_rpc: str = "https://opt-mainnet.g.alchemy.com/v2/your-api-key"
    bsc_rpc: str = "https://bsc-dataseed.binance.org/"
    
    # API Keys
    coingecko_api_key: Optional[str] = None
    oneinch_api_key: Optional[str] = None
    lifi_api_key: Optional[str] = None
    
    # External APIs
    oneinch_base_url: str = "https://api.1inch.dev"
    lifi_base_url: str = "https://li.quest/v1"
    coingecko_base_url: str = "https://api.coingecko.com/api/v3"
    
    # Redis (optional)
    redis_url: Optional[str] = "redis://localhost:6379"
    
    # Telegram (optional)
    telegram_bot_token: Optional[str] = None
    
    # OpenAI API (for AI Chat)
    openai_api_key: Optional[str] = None
    
    # Google Gemini API
    gemini_api_key: Optional[str] = None
    
    # Anthropic Claude API
    anthropic_api_key: Optional[str] = None
    
    # Groq API (FREE)
    groq_api_key: Optional[str] = None
    
    # HuggingFace API (FREE)
    huggingface_api_key: Optional[str] = None
    
    # AI Environment Settings
    ai_environment: str = "development"
    ai_debug: str = "false"
    ai_model_cache: str = "./models"
    mlflow_tracking_uri: str = "sqlite:///mlflow.db"
    
    class Config:
        env_file = ".env"


settings = Settings()