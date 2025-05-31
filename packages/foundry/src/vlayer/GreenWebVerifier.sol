// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

import {GreenWebProofProver} from "./GreenWebProofProver.sol";
import {Proof} from "vlayer-0.1.0/Proof.sol";
import {Verifier} from "vlayer-0.1.0/Verifier.sol";

import {IVeriGreen} from '../interfaces/IVeriGreen.sol';

import { GreenEvents } from '../shared/GreenEvents.sol';


contract WebProofVerifier is Verifier{
    address public prover;
    IVeriGreen public veriGreen;

    constructor(address _prover, address _veriGreen) {
        prover = _prover;
        veriGreen = IVeriGreen(_veriGreen);
    }

    function verify(Proof calldata, uint256 forestId, address account)
        external
        onlyVerified(prover, GreenWebProofProver.main.selector)
    {
        veriGreen.verifyLand(account, forestId);
    }
}

