#!/usr/bin/env python3
"""
Demonstration of the VeriGreen NDVI Calculation Engine
=====================================================

This script demonstrates how to use the NDVI calculation engine components
for processing satellite imagery and analyzing vegetation health.
"""

import numpy as np
from src.ndvi import BandLoader, NDVICalculator, NDVIStatistics, ThresholdVerifier, VegetationClass

def create_synthetic_sentinel2_data():
    """Create synthetic Sentinel-2 like data for demonstration."""
    print("🛰️  Creating synthetic Sentinel-2 data...")
    
    # Simulate realistic reflectance values
    np.random.seed(123)  # For reproducible demo
    
    # RED band (B04) - typically lower for healthy vegetation
    red_reflectance = np.random.uniform(0.03, 0.12, (50, 50))
    
    # NIR band (B08) - typically higher for healthy vegetation  
    nir_reflectance = np.random.uniform(0.25, 0.65, (50, 50))
    
    # Add some water/urban areas (low NDVI)
    red_reflectance[0:10, 0:10] = np.random.uniform(0.15, 0.25, (10, 10))
    nir_reflectance[0:10, 0:10] = np.random.uniform(0.10, 0.20, (10, 10))
    
    # Add some very dense vegetation (high NDVI)
    red_reflectance[40:50, 40:50] = np.random.uniform(0.02, 0.06, (10, 10))
    nir_reflectance[40:50, 40:50] = np.random.uniform(0.60, 0.85, (10, 10))
    
    print(f"   📊 RED band range: {red_reflectance.min():.4f} - {red_reflectance.max():.4f}")
    print(f"   📊 NIR band range: {nir_reflectance.min():.4f} - {nir_reflectance.max():.4f}")
    
    return red_reflectance, nir_reflectance

def demonstrate_ndvi_calculation():
    """Demonstrate NDVI calculation process."""
    print("\n🌱 NDVI Calculation Engine Demonstration")
    print("=" * 50)
    
    # Step 1: Create synthetic data
    red_data, nir_data = create_synthetic_sentinel2_data()
    
    # Step 2: Create band data objects
    print("\n📡 Creating band data objects...")
    from rasterio.transform import Affine
    import rasterio
    
    transform = Affine(10.0, 0.0, 500000.0, 0.0, -10.0, 6000000.0)  # UTM-like
    crs = rasterio.CRS.from_epsg(32633)  # UTM Zone 33N
    
    from src.ndvi.band_loader import BandData
    red_band = BandData(red_data, transform, crs, None, 1.0, 0.0)
    nir_band = BandData(nir_data, transform, crs, None, 1.0, 0.0)
    
    # Step 3: Calculate NDVI
    print("🔢 Calculating NDVI...")
    calculator = NDVICalculator(default_threshold=0.65)
    ndvi_result = calculator.calculate_ndvi(
        red_band, nir_band, 
        tile_id="DEMO_TILE_001",
        threshold=0.6
    )
    
    print(f"   ✅ Calculation complete for tile: {ndvi_result.tile_id}")
    print(f"   📈 Mean NDVI: {ndvi_result.mean_ndvi:.4f}")
    print(f"   📊 NDVI Range: [{ndvi_result.min_ndvi:.4f}, {ndvi_result.max_ndvi:.4f}]")
    print(f"   🎯 Threshold (≥{ndvi_result.threshold_value}): {'✅ PASSED' if ndvi_result.threshold_passed else '❌ FAILED'}")
    print(f"   🖼️  Valid pixels: {ndvi_result.valid_pixel_count}/{ndvi_result.total_pixel_count} ({ndvi_result.valid_pixel_percentage:.1f}%)")
    
    # Step 4: Calculate detailed statistics
    print("\n📊 Calculating detailed statistics...")
    stats_calc = NDVIStatistics()
    stats = stats_calc.calculate_comprehensive_statistics(
        ndvi_result.ndvi_array,
        threshold=0.6,
        include_spatial=True
    )
    
    print(f"   📏 Standard deviation: {stats.std:.4f}")
    print(f"   📐 Skewness: {stats.skewness:.4f}")
    print(f"   📊 25th percentile: {stats.quartiles['Q1']:.4f}")
    print(f"   📊 75th percentile: {stats.quartiles['Q3']:.4f}")
    print(f"   🌐 Spatial autocorrelation: {stats.spatial_autocorrelation:.4f}")
    print(f"   🔄 Spatial variability: {stats.spatial_variability:.4f}")
    
    # Step 5: Classify vegetation
    print("\n🌿 Classifying vegetation types...")
    verifier = ThresholdVerifier()
    classification = verifier.classify_vegetation(ndvi_result.ndvi_array)
    
    print(f"   🏆 Dominant class: {classification.dominant_class.value}")
    print("   📋 Class distribution:")
    
    for veg_class, percentage in classification.class_percentages.items():
        if percentage > 0:
            pixel_count = classification.class_statistics[veg_class]['pixel_count']
            print(f"      {veg_class.value:20s}: {percentage:6.2f}% ({pixel_count:4d} pixels)")
    
    # Step 6: Generate color map for visualization
    print("\n🎨 Generating color map for visualization...")
    color_map = verifier.create_color_map(classification)
    print("   🌈 Available colors for each class:")
    for class_idx, color in color_map.items():
        if class_idx >= 0:
            class_name = classification.threshold_definitions[class_idx].vegetation_class.value
            print(f"      {class_name:20s}: {color}")
    
    # Step 7: Validate threshold definitions
    print("\n✅ Validating threshold definitions...")
    validation = verifier.validate_thresholds(verifier.default_thresholds)
    print(f"   🔍 Validation result: {'✅ VALID' if validation['valid'] else '❌ INVALID'}")
    if validation['warnings']:
        print("   ⚠️  Warnings:")
        for warning in validation['warnings']:
            print(f"      - {warning}")
    
    return ndvi_result, stats, classification

def demonstrate_batch_processing():
    """Demonstrate batch processing capabilities."""
    print("\n🔄 Batch Processing Demonstration")
    print("=" * 40)
    
    # Simulate multiple tiles
    tile_data = {}
    for i in range(3):
        tile_id = f"TILE_{i+1:03d}"
        red_data, nir_data = create_synthetic_sentinel2_data()
        
        # Save as temporary "files" (in real usage, these would be actual file paths)
        tile_data[tile_id] = {
            'red_data': red_data,
            'nir_data': nir_data
        }
    
    print(f"📦 Processing {len(tile_data)} tiles...")
    
    calculator = NDVICalculator(default_threshold=0.65)
    results = {}
    
    for tile_id, data in tile_data.items():
        from rasterio.transform import Affine
        import rasterio
        from src.ndvi.band_loader import BandData
        
        transform = Affine(10.0, 0.0, 500000.0, 0.0, -10.0, 6000000.0)
        crs = rasterio.CRS.from_epsg(32633)
        
        red_band = BandData(data['red_data'], transform, crs, None, 1.0, 0.0)
        nir_band = BandData(data['nir_data'], transform, crs, None, 1.0, 0.0)
        
        result = calculator.calculate_ndvi(red_band, nir_band, tile_id=tile_id)
        results[tile_id] = result
        
        print(f"   ✅ {tile_id}: Mean NDVI = {result.mean_ndvi:.4f}, "
              f"Threshold {'✅' if result.threshold_passed else '❌'}")
    
    # Summary statistics
    all_means = [r.mean_ndvi for r in results.values()]
    print(f"\n📊 Batch Summary:")
    print(f"   📈 Overall mean NDVI: {np.mean(all_means):.4f}")
    print(f"   📊 NDVI range: [{np.min(all_means):.4f}, {np.max(all_means):.4f}]")
    print(f"   🎯 Tiles passing threshold: {sum(r.threshold_passed for r in results.values())}/{len(results)}")

def main():
    """Main demonstration function."""
    print("🌍 VeriGreen NDVI Calculation Engine Demo")
    print("=" * 60)
    print("This demo shows how to use the NDVI engine for vegetation analysis.")
    print("In production, this would process real Sentinel-2 satellite imagery.")
    
    try:
        # Main demonstration
        ndvi_result, stats, classification = demonstrate_ndvi_calculation()
        
        # Batch processing demo
        demonstrate_batch_processing()
        
        print("\n🎉 Demo completed successfully!")
        print("\n📚 Next steps:")
        print("   1. Integrate with real Sentinel-2 data downloads")
        print("   2. Add API endpoints for NDVI calculation")
        print("   3. Store results in database with tile metadata")
        print("   4. Generate visualizations and reports")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 