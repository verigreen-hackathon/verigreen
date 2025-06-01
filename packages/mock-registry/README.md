# 🧪 VeriGreen Mock Registry

The **Mock Registry** is a local development and simulation tool used to emulate external registry services during VeriGreen testing.

It allows developers to:

- Simulate registry lookups
- Mock contract data responses
- Run full-stack integration flows without relying on live infrastructure

This is useful for local development, automated testing, and frontend/backend interface validation.

---

## 🖥 Scripts

The following scripts are available:

- `dev` – Runs the app in development mode on port 3003
- `build` – Compiles the Next.js application for production
- `start` – Runs the production build on port 3003
- `lint` – Runs the linter on the codebase

---

## 🧱 Tech Stack

- **Next.js** – React framework for frontend and API routes
- **TypeScript** – For static typing and developer tooling
- **Mock APIs** – Used to replicate behaviors of real registries

---

## 🌐 Usage Context

This package is **not intended for production**. It should only be used in:

- Local development environments
- Testing pipelines
- Staging simulations

---

## 🧩 Integration

The Mock Registry connects with other VeriGreen components such as:

- The web app (to simulate verification flows)
- The backend (for API mocking)
- Smart contract testing (mocking registry calls if needed)

This helps decouple frontend/backend development from live chain dependencies and third-party APIs.

---

If you need a real registry or are deploying to production, this package should be replaced with the actual service integration.
