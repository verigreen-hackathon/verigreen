# Mock Government Land Registry Portal

A Next.js-based mock government land registry portal that provides secure access to land ownership records and property information.

## Features

- **User Authentication**: Secure login system with demo credentials
- **Land Records API**: RESTful API for accessing property ownership data
- **Government Portal UI**: Professional government-style interface
- **Property Search**: Search by property ID, owner ID, or owner name
- **Secure Access**: Authentication-protected land record access

## Getting Started

### Installation

```bash
npm install
# or
yarn install
# or  
pnpm install
```

### Development

Run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
```

Open [http://localhost:3003](http://localhost:3003) with your browser to see the portal.

### Demo Credentials

The portal includes demo accounts for testing:

- **Alice Johnson**: `alice.johnson@email.com` / `password123`
- **Bob Smith**: `bob.smith@email.com` / `password123`  
- **Demo User**: `demo@example.com` / `demo`

## API Endpoints

### Authentication

- `POST /api/login` - User authentication
  ```json
  {
    "email": "alice.johnson@email.com",
    "password": "password123"
  }
  ```

### Land Records

- `GET /api/ownership/verify` - Get land ownership records
  - Query parameters:
    - `property_id`: Search by property ID
    - `owner_id`: Search by owner government ID
    - `owner_name`: Search by owner name
  - Requires authentication (Bearer token or session cookie)

## Project Structure

```
src/
├── app/
│   ├── page.tsx           # Main portal homepage
│   ├── login/
│   │   └── page.tsx       # Login page
│   ├── api/
│   │   ├── login/
│   │   │   └── route.ts   # Authentication API
│   │   └── ownership/
│   │       └── verify/
│   │           └── route.ts # Land records API
│   ├── layout.tsx         # Main layout with header/footer
│   └── globals.css        # Global styles
```

## Data Structure

The portal maintains mock land records with the following structure:

- **Owner Information**: Name, ID, email, phone
- **Property Details**: ID, size, location, type, coordinates, zoning
- **Verification Status**: Status, timestamp, verifier details
- **Legal Information**: Deed number, title type, encumbrances, liens
- **Government Seal**: Authority verification and digital signatures

## Security Features

- Session-based authentication
- Authorization headers support
- Government-grade data formatting
- CORS protection
- Request tracking and logging

## Deployment

### Build for Production

```bash
npm run build
npm start
```

### Environment Configuration

The application runs on port 3003 by default. This can be configured in the npm scripts in `package.json`.

## Use Cases

This mock registry is perfect for:

- Testing integrations with government land registry APIs
- Demonstrating property verification workflows  
- Building prototypes for land ownership applications
- Educational purposes for understanding government data structures

## Contributing

This is a mock service designed for development and testing purposes. The data is entirely fictional and should not be used for any real property transactions or legal purposes.
