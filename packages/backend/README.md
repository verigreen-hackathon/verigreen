# Smart Contract Interaction Backend

This is a TypeScript-based backend service for interacting with smart contracts and providing REST API endpoints.

## Setup

1. Install dependencies:
```bash
yarn install
```

2. Create a `.env` file in the root directory with the following variables:
```
PORT=3000
RPC_URL=your_rpc_url_here
PRIVATE_KEY=your_private_key_here
CONTRACT_ADDRESS=your_contract_address_here
```

## Development

To run the development server:
```bash
yarn dev
```

## Building

To build the project:
```bash
yarn build
```

To run the production server:
```bash
yarn start
```

## Project Structure

- `src/index.ts` - Main application entry point
- `src/contracts/` - Smart contract interaction code
  - `interfaces.ts` - Contract interfaces and service classes

## API Endpoints

- `GET /health` - Health check endpoint

More endpoints will be added as the project develops. 