// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title MultiSigWallet
 * @dev Multi-signature wallet for CrossFlow AI governance
 * @notice Requires multiple signatures to execute transactions
 */
contract MultiSigWallet is ReentrancyGuard {
    /// @dev Maximum number of owners allowed
    uint256 public constant MAX_OWNER_COUNT = 50;

    /// @dev Mapping from owner address to owner status
    mapping(address => bool) public isOwner;
    
    /// @dev Array of owner addresses
    address[] public owners;
    
    /// @dev Number of required confirmations
    uint256 public required;
    
    /// @dev Mapping from transaction ID to owner confirmations
    mapping(uint256 => mapping(address => bool)) public confirmations;
    
    /// @dev Array of transactions
    Transaction[] public transactions;
    
    /// @dev Transaction structure
    struct Transaction {
        address destination;
        uint256 value;
        bytes data;
        bool executed;
        uint256 confirmationCount;
    }

    /// @dev Events
    event Confirmation(address indexed sender, uint256 indexed transactionId);
    event Revocation(address indexed sender, uint256 indexed transactionId);
    event Submission(uint256 indexed transactionId);
    event Execution(uint256 indexed transactionId);
    event ExecutionFailure(uint256 indexed transactionId);
    event Deposit(address indexed sender, uint256 value);
    event OwnerAddition(address indexed owner);
    event OwnerRemoval(address indexed owner);
    event RequirementChange(uint256 required);

    /// @dev Modifiers
    modifier onlyWallet() {
        require(msg.sender == address(this), "Only wallet can call this function");
        _;
    }

    modifier ownerDoesNotExist(address owner) {
        require(!isOwner[owner], "Owner already exists");
        _;
    }

    modifier ownerExists(address owner) {
        require(isOwner[owner], "Owner does not exist");
        _;
    }

    modifier transactionExists(uint256 transactionId) {
        require(transactionId < transactions.length, "Transaction does not exist");
        _;
    }

    modifier confirmed(uint256 transactionId, address owner) {
        require(confirmations[transactionId][owner], "Transaction not confirmed by owner");
        _;
    }

    modifier notConfirmed(uint256 transactionId, address owner) {
        require(!confirmations[transactionId][owner], "Transaction already confirmed by owner");
        _;
    }

    modifier notExecuted(uint256 transactionId) {
        require(!transactions[transactionId].executed, "Transaction already executed");
        _;
    }

    modifier notNull(address _address) {
        require(_address != address(0), "Address cannot be null");
        _;
    }

    modifier validRequirement(uint256 ownerCount, uint256 _required) {
        require(
            ownerCount <= MAX_OWNER_COUNT &&
            _required <= ownerCount &&
            _required != 0 &&
            ownerCount != 0,
            "Invalid requirement"
        );
        _;
    }

    /**
     * @dev Constructor
     * @param _owners List of initial owners
     * @param _required Number of required confirmations
     */
    constructor(address[] memory _owners, uint256 _required)
        validRequirement(_owners.length, _required)
    {
        for (uint256 i = 0; i < _owners.length; i++) {
            require(!isOwner[_owners[i]] && _owners[i] != address(0), "Invalid owner");
            isOwner[_owners[i]] = true;
        }
        owners = _owners;
        required = _required;
    }

    /**
     * @dev Allows to add a new owner. Transaction has to be sent by wallet.
     * @param owner Address of new owner.
     */
    function addOwner(address owner)
        public
        onlyWallet
        ownerDoesNotExist(owner)
        notNull(owner)
        validRequirement(owners.length + 1, required)
    {
        isOwner[owner] = true;
        owners.push(owner);
        emit OwnerAddition(owner);
    }

    /**
     * @dev Allows to remove an owner. Transaction has to be sent by wallet.
     * @param owner Address of owner.
     */
    function removeOwner(address owner) public onlyWallet ownerExists(owner) {
        isOwner[owner] = false;
        for (uint256 i = 0; i < owners.length - 1; i++) {
            if (owners[i] == owner) {
                owners[i] = owners[owners.length - 1];
                break;
            }
        }
        owners.pop();
        if (required > owners.length) changeRequirement(owners.length);
        emit OwnerRemoval(owner);
    }

    /**
     * @dev Allows to replace an owner with a new owner. Transaction has to be sent by wallet.
     * @param owner Address of owner to be replaced.
     * @param newOwner Address of new owner.
     */
    function replaceOwner(address owner, address newOwner)
        public
        onlyWallet
        ownerExists(owner)
        ownerDoesNotExist(newOwner)
    {
        for (uint256 i = 0; i < owners.length; i++) {
            if (owners[i] == owner) {
                owners[i] = newOwner;
                break;
            }
        }
        isOwner[owner] = false;
        isOwner[newOwner] = true;
        emit OwnerRemoval(owner);
        emit OwnerAddition(newOwner);
    }

    /**
     * @dev Allows to change the number of required confirmations. Transaction has to be sent by wallet.
     * @param _required Number of required confirmations.
     */
    function changeRequirement(uint256 _required)
        public
        onlyWallet
        validRequirement(owners.length, _required)
    {
        required = _required;
        emit RequirementChange(_required);
    }

    /**
     * @dev Allows an owner to submit and confirm a transaction.
     * @param destination Transaction target address.
     * @param value Transaction ether value.
     * @param data Transaction data payload.
     * @return transactionId Returns transaction ID.
     */
    function submitTransaction(
        address destination,
        uint256 value,
        bytes memory data
    ) public returns (uint256 transactionId) {
        transactionId = addTransaction(destination, value, data);
        confirmTransaction(transactionId);
    }

    /**
     * @dev Allows an owner to confirm a transaction.
     * @param transactionId Transaction ID.
     */
    function confirmTransaction(uint256 transactionId)
        public
        ownerExists(msg.sender)
        transactionExists(transactionId)
        notConfirmed(transactionId, msg.sender)
    {
        confirmations[transactionId][msg.sender] = true;
        transactions[transactionId].confirmationCount++;
        emit Confirmation(msg.sender, transactionId);
        executeTransaction(transactionId);
    }

    /**
     * @dev Allows an owner to revoke a confirmation for a transaction.
     * @param transactionId Transaction ID.
     */
    function revokeConfirmation(uint256 transactionId)
        public
        ownerExists(msg.sender)
        confirmed(transactionId, msg.sender)
        notExecuted(transactionId)
    {
        confirmations[transactionId][msg.sender] = false;
        transactions[transactionId].confirmationCount--;
        emit Revocation(msg.sender, transactionId);
    }

    /**
     * @dev Allows anyone to execute a confirmed transaction.
     * @param transactionId Transaction ID.
     */
    function executeTransaction(uint256 transactionId)
        public
        ownerExists(msg.sender)
        confirmed(transactionId, msg.sender)
        notExecuted(transactionId)
    {
        if (isConfirmed(transactionId)) {
            Transaction storage txn = transactions[transactionId];
            txn.executed = true;
            (bool success, ) = txn.destination.call{value: txn.value}(txn.data);
            if (success) {
                emit Execution(transactionId);
            } else {
                emit ExecutionFailure(transactionId);
                txn.executed = false;
            }
        }
    }

    /**
     * @dev Returns the confirmation status of a transaction.
     * @param transactionId Transaction ID.
     * @return Confirmation status.
     */
    function isConfirmed(uint256 transactionId) public view returns (bool) {
        return transactions[transactionId].confirmationCount >= required;
    }

    /**
     * @dev Adds a new transaction to the transaction mapping, if transaction does not exist yet.
     * @param destination Transaction target address.
     * @param value Transaction ether value.
     * @param data Transaction data payload.
     * @return transactionId Returns transaction ID.
     */
    function addTransaction(
        address destination,
        uint256 value,
        bytes memory data
    ) internal notNull(destination) returns (uint256 transactionId) {
        transactionId = transactions.length;
        transactions.push(
            Transaction({
                destination: destination,
                value: value,
                data: data,
                executed: false,
                confirmationCount: 0
            })
        );
        emit Submission(transactionId);
    }

    /**
     * @dev Returns number of confirmations of a transaction.
     * @param transactionId Transaction ID.
     * @return count Number of confirmations.
     */
    function getConfirmationCount(uint256 transactionId) public view returns (uint256 count) {
        return transactions[transactionId].confirmationCount;
    }

    /**
     * @dev Returns total number of transactions after filers are applied.
     * @param pending Include pending transactions.
     * @param executed Include executed transactions.
     * @return count Total number of transactions after filters are applied.
     */
    function getTransactionCount(bool pending, bool executed) public view returns (uint256 count) {
        for (uint256 i = 0; i < transactions.length; i++) {
            if ((pending && !transactions[i].executed) || (executed && transactions[i].executed)) {
                count++;
            }
        }
    }

    /**
     * @dev Returns list of owners.
     * @return List of owner addresses.
     */
    function getOwners() public view returns (address[] memory) {
        return owners;
    }

    /**
     * @dev Returns array with owner addresses, which confirmed transaction.
     * @param transactionId Transaction ID.
     * @return _confirmations Returns array of owner addresses.
     */
    function getConfirmations(uint256 transactionId)
        public
        view
        returns (address[] memory _confirmations)
    {
        address[] memory confirmationsTemp = new address[](owners.length);
        uint256 count = 0;
        uint256 i;
        for (i = 0; i < owners.length; i++) {
            if (confirmations[transactionId][owners[i]]) {
                confirmationsTemp[count] = owners[i];
                count++;
            }
        }
        _confirmations = new address[](count);
        for (i = 0; i < count; i++) {
            _confirmations[i] = confirmationsTemp[i];
        }
    }

    /**
     * @dev Returns list of transaction IDs in defined range.
     * @param from Index start position of transaction array.
     * @param to Index end position of transaction array.
     * @param pending Include pending transactions.
     * @param executed Include executed transactions.
     * @return _transactionIds Returns array of transaction IDs.
     */
    function getTransactionIds(
        uint256 from,
        uint256 to,
        bool pending,
        bool executed
    ) public view returns (uint256[] memory _transactionIds) {
        uint256[] memory transactionIdsTemp = new uint256[](transactions.length);
        uint256 count = 0;
        uint256 i;
        for (i = 0; i < transactions.length; i++) {
            if ((pending && !transactions[i].executed) || (executed && transactions[i].executed)) {
                transactionIdsTemp[count] = i;
                count++;
            }
        }
        _transactionIds = new uint256[](to - from);
        for (i = from; i < to; i++) {
            _transactionIds[i - from] = transactionIdsTemp[i];
        }
    }

    /**
     * @dev Fallback function allows to deposit ether.
     */
    receive() external payable {
        if (msg.value > 0) {
            emit Deposit(msg.sender, msg.value);
        }
    }
}