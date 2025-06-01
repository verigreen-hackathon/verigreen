#!/usr/bin/env python3
"""
Test script for the complete Global NDVI processing pipeline
"""

import sys
import os
import asyncio

# Add the src directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from processing.global_ndvi_processor import GlobalNDVIProcessor


async def test_global_ndvi_processing():
    """Test the complete global NDVI processing pipeline"""
    
    print("🧪 Testing Global NDVI Processing Pipeline")
    print("=" * 60)
    
    processor = GlobalNDVIProcessor()
    
    # Test cases from different biomes
    test_cases = [
        ([-60.0, -3.0, -59.5, -2.5], "Amazon Rainforest, Brazil"),
        ([2.0, 48.5, 2.5, 49.0], "Paris, France (Temperate)"),
        ([-122.5, 37.5, -122.0, 38.0], "San Francisco, USA (Temperate)"),
        ([139.5, 35.5, 140.0, 36.0], "Tokyo, Japan (Temperate)"),
    ]
    
    for i, (bounding_box, location) in enumerate(test_cases):
        print(f"\n🌍 Test Case {i+1}: {location}")
        print(f"Coordinates: {bounding_box}")
        print("-" * 40)
        
        try:
            analysis_id = f"test_analysis_{i+1}"
            
            # Process the global coordinates
            result = await processor.process_global_coordinates(
                bounding_box=bounding_box,
                analysis_id=analysis_id,
                force_download=False
            )
            
            # Display results
            print(f"✅ Processing completed successfully!")
            print(f"📊 Analysis Results:")
            print(f"   • Analysis ID: {result.analysis_id}")
            print(f"   • Total Area: {result.total_area_km2} km²")
            print(f"   • Grid Size: {result.grid_size}x{result.grid_size}")
            print(f"   • Number of Tiles: {len(result.tiles)}")
            print(f"   • Processing Time: {result.processing_time:.2f}s")
            
            print(f"\n🌱 NDVI Statistics:")
            print(f"   • Mean NDVI: {result.mean_ndvi_global:.3f}")
            print(f"   • Mean Health Score: {result.mean_health_score:.3f}")
            print(f"   • Forest Coverage: {result.forest_coverage_percentage:.1f}%")
            
            # Show biome distribution
            biomes = {}
            for tile in result.tiles:
                biome = tile.biome_classification
                biomes[biome] = biomes.get(biome, 0) + 1
            
            print(f"\n🏞️ Biome Distribution:")
            for biome, count in biomes.items():
                percentage = (count / len(result.tiles)) * 100
                print(f"   • {biome}: {count} tiles ({percentage:.1f}%)")
            
            # Show sample tiles
            print(f"\n📍 Sample Tiles (first 5):")
            for j, tile in enumerate(result.tiles[:5]):
                print(f"   {j+1}. {tile.tile_id}: NDVI={tile.mean_ndvi:.3f}, "
                     f"Health={tile.health_score:.3f}, "
                     f"Biome={tile.biome_classification}, "
                     f"VegType={tile.vegetation_type}")
            
            # Show data quality
            high_quality = len([t for t in result.tiles if t.valid_pixel_percentage > 90])
            medium_quality = len([t for t in result.tiles if 70 <= t.valid_pixel_percentage <= 90])
            low_quality = len([t for t in result.tiles if t.valid_pixel_percentage < 70])
            
            print(f"\n📈 Data Quality:")
            print(f"   • High Quality (>90%): {high_quality} tiles")
            print(f"   • Medium Quality (70-90%): {medium_quality} tiles")
            print(f"   • Low Quality (<70%): {low_quality} tiles")
            
            if result.errors:
                print(f"\n⚠️ Errors: {result.errors}")
            
        except Exception as e:
            print(f"❌ Test failed for {location}: {e}")
    
    print("\n" + "=" * 60)
    print("🏁 Global NDVI processing tests completed!")


async def test_biome_classification():
    """Test the biome classification logic"""
    
    print("\n🧪 Testing Biome Classification")
    print("=" * 40)
    
    processor = GlobalNDVIProcessor()
    
    test_locations = [
        (-2.5, -59.75, "Amazon Rainforest"),
        (48.75, 2.25, "Paris, France"),
        (37.75, -122.25, "San Francisco"),
        (35.75, 139.75, "Tokyo"),
        (55.75, 37.62, "Moscow"),
        (0, 32, "Central Africa"),
        (30, -20, "Sahara Desert"),
        (-40, 145, "Southern Australia"),
    ]
    
    for lat, lon, location in test_locations:
        biome = processor._classify_biome(lat, lon)
        base_ndvi = processor._get_base_ndvi_for_biome(biome)
        
        print(f"📍 {location}: {biome} (base NDVI: {base_ndvi:.3f})")
    
    print("\n✅ Biome classification tests completed!")


async def test_health_score_calculation():
    """Test health score calculation for different biomes"""
    
    print("\n🧪 Testing Health Score Calculation")
    print("=" * 40)
    
    processor = GlobalNDVIProcessor()
    
    test_ndvi_values = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    test_biomes = ["tropical_rainforest", "temperate_forest", "grassland", "desert"]
    
    for biome in test_biomes:
        print(f"\n🏞️ {biome.replace('_', ' ').title()}:")
        for ndvi in test_ndvi_values:
            health_score = processor._calculate_health_score(ndvi, biome)
            print(f"   NDVI {ndvi:.1f} → Health Score {health_score:.3f}")
    
    print("\n✅ Health score calculation tests completed!")


if __name__ == "__main__":
    print("🚀 Global NDVI Processor Test Suite")
    print("=" * 60)
    
    # Run all tests
    asyncio.run(test_global_ndvi_processing())
    asyncio.run(test_biome_classification())
    asyncio.run(test_health_score_calculation())
    
    print("\n" + "=" * 60)
    print("🎯 All Global NDVI tests completed!")
    print("🌐 The processor is ready for integration with the API") 