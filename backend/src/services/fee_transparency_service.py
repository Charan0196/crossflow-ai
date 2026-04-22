"""
Fee Transparency Service
Provides detailed fee breakdown display and comparison across execution paths
"""
from typing import Dict, List, Optional, Any
from decimal import Decimal
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

from src.services.gas_optimization_service import GasOptimizationResult, FeeBreakdown, FeeType


class ExecutionPath(Enum):
    DIRECT = "direct"
    MULTI_HOP = "multi_hop"
    OPTIMIZED = "optimized"
    FASTEST = "fastest"
    CHEAPEST = "cheapest"


@dataclass
class PathComparison:
    """Comparison between different execution paths"""
    path_name: str
    path_type: ExecutionPath
    total_fees_usd: Decimal
    total_fees_eth: Decimal
    execution_time_minutes: int
    gas_fees_usd: Decimal
    protocol_fees_usd: Decimal
    solver_fees_usd: Decimal
    bridge_fees_usd: Decimal
    success_probability: float
    complexity_score: int  # 1-10, 1 being simplest
    recommended: bool = False


@dataclass
class FeeTransparencyReport:
    """Comprehensive fee transparency report"""
    trade_summary: Dict[str, Any]
    fee_breakdown: List[FeeBreakdown]
    path_comparisons: List[PathComparison]
    cost_analysis: Dict[str, Any]
    savings_opportunities: List[Dict[str, Any]]
    transparency_metrics: Dict[str, Any]
    generated_at: datetime


class FeeTransparencyService:
    def __init__(self):
        self.fee_categories = {
            FeeType.GAS_FEE: {
                "display_name": "Network Gas Fees",
                "description": "Fees paid to blockchain validators for transaction processing",
                "color": "#FF6B6B",
                "is_variable": True
            },
            FeeType.PROTOCOL_FEE: {
                "display_name": "Protocol Fees",
                "description": "Fees charged by CrossFlow AI protocol for service",
                "color": "#4ECDC4",
                "is_variable": False
            },
            FeeType.SOLVER_FEE: {
                "display_name": "Solver Fees",
                "description": "Fees paid to market makers for trade execution",
                "color": "#45B7D1",
                "is_variable": True
            },
            FeeType.BRIDGE_FEE: {
                "display_name": "Bridge Fees",
                "description": "Fees for cross-chain asset transfers",
                "color": "#96CEB4",
                "is_variable": True
            },
            FeeType.SLIPPAGE_BUFFER: {
                "display_name": "Slippage Protection",
                "description": "Buffer to protect against price movements during execution",
                "color": "#FFEAA7",
                "is_variable": True
            }
        }
    
    async def generate_comprehensive_fee_report(
        self,
        trade_amount_usd: Decimal,
        input_token: str,
        output_token: str,
        source_chain: int,
        destination_chain: int,
        gas_optimization_result: GasOptimizationResult,
        execution_paths: Optional[List[Dict]] = None
    ) -> FeeTransparencyReport:
        """
        Generate comprehensive fee transparency report
        Requirements: 8.5 - Detailed fee breakdown display
        """
        try:
            # Build trade summary
            trade_summary = {
                "trade_amount_usd": str(trade_amount_usd),
                "input_token": input_token,
                "output_token": output_token,
                "source_chain": source_chain,
                "destination_chain": destination_chain,
                "is_cross_chain": source_chain != destination_chain,
                "estimated_execution_time": "15-30 minutes" if source_chain != destination_chain else "2-5 minutes"
            }
            
            # Generate path comparisons
            path_comparisons = self._generate_path_comparisons(
                trade_amount_usd, source_chain, destination_chain, gas_optimization_result, execution_paths
            )
            
            # Perform cost analysis
            cost_analysis = self._perform_cost_analysis(
                trade_amount_usd, gas_optimization_result.fee_breakdown, path_comparisons
            )
            
            # Identify savings opportunities
            savings_opportunities = self._identify_savings_opportunities(
                gas_optimization_result, path_comparisons
            )
            
            # Calculate transparency metrics
            transparency_metrics = self._calculate_transparency_metrics(
                gas_optimization_result.fee_breakdown, path_comparisons
            )
            
            return FeeTransparencyReport(
                trade_summary=trade_summary,
                fee_breakdown=gas_optimization_result.fee_breakdown,
                path_comparisons=path_comparisons,
                cost_analysis=cost_analysis,
                savings_opportunities=savings_opportunities,
                transparency_metrics=transparency_metrics,
                generated_at=datetime.now()
            )
            
        except Exception as e:
            # Return minimal report on error
            return FeeTransparencyReport(
                trade_summary={"error": f"Report generation failed: {str(e)}"},
                fee_breakdown=[],
                path_comparisons=[],
                cost_analysis={},
                savings_opportunities=[],
                transparency_metrics={},
                generated_at=datetime.now()
            )
    
    async def compare_execution_paths(
        self,
        trade_amount_usd: Decimal,
        source_chain: int,
        destination_chain: int,
        base_gas_result: GasOptimizationResult
    ) -> List[PathComparison]:
        """
        Compare different execution paths for the trade
        Requirements: 8.5 - Fee comparison across different execution paths
        """
        comparisons = []
        
        try:
            # Path 1: Direct execution (current path)
            direct_path = PathComparison(
                path_name="Direct Execution",
                path_type=ExecutionPath.DIRECT,
                total_fees_usd=base_gas_result.total_gas_cost_usd + self._calculate_protocol_fees_total(trade_amount_usd),
                total_fees_eth=base_gas_result.total_gas_cost_eth,
                execution_time_minutes=20 if source_chain != destination_chain else 3,
                gas_fees_usd=base_gas_result.total_gas_cost_usd,
                protocol_fees_usd=self._calculate_protocol_fees_total(trade_amount_usd),
                solver_fees_usd=trade_amount_usd * Decimal('0.002'),  # 0.2% solver fee
                bridge_fees_usd=Decimal('5') if source_chain != destination_chain else Decimal('0'),
                success_probability=0.95,
                complexity_score=3,
                recommended=True
            )
            comparisons.append(direct_path)
            
            # Path 2: Multi-hop via Ethereum (if not already on Ethereum)
            if source_chain != 1 and destination_chain != 1:
                multihop_fees = base_gas_result.total_gas_cost_usd * Decimal('1.4')  # 40% more gas
                multihop_path = PathComparison(
                    path_name="Multi-hop via Ethereum",
                    path_type=ExecutionPath.MULTI_HOP,
                    total_fees_usd=multihop_fees + self._calculate_protocol_fees_total(trade_amount_usd) * Decimal('1.2'),
                    total_fees_eth=base_gas_result.total_gas_cost_eth * Decimal('1.4'),
                    execution_time_minutes=35,
                    gas_fees_usd=multihop_fees,
                    protocol_fees_usd=self._calculate_protocol_fees_total(trade_amount_usd) * Decimal('1.2'),
                    solver_fees_usd=trade_amount_usd * Decimal('0.003'),  # Higher solver fee
                    bridge_fees_usd=Decimal('12'),  # Two bridge operations
                    success_probability=0.92,
                    complexity_score=6
                )
                comparisons.append(multihop_path)
            
            # Path 3: Optimized route (using L2s when possible)
            if source_chain == 1:  # Starting from Ethereum
                optimized_fees = base_gas_result.total_gas_cost_usd * Decimal('0.3')  # 70% savings on L2
                optimized_path = PathComparison(
                    path_name="L2 Optimized Route",
                    path_type=ExecutionPath.OPTIMIZED,
                    total_fees_usd=optimized_fees + self._calculate_protocol_fees_total(trade_amount_usd),
                    total_fees_eth=base_gas_result.total_gas_cost_eth * Decimal('0.3'),
                    execution_time_minutes=25,
                    gas_fees_usd=optimized_fees,
                    protocol_fees_usd=self._calculate_protocol_fees_total(trade_amount_usd),
                    solver_fees_usd=trade_amount_usd * Decimal('0.0015'),  # Lower solver fee
                    bridge_fees_usd=Decimal('3'),  # Cheaper L2 bridge
                    success_probability=0.93,
                    complexity_score=4
                )
                comparisons.append(optimized_path)
            
            # Path 4: Fastest execution (higher gas, premium solvers)
            fastest_fees = base_gas_result.total_gas_cost_usd * Decimal('1.8')  # 80% more for speed
            fastest_path = PathComparison(
                path_name="Fastest Execution",
                path_type=ExecutionPath.FASTEST,
                total_fees_usd=fastest_fees + self._calculate_protocol_fees_total(trade_amount_usd) * Decimal('1.1'),
                total_fees_eth=base_gas_result.total_gas_cost_eth * Decimal('1.8'),
                execution_time_minutes=8 if source_chain != destination_chain else 1,
                gas_fees_usd=fastest_fees,
                protocol_fees_usd=self._calculate_protocol_fees_total(trade_amount_usd) * Decimal('1.1'),
                solver_fees_usd=trade_amount_usd * Decimal('0.004'),  # Premium solver fee
                bridge_fees_usd=Decimal('8') if source_chain != destination_chain else Decimal('0'),
                success_probability=0.98,
                complexity_score=2
            )
            comparisons.append(fastest_path)
            
            # Path 5: Cheapest execution (slower, economy settings)
            cheapest_fees = base_gas_result.total_gas_cost_usd * Decimal('0.6')  # 40% savings
            cheapest_path = PathComparison(
                path_name="Economy Execution",
                path_type=ExecutionPath.CHEAPEST,
                total_fees_usd=cheapest_fees + self._calculate_protocol_fees_total(trade_amount_usd) * Decimal('0.9'),
                total_fees_eth=base_gas_result.total_gas_cost_eth * Decimal('0.6'),
                execution_time_minutes=45 if source_chain != destination_chain else 8,
                gas_fees_usd=cheapest_fees,
                protocol_fees_usd=self._calculate_protocol_fees_total(trade_amount_usd) * Decimal('0.9'),
                solver_fees_usd=trade_amount_usd * Decimal('0.001'),  # Lower solver fee
                bridge_fees_usd=Decimal('3') if source_chain != destination_chain else Decimal('0'),
                success_probability=0.88,
                complexity_score=5
            )
            comparisons.append(cheapest_path)
            
            # Sort by total fees and mark the cheapest as recommended if savings > 20%
            comparisons.sort(key=lambda x: x.total_fees_usd)
            if len(comparisons) > 1:
                cheapest = comparisons[0]
                most_expensive = comparisons[-1]
                savings_percentage = (most_expensive.total_fees_usd - cheapest.total_fees_usd) / most_expensive.total_fees_usd
                
                if savings_percentage > Decimal('0.2'):  # More than 20% savings
                    # Reset recommendations
                    for comp in comparisons:
                        comp.recommended = False
                    cheapest.recommended = True
            
            return comparisons
            
        except Exception as e:
            print(f"Error comparing execution paths: {e}")
            return []
    
    def format_fee_breakdown_for_display(
        self, 
        fee_breakdown: List[FeeBreakdown],
        trade_amount_usd: Decimal
    ) -> Dict[str, Any]:
        """
        Format fee breakdown for user-friendly display
        Requirements: 8.5 - Show protocol fees, gas costs, and solver fees
        """
        try:
            # Group fees by category
            categorized_fees = {}
            total_fees_usd = Decimal('0')
            total_fees_eth = Decimal('0')
            
            for fee in fee_breakdown:
                category = fee.fee_type
                category_info = self.fee_categories.get(category, {
                    "display_name": category.value.replace('_', ' ').title(),
                    "description": f"{category.value} fees",
                    "color": "#95A5A6",
                    "is_variable": True
                })
                
                if category not in categorized_fees:
                    categorized_fees[category] = {
                        "display_name": category_info["display_name"],
                        "description": category_info["description"],
                        "color": category_info["color"],
                        "is_variable": category_info["is_variable"],
                        "total_usd": Decimal('0'),
                        "total_eth": Decimal('0'),
                        "items": []
                    }
                
                categorized_fees[category]["total_usd"] += fee.amount_usd
                categorized_fees[category]["total_eth"] += fee.amount_eth
                categorized_fees[category]["items"].append({
                    "description": fee.description,
                    "amount_usd": str(fee.amount_usd),
                    "amount_eth": str(fee.amount_eth),
                    "percentage_of_trade": str(fee.percentage_of_trade),
                    "is_optional": fee.is_optional
                })
                
                total_fees_usd += fee.amount_usd
                total_fees_eth += fee.amount_eth
            
            # Calculate percentages and format for display
            formatted_categories = {}
            for category, data in categorized_fees.items():
                percentage_of_total = (data["total_usd"] / total_fees_usd * 100) if total_fees_usd > 0 else Decimal('0')
                percentage_of_trade = (data["total_usd"] / trade_amount_usd * 100) if trade_amount_usd > 0 else Decimal('0')
                
                formatted_categories[category.value] = {
                    "display_name": data["display_name"],
                    "description": data["description"],
                    "color": data["color"],
                    "is_variable": data["is_variable"],
                    "total_usd": str(data["total_usd"]),
                    "total_eth": str(data["total_eth"]),
                    "percentage_of_total_fees": f"{percentage_of_total:.1f}%",
                    "percentage_of_trade_value": f"{percentage_of_trade:.2f}%",
                    "items": data["items"]
                }
            
            return {
                "summary": {
                    "total_fees_usd": str(total_fees_usd),
                    "total_fees_eth": str(total_fees_eth),
                    "trade_amount_usd": str(trade_amount_usd),
                    "total_fee_percentage": f"{(total_fees_usd / trade_amount_usd * 100) if trade_amount_usd > 0 else Decimal('0'):.2f}%",
                    "number_of_fee_types": len(categorized_fees)
                },
                "categories": formatted_categories,
                "visual_data": self._generate_visual_data(categorized_fees, total_fees_usd),
                "cost_efficiency": self._assess_cost_efficiency(total_fees_usd, trade_amount_usd)
            }
            
        except Exception as e:
            return {
                "error": f"Fee formatting error: {str(e)}",
                "summary": {
                    "total_fees_usd": "0",
                    "total_fees_eth": "0",
                    "trade_amount_usd": str(trade_amount_usd),
                    "total_fee_percentage": "0%"
                }
            }
    
    def _generate_path_comparisons(
        self,
        trade_amount_usd: Decimal,
        source_chain: int,
        destination_chain: int,
        gas_result: GasOptimizationResult,
        execution_paths: Optional[List[Dict]]
    ) -> List[PathComparison]:
        """Generate path comparisons from gas optimization result"""
        # Create path comparisons synchronously to avoid asyncio issues
        comparisons = []
        
        try:
            # Path 1: Direct execution (current path)
            direct_path = PathComparison(
                path_name="Direct Execution",
                path_type=ExecutionPath.DIRECT,
                total_fees_usd=gas_result.total_gas_cost_usd + self._calculate_protocol_fees_total(trade_amount_usd),
                total_fees_eth=gas_result.total_gas_cost_eth,
                execution_time_minutes=20 if source_chain != destination_chain else 3,
                gas_fees_usd=gas_result.total_gas_cost_usd,
                protocol_fees_usd=self._calculate_protocol_fees_total(trade_amount_usd),
                solver_fees_usd=trade_amount_usd * Decimal('0.002'),  # 0.2% solver fee
                bridge_fees_usd=Decimal('5') if source_chain != destination_chain else Decimal('0'),
                success_probability=0.95,
                complexity_score=3,
                recommended=True
            )
            comparisons.append(direct_path)
            
            # Path 2: Economy execution (slower, cheaper)
            cheapest_fees = gas_result.total_gas_cost_usd * Decimal('0.6')  # 40% savings
            cheapest_path = PathComparison(
                path_name="Economy Execution",
                path_type=ExecutionPath.CHEAPEST,
                total_fees_usd=cheapest_fees + self._calculate_protocol_fees_total(trade_amount_usd) * Decimal('0.9'),
                total_fees_eth=gas_result.total_gas_cost_eth * Decimal('0.6'),
                execution_time_minutes=45 if source_chain != destination_chain else 8,
                gas_fees_usd=cheapest_fees,
                protocol_fees_usd=self._calculate_protocol_fees_total(trade_amount_usd) * Decimal('0.9'),
                solver_fees_usd=trade_amount_usd * Decimal('0.001'),  # Lower solver fee
                bridge_fees_usd=Decimal('3') if source_chain != destination_chain else Decimal('0'),
                success_probability=0.88,
                complexity_score=5
            )
            comparisons.append(cheapest_path)
            
            return comparisons
            
        except Exception as e:
            print(f"Error generating path comparisons: {e}")
            return [direct_path] if 'direct_path' in locals() else []
    
    def _perform_cost_analysis(
        self,
        trade_amount_usd: Decimal,
        fee_breakdown: List[FeeBreakdown],
        path_comparisons: List[PathComparison]
    ) -> Dict[str, Any]:
        """Perform comprehensive cost analysis"""
        total_fees = sum(fee.amount_usd for fee in fee_breakdown)
        
        # Find best and worst paths
        if path_comparisons:
            cheapest_path = min(path_comparisons, key=lambda x: x.total_fees_usd)
            most_expensive_path = max(path_comparisons, key=lambda x: x.total_fees_usd)
            fastest_path = min(path_comparisons, key=lambda x: x.execution_time_minutes)
        else:
            cheapest_path = most_expensive_path = fastest_path = None
        
        return {
            "fee_to_trade_ratio": str((total_fees / trade_amount_usd * 100) if trade_amount_usd > 0 else Decimal('0')),
            "cost_efficiency_rating": self._get_efficiency_rating(total_fees, trade_amount_usd),
            "cheapest_path": {
                "name": cheapest_path.path_name if cheapest_path else "Unknown",
                "total_fees": str(cheapest_path.total_fees_usd) if cheapest_path else "0",
                "savings_vs_current": str(total_fees - cheapest_path.total_fees_usd) if cheapest_path else "0"
            } if cheapest_path else None,
            "fastest_path": {
                "name": fastest_path.path_name if fastest_path else "Unknown",
                "execution_time": fastest_path.execution_time_minutes if fastest_path else 0,
                "additional_cost": str(fastest_path.total_fees_usd - total_fees) if fastest_path else "0"
            } if fastest_path else None,
            "fee_volatility": self._calculate_fee_volatility(path_comparisons),
            "optimization_potential": str(
                (most_expensive_path.total_fees_usd - cheapest_path.total_fees_usd) 
                if cheapest_path and most_expensive_path else Decimal('0')
            )
        }
    
    def _identify_savings_opportunities(
        self,
        gas_result: GasOptimizationResult,
        path_comparisons: List[PathComparison]
    ) -> List[Dict[str, Any]]:
        """Identify potential savings opportunities"""
        opportunities = []
        
        # From gas optimization suggestions
        for suggestion in gas_result.optimization_suggestions:
            opportunities.append({
                "type": "gas_optimization",
                "title": suggestion.suggestion_type.replace('_', ' ').title(),
                "description": suggestion.description,
                "potential_savings_usd": str(suggestion.potential_savings_usd),
                "implementation_effort": suggestion.implementation_complexity,
                "estimated_delay": suggestion.estimated_delay
            })
        
        # From path comparisons
        if path_comparisons:
            current_path = next((p for p in path_comparisons if p.recommended), path_comparisons[0])
            cheapest_path = min(path_comparisons, key=lambda x: x.total_fees_usd)
            
            if cheapest_path != current_path:
                savings = current_path.total_fees_usd - cheapest_path.total_fees_usd
                if savings > Decimal('1'):  # More than $1 savings
                    opportunities.append({
                        "type": "alternative_path",
                        "title": f"Switch to {cheapest_path.path_name}",
                        "description": f"Save ${savings:.2f} by using {cheapest_path.path_name.lower()}",
                        "potential_savings_usd": str(savings),
                        "implementation_effort": "easy",
                        "estimated_delay": max(0, cheapest_path.execution_time_minutes - current_path.execution_time_minutes) * 60
                    })
        
        return opportunities
    
    def _calculate_transparency_metrics(
        self,
        fee_breakdown: List[FeeBreakdown],
        path_comparisons: List[PathComparison]
    ) -> Dict[str, Any]:
        """Calculate transparency and trust metrics"""
        return {
            "fee_categories_covered": len(set(fee.fee_type for fee in fee_breakdown)),
            "total_fee_items": len(fee_breakdown),
            "optional_fees_count": sum(1 for fee in fee_breakdown if fee.is_optional),
            "path_options_provided": len(path_comparisons),
            "transparency_score": self._calculate_transparency_score(fee_breakdown, path_comparisons),
            "trust_indicators": {
                "all_fees_disclosed": len(fee_breakdown) > 0,
                "multiple_paths_shown": len(path_comparisons) > 1,
                "optional_fees_marked": any(fee.is_optional for fee in fee_breakdown),
                "success_probabilities_shown": all(hasattr(p, 'success_probability') for p in path_comparisons)
            }
        }
    
    def _calculate_protocol_fees_total(self, trade_amount_usd: Decimal) -> Decimal:
        """Calculate total protocol fees"""
        return trade_amount_usd * Decimal('0.005')  # 0.5% total protocol fees
    
    def _generate_visual_data(self, categorized_fees: Dict, total_fees: Decimal) -> Dict[str, Any]:
        """Generate data for visual fee breakdown (pie chart, etc.)"""
        chart_data = []
        
        for category, data in categorized_fees.items():
            percentage = (data["total_usd"] / total_fees * 100) if total_fees > 0 else 0
            chart_data.append({
                "label": data["display_name"],
                "value": float(percentage),
                "amount_usd": str(data["total_usd"]),
                "color": data["color"]
            })
        
        return {
            "pie_chart_data": chart_data,
            "bar_chart_data": sorted(chart_data, key=lambda x: x["value"], reverse=True)
        }
    
    def _assess_cost_efficiency(self, total_fees: Decimal, trade_amount: Decimal) -> Dict[str, Any]:
        """Assess cost efficiency of the trade"""
        if trade_amount == 0:
            return {"rating": "unknown", "percentage": "0%"}
        
        fee_percentage = total_fees / trade_amount * 100
        
        if fee_percentage < Decimal('0.5'):
            rating = "excellent"
            color = "#27AE60"
        elif fee_percentage < Decimal('1.0'):
            rating = "good"
            color = "#F39C12"
        elif fee_percentage < Decimal('2.0'):
            rating = "fair"
            color = "#E67E22"
        else:
            rating = "poor"
            color = "#E74C3C"
        
        return {
            "rating": rating,
            "percentage": f"{fee_percentage:.2f}%",
            "color": color,
            "description": self._get_efficiency_description(rating)
        }
    
    def _get_efficiency_rating(self, total_fees: Decimal, trade_amount: Decimal) -> str:
        """Get efficiency rating string"""
        return self._assess_cost_efficiency(total_fees, trade_amount)["rating"]
    
    def _get_efficiency_description(self, rating: str) -> str:
        """Get description for efficiency rating"""
        descriptions = {
            "excellent": "Very low fees relative to trade size",
            "good": "Reasonable fees for this trade size",
            "fair": "Moderate fees, consider optimization",
            "poor": "High fees, strongly consider alternatives"
        }
        return descriptions.get(rating, "Unknown efficiency")
    
    def _calculate_fee_volatility(self, path_comparisons: List[PathComparison]) -> str:
        """Calculate fee volatility across different paths"""
        if len(path_comparisons) < 2:
            return "low"
        
        fees = [float(p.total_fees_usd) for p in path_comparisons]
        min_fee = min(fees)
        max_fee = max(fees)
        
        if min_fee == 0:
            return "high"
        
        volatility_ratio = (max_fee - min_fee) / min_fee
        
        if volatility_ratio < 0.2:
            return "low"
        elif volatility_ratio < 0.5:
            return "medium"
        else:
            return "high"
    
    def _calculate_transparency_score(
        self, 
        fee_breakdown: List[FeeBreakdown], 
        path_comparisons: List[PathComparison]
    ) -> float:
        """Calculate overall transparency score (0.0 to 1.0)"""
        score = 0.0
        
        # Fee breakdown completeness (40% of score)
        if fee_breakdown:
            fee_types_covered = len(set(fee.fee_type for fee in fee_breakdown))
            max_fee_types = len(FeeType)
            score += 0.4 * (fee_types_covered / max_fee_types)
        
        # Path options provided (30% of score)
        if path_comparisons:
            score += 0.3 * min(1.0, len(path_comparisons) / 3)  # Max score at 3+ paths
        
        # Optional fees marked (15% of score)
        if any(fee.is_optional for fee in fee_breakdown):
            score += 0.15
        
        # Success probabilities shown (15% of score)
        if all(hasattr(p, 'success_probability') for p in path_comparisons):
            score += 0.15
        
        return min(1.0, score)


# Global instance
fee_transparency_service = FeeTransparencyService()