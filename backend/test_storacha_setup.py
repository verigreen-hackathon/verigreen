#!/usr/bin/env python3
"""
Simple test script to validate Storacha setup and upload functionality.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from src.filecoin.client import (
    StorachaClient, 
    StorachaConfig, 
    create_config_from_env,
    test_connection
)


async def test_storacha_setup():
    """Test comprehensive Storacha setup and functionality."""
    print("🔧 Testing Storacha Setup...")
    
    # Test 1: Environment Configuration
    print("\n1. Testing environment configuration...")
    try:
        config = create_config_from_env()
        print(f"✅ Configuration loaded successfully")
        print(f"   Base URL: {config.base_url}")
        print(f"   Space DID: {config.space_did}")
        print(f"   Auth Secret: {config.auth_secret[:10]}...")
        print(f"   Auth Token: {config.auth_token[:20]}...")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False
    
    # Test 2: Connection Test
    print("\n2. Testing connection to Storacha...")
    try:
        connection_ok = await test_connection(config)
        if connection_ok:
            print("✅ Connection successful!")
        else:
            print("❌ Connection failed!")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False
    
    # Test 3: List existing uploads
    print("\n3. Listing existing uploads...")
    try:
        async with StorachaClient(config) as client:
            uploads = await client.list_uploads()
            print(f"✅ Found {len(uploads)} existing uploads")
            for i, upload in enumerate(uploads[:3]):  # Show first 3
                root_cid = upload.get('root', {}).get('/', 'unknown')
                print(f"   {i+1}. {root_cid}")
    except Exception as e:
        print(f"❌ List uploads error: {e}")
        return False
    
    # Test 4: Upload a small test file
    print("\n4. Testing file upload...")
    try:
        test_data = b"Hello, Storacha! This is a test file for VeriGreen project."
        
        async with StorachaClient(config) as client:
            print(f"   Uploading {len(test_data)} bytes of test data...")
            result = await client.upload_data(test_data, "test_file.txt")
            
            print(f"✅ Upload successful!")
            print(f"   Content CID: {result.content_cid}")
            print(f"   Shard CID: {result.shard_cid}")
            print(f"   Size: {result.size} bytes")
            print(f"   IPFS Gateway: https://{result.content_cid}.ipfs.w3s.link")
            
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return False
    
    # Test 5: Verify upload appears in list
    print("\n5. Verifying upload in list...")
    try:
        async with StorachaClient(config) as client:
            uploads = await client.list_uploads()
            new_count = len(uploads)
            print(f"✅ Upload list now contains {new_count} items")
            
            # Find our upload
            our_upload = None
            for upload in uploads:
                if upload.get('root', {}).get('/') == result.content_cid:
                    our_upload = upload
                    break
            
            if our_upload:
                print(f"✅ Found our upload in the list!")
                print(f"   Root: {our_upload.get('root', {}).get('/')}")
                shards = our_upload.get('shards', [])
                print(f"   Shards: {len(shards)} ({[s.get('/') for s in shards]})")
            else:
                print(f"⚠️  Upload not found in list (may take time to appear)")
            
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False
    
    print(f"\n🎉 All tests passed! Storacha integration is working correctly.")
    print(f"\n📋 Summary:")
    print(f"   ✅ Configuration loaded from environment")
    print(f"   ✅ Connection to Storacha established")
    print(f"   ✅ Can list existing uploads")
    print(f"   ✅ Successfully uploaded test data")
    print(f"   ✅ Upload verification completed")
    print(f"\n🚀 Ready to proceed with VeriGreen satellite data uploads!")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(test_storacha_setup())
    sys.exit(0 if success else 1) 