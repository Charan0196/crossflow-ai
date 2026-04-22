// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/**
 * @title TestContract
 * @dev Simple test contract to verify Hardhat setup
 */
contract TestContract {
    string public message;
    
    constructor(string memory _message) {
        message = _message;
    }
    
    function setMessage(string memory _message) public {
        message = _message;
    }
    
    function getMessage() public view returns (string memory) {
        return message;
    }
}