"""
AI Configuration and Settings
"""
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class ModelType(Enum):
    """Types of ML models used in the system"""
    LSTM = "lstm"
    ARIMA = "arima"
    TRANSFORMER = "transformer"
    RANDOM_FOREST = "random_forest"
    XGBOOST = "xgboost"
    LINEAR_REGRESSION = "linear_regression"


class AgentType(Enum):
    """Types of AI agents in the system"""
    MARKET_INTELLIGENCE = "market_intelligence"
    EXECUTION_OPTIMIZER = "execution_optimizer"
    SOLVER_COORDINATOR = "solver_coordinator"
    PREDICTIVE_ANALYTICS = "predictive_analytics"
    RISK_ASSESSMENT = "risk_assessment"
    LEARNING_ENGINE = "learning_engine"
    PORTFOLIO_OPTIMIZER = "portfolio_optimizer"


@dataclass
class AIConfig:
    """Main AI configuration class"""
    
    # Environment settings
    environment: str = field(default_factory=lambda: os.getenv("AI_ENVIRONMENT", "development"))
    debug_mode: bool = field(default_factory=lambda: os.getenv("AI_DEBUG", "false").lower() == "true")
    
    # Model settings
    model_cache_dir: str = field(default_factory=lambda: os.getenv("AI_MODEL_CACHE", "./models"))
    model_version: str = "v1.0.0"
    
    # Redis settings for caching and communication
    redis_host: str = field(default_factory=lambda: os.getenv("REDIS_HOST", "localhost"))
    redis_port: int = field(default_factory=lambda: int(os.getenv("REDIS_PORT", "6379")))
    redis_db: int = field(default_factory=lambda: int(os.getenv("REDIS_DB", "0")))
    
    # MLflow settings
    mlflow_tracking_uri: str = field(default_factory=lambda: os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db"))
    mlflow_experiment_name: str = "crossflow-ai-phase2"
    
    # Performance settings
    max_concurrent_predictions: int = 100
    prediction_timeout_seconds: int = 30
    model_update_interval_hours: int = 24
    
    # Market data settings
    market_data_refresh_seconds: int = 1
    historical_data_days: int = 365
    
    # Agent communication settings
    agent_communication_timeout: int = 5
    max_message_queue_size: int = 1000
    
    # Real-time decision making
    decision_latency_target_ms: int = 100
    max_decision_queue_size: int = 500
    
    # Learning settings
    learning_rate: float = 0.001
    batch_size: int = 32
    max_epochs: int = 100
    early_stopping_patience: int = 10
    
    # Risk management
    max_portfolio_risk: float = 0.05  # 5% VaR
    risk_check_interval_seconds: int = 10
    
    # Property-based testing
    property_test_iterations: int = 100
    test_data_seed: int = 42


@dataclass
class ModelConfig:
    """Configuration for individual ML models"""
    model_type: ModelType
    model_name: str
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    training_config: Dict[str, Any] = field(default_factory=dict)
    deployment_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentConfig:
    """Configuration for individual AI agents"""
    agent_type: AgentType
    agent_name: str
    models: Dict[str, ModelConfig] = field(default_factory=dict)
    communication_config: Dict[str, Any] = field(default_factory=dict)
    performance_config: Dict[str, Any] = field(default_factory=dict)


# Default model configurations
DEFAULT_MODEL_CONFIGS = {
    ModelType.LSTM: ModelConfig(
        model_type=ModelType.LSTM,
        model_name="price_prediction_lstm",
        hyperparameters={
            "hidden_size": 128,
            "num_layers": 2,
            "dropout": 0.2,
            "sequence_length": 60
        },
        training_config={
            "learning_rate": 0.001,
            "batch_size": 32,
            "epochs": 100,
            "validation_split": 0.2
        }
    ),
    ModelType.TRANSFORMER: ModelConfig(
        model_type=ModelType.TRANSFORMER,
        model_name="market_analysis_transformer",
        hyperparameters={
            "d_model": 256,
            "nhead": 8,
            "num_layers": 6,
            "dropout": 0.1,
            "sequence_length": 100
        },
        training_config={
            "learning_rate": 0.0001,
            "batch_size": 16,
            "epochs": 50,
            "warmup_steps": 1000
        }
    ),
    ModelType.XGBOOST: ModelConfig(
        model_type=ModelType.XGBOOST,
        model_name="risk_assessment_xgb",
        hyperparameters={
            "n_estimators": 100,
            "max_depth": 6,
            "learning_rate": 0.1,
            "subsample": 0.8,
            "colsample_bytree": 0.8
        },
        training_config={
            "early_stopping_rounds": 10,
            "eval_metric": "rmse"
        }
    )
}

# Default agent configurations
DEFAULT_AGENT_CONFIGS = {
    AgentType.MARKET_INTELLIGENCE: AgentConfig(
        agent_type=AgentType.MARKET_INTELLIGENCE,
        agent_name="market_intelligence_engine",
        models={
            "trend_analysis": DEFAULT_MODEL_CONFIGS[ModelType.LSTM],
            "sentiment_analysis": DEFAULT_MODEL_CONFIGS[ModelType.TRANSFORMER]
        },
        communication_config={
            "max_connections": 50,
            "heartbeat_interval": 30
        },
        performance_config={
            "analysis_timeout": 5,
            "cache_ttl": 60
        }
    ),
    AgentType.PREDICTIVE_ANALYTICS: AgentConfig(
        agent_type=AgentType.PREDICTIVE_ANALYTICS,
        agent_name="predictive_analytics_system",
        models={
            "price_forecasting": DEFAULT_MODEL_CONFIGS[ModelType.LSTM],
            "volatility_prediction": DEFAULT_MODEL_CONFIGS[ModelType.TRANSFORMER]
        },
        communication_config={
            "max_connections": 30,
            "prediction_cache_size": 1000
        },
        performance_config={
            "prediction_timeout": 10,
            "model_update_frequency": 3600
        }
    ),
    AgentType.RISK_ASSESSMENT: AgentConfig(
        agent_type=AgentType.RISK_ASSESSMENT,
        agent_name="risk_assessment_module",
        models={
            "risk_calculation": DEFAULT_MODEL_CONFIGS[ModelType.XGBOOST]
        },
        communication_config={
            "max_connections": 20,
            "alert_priority": "high"
        },
        performance_config={
            "risk_check_interval": 10,
            "alert_threshold": 0.05
        }
    )
}


def get_ai_config() -> AIConfig:
    """Get the main AI configuration"""
    return AIConfig()


def get_model_config(model_type: ModelType) -> ModelConfig:
    """Get configuration for a specific model type"""
    return DEFAULT_MODEL_CONFIGS.get(model_type, ModelConfig(model_type, f"default_{model_type.value}"))


def get_agent_config(agent_type: AgentType) -> AgentConfig:
    """Get configuration for a specific agent type"""
    return DEFAULT_AGENT_CONFIGS.get(agent_type, AgentConfig(agent_type, f"default_{agent_type.value}"))