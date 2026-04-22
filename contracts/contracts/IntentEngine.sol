// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "./interfaces/IERC7683.sol";
import "./libraries/IntentLib.sol";
import "./libraries/IntentValidator.sol";

/**
 * @title IntentEngine
 * @dev Core contract implementing ERC-7683 cross-chain intent standard
 * @notice This contract manages the creation, validation, and tracking of cross-chain intents
 */
contract IntentEngine is IERC7683, Ownable, ReentrancyGuard, Pausable {
    using IntentLib for IERC7683.Intent;
    using IntentLib for IERC7683.SignedIntent;
    using IntentValidator for IERC7683.Intent;

    /// @dev Contract name for EIP-712
    string public constant NAME = "CrossFlow AI Intent Engine";
    
    /// @dev Contract version for EIP-712
    string public constant VERSION = "1.0.0";

    /// @dev Domain separator for EIP-712
    bytes32 public immutable DOMAIN_SEPARATOR;

    /// @dev Mapping from intent hash to intent data
    mapping(bytes32 => Intent) public intents;

    /// @dev Mapping from intent hash to fulfillment status
    mapping(bytes32 => bool) public intentFulfilled;

    /// @dev Mapping from intent hash to cancellation status
    mapping(bytes32 => bool) public intentCancelled;

    /// @dev Mapping from user to nonce for replay protection
    mapping(address => uint256) public userNonces;

    /// @dev Mapping from solver address to authorization status
    mapping(address => bool) public authorizedSolvers;

    /// @dev Mapping from intent hash to solver bids
    mapping(bytes32 => mapping(address => SolverBid)) public solverBids;

    /// @dev Mapping from intent hash to list of bidding solvers
    mapping(bytes32 => address[]) public intentBidders;

    /// @dev Mapping from intent hash to selected solver
    mapping(bytes32 => address) public selectedSolvers;

    /// @dev Validation configuration
    IntentValidator.ValidationConfig internal validationConfig;

    /// @dev Solver bid structure
    struct SolverBid {
        address solver;
        uint256 outputAmount;
        uint256 executionTimeEstimate;
        uint256 gasFeeEstimate;
        uint256 solverFee;
        uint256 bidTimestamp;
        bool isValid;
    }

    /// @dev Events for intent lifecycle
    event IntentValidated(bytes32 indexed intentHash, address indexed user);
    event IntentBroadcasted(bytes32 indexed intentHash, address indexed user, uint256 targetSolvers);
    event SolverBidReceived(bytes32 indexed intentHash, address indexed solver, uint256 outputAmount);
    event SolverSelected(bytes32 indexed intentHash, address indexed solver, uint256 outputAmount);
    event SolverAuthorized(address indexed solver, bool authorized);
    event ChainSupported(uint256 indexed chainId, bool supported);
    event TokenSupported(address indexed token, uint256 indexed chainId, bool supported);
    event DeadlineLimitsUpdated(uint256 minimumDeadline, uint256 maximumDeadline);
    event ValidationConfigUpdated();

    /**
     * @dev Constructor
     * @param initialOwner The initial owner of the contract
     */
    constructor(address initialOwner) Ownable(initialOwner) {
        DOMAIN_SEPARATOR = IntentLib.computeDomainSeparator(
            NAME,
            VERSION,
            block.chainid,
            address(this)
        );

        // Initialize validation configuration
        validationConfig.minimumDeadline = 300; // 5 minutes
        validationConfig.maximumDeadline = 86400 * 7; // 7 days
        validationConfig.maxPriceImpact = 1000; // 10% in basis points

        // Initialize supported chains
        _setSupportedChain(1, true);     // Ethereum
        _setSupportedChain(137, true);   // Polygon
        _setSupportedChain(42161, true); // Arbitrum
        _setSupportedChain(10, true);    // Optimism
        _setSupportedChain(56, true);    // BSC
        _setSupportedChain(8453, true);  // Base
    }

    /**
     * @dev Creates a new intent
     * @param signedIntent The signed intent data
     * @return intentHash The hash of the created intent
     */
    function createIntent(SignedIntent calldata signedIntent) 
        external 
        override 
        nonReentrant 
        whenNotPaused 
        returns (bytes32 intentHash) 
    {
        // Comprehensive intent validation using IntentValidator library
        IntentValidator.ValidationResult memory validationResult = 
            signedIntent.intent.validateIntent(validationConfig);
        
        require(validationResult.isValid, validationResult.reason);

        // Verify signature
        address signer = signedIntent.recoverSigner(DOMAIN_SEPARATOR);
        require(signer == signedIntent.intent.user, "Invalid signature");

        // Check nonce
        require(signedIntent.intent.nonce == userNonces[signedIntent.intent.user], "Invalid nonce");

        // Compute intent hash
        intentHash = IntentLib.computeIntentHash(signedIntent.intent);

        // Ensure intent doesn't already exist
        require(intents[intentHash].user == address(0), "Intent already exists");

        // Store intent
        intents[intentHash] = signedIntent.intent;

        // Increment user nonce
        userNonces[signedIntent.intent.user]++;

        // Emit events
        emit IntentCreated(
            intentHash,
            signedIntent.intent.user,
            signedIntent.intent.sourceChain,
            signedIntent.intent.destinationChain
        );

        emit IntentValidated(intentHash, signedIntent.intent.user);

        // Broadcast intent to solver network
        _broadcastIntentToSolvers(intentHash, signedIntent.intent);

        return intentHash;
    }

    /**
     * @dev Fulfills an intent (only by authorized solvers)
     * @param fulfillment The fulfillment data
     */
    function fulfillIntent(Fulfillment calldata fulfillment) 
        external 
        override 
        nonReentrant 
        whenNotPaused 
    {
        require(authorizedSolvers[msg.sender], "Unauthorized solver");

        bytes32 intentHash = fulfillment.intentHash;
        Intent memory intent = intents[intentHash];

        // Validate intent exists and is not fulfilled/cancelled
        require(intent.user != address(0), "Intent does not exist");
        require(!intentFulfilled[intentHash], "Intent already fulfilled");
        require(!intentCancelled[intentHash], "Intent cancelled");

        // Check deadline
        require(block.timestamp <= intent.deadline, "Intent expired");

        // Validate minimum output amount
        require(fulfillment.outputAmount >= intent.minimumOutputAmount, "Insufficient output amount");

        // Mark as fulfilled
        intentFulfilled[intentHash] = true;

        // Emit event
        emit IntentFulfilled(intentHash, fulfillment.solver, fulfillment.outputAmount);
    }

    /**
     * @dev Cancels an intent (only by the original user)
     * @param intentHash The hash of the intent to cancel
     */
    function cancelIntent(bytes32 intentHash) external override nonReentrant {
        Intent memory intent = intents[intentHash];

        // Validate intent exists and caller is the user
        require(intent.user != address(0), "Intent does not exist");
        require(msg.sender == intent.user, "Only user can cancel");
        require(!intentFulfilled[intentHash], "Intent already fulfilled");
        require(!intentCancelled[intentHash], "Intent already cancelled");

        // Mark as cancelled
        intentCancelled[intentHash] = true;

        // Emit event
        emit IntentCancelled(intentHash, intent.user);
    }

    /**
     * @dev Gets intent data by hash
     * @param intentHash The hash of the intent
     * @return intent The intent data
     */
    function getIntent(bytes32 intentHash) external view override returns (Intent memory intent) {
        return intents[intentHash];
    }

    /**
     * @dev Checks if an intent is fulfilled
     * @param intentHash The hash of the intent
     * @return fulfilled True if the intent is fulfilled
     */
    function isIntentFulfilled(bytes32 intentHash) external view override returns (bool fulfilled) {
        return intentFulfilled[intentHash];
    }

    /**
     * @dev Computes the hash of an intent
     * @param intent The intent data
     * @return hash The computed hash
     */
    function computeIntentHash(Intent calldata intent) external pure override returns (bytes32 hash) {
        return IntentLib.computeIntentHash(intent);
    }

    /**
     * @dev Checks if an intent is cancelled
     * @param intentHash The hash of the intent
     * @return cancelled True if the intent is cancelled
     */
    function isIntentCancelled(bytes32 intentHash) external view returns (bool cancelled) {
        return intentCancelled[intentHash];
    }

    /**
     * @dev Gets the current nonce for a user
     * @param user The user address
     * @return nonce The current nonce
     */
    function getUserNonce(address user) external view returns (uint256 nonce) {
        return userNonces[user];
    }

    /**
     * @dev Authorizes or deauthorizes a solver (only owner)
     * @param solver The solver address
     * @param authorized Whether the solver is authorized
     */
    function setSolverAuthorization(address solver, bool authorized) external onlyOwner {
        authorizedSolvers[solver] = authorized;
        emit SolverAuthorized(solver, authorized);
    }

    /**
     * @dev Sets chain support status (only owner)
     * @param chainId The chain ID
     * @param supported Whether the chain is supported
     */
    function setSupportedChain(uint256 chainId, bool supported) external onlyOwner {
        _setSupportedChain(chainId, supported);
    }

    /**
     * @dev Sets token support status for a specific chain (only owner)
     * @param token The token address
     * @param chainId The chain ID
     * @param supported Whether the token is supported on this chain
     */
    function setSupportedToken(address token, uint256 chainId, bool supported) external onlyOwner {
        validationConfig.supportedTokens[token][chainId] = supported;
        emit TokenSupported(token, chainId, supported);
    }

    /**
     * @dev Sets deadline limits (only owner)
     * @param _minimumDeadline The minimum deadline in seconds
     * @param _maximumDeadline The maximum deadline in seconds
     */
    function setDeadlineLimits(uint256 _minimumDeadline, uint256 _maximumDeadline) external onlyOwner {
        require(_minimumDeadline < _maximumDeadline, "Invalid deadline limits");
        validationConfig.minimumDeadline = _minimumDeadline;
        validationConfig.maximumDeadline = _maximumDeadline;
        emit DeadlineLimitsUpdated(_minimumDeadline, _maximumDeadline);
    }

    /**
     * @dev Sets maximum price impact (only owner)
     * @param _maxPriceImpact Maximum price impact in basis points
     */
    function setMaxPriceImpact(uint256 _maxPriceImpact) external onlyOwner {
        require(_maxPriceImpact <= 5000, "Price impact too high"); // Max 50%
        validationConfig.maxPriceImpact = _maxPriceImpact;
        emit ValidationConfigUpdated();
    }

    /**
     * @dev Pauses the contract (only owner)
     */
    function pause() external onlyOwner {
        _pause();
    }

    /**
     * @dev Unpauses the contract (only owner)
     */
    function unpause() external onlyOwner {
        _unpause();
    }

    /**
     * @dev Internal function to set chain support
     * @param chainId The chain ID
     * @param supported Whether the chain is supported
     */
    function _setSupportedChain(uint256 chainId, bool supported) internal {
        validationConfig.supportedChains[chainId] = supported;
        emit ChainSupported(chainId, supported);
    }

    /**
     * @dev Validates an intent using the validation library
     * @param intent The intent to validate
     * @return result The validation result
     */
    function validateIntentExternal(Intent calldata intent) 
        external 
        view 
        returns (IntentValidator.ValidationResult memory result) 
    {
        return intent.validateIntent(validationConfig);
    }

    /**
     * @dev Checks if a chain is supported
     * @param chainId The chain ID to check
     * @return supported True if the chain is supported
     */
    function isChainSupported(uint256 chainId) external view returns (bool supported) {
        return validationConfig.supportedChains[chainId];
    }

    /**
     * @dev Checks if a token is supported on a specific chain
     * @param token The token address
     * @param chainId The chain ID
     * @return supported True if the token is supported on the chain
     */
    function isTokenSupported(address token, uint256 chainId) external view returns (bool supported) {
        return validationConfig.supportedTokens[token][chainId];
    }

    /**
     * @dev Gets current validation configuration
     * @return minimumDeadline Minimum deadline in seconds
     * @return maximumDeadline Maximum deadline in seconds
     * @return maxPriceImpact Maximum price impact in basis points
     */
    function getValidationConfig() external view returns (
        uint256 minimumDeadline,
        uint256 maximumDeadline,
        uint256 maxPriceImpact
    ) {
        return (
            validationConfig.minimumDeadline,
            validationConfig.maximumDeadline,
            validationConfig.maxPriceImpact
        );
    }

    /**
     * @dev Submits a solver bid for an intent
     * @param intentHash The hash of the intent
     * @param outputAmount The output amount the solver can provide
     * @param executionTimeEstimate Estimated execution time in seconds
     * @param gasFeeEstimate Estimated gas fee
     * @param solverFee Solver's fee
     */
    function submitSolverBid(
        bytes32 intentHash,
        uint256 outputAmount,
        uint256 executionTimeEstimate,
        uint256 gasFeeEstimate,
        uint256 solverFee
    ) external nonReentrant whenNotPaused {
        require(authorizedSolvers[msg.sender], "Unauthorized solver");
        
        Intent memory intent = intents[intentHash];
        require(intent.user != address(0), "Intent does not exist");
        require(!intentFulfilled[intentHash], "Intent already fulfilled");
        require(!intentCancelled[intentHash], "Intent cancelled");
        require(block.timestamp <= intent.deadline, "Intent expired");
        
        // Validate minimum output amount
        require(outputAmount >= intent.minimumOutputAmount, "Output amount too low");
        
        // Check if solver already has a bid
        require(!solverBids[intentHash][msg.sender].isValid, "Solver already bid");
        
        // Create bid
        SolverBid memory bid = SolverBid({
            solver: msg.sender,
            outputAmount: outputAmount,
            executionTimeEstimate: executionTimeEstimate,
            gasFeeEstimate: gasFeeEstimate,
            solverFee: solverFee,
            bidTimestamp: block.timestamp,
            isValid: true
        });
        
        solverBids[intentHash][msg.sender] = bid;
        intentBidders[intentHash].push(msg.sender);
        
        emit SolverBidReceived(intentHash, msg.sender, outputAmount);
    }

    /**
     * @dev Selects the best solver for an intent (can be called by anyone after bid period)
     * @param intentHash The hash of the intent
     * @return selectedSolver The address of the selected solver
     */
    function selectBestSolver(bytes32 intentHash) external nonReentrant returns (address selectedSolver) {
        Intent memory intent = intents[intentHash];
        require(intent.user != address(0), "Intent does not exist");
        require(!intentFulfilled[intentHash], "Intent already fulfilled");
        require(!intentCancelled[intentHash], "Intent cancelled");
        require(selectedSolvers[intentHash] == address(0), "Solver already selected");
        
        address[] memory bidders = intentBidders[intentHash];
        require(bidders.length > 0, "No bids received");
        
        // Simple selection algorithm - highest output amount wins
        // In production, would use more sophisticated scoring
        address bestSolver = address(0);
        uint256 bestOutput = 0;
        
        for (uint256 i = 0; i < bidders.length; i++) {
            address solver = bidders[i];
            SolverBid memory bid = solverBids[intentHash][solver];
            
            if (bid.isValid && bid.outputAmount > bestOutput) {
                bestOutput = bid.outputAmount;
                bestSolver = solver;
            }
        }
        
        require(bestSolver != address(0), "No valid bids found");
        
        selectedSolvers[intentHash] = bestSolver;
        
        emit SolverSelected(intentHash, bestSolver, bestOutput);
        
        return bestSolver;
    }

    /**
     * @dev Gets solver bid for an intent
     * @param intentHash The hash of the intent
     * @param solver The solver address
     * @return bid The solver's bid
     */
    function getSolverBid(bytes32 intentHash, address solver) external view returns (SolverBid memory bid) {
        return solverBids[intentHash][solver];
    }

    /**
     * @dev Gets all bidders for an intent
     * @param intentHash The hash of the intent
     * @return bidders Array of solver addresses that bid
     */
    function getIntentBidders(bytes32 intentHash) external view returns (address[] memory bidders) {
        return intentBidders[intentHash];
    }

    /**
     * @dev Gets selected solver for an intent
     * @param intentHash The hash of the intent
     * @return solver The selected solver address
     */
    function getSelectedSolver(bytes32 intentHash) external view returns (address solver) {
        return selectedSolvers[intentHash];
    }

    /**
     * @dev Internal function to broadcast intent to solvers
     * @param intentHash The hash of the intent
     * @param intent The intent data
     */
    function _broadcastIntentToSolvers(bytes32 intentHash, Intent memory intent) internal {
        // Count active solvers for the required chains
        uint256 targetSolvers = 0;
        
        // In a real implementation, would iterate through registered solvers
        // and check their supported chains. For now, emit event for off-chain processing
        
        emit IntentBroadcasted(intentHash, intent.user, targetSolvers);
    }

    /**
     * @dev Batch function to get multiple intent statuses
     * @param intentHashes Array of intent hashes
     * @return statuses Array of status structs
     */
    function getIntentStatuses(bytes32[] calldata intentHashes) 
        external 
        view 
        returns (IntentStatus[] memory statuses) 
    {
        statuses = new IntentStatus[](intentHashes.length);
        
        for (uint256 i = 0; i < intentHashes.length; i++) {
            bytes32 hash = intentHashes[i];
            statuses[i] = IntentStatus({
                exists: intents[hash].user != address(0),
                fulfilled: intentFulfilled[hash],
                cancelled: intentCancelled[hash],
                expired: intents[hash].deadline < block.timestamp
            });
        }
    }

    /**
     * @dev Struct for batch intent status queries
     */
    struct IntentStatus {
        bool exists;
        bool fulfilled;
        bool cancelled;
        bool expired;
    }
}