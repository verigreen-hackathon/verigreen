#!/usr/bin/env python3
"""
VeriGreen Global Forest Monitoring API Demo Script
Demonstrates worldwide forest health analysis capabilities
"""

import requests
import json
import time

API_BASE = "http://localhost:8000"
WALLET = "0x742d35Cc6634C0532925a3b8D364B4a456fA4D42"

def analyze_location(name, bounding_box):
    """Analyze forest health for a specific location"""
    print(f"\n🌍 Analyzing {name}...")
    print(f"Coordinates: {bounding_box}")
    
    payload = {
        "bounding_box": bounding_box,
        "wallet_address": WALLET
    }
    
    start_time = time.time()
    response = requests.post(f"{API_BASE}/forest/analyze", json=payload)
    end_time = time.time()
    
    if response.status_code == 200:
        data = response.json()
        
        # Extract key metrics from simplified response
        processing_time = data["processing_time"]
        forest_grid = data["forest_grid"]
        
        # Calculate metrics from grid data
        total_tiles = len(forest_grid)
        avg_ndvi = sum(tile["ndvi"] for tile in forest_grid) / total_tiles
        avg_health = sum(tile["health_score"] for tile in forest_grid) / total_tiles
        forest_tiles = sum(1 for tile in forest_grid if tile["ndvi"] > 0.4)
        forest_coverage = (forest_tiles / total_tiles) * 100
        
        print(f"✅ Success! ({end_time - start_time:.1f}s total)")
        print(f"📊 Processing Time: {processing_time}")
        print(f"🌱 Mean NDVI: {avg_ndvi:.3f}")
        print(f"💚 Health Score: {avg_health:.3f}")
        print(f"🌲 Forest Coverage: {forest_coverage:.1f}%")
        print(f"🔗 Filecoin CID: {data['filecoin_cid']}")
        
        # Show sample tiles
        print(f"🎯 Sample Tiles:")
        for i, tile in enumerate(forest_grid[:3]):
            print(f"   Tile {tile['tile_id']}: Grid({tile['x']},{tile['y']}) "
                 f"NDVI {tile['ndvi']:.3f}, Health {tile['health_score']:.3f}")
        
        return data
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None

def main():
    """Run the complete demo"""
    print("🌟 VeriGreen Global Forest Monitoring API Demo")
    print("=" * 60)
    
    # Demo locations showcasing different biomes
    locations = [
        ("Amazon Rainforest, Brazil", [-60.0, -3.0, -59.5, -2.5]),
        ("Paris Region, France", [2.0, 48.5, 2.5, 49.0]),
        ("San Francisco Bay, USA", [-122.5, 37.5, -122.0, 38.0]),
        ("Tokyo Region, Japan", [139.5, 35.5, 140.0, 36.0]),
        ("Sahara Desert, Algeria", [2.0, 25.0, 2.5, 25.5]),
    ]
    
    results = []
    total_start = time.time()
    
    for name, coords in locations:
        result = analyze_location(name, coords)
        if result:
            results.append((name, result))
        time.sleep(1)  # Brief pause between requests
    
    total_time = time.time() - total_start
    
    print(f"\n" + "=" * 60)
    print(f"🏆 Demo Complete! Total time: {total_time:.1f}s")
    print(f"📈 Analyzed {len(results)} locations across {len(results)} biomes")
    print(f"🌍 Demonstrated global coverage from rainforest to desert")
    
    # Calculate average processing time from string format (e.g., "1.23s")
    avg_processing = sum(float(r[1]['processing_time'].rstrip('s')) for r in results) / len(results)
    print(f"⚡ Average processing: {avg_processing:.2f}s")
    
    # Summary comparison
    print(f"\n📊 Location Comparison:")
    for name, result in results:
        forest_grid = result["forest_grid"]
        avg_ndvi = sum(tile["ndvi"] for tile in forest_grid) / len(forest_grid)
        avg_health = sum(tile["health_score"] for tile in forest_grid) / len(forest_grid)
        forest_tiles = sum(1 for tile in forest_grid if tile["ndvi"] > 0.4)
        coverage = (forest_tiles / len(forest_grid)) * 100
        print(f"   {name}: NDVI {avg_ndvi:.3f}, Health {avg_health:.3f}, {coverage:.0f}% forest")

if __name__ == "__main__":
    main() 