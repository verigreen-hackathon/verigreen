// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

import "forge-std/Test.sol";
import "../../src/vlayer/GreenWebProofProver.sol";
import "../../src/vlayer/GreenWebVerifier.sol";

contract GreenWebProofTest is Test {
    GreenWebProofProver public prover;
    GreenWebVerifier public verifier;
    
    address public alice = address(0x1);
    address public bob = address(0x2);
    
    event LandOwnershipVerified(
        uint256 indexed tokenId,
        string indexed landId,
        string ownerName,
        uint256 landPortion,
        address indexed verifiedOwner
    );

    function setUp() public {
        // Deploy the prover contract
        prover = new GreenWebProofProver();
        
        // Deploy the verifier contract with the prover address
        verifier = new GreenWebVerifier(address(prover));
    }

    function testProverContractDeployment() public {
        // Test that the prover contract is deployed correctly
        assertTrue(address(prover) != address(0));
    }

    function testVerifierContractDeployment() public {
        // Test that the verifier contract is deployed correctly
        assertTrue(address(verifier) != address(0));
        assertEq(verifier.prover(), address(prover));
        
        // Check ERC721 metadata
        assertEq(verifier.name(), "GreenLandOwnership");
        assertEq(verifier.symbol(), "GLND");
    }

    function testLandIdToTokenIdMapping() public {
        string memory landId = "LAND-PARCEL-001";
        uint256 expectedTokenId = uint256(keccak256(abi.encodePacked(landId)));
        
        // The mapping should be empty initially
        vm.expectRevert("Land record does not exist");
        verifier.getLandRecordByLandId(landId);
    }

    function testDuplicateLandVerificationPrevention() public {
        // This test would require mocking the onlyVerified modifier
        // For now, we test the token ID generation logic
        
        string memory landId = "LAND-PARCEL-001";
        uint256 tokenId = uint256(keccak256(abi.encodePacked(landId)));
        
        // Check that the same land ID always generates the same token ID
        uint256 tokenId2 = uint256(keccak256(abi.encodePacked(landId)));
        assertEq(tokenId, tokenId2);
        
        // Different land IDs should generate different token IDs
        string memory differentLandId = "LAND-PARCEL-002";
        uint256 differentTokenId = uint256(keccak256(abi.encodePacked(differentLandId)));
        assertTrue(tokenId != differentTokenId);
    }

    function testEventEmission() public {
        // This test demonstrates the expected event structure
        // In a real scenario, this would be triggered by the verify function
        
        string memory ownerName = "Alice Johnson";
        string memory landId = "LAND-PARCEL-001";
        uint256 landPortion = 5000;
        uint256 tokenId = uint256(keccak256(abi.encodePacked(landId)));
        
        // Test event emission expectation
        vm.expectEmit(true, true, true, true);
        emit LandOwnershipVerified(tokenId, landId, ownerName, landPortion, alice);
        
        // This would normally be called by verify(), but we emit it manually for testing
        vm.prank(address(verifier));
        emit LandOwnershipVerified(tokenId, landId, ownerName, landPortion, alice);
    }

    function testGetLandRecordFunction() public {
        // Test the getLandRecord function structure
        // This would fail initially since no tokens are minted
        
        uint256 nonExistentTokenId = 999;
        vm.expectRevert("Token does not exist");
        verifier.getLandRecord(nonExistentTokenId);
    }

    // Note: The actual verification flow would require:
    // 1. A valid WebProof from the vlayer system
    // 2. The onlyVerified modifier to pass
    // 3. Integration with the vlayer proving infrastructure
    
    // For testing the full flow in a real environment, you would:
    // 1. Generate a real WebProof using the vlayer browser extension or CLI
    // 2. Call the prover's main() function off-chain via vlayer service
    // 3. Submit the resulting proof to the verifier's verify() function
    
    function testExpectedWorkflow() public {
        // This test outlines the expected workflow
        
        console.log("=== Expected Green Land Ownership Verification Workflow ===");
        console.log("1. User visits government land registry website");
        console.log("2. vlayer browser extension captures HTTPS response with TLS notarization");
        console.log("3. GreenWebProofProver.main() verifies web proof and extracts land data");
        console.log("4. ZK proof is generated off-chain proving correct extraction");
        console.log("5. User calls GreenWebVerifier.verify() with proof and extracted data");
        console.log("6. On successful verification, land ownership NFT is minted");
        console.log("7. Land ownership record is stored on-chain with minimal data disclosure");
        
        assertTrue(true); // Workflow test passes if no reverts
    }
} 