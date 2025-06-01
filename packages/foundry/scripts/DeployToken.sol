// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

import { GreenToken } from '../src/GreenToken.sol';
import { Script } from '../dependencies/forge-std-1.9.4/src/Script.sol';

contract EntropyScript is Script {
    function run() public {
        vm.createSelectFork("optimism-sepolia");
        vm.startBroadcast();
        new GreenToken(0x41Ed27F978463b21639704883F1466a67c0E56Af, 0xe04cd2CCa7C8f0eCc12feFca2642384bCAA7821F); // wallet, verigreen
        vm.stopBroadcast();
    }
}