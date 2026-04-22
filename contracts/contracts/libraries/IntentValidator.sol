// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "../interfaces/IERC7683.sol";

/**
 * @title IntentValidator
 * @dev Library for validating ERC-7683 intents on-chain
 * @notice Implements comprehensive validation logic for cross-chain intents
 */
library IntentValidator {
    /// @dev Custom errors for validation failures
    error InvalidUserAddress();
    error InvalidTokenAddress();
    error InvalidAmount();
    error InvalidChainId();
    error IntentExpired();
    error UnsupportedChain(uint256 chainId);
    error UnsupportedToken(address token, uint256 chainId);
    error InsufficientLiquidity();
    error MinimumOutputNotFeasible();
    error DeadlineTooSoon();
    error DeadlineTooFar();
    error PriceImpactTooHigh(uint256 impact);

    /// @dev Validation configuration
    struct ValidationConfig {
        uint256 minimumDeadline;    // Minimum deadline in seconds from now
        uint256 maximumDeadline;    // Maximum deadline in seconds from now
        uint256 maxPriceImpact;     // Maximum allowed price impact (basis points)
        mapping(uint256 => bool) supportedChains;
        mapping(address => mapping(uint256 => bool)) supportedTokens;
    }

    /// @dev Validation result structure
    struct ValidationResult {
        bool isValid;
        string reason;
        uint256 estimatedOutput;
        uint256 priceImpact;
        uint256 gasEstimate;
    }

    /// @dev Liquidity information structure
    struct LiquidityInfo {
        bool hasLiquidity;
        uint256 availableAmount;
        uint256 priceImpact;
        address[] protocols;
    }

    /**
     * @dev Validates an intent's basic parameters
     * @param intent The intent to validate
     * @return isValid True if the intent passes basic validation
     * @return reason Reason for validation failure (empty if valid)
     */
    function validateBasicParameters(IERC7683.Intent memory intent) 
        internal 
        view 
        returns (bool isValid, string memory reason) 
    {
        // Check user address
        if (intent.user == address(0)) {
            return (false, "Invalid user address");
        }

        // Check token addresses
        if (intent.inputToken == address(0)) {
            return (false, "Invalid input token address");
        }
        
        if (intent.outputToken == address(0)) {
            return (false, "Invalid output token address");
        }

        // Check amounts
        if (intent.inputAmount == 0) {
            return (false, "Input amount must be greater than zero");
        }
        
        if (intent.minimumOutputAmount == 0) {
            return (false, "Minimum output amount must be greater than zero");
        }

        // Check chain IDs
        if (intent.sourceChain == 0) {
            return (false, "Invalid source chain ID");
        }
        
        if (intent.destinationChain == 0) {
            return (false, "Invalid destination chain ID");
        }

        // Check deadline
        if (intent.deadline <= block.timestamp) {
            return (false, "Intent has expired");
        }

        return (true, "");
    }

    /**
     * @dev Validates chain support for an intent
     * @param intent The intent to validate
     * @param config Validation configuration
     * @return isValid True if both chains are supported
     * @return reason Reason for validation failure (empty if valid)
     */
    function validateChainSupport(
        IERC7683.Intent memory intent,
        ValidationConfig storage config
    ) internal view returns (bool isValid, string memory reason) {
        if (!config.supportedChains[intent.sourceChain]) {
            return (false, "Source chain not supported");
        }
        
        if (!config.supportedChains[intent.destinationChain]) {
            return (false, "Destination chain not supported");
        }
        
        return (true, "");
    }

    /**
     * @dev Validates deadline constraints
     * @param intent The intent to validate
     * @param config Validation configuration
     * @return isValid True if deadline is within acceptable range
     * @return reason Reason for validation failure (empty if valid)
     */
    function validateDeadline(
        IERC7683.Intent memory intent,
        ValidationConfig storage config
    ) internal view returns (bool isValid, string memory reason) {
        uint256 timeUntilDeadline = intent.deadline - block.timestamp;
        
        if (timeUntilDeadline < config.minimumDeadline) {
            return (false, "Deadline too soon");
        }
        
        if (timeUntilDeadline > config.maximumDeadline) {
            return (false, "Deadline too far in future");
        }
        
        return (true, "");
    }

    /**
     * @dev Validates token compatibility on respective chains
     * @param intent The intent to validate
     * @param config Validation configuration
     * @return isValid True if tokens are supported on their chains
     * @return reason Reason for validation failure (empty if valid)
     */
    function validateTokenCompatibility(
        IERC7683.Intent memory intent,
        ValidationConfig storage config
    ) internal view returns (bool isValid, string memory reason) {
        // Check input token on source chain
        if (!config.supportedTokens[intent.inputToken][intent.sourceChain]) {
            return (false, "Input token not supported on source chain");
        }
        
        // Check output token on destination chain
        if (!config.supportedTokens[intent.outputToken][intent.destinationChain]) {
            return (false, "Output token not supported on destination chain");
        }
        
        return (true, "");
    }

    /**
     * @dev Comprehensive intent validation
     * @param intent The intent to validate
     * @param config Validation configuration
     * @return result Complete validation result
     */
    function validateIntent(
        IERC7683.Intent memory intent,
        ValidationConfig storage config
    ) internal view returns (ValidationResult memory result) {
        // Basic parameter validation
        (bool basicValid, string memory basicReason) = validateBasicParameters(intent);
        if (!basicValid) {
            return ValidationResult({
                isValid: false,
                reason: basicReason,
                estimatedOutput: 0,
                priceImpact: 0,
                gasEstimate: 0
            });
        }

        // Chain support validation
        (bool chainValid, string memory chainReason) = validateChainSupport(intent, config);
        if (!chainValid) {
            return ValidationResult({
                isValid: false,
                reason: chainReason,
                estimatedOutput: 0,
                priceImpact: 0,
                gasEstimate: 0
            });
        }

        // Deadline validation
        (bool deadlineValid, string memory deadlineReason) = validateDeadline(intent, config);
        if (!deadlineValid) {
            return ValidationResult({
                isValid: false,
                reason: deadlineReason,
                estimatedOutput: 0,
                priceImpact: 0,
                gasEstimate: 0
            });
        }

        // Token compatibility validation
        (bool tokenValid, string memory tokenReason) = validateTokenCompatibility(intent, config);
        if (!tokenValid) {
            return ValidationResult({
                isValid: false,
                reason: tokenReason,
                estimatedOutput: 0,
                priceImpact: 0,
                gasEstimate: 0
            });
        }

        // If all validations pass
        return ValidationResult({
            isValid: true,
            reason: "Intent validation successful",
            estimatedOutput: intent.minimumOutputAmount, // Placeholder
            priceImpact: 0, // Would be calculated with oracle data
            gasEstimate: estimateGasCost(intent)
        });
    }

    /**
     * @dev Estimates gas cost for intent execution
     * @param intent The intent to estimate
     * @return gasEstimate Estimated gas cost
     */
    function estimateGasCost(IERC7683.Intent memory intent) 
        internal 
        pure 
        returns (uint256 gasEstimate) 
    {
        // Base gas cost for intent processing
        uint256 baseGas = 50000;
        
        // Additional gas for cross-chain operations
        uint256 crossChainGas = intent.sourceChain != intent.destinationChain ? 100000 : 0;
        
        // Additional gas based on token operations
        uint256 tokenGas = 30000; // ERC20 transfer gas
        
        return baseGas + crossChainGas + tokenGas;
    }

    /**
     * @dev Validates minimum output amount feasibility
     * @param intent The intent to validate
     * @param currentMarketRate Current exchange rate (scaled by 1e18)
     * @param slippageTolerance Maximum allowed slippage (basis points)
     * @return isValid True if minimum output is feasible
     * @return estimatedOutput Estimated output amount
     */
    function validateMinimumOutput(
        IERC7683.Intent memory intent,
        uint256 currentMarketRate,
        uint256 slippageTolerance
    ) internal pure returns (bool isValid, uint256 estimatedOutput) {
        // Calculate estimated output with slippage
        estimatedOutput = (intent.inputAmount * currentMarketRate) / 1e18;
        uint256 slippageAmount = (estimatedOutput * slippageTolerance) / 10000;
        uint256 outputWithSlippage = estimatedOutput - slippageAmount;
        
        // Check if minimum output is feasible
        isValid = outputWithSlippage >= intent.minimumOutputAmount;
    }

    /**
     * @dev Calculates price impact for a trade
     * @param inputAmount Amount of input tokens
     * @param outputAmount Amount of output tokens
     * @param marketRate Current market rate (scaled by 1e18)
     * @return priceImpact Price impact in basis points
     */
    function calculatePriceImpact(
        uint256 inputAmount,
        uint256 outputAmount,
        uint256 marketRate
    ) internal pure returns (uint256 priceImpact) {
        if (inputAmount == 0 || marketRate == 0) {
            return 0;
        }
        
        uint256 expectedOutput = (inputAmount * marketRate) / 1e18;
        if (expectedOutput <= outputAmount) {
            return 0; // No negative price impact
        }
        
        uint256 impact = ((expectedOutput - outputAmount) * 10000) / expectedOutput;
        return impact;
    }

    /**
     * @dev Validates that price impact is within acceptable limits
     * @param intent The intent to validate
     * @param marketRate Current market rate (scaled by 1e18)
     * @param maxPriceImpact Maximum allowed price impact (basis points)
     * @return isValid True if price impact is acceptable
     * @return priceImpact Calculated price impact in basis points
     */
    function validatePriceImpact(
        IERC7683.Intent memory intent,
        uint256 marketRate,
        uint256 maxPriceImpact
    ) internal pure returns (bool isValid, uint256 priceImpact) {
        priceImpact = calculatePriceImpact(
            intent.inputAmount,
            intent.minimumOutputAmount,
            marketRate
        );
        
        isValid = priceImpact <= maxPriceImpact;
    }

    /**
     * @dev Batch validation for multiple intents
     * @param intents Array of intents to validate
     * @param config Validation configuration
     * @return results Array of validation results
     */
    function validateBatchIntents(
        IERC7683.Intent[] memory intents,
        ValidationConfig storage config
    ) internal view returns (ValidationResult[] memory results) {
        results = new ValidationResult[](intents.length);
        
        for (uint256 i = 0; i < intents.length; i++) {
            results[i] = validateIntent(intents[i], config);
        }
    }
}