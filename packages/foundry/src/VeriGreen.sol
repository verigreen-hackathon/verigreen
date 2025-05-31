// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

import { GreenErrors } from './shared/GreenErrors.sol';
import { GreenEvents } from './shared/GreenEvents.sol';

import { IVeriGreen } from './interfaces/IVeriGreen.sol';
import { IVeriGreenToken } from './interfaces/IVeriGreenToken.sol';
import { Ownable } from "openzeppelin-contracts/access/Ownable.sol";


contract VeriGreen is IVeriGreen, Ownable {
    // user address => forest id => verified tiles hash
    mapping(address => mapping(uint256 => bytes32)) userLands;
    mapping(address => uint256) verifiedUserLands;

    address public greenVerifier;
    IVeriGreenToken public greenToken;

    uint256 public rewardAmount;

    constructor(address greenVerifierAddress, address initialOwner) Ownable(initialOwner){
        greenVerifier = greenVerifierAddress;
    }

    modifier onlyVerifier() {
        if(msg.sender != greenVerifier) {
            revert GreenErrors.NotValidProver();
        }    
        _;
    }

    function setGreenTokenAddress(address greenTokenAddress_) external onlyOwner {
        greenToken = IVeriGreenToken(greenTokenAddress_);
    }

    function setRewardAmount(uint256 rewardAmount_) external onlyOwner {
        rewardAmount = rewardAmount_;
    }

    function verifyLand(address account, uint256 forestId) public onlyVerifier {
        verifiedUserLands[account] = forestId;
        
        emit GreenEvents.LandClaimed(account, forestId);
    }

    function verifyTilesInLand(address account, uint256 forestId, bytes32 tilesHash) public {
        if(verifiedUserLands[account] != forestId) {
            revert GreenErrors.LandIsNotVerified();
        }
        
        userLands[account][forestId] = tilesHash;

        greenToken.mint(account, rewardAmount);
        
        emit GreenEvents.LandTilesVerified(account, forestId, tilesHash);
    }
}