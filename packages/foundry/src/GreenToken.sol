// SPDX-License-Identifier: MIT
// Compatible with OpenZeppelin Contracts ^5.0.0
pragma solidity ^0.8.30;

import {ERC20} from "openzeppelin-contracts/token/ERC20/ERC20.sol";
import {Ownable} from "openzeppelin-contracts/access/Ownable.sol";

contract GreenToken is ERC20, Ownable {
    address public veriGreen;
    constructor(address initialOwner, address veriGreen_)
        ERC20("GreenToken", "GREEN")
        Ownable(initialOwner)
    {
        veriGreen = veriGreen_;
    }

    modifier onlyOwnerAndVeriGreen {
        require(owner() != msg.sender && msg.sender != veriGreen, "Not authorized!");
        _;
    }

    function mint(address to, uint256 amount) external onlyOwnerAndVeriGreen {
        _mint(to, amount);
    }
}