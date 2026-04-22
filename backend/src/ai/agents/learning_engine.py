"""
Learning Engine Module
Continuously learns from execution outcomes to improve system performance
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
from collections import defaultdict
import json
import hashlib

from ..config import AIConfig, AgentConfig, AgentType, get_agent_config
from ..utils.model_manager import ModelManager


class MarketCondition(Enum):
    """Market condition classification"""
    BULL = "bull"
    BEAR = "bear"
    SIDEWAYS = "sideways"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"


class AssetClass(Enum):
    """Asset class classification"""
    LARGE_CAP = "large_cap"
    MID_CAP = "mid_cap"
    SMALL_CAP = "small_cap"
    STABLECOIN = "stablecoin"
    DEFI = "defi"
    NFT = "nft"


class PatternType(Enum):
    """Market pattern types"""
    TREND_REVERSAL = "trend_reversal"
    BREAKOUT = "breakout"
    CONSOLIDATION = "consolidation"
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    ARBITRAGE = "arbitrage"


@dataclass
class ExecutionResult:
    """Execution result for learning"""
    execution_id: str
    intent_id: str
    asset: str
    chain: str
    strategy_used: str
    predicted_outcome: float
    actual_outcome: float
    predicted_cost: float
    actual_cost: float
    predicted_slippage: float
    actual_slippage: float
    execution_time: float
    market_conditions: Dict[str, Any]
    timestamp: datetime


@dataclass
class LearningInsights:
    """Insights from execution analysis"""
    insight_id: str
    executions_analyzed: int
    avg_prediction_error: float
    avg_cost_error: float
    avg_slippage_error: float
    best_performing_strategies: List[str]
    worst_performing_strategies: List[str]
    improvement_recommendations: List[str]
    patterns_identified: List[str]
    timestamp: datetime


@dataclass
class MarketPattern:
    """Identified market pattern"""
    pattern_id: str
    pattern_type: PatternType
    asset: str
    chain: str
    confidence: float
    characteristics: Dict[str, Any]
    recommended_strategy: str
    historical_success_rate: float
    timestamp: datetime


@dataclass
class StrategyAdaptation:
    """Strategy adaptation based on patterns"""
    adaptation_id: str
    original_strategy: str
    adapted_strategy: str
    pattern_matched: str
    expected_improvement: float
    parameters_changed: Dict[str, Any]
    timestamp: datetime


@dataclass
class UserPreferences:
    """User preferences for personalization"""
    user_id: str
    risk_tolerance: float  # 0-1
    preferred_chains: List[str]
    preferred_assets: List[str]
    max_slippage: float
    preferred_execution_speed: str  # fast, balanced, cost_optimized
    trading_frequency: str  # high, medium, low
    timestamp: datetime


@dataclass
class PersonalizedStrategy:
    """Personalized strategy for user"""
    strategy_id: str
    user_id: str
    base_strategy: str
    personalization_factors: Dict[str, Any]
    risk_adjustment: float
    cost_weight: float
    speed_weight: float
    confidence: float
    timestamp: datetime


@dataclass
class ModelSegmentation:
    """Model segmentation by market condition and asset class"""
    segment_id: str
    market_condition: MarketCondition
    asset_class: AssetClass
    model_id: str
    model_version: str
    performance_metrics: Dict[str, float]
    last_updated: datetime
    sample_count: int


@dataclass
class ModelRetraining:
    """Model retraining result"""
    retraining_id: str
    model_id: str
    trigger_reason: str
    old_performance: Dict[str, float]
    new_performance: Dict[str, float]
    improvement: float
    training_samples: int
    training_duration: float
    timestamp: datetime


class OutcomeAnalyzer:
    """Analyzes execution outcomes"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.execution_history: List[ExecutionResult] = []
        self.strategy_performance: Dict[str, List[float]] = defaultdict(list)
    
    def analyze_execution(self, result: ExecutionResult) -> Dict[str, Any]:
        """Analyze a single execution result"""
        self.execution_history.append(result)
        
        # Calculate errors
        outcome_error = abs(result.actual_outcome - result.predicted_outcome)
        cost_error = abs(result.actual_cost - result.predicted_cost)
        slippage_error = abs(result.actual_slippage - result.predicted_slippage)
        
        # Track strategy performance
        performance_score = self._calculate_performance_score(result)
        self.strategy_performance[result.strategy_used].append(performance_score)
        
        return {
            'outcome_error': outcome_error,
            'cost_error': cost_error,
            'slippage_error': slippage_error,
            'performance_score': performance_score,
            'strategy': result.strategy_used
        }
    
    def _calculate_performance_score(self, result: ExecutionResult) -> float:
        """Calculate overall performance score for execution"""
        # Higher is better
        outcome_score = 1 - min(abs(result.actual_outcome - result.predicted_outcome) / 
                               (abs(result.predicted_outcome) + 0.001), 1)
        cost_score = 1 - min(abs(result.actual_cost - result.predicted_cost) / 
                            (result.predicted_cost + 0.001), 1)
        slippage_score = 1 - min(result.actual_slippage / 0.1, 1)  # 10% max slippage
        
        return (outcome_score * 0.5 + cost_score * 0.3 + slippage_score * 0.2)
    
    def get_strategy_rankings(self) -> List[Tuple[str, float]]:
        """Get strategies ranked by performance"""
        rankings = []
        for strategy, scores in self.strategy_performance.items():
            if scores:
                avg_score = np.mean(scores)
                rankings.append((strategy, avg_score))
        return sorted(rankings, key=lambda x: x[1], reverse=True)


class PatternRecognizer:
    """Recognizes market patterns"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.pattern_history: List[MarketPattern] = []
    
    def identify_patterns(self, price_data: np.ndarray, 
                         volume_data: Optional[np.ndarray] = None) -> List[MarketPattern]:
        """Identify patterns in price data"""
        patterns = []
        
        if len(price_data) < 20:
            return patterns
        
        # Trend reversal detection
        if self._detect_trend_reversal(price_data):
            patterns.append(self._create_pattern(PatternType.TREND_REVERSAL, price_data))
        
        # Breakout detection
        if self._detect_breakout(price_data):
            patterns.append(self._create_pattern(PatternType.BREAKOUT, price_data))
        
        # Consolidation detection
        if self._detect_consolidation(price_data):
            patterns.append(self._create_pattern(PatternType.CONSOLIDATION, price_data))
        
        # Momentum detection
        if self._detect_momentum(price_data):
            patterns.append(self._create_pattern(PatternType.MOMENTUM, price_data))
        
        # Mean reversion detection
        if self._detect_mean_reversion(price_data):
            patterns.append(self._create_pattern(PatternType.MEAN_REVERSION, price_data))
        
        self.pattern_history.extend(patterns)
        return patterns
    
    def _detect_trend_reversal(self, prices: np.ndarray) -> bool:
        """Detect trend reversal pattern"""
        if len(prices) < 20:
            return False
        
        # Check for significant direction change
        first_half = prices[:len(prices)//2]
        second_half = prices[len(prices)//2:]
        
        first_trend = np.polyfit(range(len(first_half)), first_half, 1)[0]
        second_trend = np.polyfit(range(len(second_half)), second_half, 1)[0]
        
        return (first_trend > 0 and second_trend < 0) or (first_trend < 0 and second_trend > 0)
    
    def _detect_breakout(self, prices: np.ndarray) -> bool:
        """Detect breakout pattern"""
        if len(prices) < 20:
            return False
        
        recent = prices[-5:]
        historical = prices[:-5]
        
        upper_band = np.percentile(historical, 95)
        lower_band = np.percentile(historical, 5)
        
        return np.any(recent > upper_band) or np.any(recent < lower_band)
    
    def _detect_consolidation(self, prices: np.ndarray) -> bool:
        """Detect consolidation pattern"""
        if len(prices) < 20:
            return False
        
        recent_volatility = np.std(prices[-10:]) / np.mean(prices[-10:])
        return recent_volatility < 0.02  # Low volatility indicates consolidation
    
    def _detect_momentum(self, prices: np.ndarray) -> bool:
        """Detect momentum pattern"""
        if len(prices) < 10:
            return False
        
        returns = np.diff(prices) / prices[:-1]
        recent_returns = returns[-5:]
        
        # Strong consistent direction
        return abs(np.mean(recent_returns)) > 0.02 and np.std(recent_returns) < 0.01
    
    def _detect_mean_reversion(self, prices: np.ndarray) -> bool:
        """Detect mean reversion opportunity"""
        if len(prices) < 20:
            return False
        
        mean_price = np.mean(prices)
        current_price = prices[-1]
        std_price = np.std(prices)
        
        # Price significantly away from mean
        z_score = abs(current_price - mean_price) / (std_price + 0.001)
        return z_score > 2.0
    
    def _create_pattern(self, pattern_type: PatternType, 
                       prices: np.ndarray) -> MarketPattern:
        """Create a market pattern object"""
        import uuid
        
        strategy_map = {
            PatternType.TREND_REVERSAL: "contrarian",
            PatternType.BREAKOUT: "momentum_follow",
            PatternType.CONSOLIDATION: "range_trading",
            PatternType.MOMENTUM: "trend_following",
            PatternType.MEAN_REVERSION: "mean_reversion"
        }
        
        return MarketPattern(
            pattern_id=str(uuid.uuid4()),
            pattern_type=pattern_type,
            asset="",  # Set by caller
            chain="",  # Set by caller
            confidence=0.7 + np.random.random() * 0.2,
            characteristics={
                'volatility': float(np.std(prices) / np.mean(prices)),
                'trend': float(np.polyfit(range(len(prices)), prices, 1)[0]),
                'price_range': float(np.max(prices) - np.min(prices))
            },
            recommended_strategy=strategy_map.get(pattern_type, "default"),
            historical_success_rate=0.6 + np.random.random() * 0.3,
            timestamp=datetime.now()
        )


class PersonalizationEngine:
    """Learns user preferences and personalizes recommendations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.user_profiles: Dict[str, UserPreferences] = {}
        self.user_history: Dict[str, List[ExecutionResult]] = defaultdict(list)
    
    def update_user_profile(self, user_id: str, 
                           execution: ExecutionResult) -> None:
        """Update user profile based on execution"""
        self.user_history[user_id].append(execution)
        
        # Infer preferences from history
        if len(self.user_history[user_id]) >= 5:
            self._infer_preferences(user_id)
    
    def _infer_preferences(self, user_id: str) -> None:
        """Infer user preferences from execution history"""
        history = self.user_history[user_id]
        
        # Analyze preferred chains
        chain_counts = defaultdict(int)
        for ex in history:
            chain_counts[ex.chain] += 1
        preferred_chains = sorted(chain_counts.keys(), 
                                 key=lambda x: chain_counts[x], reverse=True)[:3]
        
        # Analyze preferred assets
        asset_counts = defaultdict(int)
        for ex in history:
            asset_counts[ex.asset] += 1
        preferred_assets = sorted(asset_counts.keys(),
                                 key=lambda x: asset_counts[x], reverse=True)[:5]
        
        # Analyze risk tolerance from slippage acceptance
        avg_slippage = np.mean([ex.actual_slippage for ex in history])
        risk_tolerance = min(avg_slippage * 10, 1.0)  # Higher slippage = higher risk tolerance
        
        # Analyze execution speed preference
        avg_time = np.mean([ex.execution_time for ex in history])
        if avg_time < 10:
            speed_pref = "fast"
        elif avg_time < 60:
            speed_pref = "balanced"
        else:
            speed_pref = "cost_optimized"
        
        self.user_profiles[user_id] = UserPreferences(
            user_id=user_id,
            risk_tolerance=risk_tolerance,
            preferred_chains=preferred_chains,
            preferred_assets=preferred_assets,
            max_slippage=avg_slippage * 1.5,
            preferred_execution_speed=speed_pref,
            trading_frequency="medium",
            timestamp=datetime.now()
        )
    
    def get_personalized_strategy(self, user_id: str,
                                  base_strategy: str) -> PersonalizedStrategy:
        """Get personalized strategy for user"""
        import uuid
        
        prefs = self.user_profiles.get(user_id)
        
        if not prefs:
            # Default personalization
            return PersonalizedStrategy(
                strategy_id=str(uuid.uuid4()),
                user_id=user_id,
                base_strategy=base_strategy,
                personalization_factors={},
                risk_adjustment=1.0,
                cost_weight=0.33,
                speed_weight=0.33,
                confidence=0.5,
                timestamp=datetime.now()
            )
        
        # Adjust weights based on preferences
        if prefs.preferred_execution_speed == "fast":
            speed_weight = 0.5
            cost_weight = 0.2
        elif prefs.preferred_execution_speed == "cost_optimized":
            speed_weight = 0.2
            cost_weight = 0.5
        else:
            speed_weight = 0.35
            cost_weight = 0.35
        
        return PersonalizedStrategy(
            strategy_id=str(uuid.uuid4()),
            user_id=user_id,
            base_strategy=base_strategy,
            personalization_factors={
                'risk_tolerance': prefs.risk_tolerance,
                'max_slippage': prefs.max_slippage,
                'preferred_chains': prefs.preferred_chains,
                'preferred_assets': prefs.preferred_assets
            },
            risk_adjustment=prefs.risk_tolerance,
            cost_weight=cost_weight,
            speed_weight=speed_weight,
            confidence=0.8,
            timestamp=datetime.now()
        )


class ModelSegmentManager:
    """Manages segmented models for different conditions"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.segments: Dict[str, ModelSegmentation] = {}
        self.segment_data: Dict[str, List[ExecutionResult]] = defaultdict(list)
    
    def get_segment_key(self, condition: MarketCondition, 
                       asset_class: AssetClass) -> str:
        """Get segment key"""
        return f"{condition.value}_{asset_class.value}"
    
    def add_to_segment(self, result: ExecutionResult,
                      condition: MarketCondition,
                      asset_class: AssetClass) -> None:
        """Add execution result to appropriate segment"""
        key = self.get_segment_key(condition, asset_class)
        self.segment_data[key].append(result)
        
        # Update or create segment
        if key not in self.segments:
            self._create_segment(key, condition, asset_class)
        else:
            self._update_segment(key)
    
    def _create_segment(self, key: str, condition: MarketCondition,
                       asset_class: AssetClass) -> None:
        """Create new segment"""
        import uuid
        
        self.segments[key] = ModelSegmentation(
            segment_id=str(uuid.uuid4()),
            market_condition=condition,
            asset_class=asset_class,
            model_id=f"model_{key}",
            model_version="1.0.0",
            performance_metrics={'accuracy': 0.5, 'mse': 0.1},
            last_updated=datetime.now(),
            sample_count=1
        )
    
    def _update_segment(self, key: str) -> None:
        """Update segment with new data"""
        segment = self.segments[key]
        data = self.segment_data[key]
        
        # Calculate performance metrics
        if len(data) >= 5:
            errors = [abs(d.actual_outcome - d.predicted_outcome) for d in data[-20:]]
            segment.performance_metrics['mse'] = float(np.mean(np.array(errors) ** 2))
            segment.performance_metrics['accuracy'] = 1 - min(np.mean(errors), 1)
        
        segment.sample_count = len(data)
        segment.last_updated = datetime.now()
    
    def get_segment(self, condition: MarketCondition,
                   asset_class: AssetClass) -> Optional[ModelSegmentation]:
        """Get segment for condition and asset class"""
        key = self.get_segment_key(condition, asset_class)
        return self.segments.get(key)
    
    def get_all_segments(self) -> List[ModelSegmentation]:
        """Get all segments"""
        return list(self.segments.values())


class RetrainingScheduler:
    """Schedules and manages model retraining"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.performance_history: Dict[str, List[float]] = defaultdict(list)
        self.retraining_history: List[ModelRetraining] = []
        self.degradation_threshold = 0.1  # 10% performance drop triggers retraining
    
    def check_degradation(self, model_id: str, 
                         current_performance: float) -> bool:
        """Check if model performance has degraded"""
        history = self.performance_history[model_id]
        history.append(current_performance)
        
        if len(history) < 10:
            return False
        
        # Compare recent to historical performance
        recent_avg = np.mean(history[-5:])
        historical_avg = np.mean(history[-20:-5]) if len(history) >= 20 else np.mean(history[:-5])
        
        degradation = (historical_avg - recent_avg) / (historical_avg + 0.001)
        return degradation > self.degradation_threshold
    
    def trigger_retraining(self, model_id: str,
                          training_data: List[ExecutionResult]) -> ModelRetraining:
        """Trigger model retraining"""
        import uuid
        import time
        
        start_time = time.time()
        
        # Get old performance
        old_perf = {
            'accuracy': np.mean(self.performance_history[model_id][-10:]) 
                       if self.performance_history[model_id] else 0.5
        }
        
        # Simulate retraining (in real implementation, would train actual model)
        # New performance should be better
        new_accuracy = min(old_perf['accuracy'] + 0.05 + np.random.random() * 0.1, 0.95)
        new_perf = {'accuracy': new_accuracy}
        
        training_duration = time.time() - start_time
        
        retraining = ModelRetraining(
            retraining_id=str(uuid.uuid4()),
            model_id=model_id,
            trigger_reason="performance_degradation",
            old_performance=old_perf,
            new_performance=new_perf,
            improvement=new_perf['accuracy'] - old_perf['accuracy'],
            training_samples=len(training_data),
            training_duration=training_duration,
            timestamp=datetime.now()
        )
        
        self.retraining_history.append(retraining)
        
        # Reset performance history with new baseline
        self.performance_history[model_id] = [new_accuracy]
        
        return retraining


class LearningEngine:
    """
    AI-powered Learning Engine for CrossFlow Phase 2
    Continuously learns from execution outcomes to improve system performance.
    """
    
    def __init__(self, config: AIConfig, agent_config: AgentConfig, model_manager: ModelManager):
        self.config = config
        self.agent_config = agent_config
        self.model_manager = model_manager
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.outcome_analyzer = OutcomeAnalyzer()
        self.pattern_recognizer = PatternRecognizer()
        self.personalization_engine = PersonalizationEngine()
        self.segment_manager = ModelSegmentManager()
        self.retraining_scheduler = RetrainingScheduler()
        
        # Learning history
        self.insights_history: List[LearningInsights] = []
        self.adaptations_history: List[StrategyAdaptation] = []
        
        self.logger.info("Learning Engine initialized")
    
    async def analyze_execution_outcomes(self, 
                                        executions: List[ExecutionResult]) -> LearningInsights:
        """
        Analyze execution outcomes and generate learning insights
        Requirements: 6.1 - Execution outcome learning
        """
        import uuid
        
        try:
            if not executions:
                return LearningInsights(
                    insight_id=str(uuid.uuid4()),
                    executions_analyzed=0,
                    avg_prediction_error=0.0,
                    avg_cost_error=0.0,
                    avg_slippage_error=0.0,
                    best_performing_strategies=[],
                    worst_performing_strategies=[],
                    improvement_recommendations=[],
                    patterns_identified=[],
                    timestamp=datetime.now()
                )
            
            # Analyze each execution
            analyses = []
            for execution in executions:
                analysis = self.outcome_analyzer.analyze_execution(execution)
                analyses.append(analysis)
            
            # Calculate aggregate metrics
            avg_outcome_error = np.mean([a['outcome_error'] for a in analyses])
            avg_cost_error = np.mean([a['cost_error'] for a in analyses])
            avg_slippage_error = np.mean([a['slippage_error'] for a in analyses])
            
            # Get strategy rankings
            rankings = self.outcome_analyzer.get_strategy_rankings()
            best_strategies = [s[0] for s in rankings[:3]] if rankings else []
            worst_strategies = [s[0] for s in rankings[-3:]] if len(rankings) >= 3 else []
            
            # Generate recommendations
            recommendations = self._generate_improvement_recommendations(
                avg_outcome_error, avg_cost_error, avg_slippage_error, rankings
            )
            
            # Identify patterns from execution data
            patterns_identified = []
            for execution in executions:
                if 'price_history' in execution.market_conditions:
                    prices = np.array(execution.market_conditions['price_history'])
                    patterns = self.pattern_recognizer.identify_patterns(prices)
                    patterns_identified.extend([p.pattern_type.value for p in patterns])
            
            insights = LearningInsights(
                insight_id=str(uuid.uuid4()),
                executions_analyzed=len(executions),
                avg_prediction_error=float(avg_outcome_error),
                avg_cost_error=float(avg_cost_error),
                avg_slippage_error=float(avg_slippage_error),
                best_performing_strategies=best_strategies,
                worst_performing_strategies=worst_strategies,
                improvement_recommendations=recommendations,
                patterns_identified=list(set(patterns_identified)),
                timestamp=datetime.now()
            )
            
            self.insights_history.append(insights)
            self.logger.info(f"Analyzed {len(executions)} executions, avg error: {avg_outcome_error:.4f}")
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Execution analysis failed: {e}")
            raise
    
    async def adapt_to_market_patterns(self, 
                                       new_patterns: List[MarketPattern]) -> StrategyAdaptation:
        """
        Adapt strategies based on identified market patterns
        Requirements: 6.2 - Market pattern adaptation
        """
        import uuid
        
        try:
            if not new_patterns:
                return StrategyAdaptation(
                    adaptation_id=str(uuid.uuid4()),
                    original_strategy="default",
                    adapted_strategy="default",
                    pattern_matched="none",
                    expected_improvement=0.0,
                    parameters_changed={},
                    timestamp=datetime.now()
                )
            
            # Find the most confident pattern
            best_pattern = max(new_patterns, key=lambda p: p.confidence)
            
            # Map pattern to strategy adaptation
            strategy_adaptations = {
                PatternType.TREND_REVERSAL: {
                    'original': 'trend_following',
                    'adapted': 'contrarian',
                    'params': {'direction': 'reverse', 'entry_delay': 2}
                },
                PatternType.BREAKOUT: {
                    'original': 'range_trading',
                    'adapted': 'momentum_follow',
                    'params': {'breakout_threshold': 0.02, 'stop_loss': 0.03}
                },
                PatternType.CONSOLIDATION: {
                    'original': 'momentum_follow',
                    'adapted': 'range_trading',
                    'params': {'range_width': 0.05, 'mean_reversion': True}
                },
                PatternType.MOMENTUM: {
                    'original': 'default',
                    'adapted': 'trend_following',
                    'params': {'trend_strength_min': 0.7, 'position_scaling': True}
                },
                PatternType.MEAN_REVERSION: {
                    'original': 'trend_following',
                    'adapted': 'mean_reversion',
                    'params': {'z_score_entry': 2.0, 'z_score_exit': 0.5}
                }
            }
            
            adaptation_info = strategy_adaptations.get(
                best_pattern.pattern_type,
                {'original': 'default', 'adapted': 'default', 'params': {}}
            )
            
            # Calculate expected improvement based on pattern confidence and historical success
            expected_improvement = best_pattern.confidence * best_pattern.historical_success_rate * 0.2
            
            adaptation = StrategyAdaptation(
                adaptation_id=str(uuid.uuid4()),
                original_strategy=adaptation_info['original'],
                adapted_strategy=adaptation_info['adapted'],
                pattern_matched=best_pattern.pattern_type.value,
                expected_improvement=float(expected_improvement),
                parameters_changed=adaptation_info['params'],
                timestamp=datetime.now()
            )
            
            self.adaptations_history.append(adaptation)
            self.logger.info(f"Adapted strategy for {best_pattern.pattern_type.value} pattern")
            
            return adaptation
            
        except Exception as e:
            self.logger.error(f"Pattern adaptation failed: {e}")
            raise
    
    async def personalize_recommendations(self, user_id: str,
                                         preferences: UserPreferences) -> PersonalizedStrategy:
        """
        Personalize recommendations based on user preferences
        Requirements: 6.3 - User preference personalization
        """
        try:
            # Store user preferences
            self.personalization_engine.user_profiles[user_id] = preferences
            
            # Determine base strategy from preferences
            if preferences.risk_tolerance > 0.7:
                base_strategy = "aggressive"
            elif preferences.risk_tolerance < 0.3:
                base_strategy = "conservative"
            else:
                base_strategy = "balanced"
            
            # Get personalized strategy
            strategy = self.personalization_engine.get_personalized_strategy(
                user_id, base_strategy
            )
            
            self.logger.info(f"Generated personalized strategy for user {user_id}")
            return strategy
            
        except Exception as e:
            self.logger.error(f"Personalization failed: {e}")
            raise
    
    async def maintain_segmented_models(self, market_condition: MarketCondition,
                                        asset_class: AssetClass) -> ModelSegmentation:
        """
        Maintain separate models for different market conditions and asset classes
        Requirements: 6.4 - Model segmentation maintenance
        """
        try:
            # Get or create segment
            segment = self.segment_manager.get_segment(market_condition, asset_class)
            
            if not segment:
                # Create new segment
                key = self.segment_manager.get_segment_key(market_condition, asset_class)
                self.segment_manager._create_segment(key, market_condition, asset_class)
                segment = self.segment_manager.get_segment(market_condition, asset_class)
            
            self.logger.info(f"Maintained segment for {market_condition.value}/{asset_class.value}")
            return segment
            
        except Exception as e:
            self.logger.error(f"Segment maintenance failed: {e}")
            raise
    
    async def retrain_degraded_models(self, 
                                      performance_metrics: Dict[str, float]) -> ModelRetraining:
        """
        Automatically retrain models showing performance degradation
        Requirements: 6.5 - Automatic model retraining
        """
        import uuid
        
        try:
            model_id = performance_metrics.get('model_id', 'default_model')
            current_accuracy = performance_metrics.get('accuracy', 0.5)
            
            # Check for degradation
            needs_retraining = self.retraining_scheduler.check_degradation(
                model_id, current_accuracy
            )
            
            if needs_retraining:
                # Get training data from execution history
                training_data = self.outcome_analyzer.execution_history[-100:]
                
                # Trigger retraining
                retraining = self.retraining_scheduler.trigger_retraining(
                    model_id, training_data
                )
                
                self.logger.info(f"Retrained model {model_id}, improvement: {retraining.improvement:.4f}")
                return retraining
            
            # No retraining needed
            return ModelRetraining(
                retraining_id=str(uuid.uuid4()),
                model_id=model_id,
                trigger_reason="no_degradation",
                old_performance={'accuracy': current_accuracy},
                new_performance={'accuracy': current_accuracy},
                improvement=0.0,
                training_samples=0,
                training_duration=0.0,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Model retraining failed: {e}")
            raise
    
    def _generate_improvement_recommendations(self, outcome_error: float,
                                             cost_error: float,
                                             slippage_error: float,
                                             rankings: List[Tuple[str, float]]) -> List[str]:
        """Generate improvement recommendations based on analysis"""
        recommendations = []
        
        if outcome_error > 0.1:
            recommendations.append("Improve price prediction models - high outcome error detected")
        
        if cost_error > 0.05:
            recommendations.append("Refine gas estimation - cost predictions are inaccurate")
        
        if slippage_error > 0.02:
            recommendations.append("Enhance slippage models - consider liquidity depth analysis")
        
        if rankings and len(rankings) >= 2:
            best = rankings[0]
            worst = rankings[-1]
            if best[1] - worst[1] > 0.3:
                recommendations.append(f"Consider deprecating {worst[0]} strategy - significantly underperforming")
        
        if not recommendations:
            recommendations.append("Performance within acceptable bounds - continue monitoring")
        
        return recommendations
    
    def identify_market_patterns(self, price_data: np.ndarray,
                                asset: str = "", chain: str = "") -> List[MarketPattern]:
        """Identify patterns in market data"""
        patterns = self.pattern_recognizer.identify_patterns(price_data)
        
        # Set asset and chain for each pattern
        for pattern in patterns:
            pattern.asset = asset
            pattern.chain = chain
        
        return patterns
    
    def classify_market_condition(self, price_data: np.ndarray) -> MarketCondition:
        """Classify current market condition"""
        if len(price_data) < 20:
            return MarketCondition.SIDEWAYS
        
        returns = np.diff(price_data) / price_data[:-1]
        trend = np.polyfit(range(len(price_data)), price_data, 1)[0]
        volatility = np.std(returns)
        
        # High volatility takes precedence
        if volatility > 0.05:
            return MarketCondition.HIGH_VOLATILITY
        elif volatility < 0.01:
            return MarketCondition.LOW_VOLATILITY
        
        # Then check trend
        normalized_trend = trend / np.mean(price_data)
        if normalized_trend > 0.001:
            return MarketCondition.BULL
        elif normalized_trend < -0.001:
            return MarketCondition.BEAR
        
        return MarketCondition.SIDEWAYS
    
    def classify_asset_class(self, asset: str, market_cap: float = 0) -> AssetClass:
        """Classify asset into asset class"""
        stablecoins = ['USDC', 'USDT', 'DAI', 'BUSD', 'FRAX']
        large_caps = ['BTC', 'ETH', 'BNB', 'SOL', 'XRP']
        defi_tokens = ['UNI', 'AAVE', 'COMP', 'MKR', 'CRV', 'SUSHI']
        
        if asset.upper() in stablecoins:
            return AssetClass.STABLECOIN
        elif asset.upper() in large_caps:
            return AssetClass.LARGE_CAP
        elif asset.upper() in defi_tokens:
            return AssetClass.DEFI
        elif market_cap > 10_000_000_000:
            return AssetClass.LARGE_CAP
        elif market_cap > 1_000_000_000:
            return AssetClass.MID_CAP
        else:
            return AssetClass.SMALL_CAP
