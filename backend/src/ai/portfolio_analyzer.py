"""
Phase 5: Portfolio Analyzer

AI-powered portfolio analysis:
- Portfolio metrics calculation
- Concentration risk detection
- Rebalancing recommendations
- Performance tracking
- Arbitrage suggestions
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime, timedelta
from enum import Enum

from src.services.advanced_price_oracle import price_oracle
from src.config.phase5_config import phase5_config, CHAIN_CONFIGS

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Portfolio risk levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TokenHolding:
    """A token holding in the portfolio"""
    token: str
    symbol: str
    chain_id: int
    amount: Decimal
    value_usd: Decimal
    price_usd: Decimal
    allocation_pct: float
    change_24h: float = 0.0


@dataclass
class PortfolioMetrics:
    """Portfolio metrics and analysis"""
    total_value_usd: Decimal
    holdings: List[TokenHolding]
    allocations: Dict[str, float]  # token -> percentage
    chain_distribution: Dict[str, float]  # chain -> percentage
    risk_score: float  # 0-100
    concentration_risk: RiskLevel
    largest_position_pct: float
    performance_24h: float
    performance_7d: float
    performance_30d: float
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_value_usd": str(self.total_value_usd),
            "holdings": [
                {
                    "token": h.token,
                    "symbol": h.symbol,
                    "chain_id": h.chain_id,
                    "amount": str(h.amount),
                    "value_usd": str(h.value_usd),
                    "price_usd": str(h.price_usd),
                    "allocation_pct": h.allocation_pct,
                    "change_24h": h.change_24h
                }
                for h in self.holdings
            ],
            "allocations": self.allocations,
            "chain_distribution": self.chain_distribution,
            "risk_score": self.risk_score,
            "concentration_risk": self.concentration_risk.value,
            "largest_position_pct": self.largest_position_pct,
            "performance_24h": self.performance_24h,
            "performance_7d": self.performance_7d,
            "performance_30d": self.performance_30d,
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown": self.max_drawdown
        }


@dataclass
class RebalanceAction:
    """A recommended rebalancing action"""
    action: str  # "buy" or "sell"
    token: str
    symbol: str
    chain_id: int
    amount: Decimal
    amount_usd: Decimal
    reason: str
    expected_improvement: float
    gas_cost_usd: Decimal
    priority: int  # 1 = highest
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "token": self.token,
            "symbol": self.symbol,
            "chain_id": self.chain_id,
            "amount": str(self.amount),
            "amount_usd": str(self.amount_usd),
            "reason": self.reason,
            "expected_improvement": self.expected_improvement,
            "gas_cost_usd": str(self.gas_cost_usd),
            "priority": self.priority
        }


@dataclass
class RebalanceRecommendation:
    """Complete rebalancing recommendation"""
    recommendations: List[RebalanceAction]
    current_risk_score: float
    projected_risk_score: float
    total_gas_cost_usd: Decimal
    expected_improvement: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "recommendations": [r.to_dict() for r in self.recommendations],
            "current_risk_score": self.current_risk_score,
            "projected_risk_score": self.projected_risk_score,
            "total_gas_cost_usd": str(self.total_gas_cost_usd),
            "expected_improvement": self.expected_improvement
        }


class PortfolioAnalyzer:
    """
    AI-powered portfolio analysis and optimization
    """
    
    def __init__(self):
        self.concentration_threshold = phase5_config.ai.concentration_risk_threshold
        self.rebalance_threshold = phase5_config.ai.rebalance_threshold
    
    async def analyze_portfolio(
        self,
        holdings: List[Dict[str, Any]]
    ) -> PortfolioMetrics:
        """
        Analyze a portfolio and calculate metrics
        
        Args:
            holdings: List of holdings with token, amount, chain_id
        
        Returns:
            PortfolioMetrics with analysis
        """
        # Get current prices for all tokens
        token_holdings = []
        total_value = Decimal("0")
        
        for holding in holdings:
            token = holding.get("token", "")
            symbol = holding.get("symbol", token)
            amount = Decimal(str(holding.get("amount", 0)))
            chain_id = holding.get("chain_id", 1)
            
            # Get price
            price_data = await price_oracle.get_price(f"{symbol}USDT")
            price = price_data.price if price_data else Decimal("0")
            change_24h = price_data.change_24h if price_data else 0.0
            
            value = amount * price
            total_value += value
            
            token_holdings.append(TokenHolding(
                token=token,
                symbol=symbol,
                chain_id=chain_id,
                amount=amount,
                value_usd=value,
                price_usd=price,
                allocation_pct=0,  # Calculate after total
                change_24h=change_24h
            ))
        
        # Calculate allocations
        allocations = {}
        chain_distribution = {}
        largest_position = 0.0
        
        for holding in token_holdings:
            if total_value > 0:
                allocation = float(holding.value_usd / total_value * 100)
                holding.allocation_pct = allocation
                allocations[holding.symbol] = allocation
                
                # Track largest position
                if allocation > largest_position:
                    largest_position = allocation
                
                # Chain distribution
                chain_name = CHAIN_CONFIGS.get(holding.chain_id, {})
                chain_name = chain_name.name if hasattr(chain_name, 'name') else f"Chain {holding.chain_id}"
                chain_distribution[chain_name] = chain_distribution.get(chain_name, 0) + allocation
        
        # Calculate risk metrics
        risk_score = self._calculate_risk_score(token_holdings, allocations)
        concentration_risk = self._assess_concentration_risk(largest_position)
        
        # Calculate performance (simplified - would use historical data)
        performance_24h = sum(
            h.change_24h * h.allocation_pct / 100 
            for h in token_holdings
        )
        
        return PortfolioMetrics(
            total_value_usd=total_value,
            holdings=token_holdings,
            allocations=allocations,
            chain_distribution=chain_distribution,
            risk_score=risk_score,
            concentration_risk=concentration_risk,
            largest_position_pct=largest_position,
            performance_24h=performance_24h,
            performance_7d=performance_24h * 3,  # Simplified
            performance_30d=performance_24h * 10,  # Simplified
        )
    
    def _calculate_risk_score(
        self,
        holdings: List[TokenHolding],
        allocations: Dict[str, float]
    ) -> float:
        """Calculate portfolio risk score (0-100, higher = riskier)"""
        if not holdings:
            return 0
        
        # Factors:
        # 1. Concentration (higher concentration = higher risk)
        # 2. Volatility of holdings
        # 3. Number of positions (fewer = higher risk)
        # 4. Chain diversification
        
        # Concentration risk (Herfindahl index)
        hhi = sum((a / 100) ** 2 for a in allocations.values())
        concentration_score = hhi * 100  # 0-100
        
        # Position count risk
        position_count = len(holdings)
        if position_count < 3:
            position_score = 80
        elif position_count < 5:
            position_score = 50
        elif position_count < 10:
            position_score = 30
        else:
            position_score = 10
        
        # Chain diversification
        chains = set(h.chain_id for h in holdings)
        if len(chains) < 2:
            chain_score = 60
        elif len(chains) < 4:
            chain_score = 30
        else:
            chain_score = 10
        
        # Weighted average
        risk_score = (
            concentration_score * 0.4 +
            position_score * 0.3 +
            chain_score * 0.3
        )
        
        return min(risk_score, 100)
    
    def _assess_concentration_risk(self, largest_position_pct: float) -> RiskLevel:
        """Assess concentration risk level"""
        if largest_position_pct >= 80:
            return RiskLevel.CRITICAL
        elif largest_position_pct >= 50:
            return RiskLevel.HIGH
        elif largest_position_pct >= 30:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    async def get_rebalance_recommendations(
        self,
        holdings: List[Dict[str, Any]],
        target_allocations: Optional[Dict[str, float]] = None,
        risk_tolerance: float = 0.5
    ) -> RebalanceRecommendation:
        """
        Generate rebalancing recommendations
        
        Args:
            holdings: Current holdings
            target_allocations: Target allocation percentages (optional)
            risk_tolerance: User's risk tolerance (0-1)
        
        Returns:
            RebalanceRecommendation with actions
        """
        # Analyze current portfolio
        metrics = await self.analyze_portfolio(holdings)
        
        # Generate default target allocations if not provided
        if not target_allocations:
            target_allocations = self._generate_target_allocations(
                metrics, risk_tolerance
            )
        
        recommendations = []
        total_gas = Decimal("0")
        
        # Compare current vs target
        for symbol, target_pct in target_allocations.items():
            current_pct = metrics.allocations.get(symbol, 0)
            diff = target_pct - current_pct
            
            if abs(diff) < self.rebalance_threshold:
                continue
            
            # Find holding
            holding = next(
                (h for h in metrics.holdings if h.symbol == symbol),
                None
            )
            
            if diff > 0:
                # Need to buy
                amount_usd = Decimal(str(abs(diff) / 100)) * metrics.total_value_usd
                gas_cost = Decimal("5")  # Estimated
                
                recommendations.append(RebalanceAction(
                    action="buy",
                    token=holding.token if holding else "",
                    symbol=symbol,
                    chain_id=holding.chain_id if holding else 1,
                    amount=amount_usd / holding.price_usd if holding and holding.price_usd > 0 else Decimal("0"),
                    amount_usd=amount_usd,
                    reason=f"Increase {symbol} allocation from {current_pct:.1f}% to {target_pct:.1f}%",
                    expected_improvement=abs(diff) * 0.1,
                    gas_cost_usd=gas_cost,
                    priority=1 if diff > 10 else 2
                ))
                total_gas += gas_cost
            else:
                # Need to sell
                amount_usd = Decimal(str(abs(diff) / 100)) * metrics.total_value_usd
                gas_cost = Decimal("5")
                
                recommendations.append(RebalanceAction(
                    action="sell",
                    token=holding.token if holding else "",
                    symbol=symbol,
                    chain_id=holding.chain_id if holding else 1,
                    amount=amount_usd / holding.price_usd if holding and holding.price_usd > 0 else Decimal("0"),
                    amount_usd=amount_usd,
                    reason=f"Reduce {symbol} allocation from {current_pct:.1f}% to {target_pct:.1f}%",
                    expected_improvement=abs(diff) * 0.1,
                    gas_cost_usd=gas_cost,
                    priority=1 if abs(diff) > 10 else 2
                ))
                total_gas += gas_cost
        
        # Sort by priority
        recommendations.sort(key=lambda r: r.priority)
        
        # Calculate projected improvement
        projected_risk = metrics.risk_score * 0.7  # Simplified
        
        return RebalanceRecommendation(
            recommendations=recommendations,
            current_risk_score=metrics.risk_score,
            projected_risk_score=projected_risk,
            total_gas_cost_usd=total_gas,
            expected_improvement=metrics.risk_score - projected_risk
        )
    
    def _generate_target_allocations(
        self,
        metrics: PortfolioMetrics,
        risk_tolerance: float
    ) -> Dict[str, float]:
        """Generate target allocations based on risk tolerance"""
        # Simple allocation strategy
        # Lower risk = more stablecoins, higher risk = more volatile assets
        
        targets = {}
        stablecoins = {"USDC", "USDT", "DAI", "BUSD"}
        major_assets = {"BTC", "ETH"}
        
        # Base allocations
        stable_target = 30 - (risk_tolerance * 25)  # 5-30%
        major_target = 40 + (risk_tolerance * 20)   # 40-60%
        alt_target = 100 - stable_target - major_target
        
        # Distribute among current holdings
        stable_holdings = [h for h in metrics.holdings if h.symbol in stablecoins]
        major_holdings = [h for h in metrics.holdings if h.symbol in major_assets]
        alt_holdings = [h for h in metrics.holdings if h.symbol not in stablecoins and h.symbol not in major_assets]
        
        # Assign targets
        for h in stable_holdings:
            targets[h.symbol] = stable_target / len(stable_holdings) if stable_holdings else 0
        
        for h in major_holdings:
            targets[h.symbol] = major_target / len(major_holdings) if major_holdings else 0
        
        for h in alt_holdings:
            targets[h.symbol] = alt_target / len(alt_holdings) if alt_holdings else 0
        
        return targets
    
    async def get_arbitrage_suggestions(
        self,
        holdings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Get arbitrage suggestions based on portfolio holdings
        """
        suggestions = []
        
        for holding in holdings:
            symbol = holding.get("symbol", "")
            
            # Check for arbitrage opportunities
            opportunities = await price_oracle.detect_arbitrage_opportunities(
                symbol, Decimal(str(holding.get("value_usd", 1000)))
            )
            
            for opp in opportunities:
                if opp.is_profitable:
                    suggestions.append({
                        "token": symbol,
                        "opportunity": opp.to_dict(),
                        "holding_amount": str(holding.get("amount", 0)),
                        "potential_profit": str(opp.net_profit_usd)
                    })
        
        # Sort by profit
        suggestions.sort(
            key=lambda s: Decimal(s["potential_profit"]),
            reverse=True
        )
        
        return suggestions[:5]  # Top 5 opportunities


# Global portfolio analyzer instance
portfolio_analyzer = PortfolioAnalyzer()
