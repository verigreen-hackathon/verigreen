#!/usr/bin/env python3
"""
Test script for the GlobalGridCalculator to ensure it works correctly
"""

import sys
import os

# Add the src directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sentinel.grid import GlobalGridCalculator, GridError


def test_global_grid_calculator():
    """Test the GlobalGridCalculator functionality"""
    
    print("🧪 Testing GlobalGridCalculator")
    print("=" * 50)
    
    # Initialize calculator
    calculator = GlobalGridCalculator()
    print(f"✅ Initialized calculator: {calculator.grid_size}x{calculator.grid_size} grid")
    
    # Test bounding box - Amazon rainforest area
    bounding_box = [-60.0, -3.0, -59.5, -2.5]
    print(f"📍 Testing bounding box: {bounding_box}")
    
    # Test coordinate validation
    is_valid, message = calculator.validate_global_coordinates(bounding_box)
    print(f"✅ Coordinate validation: {is_valid} - {message}")
    
    if not is_valid:
        print("❌ Invalid coordinates, stopping test")
        return False
    
    # Test grid calculation
    try:
        tiles = calculator.calculate_global_grid(bounding_box)
        print(f"✅ Generated {len(tiles)} tiles")
        
        # Show sample tiles
        print("\n🔍 Sample tiles:")
        for i, tile in enumerate(tiles[:5]):
            print(f"   {i+1}. {tile.tile_id}: Grid({tile.grid_x},{tile.grid_y}) -> {tile.center_lat_lon}")
        
        if len(tiles) > 5:
            print(f"   ... and {len(tiles) - 5} more tiles")
        
    except GridError as e:
        print(f"❌ Grid calculation failed: {e}")
        return False
    
    # Test area calculation
    try:
        area_stats = calculator.calculate_grid_area_km2(bounding_box)
        print(f"\n📊 Area statistics:")
        print(f"   Total area: {area_stats['total_area_km2']} km²")
        print(f"   Tile area: {area_stats['tile_area_km2']} km²")
        print(f"   Grid dimensions: {area_stats['grid_dimensions_km']['width']}x{area_stats['grid_dimensions_km']['height']} km")
        
    except Exception as e:
        print(f"❌ Area calculation failed: {e}")
        return False
    
    # Test MGRS tile estimation
    try:
        mgrs_tiles = calculator.get_sentinel_mgrs_tiles(bounding_box)
        print(f"\n🛰️ Estimated MGRS tiles: {mgrs_tiles}")
        
    except Exception as e:
        print(f"❌ MGRS tile estimation failed: {e}")
        return False
    
    print("\n🎯 All tests passed!")
    return True


def test_invalid_coordinates():
    """Test error handling with invalid coordinates"""
    
    print("\n🧪 Testing invalid coordinates")
    print("=" * 50)
    
    calculator = GlobalGridCalculator()
    
    test_cases = [
        ([-200, -3, -59.5, -2.5], "Invalid longitude"),
        ([-60, -3, -60, -2.5], "West >= East"),
        ([-60, -3, -59.5, -3], "South >= North"),
        ([-70, -10, -50, 10], "Bounding box too large"),
    ]
    
    for coords, expected_error in test_cases:
        is_valid, message = calculator.validate_global_coordinates(coords)
        if not is_valid:
            print(f"✅ Correctly rejected {expected_error}: {message}")
        else:
            print(f"❌ Should have rejected {expected_error} but didn't")
    
    print("✅ Error handling tests completed")


if __name__ == "__main__":
    print("🚀 GlobalGridCalculator Test Suite")
    print("=" * 60)
    
    # Run main tests
    success = test_global_grid_calculator()
    
    if success:
        # Run error handling tests
        test_invalid_coordinates()
    
    print("\n" + "=" * 60)
    print("🏁 Test suite completed!") 