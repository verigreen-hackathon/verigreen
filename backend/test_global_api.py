#!/usr/bin/env python3
"""
Test script for the new Global Forest Monitoring API endpoint
"""

import requests
import json
import sys
import time


def test_global_forest_api():
    """Test the /forest/analyze endpoint with sample data"""
    
    # API endpoint
    base_url = "http://localhost:8000"
    endpoint = f"{base_url}/forest/analyze"
    
    # Test data - Amazon rainforest area in Brazil
    test_request = {
        "bounding_box": [-60.0, -3.0, -59.5, -2.5],  # Small area in Amazon
        "wallet_address": "0x742d35cc6600c2a773ad2b6c8c4b2df2c4b2a6e1"
    }
    
    print("🌍 Testing Global Forest Monitoring API")
    print(f"📍 Endpoint: {endpoint}")
    print(f"📦 Request data: {json.dumps(test_request, indent=2)}")
    print("\n" + "="*50)
    
    try:
        # Make the API request
        print("⏳ Sending request...")
        start_time = time.time()
        
        response = requests.post(
            endpoint,
            json=test_request,
            headers={"Content-Type": "application/json"}
        )
        
        request_time = time.time() - start_time
        print(f"⏱️ Request completed in {request_time:.3f} seconds")
        
        # Check response status
        if response.status_code == 200:
            print("✅ API request successful!")
            
            # Parse response
            data = response.json()
            
            # Display key response information
            print(f"\n📊 Analysis Results:")
            print(f"   🆔 Analysis ID: {data['analysis_id']}")
            print(f"   📊 Status: {data['status']}")
            print(f"   🌲 Forest tiles: {len(data['forest_grid'])}")
            print(f"   ⏱️ Processing time: {data['processing_time']} seconds")
            print(f"   💰 Wallet: {data['wallet_address']}")
            print(f"   📍 Bounding box: {data['bounding_box']}")
            
            # Show sample tiles
            print(f"\n🔍 Sample forest tiles:")
            for i, tile in enumerate(data['forest_grid'][:5]):  # Show first 5 tiles
                print(f"   Tile {i+1}: {tile['tile_id']} | Health: {tile['health_score']} | NDVI: {tile['ndvi']} | Coords: {tile['coordinates']}")
            
            if len(data['forest_grid']) > 5:
                print(f"   ... and {len(data['forest_grid']) - 5} more tiles")
            
            print(f"\n🎯 Test completed successfully!")
            return True
            
        else:
            print(f"❌ API request failed with status {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - make sure the FastAPI server is running on localhost:8000")
        print("💡 Start the server with: cd backend/src && python app.py")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        return False


def test_validation():
    """Test input validation with invalid data"""
    
    base_url = "http://localhost:8000"
    endpoint = f"{base_url}/forest/analyze"
    
    print("\n🧪 Testing input validation...")
    
    # Test cases with invalid data
    test_cases = [
        {
            "name": "Invalid longitude range",
            "data": {
                "bounding_box": [-200.0, -3.0, -59.5, -2.5],  # Invalid west longitude
                "wallet_address": "0x742d35cc6600c2a773ad2b6c8c4b2df2c4b2a6e1"
            }
        },
        {
            "name": "Invalid wallet address",
            "data": {
                "bounding_box": [-60.0, -3.0, -59.5, -2.5],
                "wallet_address": "invalid_wallet"  # Invalid format
            }
        },
        {
            "name": "Bounding box too large",
            "data": {
                "bounding_box": [-70.0, -10.0, -50.0, 10.0],  # 20x20 degree box
                "wallet_address": "0x742d35cc6600c2a773ad2b6c8c4b2df2c4b2a6e1"
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📝 Testing: {test_case['name']}")
        try:
            response = requests.post(endpoint, json=test_case['data'])
            if response.status_code == 422:
                print("✅ Validation correctly rejected invalid input")
            else:
                print(f"⚠️ Unexpected response: {response.status_code}")
        except Exception as e:
            print(f"❌ Test error: {str(e)}")


if __name__ == "__main__":
    print("🚀 Global Forest Monitoring API Test Suite")
    print("="*60)
    
    # Run main functionality test
    success = test_global_forest_api()
    
    if success:
        # Run validation tests
        test_validation()
    
    print("\n" + "="*60)
    print("🏁 Test suite completed!") 