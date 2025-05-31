// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

library GreenEvents {
    // GreenEntropy
    event RandomNumberRequested(uint64 indexed sequenceNumber, bytes32 userRandomNumber);
    event RandomNumberGenerated(uint64 indexed sequenceNumber, uint256 randomNumber);

    // VeriGreen
    event LandClaimed(address indexed owner, uint256 indexed forestId);
    event LandTilesVerified(address indexed owner, uint256 indexed forestId, bytes32 tilesHash);
}