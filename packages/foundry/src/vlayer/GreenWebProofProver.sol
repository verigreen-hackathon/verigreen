// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

import {Strings} from "openzeppelin-contracts/utils/Strings.sol";
import {Proof} from "vlayer-0.1.0/Proof.sol";
import {Prover} from "vlayer-0.1.0/Prover.sol";
import {Web, WebProof, WebProofLib, WebLib} from "vlayer-0.1.0/WebProof.sol";

contract GreenWebProofProver is Prover {
    using Strings for string;
    using WebProofLib for WebProof;
    using WebLib for Web;

    string dataUrl = "https://api.x.com/1.1/account/settings.json";

    function main(WebProof calldata webProof, address account)
        public
        view
        returns (Proof memory, string memory, bytes memory, address)
    {
        Web memory web = webProof.verify(dataUrl);

        string memory forest_id = web.jsonGetString("forest_id");
        string memory coordinate1 = web.jsonGetString("coordinate1");
        string memory coordinate2 = web.jsonGetString("coordinate2");
        string memory coordinate3 = web.jsonGetString("coordinate3");
        string memory coordinate4 = web.jsonGetString("coordinate4");

        return (proof(), forest_id, abi.encode(coordinate1, coordinate2, coordinate3, coordinate4), account);
    }
}
