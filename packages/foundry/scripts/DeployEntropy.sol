// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

import { GreenEntropy } from '../src/pyth/GreenEntropy.sol';
import { Script } from '../dependencies/forge-std-1.9.4/src/Script.sol';

contract EntropyScript is Script {
    function run() public {
        vm.createSelectFork("optimism-sepolia");
        vm.startBroadcast();
        new GreenEntropy(0x4821932D0CDd71225A6d914706A621e0389D7061);
        vm.stopBroadcast();
    }
}