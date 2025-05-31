// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

import {Script, console} from "forge-std/Script.sol";
import {GreenWebProofProver} from "../src/vlayer/GreenWebProofProver.sol";
import {GreenWebVerifier} from "../src/vlayer/GreenWebVerifier.sol";

contract DeployGreenWebProof is Script {
    GreenWebProofProver public prover;
    GreenWebVerifier public verifier;
    
    function setUp() public {}

    function run() public {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerPrivateKey);
        
        console.log("===========================================");
        console.log("🚀 Deploying Green Land Ownership Contracts");
        console.log("===========================================");
        console.log("Deployer:", deployer);
        console.log("Chain ID:", block.chainid);
        console.log("Block Number:", block.number);
        console.log("");

        vm.startBroadcast(deployerPrivateKey);

        // Deploy the Prover contract
        console.log("📄 Deploying GreenWebProofProver...");
        prover = new GreenWebProofProver();
        console.log("✅ GreenWebProofProver deployed at:", address(prover));
        console.log("");

        // Deploy the Verifier contract with the Prover address
        console.log("📄 Deploying GreenWebVerifier...");
        verifier = new GreenWebVerifier(address(prover));
        console.log("✅ GreenWebVerifier deployed at:", address(verifier));
        console.log("");

        vm.stopBroadcast();

        // Verify deployment
        console.log("🔍 Verifying deployment...");
        require(address(prover) != address(0), "Prover deployment failed");
        require(address(verifier) != address(0), "Verifier deployment failed");
        require(verifier.prover() == address(prover), "Verifier-Prover link failed");
        
        // Check ERC721 metadata
        console.log("📋 ERC721 Metadata:");
        console.log("- Name:", verifier.name());
        console.log("- Symbol:", verifier.symbol());
        console.log("");

        // Display final summary
        console.log("===========================================");
        console.log("🎉 Deployment Summary");
        console.log("===========================================");
        console.log("GreenWebProofProver:", address(prover));
        console.log("GreenWebVerifier:", address(verifier));
        console.log("Deployer:", deployer);
        console.log("Chain ID:", block.chainid);
        console.log("");
        
        console.log("📝 Next Steps:");
        console.log("1. Update your .env file with the contract addresses");
        console.log("2. Run the land ownership proving script:");
        console.log("   bun run vlayer/proveLandOwnership.ts");
        console.log("3. Verify contracts on block explorer if needed");
        console.log("");
        
        console.log("🌐 Expected Government API Integration:");
        console.log("- URL: https://api.landrecords.gov/v1/ownership/verify");
        console.log("- Method: GET with authentication");
        console.log("- Response: JSON with owner and property data");
        console.log("");
        
        console.log("🔗 Contract Interaction:");
        console.log("- Generate WebProof using vlayer browser extension");
        console.log("- Call GreenWebProofProver.main() off-chain via vlayer");
        console.log("- Submit proof to GreenWebVerifier.verify() on-chain");
        console.log("- User receives land ownership NFT upon verification");
        console.log("===========================================");
    }

    function getProverAddress() public view returns (address) {
        return address(prover);
    }

    function getVerifierAddress() public view returns (address) {
        return address(verifier);
    }
} 