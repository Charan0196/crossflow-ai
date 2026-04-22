// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "../interfaces/IERC7683.sol";

/**
 * @title IntentLib
 * @dev Library for ERC-7683 intent operations and utilities
 */
library IntentLib {
    /// @dev Type hash for EIP-712 domain separator
    bytes32 public constant DOMAIN_TYPEHASH = keccak256(
        "EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"
    );

    /// @dev Type hash for Intent struct
    bytes32 public constant INTENT_TYPEHASH = keccak256(
        "Intent(address user,uint256 sourceChain,uint256 destinationChain,address inputToken,address outputToken,uint256 inputAmount,uint256 minimumOutputAmount,uint256 deadline,uint256 nonce,address recipient)"
    );

    /**
     * @dev Computes the hash of an intent according to EIP-712
     * @param intent The intent to hash
     * @return The computed hash
     */
    function computeIntentHash(IERC7683.Intent memory intent) internal pure returns (bytes32) {
        return keccak256(abi.encode(
            INTENT_TYPEHASH,
            intent.user,
            intent.sourceChain,
            intent.destinationChain,
            intent.inputToken,
            intent.outputToken,
            intent.inputAmount,
            intent.minimumOutputAmount,
            intent.deadline,
            intent.nonce,
            intent.recipient
        ));
    }

    /**
     * @dev Computes the EIP-712 domain separator
     * @param name The name of the contract
     * @param version The version of the contract
     * @param chainId The chain ID
     * @param verifyingContract The address of the verifying contract
     * @return The computed domain separator
     */
    function computeDomainSeparator(
        string memory name,
        string memory version,
        uint256 chainId,
        address verifyingContract
    ) internal pure returns (bytes32) {
        return keccak256(abi.encode(
            DOMAIN_TYPEHASH,
            keccak256(bytes(name)),
            keccak256(bytes(version)),
            chainId,
            verifyingContract
        ));
    }

    /**
     * @dev Computes the EIP-712 typed data hash
     * @param domainSeparator The domain separator
     * @param structHash The struct hash
     * @return The typed data hash
     */
    function computeTypedDataHash(
        bytes32 domainSeparator,
        bytes32 structHash
    ) internal pure returns (bytes32) {
        return keccak256(abi.encodePacked("\x19\x01", domainSeparator, structHash));
    }

    /**
     * @dev Validates an intent's basic parameters
     * @param intent The intent to validate
     * @return valid True if the intent is valid
     * @return reason The reason for invalidity (empty if valid)
     */
    function validateIntent(IERC7683.Intent memory intent) 
        internal 
        view 
        returns (bool valid, string memory reason) 
    {
        // Check deadline
        if (intent.deadline <= block.timestamp) {
            return (false, "Intent has expired");
        }

        // Check user address
        if (intent.user == address(0)) {
            return (false, "Invalid user address");
        }

        // Check token addresses
        if (intent.inputToken == address(0) || intent.outputToken == address(0)) {
            return (false, "Invalid token address");
        }

        // Check amounts
        if (intent.inputAmount == 0 || intent.minimumOutputAmount == 0) {
            return (false, "Input amount must be greater than zero");
        }

        // Check chain IDs
        if (intent.sourceChain == 0 || intent.destinationChain == 0) {
            return (false, "Invalid chain ID");
        }

        // Set default recipient if not specified
        if (intent.recipient == address(0)) {
            intent.recipient = intent.user;
        }

        return (true, "");
    }

    /**
     * @dev Recovers the signer address from a signed intent
     * @param signedIntent The signed intent
     * @param domainSeparator The domain separator for EIP-712
     * @return signer The recovered signer address
     */
    function recoverSigner(
        IERC7683.SignedIntent memory signedIntent,
        bytes32 domainSeparator
    ) internal pure returns (address signer) {
        bytes32 intentHash = computeIntentHash(signedIntent.intent);
        bytes32 typedDataHash = computeTypedDataHash(domainSeparator, intentHash);
        
        return recoverSignerFromHash(typedDataHash, signedIntent.signature);
    }

    /**
     * @dev Recovers signer from hash and signature
     * @param hash The hash that was signed
     * @param signature The signature
     * @return signer The recovered signer address
     */
    function recoverSignerFromHash(
        bytes32 hash,
        bytes memory signature
    ) internal pure returns (address signer) {
        require(signature.length == 65, "Invalid signature length");

        bytes32 r;
        bytes32 s;
        uint8 v;

        assembly {
            r := mload(add(signature, 32))
            s := mload(add(signature, 64))
            v := byte(0, mload(add(signature, 96)))
        }

        // Adjust v if necessary
        if (v < 27) {
            v += 27;
        }

        require(v == 27 || v == 28, "Invalid signature v value");

        return ecrecover(hash, v, r, s);
    }

    /**
     * @dev Checks if two intents are equivalent
     * @param intent1 The first intent
     * @param intent2 The second intent
     * @return equivalent True if the intents are equivalent
     */
    function areIntentsEquivalent(
        IERC7683.Intent memory intent1,
        IERC7683.Intent memory intent2
    ) internal pure returns (bool equivalent) {
        return computeIntentHash(intent1) == computeIntentHash(intent2);
    }

    /**
     * @dev Estimates the gas cost for fulfilling an intent
     * @param intent The intent to estimate
     * @return gasEstimate The estimated gas cost
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
     * @dev Generates a unique intent ID
     * @param intent The intent
     * @param blockNumber The block number
     * @return intentId The unique intent ID
     */
    function generateIntentId(
        IERC7683.Intent memory intent,
        uint256 blockNumber
    ) internal pure returns (bytes32 intentId) {
        return keccak256(abi.encode(
            computeIntentHash(intent),
            blockNumber,
            intent.nonce
        ));
    }
}