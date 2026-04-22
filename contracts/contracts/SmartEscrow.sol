// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "./interfaces/IERC7683.sol";

/**
 * @title SmartEscrow
 * @dev Smart contract for secure cross-chain trade settlement
 * @notice This contract holds user funds safely until cross-chain trades are fulfilled
 */
contract SmartEscrow is Ownable, ReentrancyGuard, Pausable {
    using SafeERC20 for IERC20;

    /// @dev Default timeout period for trades (30 minutes)
    uint256 public constant DEFAULT_TIMEOUT_PERIOD = 30 minutes;
    
    /// @dev Maximum timeout period (7 days)
    uint256 public constant MAX_TIMEOUT_PERIOD = 7 days;
    
    /// @dev Minimum timeout period (5 minutes)
    uint256 public constant MIN_TIMEOUT_PERIOD = 5 minutes;

    /// @dev Current timeout period for new escrows
    uint256 public timeoutPeriod = DEFAULT_TIMEOUT_PERIOD;

    /// @dev Mapping from intent hash to escrow data
    mapping(bytes32 => EscrowData) public escrows;

    /// @dev Mapping from solver address to authorization status
    mapping(address => bool) public authorizedSolvers;

    /// @dev Mapping from intent hash to fulfillment proof
    mapping(bytes32 => FulfillmentProof) public fulfillmentProofs;

    /// @dev Multi-signature governance addresses
    mapping(address => bool) public governanceMembers;
    uint256 public governanceThreshold;
    uint256 public governanceMemberCount;

    /// @dev Emergency governance proposals
    mapping(bytes32 => GovernanceProposal) public governanceProposals;
    mapping(bytes32 => mapping(address => bool)) public proposalVotes;

    /// @dev Escrow data structure
    struct EscrowData {
        address user;
        address token;
        uint256 amount;
        uint256 lockTimestamp;
        uint256 timeoutDeadline;
        bytes32 intentHash;
        EscrowStatus status;
        address selectedSolver;
    }

    /// @dev Fulfillment proof structure
    struct FulfillmentProof {
        address solver;
        uint256 outputAmount;
        bytes32 destinationTxHash;
        uint256 destinationChainId;
        bytes proof;
        uint256 timestamp;
        bool verified;
    }

    /// @dev Governance proposal structure
    struct GovernanceProposal {
        address proposer;
        bytes32 action;
        bytes data;
        uint256 timestamp;
        uint256 voteCount;
        bool executed;
        ProposalType proposalType;
    }

    /// @dev Escrow status enumeration
    enum EscrowStatus {
        NONE,
        LOCKED,
        FULFILLED,
        REFUNDED,
        EMERGENCY_WITHDRAWN
    }

    /// @dev Governance proposal types
    enum ProposalType {
        EMERGENCY_PAUSE,
        EMERGENCY_WITHDRAW,
        SOLVER_AUTHORIZATION,
        TIMEOUT_CHANGE
    }

    /// @dev Events for escrow operations
    event FundsLocked(
        bytes32 indexed intentHash,
        address indexed user,
        address indexed token,
        uint256 amount,
        uint256 timeoutDeadline
    );

    event FundsReleased(
        bytes32 indexed intentHash,
        address indexed solver,
        address indexed user,
        uint256 amount
    );

    event FundsRefunded(
        bytes32 indexed intentHash,
        address indexed user,
        uint256 amount
    );

    event TimeoutPeriodUpdated(uint256 oldPeriod, uint256 newPeriod);

    event SolverAuthorized(address indexed solver, bool authorized);

    event FulfillmentProofSubmitted(
        bytes32 indexed intentHash,
        address indexed solver,
        uint256 outputAmount,
        bytes32 destinationTxHash
    );

    event FulfillmentProofVerified(
        bytes32 indexed intentHash,
        address indexed solver,
        bool verified
    );

    event GovernanceMemberAdded(address indexed member);
    event GovernanceMemberRemoved(address indexed member);
    event GovernanceThresholdUpdated(uint256 oldThreshold, uint256 newThreshold);

    event GovernanceProposalCreated(
        bytes32 indexed proposalId,
        address indexed proposer,
        ProposalType proposalType
    );

    event GovernanceProposalVoted(
        bytes32 indexed proposalId,
        address indexed voter,
        uint256 voteCount
    );

    event GovernanceProposalExecuted(
        bytes32 indexed proposalId,
        address indexed executor
    );

    event EmergencyWithdrawal(
        bytes32 indexed intentHash,
        address indexed user,
        uint256 amount
    );

    /**
     * @dev Constructor
     * @param initialOwner The initial owner of the contract
     * @param _governanceMembers Initial governance members
     * @param _governanceThreshold Number of votes required for governance actions
     */
    constructor(
        address initialOwner,
        address[] memory _governanceMembers,
        uint256 _governanceThreshold
    ) Ownable(initialOwner) {
        require(_governanceThreshold > 0, "Invalid governance threshold");
        require(_governanceMembers.length >= _governanceThreshold, "Not enough governance members");

        governanceThreshold = _governanceThreshold;
        governanceMemberCount = _governanceMembers.length;

        for (uint256 i = 0; i < _governanceMembers.length; i++) {
            require(_governanceMembers[i] != address(0), "Invalid governance member");
            governanceMembers[_governanceMembers[i]] = true;
            emit GovernanceMemberAdded(_governanceMembers[i]);
        }
    }

    /**
     * @dev Locks funds in escrow for a cross-chain trade
     * @param intentHash The hash of the intent
     * @param token The token address to lock
     * @param amount The amount to lock
     * @param user The user address
     * @param selectedSolver The solver selected for this intent
     */
    function lockFunds(
        bytes32 intentHash,
        address token,
        uint256 amount,
        address user,
        address selectedSolver
    ) external nonReentrant whenNotPaused {
        require(intentHash != bytes32(0), "Invalid intent hash");
        require(token != address(0), "Invalid token address");
        require(amount > 0, "Invalid amount");
        require(user != address(0), "Invalid user address");
        require(selectedSolver != address(0), "Invalid solver address");
        require(authorizedSolvers[selectedSolver], "Solver not authorized");
        require(escrows[intentHash].status == EscrowStatus.NONE, "Escrow already exists");

        // Transfer tokens from user to escrow
        IERC20(token).safeTransferFrom(user, address(this), amount);

        // Calculate timeout deadline
        uint256 timeoutDeadline = block.timestamp + timeoutPeriod;

        // Create escrow data
        escrows[intentHash] = EscrowData({
            user: user,
            token: token,
            amount: amount,
            lockTimestamp: block.timestamp,
            timeoutDeadline: timeoutDeadline,
            intentHash: intentHash,
            status: EscrowStatus.LOCKED,
            selectedSolver: selectedSolver
        });

        emit FundsLocked(intentHash, user, token, amount, timeoutDeadline);
    }

    /**
     * @dev Releases funds from escrow after successful fulfillment
     * @param intentHash The hash of the intent
     * @param fulfillmentProof The proof of fulfillment
     */
    function releaseFunds(
        bytes32 intentHash,
        FulfillmentProof calldata fulfillmentProof
    ) external nonReentrant whenNotPaused {
        EscrowData storage escrow = escrows[intentHash];
        
        require(escrow.status == EscrowStatus.LOCKED, "Invalid escrow status");
        require(block.timestamp <= escrow.timeoutDeadline, "Escrow timed out");
        require(fulfillmentProof.solver == escrow.selectedSolver, "Invalid solver");
        require(authorizedSolvers[fulfillmentProof.solver], "Solver not authorized");

        // Store fulfillment proof
        fulfillmentProofs[intentHash] = fulfillmentProof;

        // Verify fulfillment proof (simplified for Phase 1)
        bool proofValid = _verifyFulfillmentProof(intentHash, fulfillmentProof);
        require(proofValid, "Invalid fulfillment proof");

        // Update escrow status
        escrow.status = EscrowStatus.FULFILLED;

        // Release funds to solver (they've already provided output tokens to user)
        IERC20(escrow.token).safeTransfer(fulfillmentProof.solver, escrow.amount);

        emit FulfillmentProofSubmitted(
            intentHash,
            fulfillmentProof.solver,
            fulfillmentProof.outputAmount,
            fulfillmentProof.destinationTxHash
        );

        emit FulfillmentProofVerified(intentHash, fulfillmentProof.solver, true);

        emit FundsReleased(intentHash, fulfillmentProof.solver, escrow.user, escrow.amount);
    }

    /**
     * @dev Refunds funds to user after timeout
     * @param intentHash The hash of the intent
     */
    function refundFunds(bytes32 intentHash) external nonReentrant {
        EscrowData storage escrow = escrows[intentHash];
        
        require(escrow.status == EscrowStatus.LOCKED, "Invalid escrow status");
        require(block.timestamp > escrow.timeoutDeadline, "Timeout not reached");

        // Update escrow status
        escrow.status = EscrowStatus.REFUNDED;

        // Refund tokens to user
        IERC20(escrow.token).safeTransfer(escrow.user, escrow.amount);

        emit FundsRefunded(intentHash, escrow.user, escrow.amount);
    }

    /**
     * @dev Gets escrow status for an intent
     * @param intentHash The hash of the intent
     * @return status The current escrow status
     */
    function getEscrowStatus(bytes32 intentHash) external view returns (EscrowStatus status) {
        return escrows[intentHash].status;
    }

    /**
     * @dev Gets complete escrow data for an intent
     * @param intentHash The hash of the intent
     * @return escrowData The complete escrow data
     */
    function getEscrowData(bytes32 intentHash) external view returns (EscrowData memory escrowData) {
        return escrows[intentHash];
    }

    /**
     * @dev Sets the timeout period for new escrows (only owner)
     * @param newTimeoutPeriod The new timeout period in seconds
     */
    function setTimeoutPeriod(uint256 newTimeoutPeriod) external onlyOwner {
        require(newTimeoutPeriod >= MIN_TIMEOUT_PERIOD, "Timeout too short");
        require(newTimeoutPeriod <= MAX_TIMEOUT_PERIOD, "Timeout too long");

        uint256 oldPeriod = timeoutPeriod;
        timeoutPeriod = newTimeoutPeriod;

        emit TimeoutPeriodUpdated(oldPeriod, newTimeoutPeriod);
    }

    /**
     * @dev Authorizes or deauthorizes a solver (only owner)
     * @param solver The solver address
     * @param authorized Whether the solver is authorized
     */
    function setSolverAuthorization(address solver, bool authorized) external onlyOwner {
        require(solver != address(0), "Invalid solver address");
        authorizedSolvers[solver] = authorized;
        emit SolverAuthorized(solver, authorized);
    }

    /**
     * @dev Pauses the contract (only owner or governance)
     */
    function pause() external {
        require(msg.sender == owner() || governanceMembers[msg.sender], "Unauthorized");
        _pause();
    }

    /**
     * @dev Unpauses the contract (only owner)
     */
    function unpause() external onlyOwner {
        _unpause();
    }

    /**
     * @dev Adds a governance member (only owner)
     * @param member The address to add as governance member
     */
    function addGovernanceMember(address member) external onlyOwner {
        require(member != address(0), "Invalid member address");
        require(!governanceMembers[member], "Already a member");

        governanceMembers[member] = true;
        governanceMemberCount++;

        emit GovernanceMemberAdded(member);
    }

    /**
     * @dev Removes a governance member (only owner)
     * @param member The address to remove from governance
     */
    function removeGovernanceMember(address member) external onlyOwner {
        require(governanceMembers[member], "Not a member");
        require(governanceMemberCount > governanceThreshold, "Cannot remove, would break threshold");

        governanceMembers[member] = false;
        governanceMemberCount--;

        emit GovernanceMemberRemoved(member);
    }

    /**
     * @dev Updates governance threshold (only owner)
     * @param newThreshold The new threshold for governance actions
     */
    function setGovernanceThreshold(uint256 newThreshold) external onlyOwner {
        require(newThreshold > 0, "Invalid threshold");
        require(newThreshold <= governanceMemberCount, "Threshold too high");

        uint256 oldThreshold = governanceThreshold;
        governanceThreshold = newThreshold;

        emit GovernanceThresholdUpdated(oldThreshold, newThreshold);
    }

    /**
     * @dev Creates a governance proposal (only governance members)
     * @param action The action identifier
     * @param data The proposal data
     * @param proposalType The type of proposal
     * @return proposalId The ID of the created proposal
     */
    function createGovernanceProposal(
        bytes32 action,
        bytes calldata data,
        ProposalType proposalType
    ) external returns (bytes32 proposalId) {
        require(governanceMembers[msg.sender], "Not a governance member");

        proposalId = keccak256(abi.encodePacked(action, data, block.timestamp, msg.sender));

        governanceProposals[proposalId] = GovernanceProposal({
            proposer: msg.sender,
            action: action,
            data: data,
            timestamp: block.timestamp,
            voteCount: 1, // Proposer automatically votes
            executed: false,
            proposalType: proposalType
        });

        proposalVotes[proposalId][msg.sender] = true;

        emit GovernanceProposalCreated(proposalId, msg.sender, proposalType);
        emit GovernanceProposalVoted(proposalId, msg.sender, 1);

        return proposalId;
    }

    /**
     * @dev Votes on a governance proposal (only governance members)
     * @param proposalId The ID of the proposal
     */
    function voteOnProposal(bytes32 proposalId) external {
        require(governanceMembers[msg.sender], "Not a governance member");
        require(!proposalVotes[proposalId][msg.sender], "Already voted");

        GovernanceProposal storage proposal = governanceProposals[proposalId];
        require(proposal.proposer != address(0), "Proposal does not exist");
        require(!proposal.executed, "Proposal already executed");

        proposalVotes[proposalId][msg.sender] = true;
        proposal.voteCount++;

        emit GovernanceProposalVoted(proposalId, msg.sender, proposal.voteCount);
    }

    /**
     * @dev Executes a governance proposal if threshold is met
     * @param proposalId The ID of the proposal
     */
    function executeGovernanceProposal(bytes32 proposalId) external {
        GovernanceProposal storage proposal = governanceProposals[proposalId];
        require(proposal.proposer != address(0), "Proposal does not exist");
        require(!proposal.executed, "Proposal already executed");
        require(proposal.voteCount >= governanceThreshold, "Insufficient votes");

        proposal.executed = true;

        // Execute based on proposal type
        if (proposal.proposalType == ProposalType.EMERGENCY_PAUSE) {
            _pause();
        } else if (proposal.proposalType == ProposalType.EMERGENCY_WITHDRAW) {
            _executeEmergencyWithdrawal(proposal.data);
        }
        // Add more proposal type handlers as needed

        emit GovernanceProposalExecuted(proposalId, msg.sender);
    }

    /**
     * @dev Emergency withdrawal function (governance only)
     * @param intentHash The intent hash for emergency withdrawal
     */
    function emergencyWithdraw(bytes32 intentHash) external {
        require(governanceMembers[msg.sender], "Not a governance member");
        
        EscrowData storage escrow = escrows[intentHash];
        require(escrow.status == EscrowStatus.LOCKED, "Invalid escrow status");

        // Update escrow status
        escrow.status = EscrowStatus.EMERGENCY_WITHDRAWN;

        // Return funds to user
        IERC20(escrow.token).safeTransfer(escrow.user, escrow.amount);

        emit EmergencyWithdrawal(intentHash, escrow.user, escrow.amount);
    }

    /**
     * @dev Checks if an address is an authorized solver
     * @param solver The solver address to check
     * @return authorized True if the solver is authorized
     */
    function isSolverAuthorized(address solver) external view returns (bool authorized) {
        return authorizedSolvers[solver];
    }

    /**
     * @dev Gets fulfillment proof for an intent
     * @param intentHash The hash of the intent
     * @return proof The fulfillment proof
     */
    function getFulfillmentProof(bytes32 intentHash) external view returns (FulfillmentProof memory proof) {
        return fulfillmentProofs[intentHash];
    }

    /**
     * @dev Batch function to get multiple escrow statuses
     * @param intentHashes Array of intent hashes
     * @return statuses Array of escrow statuses
     */
    function getEscrowStatuses(bytes32[] calldata intentHashes) 
        external 
        view 
        returns (EscrowStatus[] memory statuses) 
    {
        statuses = new EscrowStatus[](intentHashes.length);
        
        for (uint256 i = 0; i < intentHashes.length; i++) {
            statuses[i] = escrows[intentHashes[i]].status;
        }
    }

    /**
     * @dev Internal function to verify fulfillment proof
     * @param intentHash The intent hash
     * @param proof The fulfillment proof
     * @return valid True if the proof is valid
     */
    function _verifyFulfillmentProof(
        bytes32 intentHash,
        FulfillmentProof calldata proof
    ) internal pure returns (bool valid) {
        // Simplified verification for Phase 1
        // In production, would verify cross-chain transaction proof
        return proof.destinationTxHash != bytes32(0) && 
               proof.outputAmount > 0 && 
               proof.destinationChainId > 0;
    }

    /**
     * @dev Internal function to execute emergency withdrawal
     * @param data The encoded intent hash for withdrawal
     */
    function _executeEmergencyWithdrawal(bytes memory data) internal {
        bytes32 intentHash = abi.decode(data, (bytes32));
        
        EscrowData storage escrow = escrows[intentHash];
        require(escrow.status == EscrowStatus.LOCKED, "Invalid escrow status");

        escrow.status = EscrowStatus.EMERGENCY_WITHDRAWN;
        IERC20(escrow.token).safeTransfer(escrow.user, escrow.amount);

        emit EmergencyWithdrawal(intentHash, escrow.user, escrow.amount);
    }
}