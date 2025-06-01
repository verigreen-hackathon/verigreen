#!/bin/bash

# VeriGreen Backend Setup Test Script
# Tests all major components including Storacha integration

echo "🧪 VeriGreen Backend Setup Test"
echo "================================"

# Check Python dependencies
echo "📦 Checking Python dependencies..."
if ! python3 -c "import aiohttp, aiofiles, certifi" 2>/dev/null; then
    echo "❌ Missing Python dependencies. Run: pip install -r requirements.txt"
    exit 1
fi
echo "✅ Python dependencies OK"

# Check Node.js tools (optional but recommended)
echo "🔧 Checking Node.js tools..."
if command -v w3 &> /dev/null; then
    echo "✅ w3 CLI found: $(w3 --version)"
    W3_AVAILABLE=true
else
    echo "⚠️  w3 CLI not found (needed for Storacha). Install: npm install -g @web3-storage/w3cli"
    W3_AVAILABLE=false
fi

if command -v ipfs-car &> /dev/null; then
    echo "✅ ipfs-car found: $(ipfs-car --version)"
else
    echo "⚠️  ipfs-car not found (needed for Storacha). Install: npm install -g ipfs-car"
fi

# Test environment configuration
echo "⚙️  Checking environment configuration..."
if [ -f ".env" ]; then
    echo "✅ .env file found"
    if grep -q "STORACHA_SPACE_DID" .env; then
        echo "✅ Storacha configuration detected"
        STORACHA_CONFIG=true
    else
        echo "⚠️  Storacha not configured. Run: python3 generate_ucan_headers.py"
        STORACHA_CONFIG=false
    fi
else
    echo "⚠️  .env file not found"
    STORACHA_CONFIG=false
fi

# Test basic imports
echo "🐍 Testing Python imports..."
if python3 -c "from src.filecoin.client import StorachaClient, create_config_from_env" 2>/dev/null; then
    echo "✅ Storacha client imports OK"
else
    echo "❌ Failed to import Storacha client"
    exit 1
fi

# Test Storacha connection if configured
if [ "$STORACHA_CONFIG" = true ] && [ "$W3_AVAILABLE" = true ]; then
    echo "🔗 Testing Storacha connection..."
    if python3 test_storacha_setup.py; then
        echo "🎉 All tests passed! VeriGreen backend is ready!"
    else
        echo "❌ Storacha test failed. Check the troubleshooting guide."
        exit 1
    fi
else
    echo "ℹ️  Skipping Storacha test (not configured or w3 CLI missing)"
    echo "📋 Next steps:"
    echo "   1. Install w3 CLI: npm install -g @web3-storage/w3cli"
    echo "   2. Install ipfs-car: npm install -g ipfs-car"
    echo "   3. Follow the setup guide: STORACHA_QUICKSTART.md"
    echo "   4. Run: python3 test_storacha_setup.py"
fi

echo ""
echo "🚀 Setup check complete!" 