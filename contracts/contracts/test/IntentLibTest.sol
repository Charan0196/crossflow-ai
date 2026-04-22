// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "../libraries/IntentLib.sol";
import "../interfaces/IERC7683.sol";

/**
 * @title IntentLibTest
 * @dev Test contract that exposes IntentLib functions for testing
 */
contract IntentLibTest {
    using IntentLib for IERC7683.Intent;
    using IntentLib for IERC7683.SignedIntent;

    function computeIntentHash(IERC7683.Intent memory intent) external pure returns (bytes32) {
        return IntentLib.computeIntentHash(intent);
    }

    function computeDomainSeparator(
        string memory name,
        string memory version,
        uint256 chainId,
        address verifyingContract
    ) external pure returns (bytes32) {
        return IntentLib.computeDomainSeparator(name, version, chainId, verifyingContract);
    }

    function validateIntent(IERC7683.Intent memory intent) 
        external 
        view 
        returns (bool valid, string memory reason) 
    {
        return IntentLib.validateIntent(intent);
    }

    function recoverSigner(
        IERC7683.SignedIntent memory signedIntent,
        bytes32 domainSeparator
    ) external pure returns (address) {
        return IntentLib.recoverSigner(signedIntent, domainSeparator);
    }

    function estimateGasCost(IERC7683.Intent memory intent) external pure returns (uint256) {
        return IntentLib.estimateGasCost(intent);
    }

    function areIntentsEquivalent(
        IERC7683.Intent memory intent1,
        IERC7683.Intent memory intent2
    ) external pure returns (bool) {
        return IntentLib.areIntentsEquivalent(intent1, intent2);
    }

    function generateIntentId(
        IERC7683.Intent memory intent,
        uint256 blockNumber
    ) external pure returns (bytes32) {
        return IntentLib.generateIntentId(intent, blockNumber);
    }
}