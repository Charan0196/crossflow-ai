// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title IERC7683
 * @dev Interface for ERC-7683 Cross-Chain Intent Standard
 * @notice This interface defines the standard for cross-chain intents
 */
interface IERC7683 {
    /**
     * @dev Struct representing a cross-chain intent
     * @param user The address of the user creating the intent
     * @param sourceChain The chain ID where the intent originates
     * @param destinationChain The chain ID where the intent should be fulfilled
     * @param inputToken The token address on the source chain
     * @param outputToken The token address on the destination chain
     * @param inputAmount The amount of input tokens
     * @param minimumOutputAmount The minimum acceptable output amount
     * @param deadline The timestamp after which the intent expires
     * @param nonce A unique nonce for the intent
     * @param recipient The address to receive the output tokens (optional, defaults to user)
     */
    struct Intent {
        address user;
        uint256 sourceChain;
        uint256 destinationChain;
        address inputToken;
        address outputToken;
        uint256 inputAmount;
        uint256 minimumOutputAmount;
        uint256 deadline;
        uint256 nonce;
        address recipient;
    }

    /**
     * @dev Struct representing an intent signature
     * @param intent The intent data
     * @param signature The user's signature of the intent
     */
    struct SignedIntent {
        Intent intent;
        bytes signature;
    }

    /**
     * @dev Struct representing solver fulfillment data
     * @param intentHash The hash of the intent being fulfilled
     * @param solver The address of the solver fulfilling the intent
     * @param outputAmount The actual output amount provided
     * @param proof Proof of fulfillment on the destination chain
     */
    struct Fulfillment {
        bytes32 intentHash;
        address solver;
        uint256 outputAmount;
        bytes proof;
    }

    /**
     * @dev Emitted when an intent is created
     * @param intentHash The hash of the intent
     * @param user The user who created the intent
     * @param sourceChain The source chain ID
     * @param destinationChain The destination chain ID
     */
    event IntentCreated(
        bytes32 indexed intentHash,
        address indexed user,
        uint256 indexed sourceChain,
        uint256 destinationChain
    );

    /**
     * @dev Emitted when an intent is fulfilled
     * @param intentHash The hash of the fulfilled intent
     * @param solver The solver who fulfilled the intent
     * @param outputAmount The actual output amount
     */
    event IntentFulfilled(
        bytes32 indexed intentHash,
        address indexed solver,
        uint256 outputAmount
    );

    /**
     * @dev Emitted when an intent is cancelled
     * @param intentHash The hash of the cancelled intent
     * @param user The user who cancelled the intent
     */
    event IntentCancelled(
        bytes32 indexed intentHash,
        address indexed user
    );

    /**
     * @dev Creates a new intent
     * @param signedIntent The signed intent data
     * @return intentHash The hash of the created intent
     */
    function createIntent(SignedIntent calldata signedIntent) external returns (bytes32 intentHash);

    /**
     * @dev Fulfills an intent
     * @param fulfillment The fulfillment data
     */
    function fulfillIntent(Fulfillment calldata fulfillment) external;

    /**
     * @dev Cancels an intent (only by the original user)
     * @param intentHash The hash of the intent to cancel
     */
    function cancelIntent(bytes32 intentHash) external;

    /**
     * @dev Gets intent data by hash
     * @param intentHash The hash of the intent
     * @return intent The intent data
     */
    function getIntent(bytes32 intentHash) external view returns (Intent memory intent);

    /**
     * @dev Checks if an intent is fulfilled
     * @param intentHash The hash of the intent
     * @return fulfilled True if the intent is fulfilled
     */
    function isIntentFulfilled(bytes32 intentHash) external view returns (bool fulfilled);

    /**
     * @dev Computes the hash of an intent
     * @param intent The intent data
     * @return hash The computed hash
     */
    function computeIntentHash(Intent calldata intent) external pure returns (bytes32 hash);
}