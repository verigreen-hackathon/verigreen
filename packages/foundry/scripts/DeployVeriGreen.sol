// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

import { VeriGreen } from '../src/VeriGreen.sol';
import { Script } from '../dependencies/forge-std-1.9.4/src/Script.sol';

contract VeriGreenScript is Script {
    function run() public {
        vm.createSelectFork("optimism-sepolia");
        vm.startBroadcast();
        new VeriGreen(0x41Ed27F978463b21639704883F1466a67c0E56Af);
        // veriGreen.setRewardAmount(100 ether);
        // veriGreen.setGreenTokenAddress();
        // veriGreen.setVerifierAddress();
        vm.stopBroadcast();
    }
}