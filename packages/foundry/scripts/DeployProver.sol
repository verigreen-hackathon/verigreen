// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

import { GreenWebProofProver } from '../src/vlayer/GreenWebProofProver.sol';
import { Script } from '../dependencies/forge-std-1.9.4/src/Script.sol';

contract EntropyScript is Script {
    function run() public {
        vm.createSelectFork("optimism-sepolia");
        vm.startBroadcast();
        new GreenWebProofProver();
        vm.stopBroadcast();
    }
}