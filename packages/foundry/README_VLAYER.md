# Green Land Ownership - vlayer Web Proofs Implementation

This project implements a decentralized land ownership verification system using vlayer's Web Proofs technology. Users can prove their land ownership from government websites and mint verifiable NFTs on-chain without revealing unnecessary personal information.

## 🏗️ Architecture

### Smart Contracts

#### `GreenWebProofProver.sol`
- **Purpose**: Defines the off-chain proof generation logic
- **Functionality**: 
  - Verifies government land registry API responses using TLS notarization
  - Extracts owner name, land ID, and land portion from verified web data
  - Runs off-chain in vlayer's ZK proving environment
- **Key Method**: `main(WebProof calldata webProof, address account)`

#### `GreenWebVerifier.sol`  
- **Purpose**: On-chain verification and NFT minting
- **Functionality**:
  - Verifies ZK proofs from the Prover contract
  - Mints unique land ownership NFTs (ERC721)
  - Stores minimal land ownership data on-chain
  - Prevents duplicate verifications for the same land parcel
- **Key Method**: `verify(Proof calldata, string memory ownerName, string memory landId, uint256 landPortion, address account)`

### Scripts and Tools

#### `script/DeployGreenWebProof.s.sol`
- **Purpose**: Foundry deployment script for both contracts
- **Usage**: `forge script script/DeployGreenWebProof.s.sol --broadcast --rpc-url $RPC_URL`

#### `vlayer/proveLandOwnership.ts`
- **Purpose**: TypeScript script for generating land ownership proofs
- **Usage**: `bun run prove:land` (from vlayer directory)

### Data Flow

```mermaid
graph TD
    A[User visits government land registry] --> B[vlayer extension captures HTTPS response]
    B --> C[TLS Notary validates web data integrity]
    C --> D[GreenWebProofProver.main() runs off-chain]
    D --> E[ZK proof generated proving correct extraction]
    E --> F[User submits proof to GreenWebVerifier]
    F --> G[On-chain verification via onlyVerified modifier]
    G --> H[Land ownership NFT minted]
```

## 🌐 Expected Government API Structure

The system expects land registry APIs to return data in this format:

```json
{
  "owner": {
    "name": "Alice Johnson",
    "id": "GOV123456789"
  },
  "property": {
    "id": "LAND-PARCEL-001",
    "portion_sqm": 5000,
    "location": "123 Green Valley Road",
    "type": "residential"
  },
  "verification": {
    "status": "verified",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

## 🔧 Setup and Installation

### Prerequisites
- Node.js >= 18
- Foundry
- Bun runtime
- Access to Optimism Sepolia testnet

### Installation

1. **Complete setup:**
   ```bash
   cd packages/foundry/vlayer
   bun run setup
   ```

2. **Set up environment variables:**
   ```bash
   # Copy and edit environment template
   cp ../env.example ../.env
   # Edit .env with your actual values
   ```

## 🚀 Deployment

### 1. Build Contracts
```bash
# From vlayer directory
bun run build

# Or directly with Foundry
cd packages/foundry
forge build
```

### 2. Deploy to Networks

#### Local Deployment (Anvil)
```bash
# Start local node (in separate terminal)
bun run anvil

# Deploy to local network
bun run deploy:local
```

#### Optimism Sepolia Deployment
```bash
# Set environment variables first
export PRIVATE_KEY=your_private_key
export ETHERSCAN_API_KEY=your_etherscan_key

# Deploy with verification
bun run deploy:sepolia

# Or simulate deployment first
bun run deploy:simulate
```

#### Direct Foundry Commands
```bash
# Deploy to Optimism Sepolia
forge script script/DeployGreenWebProof.s.sol \
  --broadcast \
  --rpc-url https://sepolia.optimism.io \
  --private-key $PRIVATE_KEY \
  --etherscan-api-key $ETHERSCAN_API_KEY \
  --verify

# Deploy to local Anvil
forge script script/DeployGreenWebProof.s.sol \
  --broadcast \
  --rpc-url http://localhost:8545
```

### 3. Verify Contracts (if needed)
```bash
# Set contract addresses from deployment
export PROVER_ADDRESS=0x...
export VERIFIER_ADDRESS=0x...

# Verify both contracts
bun run verify:prover
bun run verify:verifier
```

## 📖 Usage

### Available Scripts

From the `packages/foundry/vlayer` directory:

```bash
# Build and test
bun run build                    # Compile contracts
bun run test                     # Run Foundry tests
bun run test:verbose             # Run tests with full output
bun run test:gas                 # Run tests with gas reporting
bun run test:coverage            # Generate coverage report

# Deployment
bun run deploy:local             # Deploy to local Anvil
bun run deploy:sepolia           # Deploy to Optimism Sepolia
bun run deploy:simulate          # Simulate deployment

# Land ownership proving
bun run prove:land               # Generate land ownership proof
bun run prove:land:debug         # Generate with debug logging

# Verification
bun run verify:prover            # Verify prover contract
bun run verify:verifier          # Verify verifier contract

# Development
bun run clean                    # Clean build artifacts
bun run setup                    # Complete setup
bun run dev                      # Full development workflow
bun run docs                     # Generate documentation

# Utilities
bun run anvil                    # Start local Anvil node
bun run lint:solidity            # Lint Solidity code
bun run lint-fix:solidity        # Fix linting issues
```

### Generating Proofs

1. **User captures land ownership data:**
   - Visit government land registry website
   - Use vlayer browser extension to capture HTTPS response
   - Extension handles TLS notarization automatically

2. **Generate ZK proof:**
   ```bash
   cd packages/foundry/vlayer
   bun run prove:land
   ```

   Or programmatically:
   ```typescript
   import { proveLandOwnership } from './vlayer/proveLandOwnership';
   
   const proofData = await proveLandOwnership();
   console.log('Proof ready for verification:', proofData);
   ```

### On-Chain Verification

```typescript
// Frontend integration example
const { proof, ownerName, landId, landPortion, account } = proofData;

const tx = await verifierContract.verify(
  proof,
  ownerName,
  landId, 
  landPortion,
  account
);

await tx.wait();
console.log('Land ownership NFT minted!');
```

### Querying Land Records

```solidity
// Get land record by token ID
GreenWebVerifier.LandOwnership memory record = verifier.getLandRecord(tokenId);

// Get land record by land ID
GreenWebVerifier.LandOwnership memory record = verifier.getLandRecordByLandId("LAND-PARCEL-001");
```

## 🧪 Testing

### Run Tests
```bash
# Standard tests
bun run test

# Verbose output
bun run test:verbose

# With gas reporting
bun run test:gas

# Coverage report
bun run test:coverage
```

### Direct Foundry Commands
```bash
cd packages/foundry

# Basic testing
forge test -vv

# Test specific contract
forge test --match-contract GreenWebProofTest -vv

# Test with gas report
forge test --gas-report

# Generate coverage
forge coverage
```

### Test Land Ownership Proof Generation
```bash
cd packages/foundry/vlayer
bun run prove:land
```

## 🔐 Security Considerations

### Trust Assumptions
- **TLS Notary**: Currently relies on vlayer's notary service for TLS validation
- **Government APIs**: Assumes target government APIs are authentic and secure
- **ZK Proving**: Uses RISC Zero zkEVM for proof generation

### Privacy Features
- **Minimal Disclosure**: Only necessary land ownership data is stored on-chain
- **Data Redaction**: Sensitive information can be redacted before proof generation
- **No Full Web Page Storage**: Complete webpage content never touches the blockchain

### Security Guarantees
- **Authenticity**: Cryptographic proof that data came from specified government domain
- **Integrity**: TLS notarization ensures data wasn't tampered with
- **Non-Repudiation**: ZK proofs provide mathematical certainty of correct extraction

## 🌍 Deployment Networks

### Optimism Sepolia (Primary Testnet)
- **Chain ID**: 11155420
- **RPC**: https://sepolia.optimism.io
- **Explorer**: https://sepolia-optimism.etherscan.io

### Supported Features
- ✅ Web Proof verification
- ✅ ERC721 NFT minting
- ✅ Land ownership tracking
- ✅ Duplicate prevention
- ✅ Event emission for indexing

## 📚 Documentation References

- [vlayer Documentation](https://book.vlayer.xyz/)
- [Web Proofs Guide](https://book.vlayer.xyz/features/web.html)
- [Optimism Sepolia Faucet](https://chainlist.org/chain/11155420)

## 🚧 Future Enhancements

- **Multi-Government Support**: Extend to support multiple land registry APIs
- **Batch Verification**: Allow verification of multiple land parcels in one transaction
- **Land Transfer System**: Enable verified land ownership transfers
- **Oracle Integration**: Combine with price oracles for land valuation
- **Mobile App**: Native mobile application with browser extension functionality

## 🐛 Troubleshooting

### Common Issues

1. **Import Path Errors**: Ensure remappings.txt is correctly configured
2. **vlayer Token**: Verify VLAYER_TOKEN is set and valid
3. **Network Issues**: Confirm you're connected to Optimism Sepolia
4. **Gas Estimation**: Use "pending" block tag for gas estimation on slower networks

### Debug Mode
```bash
# Enable verbose logging
cd packages/foundry/vlayer
bun run prove:land:debug
```

### Quick Commands Reference
```bash
# Full development workflow
cd packages/foundry/vlayer
bun run setup && bun run dev

# Deploy and verify on Optimism Sepolia
export PRIVATE_KEY=your_key ETHERSCAN_API_KEY=your_key
bun run deploy:sepolia

# Test everything
bun run test:verbose && bun run prove:land
```

## 📄 License

MIT License - see LICENSE file for details.

---

**Note**: This implementation uses mock government API endpoints for demonstration. In production, replace with actual government land registry APIs and ensure compliance with local regulations. 