# 🔧 VeriGreen Backend

This is the **backend service** for the VeriGreen platform. It is responsible for:

- Exposing APIs for the web app
- Authenticating users (via wallet)
- Interacting with smart contracts (Verifier, Entropy, Registry)
- Accessing and managing database records
- Communicating with the Verifier backend
- Triggering rewards and managing verification outcomes

---

## 🌍 Environment Variables

Create a `.env` file with the following variables:

- `DATABASE_URL` – PostgreSQL database connection string
- `ENTROPY_ADDRESS` – On-chain address for the entropy/randomness contract
- `VERI_GREEN_ADDRESS` – Smart contract address for the VeriGreen registry
- `PRIVATE_KEY` – Signer private key for backend-initiated transactions
- `VERIFIER_URL` – URL of the off-chain verifier service

---

## 🧪 Development Workflow

1. Install dependencies from the root of the monorepo using Yarn.
2. To run the server in development mode, use the `dev` script.
3. To continuously compile TypeScript while developing, use the `watch` script.
4. For production, build the codebase and start the server using `build` followed by `start`.

---

## 🔨 Available Scripts

- `start` — Runs the compiled backend server from `dist/index.js`
- `dev` — Runs the backend in development mode using `ts-node`
- `build` — Compiles TypeScript into the `dist/` directory
- `watch` — Watches files and recompiles on changes

---

## 🐳 Docker Usage

The backend includes a `Dockerfile`.

To containerize the backend:

1. Build the image using your preferred Docker tool.
2. Provide your `.env` file to the container as environment input.
3. Map the container port to your host (default is 3000, if not changed in the code).
   This enables reproducible builds and deploys in cloud or local environments.

---

## 🧱 Tech Stack

- **TypeScript**
- **Express.js**
- **Ethers.js**
- **MongoDB**
- **Sattelite data integration** (via external verifier)
- **Docker** for deployment and isolation

---

Let us know if you'd like to contribute, raise issues, or extend the backend functionality.
