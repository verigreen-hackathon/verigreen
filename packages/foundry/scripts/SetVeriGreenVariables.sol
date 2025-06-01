// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

import { VeriGreen } from '../src/VeriGreen.sol';
import { Script } from '../dependencies/forge-std-1.9.4/src/Script.sol';

contract VeriGreenScript is Script {
    function run() public {
        vm.createSelectFork("optimism-sepolia");
        vm.startBroadcast(uint256(0xe83e3a756009d705b0d54a99d1dcb3213d342566d2952984897790bf0e4eae61));
        VeriGreen veriGreen = VeriGreen(0x41Ed27F978463b21639704883F1466a67c0E56Af);
        veriGreen.setRewardAmount(100 ether);
        veriGreen.setGreenTokenAddress(0x679fE316ACB2C6fDD3f4067e20Ed23b64407744D);
        veriGreen.setVerifierAddress(0x2E6542449ef64c3bF5f891FA4e73Caa395c27226);
        vm.stopBroadcast();
    }
}