#!/usr/bin/env python3
"""
Storage Optimization Test Framework for VeriGreen Demo

This script helps determine the optimal tile size and grid configuration
for the demo given the 5GB storage constraint on Storacha.
"""

import asyncio
import os
import sys
import json
import time
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
import numpy as np
from PIL import Image
import rasterio
from rasterio.windows import Window

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from src.filecoin.client import (
    StorachaClient, 
    StorachaConfig, 
    create_config_from_env
)


@dataclass
class TileConfig:
    """Configuration for tile generation."""
    tile_size: int  # pixels (e.g., 32, 64, 128, 256)
    image_format: str  # 'PNG', 'JPEG', 'TIFF'
    compression: Optional[str] = None  # JPEG quality or PNG compression
    

@dataclass
class StorageAnalysis:
    """Analysis results for a tile configuration."""
    config: TileConfig
    total_tiles: int
    avg_tile_size_bytes: int
    total_estimated_size_mb: float
    upload_time_estimate_minutes: float
    fits_in_5gb: bool
    sample_tile_sizes: List[int]


@dataclass
class BatchUploadResult:
    """Results from a batch upload test."""
    batch_size: int
    upload_time_seconds: float
    success_count: int
    failure_count: int
    total_bytes_uploaded: int
    avg_upload_speed_mbps: float


class StorageOptimizer:
    """Optimize tile configuration for storage constraints."""
    
    def __init__(self, storacha_config: StorachaConfig):
        self.config = storacha_config
        self.sentinel_dir = Path("data/raw/sentinel")
        self.output_dir = Path("data/processed/optimization_test")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Storage constraint
        self.max_storage_gb = 5.0
        self.max_storage_bytes = int(self.max_storage_gb * 1024 * 1024 * 1024)
        
    def get_image_dimensions(self, band_file: Path) -> Tuple[int, int]:
        """Get dimensions of satellite image."""
        with rasterio.open(band_file) as src:
            return src.width, src.height
    
    def calculate_grid_size(self, image_width: int, image_height: int, tile_size: int) -> Tuple[int, int]:
        """Calculate how many tiles fit in each dimension."""
        tiles_x = (image_width + tile_size - 1) // tile_size  # Ceiling division
        tiles_y = (image_height + tile_size - 1) // tile_size
        return tiles_x, tiles_y
    
    def generate_sample_tiles(self, config: TileConfig, num_samples: int = 10) -> List[int]:
        """Generate a few sample tiles to estimate file sizes."""
        print(f"  📏 Generating {num_samples} sample tiles (size: {config.tile_size}px, format: {config.image_format})")
        
        sample_sizes = []
        b04_path = self.sentinel_dir / "B04.jp2"
        b08_path = self.sentinel_dir / "B08.jp2"
        
        if not b04_path.exists() or not b08_path.exists():
            print(f"  ⚠️  Sentinel data not found. Using synthetic data for estimation.")
            # Generate synthetic tiles for size estimation
            for i in range(num_samples):
                synthetic_data = np.random.randint(0, 255, (config.tile_size, config.tile_size, 3), dtype=np.uint8)
                img = Image.fromarray(synthetic_data)
                
                temp_path = self.output_dir / f"sample_{config.tile_size}_{config.image_format}_{i}.{config.image_format.lower()}"
                
                if config.image_format == 'JPEG':
                    quality = config.compression or 85
                    img.save(temp_path, format='JPEG', quality=quality)
                elif config.image_format == 'PNG':
                    compress_level = config.compression or 6
                    img.save(temp_path, format='PNG', compress_level=compress_level)
                else:
                    img.save(temp_path, format=config.image_format)
                
                sample_sizes.append(temp_path.stat().st_size)
                temp_path.unlink()  # Clean up
            
            return sample_sizes
        
        # Use actual satellite data
        with rasterio.open(b04_path) as b04, rasterio.open(b08_path) as b08:
            width, height = b04.width, b04.height
            
            for i in range(num_samples):
                # Random tile position
                x = np.random.randint(0, max(1, width - config.tile_size))
                y = np.random.randint(0, max(1, height - config.tile_size))
                
                window = Window(x, y, config.tile_size, config.tile_size)
                
                # Read bands
                red_data = b04.read(1, window=window)
                nir_data = b08.read(1, window=window)
                
                # Calculate NDVI
                ndvi = (nir_data.astype(float) - red_data.astype(float)) / (nir_data.astype(float) + red_data.astype(float) + 1e-10)
                
                # Normalize to 0-255 for image
                ndvi_normalized = ((ndvi + 1) * 127.5).astype(np.uint8)
                
                # Create RGB image (for demo purposes)
                rgb_data = np.stack([red_data, nir_data, ndvi_normalized], axis=-1)
                
                # Ensure proper shape and data type
                if rgb_data.shape[0] == config.tile_size and rgb_data.shape[1] == config.tile_size:
                    img = Image.fromarray(rgb_data)
                    
                    temp_path = self.output_dir / f"sample_{config.tile_size}_{config.image_format}_{i}.{config.image_format.lower()}"
                    
                    if config.image_format == 'JPEG':
                        quality = config.compression or 85
                        img.save(temp_path, format='JPEG', quality=quality)
                    elif config.image_format == 'PNG':
                        compress_level = config.compression or 6
                        img.save(temp_path, format='PNG', compress_level=compress_level)
                    else:
                        img.save(temp_path, format=config.image_format)
                    
                    sample_sizes.append(temp_path.stat().st_size)
                    temp_path.unlink()  # Clean up
        
        return sample_sizes
    
    def analyze_storage_requirements(self, config: TileConfig) -> StorageAnalysis:
        """Analyze storage requirements for a given tile configuration."""
        print(f"\n🔍 Analyzing storage for {config.tile_size}px tiles ({config.image_format})")
        
        # Get image dimensions
        b04_path = self.sentinel_dir / "B04.jp2"
        if b04_path.exists():
            width, height = self.get_image_dimensions(b04_path)
            print(f"  📐 Image dimensions: {width} x {height} pixels")
        else:
            # Use typical Sentinel-2 tile dimensions
            width, height = 10980, 10980
            print(f"  📐 Using typical Sentinel-2 dimensions: {width} x {height} pixels")
        
        # Calculate grid
        tiles_x, tiles_y = self.calculate_grid_size(width, height, config.tile_size)
        total_tiles = tiles_x * tiles_y
        print(f"  🔢 Grid: {tiles_x} x {tiles_y} = {total_tiles} tiles")
        
        # Generate sample tiles to estimate size
        sample_sizes = self.generate_sample_tiles(config, num_samples=min(10, total_tiles))
        avg_tile_size = int(np.mean(sample_sizes)) if sample_sizes else 0
        
        # Calculate total storage
        total_size_bytes = total_tiles * avg_tile_size
        total_size_mb = total_size_bytes / (1024 * 1024)
        total_size_gb = total_size_mb / 1024
        
        # Estimate upload time (assuming 1MB/s average)
        upload_time_minutes = total_size_mb / 60  # Conservative estimate
        
        fits_in_5gb = total_size_bytes <= self.max_storage_bytes
        
        print(f"  📊 Average tile size: {avg_tile_size / 1024:.1f} KB")
        print(f"  📦 Total estimated storage: {total_size_mb:.1f} MB ({total_size_gb:.2f} GB)")
        print(f"  ⏱️  Estimated upload time: {upload_time_minutes:.1f} minutes")
        print(f"  ✅ Fits in 5GB: {'Yes' if fits_in_5gb else 'No'}")
        
        return StorageAnalysis(
            config=config,
            total_tiles=total_tiles,
            avg_tile_size_bytes=avg_tile_size,
            total_estimated_size_mb=total_size_mb,
            upload_time_estimate_minutes=upload_time_minutes,
            fits_in_5gb=fits_in_5gb,
            sample_tile_sizes=sample_sizes
        )
    
    async def test_batch_upload_performance(self, batch_sizes: List[int]) -> List[BatchUploadResult]:
        """Test upload performance for different batch sizes."""
        print(f"\n🚀 Testing batch upload performance...")
        
        results = []
        test_data = b"X" * 1024  # 1KB test data per file
        
        async with StorachaClient(self.config) as client:
            for batch_size in batch_sizes:
                print(f"\n  📦 Testing batch size: {batch_size}")
                
                start_time = time.time()
                success_count = 0
                failure_count = 0
                total_bytes = 0
                
                # Create batch upload tasks
                tasks = []
                for i in range(batch_size):
                    filename = f"batch_test_{batch_size}_{i}.txt"
                    tasks.append(client.upload_data(test_data, filename))
                
                # Execute batch
                try:
                    results_batch = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for result in results_batch:
                        if isinstance(result, Exception):
                            failure_count += 1
                        else:
                            success_count += 1
                            total_bytes += len(test_data)
                    
                except Exception as e:
                    print(f"    ❌ Batch upload failed: {e}")
                    failure_count = batch_size
                
                end_time = time.time()
                upload_time = end_time - start_time
                
                # Calculate metrics
                if upload_time > 0:
                    speed_mbps = (total_bytes / (1024 * 1024)) / upload_time
                else:
                    speed_mbps = 0
                
                result = BatchUploadResult(
                    batch_size=batch_size,
                    upload_time_seconds=upload_time,
                    success_count=success_count,
                    failure_count=failure_count,
                    total_bytes_uploaded=total_bytes,
                    avg_upload_speed_mbps=speed_mbps
                )
                
                results.append(result)
                
                print(f"    ✅ Success: {success_count}/{batch_size}")
                print(f"    ⏱️  Time: {upload_time:.2f}s")
                print(f"    🚄 Speed: {speed_mbps:.2f} MB/s")
                
                # Brief pause between batches
                await asyncio.sleep(1)
        
        return results
    
    def generate_recommendations(self, analyses: List[StorageAnalysis], batch_results: List[BatchUploadResult]) -> Dict:
        """Generate recommendations based on analysis."""
        print(f"\n📋 Generating Recommendations...")
        
        # Find configurations that fit in 5GB
        viable_configs = [a for a in analyses if a.fits_in_5gb]
        
        if not viable_configs:
            print("  ⚠️  No configurations fit within 5GB limit!")
            return {
                "status": "error",
                "message": "No tile configurations fit within 5GB storage limit",
                "recommendations": []
            }
        
        # Sort by total tiles (higher resolution preferred)
        viable_configs.sort(key=lambda x: x.total_tiles, reverse=True)
        
        # Batch performance summary
        best_batch_performance = max(batch_results, key=lambda x: x.avg_upload_speed_mbps) if batch_results else None
        
        recommendations = []
        
        for i, config in enumerate(viable_configs[:3]):  # Top 3 recommendations
            rank = ["🥇", "🥈", "🥉"][i] if i < 3 else f"{i+1}."
            
            rec = {
                "rank": i + 1,
                "emoji": rank,
                "tile_size": config.config.tile_size,
                "format": config.config.image_format,
                "total_tiles": config.total_tiles,
                "storage_mb": config.total_estimated_size_mb,
                "upload_time_minutes": config.upload_time_estimate_minutes,
                "avg_tile_size_kb": config.avg_tile_size_bytes / 1024,
                "storage_efficiency": config.total_estimated_size_mb / self.max_storage_gb / 1024,  # % of 5GB used
            }
            
            recommendations.append(rec)
            
            print(f"  {rank} {config.config.tile_size}px {config.config.image_format} tiles")
            print(f"      🔢 Total tiles: {config.total_tiles:,}")
            print(f"      📦 Storage: {config.total_estimated_size_mb:.1f} MB ({config.total_estimated_size_mb/1024/5*100:.1f}% of 5GB)")
            print(f"      ⏱️  Upload time: ~{config.upload_time_estimate_minutes:.1f} minutes")
            print(f"      📏 Avg tile size: {config.avg_tile_size_bytes/1024:.1f} KB")
        
        if best_batch_performance:
            print(f"\n  🚄 Best batch performance: {best_batch_performance.batch_size} files at {best_batch_performance.avg_upload_speed_mbps:.2f} MB/s")
        
        return {
            "status": "success",
            "max_storage_gb": self.max_storage_gb,
            "recommendations": recommendations,
            "batch_performance": {
                "best_batch_size": best_batch_performance.batch_size if best_batch_performance else None,
                "best_speed_mbps": best_batch_performance.avg_upload_speed_mbps if best_batch_performance else None,
            } if best_batch_performance else None
        }


async def main():
    """Main optimization test."""
    print("🌱 VeriGreen Storage Optimization Test")
    print("=" * 50)
    
    # Load configuration
    try:
        config = create_config_from_env()
        print(f"✅ Storacha configuration loaded")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False
    
    optimizer = StorageOptimizer(config)
    
    # Test configurations
    tile_configs = [
        # PNG with different tile sizes
        TileConfig(32, 'PNG', 6),
        TileConfig(64, 'PNG', 6),
        TileConfig(128, 'PNG', 6),
        TileConfig(256, 'PNG', 6),
        
        # JPEG with different qualities
        TileConfig(64, 'JPEG', 85),
        TileConfig(128, 'JPEG', 85),
        TileConfig(256, 'JPEG', 85),
        TileConfig(128, 'JPEG', 70),  # Lower quality for more compression
        TileConfig(256, 'JPEG', 70),
    ]
    
    # Analyze storage requirements
    print(f"\n🔍 Analyzing Storage Requirements")
    print("=" * 50)
    
    analyses = []
    for config in tile_configs:
        analysis = optimizer.analyze_storage_requirements(config)
        analyses.append(analysis)
    
    # Test batch upload performance
    print(f"\n🚀 Testing Batch Upload Performance")
    print("=" * 50)
    
    batch_sizes = [1, 4, 8, 16, 32]  # Start conservative for 5GB limit
    batch_results = await optimizer.test_batch_upload_performance(batch_sizes)
    
    # Generate recommendations
    print(f"\n📊 Final Analysis and Recommendations")
    print("=" * 50)
    
    recommendations = optimizer.generate_recommendations(analyses, batch_results)
    
    # Save results
    results_file = optimizer.output_dir / "storage_optimization_results.json"
    with open(results_file, 'w') as f:
        # Convert analyses to dict for JSON serialization
        analyses_dict = []
        for a in analyses:
            analyses_dict.append({
                "tile_size": a.config.tile_size,
                "format": a.config.image_format,
                "compression": a.config.compression,
                "total_tiles": a.total_tiles,
                "avg_tile_size_bytes": a.avg_tile_size_bytes,
                "total_estimated_size_mb": a.total_estimated_size_mb,
                "upload_time_estimate_minutes": a.upload_time_estimate_minutes,
                "fits_in_5gb": a.fits_in_5gb,
                "sample_tile_sizes": a.sample_tile_sizes
            })
        
        batch_dict = []
        for b in batch_results:
            batch_dict.append({
                "batch_size": b.batch_size,
                "upload_time_seconds": b.upload_time_seconds,
                "success_count": b.success_count,
                "failure_count": b.failure_count,
                "total_bytes_uploaded": b.total_bytes_uploaded,
                "avg_upload_speed_mbps": b.avg_upload_speed_mbps
            })
        
        json.dump({
            "analyses": analyses_dict,
            "batch_results": batch_dict,
            "recommendations": recommendations
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")
    print(f"\n🎉 Storage optimization analysis complete!")
    
    if recommendations["status"] == "success" and recommendations["recommendations"]:
        best = recommendations["recommendations"][0]
        print(f"\n🌟 RECOMMENDED FOR DEMO:")
        print(f"   📏 Tile size: {best['tile_size']}px")
        print(f"   🖼️  Format: {best['format']}")
        print(f"   🔢 Total tiles: {best['total_tiles']:,}")
        print(f"   📦 Storage needed: {best['storage_mb']:.1f} MB ({best['storage_mb']/1024/5*100:.1f}% of 5GB)")
        print(f"   ⏱️  Estimated upload: ~{best['upload_time_minutes']:.1f} minutes")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 