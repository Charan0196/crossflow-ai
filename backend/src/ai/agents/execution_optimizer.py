"""
Execution Strategy Optimizer
Develops and optimizes execution strategies for cross-chain intents based on
market conditions, cost analysis, and timing optimization.
"""
import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import redis

from ..config import AIConfig, AgentConfig, AgentType
from ..utils.model_manager import ModelManager
from .market_intelligence import MarketIntelligenceEngine, MarketAnalysis


class ExecutionStrategy(Enum):
    """Types of execution strategies"""
    IMMEDIATE = "immediate"
    DELAYED = "delayed"
    SPLIT = "split"
    BATCH = "batch"
    ADAPTIVE = "adaptive"


class ExecutionPriority(Enum):
    """Execution priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class ExecutionPath:
    """Represents a possible execution path for an intent"""
    path_id: str
    source_chain: str
    target_chain: str
    intermediate_chains: List[str] = field(default_factory=list)
    estimated_cost: float = 0.0
    estimated_time: float = 0.0  # in seconds
    estimated_slippage: float = 0.0
    success_probability: float = 1.0
    gas_cost: float = 0.0
    bridge_fees: float = 0.0
    protocol_fees: float = 0.0
    total_cost: float = 0.0
    confidence_score: float = 0.0


@dataclass
class ExecutionTiming:
    """Optimal timing for execution"""
    recommended_time: datetime
    urgency_score: float  # 0-1 scale
    delay_benefit: float  # Expected benefit from delaying
    volatility_window: Tuple[datetime, datetime]
    market_conditions: Dict[str, Any]


@dataclass
class ExecutionPlan:
    """Complete execution plan for an intent"""
    plan_id: str
    intent_id: str
    strategy: ExecutionStrategy
    priority: ExecutionPriority
    execution_paths: List[ExecutionPath]
    timing: ExecutionTiming
    coordination_requirements: List[str] = field(default_factory=list)
    risk_assessment: Dict[str, float] = field(default_factory=dict)
    expected_outcome: Dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None


@dataclass
class IntentCoordination:
    """Coordination between multiple intents"""
    coordination_id: str
    intent_ids: List[str]
    coordination_type: str  # batch, sequence, parallel
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    resource_allocation: Dict[str, float] = field(default_factory=dict)
    execution_order: List[str] = field(default_factory=list)
    estimated_savings: float = 0.0
    coordination_overhead: float = 0.0
    
    # Enhanced coordination fields
    batching_opportunities: Dict[str, Any] = field(default_factory=dict)
    conflict_resolution_plan: Dict[str, Any] = field(default_factory=dict)


class ExecutionStrategyOptimizer:
    """
    AI-powered execution strategy optimizer that creates optimal execution plans
    for cross-chain intents based on market conditions and cost analysis.
    """
    
    def __init__(self, config: AIConfig, agent_config: AgentConfig, 
                 model_manager: ModelManager, market_intelligence: MarketIntelligenceEngine):
        self.config = config
        self.agent_config = agent_config
        self.model_manager = model_manager
        self.market_intelligence = market_intelligence
        self.logger = logging.getLogger(__name__)
        
        # Redis for caching and coordination
        self.redis_client = redis.Redis(
            host=config.redis_host,
            port=config.redis_port,
            db=config.redis_db,
            decode_responses=True
        )
        
        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Strategy cache
        self.strategy_cache: Dict[str, ExecutionPlan] = {}
        self.coordination_cache: Dict[str, IntentCoordination] = {}
        
        # Performance tracking
        self.strategy_performance: Dict[str, List[float]] = {}
        
        self.logger.info("Execution Strategy Optimizer initialized")
    
    async def generate_execution_strategy(self, intent_id: str, intent_data: Dict[str, Any],
                                        market_context: Optional[Dict[str, Any]] = None) -> ExecutionPlan:
        """
        Generate optimal execution strategy for a given intent
        
        Args:
            intent_id: Unique identifier for the intent
            intent_data: Intent details (asset, amount, source/target chains, etc.)
            market_context: Optional market context for strategy optimization
            
        Returns:
            Complete execution plan with optimal strategy
        """
        
        try:
            # Extract intent parameters
            asset = intent_data.get('asset')
            amount = intent_data.get('amount', 0)
            source_chain = intent_data.get('source_chain')
            target_chain = intent_data.get('target_chain')
            deadline = intent_data.get('deadline')
            priority = ExecutionPriority(intent_data.get('priority', 'normal'))
            
            if not all([asset, source_chain, target_chain]):
                raise ValueError("Missing required intent parameters")
            
            # Get market analysis for relevant chains
            market_analyses = await self._get_market_analyses([source_chain, target_chain], asset)
            
            # Generate execution paths
            execution_paths = await self._generate_execution_paths(
                source_chain, target_chain, asset, amount, market_analyses
            )
            
            # Optimize timing based on market conditions
            timing = await self._optimize_execution_timing(
                execution_paths, market_analyses, deadline, priority
            )
            
            # Select optimal strategy
            strategy = self._select_execution_strategy(
                execution_paths, timing, priority, amount
            )
            
            # Assess risks
            risk_assessment = await self._assess_execution_risks(
                execution_paths, market_analyses, timing
            )
            
            # Calculate expected outcome
            expected_outcome = self._calculate_expected_outcome(
                execution_paths, timing, risk_assessment
            )
            
            # Calculate overall confidence
            confidence_score = self._calculate_strategy_confidence(
                execution_paths, timing, risk_assessment, market_analyses
            )
            
            # Create execution plan
            plan = ExecutionPlan(
                plan_id=f"plan_{intent_id}_{int(datetime.now().timestamp())}",
                intent_id=intent_id,
                strategy=strategy,
                priority=priority,
                execution_paths=execution_paths,
                timing=timing,
                risk_assessment=risk_assessment,
                expected_outcome=expected_outcome,
                confidence_score=confidence_score,
                expires_at=datetime.now() + timedelta(hours=1)  # Plans expire after 1 hour
            )
            
            # Cache the plan
            self.strategy_cache[plan.plan_id] = plan
            
            self.logger.info(f"Generated execution strategy {plan.plan_id} for intent {intent_id}")
            return plan
            
        except Exception as e:
            self.logger.error(f"Failed to generate execution strategy for intent {intent_id}: {e}")
            raise
    
    async def _get_market_analyses(self, chains: List[str], asset: str) -> Dict[str, MarketAnalysis]:
        """Get market analyses for relevant chains"""
        
        analyses = {}
        
        for chain in chains:
            try:
                analysis = await self.market_intelligence.analyze_market(asset, chain)
                analyses[chain] = analysis
            except Exception as e:
                self.logger.warning(f"Failed to get market analysis for {asset} on {chain}: {e}")
        
        return analyses
    
    async def _generate_execution_paths(self, source_chain: str, target_chain: str,
                                      asset: str, amount: float,
                                      market_analyses: Dict[str, MarketAnalysis]) -> List[ExecutionPath]:
        """Generate possible execution paths"""
        
        paths = []
        
        # Direct path
        direct_path = await self._create_direct_path(
            source_chain, target_chain, asset, amount, market_analyses
        )
        paths.append(direct_path)
        
        # Multi-hop paths (through intermediate chains)
        intermediate_chains = ['ethereum', 'polygon', 'arbitrum', 'optimism']
        intermediate_chains = [c for c in intermediate_chains if c not in [source_chain, target_chain]]
        
        for intermediate in intermediate_chains[:2]:  # Limit to 2 intermediate chains
            multi_hop_path = await self._create_multi_hop_path(
                source_chain, target_chain, intermediate, asset, amount, market_analyses
            )
            if multi_hop_path:
                paths.append(multi_hop_path)
        
        # Sort paths by total cost
        paths.sort(key=lambda p: p.total_cost)
        
        return paths[:5]  # Return top 5 paths
    
    async def _create_direct_path(self, source_chain: str, target_chain: str,
                                asset: str, amount: float,
                                market_analyses: Dict[str, MarketAnalysis]) -> ExecutionPath:
        """Create direct execution path"""
        
        path_id = f"direct_{source_chain}_{target_chain}"
        
        # Estimate costs
        gas_cost = self._estimate_gas_cost(source_chain, target_chain, amount)
        bridge_fees = self._estimate_bridge_fees(source_chain, target_chain, amount)
        protocol_fees = self._estimate_protocol_fees(amount)
        slippage = self._estimate_slippage(asset, amount, market_analyses.get(source_chain))
        
        total_cost = gas_cost + bridge_fees + protocol_fees + (amount * slippage)
        
        # Estimate execution time
        execution_time = self._estimate_execution_time(source_chain, target_chain)
        
        # Calculate success probability
        success_probability = self._calculate_success_probability(
            source_chain, target_chain, market_analyses
        )
        
        # Calculate confidence score
        confidence_score = self._calculate_path_confidence(
            source_chain, target_chain, market_analyses, success_probability
        )
        
        return ExecutionPath(
            path_id=path_id,
            source_chain=source_chain,
            target_chain=target_chain,
            estimated_cost=total_cost,
            estimated_time=execution_time,
            estimated_slippage=slippage,
            success_probability=success_probability,
            gas_cost=gas_cost,
            bridge_fees=bridge_fees,
            protocol_fees=protocol_fees,
            total_cost=total_cost,
            confidence_score=confidence_score
        )
    
    async def _create_multi_hop_path(self, source_chain: str, target_chain: str,
                                   intermediate_chain: str, asset: str, amount: float,
                                   market_analyses: Dict[str, MarketAnalysis]) -> Optional[ExecutionPath]:
        """Create multi-hop execution path"""
        
        try:
            path_id = f"multihop_{source_chain}_{intermediate_chain}_{target_chain}"
            
            # First hop: source -> intermediate
            gas_cost_1 = self._estimate_gas_cost(source_chain, intermediate_chain, amount)
            bridge_fees_1 = self._estimate_bridge_fees(source_chain, intermediate_chain, amount)
            
            # Second hop: intermediate -> target
            gas_cost_2 = self._estimate_gas_cost(intermediate_chain, target_chain, amount)
            bridge_fees_2 = self._estimate_bridge_fees(intermediate_chain, target_chain, amount)
            
            total_gas_cost = gas_cost_1 + gas_cost_2
            total_bridge_fees = bridge_fees_1 + bridge_fees_2
            protocol_fees = self._estimate_protocol_fees(amount) * 1.2  # Higher fees for multi-hop
            
            # Estimate slippage for both hops
            slippage_1 = self._estimate_slippage(asset, amount, market_analyses.get(source_chain))
            slippage_2 = self._estimate_slippage(asset, amount, market_analyses.get(intermediate_chain))
            total_slippage = slippage_1 + slippage_2
            
            total_cost = total_gas_cost + total_bridge_fees + protocol_fees + (amount * total_slippage)
            
            # Estimate execution time (longer for multi-hop)
            execution_time = (
                self._estimate_execution_time(source_chain, intermediate_chain) +
                self._estimate_execution_time(intermediate_chain, target_chain) +
                300  # 5 minutes additional coordination time
            )
            
            # Calculate success probability (lower for multi-hop)
            success_prob_1 = self._calculate_success_probability(
                source_chain, intermediate_chain, market_analyses
            )
            success_prob_2 = self._calculate_success_probability(
                intermediate_chain, target_chain, market_analyses
            )
            success_probability = success_prob_1 * success_prob_2
            
            # Calculate confidence score
            confidence_score = self._calculate_path_confidence(
                source_chain, target_chain, market_analyses, success_probability
            ) * 0.9  # Slightly lower confidence for multi-hop
            
            return ExecutionPath(
                path_id=path_id,
                source_chain=source_chain,
                target_chain=target_chain,
                intermediate_chains=[intermediate_chain],
                estimated_cost=total_cost,
                estimated_time=execution_time,
                estimated_slippage=total_slippage,
                success_probability=success_probability,
                gas_cost=total_gas_cost,
                bridge_fees=total_bridge_fees,
                protocol_fees=protocol_fees,
                total_cost=total_cost,
                confidence_score=confidence_score
            )
            
        except Exception as e:
            self.logger.warning(f"Failed to create multi-hop path via {intermediate_chain}: {e}")
            return None
    
    def _estimate_gas_cost(self, source_chain: str, target_chain: str, amount: float) -> float:
        """Estimate gas costs for execution"""
        
        # Base gas costs by chain (in USD equivalent)
        base_costs = {
            'ethereum': 50.0,
            'polygon': 0.1,
            'arbitrum': 2.0,
            'optimism': 2.0,
            'bsc': 0.5,
            'avalanche': 1.0
        }
        
        source_cost = base_costs.get(source_chain.lower(), 10.0)
        target_cost = base_costs.get(target_chain.lower(), 10.0)
        
        # Scale with amount (larger amounts may require more gas)
        amount_multiplier = 1.0 + (amount / 1000000) * 0.1  # 10% increase per $1M
        
        return (source_cost + target_cost) * amount_multiplier
    
    def _estimate_bridge_fees(self, source_chain: str, target_chain: str, amount: float) -> float:
        """Estimate bridge fees"""
        
        # Bridge fee rates (percentage of amount)
        bridge_rates = {
            ('ethereum', 'polygon'): 0.001,
            ('ethereum', 'arbitrum'): 0.0005,
            ('ethereum', 'optimism'): 0.0005,
            ('polygon', 'bsc'): 0.002,
            ('arbitrum', 'optimism'): 0.0003,
        }
        
        # Default rate for unknown pairs
        default_rate = 0.003
        
        bridge_key = (source_chain.lower(), target_chain.lower())
        reverse_key = (target_chain.lower(), source_chain.lower())
        
        rate = bridge_rates.get(bridge_key, bridge_rates.get(reverse_key, default_rate))
        
        return amount * rate
    
    def _estimate_protocol_fees(self, amount: float) -> float:
        """Estimate protocol fees"""
        return amount * 0.001  # 0.1% protocol fee
    
    def _estimate_slippage(self, asset: str, amount: float, 
                          market_analysis: Optional[MarketAnalysis]) -> float:
        """Estimate slippage based on market conditions"""
        
        base_slippage = 0.003  # 0.3% base slippage
        
        if not market_analysis:
            return base_slippage
        
        # Adjust for volatility
        volatility_multiplier = 1.0 + market_analysis.volatility
        
        # Adjust for volume (lower relative volume = higher slippage)
        volume_multiplier = max(0.5, 2.0 - market_analysis.relative_volume)
        
        # Adjust for amount (larger amounts = higher slippage)
        amount_multiplier = 1.0 + (amount / 100000) * 0.001  # 0.1% per $100k
        
        return base_slippage * volatility_multiplier * volume_multiplier * amount_multiplier
    
    def _estimate_execution_time(self, source_chain: str, target_chain: str) -> float:
        """Estimate execution time in seconds"""
        
        # Base execution times by chain (in seconds)
        chain_times = {
            'ethereum': 900,    # 15 minutes
            'polygon': 120,     # 2 minutes
            'arbitrum': 300,    # 5 minutes
            'optimism': 300,    # 5 minutes
            'bsc': 180,         # 3 minutes
            'avalanche': 180    # 3 minutes
        }
        
        source_time = chain_times.get(source_chain.lower(), 600)
        target_time = chain_times.get(target_chain.lower(), 600)
        
        # Bridge time (additional time for cross-chain operations)
        bridge_time = 600  # 10 minutes base bridge time
        
        return source_time + target_time + bridge_time
    
    def _calculate_success_probability(self, source_chain: str, target_chain: str,
                                     market_analyses: Dict[str, MarketAnalysis]) -> float:
        """Calculate probability of successful execution"""
        
        # Base success rates by chain
        chain_reliability = {
            'ethereum': 0.98,
            'polygon': 0.95,
            'arbitrum': 0.96,
            'optimism': 0.96,
            'bsc': 0.93,
            'avalanche': 0.94
        }
        
        source_reliability = chain_reliability.get(source_chain.lower(), 0.90)
        target_reliability = chain_reliability.get(target_chain.lower(), 0.90)
        
        # Adjust for market conditions
        market_factor = 1.0
        
        for chain, analysis in market_analyses.items():
            if analysis.volatility_regime.value in ['high_volatility', 'extreme_volatility']:
                market_factor *= 0.95  # Reduce success probability in high volatility
        
        return source_reliability * target_reliability * market_factor
    
    def _calculate_path_confidence(self, source_chain: str, target_chain: str,
                                 market_analyses: Dict[str, MarketAnalysis],
                                 success_probability: float) -> float:
        """Calculate confidence score for execution path"""
        
        confidence_factors = []
        
        # Success probability factor
        confidence_factors.append(success_probability)
        
        # Market analysis confidence
        for analysis in market_analyses.values():
            confidence_factors.append(analysis.analysis_confidence)
        
        # Chain familiarity factor (higher for well-known chains)
        known_chains = ['ethereum', 'polygon', 'arbitrum', 'optimism']
        familiarity = 1.0
        if source_chain.lower() in known_chains:
            familiarity *= 1.1
        if target_chain.lower() in known_chains:
            familiarity *= 1.1
        
        confidence_factors.append(min(familiarity, 1.0))
        
        # Calculate overall confidence
        if confidence_factors:
            return sum(confidence_factors) / len(confidence_factors)
        else:
            return 0.5
    
    async def _optimize_execution_timing(self, execution_paths: List[ExecutionPath],
                                       market_analyses: Dict[str, MarketAnalysis],
                                       deadline: Optional[datetime],
                                       priority: ExecutionPriority) -> ExecutionTiming:
        """Optimize execution timing based on market conditions and volatility"""
        
        current_time = datetime.now()
        
        # Calculate urgency based on priority and deadline
        if deadline:
            time_to_deadline = (deadline - current_time).total_seconds()
            deadline_urgency = max(0.0, 1.0 - (time_to_deadline / 3600))  # 1 hour = max urgency
        else:
            deadline_urgency = 0.0  # No deadline urgency
        
        # Calculate priority-based urgency
        priority_urgency = {
            ExecutionPriority.LOW: 0.2,
            ExecutionPriority.NORMAL: 0.4,
            ExecutionPriority.HIGH: 0.7,
            ExecutionPriority.URGENT: 0.9
        }
        
        # Combine deadline and priority urgency (take the maximum)
        urgency_score = max(deadline_urgency, priority_urgency[priority])
        
        # Ensure urgent priority always has high urgency
        if priority == ExecutionPriority.URGENT:
            urgency_score = max(urgency_score, 0.8)
        
        urgency_score = min(urgency_score, 1.0)
        
        # Enhanced volatility-based timing optimization
        volatility_analysis = await self._analyze_volatility_patterns(market_analyses)
        timing_adjustment = await self._calculate_volatility_timing_adjustment(
            volatility_analysis, urgency_score, deadline, priority
        )
        
        # Apply dynamic execution scheduling
        optimal_timing = await self._apply_dynamic_execution_scheduling(
            timing_adjustment, execution_paths, market_analyses
        )
        
        # Calculate slippage minimization benefits
        slippage_optimization = await self._optimize_slippage_timing(
            execution_paths, volatility_analysis, optimal_timing
        )
        
        # Combine all timing factors
        recommended_time = optimal_timing['recommended_time']
        delay_benefit = optimal_timing['delay_benefit'] + slippage_optimization['slippage_reduction_benefit']
        
        # Balance urgency vs delay benefit
        if priority == ExecutionPriority.URGENT:  # Only urgent priority completely overrides volatility optimization
            recommended_time = current_time
            delay_benefit = 0.0
        elif urgency_score > 0.8:  # Very high urgency reduces but doesn't eliminate delay benefit
            if delay_benefit > 0.1:  # Preserve some delay benefit for high volatility
                delay_benefit *= 0.3  # Reduce delay benefit but don't eliminate it
            recommended_time = current_time
        
        # Define volatility window based on analysis
        volatility_window = volatility_analysis['optimal_execution_window']
        
        # Enhanced market conditions summary
        market_conditions = {
            'avg_volatility': volatility_analysis['current_volatility'],
            'volatility_trend': volatility_analysis['volatility_trend'],
            'volatility_regime': volatility_analysis['volatility_regime'],
            'high_volatility_chains': volatility_analysis['high_volatility_chains'],
            'market_sentiment': sum(
                analysis.sentiment_score for analysis in market_analyses.values()
            ) / len(market_analyses) if market_analyses else 0.0,
            'predicted_volatility_decrease': volatility_analysis['predicted_decrease_time'],
            'slippage_optimization_potential': slippage_optimization['potential_savings']
        }
        
        return ExecutionTiming(
            recommended_time=recommended_time,
            urgency_score=urgency_score,
            delay_benefit=delay_benefit,
            volatility_window=volatility_window,
            market_conditions=market_conditions
        )
    
    async def _analyze_volatility_patterns(self, market_analyses: Dict[str, MarketAnalysis]) -> Dict[str, Any]:
        """
        Analyze volatility patterns across chains to determine optimal execution timing
        
        Returns:
            Dictionary containing volatility analysis results
        """
        
        current_time = datetime.now()
        
        # Extract volatility data
        volatility_data = {}
        volatility_scores = []
        
        for chain, analysis in market_analyses.items():
            volatility_data[chain] = {
                'current_volatility': analysis.volatility,
                'volatility_regime': analysis.volatility_regime.value,
                'trend_strength': analysis.trend_strength,
                'volume_volatility': analysis.relative_volume
            }
            volatility_scores.append(analysis.volatility)
        
        # Calculate aggregate volatility metrics
        current_volatility = sum(volatility_scores) / len(volatility_scores) if volatility_scores else 0.5
        max_volatility = max(volatility_scores) if volatility_scores else 0.5
        min_volatility = min(volatility_scores) if volatility_scores else 0.5
        volatility_spread = max_volatility - min_volatility
        
        # Determine volatility trend
        volatility_trend = self._calculate_volatility_trend(market_analyses)
        
        # Classify volatility regime
        volatility_regime = self._classify_volatility_regime(current_volatility, volatility_spread)
        
        # Identify high volatility chains
        high_volatility_chains = [
            chain for chain, analysis in market_analyses.items()
            if analysis.volatility > 0.7 or analysis.volatility_regime.value in ['high_volatility', 'extreme_volatility']
        ]
        
        # Predict optimal execution window
        optimal_window = self._predict_optimal_execution_window(
            current_volatility, volatility_trend, volatility_regime
        )
        
        # Estimate when volatility might decrease
        predicted_decrease_time = self._predict_volatility_decrease(
            current_volatility, volatility_trend, market_analyses
        )
        
        return {
            'current_volatility': current_volatility,
            'max_volatility': max_volatility,
            'min_volatility': min_volatility,
            'volatility_spread': volatility_spread,
            'volatility_trend': volatility_trend,
            'volatility_regime': volatility_regime,
            'high_volatility_chains': high_volatility_chains,
            'optimal_execution_window': optimal_window,
            'predicted_decrease_time': predicted_decrease_time,
            'chain_volatility_data': volatility_data
        }
    
    def _calculate_volatility_trend(self, market_analyses: Dict[str, MarketAnalysis]) -> str:
        """Calculate overall volatility trend across markets"""
        
        increasing_count = 0
        decreasing_count = 0
        stable_count = 0
        
        for analysis in market_analyses.values():
            # Use trend strength as proxy for volatility direction
            if analysis.trend_strength > 0.6:
                if analysis.volatility > 0.6:
                    increasing_count += 1
                else:
                    stable_count += 1
            elif analysis.trend_strength < 0.3:
                decreasing_count += 1
            else:
                stable_count += 1
        
        total_markets = len(market_analyses)
        if total_markets == 0:
            return 'stable'
        
        increasing_ratio = increasing_count / total_markets
        decreasing_ratio = decreasing_count / total_markets
        
        if increasing_ratio > 0.6:
            return 'increasing'
        elif decreasing_ratio > 0.6:
            return 'decreasing'
        else:
            return 'stable'
    
    def _classify_volatility_regime(self, current_volatility: float, volatility_spread: float) -> str:
        """Classify the current volatility regime"""
        
        if current_volatility > 0.8 or volatility_spread > 0.5:
            return 'extreme_volatility'
        elif current_volatility > 0.6 or volatility_spread > 0.3:
            return 'high_volatility'
        elif current_volatility > 0.4 or volatility_spread > 0.2:
            return 'medium_volatility'
        else:
            return 'low_volatility'
    
    def _predict_optimal_execution_window(self, current_volatility: float, 
                                        volatility_trend: str, volatility_regime: str) -> Tuple[datetime, datetime]:
        """Predict the optimal execution window based on volatility analysis"""
        
        current_time = datetime.now()
        
        if volatility_regime == 'extreme_volatility':
            if volatility_trend == 'decreasing':
                # Wait for volatility to decrease
                start_time = current_time + timedelta(minutes=45)
                end_time = current_time + timedelta(hours=3)
            else:
                # Execute immediately if volatility is increasing
                start_time = current_time
                end_time = current_time + timedelta(minutes=15)
        
        elif volatility_regime == 'high_volatility':
            if volatility_trend == 'decreasing':
                # Short wait for volatility to decrease
                start_time = current_time + timedelta(minutes=20)
                end_time = current_time + timedelta(hours=2)
            else:
                # Execute soon but not immediately
                start_time = current_time + timedelta(minutes=5)
                end_time = current_time + timedelta(minutes=30)
        
        elif volatility_regime == 'medium_volatility':
            # Flexible execution window
            start_time = current_time + timedelta(minutes=10)
            end_time = current_time + timedelta(hours=1)
        
        else:  # low_volatility
            # Execute anytime - volatility is favorable
            start_time = current_time
            end_time = current_time + timedelta(hours=4)
        
        return (start_time, end_time)
    
    def _predict_volatility_decrease(self, current_volatility: float, volatility_trend: str,
                                   market_analyses: Dict[str, MarketAnalysis]) -> Optional[datetime]:
        """Predict when volatility might decrease to acceptable levels"""
        
        current_time = datetime.now()
        
        if current_volatility < 0.5:
            return None  # Already at acceptable levels
        
        # Base prediction on volatility trend and market conditions
        if volatility_trend == 'decreasing':
            # Volatility is already decreasing
            if current_volatility > 0.8:
                return current_time + timedelta(minutes=60)  # 1 hour for extreme volatility
            elif current_volatility > 0.6:
                return current_time + timedelta(minutes=30)  # 30 minutes for high volatility
            else:
                return current_time + timedelta(minutes=15)  # 15 minutes for medium volatility
        
        elif volatility_trend == 'stable':
            # Volatility might decrease naturally
            return current_time + timedelta(hours=2)  # 2 hours for natural decrease
        
        else:  # increasing
            # Volatility is increasing - longer wait expected
            return current_time + timedelta(hours=4)  # 4 hours for volatility to peak and decrease
    
    async def _calculate_volatility_timing_adjustment(self, volatility_analysis: Dict[str, Any],
                                                    urgency_score: float, 
                                                    deadline: Optional[datetime],
                                                    priority: ExecutionPriority) -> Dict[str, Any]:
        """Calculate timing adjustments based on volatility analysis"""
        
        current_time = datetime.now()
        current_volatility = volatility_analysis['current_volatility']
        volatility_regime = volatility_analysis['volatility_regime']
        volatility_trend = volatility_analysis['volatility_trend']
        
        # Base delay calculation
        if volatility_regime == 'extreme_volatility':
            base_delay = 3600  # 1 hour
            delay_benefit = 0.45  # Increased from 0.4
        elif volatility_regime == 'high_volatility':
            base_delay = 1800  # 30 minutes
            delay_benefit = 0.28  # Increased from 0.25
        elif volatility_regime == 'medium_volatility':
            base_delay = 600   # 10 minutes
            delay_benefit = 0.12  # Increased from 0.1
        else:  # low_volatility
            base_delay = 0
            delay_benefit = 0.0
        
        # Adjust based on volatility trend
        if volatility_trend == 'decreasing':
            # Volatility is decreasing - reduce delay
            base_delay = int(base_delay * 0.6)
            delay_benefit *= 1.2
        elif volatility_trend == 'increasing':
            # Volatility is increasing - increase delay or execute immediately
            if urgency_score < 0.75:  # Allow HIGH priority to still get some delay benefit
                base_delay = int(base_delay * 1.5)
                delay_benefit *= 0.8
            else:
                base_delay = 0  # Execute immediately if urgent
                delay_benefit = 0.0
        
        # Consider deadline constraints
        if deadline:
            time_to_deadline = (deadline - current_time).total_seconds()
            if base_delay > time_to_deadline * 0.5:  # Don't delay more than 50% of remaining time
                base_delay = int(time_to_deadline * 0.3)
                delay_benefit *= 0.7
        
        # Urgency override
        if priority == ExecutionPriority.URGENT:  # Only urgent priority completely overrides delay benefits
            base_delay = 0
            delay_benefit = 0.0
        elif urgency_score > 0.8:  # Very high urgency reduces delay but preserves some benefit
            base_delay = int(base_delay * 0.2)  # Reduce delay significantly
            if delay_benefit > 0.1:  # Preserve some delay benefit for high volatility
                delay_benefit *= 0.3
        
        recommended_time = current_time + timedelta(seconds=base_delay)
        
        return {
            'base_delay': base_delay,
            'delay_benefit': delay_benefit,
            'recommended_time': recommended_time,
            'volatility_factor': current_volatility,
            'trend_adjustment': volatility_trend
        }
    
    async def _apply_dynamic_execution_scheduling(self, timing_adjustment: Dict[str, Any],
                                                execution_paths: List[ExecutionPath],
                                                market_analyses: Dict[str, MarketAnalysis]) -> Dict[str, Any]:
        """Apply dynamic execution scheduling based on market conditions"""
        
        current_time = datetime.now()
        base_recommended_time = timing_adjustment['recommended_time']
        
        # Analyze execution path characteristics
        if not execution_paths:
            return {
                'recommended_time': base_recommended_time,
                'delay_benefit': timing_adjustment['delay_benefit'],
                'scheduling_confidence': 0.5
            }
        
        best_path = execution_paths[0]
        
        # Adjust timing based on path complexity
        if best_path.intermediate_chains:
            # Multi-hop paths benefit more from stable conditions
            if timing_adjustment['volatility_factor'] > 0.6:
                # Add extra delay for multi-hop in high volatility
                extra_delay = 900  # 15 minutes
                base_recommended_time += timedelta(seconds=extra_delay)
                delay_benefit = timing_adjustment['delay_benefit'] * 1.3
            else:
                delay_benefit = timing_adjustment['delay_benefit']
        else:
            # Direct paths are less sensitive to volatility but still benefit
            delay_benefit = timing_adjustment['delay_benefit'] * 0.9  # Less aggressive reduction
        
        # Consider gas cost optimization
        if best_path.gas_cost > 100:  # High gas cost transactions
            # Check if delaying might reduce gas costs
            gas_optimization_benefit = self._estimate_gas_cost_reduction_benefit(
                best_path, market_analyses
            )
            delay_benefit += gas_optimization_benefit
        
        # Calculate scheduling confidence
        scheduling_confidence = self._calculate_scheduling_confidence(
            timing_adjustment, execution_paths, market_analyses
        )
        
        return {
            'recommended_time': base_recommended_time,
            'delay_benefit': delay_benefit,
            'scheduling_confidence': scheduling_confidence,
            'gas_optimization_benefit': gas_optimization_benefit if 'gas_optimization_benefit' in locals() else 0.0
        }
    
    def _estimate_gas_cost_reduction_benefit(self, execution_path: ExecutionPath,
                                           market_analyses: Dict[str, MarketAnalysis]) -> float:
        """Estimate potential gas cost reduction from delaying execution"""
        
        # Simple heuristic: gas costs tend to be lower during off-peak hours
        current_hour = datetime.now().hour
        
        # Peak hours: 8-10 AM and 6-8 PM UTC (when markets are most active)
        if current_hour in [8, 9, 18, 19]:
            # Currently in peak hours - delaying might help
            potential_savings = execution_path.gas_cost * 0.2  # 20% potential savings
            return potential_savings * 0.1  # Convert to delay benefit (10% of savings)
        else:
            # Not in peak hours - minimal benefit from delaying
            return 0.0
    
    def _calculate_scheduling_confidence(self, timing_adjustment: Dict[str, Any],
                                       execution_paths: List[ExecutionPath],
                                       market_analyses: Dict[str, MarketAnalysis]) -> float:
        """Calculate confidence in the scheduling decision"""
        
        confidence_factors = []
        
        # Volatility prediction confidence
        volatility_factor = timing_adjustment['volatility_factor']
        if volatility_factor > 0.8 or volatility_factor < 0.3:
            # High or low volatility - more confident in predictions
            confidence_factors.append(0.8)
        else:
            # Medium volatility - less predictable
            confidence_factors.append(0.6)
        
        # Market analysis confidence
        if market_analyses:
            analysis_confidences = [analysis.analysis_confidence for analysis in market_analyses.values()]
            avg_analysis_confidence = sum(analysis_confidences) / len(analysis_confidences)
            confidence_factors.append(avg_analysis_confidence)
        
        # Path complexity confidence
        if execution_paths:
            best_path = execution_paths[0]
            if best_path.intermediate_chains:
                # Multi-hop paths are less predictable
                confidence_factors.append(0.6)
            else:
                # Direct paths are more predictable
                confidence_factors.append(0.8)
        
        # Trend consistency confidence
        trend_adjustment = timing_adjustment.get('trend_adjustment', 'stable')
        if trend_adjustment in ['increasing', 'decreasing']:
            # Clear trend - more confident
            confidence_factors.append(0.8)
        else:
            # Stable/unclear trend - less confident
            confidence_factors.append(0.6)
        
        # Calculate overall confidence
        if confidence_factors:
            return sum(confidence_factors) / len(confidence_factors)
        else:
            return 0.5
    
    async def _optimize_slippage_timing(self, execution_paths: List[ExecutionPath],
                                      volatility_analysis: Dict[str, Any],
                                      optimal_timing: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize timing to minimize slippage based on volatility patterns"""
        
        if not execution_paths:
            return {
                'slippage_reduction_benefit': 0.0,
                'potential_savings': 0.0,
                'optimal_slippage_window': None
            }
        
        best_path = execution_paths[0]
        current_slippage = best_path.estimated_slippage
        
        # Calculate potential slippage reduction from timing optimization
        volatility_regime = volatility_analysis['volatility_regime']
        volatility_trend = volatility_analysis['volatility_trend']
        
        if volatility_regime in ['extreme_volatility', 'high_volatility']:
            if volatility_trend == 'decreasing':
                # Waiting could significantly reduce slippage
                potential_slippage_reduction = current_slippage * 0.4  # 40% reduction
                slippage_reduction_benefit = 0.3
            elif volatility_trend == 'increasing':
                # Execute soon but still some optimization potential from timing
                potential_slippage_reduction = current_slippage * 0.1  # 10% reduction from optimal timing
                slippage_reduction_benefit = 0.05
            else:  # stable
                # Moderate benefit from waiting
                potential_slippage_reduction = current_slippage * 0.2  # 20% reduction
                slippage_reduction_benefit = 0.15
        
        elif volatility_regime == 'medium_volatility':
            # Small benefit from timing optimization
            potential_slippage_reduction = current_slippage * 0.1  # 10% reduction
            slippage_reduction_benefit = 0.05
        
        else:  # low_volatility
            # Minimal benefit - already optimal conditions
            potential_slippage_reduction = 0.0
            slippage_reduction_benefit = 0.0
        
        # Calculate monetary value of slippage savings
        # Use a more realistic amount estimation based on typical transaction sizes
        # For high volatility scenarios, assume larger amounts that would benefit from optimization
        if volatility_regime in ['extreme_volatility', 'high_volatility']:
            # Assume larger amounts for high volatility scenarios
            estimated_amount = max(best_path.total_cost / 0.005, 50000)  # At least $50K for high volatility
        else:
            estimated_amount = best_path.total_cost / 0.01  # Original estimation for lower volatility
        
        potential_savings = potential_slippage_reduction * estimated_amount
        
        # Determine optimal slippage window
        optimal_window = volatility_analysis['optimal_execution_window']
        
        return {
            'slippage_reduction_benefit': slippage_reduction_benefit,
            'potential_savings': potential_savings,
            'optimal_slippage_window': optimal_window,
            'current_slippage': current_slippage,
            'optimized_slippage': current_slippage - potential_slippage_reduction
        }
    
    def _select_execution_strategy(self, execution_paths: List[ExecutionPath],
                                 timing: ExecutionTiming, priority: ExecutionPriority,
                                 amount: float) -> ExecutionStrategy:
        """Select optimal execution strategy"""
        
        # Strategy selection logic
        if priority == ExecutionPriority.URGENT or timing.urgency_score > 0.8:
            return ExecutionStrategy.IMMEDIATE
        
        if timing.delay_benefit > 0.2:
            return ExecutionStrategy.DELAYED
        
        if amount > 1000000:  # Large amounts benefit from splitting
            return ExecutionStrategy.SPLIT
        
        if len(execution_paths) > 1 and execution_paths[0].total_cost > execution_paths[1].total_cost * 0.8:
            return ExecutionStrategy.ADAPTIVE
        
        return ExecutionStrategy.IMMEDIATE
    
    async def _assess_execution_risks(self, execution_paths: List[ExecutionPath],
                                    market_analyses: Dict[str, MarketAnalysis],
                                    timing: ExecutionTiming) -> Dict[str, float]:
        """Assess various execution risks"""
        
        risks = {}
        
        # Market risk (volatility-based)
        volatilities = [analysis.volatility for analysis in market_analyses.values()]
        avg_volatility = sum(volatilities) / len(volatilities) if volatilities else 0.5
        risks['market_risk'] = min(avg_volatility, 1.0)
        
        # Execution risk (based on path complexity and success probability)
        if execution_paths:
            best_path = execution_paths[0]
            execution_risk = 1.0 - best_path.success_probability
            if best_path.intermediate_chains:
                execution_risk *= 1.2  # Higher risk for multi-hop
            risks['execution_risk'] = min(execution_risk, 1.0)
        else:
            risks['execution_risk'] = 0.5
        
        # Timing risk (based on urgency and delay)
        timing_risk = timing.urgency_score * 0.5  # High urgency = higher timing risk
        if timing.delay_benefit > 0.1:
            timing_risk += 0.2  # Risk of missing optimal timing
        risks['timing_risk'] = min(timing_risk, 1.0)
        
        # Liquidity risk (based on market conditions)
        liquidity_risk = 0.1  # Base liquidity risk
        for analysis in market_analyses.values():
            if analysis.relative_volume < 0.5:  # Low volume
                liquidity_risk += 0.2
        risks['liquidity_risk'] = min(liquidity_risk, 1.0)
        
        # Overall risk
        risks['overall_risk'] = sum(risks.values()) / len(risks)
        
        return risks
    
    def _calculate_expected_outcome(self, execution_paths: List[ExecutionPath],
                                  timing: ExecutionTiming,
                                  risk_assessment: Dict[str, float]) -> Dict[str, Any]:
        """Calculate expected execution outcome"""
        
        if not execution_paths:
            return {'success_probability': 0.0, 'expected_cost': 0.0}
        
        best_path = execution_paths[0]
        
        # Adjust success probability based on risks
        adjusted_success_prob = best_path.success_probability * (1.0 - risk_assessment.get('overall_risk', 0.5))
        
        # Expected cost (including risk premium)
        risk_premium = best_path.total_cost * risk_assessment.get('overall_risk', 0.0) * 0.1
        expected_cost = best_path.total_cost + risk_premium
        
        # Expected execution time
        timing_delay = 0 if timing.urgency_score > 0.7 else (timing.recommended_time - datetime.now()).total_seconds()
        expected_time = best_path.estimated_time + timing_delay
        
        return {
            'success_probability': adjusted_success_prob,
            'expected_cost': expected_cost,
            'expected_time': expected_time,
            'cost_savings_potential': timing.delay_benefit * best_path.total_cost,
            'risk_premium': risk_premium
        }
    
    def _calculate_strategy_confidence(self, execution_paths: List[ExecutionPath],
                                     timing: ExecutionTiming,
                                     risk_assessment: Dict[str, float],
                                     market_analyses: Dict[str, MarketAnalysis]) -> float:
        """Calculate overall strategy confidence with learning adjustments"""
        
        confidence_factors = []
        
        # Path confidence
        if execution_paths:
            path_confidences = [path.confidence_score for path in execution_paths]
            avg_path_confidence = sum(path_confidences) / len(path_confidences)
            confidence_factors.append(avg_path_confidence)
        
        # Market analysis confidence
        if market_analyses:
            market_confidences = [analysis.analysis_confidence for analysis in market_analyses.values()]
            avg_market_confidence = sum(market_confidences) / len(market_confidences)
            confidence_factors.append(avg_market_confidence)
        
        # Risk-adjusted confidence
        overall_risk = risk_assessment.get('overall_risk', 0.5)
        risk_adjusted_confidence = 1.0 - overall_risk
        confidence_factors.append(risk_adjusted_confidence)
        
        # Timing confidence
        timing_confidence = 1.0 - abs(timing.urgency_score - 0.5)  # Optimal at medium urgency
        confidence_factors.append(timing_confidence)
        
        # Calculate base confidence
        if confidence_factors:
            base_confidence = sum(confidence_factors) / len(confidence_factors)
        else:
            base_confidence = 0.5
        
        # Apply learning adjustments if available
        if execution_paths:
            best_path = execution_paths[0]
            strategy_key = f"unknown_{best_path.source_chain}_{best_path.target_chain}"
            
            # Apply strategy adjustments from learning
            _, _, _, adjusted_confidence = self.apply_strategy_adjustments(
                strategy_key, 0.0, 0.0, 0.0, base_confidence
            )
            
            # Apply performance-based adjustments
            performance_stats = self.get_strategy_performance_stats()
            if strategy_key in performance_stats:
                stats = performance_stats[strategy_key]
                
                # Boost confidence for well-performing strategies
                if stats['avg_performance'] > 0.8:
                    adjusted_confidence *= 1.1
                elif stats['avg_performance'] < 0.6:
                    adjusted_confidence *= 0.9
                
                # Consider recent trend
                if stats['recent_trend'] == 'improving':
                    adjusted_confidence *= 1.05
                elif stats['recent_trend'] == 'declining':
                    adjusted_confidence *= 0.95
            
            return min(1.0, max(0.0, adjusted_confidence))
        
        return base_confidence
    
    async def run_periodic_learning_update(self) -> None:
        """Run periodic learning updates (should be called regularly)"""
        
        try:
            # Update strategy models based on performance
            await self.update_strategy_models()
            
            # Clean up old performance data
            self._cleanup_old_performance_data()
            
            # Log learning statistics
            stats = self.get_strategy_performance_stats()
            self.logger.info(f"Learning update completed. Tracking {len(stats)} strategy variants")
            
            # Log to MLflow
            try:
                import mlflow
                with mlflow.start_run(run_name="periodic_learning_update"):
                    mlflow.log_metric("tracked_strategies", len(stats))
                    
                    # Log average performance by strategy
                    for strategy_key, data in stats.items():
                        mlflow.log_metric(f"avg_perf_{strategy_key}", data['avg_performance'])
                        mlflow.log_metric(f"exec_count_{strategy_key}", data['execution_count'])
                        
            except Exception as e:
                self.logger.warning(f"Failed to log learning update to MLflow: {e}")
                
        except Exception as e:
            self.logger.error(f"Failed to run periodic learning update: {e}")
    
    def _cleanup_old_performance_data(self) -> None:
        """Clean up old performance data to prevent memory bloat"""
        
        try:
            current_time = datetime.now()
            cutoff_time = current_time - timedelta(days=30)  # Keep 30 days of data
            
            # This is a simplified cleanup - in a real system, you'd want to 
            # store timestamps with performance data and clean based on age
            for strategy_key in list(self.strategy_performance.keys()):
                performances = self.strategy_performance[strategy_key]
                
                # Keep only recent data (last 200 executions max)
                if len(performances) > 200:
                    self.strategy_performance[strategy_key] = performances[-200:]
            
            self.logger.debug("Cleaned up old performance data")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old performance data: {e}")
    
    async def shutdown(self):
        """Shutdown the execution strategy optimizer"""
        
        try:
            # Close Redis connection
            self.redis_client.close()
            
            # Shutdown thread pool
            self.executor.shutdown(wait=True)
            
            self.logger.info("Execution Strategy Optimizer shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
    
    async def coordinate_multiple_intents(self, intent_plans: List[ExecutionPlan]) -> IntentCoordination:
        """
        Coordinate execution of multiple intents for efficiency gains
        
        Args:
            intent_plans: List of execution plans to coordinate
            
        Returns:
            Coordination plan with optimized execution order and resource allocation
        """
        
        if len(intent_plans) < 2:
            raise ValueError("Need at least 2 intents for coordination")
        
        try:
            coordination_id = f"coord_{int(datetime.now().timestamp())}"
            intent_ids = [plan.intent_id for plan in intent_plans]
            
            # Enhanced intent dependency analysis and ordering
            dependencies = await self._analyze_intent_dependencies_enhanced(intent_plans)
            
            # Analyze coordination opportunities
            coordination_type = self._determine_coordination_type(intent_plans)
            
            # Implement execution batching for efficiency
            batching_opportunities = await self._identify_batching_opportunities(intent_plans)
            
            # Optimize execution order considering dependencies and batching
            execution_order = await self._optimize_execution_order_enhanced(
                intent_plans, dependencies, batching_opportunities
            )
            
            # Create resource allocation optimization
            resource_allocation = await self._optimize_resource_allocation_enhanced(
                intent_plans, coordination_type, batching_opportunities
            )
            
            # Add coordination conflict resolution
            conflict_resolution_plan = await self._create_conflict_resolution_plan(
                intent_plans, dependencies, resource_allocation
            )
            
            # Calculate coordination benefits
            estimated_savings = self._calculate_coordination_savings(intent_plans, coordination_type)
            coordination_overhead = self._calculate_coordination_overhead(intent_plans, coordination_type)
            
            coordination = IntentCoordination(
                coordination_id=coordination_id,
                intent_ids=intent_ids,
                coordination_type=coordination_type,
                dependencies=dependencies,
                resource_allocation=resource_allocation,
                execution_order=execution_order,
                estimated_savings=estimated_savings,
                coordination_overhead=coordination_overhead
            )
            
            # Add enhanced coordination metadata
            coordination.batching_opportunities = batching_opportunities
            coordination.conflict_resolution_plan = conflict_resolution_plan
            
            # Cache coordination plan
            self.coordination_cache[coordination_id] = coordination
            
            self.logger.info(f"Created enhanced coordination plan {coordination_id} for {len(intent_ids)} intents")
            return coordination
            
        except Exception as e:
            self.logger.error(f"Failed to coordinate intents: {e}")
            raise
    
    async def _analyze_intent_dependencies_enhanced(self, intent_plans: List[ExecutionPlan]) -> Dict[str, Any]:
        """
        Enhanced intent dependency analysis including resource conflicts, timing dependencies,
        and chain utilization conflicts
        """
        
        dependencies = {
            'resource_dependencies': {},
            'timing_dependencies': {},
            'chain_dependencies': {},
            'priority_dependencies': {},
            'execution_graph': {}
        }
        
        for i, plan_a in enumerate(intent_plans):
            plan_a_id = plan_a.intent_id
            dependencies['execution_graph'][plan_a_id] = {
                'depends_on': [],
                'blocks': [],
                'can_parallel': []
            }
        
        # Initialize execution graph for all plans first
        for plan in intent_plans:
            plan_id = plan.intent_id
            if plan_id not in dependencies['execution_graph']:
                dependencies['execution_graph'][plan_id] = {
                    'depends_on': [],
                    'blocks': [],
                    'can_parallel': []
                }
        
        # Now analyze dependencies between all pairs
        for i, plan_a in enumerate(intent_plans):
            plan_a_id = plan_a.intent_id
            
            for j, plan_b in enumerate(intent_plans):
                if i >= j:
                    continue
                
                plan_b_id = plan_b.intent_id
                
                # Analyze resource conflicts
                resource_conflict = await self._analyze_resource_conflict(plan_a, plan_b)
                if resource_conflict['has_conflict']:
                    if resource_conflict['severity'] == 'high':
                        # High severity - must be sequential
                        if self._priority_to_numeric(plan_a.priority) > self._priority_to_numeric(plan_b.priority):
                            dependencies['resource_dependencies'][plan_b_id] = dependencies['resource_dependencies'].get(plan_b_id, [])
                            dependencies['resource_dependencies'][plan_b_id].append(plan_a_id)
                            dependencies['execution_graph'][plan_b_id]['depends_on'].append(plan_a_id)
                            dependencies['execution_graph'][plan_a_id]['blocks'].append(plan_b_id)
                        else:
                            dependencies['resource_dependencies'][plan_a_id] = dependencies['resource_dependencies'].get(plan_a_id, [])
                            dependencies['resource_dependencies'][plan_a_id].append(plan_b_id)
                            dependencies['execution_graph'][plan_a_id]['depends_on'].append(plan_b_id)
                            dependencies['execution_graph'][plan_b_id]['blocks'].append(plan_a_id)
                    else:
                        # Low severity - can potentially run in parallel with coordination
                        dependencies['execution_graph'][plan_a_id]['can_parallel'].append(plan_b_id)
                        dependencies['execution_graph'][plan_b_id]['can_parallel'].append(plan_a_id)
                
                # Analyze timing dependencies
                timing_conflict = self._analyze_timing_dependency(plan_a, plan_b)
                if timing_conflict['has_dependency']:
                    dependencies['timing_dependencies'][timing_conflict['dependent']] = dependencies['timing_dependencies'].get(timing_conflict['dependent'], [])
                    dependencies['timing_dependencies'][timing_conflict['dependent']].append(timing_conflict['prerequisite'])
                
                # Analyze chain utilization conflicts
                chain_conflict = self._analyze_chain_dependency(plan_a, plan_b)
                if chain_conflict['has_conflict']:
                    dependencies['chain_dependencies'][chain_conflict['conflicted_chain']] = dependencies['chain_dependencies'].get(chain_conflict['conflicted_chain'], [])
                    dependencies['chain_dependencies'][chain_conflict['conflicted_chain']].extend([plan_a_id, plan_b_id])
                
                # Analyze priority-based dependencies
                priority_dependency = self._analyze_priority_dependency(plan_a, plan_b)
                if priority_dependency['has_dependency']:
                    dependencies['priority_dependencies'][priority_dependency['lower_priority']] = dependencies['priority_dependencies'].get(priority_dependency['lower_priority'], [])
                    dependencies['priority_dependencies'][priority_dependency['lower_priority']].append(priority_dependency['higher_priority'])
        
        return dependencies
    
    async def _analyze_resource_conflict(self, plan_a: ExecutionPlan, plan_b: ExecutionPlan) -> Dict[str, Any]:
        """Analyze resource conflicts between two execution plans"""
        
        conflict_analysis = {
            'has_conflict': False,
            'severity': 'none',
            'conflict_type': [],
            'resolution_strategy': None
        }
        
        if not plan_a.execution_paths or not plan_b.execution_paths:
            return conflict_analysis
        
        path_a = plan_a.execution_paths[0]
        path_b = plan_b.execution_paths[0]
        
        # Check for same chain usage
        chains_a = {path_a.source_chain, path_a.target_chain}
        chains_b = {path_b.source_chain, path_b.target_chain}
        common_chains = chains_a.intersection(chains_b)
        
        if common_chains:
            conflict_analysis['has_conflict'] = True
            conflict_analysis['conflict_type'].append('chain_overlap')
            
            # Check timing overlap
            time_diff = abs((plan_a.timing.recommended_time - plan_b.timing.recommended_time).total_seconds())
            
            if time_diff < 1800:  # Within 30 minutes
                conflict_analysis['severity'] = 'high'
                conflict_analysis['resolution_strategy'] = 'sequential_execution'
            elif time_diff < 3600:  # Within 1 hour
                conflict_analysis['severity'] = 'medium'
                conflict_analysis['resolution_strategy'] = 'staggered_execution'
            else:
                conflict_analysis['severity'] = 'low'
                conflict_analysis['resolution_strategy'] = 'parallel_with_monitoring'
        
        # Check for gas price competition
        if (path_a.gas_cost > 50 and path_b.gas_cost > 50 and 
            abs((plan_a.timing.recommended_time - plan_b.timing.recommended_time).total_seconds()) < 600):
            conflict_analysis['has_conflict'] = True
            conflict_analysis['conflict_type'].append('gas_competition')
            if conflict_analysis['severity'] == 'none':
                conflict_analysis['severity'] = 'medium'
                conflict_analysis['resolution_strategy'] = 'gas_optimization'
        
        # Check for liquidity competition
        if (common_chains and 
            any(analysis.relative_volume < 0.7 for analysis in []) and  # Would need market analysis
            time_diff < 900):  # Within 15 minutes
            conflict_analysis['has_conflict'] = True
            conflict_analysis['conflict_type'].append('liquidity_competition')
            conflict_analysis['severity'] = 'high'
            conflict_analysis['resolution_strategy'] = 'sequential_execution'
        
        return conflict_analysis
    
    def _analyze_timing_dependency(self, plan_a: ExecutionPlan, plan_b: ExecutionPlan) -> Dict[str, Any]:
        """Analyze timing dependencies between execution plans"""
        
        dependency_analysis = {
            'has_dependency': False,
            'prerequisite': None,
            'dependent': None,
            'dependency_type': None,
            'minimum_delay': 0
        }
        
        # Check if one plan should wait for the other based on market conditions
        urgency_a = plan_a.timing.urgency_score
        urgency_b = plan_b.timing.urgency_score
        
        # High urgency plans should execute before low urgency plans
        if abs(urgency_a - urgency_b) > 0.3:
            if urgency_a > urgency_b:
                dependency_analysis['has_dependency'] = True
                dependency_analysis['prerequisite'] = plan_a.intent_id
                dependency_analysis['dependent'] = plan_b.intent_id
                dependency_analysis['dependency_type'] = 'urgency_priority'
                dependency_analysis['minimum_delay'] = 300  # 5 minutes minimum delay
            else:
                dependency_analysis['has_dependency'] = True
                dependency_analysis['prerequisite'] = plan_b.intent_id
                dependency_analysis['dependent'] = plan_a.intent_id
                dependency_analysis['dependency_type'] = 'urgency_priority'
                dependency_analysis['minimum_delay'] = 300
        
        # Check for deadline-based dependencies
        if (plan_a.expires_at and plan_b.expires_at and 
            abs((plan_a.expires_at - plan_b.expires_at).total_seconds()) > 3600):
            earlier_deadline = plan_a if plan_a.expires_at < plan_b.expires_at else plan_b
            later_deadline = plan_b if earlier_deadline == plan_a else plan_a
            
            dependency_analysis['has_dependency'] = True
            dependency_analysis['prerequisite'] = earlier_deadline.intent_id
            dependency_analysis['dependent'] = later_deadline.intent_id
            dependency_analysis['dependency_type'] = 'deadline_priority'
            dependency_analysis['minimum_delay'] = 0
        
        return dependency_analysis
    
    def _analyze_chain_dependency(self, plan_a: ExecutionPlan, plan_b: ExecutionPlan) -> Dict[str, Any]:
        """Analyze chain-specific dependencies and conflicts"""
        
        chain_analysis = {
            'has_conflict': False,
            'conflicted_chain': None,
            'conflict_severity': 'none',
            'recommended_spacing': 0
        }
        
        if not plan_a.execution_paths or not plan_b.execution_paths:
            return chain_analysis
        
        path_a = plan_a.execution_paths[0]
        path_b = plan_b.execution_paths[0]
        
        # Check for same source chain conflicts
        if path_a.source_chain == path_b.source_chain:
            chain_analysis['has_conflict'] = True
            chain_analysis['conflicted_chain'] = path_a.source_chain
            
            # Ethereum has higher congestion risk
            if path_a.source_chain.lower() == 'ethereum':
                chain_analysis['conflict_severity'] = 'high'
                chain_analysis['recommended_spacing'] = 900  # 15 minutes
            else:
                chain_analysis['conflict_severity'] = 'medium'
                chain_analysis['recommended_spacing'] = 300  # 5 minutes
        
        # Check for same target chain conflicts
        elif path_a.target_chain == path_b.target_chain:
            chain_analysis['has_conflict'] = True
            chain_analysis['conflicted_chain'] = path_a.target_chain
            chain_analysis['conflict_severity'] = 'medium'
            chain_analysis['recommended_spacing'] = 300
        
        return chain_analysis
    
    def _analyze_priority_dependency(self, plan_a: ExecutionPlan, plan_b: ExecutionPlan) -> Dict[str, Any]:
        """Analyze priority-based dependencies"""
        
        priority_analysis = {
            'has_dependency': False,
            'higher_priority': None,
            'lower_priority': None,
            'priority_gap': 0
        }
        
        priority_values = {
            ExecutionPriority.LOW: 1,
            ExecutionPriority.NORMAL: 2,
            ExecutionPriority.HIGH: 3,
            ExecutionPriority.URGENT: 4
        }
        
        priority_a = priority_values.get(plan_a.priority, 2)
        priority_b = priority_values.get(plan_b.priority, 2)
        
        if abs(priority_a - priority_b) >= 2:  # Significant priority difference
            priority_analysis['has_dependency'] = True
            priority_analysis['priority_gap'] = abs(priority_a - priority_b)
            
            if priority_a > priority_b:
                priority_analysis['higher_priority'] = plan_a.intent_id
                priority_analysis['lower_priority'] = plan_b.intent_id
            else:
                priority_analysis['higher_priority'] = plan_b.intent_id
                priority_analysis['lower_priority'] = plan_a.intent_id
        
        return priority_analysis
    
    async def _identify_batching_opportunities(self, intent_plans: List[ExecutionPlan]) -> Dict[str, Any]:
        """
        Identify opportunities for batching intents for efficiency gains
        """
        
        batching_opportunities = {
            'same_chain_batches': [],
            'same_asset_batches': [],
            'timing_batches': [],
            'gas_optimization_batches': [],
            'estimated_savings': {}
        }
        
        # Group by source chain for potential batching
        chain_groups = {}
        for plan in intent_plans:
            if plan.execution_paths:
                source_chain = plan.execution_paths[0].source_chain
                if source_chain not in chain_groups:
                    chain_groups[source_chain] = []
                chain_groups[source_chain].append(plan)
        
        # Identify same-chain batching opportunities
        for chain, plans in chain_groups.items():
            if len(plans) >= 2:
                # Check if plans can be batched (similar timing, compatible priorities)
                batchable_plans = []
                for plan in plans:
                    if (plan.priority != ExecutionPriority.URGENT and 
                        plan.timing.urgency_score < 0.8):
                        batchable_plans.append(plan)
                
                if len(batchable_plans) >= 2:
                    batch_info = {
                        'chain': chain,
                        'intent_ids': [p.intent_id for p in batchable_plans],
                        'estimated_gas_savings': sum(p.execution_paths[0].gas_cost for p in batchable_plans) * 0.15,
                        'batch_window': self._calculate_batch_window(batchable_plans)
                    }
                    batching_opportunities['same_chain_batches'].append(batch_info)
        
        # Identify timing-based batching opportunities
        timing_groups = self._group_by_timing_window(intent_plans)
        for window, plans in timing_groups.items():
            if len(plans) >= 2:
                batch_info = {
                    'timing_window': window,
                    'intent_ids': [p.intent_id for p in plans],
                    'coordination_benefit': 0.1,  # 10% efficiency gain
                    'window_duration': window[1] - window[0]
                }
                batching_opportunities['timing_batches'].append(batch_info)
        
        # Calculate total estimated savings
        total_gas_savings = sum(
            batch['estimated_gas_savings'] 
            for batch in batching_opportunities['same_chain_batches']
        )
        total_coordination_benefits = sum(
            batch['coordination_benefit'] * 1000  # Convert to dollar estimate
            for batch in batching_opportunities['timing_batches']
        )
        
        batching_opportunities['estimated_savings'] = {
            'gas_savings': total_gas_savings,
            'coordination_benefits': total_coordination_benefits,
            'total_savings': total_gas_savings + total_coordination_benefits
        }
        
        return batching_opportunities
    
    def _calculate_batch_window(self, plans: List[ExecutionPlan]) -> Tuple[datetime, datetime]:
        """Calculate optimal batching window for a group of plans"""
        
        earliest_time = min(plan.timing.recommended_time for plan in plans)
        latest_time = max(plan.timing.recommended_time for plan in plans)
        
        # Extend window slightly to accommodate all plans
        window_start = earliest_time - timedelta(minutes=5)
        window_end = latest_time + timedelta(minutes=15)
        
        return (window_start, window_end)
    
    def _group_by_timing_window(self, intent_plans: List[ExecutionPlan]) -> Dict[Tuple[datetime, datetime], List[ExecutionPlan]]:
        """Group plans by timing windows for batching opportunities"""
        
        timing_groups = {}
        window_size = timedelta(minutes=30)  # 30-minute windows
        
        for plan in intent_plans:
            # Create 30-minute window around recommended time
            window_start = plan.timing.recommended_time - window_size / 2
            window_end = plan.timing.recommended_time + window_size / 2
            window = (window_start, window_end)
            
            # Find existing overlapping window or create new one
            overlapping_window = None
            for existing_window in timing_groups.keys():
                if (window_start <= existing_window[1] and window_end >= existing_window[0]):
                    overlapping_window = existing_window
                    break
            
            if overlapping_window:
                timing_groups[overlapping_window].append(plan)
            else:
                timing_groups[window] = [plan]
        
        # Filter out single-plan groups
        return {window: plans for window, plans in timing_groups.items() if len(plans) >= 2}
    
    async def _optimize_execution_order_enhanced(self, intent_plans: List[ExecutionPlan], 
                                               dependencies: Dict[str, Any],
                                               batching_opportunities: Dict[str, Any]) -> List[str]:
        """
        Enhanced execution order optimization using topological sort to respect all dependencies
        """
        
        # Build a complete dependency graph from all dependency types
        all_dependencies = {}
        
        # Collect all dependencies into a single graph
        for intent_plan in intent_plans:
            intent_id = intent_plan.intent_id
            all_dependencies[intent_id] = set()
            
            # Add resource dependencies
            resource_deps = dependencies.get('resource_dependencies', {}).get(intent_id, [])
            all_dependencies[intent_id].update(resource_deps)
            
            # Add timing dependencies
            timing_deps = dependencies.get('timing_dependencies', {}).get(intent_id, [])
            all_dependencies[intent_id].update(timing_deps)
            
            # Add priority dependencies
            priority_deps = dependencies.get('priority_dependencies', {}).get(intent_id, [])
            all_dependencies[intent_id].update(priority_deps)
            
            # Add execution graph dependencies
            execution_deps = dependencies.get('execution_graph', {}).get(intent_id, {}).get('depends_on', [])
            all_dependencies[intent_id].update(execution_deps)
        
        # Perform topological sort with priority-based tie-breaking
        execution_order = []
        remaining_plans = {plan.intent_id: plan for plan in intent_plans}
        
        # Create batches from batching opportunities
        batches = []
        batched_intents = set()
        
        # Process same-chain batches (only if they don't violate dependencies)
        same_chain_batches = batching_opportunities.get('same_chain_batches', [])
        for batch_info in same_chain_batches:
            batch_intents = batch_info['intent_ids']
            
            # Check if batch violates any dependencies
            batch_valid = True
            for intent_a in batch_intents:
                for intent_b in batch_intents:
                    if intent_a != intent_b:
                        # Check if intent_a depends on intent_b
                        deps_a = all_dependencies.get(intent_a, set())
                        if intent_b in deps_a:
                            batch_valid = False
                            break
                if not batch_valid:
                    break
            
            if batch_valid and not any(intent_id in batched_intents for intent_id in batch_intents):
                batches.append(batch_intents)
                batched_intents.update(batch_intents)
        
        # Process timing batches (if not already batched and don't violate dependencies)
        timing_batches = batching_opportunities.get('timing_batches', [])
        for batch_info in timing_batches:
            batch_intents = [
                intent_id for intent_id in batch_info['intent_ids'] 
                if intent_id not in batched_intents
            ]
            
            if len(batch_intents) >= 2:
                # Check if batch violates any dependencies
                batch_valid = True
                for intent_a in batch_intents:
                    for intent_b in batch_intents:
                        if intent_a != intent_b:
                            # Check if intent_a depends on intent_b
                            deps_a = all_dependencies.get(intent_a, set())
                            if intent_b in deps_a:
                                batch_valid = False
                                break
                    if not batch_valid:
                        break
                
                if batch_valid:
                    batches.append(batch_intents)
                    batched_intents.update(batch_intents)
        
        # Topological sort with batching support
        while remaining_plans or batches:
            # Find ready batches (no dependencies)
            ready_batches = []
            for batch in batches:
                # A batch is ready only if ALL intents in the batch have no pending dependencies
                batch_ready = True
                for batch_intent in batch:
                    if batch_intent in remaining_plans:
                        deps = all_dependencies.get(batch_intent, set())
                        if any(dep in remaining_plans for dep in deps):
                            batch_ready = False
                            break
                
                if batch_ready and any(intent_id in remaining_plans for intent_id in batch):
                    ready_batches.append(batch)
            
            # Find ready individual intents
            ready_intents = []
            for intent_id, plan in remaining_plans.items():
                if intent_id not in batched_intents:
                    deps = all_dependencies.get(intent_id, set())
                    if not any(dep in remaining_plans for dep in deps):
                        ready_intents.append((intent_id, plan))
            
            # Prioritize batches over individual intents for efficiency
            if ready_batches:
                # Select batch with highest priority average
                best_batch = max(ready_batches, key=lambda b: sum(
                    self._priority_to_numeric(remaining_plans[intent_id].priority) 
                    for intent_id in b if intent_id in remaining_plans
                ) / len([intent_id for intent_id in b if intent_id in remaining_plans]))
                
                # Sort intents within batch by priority
                batch_sorted = sorted(
                    [intent_id for intent_id in best_batch if intent_id in remaining_plans],
                    key=lambda x: (
                        -self._priority_to_numeric(remaining_plans[x].priority),
                        -remaining_plans[x].timing.urgency_score
                    )
                )
                
                execution_order.extend(batch_sorted)
                for intent_id in batch_sorted:
                    if intent_id in remaining_plans:
                        del remaining_plans[intent_id]
                batches.remove(best_batch)
            
            elif ready_intents:
                # Sort by priority and urgency
                ready_intents.sort(key=lambda x: (
                    -self._priority_to_numeric(x[1].priority),
                    -x[1].timing.urgency_score
                ))
                
                selected_intent_id = ready_intents[0][0]
                execution_order.append(selected_intent_id)
                del remaining_plans[selected_intent_id]
            
            else:
                # Circular dependency or error - break the cycle by selecting highest priority
                if remaining_plans:
                    remaining_items = list(remaining_plans.items())
                    remaining_items.sort(key=lambda x: (
                        -self._priority_to_numeric(x[1].priority),
                        -x[1].timing.urgency_score
                    ))
                    
                    selected_intent_id = remaining_items[0][0]
                    execution_order.append(selected_intent_id)
                    del remaining_plans[selected_intent_id]
                
                if batches:
                    # Add remaining batches
                    for batch in batches:
                        batch_remaining = [intent_id for intent_id in batch if intent_id in remaining_plans]
                        # Sort batch by priority
                        batch_remaining.sort(key=lambda x: (
                            -self._priority_to_numeric(remaining_plans[x].priority),
                            -remaining_plans[x].timing.urgency_score
                        ))
                        execution_order.extend(batch_remaining)
                        for intent_id in batch_remaining:
                            if intent_id in remaining_plans:
                                del remaining_plans[intent_id]
                    batches.clear()
        
        return execution_order
    
    def _has_no_pending_dependencies(self, intent_id: str, dependencies: Dict[str, Any], remaining_plans: Dict[str, ExecutionPlan]) -> bool:
        """Check if an intent has no pending dependencies"""
        
        # Check resource dependencies
        resource_deps = dependencies.get('resource_dependencies', {}).get(intent_id, [])
        if any(dep in remaining_plans for dep in resource_deps):
            return False
        
        # Check timing dependencies
        timing_deps = dependencies.get('timing_dependencies', {}).get(intent_id, [])
        if any(dep in remaining_plans for dep in timing_deps):
            return False
        
        # Check priority dependencies
        priority_deps = dependencies.get('priority_dependencies', {}).get(intent_id, [])
        if any(dep in remaining_plans for dep in priority_deps):
            return False
        
        # Check execution graph dependencies
        execution_deps = dependencies.get('execution_graph', {}).get(intent_id, {}).get('depends_on', [])
        if any(dep in remaining_plans for dep in execution_deps):
            return False
        
        return True
    
    async def _optimize_resource_allocation_enhanced(self, intent_plans: List[ExecutionPlan],
                                                   coordination_type: str,
                                                   batching_opportunities: Dict[str, Any]) -> Dict[str, float]:
        """
        Enhanced resource allocation optimization considering batching and coordination
        """
        
        total_cost = sum(
            plan.execution_paths[0].total_cost for plan in intent_plans 
            if plan.execution_paths
        )
        
        resource_allocation = {}
        
        # Base allocation by cost and priority
        for plan in intent_plans:
            if plan.execution_paths:
                cost_ratio = plan.execution_paths[0].total_cost / total_cost if total_cost > 0 else 1.0 / len(intent_plans)
                priority_multiplier = self._priority_to_numeric(plan.priority) / 2.5
                
                base_allocation = cost_ratio * priority_multiplier
                resource_allocation[plan.intent_id] = base_allocation
        
        # Adjust allocation based on batching opportunities
        batched_intents = set()
        for batch_info in batching_opportunities['same_chain_batches']:
            batch_intents = batch_info['intent_ids']
            batch_savings = batch_info['estimated_gas_savings']
            
            # Redistribute savings among batch members
            savings_per_intent = batch_savings / len(batch_intents) / total_cost if total_cost > 0 else 0
            
            for intent_id in batch_intents:
                if intent_id in resource_allocation:
                    resource_allocation[intent_id] -= savings_per_intent  # Reduce allocation due to savings
                    batched_intents.add(intent_id)
        
        # Adjust for coordination type
        coordination_multipliers = {
            'batch': 0.9,      # 10% resource reduction due to batching efficiency
            'sequence': 1.0,   # No change
            'parallel': 1.1    # 10% increase due to parallel coordination overhead
        }
        
        multiplier = coordination_multipliers.get(coordination_type, 1.0)
        for intent_id in resource_allocation:
            resource_allocation[intent_id] *= multiplier
        
        # Normalize allocations to sum to 1.0
        total_allocation = sum(resource_allocation.values())
        if total_allocation > 0:
            for intent_id in resource_allocation:
                resource_allocation[intent_id] /= total_allocation
        
        return resource_allocation
    
    async def _create_conflict_resolution_plan(self, intent_plans: List[ExecutionPlan],
                                             dependencies: Dict[str, Any],
                                             resource_allocation: Dict[str, float]) -> Dict[str, Any]:
        """
        Create a comprehensive conflict resolution plan for coordination issues
        """
        
        conflict_resolution = {
            'conflict_types': [],
            'resolution_strategies': {},
            'escalation_procedures': {},
            'monitoring_requirements': {},
            'fallback_plans': {}
        }
        
        # Identify potential conflicts
        resource_conflicts = []
        timing_conflicts = []
        priority_conflicts = []
        
        for i, plan_a in enumerate(intent_plans):
            for j, plan_b in enumerate(intent_plans):
                if i >= j:
                    continue
                
                # Check for resource conflicts
                if (plan_a.intent_id in dependencies.get('resource_dependencies', {}).get(plan_b.intent_id, []) or
                    plan_b.intent_id in dependencies.get('resource_dependencies', {}).get(plan_a.intent_id, [])):
                    resource_conflicts.append((plan_a.intent_id, plan_b.intent_id))
                
                # Check for timing conflicts
                time_diff = abs((plan_a.timing.recommended_time - plan_b.timing.recommended_time).total_seconds())
                if time_diff < 300 and plan_a.priority != plan_b.priority:  # Within 5 minutes with different priorities
                    timing_conflicts.append((plan_a.intent_id, plan_b.intent_id))
                
                # Check for priority conflicts
                if (plan_a.priority == ExecutionPriority.URGENT and plan_b.priority == ExecutionPriority.URGENT and
                    time_diff < 600):  # Two urgent intents within 10 minutes
                    priority_conflicts.append((plan_a.intent_id, plan_b.intent_id))
        
        # Create resolution strategies
        if resource_conflicts:
            conflict_resolution['conflict_types'].append('resource_conflicts')
            conflict_resolution['resolution_strategies']['resource_conflicts'] = {
                'strategy': 'sequential_execution_with_monitoring',
                'conflicts': resource_conflicts,
                'resolution_steps': [
                    'Execute higher priority intent first',
                    'Monitor resource utilization',
                    'Execute lower priority intent when resources are available',
                    'Implement resource pooling if possible'
                ]
            }
        
        if timing_conflicts:
            conflict_resolution['conflict_types'].append('timing_conflicts')
            conflict_resolution['resolution_strategies']['timing_conflicts'] = {
                'strategy': 'dynamic_scheduling_with_priority_override',
                'conflicts': timing_conflicts,
                'resolution_steps': [
                    'Reschedule lower priority intents',
                    'Implement priority-based queue',
                    'Use dynamic timing adjustment',
                    'Provide real-time conflict notifications'
                ]
            }
        
        if priority_conflicts:
            conflict_resolution['conflict_types'].append('priority_conflicts')
            conflict_resolution['resolution_strategies']['priority_conflicts'] = {
                'strategy': 'human_escalation_with_automated_fallback',
                'conflicts': priority_conflicts,
                'resolution_steps': [
                    'Escalate to human operator',
                    'Provide conflict analysis and recommendations',
                    'Implement automated fallback after timeout',
                    'Log all decisions for audit'
                ]
            }
        
        # Create escalation procedures
        conflict_resolution['escalation_procedures'] = {
            'level_1': {
                'trigger': 'Automated resolution fails',
                'action': 'Notify system administrator',
                'timeout': 300  # 5 minutes
            },
            'level_2': {
                'trigger': 'Level 1 timeout or multiple conflicts',
                'action': 'Escalate to human operator',
                'timeout': 900  # 15 minutes
            },
            'level_3': {
                'trigger': 'Level 2 timeout or critical system impact',
                'action': 'Emergency fallback to individual execution',
                'timeout': 0  # Immediate
            }
        }
        
        # Create monitoring requirements
        conflict_resolution['monitoring_requirements'] = {
            'real_time_metrics': [
                'resource_utilization_per_chain',
                'execution_queue_length',
                'conflict_resolution_success_rate',
                'average_coordination_overhead'
            ],
            'alert_thresholds': {
                'resource_utilization': 0.8,
                'queue_length': 10,
                'conflict_rate': 0.2,
                'coordination_overhead': 0.3
            },
            'monitoring_frequency': 30  # seconds
        }
        
        # Create fallback plans
        conflict_resolution['fallback_plans'] = {
            'coordination_failure': {
                'action': 'revert_to_individual_execution',
                'trigger': 'coordination_overhead > 50% OR conflict_rate > 30%',
                'implementation': 'Execute each intent independently with original timing'
            },
            'resource_exhaustion': {
                'action': 'implement_resource_queuing',
                'trigger': 'resource_utilization > 90%',
                'implementation': 'Queue intents and execute when resources become available'
            },
            'system_overload': {
                'action': 'emergency_load_shedding',
                'trigger': 'system_load > 95% OR response_time > 30s',
                'implementation': 'Prioritize urgent intents only, defer others'
            }
        }
        
        return conflict_resolution
    
    def _determine_coordination_type(self, intent_plans: List[ExecutionPlan]) -> str:
        """Determine the best coordination type for the intents"""
        
        # Analyze intent characteristics
        same_source_chains = len(set(plan.execution_paths[0].source_chain for plan in intent_plans if plan.execution_paths)) == 1
        same_target_chains = len(set(plan.execution_paths[0].target_chain for plan in intent_plans if plan.execution_paths)) == 1
        similar_timing = all(
            abs((plan.timing.recommended_time - intent_plans[0].timing.recommended_time).total_seconds()) < 1800
            for plan in intent_plans
        )
        
        # Determine coordination type
        if same_source_chains and same_target_chains and similar_timing:
            return "batch"  # Execute together as a batch
        elif any(plan.priority == ExecutionPriority.URGENT for plan in intent_plans):
            return "parallel"  # Execute in parallel to minimize delays
        else:
            return "sequence"  # Execute in optimized sequence
    
    def _analyze_intent_dependencies(self, intent_plans: List[ExecutionPlan]) -> Dict[str, List[str]]:
        """Analyze dependencies between intents"""
        
        dependencies = {}
        
        for i, plan_a in enumerate(intent_plans):
            for j, plan_b in enumerate(intent_plans):
                if i >= j:
                    continue
                
                # Check for resource conflicts
                if self._have_resource_conflict(plan_a, plan_b):
                    # Plan B depends on Plan A if A has higher priority
                    if plan_a.priority.value > plan_b.priority.value:
                        if plan_b.intent_id not in dependencies:
                            dependencies[plan_b.intent_id] = []
                        dependencies[plan_b.intent_id].append(plan_a.intent_id)
                    else:
                        if plan_a.intent_id not in dependencies:
                            dependencies[plan_a.intent_id] = []
                        dependencies[plan_a.intent_id].append(plan_b.intent_id)
        
        return dependencies
    
    def _have_resource_conflict(self, plan_a: ExecutionPlan, plan_b: ExecutionPlan) -> bool:
        """Check if two plans have resource conflicts"""
        
        if not plan_a.execution_paths or not plan_b.execution_paths:
            return False
        
        # Check for same chain usage at similar times
        chains_a = {plan_a.execution_paths[0].source_chain, plan_a.execution_paths[0].target_chain}
        chains_b = {plan_b.execution_paths[0].source_chain, plan_b.execution_paths[0].target_chain}
        
        if chains_a.intersection(chains_b):
            # Check timing overlap
            time_diff = abs((plan_a.timing.recommended_time - plan_b.timing.recommended_time).total_seconds())
            if time_diff < 3600:  # Within 1 hour
                return True
        
        return False
    
    def _optimize_execution_order(self, intent_plans: List[ExecutionPlan], 
                                dependencies: Dict[str, List[str]]) -> List[str]:
        """Optimize execution order considering dependencies and priorities"""
        
        # Topological sort considering dependencies
        remaining_plans = {plan.intent_id: plan for plan in intent_plans}
        execution_order = []
        
        while remaining_plans:
            # Find plans with no remaining dependencies
            ready_plans = []
            for intent_id, plan in remaining_plans.items():
                deps = dependencies.get(intent_id, [])
                if not any(dep in remaining_plans for dep in deps):
                    ready_plans.append((intent_id, plan))
            
            if not ready_plans:
                # Circular dependency or error - add remaining by priority
                ready_plans = list(remaining_plans.items())
            
            # Sort by priority and timing
            ready_plans.sort(key=lambda x: (
                -self._priority_to_numeric(x[1].priority),  # Higher priority first
                x[1].timing.urgency_score  # More urgent first
            ), reverse=True)
            
            # Add the highest priority plan to execution order
            selected_intent_id = ready_plans[0][0]
            execution_order.append(selected_intent_id)
            del remaining_plans[selected_intent_id]
        
        return execution_order
    
    def _priority_to_numeric(self, priority: ExecutionPriority) -> int:
        """Convert priority to numeric value for sorting"""
        priority_values = {
            ExecutionPriority.LOW: 1,
            ExecutionPriority.NORMAL: 2,
            ExecutionPriority.HIGH: 3,
            ExecutionPriority.URGENT: 4
        }
        return priority_values.get(priority, 2)
    
    def _optimize_resource_allocation(self, intent_plans: List[ExecutionPlan]) -> Dict[str, float]:
        """Optimize resource allocation across intents"""
        
        total_cost = sum(
            plan.execution_paths[0].total_cost for plan in intent_plans 
            if plan.execution_paths
        )
        
        resource_allocation = {}
        
        for plan in intent_plans:
            if plan.execution_paths:
                # Allocate resources based on cost and priority
                cost_ratio = plan.execution_paths[0].total_cost / total_cost if total_cost > 0 else 1.0 / len(intent_plans)
                priority_multiplier = self._priority_to_numeric(plan.priority) / 2.5  # Normalize to ~1.0
                
                allocation = cost_ratio * priority_multiplier
                resource_allocation[plan.intent_id] = allocation
        
        # Normalize allocations to sum to 1.0
        total_allocation = sum(resource_allocation.values())
        if total_allocation > 0:
            for intent_id in resource_allocation:
                resource_allocation[intent_id] /= total_allocation
        
        return resource_allocation
    
    def _calculate_coordination_savings(self, intent_plans: List[ExecutionPlan], 
                                      coordination_type: str) -> float:
        """Calculate estimated savings from coordination"""
        
        if not intent_plans:
            return 0.0
        
        # Calculate individual execution costs
        individual_costs = []
        for plan in intent_plans:
            if plan.execution_paths:
                individual_costs.append(plan.execution_paths[0].total_cost)
        
        total_individual_cost = sum(individual_costs)
        
        # Calculate coordination savings based on type
        if coordination_type == "batch":
            # Batch execution can save on gas costs
            gas_savings = sum(
                plan.execution_paths[0].gas_cost * 0.2 for plan in intent_plans 
                if plan.execution_paths
            )  # 20% gas savings
            return gas_savings
        
        elif coordination_type == "sequence":
            # Sequential execution can optimize for market conditions
            timing_savings = total_individual_cost * 0.05  # 5% savings from timing optimization
            return timing_savings
        
        elif coordination_type == "parallel":
            # Parallel execution saves time but may have higher costs
            return total_individual_cost * 0.02  # 2% savings from reduced slippage
        
        return 0.0
    
    def _calculate_coordination_overhead(self, intent_plans: List[ExecutionPlan], 
                                       coordination_type: str) -> float:
        """Calculate coordination overhead costs"""
        
        base_overhead = len(intent_plans) * 10.0  # $10 per intent coordination
        
        # Additional overhead based on coordination type
        if coordination_type == "batch":
            return base_overhead * 1.2  # 20% more overhead for batching
        elif coordination_type == "sequence":
            return base_overhead * 1.5  # 50% more overhead for sequencing
        elif coordination_type == "parallel":
            return base_overhead * 2.0  # 100% more overhead for parallel coordination
        
        return base_overhead
    
    async def learn_from_execution_outcome(self, plan_id: str, actual_outcome: Dict[str, Any]) -> None:
        """
        Learn from execution outcomes to improve future strategies
        
        Args:
            plan_id: ID of the executed plan
            actual_outcome: Actual execution results
        """
        
        try:
            plan = self.strategy_cache.get(plan_id)
            if not plan:
                self.logger.warning(f"Plan {plan_id} not found for learning")
                return
            
            # Extract actual metrics
            actual_cost = actual_outcome.get('actual_cost', 0.0)
            actual_time = actual_outcome.get('actual_time', 0.0)
            success = actual_outcome.get('success', False)
            actual_slippage = actual_outcome.get('actual_slippage', 0.0)
            
            # Calculate prediction accuracy
            if plan.execution_paths:
                best_path = plan.execution_paths[0]
                
                cost_accuracy = 1.0 - abs(actual_cost - best_path.total_cost) / best_path.total_cost if best_path.total_cost > 0 else 0.0
                time_accuracy = 1.0 - abs(actual_time - best_path.estimated_time) / best_path.estimated_time if best_path.estimated_time > 0 else 0.0
                slippage_accuracy = 1.0 - abs(actual_slippage - best_path.estimated_slippage) / best_path.estimated_slippage if best_path.estimated_slippage > 0 else 0.0
                
                # Overall performance score
                performance_score = (cost_accuracy + time_accuracy + slippage_accuracy) / 3.0
                if success:
                    performance_score *= 1.1  # Bonus for successful execution
                else:
                    performance_score *= 0.5  # Penalty for failed execution
                
                # Store performance data
                strategy_key = f"{plan.strategy.value}_{best_path.source_chain}_{best_path.target_chain}"
                if strategy_key not in self.strategy_performance:
                    self.strategy_performance[strategy_key] = []
                
                self.strategy_performance[strategy_key].append(performance_score)
                
                # Keep only recent performance data (last 100 executions)
                if len(self.strategy_performance[strategy_key]) > 100:
                    self.strategy_performance[strategy_key] = self.strategy_performance[strategy_key][-100:]
                
                self.logger.info(f"Learned from execution {plan_id}: performance_score={performance_score:.3f}")
            
            # Update model performance in MLflow
            await self._update_model_performance(plan_id, actual_outcome, plan)
            
        except Exception as e:
            self.logger.error(f"Failed to learn from execution outcome {plan_id}: {e}")
    
    async def _update_model_performance(self, plan_id: str, actual_outcome: Dict[str, Any], 
                                      plan: ExecutionPlan) -> None:
        """Update model performance metrics"""
        
        try:
            # Create performance metrics
            metrics = {
                'execution_success_rate': 1.0 if actual_outcome.get('success', False) else 0.0,
                'cost_prediction_accuracy': self._calculate_cost_accuracy(actual_outcome, plan),
                'time_prediction_accuracy': self._calculate_time_accuracy(actual_outcome, plan),
                'strategy_confidence': plan.confidence_score
            }
            
            # Log to MLflow if available
            import mlflow
            with mlflow.start_run(run_name=f"execution_outcome_{plan_id}"):
                mlflow.log_metrics(metrics)
                mlflow.log_param("strategy_type", plan.strategy.value)
                mlflow.log_param("priority", plan.priority.value)
                
        except Exception as e:
            self.logger.warning(f"Failed to update model performance: {e}")
    
    def _calculate_cost_accuracy(self, actual_outcome: Dict[str, Any], plan: ExecutionPlan) -> float:
        """Calculate cost prediction accuracy"""
        
        actual_cost = actual_outcome.get('actual_cost', 0.0)
        if not plan.execution_paths or actual_cost == 0.0:
            return 0.0
        
        predicted_cost = plan.execution_paths[0].total_cost
        if predicted_cost == 0.0:
            return 0.0
        
        accuracy = 1.0 - abs(actual_cost - predicted_cost) / predicted_cost
        return max(0.0, accuracy)
    
    def _calculate_time_accuracy(self, actual_outcome: Dict[str, Any], plan: ExecutionPlan) -> float:
        """Calculate time prediction accuracy"""
        
        actual_time = actual_outcome.get('actual_time', 0.0)
        if not plan.execution_paths or actual_time == 0.0:
            return 0.0
        
        predicted_time = plan.execution_paths[0].estimated_time
        if predicted_time == 0.0:
            return 0.0
        
        accuracy = 1.0 - abs(actual_time - predicted_time) / predicted_time
        return max(0.0, accuracy)
    
    async def update_strategy_models(self) -> None:
        """Update strategy models based on performance feedback"""
        
        try:
            stats = self.get_strategy_performance_stats()
            
            for strategy_key, performance_data in stats.items():
                # Check if strategy is underperforming
                if (performance_data['avg_performance'] < 0.7 and 
                    performance_data['execution_count'] >= 10 and
                    performance_data['recent_trend'] == 'declining'):
                    
                    await self._retrain_strategy_model(strategy_key, performance_data)
                
                # Check if strategy is performing well and can be promoted
                elif (performance_data['avg_performance'] > 0.85 and
                      performance_data['recent_trend'] == 'improving'):
                    
                    await self._promote_strategy_model(strategy_key, performance_data)
            
            self.logger.info("Strategy model updates completed")
            
        except Exception as e:
            self.logger.error(f"Failed to update strategy models: {e}")
    
    async def _retrain_strategy_model(self, strategy_key: str, performance_data: Dict[str, Any]) -> None:
        """Retrain underperforming strategy model"""
        
        try:
            # Extract strategy components
            strategy_parts = strategy_key.split('_')
            if len(strategy_parts) >= 3:
                strategy_type = strategy_parts[0]
                source_chain = strategy_parts[1]
                target_chain = strategy_parts[2]
                
                # Adjust strategy parameters based on poor performance
                adjustments = {
                    'cost_estimation_factor': 1.1,  # Be more conservative with cost estimates
                    'time_estimation_factor': 1.15,  # Be more conservative with time estimates
                    'slippage_buffer': 1.2,  # Increase slippage buffer
                    'confidence_penalty': 0.9  # Reduce confidence for this strategy
                }
                
                # Store adjustments for future strategy generation
                adjustment_key = f"adjustments_{strategy_key}"
                if not hasattr(self, 'strategy_adjustments'):
                    self.strategy_adjustments = {}
                
                self.strategy_adjustments[adjustment_key] = adjustments
                
                self.logger.info(f"Retrained strategy model for {strategy_key} due to poor performance")
                
                # Log retraining event to MLflow
                import mlflow
                with mlflow.start_run(run_name=f"strategy_retrain_{strategy_key}"):
                    mlflow.log_metrics({
                        'avg_performance_before': performance_data['avg_performance'],
                        'execution_count': performance_data['execution_count']
                    })
                    mlflow.log_params(adjustments)
                    
        except Exception as e:
            self.logger.error(f"Failed to retrain strategy model {strategy_key}: {e}")
    
    async def _promote_strategy_model(self, strategy_key: str, performance_data: Dict[str, Any]) -> None:
        """Promote well-performing strategy model"""
        
        try:
            # Extract strategy components
            strategy_parts = strategy_key.split('_')
            if len(strategy_parts) >= 3:
                strategy_type = strategy_parts[0]
                source_chain = strategy_parts[1]
                target_chain = strategy_parts[2]
                
                # Adjust strategy parameters to be more aggressive
                adjustments = {
                    'cost_estimation_factor': 0.95,  # Be more optimistic with cost estimates
                    'time_estimation_factor': 0.9,   # Be more optimistic with time estimates
                    'slippage_buffer': 0.9,          # Reduce slippage buffer
                    'confidence_bonus': 1.1          # Increase confidence for this strategy
                }
                
                # Store adjustments for future strategy generation
                adjustment_key = f"adjustments_{strategy_key}"
                if not hasattr(self, 'strategy_adjustments'):
                    self.strategy_adjustments = {}
                
                self.strategy_adjustments[adjustment_key] = adjustments
                
                self.logger.info(f"Promoted strategy model for {strategy_key} due to excellent performance")
                
                # Log promotion event to MLflow
                import mlflow
                with mlflow.start_run(run_name=f"strategy_promote_{strategy_key}"):
                    mlflow.log_metrics({
                        'avg_performance': performance_data['avg_performance'],
                        'execution_count': performance_data['execution_count']
                    })
                    mlflow.log_params(adjustments)
                    
        except Exception as e:
            self.logger.error(f"Failed to promote strategy model {strategy_key}: {e}")
    
    def apply_strategy_adjustments(self, strategy_key: str, base_cost: float, base_time: float, 
                                 base_slippage: float, base_confidence: float) -> Tuple[float, float, float, float]:
        """Apply learned adjustments to strategy parameters"""
        
        if not hasattr(self, 'strategy_adjustments'):
            return base_cost, base_time, base_slippage, base_confidence
        
        adjustment_key = f"adjustments_{strategy_key}"
        adjustments = self.strategy_adjustments.get(adjustment_key, {})
        
        adjusted_cost = base_cost * adjustments.get('cost_estimation_factor', 1.0)
        adjusted_time = base_time * adjustments.get('time_estimation_factor', 1.0)
        adjusted_slippage = base_slippage * adjustments.get('slippage_buffer', 1.0)
        
        confidence_factor = adjustments.get('confidence_penalty', adjustments.get('confidence_bonus', 1.0))
        adjusted_confidence = base_confidence * confidence_factor
        
        return adjusted_cost, adjusted_time, adjusted_slippage, adjusted_confidence
    
    # A/B Testing Framework for Strategy Comparison
    
    async def create_ab_test(self, test_name: str, strategy_variants: List[str], 
                           traffic_split: Dict[str, float] = None) -> str:
        """Create a new A/B test for strategy comparison"""
        
        try:
            if traffic_split is None:
                # Equal split by default
                split_ratio = 1.0 / len(strategy_variants)
                traffic_split = {variant: split_ratio for variant in strategy_variants}
            
            # Validate traffic split
            total_traffic = sum(traffic_split.values())
            if abs(total_traffic - 1.0) > 0.01:
                raise ValueError(f"Traffic split must sum to 1.0, got {total_traffic}")
            
            test_id = f"ab_test_{test_name}_{int(datetime.now().timestamp())}"
            
            # Initialize A/B testing attributes if not already done
            if not hasattr(self, 'ab_tests'):
                self.ab_tests = {}
            if not hasattr(self, 'ab_test_assignments'):
                self.ab_test_assignments = {}
            
            self.ab_tests[test_id] = {
                'test_name': test_name,
                'strategy_variants': strategy_variants,
                'traffic_split': traffic_split,
                'created_at': datetime.now(),
                'status': 'active',
                'results': {variant: {'executions': 0, 'total_performance': 0.0, 'success_count': 0} 
                           for variant in strategy_variants}
            }
            
            self.logger.info(f"Created A/B test {test_id} with variants: {strategy_variants}")
            return test_id
            
        except Exception as e:
            self.logger.error(f"Failed to create A/B test {test_name}: {e}")
            raise
    
    def assign_to_ab_test(self, intent_id: str, test_id: str) -> str:
        """Assign an intent to an A/B test group"""
        
        if not hasattr(self, 'ab_tests') or test_id not in self.ab_tests:
            raise ValueError(f"A/B test {test_id} not found")
        
        test = self.ab_tests[test_id]
        if test['status'] != 'active':
            raise ValueError(f"A/B test {test_id} is not active")
        
        # Use hash of intent_id for consistent assignment
        import hashlib
        hash_value = int(hashlib.md5(intent_id.encode()).hexdigest(), 16)
        random_value = (hash_value % 10000) / 10000.0  # 0.0 to 1.0
        
        # Assign based on traffic split
        cumulative_split = 0.0
        for variant, split_ratio in test['traffic_split'].items():
            cumulative_split += split_ratio
            if random_value <= cumulative_split:
                if not hasattr(self, 'ab_test_assignments'):
                    self.ab_test_assignments = {}
                self.ab_test_assignments[intent_id] = variant
                self.logger.debug(f"Assigned intent {intent_id} to A/B test variant {variant}")
                return variant
        
        # Fallback to first variant
        first_variant = list(test['strategy_variants'])[0]
        if not hasattr(self, 'ab_test_assignments'):
            self.ab_test_assignments = {}
        self.ab_test_assignments[intent_id] = first_variant
        return first_variant
    
    def get_ab_test_variant(self, intent_id: str) -> Optional[str]:
        """Get the A/B test variant for an intent"""
        if not hasattr(self, 'ab_test_assignments'):
            return None
        return self.ab_test_assignments.get(intent_id)
    
    async def record_ab_test_outcome(self, intent_id: str, test_id: str, 
                                   performance_score: float, success: bool) -> None:
        """Record A/B test outcome"""
        
        try:
            if not hasattr(self, 'ab_tests') or test_id not in self.ab_tests:
                self.logger.warning(f"A/B test {test_id} not found for outcome recording")
                return
            
            if not hasattr(self, 'ab_test_assignments'):
                self.logger.warning(f"No A/B test assignments found")
                return
                
            variant = self.ab_test_assignments.get(intent_id)
            if not variant:
                self.logger.warning(f"No A/B test variant found for intent {intent_id}")
                return
            
            test = self.ab_tests[test_id]
            if variant in test['results']:
                test['results'][variant]['executions'] += 1
                test['results'][variant]['total_performance'] += performance_score
                if success:
                    test['results'][variant]['success_count'] += 1
                
                self.logger.debug(f"Recorded A/B test outcome for {intent_id}, variant {variant}")
            
        except Exception as e:
            self.logger.error(f"Failed to record A/B test outcome: {e}")
    
    def get_ab_test_results(self, test_id: str) -> Dict[str, Any]:
        """Get A/B test results and statistical significance"""
        
        if not hasattr(self, 'ab_tests') or test_id not in self.ab_tests:
            raise ValueError(f"A/B test {test_id} not found")
        
        test = self.ab_tests[test_id]
        results = {}
        
        for variant, data in test['results'].items():
            executions = data['executions']
            if executions > 0:
                avg_performance = data['total_performance'] / executions
                success_rate = data['success_count'] / executions
            else:
                avg_performance = 0.0
                success_rate = 0.0
            
            results[variant] = {
                'executions': executions,
                'avg_performance': avg_performance,
                'success_rate': success_rate,
                'total_performance': data['total_performance'],
                'success_count': data['success_count']
            }
        
        # Calculate statistical significance (simplified)
        if len(results) >= 2:
            variants = list(results.keys())
            variant_a = variants[0]
            variant_b = variants[1]
            
            if (results[variant_a]['executions'] >= 30 and 
                results[variant_b]['executions'] >= 30):
                
                # Simple statistical significance test
                perf_diff = abs(results[variant_a]['avg_performance'] - 
                              results[variant_b]['avg_performance'])
                
                # Consider significant if difference > 5% and both have enough samples
                is_significant = perf_diff > 0.05
                
                results['statistical_analysis'] = {
                    'is_significant': is_significant,
                    'performance_difference': perf_diff,
                    'sample_size_adequate': True,
                    'winner': variant_a if results[variant_a]['avg_performance'] > results[variant_b]['avg_performance'] else variant_b
                }
            else:
                results['statistical_analysis'] = {
                    'is_significant': False,
                    'performance_difference': 0.0,
                    'sample_size_adequate': False,
                    'winner': None
                }
        
        return results
    
    async def conclude_ab_test(self, test_id: str) -> Dict[str, Any]:
        """Conclude an A/B test and apply winning strategy"""
        
        if not hasattr(self, 'ab_tests') or test_id not in self.ab_tests:
            raise ValueError(f"A/B test {test_id} not found")
        
        test = self.ab_tests[test_id]
        test['status'] = 'concluded'
        test['concluded_at'] = datetime.now()
        
        results = self.get_ab_test_results(test_id)
        
        # Apply winning strategy if statistically significant
        if ('statistical_analysis' in results and 
            results['statistical_analysis']['is_significant']):
            
            winner = results['statistical_analysis']['winner']
            
            # Promote the winning strategy
            if winner:
                await self._promote_ab_test_winner(test_id, winner, results)
                
                self.logger.info(f"A/B test {test_id} concluded: {winner} is the winner")
        else:
            self.logger.info(f"A/B test {test_id} concluded: no statistically significant winner")
        
        # Log results to MLflow
        try:
            import mlflow
            with mlflow.start_run(run_name=f"ab_test_conclusion_{test_id}"):
                for variant, data in results.items():
                    if isinstance(data, dict) and 'avg_performance' in data:
                        mlflow.log_metric(f"{variant}_avg_performance", data['avg_performance'])
                        mlflow.log_metric(f"{variant}_success_rate", data['success_rate'])
                        mlflow.log_metric(f"{variant}_executions", data['executions'])
        except Exception as e:
            self.logger.warning(f"Failed to log A/B test results to MLflow: {e}")
        
        return results
    
    async def _promote_ab_test_winner(self, test_id: str, winner_variant: str, 
                                    results: Dict[str, Any]) -> None:
        """Promote the winning A/B test variant"""
        
        try:
            # Create strategy adjustments based on winning variant
            winner_data = results[winner_variant]
            
            # Apply positive adjustments for the winning strategy
            adjustments = {
                'cost_estimation_factor': 0.98,  # Slightly more optimistic
                'time_estimation_factor': 0.97,  # Slightly more optimistic
                'confidence_bonus': 1.05,        # Increase confidence
                'ab_test_winner': True,          # Mark as A/B test winner
                'ab_test_id': test_id,
                'performance_improvement': winner_data['avg_performance']
            }
            
            # Store adjustments
            if not hasattr(self, 'strategy_adjustments'):
                self.strategy_adjustments = {}
            
            adjustment_key = f"ab_winner_{winner_variant}"
            self.strategy_adjustments[adjustment_key] = adjustments
            
            self.logger.info(f"Promoted A/B test winner {winner_variant} from test {test_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to promote A/B test winner: {e}")
    
    def get_strategy_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for different strategies"""
        
        stats = {}
        
        for strategy_key, performances in self.strategy_performance.items():
            if performances:
                stats[strategy_key] = {
                    'avg_performance': sum(performances) / len(performances),
                    'min_performance': min(performances),
                    'max_performance': max(performances),
                    'execution_count': len(performances),
                    'recent_trend': self._calculate_performance_trend(performances)
                }
        
        return stats
    
    def _calculate_performance_trend(self, performances: List[float]) -> str:
        """Calculate performance trend (improving, declining, stable)"""
        
        if len(performances) < 10:
            return "insufficient_data"
        
        recent_avg = sum(performances[-10:]) / 10
        historical_avg = sum(performances[:-10]) / len(performances[:-10])
        
        if recent_avg > historical_avg * 1.05:
            return "improving"
        elif recent_avg < historical_avg * 0.95:
            return "declining"
        else:
            return "stable"
    
    async def get_execution_plan(self, plan_id: str) -> Optional[ExecutionPlan]:
        """Get execution plan by ID"""
        return self.strategy_cache.get(plan_id)
    
    async def update_execution_plan(self, plan_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing execution plan"""
        
        plan = self.strategy_cache.get(plan_id)
        if not plan:
            return False
        
        try:
            # Update allowed fields
            if 'priority' in updates:
                plan.priority = ExecutionPriority(updates['priority'])
            
            if 'expires_at' in updates:
                plan.expires_at = updates['expires_at']
            
            # Re-optimize if significant changes
            if 'priority' in updates:
                # Re-calculate timing and strategy based on new priority
                # This would trigger re-optimization logic
                pass
            
            self.logger.info(f"Updated execution plan {plan_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update execution plan {plan_id}: {e}")
            return False
    
    def cleanup_expired_plans(self) -> int:
        """Clean up expired execution plans"""
        
        current_time = datetime.now()
        expired_plans = []
        
        for plan_id, plan in self.strategy_cache.items():
            if plan.expires_at and plan.expires_at < current_time:
                expired_plans.append(plan_id)
        
        for plan_id in expired_plans:
            del self.strategy_cache[plan_id]
        
        self.logger.info(f"Cleaned up {len(expired_plans)} expired execution plans")
        return len(expired_plans)