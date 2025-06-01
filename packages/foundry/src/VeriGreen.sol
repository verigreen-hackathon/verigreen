// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

import { GreenErrors } from './shared/GreenErrors.sol';
import { GreenEvents } from './shared/GreenEvents.sol';

import { IVeriGreen } from './interfaces/IVeriGreen.sol';
import { IVeriGreenToken } from './interfaces/IVeriGreenToken.sol';
import { Ownable } from "openzeppelin-contracts/access/Ownable.sol";


contract VeriGreen is IVeriGreen, Ownable {
    // user address => forest id => verified tiles hash
    mapping(address => mapping(bytes32 => bytes32)) verifiedUserLandsWithTiles;
    mapping(address => string) userLands;

    address public greenVerifier;
    IVeriGreenToken public greenToken;

    uint256 public rewardAmount;

    constructor(address initialOwner) Ownable(initialOwner){
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

    function setVerifierAddress(address verifierAddress_) external onlyOwner {
        greenVerifier = verifierAddress_;
    }

    function setRewardAmount(uint256 rewardAmount_) external onlyOwner {
        rewardAmount = rewardAmount_;
    }

    function verifyLand(address account, string memory forestId, string memory coordinate1, string memory coordinate2, string memory coordinate3, string memory coordinate4) public onlyVerifier {
        userLands[account] = forestId; 
        
        emit GreenEvents.LandClaimed(account, forestId, coordinate1, coordinate2, coordinate3, coordinate4);
    }

    function verifyTilesInLand(address account, string memory forestId, bytes32 tilesHash) public onlyOwner {
        if(!compareStrings(userLands[account], forestId) ) {
            revert GreenErrors.LandIsNotVerified();
        }
        
        verifiedUserLandsWithTiles[account][hashString(forestId)] = tilesHash;

        greenToken.mint(account, rewardAmount);
        
        emit GreenEvents.LandTilesVerified(account, forestId, tilesHash);
    }

    function compareStrings(string memory _a, string memory _b) public pure returns(bool) {
        return keccak256(abi.encodePacked(_a)) == keccak256(abi.encodePacked(_b));
    }

    function hashString(string memory _a) public pure returns(bytes32) {
        return keccak256(abi.encodePacked(_a));
    }
}