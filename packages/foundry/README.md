# 📜 VeriGreen Contracts

This directory contains the smart contracts that power the VeriGreen protocol. The contracts are written in Solidity and managed using the **Foundry** toolchain for EVM development and testing.

These contracts enable:

- Climate data verification
- Smart reward distribution
- Integration with zero-knowledge proof systems
- Onchain data registries and access control

---

## 🛠 Requirements

To work with this package, you will need the following tools installed on your system:

- Foundry (for compiling, testing, and deploying Solidity contracts)
- Git (to clone and manage dependencies from external repositories)
- A working RPC endpoint (e.g., Optimism Sepolia) to deploy or simulate transactions

---

## 🧱 Directory Structure

- `src/` – Solidity source files
- `out/` – Compiled artifacts generated by Foundry
- `lib/` – External dependencies
- `scripts/` – Scripts to deploy contracts
- `dependencies/` – Auto-managed libraries

---

## ⚙️ Configuration Overview

The `foundry.toml` file defines the project setup:

- The Solidity compiler version is set to `0.8.30`.
- Libraries are imported from both Git and release URLs:
  - OpenZeppelin Contracts `5.0.1`
  - forge-std `1.9.4`
  - risc0-ethereum (ZK-proof library via vLayer)
  - vlayer `1.0.2`
- File system access is granted to the `testdata/` folder for test inputs.
- RPC endpoints include:
  - Optimism Sepolia (`https://sepolia.optimism.io`)

Soldeer-specific options are disabled for automatic remapping generation.

---

## 📦 Node.js Metadata

Although Foundry manages Solidity directly, this package includes a minimal `package.json` for dependency tracking and scripting.

Key details:

- The project uses `@pythnetwork/entropy-sdk-solidity` as a dependency.
- No Node-based test scripts are currently defined.
- The structure allows interoperability with tools that expect an npm-compatible project.

---

## ✅ What to Do Next

1. Write or update smart contracts in the `src/` directory.
2. Add test cases to the `test/` directory using Foundry.
3. Use the RPC endpoint provided to deploy contracts to Optimism Sepolia or another supported chain.
4. Maintain dependency versions in the `foundry.toml` and `package.json` for reproducible builds.

---

This module is core to the VeriGreen protocol and is intended to be used with the full stack including the backend, verifier, and frontend components.
