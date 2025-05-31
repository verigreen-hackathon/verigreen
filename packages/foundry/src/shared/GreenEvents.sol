// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

library GreenEvents {
    event RandomNumberRequested(uint64 indexed sequenceNumber, bytes32 userRandomNumber);
    event RandomNumberGenerated(uint64 indexed sequenceNumber, uint256 randomNumber);
}