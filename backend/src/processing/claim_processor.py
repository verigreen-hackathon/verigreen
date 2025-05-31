"""
On-demand processing system for land claims in Batang Toru Ecosystem.

This module orchestrates the complete processing pipeline:
1. Download Sentinel-2 data for claimed areas
2. Slice imagery into tiles 
3. Calculate NDVI for tropical rainforest monitoring
4. Generate processed GeoTIFF outputs
"""

import logging
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, NamedTuple
from dataclasses import dataclass

import numpy as np

# Fixed imports - using absolute paths
from config import PROCESSED_DATA_DIR
from sentinel.download import get_or_download_sentinel_for_claim
from sentinel.slicer import ImageSlicer, TileData
from sentinel.batang_toru_mapper import get_claim_download_config
from ndvi.calculator import NDVICalculator, NDVIResult
from ndvi.statistics import NDVIStatistics

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Result of processing a land claim."""
    
    claim_id: str
    claim_area: Dict[str, Dict[str, int]]
    processing_time: float
    success: bool
    
    # Download results
    download_success: bool
    download_cache_used: bool
    downloaded_files: List[str]
    
    # Processing results
    tiles_generated: int
    ndvi_tiles: List[str]
    
    # NDVI statistics
    mean_ndvi: float
    forest_health_score: float
    conservation_metrics: Dict[str, float]
    
    # Output paths
    output_directory: str
    processed_files: List[str]
    
    # Metadata
    processing_date: str
    sentinel_date: str
    bands_processed: List[str]
    
    error_message: Optional[str] = None


class ClaimProcessor:
    """Processes satellite imagery for specific land claims in Batang Toru."""
    
    def __init__(self, output_base_dir: Optional[str] = None):
        """
        Initialize the claim processor.
        
        Args:
            output_base_dir: Base directory for processed outputs
        """
        self.output_base_dir = Path(output_base_dir) if output_base_dir else PROCESSED_DATA_DIR
        self.output_base_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.ndvi_calculator = NDVICalculator()
        self.ndvi_statistics = NDVIStatistics()
        
        logger.info(f"Initialized ClaimProcessor with output directory: {self.output_base_dir}")
    
    async def process_claim(
        self, 
        claim_id: str,
        southwest_x: int, 
        southwest_y: int,
        northeast_x: int, 
        northeast_y: int,
        force_reprocess: bool = False
    ) -> ProcessingResult:
        """
        Process a land claim with complete satellite imagery analysis.
        
        Args:
            claim_id: Unique identifier for the claim
            southwest_x, southwest_y: Southwest corner coordinates (0-9)
            northeast_x, northeast_y: Northeast corner coordinates (0-9)
            force_reprocess: Force reprocessing even if results exist
            
        Returns:
            ProcessingResult with complete processing information
        """
        start_time = datetime.now()
        logger.info(f"Starting processing for claim {claim_id}: ({southwest_x},{southwest_y}) to ({northeast_x},{northeast_y})")
        
        # Create claim-specific output directory
        claim_dir = self.output_base_dir / f"claim_{claim_id}"
        claim_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Step 1: Download Sentinel-2 data
            logger.info(f"Step 1: Downloading Sentinel-2 data for claim {claim_id}")
            download_files, download_report = get_or_download_sentinel_for_claim(
                southwest_x, southwest_y, northeast_x, northeast_y,
                force_download=force_reprocess
            )
            
            if not download_report['success']:
                error_msg = f"Failed to download Sentinel-2 data: {download_report.get('error', 'Unknown error')}"
                logger.error(error_msg)
                return self._create_error_result(claim_id, southwest_x, southwest_y, northeast_x, northeast_y, error_msg, start_time)
            
            # Step 2: Process the downloaded imagery
            logger.info(f"Step 2: Processing imagery for claim {claim_id}")
            processing_results = await self._process_downloaded_imagery(
                claim_id, download_files, claim_dir
            )
            
            # Step 3: Calculate conservation metrics
            logger.info(f"Step 3: Calculating conservation metrics for claim {claim_id}")
            conservation_metrics = self._calculate_conservation_metrics(processing_results['ndvi_results'])
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Create result
            result = ProcessingResult(
                claim_id=claim_id,
                claim_area={
                    "southwest": {"x": southwest_x, "y": southwest_y},
                    "northeast": {"x": northeast_x, "y": northeast_y}
                },
                processing_time=processing_time,
                success=True,
                
                # Download info
                download_success=download_report['success'],
                download_cache_used=download_report.get('cache_used', False),
                downloaded_files=download_report.get('files', []),
                
                # Processing info
                tiles_generated=len(processing_results['tiles']),
                ndvi_tiles=processing_results['ndvi_files'],
                
                # NDVI statistics
                mean_ndvi=processing_results['overall_ndvi_stats']['mean'],
                forest_health_score=conservation_metrics['forest_health_score'],
                conservation_metrics=conservation_metrics,
                
                # Output info
                output_directory=str(claim_dir),
                processed_files=processing_results['all_output_files'],
                
                # Metadata
                processing_date=datetime.now().isoformat(),
                sentinel_date=self._extract_sentinel_date(download_files),
                bands_processed=["B04", "B08"]
            )
            
            # Save processing report
            await self._save_processing_report(result, claim_dir)
            
            logger.info(f"Successfully processed claim {claim_id} in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            error_msg = f"Unexpected error processing claim {claim_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return self._create_error_result(claim_id, southwest_x, southwest_y, northeast_x, northeast_y, error_msg, start_time)
    
    async def _process_downloaded_imagery(
        self, 
        claim_id: str, 
        download_files: List[Path], 
        output_dir: Path
    ) -> Dict:
        """
        Process downloaded imagery files into tiles and calculate NDVI.
        
        Args:
            claim_id: Claim identifier
            download_files: List of downloaded band files
            output_dir: Output directory for processed files
            
        Returns:
            Dictionary with processing results
        """
        # Organize files by band
        band_files = {}
        for file_path in download_files:
            file_path = Path(file_path)
            if 'B04' in file_path.name:
                band_files['B04'] = file_path
            elif 'B08' in file_path.name:
                band_files['B08'] = file_path
        
        if len(band_files) != 2:
            raise ValueError(f"Expected B04 and B08 bands, got: {list(band_files.keys())}")
        
        # Create subdirectories
        tiles_dir = output_dir / "tiles"
        ndvi_dir = output_dir / "ndvi"
        tiles_dir.mkdir(exist_ok=True)
        ndvi_dir.mkdir(exist_ok=True)
        
        # Process each band
        logger.info(f"Slicing imagery into tiles for claim {claim_id}")
        
        # Initialize slicer for 10x10 grid (matching Batang Toru grid)
        slicer = ImageSlicer(
            grid_size=10,  # 10x10 grid to match Batang Toru
            tile_size=64,  # 64x64 pixel tiles for good resolution
            output_dir=tiles_dir
        )
        
        # Slice both bands
        band_tiles = {}
        for band, file_path in band_files.items():
            logger.info(f"Slicing {band} band from {file_path}")
            tiles = slicer.slice_imagery(file_path, bands=[band])
            band_tiles[band] = tiles
            
            # Save individual band tiles
            band_dir = tiles_dir / band
            band_dir.mkdir(exist_ok=True)
            slicer.output_dir = band_dir
            slicer.save_all_tiles(tiles, prefix=f"{band}_")
        
        # Calculate NDVI for corresponding tiles
        logger.info(f"Calculating NDVI for claim {claim_id}")
        ndvi_results = []
        ndvi_files = []
        
        # Ensure we have matching tiles
        b04_tiles = band_tiles['B04']
        b08_tiles = band_tiles['B08']
        
        if len(b04_tiles) != len(b08_tiles):
            logger.warning(f"Mismatch in tile count: B04={len(b04_tiles)}, B08={len(b08_tiles)}")
        
        # Process each tile pair
        for i, (red_tile, nir_tile) in enumerate(zip(b04_tiles, b08_tiles)):
            try:
                # Extract band data
                red_data = red_tile.get_band_data(0)
                nir_data = nir_tile.get_band_data(0)
                
                # Calculate NDVI
                ndvi_result = self.ndvi_calculator.calculate_ndvi(
                    red_data=red_data,
                    nir_data=nir_data,
                    tile_id=f"{claim_id}_tile_{i:02d}"
                )
                
                ndvi_results.append(ndvi_result)
                
                # Save NDVI tile as GeoTIFF
                ndvi_file = ndvi_dir / f"ndvi_tile_{i:02d}.tif"
                self._save_ndvi_tile(ndvi_result, red_tile.coordinates, ndvi_file)
                ndvi_files.append(str(ndvi_file))
                
            except Exception as e:
                logger.error(f"Failed to process tile {i} for claim {claim_id}: {str(e)}")
                continue
        
        # Calculate overall NDVI statistics
        if ndvi_results:
            combined_ndvi = np.concatenate([result.ndvi_array.flatten() for result in ndvi_results])
            overall_stats = self._calculate_overall_ndvi_stats(combined_ndvi)
        else:
            overall_stats = {'mean': 0.0, 'std': 0.0, 'min': 0.0, 'max': 0.0}
        
        # Collect all output files
        all_output_files = []
        all_output_files.extend(ndvi_files)
        for band_dir in tiles_dir.iterdir():
            if band_dir.is_dir():
                all_output_files.extend([str(f) for f in band_dir.glob("*.tif")])
        
        return {
            'tiles': b04_tiles + b08_tiles,
            'ndvi_results': ndvi_results,
            'ndvi_files': ndvi_files,
            'overall_ndvi_stats': overall_stats,
            'all_output_files': all_output_files
        }
    
    def _save_ndvi_tile(self, ndvi_result: NDVIResult, coordinates, output_path: Path):
        """Save NDVI result as a GeoTIFF tile."""
        import rasterio
        from rasterio.transform import from_bounds
        
        # Create transform for the tile
        tile_transform = from_bounds(
            coordinates.geo_bounds.left,
            coordinates.geo_bounds.bottom,
            coordinates.geo_bounds.right,
            coordinates.geo_bounds.top,
            ndvi_result.ndvi_array.shape[1],
            ndvi_result.ndvi_array.shape[0]
        )
        
        # Set up rasterio profile
        profile = {
            'driver': 'GTiff',
            'height': ndvi_result.ndvi_array.shape[0],
            'width': ndvi_result.ndvi_array.shape[1],
            'count': 1,
            'dtype': 'float32',
            'crs': 'EPSG:4326',  # WGS84
            'transform': tile_transform,
            'compress': 'lzw',
            'nodata': np.nan
        }
        
        # Write the NDVI data
        with rasterio.open(output_path, 'w', **profile) as dst:
            dst.write(ndvi_result.ndvi_array.astype('float32'), 1)
            
            # Add metadata
            dst.update_tags(
                tile_id=coordinates.tile_id,
                mean_ndvi=str(ndvi_result.mean_ndvi),
                forest_health=str(ndvi_result.threshold_passed),
                calculation_date=datetime.now().isoformat()
            )
    
    def _calculate_conservation_metrics(self, ndvi_results: List[NDVIResult]) -> Dict[str, float]:
        """Calculate conservation-specific metrics for Batang Toru."""
        if not ndvi_results:
            return {
                'forest_health_score': 0.0,
                'habitat_quality': 0.0,
                'vegetation_density': 0.0,
                'conservation_priority': 0.0
            }
        
        # Calculate overall metrics
        all_ndvi_values = np.concatenate([result.ndvi_array.flatten() for result in ndvi_results])
        valid_ndvi = all_ndvi_values[~np.isnan(all_ndvi_values)]
        
        if len(valid_ndvi) == 0:
            return {
                'forest_health_score': 0.0,
                'habitat_quality': 0.0,
                'vegetation_density': 0.0,
                'conservation_priority': 0.0
            }
        
        mean_ndvi = np.mean(valid_ndvi)
        
        # Forest health score (0-100 scale)
        # NDVI > 0.7 = excellent, 0.5-0.7 = good, 0.3-0.5 = moderate, <0.3 = poor
        if mean_ndvi > 0.7:
            forest_health_score = 85 + (mean_ndvi - 0.7) * 50
        elif mean_ndvi > 0.5:
            forest_health_score = 65 + (mean_ndvi - 0.5) * 100
        elif mean_ndvi > 0.3:
            forest_health_score = 35 + (mean_ndvi - 0.3) * 150
        else:
            forest_health_score = mean_ndvi * 116.67
        
        forest_health_score = min(100.0, max(0.0, forest_health_score))
        
        # Habitat quality (specific to Tapanuli orangutan needs)
        # Higher NDVI indicates better canopy cover and food availability
        habitat_quality = min(100.0, (mean_ndvi + 1) * 50)  # Scale [-1,1] to [0,100]
        
        # Vegetation density
        high_vegetation_pixels = np.sum(valid_ndvi > 0.6)
        vegetation_density = (high_vegetation_pixels / len(valid_ndvi)) * 100
        
        # Conservation priority (combines multiple factors)
        conservation_priority = (forest_health_score * 0.4 + 
                               habitat_quality * 0.3 + 
                               vegetation_density * 0.3)
        
        return {
            'forest_health_score': round(forest_health_score, 2),
            'habitat_quality': round(habitat_quality, 2),
            'vegetation_density': round(vegetation_density, 2),
            'conservation_priority': round(conservation_priority, 2)
        }
    
    def _calculate_overall_ndvi_stats(self, ndvi_array: np.ndarray) -> Dict[str, float]:
        """Calculate overall NDVI statistics."""
        valid_values = ndvi_array[~np.isnan(ndvi_array)]
        
        if len(valid_values) == 0:
            return {'mean': 0.0, 'std': 0.0, 'min': 0.0, 'max': 0.0}
        
        return {
            'mean': float(np.mean(valid_values)),
            'std': float(np.std(valid_values)),
            'min': float(np.min(valid_values)),
            'max': float(np.max(valid_values))
        }
    
    def _extract_sentinel_date(self, download_files: List[Path]) -> str:
        """Extract Sentinel-2 acquisition date from filenames."""
        if not download_files:
            return "unknown"
        
        # Look for date pattern in filename (e.g., 2024-6-15)
        for file_path in download_files:
            filename = Path(file_path).name
            if '_2024-' in filename:
                # Extract date from filename pattern
                parts = filename.split('_')
                for part in parts:
                    if '2024-' in part:
                        return part.replace('-', '/')
        
        return "2024/6/15"  # Default date
    
    async def _save_processing_report(self, result: ProcessingResult, output_dir: Path):
        """Save a JSON report of the processing results."""
        import json
        
        report_path = output_dir / "processing_report.json"
        
        # Convert result to dict for JSON serialization
        report_data = {
            'claim_id': result.claim_id,
            'claim_area': result.claim_area,
            'processing_time_seconds': result.processing_time,
            'success': result.success,
            'download_info': {
                'success': result.download_success,
                'cache_used': result.download_cache_used,
                'files': result.downloaded_files
            },
            'processing_info': {
                'tiles_generated': result.tiles_generated,
                'ndvi_tiles': result.ndvi_tiles,
                'bands_processed': result.bands_processed
            },
            'conservation_analysis': {
                'mean_ndvi': result.mean_ndvi,
                'forest_health_score': result.forest_health_score,
                'conservation_metrics': result.conservation_metrics
            },
            'output_info': {
                'output_directory': result.output_directory,
                'processed_files': result.processed_files
            },
            'metadata': {
                'processing_date': result.processing_date,
                'sentinel_date': result.sentinel_date
            }
        }
        
        if result.error_message:
            report_data['error_message'] = result.error_message
        
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"Saved processing report to {report_path}")
    
    def _create_error_result(
        self, 
        claim_id: str, 
        southwest_x: int, 
        southwest_y: int, 
        northeast_x: int, 
        northeast_y: int, 
        error_message: str, 
        start_time: datetime
    ) -> ProcessingResult:
        """Create an error result."""
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return ProcessingResult(
            claim_id=claim_id,
            claim_area={
                "southwest": {"x": southwest_x, "y": southwest_y},
                "northeast": {"x": northeast_x, "y": northeast_y}
            },
            processing_time=processing_time,
            success=False,
            download_success=False,
            download_cache_used=False,
            downloaded_files=[],
            tiles_generated=0,
            ndvi_tiles=[],
            mean_ndvi=0.0,
            forest_health_score=0.0,
            conservation_metrics={},
            output_directory="",
            processed_files=[],
            processing_date=datetime.now().isoformat(),
            sentinel_date="unknown",
            bands_processed=[],
            error_message=error_message
        )


# Convenience function for simple processing
async def process_claim_async(
    claim_id: str,
    southwest_x: int,
    southwest_y: int, 
    northeast_x: int,
    northeast_y: int,
    output_dir: Optional[str] = None
) -> ProcessingResult:
    """
    Asynchronous convenience function to process a single claim.
    
    Args:
        claim_id: Unique identifier for the claim
        southwest_x, southwest_y: Southwest corner (0-9)
        northeast_x, northeast_y: Northeast corner (0-9)
        output_dir: Optional output directory
        
    Returns:
        ProcessingResult with complete information
    """
    processor = ClaimProcessor(output_dir)
    return await processor.process_claim(
        claim_id, southwest_x, southwest_y, northeast_x, northeast_y
    ) 