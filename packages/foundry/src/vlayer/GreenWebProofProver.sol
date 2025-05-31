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

    // Mock government land registry API endpoint
    string dataUrl = "https://api.landrecords.gov/v1/ownership/verify";

    function main(WebProof calldata webProof, address account)
        public
        view
        returns (Proof memory, string memory, string memory, uint256, address)
    {
        // Verify the web proof against the expected government URL
        Web memory web = webProof.verify(dataUrl);

        // Extract land ownership data from the verified web response
        string memory ownerName = web.jsonGetString("owner.name");
        string memory landId = web.jsonGetString("property.id");
        uint256 landPortion = web.jsonGetUint("property.portion_sqm");

        return (proof(), ownerName, landId, landPortion, account);
    }
}
