// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "../libraries/IntentSerialization.sol";
import "../interfaces/IERC7683.sol";

/**
 * @title IntentSerializationTest
 * @dev Test contract that exposes IntentSerialization functions for testing
 */
contract IntentSerializationTest {
    function serializeIntent(IERC7683.Intent memory intent) external pure returns (bytes memory) {
        return IntentSerialization.serializeIntent(intent);
    }

    function deserializeIntent(bytes memory serialized) external pure returns (IERC7683.Intent memory) {
        return IntentSerialization.deserializeIntent(serialized);
    }

    function serializeSignedIntent(IERC7683.SignedIntent memory signedIntent) external pure returns (bytes memory) {
        return IntentSerialization.serializeSignedIntent(signedIntent);
    }

    function deserializeSignedIntent(bytes memory serialized) external pure returns (IERC7683.SignedIntent memory) {
        return IntentSerialization.deserializeSignedIntent(serialized);
    }

    function serializeFulfillment(IERC7683.Fulfillment memory fulfillment) external pure returns (bytes memory) {
        return IntentSerialization.serializeFulfillment(fulfillment);
    }

    function deserializeFulfillment(bytes memory serialized) external pure returns (IERC7683.Fulfillment memory) {
        return IntentSerialization.deserializeFulfillment(serialized);
    }

    function compressIntent(IERC7683.Intent memory intent) external pure returns (bytes32) {
        return IntentSerialization.compressIntent(intent);
    }

    function validateSerializedIntent(bytes memory serialized) external pure returns (bool) {
        return IntentSerialization.validateSerializedIntent(serialized);
    }

    function estimateSerializationGas(IERC7683.Intent memory intent) external pure returns (uint256) {
        return IntentSerialization.estimateSerializationGas(intent);
    }

    function createMerkleLeaf(IERC7683.Intent memory intent) external pure returns (bytes32) {
        return IntentSerialization.createMerkleLeaf(intent);
    }

    function batchSerializeIntents(IERC7683.Intent[] memory intents) external pure returns (bytes memory) {
        return IntentSerialization.batchSerializeIntents(intents);
    }

    function batchDeserializeIntents(bytes memory serialized) external pure returns (IERC7683.Intent[] memory) {
        return IntentSerialization.batchDeserializeIntents(serialized);
    }
}