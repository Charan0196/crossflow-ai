// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "../interfaces/IERC7683.sol";

/**
 * @title IntentSerialization
 * @dev Library for serializing and deserializing intent data for cross-chain communication
 */
library IntentSerialization {
    /**
     * @dev Serializes an intent to bytes for cross-chain transmission
     * @param intent The intent to serialize
     * @return serialized The serialized intent data
     */
    function serializeIntent(IERC7683.Intent memory intent) 
        internal 
        pure 
        returns (bytes memory serialized) 
    {
        return abi.encode(
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
        );
    }

    /**
     * @dev Deserializes bytes to an intent
     * @param serialized The serialized intent data
     * @return intent The deserialized intent
     */
    function deserializeIntent(bytes memory serialized) 
        internal 
        pure 
        returns (IERC7683.Intent memory intent) 
    {
        (
            address user,
            uint256 sourceChain,
            uint256 destinationChain,
            address inputToken,
            address outputToken,
            uint256 inputAmount,
            uint256 minimumOutputAmount,
            uint256 deadline,
            uint256 nonce,
            address recipient
        ) = abi.decode(
            serialized,
            (address, uint256, uint256, address, address, uint256, uint256, uint256, uint256, address)
        );

        intent.user = user;
        intent.sourceChain = sourceChain;
        intent.destinationChain = destinationChain;
        intent.inputToken = inputToken;
        intent.outputToken = outputToken;
        intent.inputAmount = inputAmount;
        intent.minimumOutputAmount = minimumOutputAmount;
        intent.deadline = deadline;
        intent.nonce = nonce;
        intent.recipient = recipient;
    }

    /**
     * @dev Serializes a signed intent to bytes
     * @param signedIntent The signed intent to serialize
     * @return serialized The serialized signed intent data
     */
    function serializeSignedIntent(IERC7683.SignedIntent memory signedIntent) 
        internal 
        pure 
        returns (bytes memory serialized) 
    {
        bytes memory intentData = serializeIntent(signedIntent.intent);
        return abi.encode(intentData, signedIntent.signature);
    }

    /**
     * @dev Deserializes bytes to a signed intent
     * @param serialized The serialized signed intent data
     * @return signedIntent The deserialized signed intent
     */
    function deserializeSignedIntent(bytes memory serialized) 
        internal 
        pure 
        returns (IERC7683.SignedIntent memory signedIntent) 
    {
        (bytes memory intentData, bytes memory signature) = abi.decode(serialized, (bytes, bytes));
        signedIntent.intent = deserializeIntent(intentData);
        signedIntent.signature = signature;
    }

    /**
     * @dev Serializes a fulfillment to bytes
     * @param fulfillment The fulfillment to serialize
     * @return serialized The serialized fulfillment data
     */
    function serializeFulfillment(IERC7683.Fulfillment memory fulfillment) 
        internal 
        pure 
        returns (bytes memory serialized) 
    {
        return abi.encode(
            fulfillment.intentHash,
            fulfillment.solver,
            fulfillment.outputAmount,
            fulfillment.proof
        );
    }

    /**
     * @dev Deserializes bytes to a fulfillment
     * @param serialized The serialized fulfillment data
     * @return fulfillment The deserialized fulfillment
     */
    function deserializeFulfillment(bytes memory serialized) 
        internal 
        pure 
        returns (IERC7683.Fulfillment memory fulfillment) 
    {
        (
            bytes32 intentHash,
            address solver,
            uint256 outputAmount,
            bytes memory proof
        ) = abi.decode(serialized, (bytes32, address, uint256, bytes));
        
        fulfillment.intentHash = intentHash;
        fulfillment.solver = solver;
        fulfillment.outputAmount = outputAmount;
        fulfillment.proof = proof;
    }

    /**
     * @dev Creates a compact representation of an intent for efficient storage
     * @param intent The intent to compress
     * @return compressed The compressed intent data
     */
    function compressIntent(IERC7683.Intent memory intent) 
        internal 
        pure 
        returns (bytes32 compressed) 
    {
        // Create a compact hash that includes essential intent data
        return keccak256(abi.encodePacked(
            intent.user,
            intent.sourceChain,
            intent.destinationChain,
            intent.inputToken,
            intent.outputToken,
            intent.inputAmount,
            intent.minimumOutputAmount,
            intent.deadline,
            intent.nonce
        ));
    }

    /**
     * @dev Validates serialized intent data integrity
     * @param serialized The serialized data to validate
     * @return valid True if the data is valid
     */
    function validateSerializedIntent(bytes memory serialized) 
        internal 
        pure 
        returns (bool valid) 
    {
        // Check minimum length for a valid intent (10 fields * 32 bytes minimum)
        if (serialized.length < 320) {
            return false;
        }
        
        // Additional validation can be added here
        return true;
    }

    /**
     * @dev Estimates the gas cost for serialization operations
     * @param intent The intent to estimate for
     * @return gasEstimate The estimated gas cost
     */
    function estimateSerializationGas(IERC7683.Intent memory intent) 
        internal 
        pure 
        returns (uint256 gasEstimate) 
    {
        // Base cost for encoding
        uint256 baseCost = 5000;
        
        // Additional cost per field (10 fields in Intent struct)
        uint256 fieldCost = 10 * 200;
        
        // Additional cost for dynamic data (addresses, amounts)
        uint256 dynamicCost = 1000;
        
        return baseCost + fieldCost + dynamicCost;
    }

    /**
     * @dev Creates a merkle leaf for an intent (for batch processing)
     * @param intent The intent to create a leaf for
     * @return leaf The merkle leaf hash
     */
    function createMerkleLeaf(IERC7683.Intent memory intent) 
        internal 
        pure 
        returns (bytes32 leaf) 
    {
        return keccak256(serializeIntent(intent));
    }

    /**
     * @dev Batch serializes multiple intents
     * @param intents Array of intents to serialize
     * @return serialized The batch serialized data
     */
    function batchSerializeIntents(IERC7683.Intent[] memory intents) 
        internal 
        pure 
        returns (bytes memory serialized) 
    {
        bytes[] memory serializedIntents = new bytes[](intents.length);
        
        for (uint256 i = 0; i < intents.length; i++) {
            serializedIntents[i] = serializeIntent(intents[i]);
        }
        
        return abi.encode(serializedIntents);
    }

    /**
     * @dev Batch deserializes multiple intents
     * @param serialized The batch serialized data
     * @return intents Array of deserialized intents
     */
    function batchDeserializeIntents(bytes memory serialized) 
        internal 
        pure 
        returns (IERC7683.Intent[] memory intents) 
    {
        bytes[] memory serializedIntents = abi.decode(serialized, (bytes[]));
        intents = new IERC7683.Intent[](serializedIntents.length);
        
        for (uint256 i = 0; i < serializedIntents.length; i++) {
            intents[i] = deserializeIntent(serializedIntents[i]);
        }
    }
}