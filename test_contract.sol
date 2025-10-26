// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract TestNFT {
    mapping(address => uint256) public balances;
    address public owner;
    
    constructor() {
        owner = msg.sender;
    }
    
    // Intentional vulnerability: missing access control
    function mint(address to, uint256 amount) public {
        balances[to] += amount;
    }
    
    // Intentional vulnerability: unchecked transfer
    function transfer(address to, uint256 amount) public {
        balances[msg.sender] -= amount;
        balances[to] += amount;
    }
    
    // Intentional vulnerability: tx.origin authentication
    function withdraw() public {
        require(tx.origin == owner, "Not owner");
        payable(msg.sender).transfer(address(this).balance);
    }
}
