# VeriGreen🌳

# Monorepo Structure with Yarn Workspaces

VeriGreen uses a **Yarn Workspaces monorepo** to manage the project's components efficiently. The architecture is modular and includes separate workspaces for smart contracts, backend services, the web application, and mock tools for testing.

### 🔧 Workspaces Summary

| Component                | Description                                                                     |
| ------------------------ | ------------------------------------------------------------------------------- |
| **`app`**                | Web frontend interface for users (landowners, agencies, etc.)                   |
| **`backend`**            | Handles API calls, smart contract & data integration, and interaction logic     |
| **`backend (verifier)`** | Specialized backend for NDVI metric analysis, etc.                              |
| **`mock-registry`**      | Simulates external government systems testing (e.g., mock agencies)             |
| **`foundry`**            | Smart contracts written and tested using [Foundry](https://book.getfoundry.sh/) |

### 🧶 Yarn Workspaces

To install dependencies across all workspaces:

```bash
yarn install
```

To run a specific package (e.g., web app):

```bash
yarn workspace app dev
```

To build all packages:

```bash
yarn workspaces run build
```

# Project Description

**VeriGreen** is Onchain Verification for Climate Truth: linking conservation success with modern technology!

Currently, **90% of climate credits have been deemed worthless** for measuring actual impact, since the climate credit system does not fully correlate to the carbon emissions reductions used to assess climate performance. Management systems also vary globally, involving various agencies and governments—resulting in **lack of data transparency** and **bias concerns** in the auditing process.

**VeriGreen** sees the opportunity for a **universal institutional tool** that addresses a key issue: bringing verification data into one place while also solving **access**, **trust**, and **transparency** challenges.

A key environmental metric used by forest management agencies is the **Normalized Difference Vegetation Index (NDVI)**, which assesses the health and density of vegetation using aerial/satellite imagery.

This allows us to utilize **existing satellite imaging data** with **blockchain technology** (decentralized storage, ZK proofs, and random number generators) to **verify**, **track**, and **incentivize** landowners for maintaining environmental preservation practices.  
Landowners earn tokens when they pass verification checks—**let’s use blockchain to create the climate change we wish to see in the world!**

---

# How it's Made

**VeriGreen** leverages existing satellite and blockchain technology to create a **secure**, **trustless**, and **transparent** institutional tool for environmental management agencies and landowners.

## Key Steps of the WebApp UX/UI Flow and Technologies

### 1️⃣ VeriGreen: Data Ingestion & Storage on Filecoin (Protocol Labs)

- Satellite images are downloaded and converted from large raster files to smaller tiles (GeoTIFF or PNG).
- Tiles include embedded metadata:
  - Coordinates
  - Date
  - Source
  - NDVI threshold

---

### 2️⃣ Landowner: Land Identification & Tile Selection (ZK proof from vLayer)

- Landowners log in with their wallet and claim tiles in the VeriGreen web portal.
- This creates a secure identity for each landowner (entity or individual).
- Supports a variety of landowner scales:
  - Individuals (10–100 acres)
  - Co-Ops/NGOs (100–10,000 acres)
  - Corporations (10,000–500,000 acres)

---

### 3️⃣ Agency/Government:

**Verification Request** (via random generator from Pyth Network) &  
**Response** (ZK proof from vLayer)

- A random tile is selected for verification at intervals requested by the institutional user.
- This forms an **unbiased “random sample”** to verify compliance with environmental protocols (e.g., NDVI).
- Tiles show **only the relevant environmental metrics** via ZK proof.

---

### 4️⃣ VeriGreen: Tokenized Rewards for Successful Verification

_(on Optimism, due to vLayer compatibility)_

- If verification is passed:
  - Landowner receives **tokens** and/or **NFT-based agency stamps of approval**.
  - A historical **on-chain log** of each landowner’s conservation adherence is maintained.

---

**VeriGreen** enables efficient verification and incentivizes landowners to uphold environmental standards specified by climate agencies and governments.
