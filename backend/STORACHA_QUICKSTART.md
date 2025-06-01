# Storacha Integration Quick Start Guide

This guide will take you from cloning the VeriGreen repository to successfully testing the Storacha (IPFS) storage integration.

## Prerequisites

- **Python 3.8+** installed
- **Node.js 16+** and npm installed
- Git installed
- Internet connection

## Step 1: Clone and Setup Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/verigreen.git
cd verigreen/backend

# Install Python dependencies
pip install -r requirements.txt
```

## Step 2: Install w3 CLI (Web3.Storage CLI)

The w3 CLI is required to generate proper UCAN authorization tokens for Storacha.

```bash
# Install w3 CLI globally
npm install -g @web3-storage/w3cli

# Verify installation
w3 --version
```

## Step 3: Setup Web3.Storage Account and Space

### 3.1 Login to Web3.Storage

```bash
# Replace 'your-email@example.com' with your actual email
w3 login lonpete@outlook.com
```

You'll receive an email with a verification link. Click it to complete the login.

### 3.2 Create a Space

```bash
# Create a new space for your VeriGreen project
w3 space create
```

When prompted:

- **Space name**: Enter something like "VeriGreen" or "YourProject"
- **Recovery key**: **IMPORTANT** - Save this recovery key somewhere safe! You'll need it if you lose access.

After creation, note down the space DID (starts with `did:key:z6Mk...`).

### 3.3 Verify Space Setup

```bash
# List your spaces to confirm setup
w3 space ls
```

You should see your space listed with an asterisk (\*) indicating it's active.

## Step 4: Generate UCAN Authorization Headers

Run the provided script to generate proper UCAN tokens:

```bash
# Generate UCAN headers for Storacha API
python3 generate_ucan_headers.py
```

This script will:

- ✅ Check your w3 CLI setup
- ✅ Generate UCAN tokens with required capabilities (`store/add`, `upload/add`, `upload/list`)
- ✅ Create/update your `.env` file with the credentials

## Step 5: Test the Connection

Now test that everything is working:

```bash
# Run the comprehensive test suite
python3 test_storacha_setup.py
```

### Expected Output

If successful, you should see:

```
🔧 Testing Storacha Setup...

1. Testing environment configuration...
✅ Configuration loaded successfully
   Base URL: https://up.storacha.network
   Space DID: did:key:z6Mk...
   Auth Secret: uNTRjMGVlY...
   Auth Token: uOqJlcm9vdHOB2CpYJQA...

2. Testing connection to Storacha...
✅ Connection successful!

3. Listing existing uploads...
✅ Found 0 existing uploads

4. Testing file upload...
   Uploading 59 bytes of test data...
✅ Upload successful!
   Content CID: bafybeig...
   Shard CID: bagbaiera5...
   Size: 59 bytes
   IPFS Gateway: https://bafybeig....ipfs.w3s.link

5. Verifying upload in list...
✅ Upload list now contains 1 items
✅ Found our upload in the list!

🎉 All tests passed! Storacha integration is working correctly.
🚀 Ready to proceed with VeriGreen satellite data uploads!
```

## Troubleshooting

### Issue: "w3 CLI not found"

```bash
# Make sure Node.js and npm are installed
node --version
npm --version

# Reinstall w3 CLI
npm install -g @web3-storage/w3cli
```

### Issue: "No w3 spaces found"

```bash
# Make sure you're logged in
w3 login your-email@example.com

# Create a space if you haven't
w3 space create
```

### Issue: "Connection test failed: 401 authorization error"

This usually means UCAN tokens need to be regenerated:

```bash
# Regenerate UCAN tokens
python3 generate_ucan_headers.py

# Test again
python3 test_storacha_setup.py
```

### Issue: "Delegation audience mismatch"

This happens when the space DID and UCAN tokens don't match:

```bash
# Check which space is active
w3 space ls

# If needed, switch to the correct space
w3 space use did:key:z6Mk...

# Regenerate tokens for the active space
python3 generate_ucan_headers.py
```

### Issue: "ipfs-car not found"

The Python client uses the `ipfs-car` CLI tool:

```bash
# Install ipfs-car
npm install -g ipfs-car

# Verify installation
ipfs-car --version
```

## Environment Variables Reference

After successful setup, your `.env` file should contain:

```bash
# Storacha Configuration
STORACHA_SPACE_DID=did:key:z6Mk...                    # Your space DID
STORACHA_BASE_URL=https://up.storacha.network         # Storacha API endpoint
STORACHA_UCAN_SECRET=u...                             # Generated UCAN secret
STORACHA_UCAN_TOKEN=uOqJlcm9vdHO...                   # Generated UCAN token

# Other environment variables...
```

## What's Next?

Once the test passes, your VeriGreen backend can:

- ✅ Upload satellite imagery to IPFS via Storacha
- ✅ Store NDVI analysis data permanently
- ✅ Generate IPFS CIDs for decentralized access
- ✅ List and verify uploaded content

The Storacha integration is now ready for production use in your carbon verification platform!

## Important Notes

1. **UCAN tokens expire** - By default, tokens are valid for 24 hours. Regenerate them using `python3 generate_ucan_headers.py`
2. **Space recovery key** - Keep your space recovery key safe! It's the only way to recover access if you lose your login
3. **Rate limits** - Web3.Storage has usage limits on free accounts. Check their pricing for production use
4. **IPFS propagation** - It may take a few minutes for uploaded content to be available on all IPFS gateways

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Verify all dependencies are installed correctly
3. Ensure your internet connection is stable
4. Check Web3.Storage status at https://status.web3.storage/
