// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

interface IVeriGreen {
    function verifyLand(address account, string memory forestId, string memory coordinate1, string memory coordinate2, string memory coordinate3, string memory coordinate4) external;
}