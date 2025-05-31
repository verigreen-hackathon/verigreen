// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

import {GreenWebProofProver} from "./GreenWebProofProver.sol";
import {Proof} from "vlayer-0.1.0/Proof.sol";
import {Verifier} from "vlayer-0.1.0/Verifier.sol";

import {ERC721} from "openzeppelin-contracts/token/ERC721/ERC721.sol";

contract GreenWebVerifier is Verifier, ERC721 {
    address public prover;
    
    // Store land ownership data
    struct LandOwnership {
        string ownerName;
        string landId;
        uint256 landPortion;
        address verifiedOwner;
        uint256 timestamp;
    }
    
    mapping(uint256 => LandOwnership) public landRecords;
    mapping(string => uint256) public landIdToTokenId;
    
    event LandOwnershipVerified(
        uint256 indexed tokenId,
        string indexed landId,
        string ownerName,
        uint256 landPortion,
        address indexed verifiedOwner
    );

    constructor(address _prover) ERC721("GreenLandOwnership", "GLND") {
        prover = _prover;
    }

    function verify(
        Proof calldata, 
        string memory ownerName,
        string memory landId,
        uint256 landPortion,
        address account
    )
        public
        onlyVerified(prover, GreenWebProofProver.main.selector)
    {
        // Create unique token ID based on land ID
        uint256 tokenId = uint256(keccak256(abi.encodePacked(landId)));
        
        // Check if this land parcel has already been verified
        require(_ownerOf(tokenId) == address(0), "Land ownership already verified for this parcel");
        
        // Store land ownership data
        landRecords[tokenId] = LandOwnership({
            ownerName: ownerName,
            landId: landId,
            landPortion: landPortion,
            verifiedOwner: account,
            timestamp: block.timestamp
        });
        
        // Map land ID to token ID for easy lookup
        landIdToTokenId[landId] = tokenId;
        
        // Mint the land ownership NFT
        _safeMint(account, tokenId);
        
        emit LandOwnershipVerified(tokenId, landId, ownerName, landPortion, account);
    }
    
    function getLandRecord(uint256 tokenId) 
        external 
        view 
        returns (LandOwnership memory) 
    {
        require(_exists(tokenId), "Token does not exist");
        return landRecords[tokenId];
    }
    
    function getLandRecordByLandId(string memory landId) 
        external 
        view 
        returns (LandOwnership memory) 
    {
        uint256 tokenId = landIdToTokenId[landId];
        require(_exists(tokenId), "Land record does not exist");
        return landRecords[tokenId];
    }
}

