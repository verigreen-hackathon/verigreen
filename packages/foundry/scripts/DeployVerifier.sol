// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

import { GreenWebVerifier } from '../src/vlayer/GreenWebVerifier.sol';
import { Script } from '../dependencies/forge-std-1.9.4/src/Script.sol';

contract VerifierScript is Script {
    function run() public {
        vm.createSelectFork("optimism-sepolia");
        vm.startBroadcast();
        new GreenWebVerifier(0x1535266BCb525e7D204764a25b86B2Dc3E0A7Bd2, 0xe04cd2CCa7C8f0eCc12feFca2642384bCAA7821F); // prover, verigreen
        vm.stopBroadcast();
    }
}