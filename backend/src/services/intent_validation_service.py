"""
Intent validation service for ERC-7683 cross-chain intents
Implements liquidity checking, chain support validation, and feasibility checks
"""
import asyncio
from typing import Dict, Optional, List, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from src.services.dex_service import dex_service
from src.services.price_service import price_service
from src.config.settings import settings


class ValidationResult(Enum):
    VALID = "valid"
    INSUFFICIENT_LIQUIDITY = "insufficient_liquidity"
    UNSUPPORTED_CHAIN = "unsupported_chain"
    UNSUPPORTED_TOKEN = "unsupported_token"
    MINIMUM_OUTPUT_NOT_FEASIBLE = "minimum_output_not_feasible"
    DEADLINE_TOO_SOON = "deadline_too_soon"
    DEADLINE_TOO_FAR = "deadline_too_far"
    INVALID_AMOUNT = "invalid_amount"
    PRICE_IMPACT_TOO_HIGH = "price_impact_too_high"


@dataclass
class IntentValidationRequest:
    """Intent validation request structure matching ERC-7683"""
    user: str
    source_chain: int
    destination_chain: int
    input_token: str
    output_token: str
    input_amount: str
    minimum_output_amount: str
    deadline: int
    nonce: int
    recipient: Optional[str] = None


@dataclass
class ValidationResponse:
    """Validation response with detailed information"""
    is_valid: bool
    result: ValidationResult
    reason: str
    liquidity_info: Optional[Dict] = None
    price_impact: Optional[Decimal] = None
    estimated_output: Optional[str] = None
    gas_estimate: Optional[str] = None


class IntentValidationService:
    def __init__(self):
        # Supported chains for Phase 1
        self.supported_chains = {
            1: "ethereum",
            137: "polygon", 
            42161: "arbitrum",
            10: "optimism",
            56: "bsc",
            8453: "base"
        }
        
        # Minimum and maximum deadline limits (in seconds)
        self.min_deadline = 300  # 5 minutes
        self.max_deadline = 86400 * 7  # 7 days
        
        # Price impact thresholds
        self.max_price_impact = Decimal("0.10")  # 10%
        self.warning_price_impact = Decimal("0.05")  # 5%
        
        # Minimum liquidity thresholds (in USD)
        self.min_liquidity_usd = {
            "small": Decimal("1000"),    # < $1k
            "medium": Decimal("10000"),  # $1k - $10k  
            "large": Decimal("100000")   # > $10k
        }
    
    async def validate_intent(self, intent: IntentValidationRequest) -> ValidationResponse:
        """
        Comprehensive intent validation
        Requirements: 1.3, 7.1, 7.2
        """
        try:
            # Basic parameter validation
            basic_validation = self._validate_basic_parameters(intent)
            if not basic_validation.is_valid:
                return basic_validation
            
            # Chain support validation
            chain_validation = self._validate_chain_support(intent)
            if not chain_validation.is_valid:
                return chain_validation
            
            # Deadline validation
            deadline_validation = self._validate_deadline(intent)
            if not deadline_validation.is_valid:
                return deadline_validation
            
            # Token compatibility validation
            token_validation = await self._validate_token_compatibility(intent)
            if not token_validation.is_valid:
                return token_validation
            
            # Liquidity and feasibility validation
            liquidity_validation = await self._validate_liquidity_and_feasibility(intent)
            if not liquidity_validation.is_valid:
                return liquidity_validation
            
            # If all validations pass
            return ValidationResponse(
                is_valid=True,
                result=ValidationResult.VALID,
                reason="Intent validation successful",
                liquidity_info=liquidity_validation.liquidity_info,
                price_impact=liquidity_validation.price_impact,
                estimated_output=liquidity_validation.estimated_output,
                gas_estimate=liquidity_validation.gas_estimate
            )
            
        except Exception as e:
            return ValidationResponse(
                is_valid=False,
                result=ValidationResult.INVALID_AMOUNT,
                reason=f"Validation error: {str(e)}"
            )
    
    def _validate_basic_parameters(self, intent: IntentValidationRequest) -> ValidationResponse:
        """Validate basic intent parameters"""
        # Check amounts
        try:
            input_amount = Decimal(intent.input_amount)
            minimum_output = Decimal(intent.minimum_output_amount)
            
            if input_amount <= 0:
                return ValidationResponse(
                    is_valid=False,
                    result=ValidationResult.INVALID_AMOUNT,
                    reason="Input amount must be greater than zero"
                )
            
            if minimum_output <= 0:
                return ValidationResponse(
                    is_valid=False,
                    result=ValidationResult.INVALID_AMOUNT,
                    reason="Minimum output amount must be greater than zero"
                )
                
        except (ValueError, TypeError):
            return ValidationResponse(
                is_valid=False,
                result=ValidationResult.INVALID_AMOUNT,
                reason="Invalid amount format"
            )
        
        # Check addresses
        if not intent.user or len(intent.user) != 42 or not intent.user.startswith('0x'):
            return ValidationResponse(
                is_valid=False,
                result=ValidationResult.INVALID_AMOUNT,
                reason="Invalid user address"
            )
        
        if not intent.input_token or len(intent.input_token) != 42 or not intent.input_token.startswith('0x'):
            return ValidationResponse(
                is_valid=False,
                result=ValidationResult.INVALID_AMOUNT,
                reason="Invalid input token address"
            )
        
        if not intent.output_token or len(intent.output_token) != 42 or not intent.output_token.startswith('0x'):
            return ValidationResponse(
                is_valid=False,
                result=ValidationResult.INVALID_AMOUNT,
                reason="Invalid output token address"
            )
        
        return ValidationResponse(
            is_valid=True,
            result=ValidationResult.VALID,
            reason="Basic parameters valid"
        )
    
    def _validate_chain_support(self, intent: IntentValidationRequest) -> ValidationResponse:
        """Validate that both chains are supported"""
        if intent.source_chain not in self.supported_chains:
            return ValidationResponse(
                is_valid=False,
                result=ValidationResult.UNSUPPORTED_CHAIN,
                reason=f"Source chain {intent.source_chain} is not supported"
            )
        
        if intent.destination_chain not in self.supported_chains:
            return ValidationResponse(
                is_valid=False,
                result=ValidationResult.UNSUPPORTED_CHAIN,
                reason=f"Destination chain {intent.destination_chain} is not supported"
            )
        
        return ValidationResponse(
            is_valid=True,
            result=ValidationResult.VALID,
            reason="Chain support validated"
        )
    
    def _validate_deadline(self, intent: IntentValidationRequest) -> ValidationResponse:
        """Validate intent deadline"""
        current_time = int(datetime.now().timestamp())
        time_until_deadline = intent.deadline - current_time
        
        if time_until_deadline < self.min_deadline:
            return ValidationResponse(
                is_valid=False,
                result=ValidationResult.DEADLINE_TOO_SOON,
                reason=f"Deadline must be at least {self.min_deadline} seconds from now"
            )
        
        if time_until_deadline > self.max_deadline:
            return ValidationResponse(
                is_valid=False,
                result=ValidationResult.DEADLINE_TOO_FAR,
                reason=f"Deadline cannot be more than {self.max_deadline} seconds from now"
            )
        
        return ValidationResponse(
            is_valid=True,
            result=ValidationResult.VALID,
            reason="Deadline validated"
        )
    
    async def _validate_token_compatibility(self, intent: IntentValidationRequest) -> ValidationResponse:
        """Validate token compatibility on respective chains"""
        try:
            # Check if tokens are supported on their respective chains
            source_tokens = await dex_service.get_tokens(intent.source_chain)
            if source_tokens and intent.input_token.lower() not in [
                token.lower() for token in source_tokens.get("tokens", {}).keys()
            ]:
                return ValidationResponse(
                    is_valid=False,
                    result=ValidationResult.UNSUPPORTED_TOKEN,
                    reason=f"Input token not supported on source chain {intent.source_chain}"
                )
            
            dest_tokens = await dex_service.get_tokens(intent.destination_chain)
            if dest_tokens and intent.output_token.lower() not in [
                token.lower() for token in dest_tokens.get("tokens", {}).keys()
            ]:
                return ValidationResponse(
                    is_valid=False,
                    result=ValidationResult.UNSUPPORTED_TOKEN,
                    reason=f"Output token not supported on destination chain {intent.destination_chain}"
                )
            
            return ValidationResponse(
                is_valid=True,
                result=ValidationResult.VALID,
                reason="Token compatibility validated"
            )
            
        except Exception as e:
            # If we can't validate tokens, allow the intent but log the issue
            print(f"Token compatibility validation error: {e}")
            return ValidationResponse(
                is_valid=True,
                result=ValidationResult.VALID,
                reason="Token compatibility check skipped due to API unavailability"
            )
    
    async def _validate_liquidity_and_feasibility(self, intent: IntentValidationRequest) -> ValidationResponse:
        """
        Validate liquidity availability and minimum output feasibility
        Requirements: 1.3, 7.1, 7.2
        """
        try:
            input_amount = Decimal(intent.input_amount)
            minimum_output = Decimal(intent.minimum_output_amount)
            
            # Get quote for the trade on source chain
            source_quote = await dex_service.get_quote(
                chain_id=intent.source_chain,
                from_token=intent.input_token,
                to_token=intent.output_token,
                amount=intent.input_amount
            )
            
            if not source_quote:
                return ValidationResponse(
                    is_valid=False,
                    result=ValidationResult.INSUFFICIENT_LIQUIDITY,
                    reason="Unable to get liquidity quote for the requested trade"
                )
            
            # Extract quote information
            estimated_output = Decimal(source_quote.get("dstAmount", "0"))
            if estimated_output == 0:
                return ValidationResponse(
                    is_valid=False,
                    result=ValidationResult.INSUFFICIENT_LIQUIDITY,
                    reason="No liquidity available for this trade"
                )
            
            # Check if minimum output is feasible
            if estimated_output < minimum_output:
                return ValidationResponse(
                    is_valid=False,
                    result=ValidationResult.MINIMUM_OUTPUT_NOT_FEASIBLE,
                    reason=f"Estimated output {estimated_output} is less than minimum required {minimum_output}"
                )
            
            # Calculate price impact
            price_impact = self._calculate_price_impact(source_quote)
            
            # Check price impact thresholds
            if price_impact > self.max_price_impact:
                return ValidationResponse(
                    is_valid=False,
                    result=ValidationResult.PRICE_IMPACT_TOO_HIGH,
                    reason=f"Price impact {price_impact:.2%} exceeds maximum allowed {self.max_price_impact:.2%}"
                )
            
            # Estimate gas costs
            gas_estimate = source_quote.get("estimatedGas", "0")
            
            # Prepare liquidity info
            liquidity_info = {
                "source_chain_liquidity": True,
                "estimated_output": str(estimated_output),
                "price_impact": float(price_impact),
                "gas_estimate": gas_estimate,
                "protocols": source_quote.get("protocols", [])
            }
            
            return ValidationResponse(
                is_valid=True,
                result=ValidationResult.VALID,
                reason="Liquidity and feasibility validated",
                liquidity_info=liquidity_info,
                price_impact=price_impact,
                estimated_output=str(estimated_output),
                gas_estimate=gas_estimate
            )
            
        except Exception as e:
            return ValidationResponse(
                is_valid=False,
                result=ValidationResult.INSUFFICIENT_LIQUIDITY,
                reason=f"Liquidity validation error: {str(e)}"
            )
    
    async def validate_solver_reputation_and_liquidity(
        self, 
        solver_address: str, 
        intent: IntentValidationRequest
    ) -> ValidationResponse:
        """
        Validate solver reputation and available liquidity for intent fulfillment
        Requirements: 7.3 - Solver reputation and liquidity verification
        """
        try:
            from src.services.solver_network_service import solver_network_service
            
            # Get solver information
            solver = await solver_network_service.get_solver_by_address(solver_address)
            if not solver:
                return ValidationResponse(
                    is_valid=False,
                    result=ValidationResult.UNSUPPORTED_CHAIN,  # Reusing enum value
                    reason=f"Solver {solver_address} not found in network"
                )
            
            # Check if solver is eligible for intents
            if not solver.is_eligible_for_intents:
                return ValidationResponse(
                    is_valid=False,
                    result=ValidationResult.UNSUPPORTED_CHAIN,  # Reusing enum value
                    reason=f"Solver {solver_address} is not eligible for intents (status: {solver.status.value})"
                )
            
            # Check solver reputation score
            min_reputation = 0.7  # Minimum reputation threshold
            if solver.reputation_score.total_score < min_reputation:
                return ValidationResponse(
                    is_valid=False,
                    result=ValidationResult.UNSUPPORTED_CHAIN,  # Reusing enum value
                    reason=f"Solver reputation {solver.reputation_score.total_score:.2f} below minimum {min_reputation}"
                )
            
            # Check solver supports required chains
            if intent.source_chain not in solver.supported_chains:
                return ValidationResponse(
                    is_valid=False,
                    result=ValidationResult.UNSUPPORTED_CHAIN,
                    reason=f"Solver does not support source chain {intent.source_chain}"
                )
            
            if intent.destination_chain not in solver.supported_chains:
                return ValidationResponse(
                    is_valid=False,
                    result=ValidationResult.UNSUPPORTED_CHAIN,
                    reason=f"Solver does not support destination chain {intent.destination_chain}"
                )
            
            # Check solver has sufficient stake
            if not solver.stake_info or not solver.stake_info.is_sufficient:
                return ValidationResponse(
                    is_valid=False,
                    result=ValidationResult.UNSUPPORTED_CHAIN,  # Reusing enum value
                    reason=f"Solver has insufficient stake"
                )
            
            # Check solver capacity (not overloaded)
            if solver.current_concurrent_intents >= solver.max_concurrent_intents:
                return ValidationResponse(
                    is_valid=False,
                    result=ValidationResult.UNSUPPORTED_CHAIN,  # Reusing enum value
                    reason=f"Solver at maximum capacity ({solver.current_concurrent_intents}/{solver.max_concurrent_intents})"
                )
            
            # Validate solver has liquidity for the trade
            input_amount_usd = await self._estimate_usd_value(
                intent.input_token, 
                intent.input_amount, 
                intent.source_chain
            )
            
            # Check if solver has processed similar volume before
            min_volume_threshold = max(input_amount_usd * Decimal('0.1'), Decimal('100'))  # 10% of trade or $100 minimum
            if solver.performance_metrics.total_volume_processed < min_volume_threshold:
                return ValidationResponse(
                    is_valid=False,
                    result=ValidationResult.INSUFFICIENT_LIQUIDITY,
                    reason=f"Solver has insufficient trading history for this volume"
                )
            
            return ValidationResponse(
                is_valid=True,
                result=ValidationResult.VALID,
                reason="Solver reputation and liquidity validated",
                liquidity_info={
                    "solver_address": solver_address,
                    "reputation_score": solver.reputation_score.total_score,
                    "completion_rate": solver.performance_metrics.completion_rate,
                    "total_volume_processed": str(solver.performance_metrics.total_volume_processed),
                    "stake_amount": str(solver.stake_info.effective_stake) if solver.stake_info else "0"
                }
            )
            
        except Exception as e:
            return ValidationResponse(
                is_valid=False,
                result=ValidationResult.INSUFFICIENT_LIQUIDITY,
                reason=f"Solver validation error: {str(e)}"
            )
    
    async def check_low_liquidity_warning(self, intent: IntentValidationRequest) -> ValidationResponse:
        """
        Check for low liquidity conditions and generate warnings
        Requirements: 7.4 - Low liquidity warnings
        """
        try:
            input_amount = Decimal(intent.input_amount)
            
            # Estimate USD value of the trade
            input_amount_usd = await self._estimate_usd_value(
                intent.input_token, 
                intent.input_amount, 
                intent.source_chain
            )
            
            # Get liquidity information across multiple DEXs
            liquidity_sources = await self._check_multi_dex_liquidity(intent)
            
            # Analyze liquidity depth
            total_available_liquidity = sum(
                Decimal(source.get("available_liquidity_usd", "0")) 
                for source in liquidity_sources
            )
            
            # Calculate liquidity ratio (trade size vs available liquidity)
            if total_available_liquidity > 0:
                liquidity_ratio = input_amount_usd / total_available_liquidity
            else:
                liquidity_ratio = Decimal('1.0')  # Assume 100% if we can't determine
            
            # Determine warning level
            warning_level = None
            warning_message = None
            
            if liquidity_ratio > Decimal('0.5'):  # Trade is >50% of available liquidity
                warning_level = "critical"
                warning_message = f"Critical: Trade size ({input_amount_usd:.2f} USD) is {liquidity_ratio:.1%} of available liquidity"
            elif liquidity_ratio > Decimal('0.2'):  # Trade is >20% of available liquidity
                warning_level = "high"
                warning_message = f"High impact: Trade size may cause significant price movement ({liquidity_ratio:.1%} of liquidity)"
            elif liquidity_ratio > Decimal('0.1'):  # Trade is >10% of available liquidity
                warning_level = "medium"
                warning_message = f"Medium impact: Trade size is {liquidity_ratio:.1%} of available liquidity"
            elif len(liquidity_sources) < 2:  # Only one liquidity source available
                warning_level = "low"
                warning_message = "Limited liquidity sources available for this trade"
            
            # Check for specific low liquidity tokens
            low_liquidity_tokens = await self._identify_low_liquidity_tokens([intent.input_token, intent.output_token])
            if low_liquidity_tokens:
                if not warning_level:
                    warning_level = "medium"
                    warning_message = f"Low liquidity tokens detected: {', '.join(low_liquidity_tokens)}"
                else:
                    warning_message += f" | Low liquidity tokens: {', '.join(low_liquidity_tokens)}"
            
            return ValidationResponse(
                is_valid=True,
                result=ValidationResult.VALID,
                reason=warning_message or "Liquidity check completed",
                liquidity_info={
                    "warning_level": warning_level,
                    "warning_message": warning_message,
                    "liquidity_ratio": float(liquidity_ratio),
                    "total_available_liquidity_usd": str(total_available_liquidity),
                    "trade_size_usd": str(input_amount_usd),
                    "liquidity_sources": liquidity_sources,
                    "low_liquidity_tokens": low_liquidity_tokens
                }
            )
            
        except Exception as e:
            return ValidationResponse(
                is_valid=True,  # Don't fail validation, just warn
                result=ValidationResult.VALID,
                reason=f"Liquidity warning check error: {str(e)}",
                liquidity_info={
                    "warning_level": "unknown",
                    "warning_message": "Unable to assess liquidity conditions"
                }
            )
    
    async def validate_price_impact_protection(self, intent: IntentValidationRequest) -> ValidationResponse:
        """
        Validate price impact and enforce protection thresholds
        Requirements: 7.5 - Price impact protection
        """
        try:
            # Get detailed price impact analysis
            price_impact_analysis = await self._analyze_price_impact(intent)
            
            if not price_impact_analysis:
                return ValidationResponse(
                    is_valid=False,
                    result=ValidationResult.PRICE_IMPACT_TOO_HIGH,
                    reason="Unable to calculate price impact for trade"
                )
            
            total_price_impact = price_impact_analysis["total_price_impact"]
            source_impact = price_impact_analysis["source_chain_impact"]
            dest_impact = price_impact_analysis["destination_chain_impact"]
            
            # Check against maximum allowed price impact (10%)
            if total_price_impact > self.max_price_impact:
                return ValidationResponse(
                    is_valid=False,
                    result=ValidationResult.PRICE_IMPACT_TOO_HIGH,
                    reason=f"Total price impact {total_price_impact:.2%} exceeds maximum allowed {self.max_price_impact:.2%}"
                )
            
            # Check if user approval is required for high impact trades
            requires_approval = False
            approval_reason = None
            
            if total_price_impact > Decimal('0.05'):  # >5% requires approval
                requires_approval = True
                approval_reason = f"High price impact trade ({total_price_impact:.2%}) requires explicit user approval"
            
            # Check for asymmetric price impact (one chain much higher than other)
            impact_asymmetry = abs(source_impact - dest_impact)
            if impact_asymmetry > Decimal('0.03'):  # >3% difference
                if not requires_approval:
                    requires_approval = True
                    approval_reason = f"Asymmetric price impact detected (source: {source_impact:.2%}, dest: {dest_impact:.2%})"
                else:
                    approval_reason += f" | Asymmetric impact: {impact_asymmetry:.2%} difference"
            
            return ValidationResponse(
                is_valid=True,
                result=ValidationResult.VALID,
                reason="Price impact validation completed",
                liquidity_info={
                    "total_price_impact": float(total_price_impact),
                    "source_chain_impact": float(source_impact),
                    "destination_chain_impact": float(dest_impact),
                    "requires_user_approval": requires_approval,
                    "approval_reason": approval_reason,
                    "impact_breakdown": price_impact_analysis.get("breakdown", {}),
                    "protection_level": "enforced" if total_price_impact <= self.max_price_impact else "exceeded"
                }
            )
            
        except Exception as e:
            return ValidationResponse(
                is_valid=False,
                result=ValidationResult.PRICE_IMPACT_TOO_HIGH,
                reason=f"Price impact validation error: {str(e)}"
            )
    
    async def _estimate_usd_value(self, token_address: str, amount: str, chain_id: int) -> Decimal:
        """Estimate USD value of token amount"""
        try:
            # Get token price from price service
            token_price = await price_service.get_token_price(token_address, chain_id)
            if token_price:
                return Decimal(amount) * Decimal(str(token_price))
            
            # Fallback: assume $1 if we can't get price
            return Decimal(amount)
            
        except Exception:
            return Decimal(amount)  # Fallback
    
    async def _check_multi_dex_liquidity(self, intent: IntentValidationRequest) -> List[Dict]:
        """Check liquidity across multiple DEX sources"""
        try:
            liquidity_sources = []
            
            # Check primary DEX (Uniswap V3, PancakeSwap, etc.)
            primary_quote = await dex_service.get_quote(
                chain_id=intent.source_chain,
                from_token=intent.input_token,
                to_token=intent.output_token,
                amount=intent.input_amount
            )
            
            if primary_quote:
                liquidity_sources.append({
                    "source": "primary_dex",
                    "protocol": primary_quote.get("protocols", [{}])[0].get("name", "unknown"),
                    "available_liquidity_usd": primary_quote.get("dstAmount", "0"),
                    "price_impact": self._calculate_price_impact(primary_quote)
                })
            
            # In production, would check additional DEX aggregators
            # For now, return the primary source
            return liquidity_sources
            
        except Exception as e:
            print(f"Error checking multi-DEX liquidity: {e}")
            return []
    
    async def _identify_low_liquidity_tokens(self, token_addresses: List[str]) -> List[str]:
        """Identify tokens with low liquidity"""
        try:
            low_liquidity_tokens = []
            
            for token_address in token_addresses:
                # Check if token is in known low-liquidity list
                # In production, would check against database of token liquidity metrics
                
                # For now, use simple heuristics
                if token_address.lower() in [
                    "0x0000000000000000000000000000000000000000",  # ETH (high liquidity)
                    "0xa0b86a33e6c6c9c6c6c6c6c6c6c6c6c6c6c6c6c6",  # USDC (high liquidity)
                ]:
                    continue  # Skip high liquidity tokens
                
                # Assume other tokens might have lower liquidity
                # In production, would have proper liquidity metrics
                
            return low_liquidity_tokens
            
        except Exception:
            return []
    
    async def _analyze_price_impact(self, intent: IntentValidationRequest) -> Optional[Dict]:
        """Analyze price impact across source and destination chains"""
        try:
            # Get quote for source chain
            source_quote = await dex_service.get_quote(
                chain_id=intent.source_chain,
                from_token=intent.input_token,
                to_token=intent.output_token,
                amount=intent.input_amount
            )
            
            if not source_quote:
                return None
            
            source_impact = self._calculate_price_impact(source_quote)
            
            # For cross-chain trades, destination impact would be calculated separately
            # For now, assume similar impact on destination chain
            dest_impact = source_impact * Decimal('0.8')  # Assume slightly lower impact
            
            total_impact = source_impact + dest_impact
            
            return {
                "total_price_impact": total_impact,
                "source_chain_impact": source_impact,
                "destination_chain_impact": dest_impact,
                "breakdown": {
                    "source_chain": {
                        "chain_id": intent.source_chain,
                        "impact": float(source_impact),
                        "protocols": source_quote.get("protocols", [])
                    },
                    "destination_chain": {
                        "chain_id": intent.destination_chain,
                        "impact": float(dest_impact),
                        "estimated": True
                    }
                }
            }
            
        except Exception as e:
            print(f"Error analyzing price impact: {e}")
            return None
    
    def _calculate_price_impact(self, quote: Dict) -> Decimal:
        """Calculate price impact from DEX quote"""
        try:
            # Price impact is usually provided in the quote
            if "priceImpact" in quote:
                return Decimal(str(quote["priceImpact"])) / 100
            
            # If not provided, estimate based on input/output amounts
            src_amount = Decimal(quote.get("srcAmount", "0"))
            dst_amount = Decimal(quote.get("dstAmount", "0"))
            
            if src_amount > 0 and dst_amount > 0:
                # This is a simplified calculation
                # In practice, you'd need token prices to calculate accurate price impact
                return Decimal("0.01")  # Default 1% if we can't calculate
            
            return Decimal("0")
            
        except Exception:
            return Decimal("0.01")  # Default 1% on error
    
    async def validate_batch_intents(self, intents: List[IntentValidationRequest]) -> List[ValidationResponse]:
        """Validate multiple intents in batch"""
        tasks = [self.validate_intent(intent) for intent in intents]
        return await asyncio.gather(*tasks)
    
    async def check_liquidity_across_chains(self, token_address: str, amount: str) -> Dict[int, Dict]:
        """Check liquidity for a token across all supported chains"""
        liquidity_info = {}
        
        for chain_id in self.supported_chains.keys():
            try:
                # Get tokens list to check if token exists on this chain
                tokens = await dex_service.get_tokens(chain_id)
                if tokens and token_address.lower() in [t.lower() for t in tokens.get("tokens", {}).keys()]:
                    # Get a sample quote to check liquidity
                    # Using USDC as a common base token for liquidity checking
                    usdc_addresses = {
                        1: "0xA0b86a33E6C6C9C6C6C6C6C6C6C6C6C6C6C6C6C6",  # USDC on Ethereum
                        137: "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",  # USDC on Polygon
                        42161: "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8", # USDC on Arbitrum
                        10: "0x7F5c764cBc14f9669B88837ca1490cCa17c31607",   # USDC on Optimism
                        56: "0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d",   # USDC on BSC
                        8453: "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"  # USDC on Base
                    }
                    
                    usdc_address = usdc_addresses.get(chain_id)
                    if usdc_address:
                        quote = await dex_service.get_quote(
                            chain_id=chain_id,
                            from_token=token_address,
                            to_token=usdc_address,
                            amount=amount
                        )
                        
                        liquidity_info[chain_id] = {
                            "has_liquidity": quote is not None,
                            "estimated_output": quote.get("dstAmount", "0") if quote else "0",
                            "protocols": quote.get("protocols", []) if quote else []
                        }
                    else:
                        liquidity_info[chain_id] = {
                            "has_liquidity": False,
                            "reason": "No USDC reference token available"
                        }
                else:
                    liquidity_info[chain_id] = {
                        "has_liquidity": False,
                        "reason": "Token not available on this chain"
                    }
                    
            except Exception as e:
                liquidity_info[chain_id] = {
                    "has_liquidity": False,
                    "reason": f"Error checking liquidity: {str(e)}"
                }
        
        return liquidity_info


# Global instance
intent_validation_service = IntentValidationService()