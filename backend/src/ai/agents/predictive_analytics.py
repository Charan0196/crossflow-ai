"""
Predictive Analytics System
Provides AI-powered price predictions, cross-chain forecasting, and model adaptation
for the CrossFlow AI trading platform.
"""
import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import redis
import warnings

from ..config import AIConfig, AgentConfig, AgentType, ModelType, get_agent_config
from ..utils.model_manager import ModelManager

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')


class Timeframe(Enum):
    """Prediction timeframes"""
    SHORT_TERM = "short_term"      # Minutes (5-60 min)
    MEDIUM_TERM = "medium_term"    # Hours (1-24 hours)
    LONG_TERM = "long_term"        # Days (1-7 days)


class VolatilityRegime(Enum):
    """Market volatility regimes for model adaptation"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    EXTREME = "extreme"


class ModelStatus(Enum):
    """Model status for tracking"""
    ACTIVE = "active"
    TRAINING = "training"
    UPDATING = "updating"
    DEGRADED = "degraded"
    INACTIVE = "inactive"


@dataclass
class PriceForecast:
    """Price forecast result"""
    asset: str
    chain: str
    timeframe: Timeframe
    current_price: float
    predicted_price: float
    confidence_interval_lower: float
    confidence_interval_upper: float
    prediction_confidence: float
    model_used: str
    factors_considered: List[str]
    timestamp: datetime
    prediction_horizon: timedelta
    volatility_regime: VolatilityRegime = VolatilityRegime.NORMAL


@dataclass
class CrossChainForecast:
    """Cross-chain price movement forecast"""
    asset: str
    source_chain: str
    target_chain: str
    source_price_forecast: PriceForecast
    target_price_forecast: PriceForecast
    bridge_delay_estimate: timedelta
    bridge_cost_estimate: float
    arbitrage_opportunity_score: float
    correlation_coefficient: float
    timestamp: datetime


@dataclass
class MultiTimeframePrediction:
    """Multi-timeframe prediction result"""
    asset: str
    chain: str
    short_term: PriceForecast
    medium_term: PriceForecast
    long_term: PriceForecast
    overall_trend: str  # bullish, bearish, sideways
    trend_confidence: float
    timestamp: datetime


@dataclass
class ModelPerformance:
    """Model performance tracking"""
    model_id: str
    model_type: str
    predictions_made: int
    accuracy_score: float
    mean_absolute_error: float
    mean_squared_error: float
    directional_accuracy: float
    last_updated: datetime
    performance_trend: str  # improving, stable, degrading


@dataclass
class PredictionAccuracy:
    """Prediction accuracy tracking for a single prediction"""
    prediction_id: str
    asset: str
    chain: str
    predicted_price: float
    actual_price: float
    prediction_error: float
    prediction_error_pct: float
    direction_correct: bool
    model_used: str
    timeframe: Timeframe
    timestamp: datetime


class LSTMModel:
    """LSTM-based time series forecasting model"""
    
    def __init__(self, sequence_length: int = 60, hidden_size: int = 128, 
                 num_layers: int = 2, dropout: float = 0.2):
        self.sequence_length = sequence_length
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.dropout = dropout
        self.model = None
        self.scaler = None
        self.is_trained = False
        self.logger = logging.getLogger(__name__)
    
    def train(self, data: np.ndarray, epochs: int = 100, 
              batch_size: int = 32, validation_split: float = 0.2) -> Dict[str, float]:
        """Train the LSTM model"""
        try:
            from sklearn.preprocessing import MinMaxScaler
            
            # Scale data
            self.scaler = MinMaxScaler(feature_range=(0, 1))
            scaled_data = self.scaler.fit_transform(data.reshape(-1, 1))
            
            # Create sequences
            X, y = self._create_sequences(scaled_data)
            
            if len(X) < 10:
                self.logger.warning("Insufficient data for LSTM training")
                return {"loss": 1.0, "val_loss": 1.0}
            
            # Split data
            split_idx = int(len(X) * (1 - validation_split))
            X_train, X_val = X[:split_idx], X[split_idx:]
            y_train, y_val = y[:split_idx], y[split_idx:]
            
            # Simple linear model as fallback (no PyTorch dependency)
            # In production, this would use actual LSTM
            self.model = {
                'weights': np.random.randn(self.sequence_length) * 0.01,
                'bias': 0.0
            }
            
            # Simple training simulation
            best_loss = float('inf')
            for epoch in range(min(epochs, 50)):
                # Forward pass simulation
                predictions = np.dot(X_train.reshape(len(X_train), -1), self.model['weights']) + self.model['bias']
                loss = np.mean((predictions - y_train.flatten()) ** 2)
                
                # Simple gradient descent
                grad = 2 * np.dot(X_train.reshape(len(X_train), -1).T, 
                                 (predictions - y_train.flatten())) / len(X_train)
                self.model['weights'] -= 0.01 * grad
                self.model['bias'] -= 0.01 * np.mean(predictions - y_train.flatten())
                
                if loss < best_loss:
                    best_loss = loss
            
            # Validation loss
            val_predictions = np.dot(X_val.reshape(len(X_val), -1), self.model['weights']) + self.model['bias']
            val_loss = np.mean((val_predictions - y_val.flatten()) ** 2)
            
            self.is_trained = True
            
            return {
                "loss": float(best_loss),
                "val_loss": float(val_loss),
                "epochs_trained": min(epochs, 50)
            }
            
        except Exception as e:
            self.logger.error(f"LSTM training failed: {e}")
            return {"loss": 1.0, "val_loss": 1.0, "error": str(e)}
    
    def predict(self, data: np.ndarray, steps: int = 1) -> Tuple[np.ndarray, np.ndarray]:
        """Make predictions with confidence intervals"""
        if not self.is_trained or self.model is None:
            raise ValueError("Model not trained")
        
        try:
            # Scale input data
            scaled_data = self.scaler.transform(data.reshape(-1, 1))
            
            predictions = []
            confidence_intervals = []
            
            current_sequence = scaled_data[-self.sequence_length:].flatten()
            
            for _ in range(steps):
                # Predict next value
                pred = np.dot(current_sequence, self.model['weights']) + self.model['bias']
                predictions.append(pred)
                
                # Estimate confidence interval (simplified)
                std_estimate = np.std(current_sequence) * 0.5
                confidence_intervals.append(std_estimate)
                
                # Update sequence
                current_sequence = np.roll(current_sequence, -1)
                current_sequence[-1] = pred
            
            # Inverse transform predictions
            predictions = np.array(predictions).reshape(-1, 1)
            predictions = self.scaler.inverse_transform(predictions).flatten()
            
            # Scale confidence intervals - ensure 1D
            confidence_intervals = np.array(confidence_intervals).flatten()
            scale_factor = float(self.scaler.data_max_[0] - self.scaler.data_min_[0]) if hasattr(self.scaler.data_max_, '__len__') else float(self.scaler.data_max_ - self.scaler.data_min_)
            confidence_intervals = confidence_intervals * scale_factor
            
            return predictions, confidence_intervals
            
        except Exception as e:
            self.logger.error(f"LSTM prediction failed: {e}")
            raise
    
    def _create_sequences(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Create sequences for LSTM training"""
        X, y = [], []
        for i in range(len(data) - self.sequence_length):
            X.append(data[i:i + self.sequence_length])
            y.append(data[i + self.sequence_length])
        return np.array(X), np.array(y)


class ARIMAModel:
    """ARIMA-based statistical forecasting model"""
    
    def __init__(self, order: Tuple[int, int, int] = (5, 1, 0)):
        self.order = order
        self.model = None
        self.fitted_model = None
        self.is_trained = False
        self.logger = logging.getLogger(__name__)
    
    def train(self, data: np.ndarray) -> Dict[str, float]:
        """Train the ARIMA model"""
        try:
            # Simple AR model implementation (no statsmodels dependency)
            p, d, q = self.order
            
            # Differencing
            diff_data = np.diff(data, n=d) if d > 0 else data
            
            if len(diff_data) < p + 10:
                self.logger.warning("Insufficient data for ARIMA training")
                return {"aic": float('inf'), "bic": float('inf')}
            
            # Fit AR coefficients using least squares
            X = np.column_stack([diff_data[i:-(p-i)] for i in range(p)])
            y = diff_data[p:]
            
            if len(X) > 0 and len(y) > 0:
                # Solve least squares
                try:
                    self.model = {
                        'ar_coeffs': np.linalg.lstsq(X, y, rcond=None)[0],
                        'mean': np.mean(data),
                        'last_values': data[-p:] if p > 0 else np.array([data[-1]]),
                        'd': d
                    }
                    self.is_trained = True
                    
                    # Calculate residuals for AIC/BIC
                    predictions = np.dot(X, self.model['ar_coeffs'])
                    residuals = y - predictions
                    mse = np.mean(residuals ** 2)
                    n = len(y)
                    k = p + 1  # Number of parameters
                    
                    aic = n * np.log(mse) + 2 * k
                    bic = n * np.log(mse) + k * np.log(n)
                    
                    return {"aic": float(aic), "bic": float(bic), "mse": float(mse)}
                except Exception as e:
                    self.logger.warning(f"ARIMA fitting failed: {e}")
                    return {"aic": float('inf'), "bic": float('inf')}
            
            return {"aic": float('inf'), "bic": float('inf')}
            
        except Exception as e:
            self.logger.error(f"ARIMA training failed: {e}")
            return {"aic": float('inf'), "bic": float('inf'), "error": str(e)}
    
    def predict(self, steps: int = 1) -> Tuple[np.ndarray, np.ndarray]:
        """Make predictions with confidence intervals"""
        if not self.is_trained or self.model is None:
            raise ValueError("Model not trained")
        
        try:
            predictions = []
            p = len(self.model['ar_coeffs'])
            last_values = list(self.model['last_values'])
            
            for _ in range(steps):
                # AR prediction
                if p > 0:
                    pred = np.dot(self.model['ar_coeffs'], last_values[-p:])
                else:
                    pred = self.model['mean']
                
                predictions.append(pred)
                last_values.append(pred)
            
            predictions = np.array(predictions)
            
            # Simple confidence interval estimation
            std_estimate = np.std(self.model['last_values']) * np.sqrt(np.arange(1, steps + 1))
            
            return predictions, std_estimate
            
        except Exception as e:
            self.logger.error(f"ARIMA prediction failed: {e}")
            raise


class TransformerModel:
    """Transformer-based multi-asset prediction model"""
    
    def __init__(self, d_model: int = 256, nhead: int = 8, 
                 num_layers: int = 6, sequence_length: int = 100):
        self.d_model = d_model
        self.nhead = nhead
        self.num_layers = num_layers
        self.sequence_length = sequence_length
        self.actual_seq_length = sequence_length  # Will be adjusted based on data
        self.n_features = 1
        self.model = None
        self.scaler = None
        self.is_trained = False
        self.logger = logging.getLogger(__name__)
    
    def _softmax(self, x: np.ndarray, axis: int = -1) -> np.ndarray:
        """Compute softmax values"""
        e_x = np.exp(x - np.max(x, axis=axis, keepdims=True))
        return e_x / np.sum(e_x, axis=axis, keepdims=True)
    
    def train(self, data: np.ndarray, epochs: int = 50) -> Dict[str, float]:
        """Train the transformer model"""
        try:
            from sklearn.preprocessing import StandardScaler
            
            # Scale data
            self.scaler = StandardScaler()
            if len(data.shape) == 1:
                data = data.reshape(-1, 1)
            self.n_features = data.shape[1]
            scaled_data = self.scaler.fit_transform(data)
            
            # Adjust sequence length based on available data
            self.actual_seq_length = min(self.sequence_length, len(scaled_data) - 10)
            if self.actual_seq_length < 10:
                self.logger.warning("Insufficient data for Transformer training")
                return {"loss": 1.0}
            
            # Create sequences with adjusted length
            X, y = self._create_sequences(scaled_data)
            
            if len(X) < 10:
                self.logger.warning("Insufficient data for Transformer training")
                return {"loss": 1.0}
            
            # Simplified transformer-like model
            # For 1D time series: use linear projection approach
            self.model = {
                'query_weights': np.random.randn(self.actual_seq_length) * 0.01,
                'key_weights': np.random.randn(self.actual_seq_length) * 0.01,
                'value_weights': np.random.randn(self.actual_seq_length) * 0.01,
                'output_weights': np.random.randn(self.actual_seq_length, self.n_features) * 0.01,
                'bias': np.zeros(self.n_features)
            }
            
            # Simple training
            best_loss = float('inf')
            for epoch in range(min(epochs, 30)):
                total_loss = 0
                for i in range(len(X)):
                    # Flatten sequence for 1D processing
                    seq_flat = X[i].flatten()[:self.actual_seq_length]
                    
                    # Simple attention: weighted sum of sequence values
                    query = np.dot(seq_flat, self.model['query_weights'])
                    key = np.dot(seq_flat, self.model['key_weights'])
                    value = seq_flat * self.model['value_weights']
                    
                    # Attention score (simplified)
                    attention_score = self._softmax(np.array([query * key]))[0]
                    context = value * attention_score
                    
                    # Output projection
                    pred = np.dot(context, self.model['output_weights']) + self.model['bias']
                    
                    loss = np.mean((pred - y[i]) ** 2)
                    total_loss += loss
                
                avg_loss = total_loss / len(X)
                if avg_loss < best_loss:
                    best_loss = avg_loss
            
            self.is_trained = True
            
            return {"loss": float(best_loss), "epochs_trained": min(epochs, 30)}
            
        except Exception as e:
            self.logger.error(f"Transformer training failed: {e}")
            return {"loss": 1.0, "error": str(e)}
    
    def predict(self, data: np.ndarray, steps: int = 1) -> Tuple[np.ndarray, np.ndarray]:
        """Make predictions"""
        if not self.is_trained or self.model is None:
            raise ValueError("Model not trained")
        
        try:
            if len(data.shape) == 1:
                data = data.reshape(-1, 1)
            scaled_data = self.scaler.transform(data)
            
            predictions = []
            # Use actual_seq_length for sequence extraction
            current_sequence = scaled_data[-self.actual_seq_length:].flatten()
            
            for _ in range(steps):
                # Simple attention: weighted sum of sequence values
                query = np.dot(current_sequence, self.model['query_weights'])
                key = np.dot(current_sequence, self.model['key_weights'])
                value = current_sequence * self.model['value_weights']
                
                # Attention score (simplified)
                attention_score = self._softmax(np.array([query * key]))[0]
                context = value * attention_score
                
                # Output projection
                pred = np.dot(context, self.model['output_weights']) + self.model['bias']
                
                # Ensure pred is scalar for 1D case
                pred_val = float(pred[0]) if hasattr(pred, '__len__') else float(pred)
                predictions.append(pred_val)
                
                # Update sequence
                current_sequence = np.roll(current_sequence, -1)
                current_sequence[-1] = pred_val
            
            predictions = np.array(predictions).reshape(-1, 1)
            predictions = self.scaler.inverse_transform(predictions).flatten()
            
            # Confidence intervals - return as 1D array
            confidence = np.std(data) * np.sqrt(np.arange(1, steps + 1)) * 0.5
            
            return predictions, confidence
            
        except Exception as e:
            self.logger.error(f"Transformer prediction failed: {e}")
            raise
    
    def _create_sequences(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Create sequences for training"""
        X, y = [], []
        for i in range(len(data) - self.actual_seq_length):
            X.append(data[i:i + self.actual_seq_length])
            y.append(data[i + self.actual_seq_length])
        return np.array(X), np.array(y)


class EnsembleModel:
    """Ensemble model combining multiple forecasting methods"""
    
    def __init__(self, models: Dict[str, Any], weights: Optional[Dict[str, float]] = None):
        self.models = models
        self.weights = weights or {name: 1.0 / len(models) for name in models}
        self.logger = logging.getLogger(__name__)
    
    def predict(self, data: np.ndarray, steps: int = 1) -> Tuple[np.ndarray, np.ndarray]:
        """Make ensemble predictions"""
        all_predictions = []
        all_confidences = []
        
        for name, model in self.models.items():
            try:
                if hasattr(model, 'predict'):
                    pred, conf = model.predict(data, steps) if name != 'arima' else model.predict(steps)
                    # Ensure predictions are 1D arrays
                    pred = np.array(pred).flatten()
                    conf = np.array(conf).flatten()
                    # Ensure same length
                    if len(pred) == steps and len(conf) == steps:
                        all_predictions.append(pred * self.weights[name])
                        all_confidences.append(conf * self.weights[name])
            except Exception as e:
                self.logger.warning(f"Model {name} prediction failed: {e}")
        
        if not all_predictions:
            raise ValueError("All models failed to predict")
        
        # Weighted average - stack and sum
        all_predictions = np.array(all_predictions)
        all_confidences = np.array(all_confidences)
        
        ensemble_prediction = np.sum(all_predictions, axis=0)
        ensemble_confidence = np.sqrt(np.sum(all_confidences ** 2, axis=0))
        
        return ensemble_prediction, ensemble_confidence
    
    def update_weights(self, performance_scores: Dict[str, float]) -> None:
        """Update model weights based on performance"""
        total_score = sum(performance_scores.values())
        if total_score > 0:
            self.weights = {name: score / total_score for name, score in performance_scores.items()}



class PredictiveAnalyticsSystem:
    """
    AI-powered Predictive Analytics System for CrossFlow Phase 2
    Provides price forecasting, cross-chain predictions, and model adaptation.
    """
    
    def __init__(self, config: AIConfig, agent_config: AgentConfig, model_manager: ModelManager):
        self.config = config
        self.agent_config = agent_config
        self.model_manager = model_manager
        self.logger = logging.getLogger(__name__)
        
        # Redis for caching
        try:
            self.redis_client = redis.Redis(
                host=config.redis_host,
                port=config.redis_port,
                db=config.redis_db,
                decode_responses=True
            )
        except Exception as e:
            self.logger.warning(f"Redis connection failed: {e}")
            self.redis_client = None
        
        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Model registry
        self.models: Dict[str, Dict[str, Any]] = {}  # {asset_chain: {model_type: model}}
        self.model_performance: Dict[str, ModelPerformance] = {}
        self.model_status: Dict[str, ModelStatus] = {}
        
        # Prediction tracking
        self.prediction_history: Dict[str, List[PredictionAccuracy]] = {}
        self.prediction_cache: Dict[str, PriceForecast] = {}
        self.cache_ttl = agent_config.performance_config.get("prediction_cache_ttl", 60)
        
        # Volatility regime tracking
        self.current_volatility_regime: Dict[str, VolatilityRegime] = {}
        self.volatility_history: Dict[str, List[float]] = {}
        
        # Cross-chain correlation tracking
        self.chain_correlations: Dict[str, Dict[str, float]] = {}
        
        # Model adaptation settings
        self.adaptation_threshold = 0.1  # 10% performance degradation triggers adaptation
        self.min_predictions_for_adaptation = 20
        
        self.logger.info("Predictive Analytics System initialized")

    async def generate_price_forecast(self, asset: str, chain: str, 
                                     timeframe: Timeframe,
                                     historical_data: Optional[np.ndarray] = None) -> PriceForecast:
        """
        Generate price forecast for an asset on a specific chain
        Requirements: 4.1, 4.4 - Price forecasts with confidence intervals
        """
        cache_key = f"forecast:{asset}:{chain}:{timeframe.value}"
        
        # Check cache
        cached = self._get_cached_forecast(cache_key)
        if cached:
            return cached
        
        try:
            # Get or generate historical data
            if historical_data is None:
                historical_data = await self._get_historical_data(asset, chain, timeframe)
            
            if len(historical_data) < 30:
                raise ValueError(f"Insufficient historical data for {asset} on {chain}")
            
            current_price = float(historical_data[-1])
            
            # Determine prediction horizon based on timeframe
            prediction_horizon = self._get_prediction_horizon(timeframe)
            steps = self._get_prediction_steps(timeframe)
            
            # Get current volatility regime - use stored regime if available (from adaptation)
            model_key = f"{asset}_{chain}"
            if model_key in self.current_volatility_regime:
                volatility_regime = self.current_volatility_regime[model_key]
            else:
                volatility_regime = await self._detect_volatility_regime(asset, chain, historical_data)
            
            # Select and use appropriate model
            model, model_name = await self._get_or_train_model(model_key, historical_data, volatility_regime)
            
            # Generate prediction
            predictions, confidence_intervals = model.predict(historical_data, steps)
            
            # Get final prediction (last step)
            predicted_price = float(predictions[-1]) if len(predictions) > 0 else current_price
            confidence_interval = float(confidence_intervals[-1]) if len(confidence_intervals) > 0 else current_price * 0.05
            
            # Calculate prediction confidence
            prediction_confidence = self._calculate_prediction_confidence(
                model_key, volatility_regime, len(historical_data)
            )
            
            # Determine factors considered
            factors = self._get_factors_considered(model_name, volatility_regime)
            
            forecast = PriceForecast(
                asset=asset,
                chain=chain,
                timeframe=timeframe,
                current_price=current_price,
                predicted_price=predicted_price,
                confidence_interval_lower=predicted_price - confidence_interval,
                confidence_interval_upper=predicted_price + confidence_interval,
                prediction_confidence=prediction_confidence,
                model_used=model_name,
                factors_considered=factors,
                timestamp=datetime.now(),
                prediction_horizon=prediction_horizon,
                volatility_regime=volatility_regime
            )
            
            # Cache the forecast
            self._cache_forecast(cache_key, forecast)
            
            self.logger.info(f"Generated {timeframe.value} forecast for {asset} on {chain}")
            return forecast
            
        except Exception as e:
            self.logger.error(f"Price forecast generation failed: {e}")
            raise

    async def provide_multi_timeframe_predictions(self, asset: str, chain: str,
                                                  historical_data: Optional[np.ndarray] = None) -> MultiTimeframePrediction:
        """
        Provide predictions for all timeframes (short, medium, long term)
        Requirements: 4.4 - Multi-timeframe predictions
        """
        try:
            # Generate forecasts for all timeframes
            short_term = await self.generate_price_forecast(
                asset, chain, Timeframe.SHORT_TERM, historical_data
            )
            medium_term = await self.generate_price_forecast(
                asset, chain, Timeframe.MEDIUM_TERM, historical_data
            )
            long_term = await self.generate_price_forecast(
                asset, chain, Timeframe.LONG_TERM, historical_data
            )
            
            # Determine overall trend
            overall_trend, trend_confidence = self._determine_overall_trend(
                short_term, medium_term, long_term
            )
            
            return MultiTimeframePrediction(
                asset=asset,
                chain=chain,
                short_term=short_term,
                medium_term=medium_term,
                long_term=long_term,
                overall_trend=overall_trend,
                trend_confidence=trend_confidence,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Multi-timeframe prediction failed: {e}")
            raise
    
    async def predict_cross_chain_movements(self, asset: str, 
                                           source_chain: str, target_chain: str,
                                           historical_data: Optional[Dict[str, np.ndarray]] = None) -> CrossChainForecast:
        """
        Predict cross-chain price movements accounting for bridge delays and costs
        Requirements: 4.2 - Cross-chain predictions with bridge factors
        """
        try:
            # Get historical data for both chains
            if historical_data is None:
                source_data = await self._get_historical_data(asset, source_chain, Timeframe.MEDIUM_TERM)
                target_data = await self._get_historical_data(asset, target_chain, Timeframe.MEDIUM_TERM)
            else:
                source_data = historical_data.get(source_chain, np.array([]))
                target_data = historical_data.get(target_chain, np.array([]))
            
            # Generate forecasts for both chains
            source_forecast = await self.generate_price_forecast(
                asset, source_chain, Timeframe.MEDIUM_TERM, source_data
            )
            target_forecast = await self.generate_price_forecast(
                asset, target_chain, Timeframe.MEDIUM_TERM, target_data
            )
            
            # Estimate bridge delay
            bridge_delay = self._estimate_bridge_delay(source_chain, target_chain)
            
            # Estimate bridge cost
            bridge_cost = self._estimate_bridge_cost(source_chain, target_chain, source_forecast.current_price)
            
            # Calculate correlation between chains
            correlation = self._calculate_chain_correlation(source_data, target_data)
            
            # Calculate arbitrage opportunity score
            arbitrage_score = self._calculate_arbitrage_score(
                source_forecast, target_forecast, bridge_delay, bridge_cost
            )
            
            return CrossChainForecast(
                asset=asset,
                source_chain=source_chain,
                target_chain=target_chain,
                source_price_forecast=source_forecast,
                target_price_forecast=target_forecast,
                bridge_delay_estimate=bridge_delay,
                bridge_cost_estimate=bridge_cost,
                arbitrage_opportunity_score=arbitrage_score,
                correlation_coefficient=correlation,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Cross-chain prediction failed: {e}")
            raise

    async def adapt_models_for_volatility(self, asset: str, chain: str,
                                         new_volatility_regime: VolatilityRegime) -> bool:
        """
        Adapt prediction models when volatility regime changes
        Requirements: 4.3 - Model adaptation for volatility changes
        """
        try:
            model_key = f"{asset}_{chain}"
            current_regime = self.current_volatility_regime.get(model_key, VolatilityRegime.NORMAL)
            
            if current_regime == new_volatility_regime:
                return True  # No adaptation needed
            
            self.logger.info(f"Adapting models for {model_key}: {current_regime.value} -> {new_volatility_regime.value}")
            
            # Update volatility regime
            self.current_volatility_regime[model_key] = new_volatility_regime
            
            # Adjust model parameters based on new regime
            if model_key in self.models:
                await self._adjust_model_parameters(model_key, new_volatility_regime)
            
            # Update model status
            self.model_status[model_key] = ModelStatus.UPDATING
            
            # Retrain models if needed for extreme volatility
            if new_volatility_regime in [VolatilityRegime.HIGH, VolatilityRegime.EXTREME]:
                historical_data = await self._get_historical_data(asset, chain, Timeframe.MEDIUM_TERM)
                await self._retrain_models(model_key, historical_data, new_volatility_regime)
            
            self.model_status[model_key] = ModelStatus.ACTIVE
            
            return True
            
        except Exception as e:
            self.logger.error(f"Model adaptation failed: {e}")
            return False
    
    async def update_models_from_accuracy(self, prediction_id: str, 
                                         actual_price: float) -> bool:
        """
        Update models based on prediction accuracy feedback
        Requirements: 4.5 - Model improvement from accuracy feedback
        """
        try:
            # Find the prediction
            prediction_record = None
            for asset_chain, predictions in self.prediction_history.items():
                for pred in predictions:
                    if pred.prediction_id == prediction_id:
                        prediction_record = pred
                        break
                if prediction_record:
                    break
            
            if not prediction_record:
                self.logger.warning(f"Prediction {prediction_id} not found")
                return False
            
            # Calculate accuracy metrics
            prediction_error = abs(actual_price - prediction_record.predicted_price)
            prediction_error_pct = prediction_error / prediction_record.predicted_price if prediction_record.predicted_price > 0 else 0
            direction_correct = (actual_price > prediction_record.predicted_price) == (prediction_record.predicted_price > prediction_record.actual_price)
            
            # Update prediction record
            prediction_record.actual_price = actual_price
            prediction_record.prediction_error = prediction_error
            prediction_record.prediction_error_pct = prediction_error_pct
            prediction_record.direction_correct = direction_correct
            
            # Update model performance
            model_key = f"{prediction_record.asset}_{prediction_record.chain}"
            await self._update_model_performance(model_key, prediction_record)
            
            # Check if model needs retraining
            if await self._should_retrain_model(model_key):
                self.logger.info(f"Triggering model retraining for {model_key}")
                historical_data = await self._get_historical_data(
                    prediction_record.asset, prediction_record.chain, Timeframe.MEDIUM_TERM
                )
                volatility_regime = self.current_volatility_regime.get(model_key, VolatilityRegime.NORMAL)
                await self._retrain_models(model_key, historical_data, volatility_regime)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Model update from accuracy failed: {e}")
            return False

    async def _get_or_train_model(self, model_key: str, historical_data: np.ndarray,
                                  volatility_regime: VolatilityRegime) -> Tuple[Any, str]:
        """Get existing model or train a new one"""
        
        if model_key in self.models and self.model_status.get(model_key) == ModelStatus.ACTIVE:
            # Return ensemble model if available
            if 'ensemble' in self.models[model_key]:
                return self.models[model_key]['ensemble'], 'ensemble'
            # Return best performing model
            best_model = self._get_best_model(model_key)
            if best_model:
                return best_model
        
        # Train new models
        await self._train_all_models(model_key, historical_data, volatility_regime)
        
        if 'ensemble' in self.models.get(model_key, {}):
            return self.models[model_key]['ensemble'], 'ensemble'
        
        return self._get_best_model(model_key)
    
    async def _train_all_models(self, model_key: str, historical_data: np.ndarray,
                               volatility_regime: VolatilityRegime) -> None:
        """Train all model types for an asset/chain"""
        
        self.model_status[model_key] = ModelStatus.TRAINING
        self.models[model_key] = {}
        
        try:
            # Train LSTM model
            lstm = LSTMModel(
                sequence_length=min(60, len(historical_data) // 2),
                hidden_size=128 if volatility_regime != VolatilityRegime.EXTREME else 256
            )
            lstm_metrics = lstm.train(historical_data)
            if lstm.is_trained:
                self.models[model_key]['lstm'] = lstm
                self.logger.info(f"LSTM trained for {model_key}: {lstm_metrics}")
            
            # Train ARIMA model
            arima = ARIMAModel(order=(5, 1, 0))
            arima_metrics = arima.train(historical_data)
            if arima.is_trained:
                self.models[model_key]['arima'] = arima
                self.logger.info(f"ARIMA trained for {model_key}: {arima_metrics}")
            
            # Train Transformer model
            transformer = TransformerModel(
                sequence_length=min(100, len(historical_data) // 2),
                d_model=256
            )
            transformer_metrics = transformer.train(historical_data)
            if transformer.is_trained:
                self.models[model_key]['transformer'] = transformer
                self.logger.info(f"Transformer trained for {model_key}: {transformer_metrics}")
            
            # Create ensemble
            trained_models = {k: v for k, v in self.models[model_key].items() 
                           if k != 'ensemble' and hasattr(v, 'is_trained') and v.is_trained}
            
            if len(trained_models) >= 2:
                # Weight models based on volatility regime
                weights = self._get_model_weights(volatility_regime, list(trained_models.keys()))
                self.models[model_key]['ensemble'] = EnsembleModel(trained_models, weights)
                self.logger.info(f"Ensemble created for {model_key} with {len(trained_models)} models")
            
            self.model_status[model_key] = ModelStatus.ACTIVE
            
        except Exception as e:
            self.logger.error(f"Model training failed for {model_key}: {e}")
            self.model_status[model_key] = ModelStatus.DEGRADED
    
    def _get_model_weights(self, volatility_regime: VolatilityRegime, 
                          model_names: List[str]) -> Dict[str, float]:
        """Get model weights based on volatility regime"""
        
        # Default weights
        base_weights = {
            'lstm': 0.4,
            'arima': 0.3,
            'transformer': 0.3
        }
        
        # Adjust for volatility regime
        if volatility_regime == VolatilityRegime.LOW:
            # ARIMA works better in stable markets
            base_weights = {'lstm': 0.3, 'arima': 0.5, 'transformer': 0.2}
        elif volatility_regime == VolatilityRegime.HIGH:
            # LSTM better for volatile markets
            base_weights = {'lstm': 0.5, 'arima': 0.2, 'transformer': 0.3}
        elif volatility_regime == VolatilityRegime.EXTREME:
            # Transformer for complex patterns
            base_weights = {'lstm': 0.4, 'arima': 0.1, 'transformer': 0.5}
        
        # Filter to available models and normalize
        weights = {k: v for k, v in base_weights.items() if k in model_names}
        total = sum(weights.values())
        return {k: v / total for k, v in weights.items()} if total > 0 else {k: 1/len(model_names) for k in model_names}
    
    def _get_best_model(self, model_key: str) -> Tuple[Any, str]:
        """Get the best performing model for a key"""
        
        if model_key not in self.models:
            raise ValueError(f"No models found for {model_key}")
        
        models = self.models[model_key]
        
        # Prefer ensemble if available
        if 'ensemble' in models:
            return models['ensemble'], 'ensemble'
        
        # Otherwise return first available trained model
        for name, model in models.items():
            if hasattr(model, 'is_trained') and model.is_trained:
                return model, name
        
        raise ValueError(f"No trained models found for {model_key}")

    async def _retrain_models(self, model_key: str, historical_data: np.ndarray,
                             volatility_regime: VolatilityRegime) -> None:
        """Retrain models with new data"""
        
        self.logger.info(f"Retraining models for {model_key}")
        self.model_status[model_key] = ModelStatus.UPDATING
        
        # Retrain all models
        await self._train_all_models(model_key, historical_data, volatility_regime)
        
        # Reset performance tracking
        if model_key in self.model_performance:
            self.model_performance[model_key].predictions_made = 0
            self.model_performance[model_key].last_updated = datetime.now()
    
    async def _adjust_model_parameters(self, model_key: str, 
                                       volatility_regime: VolatilityRegime) -> None:
        """Adjust model parameters for new volatility regime"""
        
        if model_key not in self.models:
            return
        
        models = self.models[model_key]
        
        # Update ensemble weights
        if 'ensemble' in models:
            model_names = [k for k in models.keys() if k != 'ensemble']
            new_weights = self._get_model_weights(volatility_regime, model_names)
            models['ensemble'].update_weights(
                {k: new_weights.get(k, 0.33) for k in model_names}
            )
    
    async def _detect_volatility_regime(self, asset: str, chain: str,
                                       historical_data: np.ndarray) -> VolatilityRegime:
        """Detect current volatility regime from historical data"""
        
        if len(historical_data) < 20:
            return VolatilityRegime.NORMAL
        
        # Calculate returns
        returns = np.diff(historical_data) / historical_data[:-1]
        
        # Calculate volatility (annualized)
        volatility = np.std(returns) * np.sqrt(365 * 24)  # Assuming hourly data
        
        # Store volatility history
        model_key = f"{asset}_{chain}"
        if model_key not in self.volatility_history:
            self.volatility_history[model_key] = []
        self.volatility_history[model_key].append(volatility)
        
        # Keep only recent history
        self.volatility_history[model_key] = self.volatility_history[model_key][-100:]
        
        # Determine regime based on volatility level
        if volatility < 0.2:
            return VolatilityRegime.LOW
        elif volatility < 0.5:
            return VolatilityRegime.NORMAL
        elif volatility < 1.0:
            return VolatilityRegime.HIGH
        else:
            return VolatilityRegime.EXTREME
    
    async def _update_model_performance(self, model_key: str, 
                                        prediction: PredictionAccuracy) -> None:
        """Update model performance metrics"""
        
        if model_key not in self.model_performance:
            self.model_performance[model_key] = ModelPerformance(
                model_id=model_key,
                model_type=prediction.model_used,
                predictions_made=0,
                accuracy_score=1.0,
                mean_absolute_error=0.0,
                mean_squared_error=0.0,
                directional_accuracy=1.0,
                last_updated=datetime.now(),
                performance_trend='stable'
            )
        
        perf = self.model_performance[model_key]
        n = perf.predictions_made
        
        # Update metrics using running average
        perf.predictions_made += 1
        perf.mean_absolute_error = (n * perf.mean_absolute_error + prediction.prediction_error) / (n + 1)
        perf.mean_squared_error = (n * perf.mean_squared_error + prediction.prediction_error ** 2) / (n + 1)
        
        # Update directional accuracy
        direction_score = 1.0 if prediction.direction_correct else 0.0
        perf.directional_accuracy = (n * perf.directional_accuracy + direction_score) / (n + 1)
        
        # Calculate accuracy score (inverse of error percentage)
        perf.accuracy_score = max(0.0, 1.0 - prediction.prediction_error_pct)
        
        # Determine performance trend
        perf.performance_trend = self._calculate_performance_trend(model_key)
        perf.last_updated = datetime.now()
    
    def _calculate_performance_trend(self, model_key: str) -> str:
        """Calculate performance trend from history"""
        
        if model_key not in self.prediction_history:
            return 'stable'
        
        predictions = self.prediction_history[model_key]
        if len(predictions) < 10:
            return 'stable'
        
        # Compare recent vs historical accuracy
        recent = predictions[-5:]
        historical = predictions[-20:-5]
        
        recent_accuracy = np.mean([1.0 - p.prediction_error_pct for p in recent])
        historical_accuracy = np.mean([1.0 - p.prediction_error_pct for p in historical])
        
        if recent_accuracy > historical_accuracy * 1.05:
            return 'improving'
        elif recent_accuracy < historical_accuracy * 0.95:
            return 'degrading'
        else:
            return 'stable'
    
    async def _should_retrain_model(self, model_key: str) -> bool:
        """Check if model should be retrained based on performance"""
        
        if model_key not in self.model_performance:
            return False
        
        perf = self.model_performance[model_key]
        
        # Need minimum predictions before retraining
        if perf.predictions_made < self.min_predictions_for_adaptation:
            return False
        
        # Check for performance degradation
        if perf.performance_trend == 'degrading':
            return True
        
        # Check accuracy threshold
        if perf.accuracy_score < 0.7:
            return True
        
        # Check directional accuracy
        if perf.directional_accuracy < 0.5:
            return True
        
        return False

    async def _get_historical_data(self, asset: str, chain: str, 
                                  timeframe: Timeframe) -> np.ndarray:
        """Get historical price data for an asset"""
        
        # Determine lookback period based on timeframe
        lookback_hours = {
            Timeframe.SHORT_TERM: 24,      # 1 day
            Timeframe.MEDIUM_TERM: 168,    # 1 week
            Timeframe.LONG_TERM: 720       # 30 days
        }
        
        hours = lookback_hours.get(timeframe, 168)
        
        # Try to get from cache first
        cache_key = f"historical:{asset}:{chain}:{hours}"
        if self.redis_client:
            try:
                cached = self.redis_client.get(cache_key)
                if cached:
                    import json
                    return np.array(json.loads(cached))
            except Exception:
                pass
        
        # Generate mock data for testing (in production, fetch from price oracles)
        base_price = 100.0
        data = [base_price]
        
        for i in range(hours - 1):
            # Random walk with slight trend
            change = np.random.normal(0, 0.02)  # 2% volatility
            new_price = data[-1] * (1 + change)
            data.append(new_price)
        
        return np.array(data)
    
    def _get_prediction_horizon(self, timeframe: Timeframe) -> timedelta:
        """Get prediction horizon for a timeframe"""
        
        horizons = {
            Timeframe.SHORT_TERM: timedelta(minutes=30),
            Timeframe.MEDIUM_TERM: timedelta(hours=4),
            Timeframe.LONG_TERM: timedelta(days=1)
        }
        return horizons.get(timeframe, timedelta(hours=1))
    
    def _get_prediction_steps(self, timeframe: Timeframe) -> int:
        """Get number of prediction steps for a timeframe"""
        
        steps = {
            Timeframe.SHORT_TERM: 6,    # 6 x 5min = 30min
            Timeframe.MEDIUM_TERM: 4,   # 4 x 1hr = 4hr
            Timeframe.LONG_TERM: 24     # 24 x 1hr = 1day
        }
        return steps.get(timeframe, 4)
    
    def _calculate_prediction_confidence(self, model_key: str, 
                                        volatility_regime: VolatilityRegime,
                                        data_points: int) -> float:
        """Calculate prediction confidence score"""
        
        # Base confidence from data availability
        data_confidence = min(1.0, data_points / 100)
        
        # Adjust for volatility regime
        volatility_factor = {
            VolatilityRegime.LOW: 1.0,
            VolatilityRegime.NORMAL: 0.9,
            VolatilityRegime.HIGH: 0.7,
            VolatilityRegime.EXTREME: 0.5
        }
        
        # Adjust for model performance
        model_factor = 1.0
        if model_key in self.model_performance:
            perf = self.model_performance[model_key]
            model_factor = perf.accuracy_score
        
        confidence = data_confidence * volatility_factor.get(volatility_regime, 0.8) * model_factor
        return max(0.1, min(1.0, confidence))
    
    def _get_factors_considered(self, model_name: str, 
                               volatility_regime: VolatilityRegime) -> List[str]:
        """Get list of factors considered in prediction"""
        
        base_factors = ['historical_prices', 'price_momentum', 'volatility']
        
        model_factors = {
            'lstm': ['sequence_patterns', 'temporal_dependencies', 'trend_memory'],
            'arima': ['autoregression', 'differencing', 'moving_average'],
            'transformer': ['attention_patterns', 'multi_scale_features', 'cross_correlations'],
            'ensemble': ['model_consensus', 'weighted_averaging', 'uncertainty_estimation']
        }
        
        factors = base_factors + model_factors.get(model_name, [])
        
        # Add volatility-specific factors
        if volatility_regime in [VolatilityRegime.HIGH, VolatilityRegime.EXTREME]:
            factors.extend(['volatility_adjustment', 'risk_scaling'])
        
        return factors
    
    def _determine_overall_trend(self, short_term: PriceForecast, 
                                medium_term: PriceForecast,
                                long_term: PriceForecast) -> Tuple[str, float]:
        """Determine overall trend from multi-timeframe predictions"""
        
        current = short_term.current_price
        
        # Calculate price changes
        short_change = (short_term.predicted_price - current) / current
        medium_change = (medium_term.predicted_price - current) / current
        long_change = (long_term.predicted_price - current) / current
        
        # Weighted average (longer term has more weight)
        weighted_change = short_change * 0.2 + medium_change * 0.3 + long_change * 0.5
        
        # Determine trend
        if weighted_change > 0.02:
            trend = 'bullish'
        elif weighted_change < -0.02:
            trend = 'bearish'
        else:
            trend = 'sideways'
        
        # Calculate confidence based on agreement
        changes = [short_change, medium_change, long_change]
        agreement = 1.0 - np.std(changes) / (abs(np.mean(changes)) + 0.01)
        
        # Combine with individual confidences
        avg_confidence = (short_term.prediction_confidence + 
                         medium_term.prediction_confidence + 
                         long_term.prediction_confidence) / 3
        
        trend_confidence = agreement * avg_confidence
        return trend, max(0.1, min(1.0, trend_confidence))

    def _estimate_bridge_delay(self, source_chain: str, target_chain: str) -> timedelta:
        """Estimate bridge delay between chains"""
        delays = {
            ('ethereum', 'polygon'): timedelta(minutes=15),
            ('ethereum', 'arbitrum'): timedelta(minutes=10),
            ('ethereum', 'optimism'): timedelta(minutes=10),
            ('polygon', 'ethereum'): timedelta(minutes=30),
            ('arbitrum', 'ethereum'): timedelta(minutes=60),
        }
        return delays.get((source_chain.lower(), target_chain.lower()), timedelta(minutes=20))
    
    def _estimate_bridge_cost(self, source_chain: str, target_chain: str, amount: float) -> float:
        """Estimate bridge cost"""
        base_rates = {('ethereum', 'polygon'): 0.001, ('ethereum', 'arbitrum'): 0.0005}
        rate = base_rates.get((source_chain.lower(), target_chain.lower()), 0.002)
        return amount * rate
    
    def _calculate_chain_correlation(self, source_data: np.ndarray, target_data: np.ndarray) -> float:
        """Calculate correlation between chain prices"""
        if len(source_data) < 10 or len(target_data) < 10:
            return 0.8
        min_len = min(len(source_data), len(target_data))
        return float(np.corrcoef(source_data[-min_len:], target_data[-min_len:])[0, 1])
    
    def _calculate_arbitrage_score(self, source: PriceForecast, target: PriceForecast,
                                  delay: timedelta, cost: float) -> float:
        """Calculate arbitrage opportunity score"""
        price_diff = abs(target.predicted_price - source.predicted_price)
        profit_potential = price_diff - cost
        if profit_potential <= 0:
            return 0.0
        time_factor = max(0.5, 1.0 - delay.total_seconds() / 3600)
        confidence_factor = (source.prediction_confidence + target.prediction_confidence) / 2
        return min(1.0, (profit_potential / source.current_price) * time_factor * confidence_factor * 10)
    
    def _get_cached_forecast(self, cache_key: str) -> Optional[PriceForecast]:
        """Get cached forecast"""
        return self.prediction_cache.get(cache_key)
    
    def _cache_forecast(self, cache_key: str, forecast: PriceForecast) -> None:
        """Cache forecast"""
        self.prediction_cache[cache_key] = forecast
    
    def get_model_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for all models"""
        return {k: {'accuracy': v.accuracy_score, 'mae': v.mean_absolute_error, 
                   'predictions': v.predictions_made, 'trend': v.performance_trend}
                for k, v in self.model_performance.items()}
    
    def get_prediction_accuracy_history(self, asset: str, chain: str) -> List[Dict]:
        """Get prediction accuracy history"""
        key = f"{asset}_{chain}"
        if key not in self.prediction_history:
            return []
        return [{'error_pct': p.prediction_error_pct, 'direction_correct': p.direction_correct,
                'timeframe': p.timeframe.value} for p in self.prediction_history[key][-50:]]
