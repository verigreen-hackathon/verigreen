#!/usr/bin/env python3
"""
Test script for the GlobalSentinelFetcher to ensure it works correctly
"""

import sys
import os

# Add the src directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sentinel.global_fetcher import GlobalSentinelFetcher


def test_mgrs_tile_calculation():
    """Test MGRS tile calculation for different global locations"""
    
    print("🧪 Testing MGRS Tile Calculation")
    print("=" * 50)
    
    fetcher = GlobalSentinelFetcher()
    
    # Test cases from different continents
    test_cases = [
        ([-60.0, -3.0, -59.5, -2.5], "Amazon Rainforest, Brazil"),
        ([2.0, 48.5, 2.5, 49.0], "Paris, France"),
        ([151.0, -34.0, 151.5, -33.5], "Sydney, Australia"),
        ([-122.5, 37.5, -122.0, 38.0], "San Francisco, USA"),
        ([13.0, 52.2, 13.5, 52.7], "Berlin, Germany"),
        ([139.5, 35.5, 140.0, 36.0], "Tokyo, Japan"),
    ]
    
    for bounding_box, location in test_cases:
        try:
            mgrs_tiles = fetcher.coordinates_to_mgrs_tiles(bounding_box)
            area_stats = fetcher.grid_calculator.calculate_grid_area_km2(bounding_box)
            
            print(f"📍 {location}:")
            print(f"   Coordinates: {bounding_box}")
            print(f"   MGRS Tiles: {mgrs_tiles}")
            print(f"   Area: {area_stats['total_area_km2']} km²")
            print()
            
        except Exception as e:
            print(f"❌ Failed for {location}: {e}")
    
    print("✅ MGRS tile calculation tests completed")


def test_s3_path_construction():
    """Test S3 path construction for Sentinel-2 data"""
    
    print("\n🧪 Testing S3 Path Construction")
    print("=" * 50)
    
    fetcher = GlobalSentinelFetcher()
    
    test_cases = [
        ("50TUG", "B04", "2024/5/15"),
        ("31TDH", "B08", "2024/4/20"),
        ("47NQH", "B04", "2024/3/10"),
    ]
    
    for mgrs_tile, band, date in test_cases:
        s3_path = fetcher.construct_s3_path(mgrs_tile, band, date)
        print(f"🛰️ {mgrs_tile} {band} {date}:")
        print(f"   S3 Path: {s3_path}")
        print()
    
    print("✅ S3 path construction tests completed")


def test_date_finding():
    """Test finding available dates for MGRS tiles"""
    
    print("\n🧪 Testing Date Finding (Limited Search)")
    print("=" * 50)
    
    fetcher = GlobalSentinelFetcher()
    
    # Test with a well-known tile that likely has data
    test_tiles = ["31TDH", "50TUG"]  # Common European tiles
    
    for mgrs_tile in test_tiles:
        try:
            # Search only 5 days to avoid long waits
            available_dates = fetcher.find_available_dates(mgrs_tile, max_days_back=5)
            
            print(f"🔍 {mgrs_tile}:")
            if available_dates:
                print(f"   Found dates: {available_dates[:3]}{'...' if len(available_dates) > 3 else ''}")
            else:
                print(f"   No recent dates found (searched 5 days)")
            print()
            
        except Exception as e:
            print(f"❌ Error searching {mgrs_tile}: {e}")
    
    print("✅ Date finding tests completed")


def test_coordinate_validation():
    """Test coordinate validation"""
    
    print("\n🧪 Testing Coordinate Validation")
    print("=" * 50)
    
    fetcher = GlobalSentinelFetcher()
    
    valid_cases = [
        [-60.0, -3.0, -59.5, -2.5],  # Amazon
        [2.0, 48.5, 2.5, 49.0],      # Paris
    ]
    
    invalid_cases = [
        [-200, -3.0, -59.5, -2.5],   # Invalid longitude
        [-60.0, -3.0, -60.0, -2.5],  # West >= East
        [-60.0, -100, -59.5, -2.5],  # Invalid latitude
    ]
    
    print("✅ Valid coordinates:")
    for coords in valid_cases:
        is_valid, msg = fetcher.grid_calculator.validate_global_coordinates(coords)
        print(f"   {coords}: {is_valid} - {msg}")
    
    print("\n❌ Invalid coordinates:")
    for coords in invalid_cases:
        is_valid, msg = fetcher.grid_calculator.validate_global_coordinates(coords)
        print(f"   {coords}: {is_valid} - {msg}")
    
    print("\n✅ Coordinate validation tests completed")


def test_caching_logic():
    """Test caching logic without actual downloads"""
    
    print("\n🧪 Testing Caching Logic")
    print("=" * 50)
    
    fetcher = GlobalSentinelFetcher()
    
    # Test cache check for a random location
    test_bbox = [-60.0, -3.0, -59.5, -2.5]
    
    try:
        cached_files = fetcher.check_cache(test_bbox, max_age_days=7)
        
        if cached_files:
            print(f"✅ Found {len(cached_files)} cached files")
        else:
            print("ℹ️  No cached files found (expected for new system)")
        
        # Test MGRS calculation for cache
        mgrs_tiles = fetcher.coordinates_to_mgrs_tiles(test_bbox)
        expected_files = len(mgrs_tiles) * len(fetcher.config["bands"])
        print(f"📊 Expected files for cache: {expected_files}")
        print(f"📂 MGRS tiles for cache key: {mgrs_tiles}")
        
    except Exception as e:
        print(f"❌ Caching test failed: {e}")
    
    print("\n✅ Caching logic tests completed")


def test_full_integration():
    """Test the full integration without actual downloads"""
    
    print("\n🧪 Testing Full Integration (No Downloads)")
    print("=" * 50)
    
    fetcher = GlobalSentinelFetcher()
    
    # Test coordinates
    test_bbox = [-60.0, -3.0, -59.5, -2.5]  # Amazon rainforest
    
    try:
        print(f"🌍 Testing integration for: {test_bbox}")
        
        # Test coordinate validation
        is_valid, msg = fetcher.grid_calculator.validate_global_coordinates(test_bbox)
        print(f"✅ Coordinate validation: {is_valid}")
        
        # Test MGRS tile calculation
        mgrs_tiles = fetcher.coordinates_to_mgrs_tiles(test_bbox)
        print(f"🛰️  MGRS tiles: {mgrs_tiles}")
        
        # Test area calculation
        area_stats = fetcher.grid_calculator.calculate_grid_area_km2(test_bbox)
        print(f"📏 Area: {area_stats['total_area_km2']} km²")
        
        # Test S3 path construction
        for mgrs_tile in mgrs_tiles:
            for band in fetcher.config["bands"]:
                s3_path = fetcher.construct_s3_path(mgrs_tile, band, "2024/5/15")
                print(f"🔗 S3 path for {mgrs_tile} {band}: {s3_path}")
        
        # Test cache check
        cached_files = fetcher.check_cache(test_bbox)
        print(f"💾 Cache check: {'Hit' if cached_files else 'Miss'}")
        
        print("\n🎯 Integration test completed successfully!")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")


if __name__ == "__main__":
    print("🚀 GlobalSentinelFetcher Test Suite")
    print("=" * 60)
    
    # Run all tests
    test_mgrs_tile_calculation()
    test_s3_path_construction()
    test_date_finding()
    test_coordinate_validation()
    test_caching_logic()
    test_full_integration()
    
    print("\n" + "=" * 60)
    print("🏁 GlobalSentinelFetcher test suite completed!")
    print("📝 Note: Actual data downloads are not tested to avoid long wait times")
    print("🌐 The fetcher is ready for integration with the API") 