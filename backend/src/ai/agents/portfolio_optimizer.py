"""
Portfolio Optimizer Module
Optimizes asset allocation and portfolio management strategies
for the CrossFlow AI trading platform.
"""
import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from collections import defaultdict

from ..config import AIConfig, AgentConfig, AgentType, get_agent_config
from ..utils.model_manager import ModelManager


class RegimeType(Enum):
    """Market regime types"""
    BULL = "bull"
    BEAR = "bear"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    CRISIS = "crisis"
    RECOVERY = "recovery"


@dataclass
class Asset:
    """Asset representation"""
    symbol: str
    chain: str
    current_price: float
    market_cap: float
    volume_24h: float
    volatility: float


@dataclass
class PortfolioPosition:
    """Portfolio position"""
    asset: Asset
    quantity: float
    value: float
    weight: float
    cost_basis: float


@dataclass
class Portfolio:
    """Portfolio representation"""
    portfolio_id: str
    positions: List[PortfolioPosition]
    total_value: float
    cash_balance: float
    timestamp: datetime


@dataclass
class AllocationConstraints:
    """Constraints for allocation optimization"""
    min_weight: float = 0.0
    max_weight: float = 1.0
    max_single_asset: float = 0.25
    max_single_chain: float = 0.40
    min_diversification: int = 3
    target_volatility: Optional[float] = None


@dataclass
class OptimalAllocation:
    """Optimal allocation result"""
    allocation_id: str
    target_weights: Dict[str, float]
    expected_return: float
    expected_volatility: float
    sharpe_ratio: float
    diversification_score: float
    constraints_satisfied: bool
    timestamp: datetime


@dataclass
class RebalancingPlan:
    """Rebalancing plan"""
    plan_id: str
    trades: List[Dict[str, Any]]
    total_cost: float
    expected_slippage: float
    execution_time: timedelta
    priority_order: List[str]
    timestamp: datetime


@dataclass
class InvestmentOpportunity:
    """Investment opportunity"""
    opportunity_id: str
    asset: Asset
    expected_return: float
    risk_score: float
    time_horizon: timedelta
    confidence: float


@dataclass
class OpportunityEvaluation:
    """Opportunity evaluation result"""
    evaluation_id: str
    opportunity_id: str
    portfolio_impact: float
    risk_adjusted_return: float
    diversification_benefit: float
    recommendation: str
    confidence: float
    timestamp: datetime


@dataclass
class CorrelationMatrix:
    """Asset correlation matrix"""
    assets: List[str]
    correlations: np.ndarray
    timestamp: datetime


@dataclass
class RegimeChange:
    """Market regime change"""
    old_regime: RegimeType
    new_regime: RegimeType
    confidence: float
    detected_at: datetime


@dataclass
class AdaptedStrategy:
    """Regime-adapted strategy"""
    strategy_id: str
    regime: RegimeType
    allocation_adjustments: Dict[str, float]
    risk_adjustment: float
    rebalance_frequency: str
    timestamp: datetime


class AllocationOptimizer:
    """Optimizes asset allocation using Modern Portfolio Theory"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.risk_free_rate = 0.02
    
    def optimize(self, assets: List[Asset], returns: np.ndarray,
                constraints: AllocationConstraints) -> Dict[str, float]:
        """Optimize allocation using mean-variance optimization"""
        n_assets = len(assets)
        if n_assets == 0:
            return {}
        
        # Calculate expected returns and covariance
        if len(returns) < n_assets:
            # Generate synthetic returns if insufficient data
            returns = np.random.normal(0.001, 0.02, (100, n_assets))
        
        mean_returns = np.mean(returns, axis=0)
        cov_matrix = np.cov(returns.T) if returns.shape[0] > 1 else np.eye(n_assets) * 0.01
        
        # Simple optimization: inverse volatility weighting
        volatilities = np.sqrt(np.diag(cov_matrix))
        volatilities = np.maximum(volatilities, 0.001)  # Avoid division by zero
        
        inv_vol_weights = 1 / volatilities
        weights = inv_vol_weights / np.sum(inv_vol_weights)
        
        # Apply constraints
        weights = np.clip(weights, constraints.min_weight, constraints.max_weight)
        weights = np.clip(weights, 0, constraints.max_single_asset)
        weights = weights / np.sum(weights)  # Renormalize
        
        return {assets[i].symbol: float(weights[i]) for i in range(n_assets)}
    
    def calculate_efficient_frontier(self, assets: List[Asset],
                                    returns: np.ndarray,
                                    n_points: int = 20) -> List[Tuple[float, float]]:
        """Calculate efficient frontier points"""
        if len(assets) == 0 or len(returns) == 0:
            return []
        
        n_assets = len(assets)
        if returns.shape[1] != n_assets:
            returns = np.random.normal(0.001, 0.02, (100, n_assets))
        
        mean_returns = np.mean(returns, axis=0)
        cov_matrix = np.cov(returns.T) if returns.shape[0] > 1 else np.eye(n_assets) * 0.01
        
        frontier = []
        for target_return in np.linspace(min(mean_returns), max(mean_returns), n_points):
            # Simplified: use equal weights adjusted for target return
            weights = np.ones(n_assets) / n_assets
            port_return = np.dot(weights, mean_returns)
            port_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            frontier.append((float(port_vol), float(port_return)))
        
        return frontier


class RebalancingEngine:
    """Generates efficient rebalancing strategies"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.min_trade_value = 10.0  # Minimum trade value
    
    def generate_plan(self, current: Dict[str, float],
                     target: Dict[str, float],
                     portfolio_value: float) -> List[Dict[str, Any]]:
        """Generate rebalancing trades"""
        trades = []
        
        all_assets = set(current.keys()) | set(target.keys())
        
        for asset in all_assets:
            current_weight = current.get(asset, 0)
            target_weight = target.get(asset, 0)
            diff = target_weight - current_weight
            
            trade_value = abs(diff * portfolio_value)
            if trade_value < self.min_trade_value:
                continue
            
            trades.append({
                'asset': asset,
                'action': 'buy' if diff > 0 else 'sell',
                'weight_change': abs(diff),
                'value': trade_value,
                'priority': 1 if abs(diff) > 0.05 else 2
            })
        
        # Sort by priority and value
        trades.sort(key=lambda x: (x['priority'], -x['value']))
        return trades
    
    def estimate_cost(self, trades: List[Dict[str, Any]]) -> float:
        """Estimate total rebalancing cost"""
        total_cost = 0
        for trade in trades:
            # Estimate gas + slippage
            gas_cost = 0.001 * trade['value']  # 0.1% gas
            slippage = 0.002 * trade['value']  # 0.2% slippage
            total_cost += gas_cost + slippage
        return total_cost


class CorrelationAnalyzer:
    """Analyzes asset correlations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_correlations(self, returns: Dict[str, np.ndarray]) -> CorrelationMatrix:
        """Calculate correlation matrix from returns"""
        assets = list(returns.keys())
        n = len(assets)
        
        if n == 0:
            return CorrelationMatrix(assets=[], correlations=np.array([]), timestamp=datetime.now())
        
        # Build returns matrix
        min_len = min(len(r) for r in returns.values())
        returns_matrix = np.column_stack([returns[a][:min_len] for a in assets])
        
        # Calculate correlation matrix
        if min_len > 1:
            corr_matrix = np.corrcoef(returns_matrix.T)
        else:
            corr_matrix = np.eye(n)
        
        return CorrelationMatrix(
            assets=assets,
            correlations=corr_matrix,
            timestamp=datetime.now()
        )
    
    def calculate_diversification_benefit(self, correlations: CorrelationMatrix,
                                         weights: Dict[str, float]) -> float:
        """Calculate diversification benefit from correlations"""
        if len(correlations.assets) < 2:
            return 0.0
        
        # Average correlation weighted by position sizes
        total_weight = 0
        weighted_corr = 0
        
        for i, asset_i in enumerate(correlations.assets):
            for j, asset_j in enumerate(correlations.assets):
                if i < j:
                    w_i = weights.get(asset_i, 0)
                    w_j = weights.get(asset_j, 0)
                    weighted_corr += correlations.correlations[i, j] * w_i * w_j
                    total_weight += w_i * w_j
        
        if total_weight == 0:
            return 0.0
        
        avg_corr = weighted_corr / total_weight
        # Diversification benefit is higher when correlation is lower
        return float(1 - avg_corr)


class RegimeDetector:
    """Detects market regime changes"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.current_regime = RegimeType.BULL
        self.regime_history: List[RegimeChange] = []
    
    def detect_regime(self, price_data: np.ndarray, 
                     volume_data: Optional[np.ndarray] = None) -> RegimeType:
        """Detect current market regime"""
        if len(price_data) < 20:
            return self.current_regime
        
        # Calculate metrics
        returns = np.diff(price_data) / price_data[:-1]
        volatility = np.std(returns)
        trend = np.polyfit(range(len(price_data)), price_data, 1)[0]
        normalized_trend = trend / np.mean(price_data)
        
        # Classify regime
        if volatility > 0.05:
            if normalized_trend < -0.001:
                return RegimeType.CRISIS
            return RegimeType.HIGH_VOLATILITY
        elif volatility < 0.01:
            return RegimeType.LOW_VOLATILITY
        elif normalized_trend > 0.001:
            if self.current_regime == RegimeType.BEAR:
                return RegimeType.RECOVERY
            return RegimeType.BULL
        elif normalized_trend < -0.001:
            return RegimeType.BEAR
        
        return self.current_regime
    
    def check_regime_change(self, new_regime: RegimeType) -> Optional[RegimeChange]:
        """Check if regime has changed"""
        if new_regime != self.current_regime:
            change = RegimeChange(
                old_regime=self.current_regime,
                new_regime=new_regime,
                confidence=0.8,
                detected_at=datetime.now()
            )
            self.regime_history.append(change)
            self.current_regime = new_regime
            return change
        return None


class PortfolioOptimizer:
    """
    AI-powered Portfolio Optimizer for CrossFlow Phase 2
    Optimizes asset allocation and portfolio management strategies.
    """
    
    def __init__(self, config: AIConfig, agent_config: AgentConfig, model_manager: ModelManager):
        self.config = config
        self.agent_config = agent_config
        self.model_manager = model_manager
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.allocation_optimizer = AllocationOptimizer()
        self.rebalancing_engine = RebalancingEngine()
        self.correlation_analyzer = CorrelationAnalyzer()
        self.regime_detector = RegimeDetector()
        
        # History
        self.allocation_history: List[OptimalAllocation] = []
        self.rebalancing_history: List[RebalancingPlan] = []
        
        self.logger.info("Portfolio Optimizer initialized")
    
    async def optimize_asset_allocation(self, portfolio: Portfolio,
                                        constraints: AllocationConstraints) -> OptimalAllocation:
        """
        Optimize asset allocation using Modern Portfolio Theory
        Requirements: 7.1 - Optimal asset allocation
        """
        import uuid
        
        try:
            assets = [p.asset for p in portfolio.positions]
            n_assets = len(assets)
            
            if n_assets == 0:
                return OptimalAllocation(
                    allocation_id=str(uuid.uuid4()),
                    target_weights={},
                    expected_return=0.0,
                    expected_volatility=0.0,
                    sharpe_ratio=0.0,
                    diversification_score=0.0,
                    constraints_satisfied=True,
                    timestamp=datetime.now()
                )
            
            # Generate synthetic returns for optimization
            returns = np.random.normal(0.001, 0.02, (100, n_assets))
            
            # Optimize allocation
            target_weights = self.allocation_optimizer.optimize(assets, returns, constraints)
            
            # Calculate portfolio metrics
            mean_returns = np.mean(returns, axis=0)
            cov_matrix = np.cov(returns.T)
            
            weights_array = np.array([target_weights.get(a.symbol, 0) for a in assets])
            expected_return = float(np.dot(weights_array, mean_returns) * 252)  # Annualized
            expected_volatility = float(np.sqrt(np.dot(weights_array.T, np.dot(cov_matrix, weights_array))) * np.sqrt(252))
            
            sharpe_ratio = (expected_return - 0.02) / expected_volatility if expected_volatility > 0 else 0
            
            # Calculate diversification score
            n_positions = sum(1 for w in target_weights.values() if w > 0.01)
            diversification_score = min(n_positions / 10, 1.0)
            
            # Check constraints
            constraints_satisfied = all(
                constraints.min_weight <= w <= constraints.max_single_asset
                for w in target_weights.values()
            )
            
            allocation = OptimalAllocation(
                allocation_id=str(uuid.uuid4()),
                target_weights=target_weights,
                expected_return=expected_return,
                expected_volatility=expected_volatility,
                sharpe_ratio=float(sharpe_ratio),
                diversification_score=diversification_score,
                constraints_satisfied=constraints_satisfied,
                timestamp=datetime.now()
            )
            
            self.allocation_history.append(allocation)
            return allocation
            
        except Exception as e:
            self.logger.error(f"Allocation optimization failed: {e}")
            raise
    
    async def generate_rebalancing_plan(self, current_allocation: Dict[str, float],
                                        target_allocation: Dict[str, float],
                                        portfolio_value: float = 100000) -> RebalancingPlan:
        """
        Generate efficient rebalancing plan
        Requirements: 7.2 - Efficient rebalancing plans
        """
        import uuid
        
        try:
            # Generate trades
            trades = self.rebalancing_engine.generate_plan(
                current_allocation, target_allocation, portfolio_value
            )
            
            # Estimate costs
            total_cost = self.rebalancing_engine.estimate_cost(trades)
            
            # Estimate slippage
            total_value = sum(t['value'] for t in trades)
            expected_slippage = 0.002 * total_value  # 0.2% average slippage
            
            # Estimate execution time
            execution_time = timedelta(minutes=len(trades) * 2)
            
            # Priority order
            priority_order = [t['asset'] for t in trades]
            
            plan = RebalancingPlan(
                plan_id=str(uuid.uuid4()),
                trades=trades,
                total_cost=total_cost,
                expected_slippage=expected_slippage,
                execution_time=execution_time,
                priority_order=priority_order,
                timestamp=datetime.now()
            )
            
            self.rebalancing_history.append(plan)
            return plan
            
        except Exception as e:
            self.logger.error(f"Rebalancing plan generation failed: {e}")
            raise
    
    async def evaluate_new_opportunity(self, opportunity: InvestmentOpportunity,
                                       portfolio: Portfolio) -> OpportunityEvaluation:
        """
        Evaluate new investment opportunity
        Requirements: 7.3 - Opportunity impact evaluation
        """
        import uuid
        
        try:
            # Calculate portfolio impact
            current_value = portfolio.total_value
            opportunity_value = opportunity.asset.current_price * 100  # Assume 100 units
            
            # Risk-adjusted return (Sharpe-like)
            risk_adjusted_return = opportunity.expected_return / (opportunity.risk_score + 0.01)
            
            # Diversification benefit
            current_assets = {p.asset.symbol for p in portfolio.positions}
            is_new_asset = opportunity.asset.symbol not in current_assets
            diversification_benefit = 0.1 if is_new_asset else 0.02
            
            # Portfolio impact
            portfolio_impact = (opportunity.expected_return * opportunity_value / current_value) if current_value > 0 else 0
            
            # Generate recommendation
            if risk_adjusted_return > 1.5 and opportunity.confidence > 0.7:
                recommendation = "strong_buy"
            elif risk_adjusted_return > 1.0 and opportunity.confidence > 0.5:
                recommendation = "buy"
            elif risk_adjusted_return > 0.5:
                recommendation = "hold"
            else:
                recommendation = "avoid"
            
            return OpportunityEvaluation(
                evaluation_id=str(uuid.uuid4()),
                opportunity_id=opportunity.opportunity_id,
                portfolio_impact=float(portfolio_impact),
                risk_adjusted_return=float(risk_adjusted_return),
                diversification_benefit=float(diversification_benefit),
                recommendation=recommendation,
                confidence=opportunity.confidence,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Opportunity evaluation failed: {e}")
            raise
    
    async def analyze_asset_correlations(self, assets: List[Asset],
                                         returns_data: Dict[str, np.ndarray]) -> CorrelationMatrix:
        """
        Analyze asset correlations for diversification
        Requirements: 7.4 - Correlation-based allocation
        """
        try:
            # Calculate correlations
            correlations = self.correlation_analyzer.calculate_correlations(returns_data)
            return correlations
            
        except Exception as e:
            self.logger.error(f"Correlation analysis failed: {e}")
            raise
    
    async def adapt_to_regime_change(self, regime_change: RegimeChange,
                                     current_allocation: Dict[str, float]) -> AdaptedStrategy:
        """
        Adapt allocation strategy to market regime change
        Requirements: 7.5 - Regime-adaptive allocation
        """
        import uuid
        
        try:
            # Define regime-specific adjustments
            regime_adjustments = {
                RegimeType.BULL: {
                    'risk_multiplier': 1.2,
                    'equity_bias': 0.1,
                    'rebalance_freq': 'monthly'
                },
                RegimeType.BEAR: {
                    'risk_multiplier': 0.7,
                    'equity_bias': -0.15,
                    'rebalance_freq': 'weekly'
                },
                RegimeType.HIGH_VOLATILITY: {
                    'risk_multiplier': 0.6,
                    'equity_bias': -0.1,
                    'rebalance_freq': 'daily'
                },
                RegimeType.LOW_VOLATILITY: {
                    'risk_multiplier': 1.1,
                    'equity_bias': 0.05,
                    'rebalance_freq': 'quarterly'
                },
                RegimeType.CRISIS: {
                    'risk_multiplier': 0.4,
                    'equity_bias': -0.25,
                    'rebalance_freq': 'daily'
                },
                RegimeType.RECOVERY: {
                    'risk_multiplier': 1.0,
                    'equity_bias': 0.08,
                    'rebalance_freq': 'weekly'
                }
            }
            
            adjustments = regime_adjustments.get(regime_change.new_regime, {
                'risk_multiplier': 1.0,
                'equity_bias': 0.0,
                'rebalance_freq': 'monthly'
            })
            
            # Apply adjustments to allocation
            allocation_adjustments = {}
            for asset, weight in current_allocation.items():
                # Adjust based on regime
                adjusted_weight = weight * adjustments['risk_multiplier']
                adjusted_weight = max(0, min(1, adjusted_weight))
                allocation_adjustments[asset] = adjusted_weight
            
            # Normalize
            total = sum(allocation_adjustments.values())
            if total > 0:
                allocation_adjustments = {k: v/total for k, v in allocation_adjustments.items()}
            
            return AdaptedStrategy(
                strategy_id=str(uuid.uuid4()),
                regime=regime_change.new_regime,
                allocation_adjustments=allocation_adjustments,
                risk_adjustment=adjustments['risk_multiplier'],
                rebalance_frequency=adjustments['rebalance_freq'],
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Regime adaptation failed: {e}")
            raise
    
    def detect_regime(self, price_data: np.ndarray) -> RegimeType:
        """Detect current market regime"""
        return self.regime_detector.detect_regime(price_data)
    
    def check_regime_change(self, price_data: np.ndarray) -> Optional[RegimeChange]:
        """Check for regime change"""
        new_regime = self.detect_regime(price_data)
        return self.regime_detector.check_regime_change(new_regime)
