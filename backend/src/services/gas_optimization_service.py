"""
Gas Optimization and Fee Management Service
Implements comprehensive gas fee estimation, optimization suggestions, and fee transparency
"""
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from src.services.web3_service import web3_service
from src.services.price_service import price_service


class GasOptimizationLevel(Enum):
    FAST = "fast"
    STANDARD = "standard"
    SLOW = "slow"
    CUSTOM = "custom"


class FeeType(Enum):
    GAS_FEE = "gas_fee"
    PROTOCOL_FEE = "protocol_fee"
    SOLVER_FEE = "solver_fee"
    BRIDGE_FEE = "bridge_fee"
    SLIPPAGE_BUFFER = "slippage_buffer"


@dataclass
class GasEstimate:
    """Gas estimation for a specific chain and operation"""
    chain_id: int
    operation_type: str
    gas_limit: int
    gas_price_gwei: Decimal
    gas_cost_eth: Decimal
    gas_cost_usd: Decimal
    confidence_level: float  # 0.0 to 1.0
    estimated_confirmation_time: int  # seconds


@dataclass
class FeeBreakdown:
    """Detailed fee breakdown for transparency"""
    fee_type: FeeType
    amount_eth: Decimal
    amount_usd: Decimal
    percentage_of_trade: Decimal
    description: str
    is_optional: bool = False


@dataclass
class OptimizationSuggestion:
    """Gas optimization suggestion"""
    suggestion_type: str
    description: str
    potential_savings_eth: Decimal
    potential_savings_usd: Decimal
    implementation_complexity: str  # "easy", "medium", "hard"
    estimated_delay: int  # additional seconds if implemented


@dataclass
class GasOptimizationResult:
    """Complete gas optimization analysis result"""
    total_gas_cost_eth: Decimal
    total_gas_cost_usd: Decimal
    fee_breakdown: List[FeeBreakdown]
    optimization_suggestions: List[OptimizationSuggestion]
    alternative_routes: List[Dict]
    user_gas_limit: Optional[Decimal]
    exceeds_user_limit: bool
    recommended_gas_level: GasOptimizationLevel


class GasOptimizationService:
    def __init__(self):
        # Chain-specific gas configurations
        self.chain_configs = {
            1: {  # Ethereum
                "name": "ethereum",
                "base_gas_price_gwei": 20,
                "fast_multiplier": 1.5,
                "slow_multiplier": 0.8,
                "max_gas_price_gwei": 200,
                "typical_confirmation_time": 180  # 3 minutes
            },
            137: {  # Polygon
                "name": "polygon",
                "base_gas_price_gwei": 30,
                "fast_multiplier": 1.3,
                "slow_multiplier": 0.9,
                "max_gas_price_gwei": 500,
                "typical_confirmation_time": 30  # 30 seconds
            },
            42161: {  # Arbitrum
                "name": "arbitrum",
                "base_gas_price_gwei": 0.1,
                "fast_multiplier": 1.2,
                "slow_multiplier": 0.95,
                "max_gas_price_gwei": 2,
                "typical_confirmation_time": 15  # 15 seconds
            },
            10: {  # Optimism
                "name": "optimism",
                "base_gas_price_gwei": 0.001,
                "fast_multiplier": 1.2,
                "slow_multiplier": 0.95,
                "max_gas_price_gwei": 0.1,
                "typical_confirmation_time": 20  # 20 seconds
            },
            56: {  # BSC
                "name": "bsc",
                "base_gas_price_gwei": 5,
                "fast_multiplier": 1.1,
                "slow_multiplier": 0.9,
                "max_gas_price_gwei": 20,
                "typical_confirmation_time": 10  # 10 seconds
            },
            8453: {  # Base
                "name": "base",
                "base_gas_price_gwei": 0.001,
                "fast_multiplier": 1.2,
                "slow_multiplier": 0.95,
                "max_gas_price_gwei": 0.1,
                "typical_confirmation_time": 15  # 15 seconds
            }
        }
        
        # Operation gas limits
        self.operation_gas_limits = {
            "simple_transfer": 21000,
            "erc20_transfer": 65000,
            "swap": 150000,
            "cross_chain_send": 200000,
            "cross_chain_receive": 100000,
            "escrow_lock": 120000,
            "escrow_release": 80000,
            "solver_bid": 100000,
            "intent_creation": 180000
        }
        
        # Protocol fee rates (as percentage of trade value)
        self.protocol_fee_rates = {
            "crossflow_protocol": Decimal('0.003'),  # 0.3%
            "layerzero_messaging": Decimal('0.001'),  # 0.1%
            "chainlink_ccip": Decimal('0.002'),  # 0.2%
        }
    
    async def estimate_comprehensive_gas_fees(
        self, 
        source_chain: int, 
        destination_chain: int,
        trade_amount_usd: Decimal,
        operations: List[str],
        gas_level: GasOptimizationLevel = GasOptimizationLevel.STANDARD
    ) -> GasOptimizationResult:
        """
        Estimate comprehensive gas fees for all chains involved in cross-chain trade
        Requirements: 8.1 - Comprehensive gas fee estimation for all chains
        """
        try:
            # Get gas estimates for both chains
            source_estimates = await self._estimate_chain_gas_fees(
                source_chain, operations, gas_level
            )
            dest_estimates = await self._estimate_chain_gas_fees(
                destination_chain, ["cross_chain_receive"], gas_level
            )
            
            # Calculate total gas costs
            total_gas_eth = sum(est.gas_cost_eth for est in source_estimates + dest_estimates)
            total_gas_usd = sum(est.gas_cost_usd for est in source_estimates + dest_estimates)
            
            # Build fee breakdown
            fee_breakdown = []
            
            # Add gas fees
            for estimate in source_estimates:
                fee_breakdown.append(FeeBreakdown(
                    fee_type=FeeType.GAS_FEE,
                    amount_eth=estimate.gas_cost_eth,
                    amount_usd=estimate.gas_cost_usd,
                    percentage_of_trade=estimate.gas_cost_usd / trade_amount_usd * 100 if trade_amount_usd > 0 else Decimal('0'),
                    description=f"Gas fee for {estimate.operation_type} on {self.chain_configs[estimate.chain_id]['name']}"
                ))
            
            for estimate in dest_estimates:
                fee_breakdown.append(FeeBreakdown(
                    fee_type=FeeType.GAS_FEE,
                    amount_eth=estimate.gas_cost_eth,
                    amount_usd=estimate.gas_cost_usd,
                    percentage_of_trade=estimate.gas_cost_usd / trade_amount_usd * 100 if trade_amount_usd > 0 else Decimal('0'),
                    description=f"Gas fee for {estimate.operation_type} on {self.chain_configs[estimate.chain_id]['name']}"
                ))
            
            # Add protocol fees
            protocol_fees = self._calculate_protocol_fees(trade_amount_usd)
            fee_breakdown.extend(protocol_fees)
            
            # Generate optimization suggestions
            optimization_suggestions = await self._generate_optimization_suggestions(
                source_chain, destination_chain, source_estimates + dest_estimates, trade_amount_usd
            )
            
            # Generate alternative routes
            alternative_routes = await self._generate_alternative_routes(
                source_chain, destination_chain, trade_amount_usd
            )
            
            return GasOptimizationResult(
                total_gas_cost_eth=total_gas_eth,
                total_gas_cost_usd=total_gas_usd,
                fee_breakdown=fee_breakdown,
                optimization_suggestions=optimization_suggestions,
                alternative_routes=alternative_routes,
                user_gas_limit=None,  # Will be set if user has limits
                exceeds_user_limit=False,
                recommended_gas_level=gas_level
            )
            
        except Exception as e:
            # Return default estimate on error
            return GasOptimizationResult(
                total_gas_cost_eth=Decimal('0.01'),
                total_gas_cost_usd=Decimal('25'),
                fee_breakdown=[],
                optimization_suggestions=[],
                alternative_routes=[],
                user_gas_limit=None,
                exceeds_user_limit=False,
                recommended_gas_level=GasOptimizationLevel.STANDARD
            )
    
    async def generate_gas_optimization_suggestions(
        self, 
        source_chain: int, 
        destination_chain: int,
        current_gas_estimates: List[GasEstimate],
        trade_amount_usd: Decimal
    ) -> List[OptimizationSuggestion]:
        """
        Generate gas optimization suggestions and alternative routing
        Requirements: 8.2 - Gas optimization suggestions and alternative routing
        """
        suggestions = []
        
        try:
            # Suggestion 1: Use L2 chains for lower fees
            if source_chain == 1:  # Ethereum mainnet
                l2_savings = await self._calculate_l2_savings(source_chain, current_gas_estimates)
                if l2_savings > Decimal('5'):  # More than $5 savings
                    suggestions.append(OptimizationSuggestion(
                        suggestion_type="use_l2_chain",
                        description=f"Consider using Arbitrum or Optimism to save ~${l2_savings:.2f} in gas fees",
                        potential_savings_eth=l2_savings / Decimal('2500'),  # Assume ETH price
                        potential_savings_usd=l2_savings,
                        implementation_complexity="easy",
                        estimated_delay=0
                    ))
            
            # Suggestion 2: Wait for lower gas prices
            if any(est.gas_price_gwei > Decimal('50') for est in current_gas_estimates):
                time_savings = await self._estimate_time_based_savings(current_gas_estimates)
                suggestions.append(OptimizationSuggestion(
                    suggestion_type="wait_for_lower_gas",
                    description=f"Gas prices are high. Waiting 2-4 hours could save ~${time_savings:.2f}",
                    potential_savings_eth=time_savings / Decimal('2500'),
                    potential_savings_usd=time_savings,
                    implementation_complexity="easy",
                    estimated_delay=7200  # 2 hours
                ))
            
            # Suggestion 3: Batch operations
            if len(current_gas_estimates) > 2:
                batch_savings = await self._calculate_batch_savings(current_gas_estimates)
                if batch_savings > Decimal('2'):
                    suggestions.append(OptimizationSuggestion(
                        suggestion_type="batch_operations",
                        description=f"Batching operations could save ~${batch_savings:.2f} in gas fees",
                        potential_savings_eth=batch_savings / Decimal('2500'),
                        potential_savings_usd=batch_savings,
                        implementation_complexity="medium",
                        estimated_delay=300  # 5 minutes additional processing
                    ))
            
            # Suggestion 4: Alternative bridge protocols
            bridge_savings = await self._calculate_bridge_alternatives(source_chain, destination_chain)
            if bridge_savings > Decimal('3'):
                suggestions.append(OptimizationSuggestion(
                    suggestion_type="alternative_bridge",
                    description=f"Using alternative bridge protocol could save ~${bridge_savings:.2f}",
                    potential_savings_eth=bridge_savings / Decimal('2500'),
                    potential_savings_usd=bridge_savings,
                    implementation_complexity="easy",
                    estimated_delay=600  # 10 minutes for different bridge
                ))
            
            # Suggestion 5: Use gas tokens (for Ethereum)
            if source_chain == 1 and trade_amount_usd > Decimal('1000'):
                gas_token_savings = current_gas_estimates[0].gas_cost_usd * Decimal('0.1')  # 10% savings
                suggestions.append(OptimizationSuggestion(
                    suggestion_type="gas_tokens",
                    description=f"Using gas tokens could save ~${gas_token_savings:.2f} for large trades",
                    potential_savings_eth=gas_token_savings / Decimal('2500'),
                    potential_savings_usd=gas_token_savings,
                    implementation_complexity="hard",
                    estimated_delay=0
                ))
            
            return suggestions
            
        except Exception as e:
            print(f"Error generating optimization suggestions: {e}")
            return []
    
    async def implement_operation_batching(
        self, 
        operations: List[Dict], 
        chain_id: int
    ) -> Dict:
        """
        Implement operation batching for cost efficiency
        Requirements: 8.3 - Operation batching for cost efficiency
        """
        try:
            if len(operations) < 2:
                return {
                    "batched": False,
                    "reason": "Insufficient operations to batch",
                    "original_operations": operations
                }
            
            # Group operations by type and compatibility
            batchable_groups = self._group_batchable_operations(operations)
            
            if not batchable_groups:
                return {
                    "batched": False,
                    "reason": "No operations can be batched together",
                    "original_operations": operations
                }
            
            # Calculate gas savings from batching
            original_gas_cost = sum(
                self.operation_gas_limits.get(op.get("type", "unknown"), 100000) 
                for op in operations
            )
            
            batched_gas_cost = 0
            batched_operations = []
            
            for group in batchable_groups:
                if len(group) > 1:
                    # Batching saves ~20% gas per additional operation
                    base_cost = self.operation_gas_limits.get(group[0].get("type", "unknown"), 100000)
                    additional_cost = sum(
                        self.operation_gas_limits.get(op.get("type", "unknown"), 100000) * 0.8
                        for op in group[1:]
                    )
                    batched_gas_cost += base_cost + additional_cost
                    
                    batched_operations.append({
                        "type": "batched_operation",
                        "operations": group,
                        "estimated_gas": int(base_cost + additional_cost)
                    })
                else:
                    # Single operation, no batching benefit
                    batched_gas_cost += self.operation_gas_limits.get(group[0].get("type", "unknown"), 100000)
                    batched_operations.append(group[0])
            
            gas_savings = original_gas_cost - batched_gas_cost
            gas_price = await self._get_current_gas_price(chain_id)
            savings_eth = Decimal(gas_savings) * gas_price / Decimal('1e9')  # Convert from gwei
            
            eth_price = await price_service.get_token_price("0x0000000000000000000000000000000000000000", 1)  # ETH price
            savings_usd = savings_eth * Decimal(str(eth_price)) if eth_price else savings_eth * Decimal('2500')
            
            return {
                "batched": True,
                "original_gas_cost": original_gas_cost,
                "batched_gas_cost": int(batched_gas_cost),
                "gas_savings": gas_savings,
                "savings_eth": str(savings_eth),
                "savings_usd": str(savings_usd),
                "batched_operations": batched_operations,
                "efficiency_improvement": f"{(gas_savings / original_gas_cost * 100):.1f}%"
            }
            
        except Exception as e:
            return {
                "batched": False,
                "reason": f"Batching error: {str(e)}",
                "original_operations": operations
            }
    
    async def enforce_user_gas_limits(
        self, 
        gas_estimate: GasOptimizationResult, 
        user_max_gas_eth: Optional[Decimal] = None,
        user_max_gas_usd: Optional[Decimal] = None
    ) -> Dict:
        """
        Enforce user-configurable gas fee limits
        Requirements: 8.4 - User-configurable gas fee limits
        """
        try:
            enforcement_result = {
                "within_limits": True,
                "user_limits": {
                    "max_gas_eth": str(user_max_gas_eth) if user_max_gas_eth else None,
                    "max_gas_usd": str(user_max_gas_usd) if user_max_gas_usd else None
                },
                "current_estimate": {
                    "total_gas_eth": str(gas_estimate.total_gas_cost_eth),
                    "total_gas_usd": str(gas_estimate.total_gas_cost_usd)
                },
                "violations": [],
                "recommendations": []
            }
            
            # Check ETH limit
            if user_max_gas_eth and gas_estimate.total_gas_cost_eth > user_max_gas_eth:
                enforcement_result["within_limits"] = False
                enforcement_result["violations"].append({
                    "type": "eth_limit_exceeded",
                    "limit": str(user_max_gas_eth),
                    "actual": str(gas_estimate.total_gas_cost_eth),
                    "excess": str(gas_estimate.total_gas_cost_eth - user_max_gas_eth)
                })
                
                # Generate recommendations to stay within limit
                enforcement_result["recommendations"].extend(
                    await self._generate_limit_compliance_recommendations(
                        gas_estimate, user_max_gas_eth, "eth"
                    )
                )
            
            # Check USD limit
            if user_max_gas_usd and gas_estimate.total_gas_cost_usd > user_max_gas_usd:
                enforcement_result["within_limits"] = False
                enforcement_result["violations"].append({
                    "type": "usd_limit_exceeded",
                    "limit": str(user_max_gas_usd),
                    "actual": str(gas_estimate.total_gas_cost_usd),
                    "excess": str(gas_estimate.total_gas_cost_usd - user_max_gas_usd)
                })
                
                # Generate recommendations to stay within limit
                enforcement_result["recommendations"].extend(
                    await self._generate_limit_compliance_recommendations(
                        gas_estimate, user_max_gas_usd, "usd"
                    )
                )
            
            # Update gas estimate with limit information
            gas_estimate.user_gas_limit = user_max_gas_eth or user_max_gas_usd
            gas_estimate.exceeds_user_limit = not enforcement_result["within_limits"]
            
            return enforcement_result
            
        except Exception as e:
            return {
                "within_limits": True,
                "error": f"Limit enforcement error: {str(e)}"
            }
    
    async def generate_fee_transparency_report(
        self, 
        gas_estimate: GasOptimizationResult,
        trade_amount_usd: Decimal,
        execution_paths: List[Dict]
    ) -> Dict:
        """
        Generate detailed fee breakdown for transparency
        Requirements: 8.5 - Detailed fee breakdown display
        """
        try:
            # Calculate total fees across all categories
            total_fees_usd = sum(fee.amount_usd for fee in gas_estimate.fee_breakdown)
            total_fees_eth = sum(fee.amount_eth for fee in gas_estimate.fee_breakdown)
            
            # Group fees by type
            fee_categories = {}
            for fee in gas_estimate.fee_breakdown:
                category = fee.fee_type.value
                if category not in fee_categories:
                    fee_categories[category] = {
                        "total_usd": Decimal('0'),
                        "total_eth": Decimal('0'),
                        "items": []
                    }
                
                fee_categories[category]["total_usd"] += fee.amount_usd
                fee_categories[category]["total_eth"] += fee.amount_eth
                fee_categories[category]["items"].append({
                    "description": fee.description,
                    "amount_usd": str(fee.amount_usd),
                    "amount_eth": str(fee.amount_eth),
                    "percentage_of_trade": str(fee.percentage_of_trade),
                    "is_optional": fee.is_optional
                })
            
            # Compare with alternative execution paths
            path_comparisons = []
            for path in execution_paths:
                path_comparisons.append({
                    "path_name": path.get("name", "Alternative Path"),
                    "total_fees_usd": str(path.get("total_fees_usd", "0")),
                    "savings_vs_current": str(total_fees_usd - Decimal(str(path.get("total_fees_usd", total_fees_usd)))),
                    "execution_time": path.get("execution_time", "unknown"),
                    "complexity": path.get("complexity", "medium")
                })
            
            # Calculate fee efficiency metrics
            fee_efficiency = {
                "total_fees_percentage": str((total_fees_usd / trade_amount_usd * 100) if trade_amount_usd > 0 else Decimal('0')),
                "gas_fees_percentage": str(sum(
                    fee.amount_usd for fee in gas_estimate.fee_breakdown 
                    if fee.fee_type == FeeType.GAS_FEE
                ) / trade_amount_usd * 100 if trade_amount_usd > 0 else Decimal('0')),
                "protocol_fees_percentage": str(sum(
                    fee.amount_usd for fee in gas_estimate.fee_breakdown 
                    if fee.fee_type == FeeType.PROTOCOL_FEE
                ) / trade_amount_usd * 100 if trade_amount_usd > 0 else Decimal('0')),
                "efficiency_rating": self._calculate_efficiency_rating(total_fees_usd, trade_amount_usd)
            }
            
            return {
                "summary": {
                    "total_fees_usd": str(total_fees_usd),
                    "total_fees_eth": str(total_fees_eth),
                    "trade_amount_usd": str(trade_amount_usd),
                    "fee_percentage": fee_efficiency["total_fees_percentage"]
                },
                "fee_categories": {
                    category: {
                        "total_usd": str(data["total_usd"]),
                        "total_eth": str(data["total_eth"]),
                        "percentage_of_total": str(data["total_usd"] / total_fees_usd * 100 if total_fees_usd > 0 else Decimal('0')),
                        "items": data["items"]
                    }
                    for category, data in fee_categories.items()
                },
                "path_comparisons": path_comparisons,
                "efficiency_metrics": fee_efficiency,
                "optimization_potential": {
                    "total_potential_savings": str(sum(
                        opt.potential_savings_usd for opt in gas_estimate.optimization_suggestions
                    )),
                    "easy_savings": str(sum(
                        opt.potential_savings_usd for opt in gas_estimate.optimization_suggestions
                        if opt.implementation_complexity == "easy"
                    )),
                    "top_recommendation": gas_estimate.optimization_suggestions[0].description if gas_estimate.optimization_suggestions else None
                },
                "transparency_score": self._calculate_transparency_score(gas_estimate.fee_breakdown),
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "error": f"Fee transparency report generation error: {str(e)}",
                "summary": {
                    "total_fees_usd": "0",
                    "total_fees_eth": "0",
                    "trade_amount_usd": str(trade_amount_usd),
                    "fee_percentage": "0"
                }
            }
    
    # Private helper methods
    
    async def _estimate_chain_gas_fees(
        self, 
        chain_id: int, 
        operations: List[str],
        gas_level: GasOptimizationLevel
    ) -> List[GasEstimate]:
        """Estimate gas fees for operations on a specific chain"""
        estimates = []
        
        try:
            chain_config = self.chain_configs.get(chain_id)
            if not chain_config:
                return estimates
            
            # Get current gas price
            current_gas_price = await self._get_current_gas_price(chain_id)
            
            # Apply gas level multiplier
            multipliers = {
                GasOptimizationLevel.FAST: chain_config["fast_multiplier"],
                GasOptimizationLevel.STANDARD: 1.0,
                GasOptimizationLevel.SLOW: chain_config["slow_multiplier"],
                GasOptimizationLevel.CUSTOM: 1.0
            }
            
            adjusted_gas_price = current_gas_price * Decimal(str(multipliers[gas_level]))
            
            # Get ETH price for USD conversion
            eth_price = await price_service.get_token_price("0x0000000000000000000000000000000000000000", 1)
            eth_price_decimal = Decimal(str(eth_price)) if eth_price else Decimal('2500')
            
            for operation in operations:
                gas_limit = self.operation_gas_limits.get(operation, 100000)
                gas_cost_eth = Decimal(gas_limit) * adjusted_gas_price / Decimal('1e9')  # Convert from gwei
                gas_cost_usd = gas_cost_eth * eth_price_decimal
                
                estimates.append(GasEstimate(
                    chain_id=chain_id,
                    operation_type=operation,
                    gas_limit=gas_limit,
                    gas_price_gwei=adjusted_gas_price,
                    gas_cost_eth=gas_cost_eth,
                    gas_cost_usd=gas_cost_usd,
                    confidence_level=0.85,  # Default confidence
                    estimated_confirmation_time=chain_config["typical_confirmation_time"]
                ))
            
            return estimates
            
        except Exception as e:
            print(f"Error estimating gas fees for chain {chain_id}: {e}")
            return []
    
    async def _get_current_gas_price(self, chain_id: int) -> Decimal:
        """Get current gas price for a chain"""
        try:
            # In production, would fetch from web3 service or gas oracle
            chain_config = self.chain_configs.get(chain_id)
            if chain_config:
                return Decimal(str(chain_config["base_gas_price_gwei"]))
            return Decimal('20')  # Default fallback
        except Exception:
            return Decimal('20')  # Default fallback
    
    def _calculate_protocol_fees(self, trade_amount_usd: Decimal) -> List[FeeBreakdown]:
        """Calculate protocol fees"""
        fees = []
        
        for protocol, rate in self.protocol_fee_rates.items():
            fee_usd = trade_amount_usd * rate
            fee_eth = fee_usd / Decimal('2500')  # Assume ETH price
            
            fees.append(FeeBreakdown(
                fee_type=FeeType.PROTOCOL_FEE,
                amount_eth=fee_eth,
                amount_usd=fee_usd,
                percentage_of_trade=rate * 100,
                description=f"{protocol.replace('_', ' ').title()} protocol fee"
            ))
        
        return fees
    
    async def _generate_optimization_suggestions(
        self, 
        source_chain: int, 
        dest_chain: int,
        gas_estimates: List[GasEstimate],
        trade_amount_usd: Decimal
    ) -> List[OptimizationSuggestion]:
        """Generate optimization suggestions"""
        return await self.generate_gas_optimization_suggestions(
            source_chain, dest_chain, gas_estimates, trade_amount_usd
        )
    
    async def _generate_alternative_routes(
        self, 
        source_chain: int, 
        dest_chain: int,
        trade_amount_usd: Decimal
    ) -> List[Dict]:
        """Generate alternative routing options"""
        alternatives = []
        
        # Alternative 1: Direct bridge vs multi-hop
        if source_chain != dest_chain:
            alternatives.append({
                "name": "Direct Bridge",
                "description": f"Direct bridge from {self.chain_configs[source_chain]['name']} to {self.chain_configs[dest_chain]['name']}",
                "estimated_time": "15-30 minutes",
                "estimated_cost_usd": "15-25",
                "complexity": "low"
            })
            
            alternatives.append({
                "name": "Multi-hop via Ethereum",
                "description": "Route through Ethereum mainnet for better liquidity",
                "estimated_time": "20-45 minutes",
                "estimated_cost_usd": "25-40",
                "complexity": "medium"
            })
        
        return alternatives
    
    async def _calculate_l2_savings(self, source_chain: int, estimates: List[GasEstimate]) -> Decimal:
        """Calculate potential savings by using L2 chains"""
        if source_chain != 1:  # Not Ethereum mainnet
            return Decimal('0')
        
        # Estimate L2 costs (typically 10-100x cheaper)
        l2_multiplier = Decimal('0.05')  # 5% of mainnet cost
        current_cost = sum(est.gas_cost_usd for est in estimates)
        l2_cost = current_cost * l2_multiplier
        
        return current_cost - l2_cost
    
    async def _estimate_time_based_savings(self, estimates: List[GasEstimate]) -> Decimal:
        """Estimate savings from waiting for lower gas prices"""
        current_cost = sum(est.gas_cost_usd for est in estimates)
        # Assume 30% savings during off-peak hours
        return current_cost * Decimal('0.3')
    
    async def _calculate_batch_savings(self, estimates: List[GasEstimate]) -> Decimal:
        """Calculate savings from batching operations"""
        total_cost = sum(est.gas_cost_usd for est in estimates)
        # Batching typically saves 15-25%
        return total_cost * Decimal('0.2')
    
    async def _calculate_bridge_alternatives(self, source_chain: int, dest_chain: int) -> Decimal:
        """Calculate savings from alternative bridge protocols"""
        # Different bridges have different fee structures
        return Decimal('5')  # Assume $5 average savings
    
    def _group_batchable_operations(self, operations: List[Dict]) -> List[List[Dict]]:
        """Group operations that can be batched together"""
        # Simple grouping by operation type
        groups = {}
        
        for op in operations:
            op_type = op.get("type", "unknown")
            if op_type not in groups:
                groups[op_type] = []
            groups[op_type].append(op)
        
        return list(groups.values())
    
    async def _generate_limit_compliance_recommendations(
        self, 
        gas_estimate: GasOptimizationResult,
        limit: Decimal,
        limit_type: str
    ) -> List[Dict]:
        """Generate recommendations to comply with user gas limits"""
        recommendations = []
        
        # Recommend using slower gas settings
        recommendations.append({
            "type": "reduce_gas_speed",
            "description": "Use slower gas settings to reduce costs",
            "potential_savings": "10-30%",
            "trade_off": "Longer confirmation time"
        })
        
        # Recommend alternative chains
        recommendations.append({
            "type": "alternative_chain",
            "description": "Consider using lower-cost chains like Polygon or Arbitrum",
            "potential_savings": "50-90%",
            "trade_off": "Different ecosystem"
        })
        
        return recommendations
    
    def _calculate_efficiency_rating(self, total_fees: Decimal, trade_amount: Decimal) -> str:
        """Calculate fee efficiency rating"""
        if trade_amount == 0:
            return "unknown"
        
        fee_percentage = total_fees / trade_amount * 100
        
        if fee_percentage < Decimal('0.5'):
            return "excellent"
        elif fee_percentage < Decimal('1.0'):
            return "good"
        elif fee_percentage < Decimal('2.0'):
            return "fair"
        else:
            return "poor"
    
    def _calculate_transparency_score(self, fee_breakdown: List[FeeBreakdown]) -> float:
        """Calculate transparency score based on fee breakdown completeness"""
        if not fee_breakdown:
            return 0.0
        
        # Score based on number of fee categories covered
        fee_types_covered = len(set(fee.fee_type for fee in fee_breakdown))
        max_fee_types = len(FeeType)
        
        return min(1.0, fee_types_covered / max_fee_types)


# Global instance
gas_optimization_service = GasOptimizationService()