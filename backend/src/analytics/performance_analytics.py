"""
Performance Analytics - Strategy Performance Tracking
Phase 4: Ecosystem & Compliance

Provides real-time analytics for strategy performance.
"""

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class DateRange:
    start: datetime
    end: datetime


@dataclass
class TradeAttribution:
    trade_id: str
    contribution_percent: float
    pnl: float
    trade_type: str
    timestamp: datetime


@dataclass
class BenchmarkComparison:
    strategy_id: str
    benchmark_name: str
    strategy_return: float
    benchmark_return: float
    alpha: float
    tracking_error: float
    period: DateRange


@dataclass
class DegradationAlert:
    strategy_id: str
    alert_type: str
    severity: str
    message: str
    current_value: float
    threshold: float
    detected_at: datetime


@dataclass
class FollowerAnalytics:
    strategy_id: str
    total_followers: int
    follower_growth_percent: float
    total_aum: float
    total_fees_earned: float
    avg_allocation: float
    period: DateRange


@dataclass
class StrategyAnalytics:
    strategy_id: str
    period: DateRange
    roi_percent: float
    max_drawdown_percent: float
    win_rate: float
    sharpe_ratio: float
    sortino_ratio: float
    benchmark_comparison: Dict[str, float]
    trade_attribution: List[TradeAttribution]
    follower_count: int
    follower_growth: float
    total_fees_earned: float


class PerformanceAnalytics:
    """
    Performance Analytics for strategy tracking.
    
    Validates: Requirements 10.1-10.6
    """
    
    DEGRADATION_THRESHOLDS = {
        "drawdown": 0.15,  # 15% max drawdown alert
        "sharpe_decline": 0.5,  # 50% Sharpe decline
        "win_rate_decline": 0.1,  # 10% win rate decline
    }
    
    BENCHMARKS = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "SPY": "sp500",
        "DeFi": "defi_index",
    }
    
    def __init__(self):
        self.strategy_data: Dict[str, Dict] = {}
        self.trade_history: Dict[str, List[Dict]] = {}
        self.follower_history: Dict[str, List[Dict]] = {}
        self.alerts: List[DegradationAlert] = []

    async def calculate_metrics(
        self,
        strategy_id: str,
        period: DateRange
    ) -> StrategyAnalytics:
        """
        Calculate real-time performance metrics.
        
        Property 35: Real-Time Metrics Calculation
        For any strategy, ROI, drawdown, win rate calculated in real-time.
        """
        trades = self.trade_history.get(strategy_id, [])
        period_trades = [
            t for t in trades
            if period.start <= t.get("timestamp", datetime.min) <= period.end
        ]
        
        # Calculate ROI
        roi = self._calculate_roi(period_trades)
        
        # Calculate max drawdown
        drawdown = self._calculate_max_drawdown(period_trades)
        
        # Calculate win rate
        win_rate = self._calculate_win_rate(period_trades)
        
        # Calculate Sharpe ratio
        returns = [t.get("return_pct", 0) for t in period_trades]
        sharpe = self._calculate_sharpe(returns)
        
        # Calculate Sortino ratio
        sortino = self._calculate_sortino(returns)
        
        # Get benchmark comparison
        benchmark_comp = await self.compare_to_benchmark(strategy_id, "ETH")
        
        # Get trade attribution
        attribution = await self.get_attribution(strategy_id)
        
        # Get follower data
        follower_data = self.strategy_data.get(strategy_id, {})
        
        return StrategyAnalytics(
            strategy_id=strategy_id,
            period=period,
            roi_percent=roi,
            max_drawdown_percent=drawdown,
            win_rate=win_rate,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            benchmark_comparison={
                benchmark_comp.benchmark_name: benchmark_comp.alpha
            } if benchmark_comp else {},
            trade_attribution=attribution[:10],  # Top 10
            follower_count=follower_data.get("followers", 0),
            follower_growth=follower_data.get("growth", 0),
            total_fees_earned=follower_data.get("fees", 0),
        )

    def _calculate_roi(self, trades: List[Dict]) -> float:
        """Calculate return on investment."""
        if not trades:
            return 0.0
        
        total_return = sum(t.get("pnl", 0) for t in trades)
        initial_value = trades[0].get("portfolio_value", 100000)
        
        return (total_return / initial_value) * 100 if initial_value > 0 else 0.0

    def _calculate_max_drawdown(self, trades: List[Dict]) -> float:
        """Calculate maximum drawdown."""
        if not trades:
            return 0.0
        
        peak = 0
        max_dd = 0
        cumulative = 0
        
        for trade in trades:
            cumulative += trade.get("pnl", 0)
            if cumulative > peak:
                peak = cumulative
            dd = (peak - cumulative) / peak if peak > 0 else 0
            max_dd = max(max_dd, dd)
        
        return max_dd * 100

    def _calculate_win_rate(self, trades: List[Dict]) -> float:
        """Calculate win rate."""
        if not trades:
            return 0.0
        
        wins = sum(1 for t in trades if t.get("pnl", 0) > 0)
        return (wins / len(trades)) * 100

    def _calculate_sharpe(self, returns: List[float], risk_free: float = 0.02) -> float:
        """Calculate Sharpe ratio."""
        if len(returns) < 2:
            return 0.0
        
        mean_return = sum(returns) / len(returns)
        excess = mean_return - (risk_free / 252)
        
        variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
        std = math.sqrt(variance) if variance > 0 else 0.001
        
        return (excess / std) * math.sqrt(252)

    def _calculate_sortino(self, returns: List[float], risk_free: float = 0.02) -> float:
        """Calculate Sortino ratio (downside deviation only)."""
        if len(returns) < 2:
            return 0.0
        
        mean_return = sum(returns) / len(returns)
        excess = mean_return - (risk_free / 252)
        
        downside = [r for r in returns if r < 0]
        if not downside:
            return 10.0  # No downside, excellent
        
        downside_var = sum(r ** 2 for r in downside) / len(downside)
        downside_std = math.sqrt(downside_var) if downside_var > 0 else 0.001
        
        return (excess / downside_std) * math.sqrt(252)

    async def compare_to_benchmark(
        self,
        strategy_id: str,
        benchmark: str
    ) -> BenchmarkComparison:
        """
        Compare strategy to benchmark.
        
        Property 36: Benchmark Comparison
        For any strategy analytics, includes benchmark comparison.
        """
        # Get strategy returns
        trades = self.trade_history.get(strategy_id, [])
        strategy_return = self._calculate_roi(trades)
        
        # Simulate benchmark returns
        benchmark_returns = {
            "BTC": 45.0,
            "ETH": 35.0,
            "SPY": 12.0,
            "DeFi": 25.0,
        }
        benchmark_return = benchmark_returns.get(benchmark, 10.0)
        
        # Calculate alpha
        alpha = strategy_return - benchmark_return
        
        # Calculate tracking error (simplified)
        tracking_error = abs(alpha) * 0.5
        
        return BenchmarkComparison(
            strategy_id=strategy_id,
            benchmark_name=benchmark,
            strategy_return=strategy_return,
            benchmark_return=benchmark_return,
            alpha=alpha,
            tracking_error=tracking_error,
            period=DateRange(
                start=datetime.utcnow() - timedelta(days=30),
                end=datetime.utcnow(),
            ),
        )

    async def get_attribution(
        self,
        strategy_id: str
    ) -> List[TradeAttribution]:
        """
        Get trade attribution analysis.
        
        Property 37: Trade Attribution Analysis
        For any strategy, attribution analysis identifying top trades available.
        """
        trades = self.trade_history.get(strategy_id, [])
        if not trades:
            return []
        
        total_pnl = sum(abs(t.get("pnl", 0)) for t in trades)
        if total_pnl == 0:
            return []
        
        attributions = []
        for trade in trades:
            pnl = trade.get("pnl", 0)
            contribution = (pnl / total_pnl) * 100 if total_pnl > 0 else 0
            
            attributions.append(TradeAttribution(
                trade_id=trade.get("trade_id", ""),
                contribution_percent=contribution,
                pnl=pnl,
                trade_type=trade.get("type", "swap"),
                timestamp=trade.get("timestamp", datetime.utcnow()),
            ))
        
        # Sort by absolute contribution
        return sorted(attributions, key=lambda x: abs(x.contribution_percent), reverse=True)

    async def detect_degradation(
        self,
        strategy_id: str
    ) -> Optional[DegradationAlert]:
        """
        Detect performance degradation.
        
        Property 38: Performance Degradation Alerting
        For any strategy with significant degradation, alerts publisher.
        """
        trades = self.trade_history.get(strategy_id, [])
        if len(trades) < 10:
            return None
        
        # Check recent vs historical performance
        recent = trades[-10:]
        historical = trades[:-10] if len(trades) > 10 else trades
        
        recent_win_rate = self._calculate_win_rate(recent)
        historical_win_rate = self._calculate_win_rate(historical)
        
        # Check for win rate decline
        if historical_win_rate > 0:
            decline = (historical_win_rate - recent_win_rate) / historical_win_rate
            if decline > self.DEGRADATION_THRESHOLDS["win_rate_decline"]:
                alert = DegradationAlert(
                    strategy_id=strategy_id,
                    alert_type="win_rate_decline",
                    severity="medium",
                    message=f"Win rate declined from {historical_win_rate:.1f}% to {recent_win_rate:.1f}%",
                    current_value=recent_win_rate,
                    threshold=historical_win_rate * (1 - self.DEGRADATION_THRESHOLDS["win_rate_decline"]),
                    detected_at=datetime.utcnow(),
                )
                self.alerts.append(alert)
                logger.warning(f"Degradation alert for {strategy_id}: {alert.message}")
                return alert
        
        # Check for drawdown
        drawdown = self._calculate_max_drawdown(recent)
        if drawdown > self.DEGRADATION_THRESHOLDS["drawdown"] * 100:
            alert = DegradationAlert(
                strategy_id=strategy_id,
                alert_type="excessive_drawdown",
                severity="high",
                message=f"Max drawdown of {drawdown:.1f}% exceeds threshold",
                current_value=drawdown,
                threshold=self.DEGRADATION_THRESHOLDS["drawdown"] * 100,
                detected_at=datetime.utcnow(),
            )
            self.alerts.append(alert)
            logger.warning(f"Degradation alert for {strategy_id}: {alert.message}")
            return alert
        
        return None

    async def get_follower_analytics(
        self,
        strategy_id: str
    ) -> FollowerAnalytics:
        """
        Get follower analytics for strategy.
        
        Property 39: Follower Analytics
        For any strategy, follower growth and fee revenue displayed.
        """
        history = self.follower_history.get(strategy_id, [])
        data = self.strategy_data.get(strategy_id, {})
        
        # Calculate growth
        if len(history) >= 2:
            old_count = history[0].get("count", 0)
            new_count = history[-1].get("count", 0)
            growth = ((new_count - old_count) / old_count * 100) if old_count > 0 else 0
        else:
            growth = 0
        
        return FollowerAnalytics(
            strategy_id=strategy_id,
            total_followers=data.get("followers", 0),
            follower_growth_percent=growth,
            total_aum=data.get("aum", 0),
            total_fees_earned=data.get("fees", 0),
            avg_allocation=data.get("avg_allocation", 0),
            period=DateRange(
                start=datetime.utcnow() - timedelta(days=30),
                end=datetime.utcnow(),
            ),
        )

    def record_trade(
        self,
        strategy_id: str,
        trade: Dict[str, Any]
    ) -> None:
        """Record a trade for analytics."""
        if strategy_id not in self.trade_history:
            self.trade_history[strategy_id] = []
        
        trade["timestamp"] = trade.get("timestamp", datetime.utcnow())
        self.trade_history[strategy_id].append(trade)

    def update_strategy_data(
        self,
        strategy_id: str,
        data: Dict[str, Any]
    ) -> None:
        """Update strategy metadata."""
        self.strategy_data[strategy_id] = data

    def record_follower_change(
        self,
        strategy_id: str,
        count: int
    ) -> None:
        """Record follower count change."""
        if strategy_id not in self.follower_history:
            self.follower_history[strategy_id] = []
        
        self.follower_history[strategy_id].append({
            "count": count,
            "timestamp": datetime.utcnow(),
        })
