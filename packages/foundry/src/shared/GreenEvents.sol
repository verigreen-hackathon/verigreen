// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

library GreenEvents {
    // GreenEntropy
    event RandomNumberRequested(uint64 indexed sequenceNumber, bytes32 userRandomNumber);
    event RandomNumberGenerated(uint64 indexed sequenceNumber, uint256 randomNumber);

    // VeriGreen
    event LandClaimed(address indexed owner, string indexed forestId, string coordinate1, string coordinate2, string coordinate3, string coordinate4 );
    event LandTilesVerified(address indexed owner, string forestId, bytes32 tilesHash);
}