"""
Risk Assessment Module
Evaluates and manages risks associated with trading strategies and portfolio positions
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

from ..config import AIConfig, AgentConfig, AgentType, get_agent_config
from ..utils.model_manager import ModelManager


class RiskLevel(Enum):
    """Risk level classification"""
    MINIMAL = "minimal"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    EXTREME = "extreme"


class RiskType(Enum):
    """Types of risk"""
    MARKET = "market"
    LIQUIDITY = "liquidity"
    EXECUTION = "execution"
    SLIPPAGE = "slippage"
    VOLATILITY = "volatility"
    CONCENTRATION = "concentration"
    COUNTERPARTY = "counterparty"
    SMART_CONTRACT = "smart_contract"


class MitigationType(Enum):
    """Types of risk mitigation strategies"""
    POSITION_SIZING = "position_sizing"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    HEDGING = "hedging"
    DIVERSIFICATION = "diversification"
    TIMING_ADJUSTMENT = "timing_adjustment"
    SPLIT_EXECUTION = "split_execution"


@dataclass
class RiskMetrics:
    """Comprehensive risk metrics"""
    value_at_risk: float  # VaR at 95% confidence
    conditional_var: float  # CVaR (Expected Shortfall)
    max_drawdown: float
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    beta: float
    correlation_risk: float
    liquidity_risk: float
    timestamp: datetime


@dataclass
class RiskAssessment:
    """Risk assessment result for an intent or position"""
    assessment_id: str
    asset: str
    chain: str
    risk_level: RiskLevel
    risk_score: float  # 0-100
    risk_metrics: RiskMetrics
    risk_breakdown: Dict[RiskType, float]
    warnings: List[str]
    recommendations: List[str]
    timestamp: datetime


@dataclass
class MitigationStrategy:
    """Risk mitigation strategy recommendation"""
    strategy_id: str
    mitigation_type: MitigationType
    description: str
    expected_risk_reduction: float
    implementation_cost: float
    priority: int
    parameters: Dict[str, Any]
    timestamp: datetime


@dataclass
class ExposureAnalysis:
    """Portfolio exposure analysis"""
    total_exposure: float
    asset_exposures: Dict[str, float]
    chain_exposures: Dict[str, float]
    sector_exposures: Dict[str, float]
    concentration_risk: float
    diversification_score: float
    exposure_limits_breached: List[str]
    timestamp: datetime


@dataclass
class Position:
    """Trading position"""
    position_id: str
    asset: str
    chain: str
    size: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float
    timestamp: datetime


@dataclass
class RealTimeRiskMonitoring:
    """Real-time risk monitoring result"""
    monitoring_id: str
    positions: List[Position]
    total_risk_score: float
    risk_alerts: List[str]
    position_risks: Dict[str, RiskAssessment]
    portfolio_var: float
    portfolio_cvar: float
    margin_utilization: float
    timestamp: datetime


@dataclass
class PositionAdjustment:
    """Position adjustment recommendation"""
    adjustment_id: str
    position_id: str
    adjustment_type: str  # reduce, close, hedge
    target_size: float
    reason: str
    urgency: str  # low, medium, high, critical
    timestamp: datetime


class RiskCalculator:
    """Calculates various risk metrics"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_var(self, returns: np.ndarray, confidence: float = 0.95,
                     method: str = 'historical') -> float:
        """Calculate Value at Risk"""
        if len(returns) < 10:
            return 0.0
        
        if method == 'historical':
            return float(np.percentile(returns, (1 - confidence) * 100))
        elif method == 'parametric':
            from scipy import stats
            mean = np.mean(returns)
            std = np.std(returns)
            return float(mean - stats.norm.ppf(confidence) * std)
        else:
            return float(np.percentile(returns, (1 - confidence) * 100))
    
    def calculate_cvar(self, returns: np.ndarray, confidence: float = 0.95) -> float:
        """Calculate Conditional VaR (Expected Shortfall)"""
        if len(returns) < 10:
            return 0.0
        
        var = self.calculate_var(returns, confidence)
        return float(np.mean(returns[returns <= var]))
    
    def calculate_max_drawdown(self, prices: np.ndarray) -> float:
        """Calculate maximum drawdown"""
        if len(prices) < 2:
            return 0.0
        
        cumulative = np.maximum.accumulate(prices)
        drawdowns = (prices - cumulative) / cumulative
        return float(np.min(drawdowns))
    
    def calculate_volatility(self, returns: np.ndarray, annualize: bool = True) -> float:
        """Calculate volatility (standard deviation of returns)"""
        if len(returns) < 2:
            return 0.0
        
        vol = np.std(returns)
        if annualize:
            vol *= np.sqrt(365 * 24)  # Assuming hourly data
        return float(vol)
    
    def calculate_sharpe_ratio(self, returns: np.ndarray, 
                              risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio"""
        if len(returns) < 10:
            return 0.0
        
        excess_returns = returns - risk_free_rate / (365 * 24)
        if np.std(excess_returns) == 0:
            return 0.0
        return float(np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(365 * 24))
    
    def calculate_sortino_ratio(self, returns: np.ndarray,
                               risk_free_rate: float = 0.02) -> float:
        """Calculate Sortino ratio (downside risk adjusted)"""
        if len(returns) < 10:
            return 0.0
        
        excess_returns = returns - risk_free_rate / (365 * 24)
        downside_returns = returns[returns < 0]
        
        if len(downside_returns) == 0 or np.std(downside_returns) == 0:
            return 0.0
        
        return float(np.mean(excess_returns) / np.std(downside_returns) * np.sqrt(365 * 24))
    
    def calculate_beta(self, asset_returns: np.ndarray, 
                      market_returns: np.ndarray) -> float:
        """Calculate beta (market sensitivity)"""
        if len(asset_returns) < 10 or len(market_returns) < 10:
            return 1.0
        
        min_len = min(len(asset_returns), len(market_returns))
        asset_returns = asset_returns[-min_len:]
        market_returns = market_returns[-min_len:]
        
        covariance = np.cov(asset_returns, market_returns)[0, 1]
        market_variance = np.var(market_returns)
        
        if market_variance == 0:
            return 1.0
        
        return float(covariance / market_variance)


class SlippageEstimator:
    """Estimates potential slippage for executions"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def estimate_slippage(self, order_size: float, liquidity: float,
                         volatility: float, spread: float) -> float:
        """Estimate slippage for an order"""
        if liquidity <= 0:
            return 0.1  # 10% default for no liquidity
        
        # Market impact model
        size_impact = (order_size / liquidity) ** 0.5 * 0.1
        volatility_impact = volatility * 0.5
        spread_impact = spread
        
        total_slippage = size_impact + volatility_impact + spread_impact
        return min(float(total_slippage), 0.2)  # Cap at 20%
    
    def estimate_execution_risk(self, order_size: float, liquidity: float,
                               time_horizon: timedelta) -> float:
        """Estimate execution risk based on order size and time"""
        if liquidity <= 0:
            return 1.0
        
        # Larger orders relative to liquidity have higher risk
        size_ratio = order_size / liquidity
        
        # Shorter time horizons increase risk
        hours = time_horizon.total_seconds() / 3600
        time_factor = 1 / (1 + hours * 0.1)
        
        risk = min(size_ratio * time_factor, 1.0)
        return float(risk)


class ExposureMonitor:
    """Monitors portfolio exposure"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.exposure_limits = {
            'single_asset': 0.25,  # Max 25% in single asset
            'single_chain': 0.40,  # Max 40% on single chain
            'single_sector': 0.35,  # Max 35% in single sector
        }
    
    def calculate_exposure(self, positions: List[Position]) -> ExposureAnalysis:
        """Calculate portfolio exposure"""
        if not positions:
            return ExposureAnalysis(
                total_exposure=0.0,
                asset_exposures={},
                chain_exposures={},
                sector_exposures={},
                concentration_risk=0.0,
                diversification_score=1.0,
                exposure_limits_breached=[],
                timestamp=datetime.now()
            )
        
        total_value = sum(p.size * p.current_price for p in positions)
        
        # Calculate asset exposures
        asset_exposures = {}
        for p in positions:
            value = p.size * p.current_price
            if p.asset not in asset_exposures:
                asset_exposures[p.asset] = 0.0
            asset_exposures[p.asset] += value / total_value if total_value > 0 else 0
        
        # Calculate chain exposures
        chain_exposures = {}
        for p in positions:
            value = p.size * p.current_price
            if p.chain not in chain_exposures:
                chain_exposures[p.chain] = 0.0
            chain_exposures[p.chain] += value / total_value if total_value > 0 else 0
        
        # Calculate concentration risk (Herfindahl index)
        concentration_risk = sum(e ** 2 for e in asset_exposures.values())
        
        # Calculate diversification score
        n_assets = len(asset_exposures)
        diversification_score = 1 - concentration_risk if n_assets > 1 else 0.0
        
        # Check exposure limits
        breached = []
        for asset, exposure in asset_exposures.items():
            if exposure > self.exposure_limits['single_asset']:
                breached.append(f"Asset {asset}: {exposure:.1%} > {self.exposure_limits['single_asset']:.1%}")
        
        for chain, exposure in chain_exposures.items():
            if exposure > self.exposure_limits['single_chain']:
                breached.append(f"Chain {chain}: {exposure:.1%} > {self.exposure_limits['single_chain']:.1%}")
        
        return ExposureAnalysis(
            total_exposure=total_value,
            asset_exposures=asset_exposures,
            chain_exposures=chain_exposures,
            sector_exposures={},  # Would need sector mapping
            concentration_risk=concentration_risk,
            diversification_score=diversification_score,
            exposure_limits_breached=breached,
            timestamp=datetime.now()
        )




class RiskAssessmentModule:
    """
    AI-powered Risk Assessment Module for CrossFlow Phase 2
    Evaluates and manages risks associated with trading strategies and portfolio positions.
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
        
        # Initialize components
        self.risk_calculator = RiskCalculator()
        self.slippage_estimator = SlippageEstimator()
        self.exposure_monitor = ExposureMonitor()
        
        # Risk thresholds
        self.risk_thresholds = {
            RiskLevel.MINIMAL: 20,
            RiskLevel.LOW: 40,
            RiskLevel.MODERATE: 60,
            RiskLevel.HIGH: 80,
            RiskLevel.EXTREME: 100
        }
        
        # Alert thresholds
        self.alert_thresholds = {
            'var_threshold': 0.05,  # 5% VaR threshold
            'drawdown_threshold': 0.10,  # 10% drawdown threshold
            'volatility_threshold': 0.50,  # 50% annualized volatility
            'concentration_threshold': 0.30,  # 30% concentration
        }
        
        # Risk history
        self.risk_history: Dict[str, List[RiskAssessment]] = {}
        self.mitigation_history: Dict[str, List[MitigationStrategy]] = {}
        
        self.logger.info("Risk Assessment Module initialized")
    
    async def calculate_intent_risks(self, asset: str, chain: str,
                                    amount: float, price_history: np.ndarray,
                                    liquidity: float = 1000000.0) -> RiskAssessment:
        """
        Calculate comprehensive risk assessment for an intent
        Requirements: 5.1 - Comprehensive risk assessment
        """
        import uuid
        
        try:
            # Calculate returns
            if len(price_history) < 30:
                # Generate synthetic data if insufficient
                price_history = self._generate_synthetic_prices(100)
            
            returns = np.diff(price_history) / price_history[:-1]
            
            # Calculate risk metrics
            var = self.risk_calculator.calculate_var(returns)
            cvar = self.risk_calculator.calculate_cvar(returns)
            max_dd = self.risk_calculator.calculate_max_drawdown(price_history)
            volatility = self.risk_calculator.calculate_volatility(returns)
            sharpe = self.risk_calculator.calculate_sharpe_ratio(returns)
            sortino = self.risk_calculator.calculate_sortino_ratio(returns)
            
            # Estimate slippage
            spread = 0.001  # 0.1% default spread
            slippage = self.slippage_estimator.estimate_slippage(
                amount, liquidity, volatility, spread
            )
            
            # Calculate execution risk
            exec_risk = self.slippage_estimator.estimate_execution_risk(
                amount, liquidity, timedelta(hours=1)
            )
            
            # Build risk metrics
            risk_metrics = RiskMetrics(
                value_at_risk=var,
                conditional_var=cvar,
                max_drawdown=max_dd,
                volatility=volatility,
                sharpe_ratio=sharpe,
                sortino_ratio=sortino,
                beta=1.0,  # Would need market data
                correlation_risk=0.0,
                liquidity_risk=exec_risk,
                timestamp=datetime.now()
            )
            
            # Calculate risk breakdown
            risk_breakdown = {
                RiskType.MARKET: abs(var) * 100,
                RiskType.VOLATILITY: min(volatility * 50, 30),
                RiskType.LIQUIDITY: exec_risk * 30,
                RiskType.SLIPPAGE: slippage * 100,
                RiskType.EXECUTION: exec_risk * 20,
            }
            
            # Calculate overall risk score
            risk_score = sum(risk_breakdown.values())
            risk_score = min(risk_score, 100)
            
            # Determine risk level
            risk_level = self._determine_risk_level(risk_score)
            
            # Generate warnings
            warnings = self._generate_warnings(risk_metrics, risk_breakdown)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(risk_level, risk_breakdown)
            
            assessment = RiskAssessment(
                assessment_id=str(uuid.uuid4()),
                asset=asset,
                chain=chain,
                risk_level=risk_level,
                risk_score=risk_score,
                risk_metrics=risk_metrics,
                risk_breakdown=risk_breakdown,
                warnings=warnings,
                recommendations=recommendations,
                timestamp=datetime.now()
            )
            
            # Store in history
            key = f"{asset}_{chain}"
            if key not in self.risk_history:
                self.risk_history[key] = []
            self.risk_history[key].append(assessment)
            
            self.logger.info(f"Risk assessment for {asset} on {chain}: {risk_level.value} ({risk_score:.1f})")
            return assessment
            
        except Exception as e:
            self.logger.error(f"Risk calculation failed: {e}")
            raise
    
    async def recommend_risk_mitigation(self, risk_assessment: RiskAssessment) -> List[MitigationStrategy]:
        """
        Recommend risk mitigation strategies
        Requirements: 5.2 - Risk mitigation recommendations
        """
        import uuid
        
        strategies = []
        
        try:
            risk_breakdown = risk_assessment.risk_breakdown
            
            # Position sizing for high market risk
            if risk_breakdown.get(RiskType.MARKET, 0) > 15:
                strategies.append(MitigationStrategy(
                    strategy_id=str(uuid.uuid4()),
                    mitigation_type=MitigationType.POSITION_SIZING,
                    description="Reduce position size to limit market exposure",
                    expected_risk_reduction=0.20,
                    implementation_cost=0.0,
                    priority=1,
                    parameters={
                        'max_position_pct': 0.05,
                        'current_risk': risk_breakdown.get(RiskType.MARKET, 0)
                    },
                    timestamp=datetime.now()
                ))
            
            # Stop loss for high volatility
            if risk_breakdown.get(RiskType.VOLATILITY, 0) > 15:
                strategies.append(MitigationStrategy(
                    strategy_id=str(uuid.uuid4()),
                    mitigation_type=MitigationType.STOP_LOSS,
                    description="Set stop-loss to limit downside risk",
                    expected_risk_reduction=0.30,
                    implementation_cost=0.001,
                    priority=2,
                    parameters={
                        'stop_loss_pct': 0.05,
                        'trailing': True
                    },
                    timestamp=datetime.now()
                ))
            
            # Split execution for high slippage
            if risk_breakdown.get(RiskType.SLIPPAGE, 0) > 10:
                strategies.append(MitigationStrategy(
                    strategy_id=str(uuid.uuid4()),
                    mitigation_type=MitigationType.SPLIT_EXECUTION,
                    description="Split order into smaller chunks to reduce slippage",
                    expected_risk_reduction=0.40,
                    implementation_cost=0.002,
                    priority=1,
                    parameters={
                        'num_chunks': 5,
                        'time_between_chunks': 60
                    },
                    timestamp=datetime.now()
                ))
            
            # Timing adjustment for high execution risk
            if risk_breakdown.get(RiskType.EXECUTION, 0) > 10:
                strategies.append(MitigationStrategy(
                    strategy_id=str(uuid.uuid4()),
                    mitigation_type=MitigationType.TIMING_ADJUSTMENT,
                    description="Adjust execution timing to periods of higher liquidity",
                    expected_risk_reduction=0.25,
                    implementation_cost=0.0,
                    priority=3,
                    parameters={
                        'preferred_hours': [14, 15, 16],  # UTC
                        'avoid_hours': [0, 1, 2, 3, 4, 5]
                    },
                    timestamp=datetime.now()
                ))
            
            # Hedging for extreme risk
            if risk_assessment.risk_level in [RiskLevel.HIGH, RiskLevel.EXTREME]:
                strategies.append(MitigationStrategy(
                    strategy_id=str(uuid.uuid4()),
                    mitigation_type=MitigationType.HEDGING,
                    description="Consider hedging position with correlated assets",
                    expected_risk_reduction=0.35,
                    implementation_cost=0.005,
                    priority=2,
                    parameters={
                        'hedge_ratio': 0.5,
                        'hedge_assets': ['USDC', 'USDT']
                    },
                    timestamp=datetime.now()
                ))
            
            # Sort by priority
            strategies.sort(key=lambda x: x.priority)
            
            # Store in history
            key = f"{risk_assessment.asset}_{risk_assessment.chain}"
            if key not in self.mitigation_history:
                self.mitigation_history[key] = []
            self.mitigation_history[key].extend(strategies)
            
            return strategies
            
        except Exception as e:
            self.logger.error(f"Mitigation recommendation failed: {e}")
            return []
    
    async def monitor_portfolio_exposure(self, positions: List[Position]) -> ExposureAnalysis:
        """
        Monitor portfolio exposure
        Requirements: 5.3 - Portfolio exposure monitoring
        """
        try:
            exposure = self.exposure_monitor.calculate_exposure(positions)
            
            # Log warnings for breached limits
            for breach in exposure.exposure_limits_breached:
                self.logger.warning(f"Exposure limit breached: {breach}")
            
            return exposure
            
        except Exception as e:
            self.logger.error(f"Exposure monitoring failed: {e}")
            raise
    
    async def provide_realtime_monitoring(self, positions: List[Position],
                                         price_data: Dict[str, np.ndarray]) -> RealTimeRiskMonitoring:
        """
        Provide real-time risk monitoring
        Requirements: 5.4 - Real-time risk monitoring
        """
        import uuid
        
        try:
            position_risks = {}
            risk_alerts = []
            total_var = 0.0
            total_cvar = 0.0
            
            for position in positions:
                # Get price history for position
                key = f"{position.asset}_{position.chain}"
                prices = price_data.get(key, self._generate_synthetic_prices(100))
                
                # Calculate risk for position
                assessment = await self.calculate_intent_risks(
                    position.asset, position.chain,
                    position.size * position.current_price,
                    prices
                )
                position_risks[position.position_id] = assessment
                
                # Aggregate VaR (simplified - assumes independence)
                position_value = position.size * position.current_price
                total_var += abs(assessment.risk_metrics.value_at_risk) * position_value
                total_cvar += abs(assessment.risk_metrics.conditional_var) * position_value
                
                # Generate alerts
                if assessment.risk_level in [RiskLevel.HIGH, RiskLevel.EXTREME]:
                    risk_alerts.append(f"HIGH RISK: {position.asset} on {position.chain} - {assessment.risk_level.value}")
                
                for warning in assessment.warnings:
                    risk_alerts.append(warning)
            
            # Calculate total risk score
            if position_risks:
                total_risk_score = np.mean([r.risk_score for r in position_risks.values()])
            else:
                total_risk_score = 0.0
            
            # Calculate margin utilization (simplified)
            total_value = sum(p.size * p.current_price for p in positions)
            margin_utilization = min(total_value / 1000000, 1.0)  # Assume 1M margin
            
            return RealTimeRiskMonitoring(
                monitoring_id=str(uuid.uuid4()),
                positions=positions,
                total_risk_score=total_risk_score,
                risk_alerts=risk_alerts,
                position_risks=position_risks,
                portfolio_var=total_var,
                portfolio_cvar=total_cvar,
                margin_utilization=margin_utilization,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Real-time monitoring failed: {e}")
            raise
    
    async def adjust_for_risk_changes(self, position: Position,
                                     risk_assessment: RiskAssessment) -> PositionAdjustment:
        """
        Generate position adjustment recommendations based on risk changes
        Requirements: 5.5 - Automatic risk adjustment
        """
        import uuid
        
        try:
            adjustment_type = "hold"
            target_size = position.size
            reason = "Risk within acceptable limits"
            urgency = "low"
            
            # Determine adjustment based on risk level
            if risk_assessment.risk_level == RiskLevel.EXTREME:
                adjustment_type = "close"
                target_size = 0.0
                reason = "Extreme risk level - recommend closing position"
                urgency = "critical"
            
            elif risk_assessment.risk_level == RiskLevel.HIGH:
                adjustment_type = "reduce"
                target_size = position.size * 0.5
                reason = "High risk level - recommend reducing position by 50%"
                urgency = "high"
            
            elif risk_assessment.risk_level == RiskLevel.MODERATE:
                # Check specific risk factors
                if risk_assessment.risk_breakdown.get(RiskType.VOLATILITY, 0) > 20:
                    adjustment_type = "reduce"
                    target_size = position.size * 0.75
                    reason = "High volatility - recommend reducing position by 25%"
                    urgency = "medium"
                elif risk_assessment.risk_breakdown.get(RiskType.LIQUIDITY, 0) > 15:
                    adjustment_type = "hedge"
                    target_size = position.size
                    reason = "Liquidity risk - recommend hedging position"
                    urgency = "medium"
            
            return PositionAdjustment(
                adjustment_id=str(uuid.uuid4()),
                position_id=position.position_id,
                adjustment_type=adjustment_type,
                target_size=target_size,
                reason=reason,
                urgency=urgency,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Risk adjustment failed: {e}")
            raise
    
    def _determine_risk_level(self, risk_score: float) -> RiskLevel:
        """Determine risk level from score"""
        if risk_score < self.risk_thresholds[RiskLevel.MINIMAL]:
            return RiskLevel.MINIMAL
        elif risk_score < self.risk_thresholds[RiskLevel.LOW]:
            return RiskLevel.LOW
        elif risk_score < self.risk_thresholds[RiskLevel.MODERATE]:
            return RiskLevel.MODERATE
        elif risk_score < self.risk_thresholds[RiskLevel.HIGH]:
            return RiskLevel.HIGH
        else:
            return RiskLevel.EXTREME
    
    def _generate_warnings(self, metrics: RiskMetrics, 
                          breakdown: Dict[RiskType, float]) -> List[str]:
        """Generate risk warnings"""
        warnings = []
        
        if abs(metrics.value_at_risk) > self.alert_thresholds['var_threshold']:
            warnings.append(f"High VaR: {abs(metrics.value_at_risk):.2%} exceeds threshold")
        
        if abs(metrics.max_drawdown) > self.alert_thresholds['drawdown_threshold']:
            warnings.append(f"High drawdown risk: {abs(metrics.max_drawdown):.2%}")
        
        if metrics.volatility > self.alert_thresholds['volatility_threshold']:
            warnings.append(f"High volatility: {metrics.volatility:.2%} annualized")
        
        if breakdown.get(RiskType.LIQUIDITY, 0) > 20:
            warnings.append("Liquidity risk elevated - consider smaller position")
        
        if breakdown.get(RiskType.SLIPPAGE, 0) > 15:
            warnings.append("High slippage expected - consider split execution")
        
        return warnings
    
    def _generate_recommendations(self, risk_level: RiskLevel,
                                 breakdown: Dict[RiskType, float]) -> List[str]:
        """Generate risk recommendations"""
        recommendations = []
        
        if risk_level in [RiskLevel.HIGH, RiskLevel.EXTREME]:
            recommendations.append("Consider reducing position size")
            recommendations.append("Set stop-loss orders")
        
        if breakdown.get(RiskType.VOLATILITY, 0) > 15:
            recommendations.append("Wait for lower volatility period")
        
        if breakdown.get(RiskType.LIQUIDITY, 0) > 15:
            recommendations.append("Use limit orders instead of market orders")
        
        if breakdown.get(RiskType.SLIPPAGE, 0) > 10:
            recommendations.append("Split order into smaller chunks")
        
        if not recommendations:
            recommendations.append("Risk levels acceptable - proceed with caution")
        
        return recommendations
    
    def _generate_synthetic_prices(self, n: int) -> np.ndarray:
        """Generate synthetic price data for testing"""
        base = 1000
        returns = np.random.normal(0, 0.02, n)
        prices = [base]
        for r in returns:
            prices.append(prices[-1] * (1 + r))
        return np.array(prices)
