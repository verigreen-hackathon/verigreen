// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

import {GreenWebProofProver} from "./GreenWebProofProver.sol";
import {Proof} from "vlayer-0.1.0/Proof.sol";
import {Verifier} from "vlayer-0.1.0/Verifier.sol";

import {IVeriGreen} from '../interfaces/IVeriGreen.sol';

import { GreenEvents } from '../shared/GreenEvents.sol';


contract GreenWebVerifier is Verifier{
    address public prover;
    IVeriGreen public veriGreen;

    constructor(address _prover, address _veriGreen) {
        prover = _prover;
        veriGreen = IVeriGreen(_veriGreen);
    }

    function verify(Proof calldata, string memory forestId, bytes memory coordinatesHash, address account)
        external
        onlyVerified(prover, GreenWebProofProver.main.selector)
    {
        (string memory coordinate1, string memory coordinate2, string memory coordinate3, string memory coordinate4) = abi.decode(coordinatesHash, (string, string, string, string));
        veriGreen.verifyLand(account, forestId, coordinate1, coordinate2, coordinate3, coordinate4);
    }
}

