"""NDVI calculation module for computing vegetation index from satellite imagery.

This module implements the core NDVI formula and provides utilities for
processing satellite imagery bands to calculate vegetation indices.
"""

import logging
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np

from .band_loader import BandData

logger = logging.getLogger(__name__)


@dataclass
class NDVIResult:
    """Container for NDVI calculation results."""
    
    ndvi_array: np.ndarray
    """The full NDVI array with values between -1 and 1."""
    
    tile_id: Optional[str] = None
    """Identifier for the processed tile."""
    
    mean_ndvi: float = 0.0
    """Mean NDVI value across all valid pixels."""
    
    min_ndvi: float = 0.0
    """Minimum NDVI value."""
    
    max_ndvi: float = 0.0
    """Maximum NDVI value."""
    
    std_ndvi: float = 0.0
    """Standard deviation of NDVI values."""
    
    valid_pixel_count: int = 0
    """Number of valid (non-NaN) pixels."""
    
    total_pixel_count: int = 0
    """Total number of pixels in the array."""
    
    valid_pixel_percentage: float = 0.0
    """Percentage of valid pixels."""
    
    threshold_passed: bool = False
    """Whether the mean NDVI exceeds the threshold (default 0.65)."""
    
    threshold_value: float = 0.65
    """The threshold value used for classification."""
    
    processed_at: str = ""
    """Timestamp when the calculation was performed."""
    
    metadata: Dict[str, Any] = None
    """Additional metadata about the calculation."""
    
    def __post_init__(self):
        """Initialize computed fields after dataclass creation."""
        if not self.processed_at:
            self.processed_at = datetime.now().isoformat()
        if self.metadata is None:
            self.metadata = {}


class NDVICalculator:
    """Calculator for NDVI (Normalized Difference Vegetation Index) values."""
    
    def __init__(self, default_threshold: float = 0.65):
        """Initialize the NDVI calculator.
        
        Args:
            default_threshold: Default threshold for vegetation classification
        """
        self.default_threshold = default_threshold
        
    def calculate_ndvi(
        self, 
        red_band: BandData, 
        nir_band: BandData,
        threshold: Optional[float] = None,
        tile_id: Optional[str] = None
    ) -> NDVIResult:
        """Calculate NDVI from RED and NIR band data.
        
        NDVI formula: (NIR - RED) / (NIR + RED)
        
        Args:
            red_band: RED band data (typically Sentinel-2 B04)
            nir_band: NIR band data (typically Sentinel-2 B08)
            threshold: Threshold for vegetation classification (defaults to instance default)
            tile_id: Optional identifier for the tile being processed
            
        Returns:
            NDVIResult containing the calculated NDVI values and statistics
            
        Raises:
            ValueError: If bands are incompatible or contain invalid data
        """
        if threshold is None:
            threshold = self.default_threshold
            
        logger.info(f"Calculating NDVI for tile: {tile_id or 'unknown'}")
        
        # Get scaled data from bands
        red_data = red_band.get_scaled_data()
        nir_data = nir_band.get_scaled_data()
        
        # Validate data compatibility
        self._validate_band_data(red_data, nir_data)
        
        # Calculate NDVI using the core formula
        ndvi_array = self._compute_ndvi_formula(red_data, nir_data)
        
        # Calculate statistics
        stats = self._calculate_statistics(ndvi_array, threshold)
        
        # Create result object
        result = NDVIResult(
            ndvi_array=ndvi_array,
            tile_id=tile_id,
            mean_ndvi=stats['mean'],
            min_ndvi=stats['min'],
            max_ndvi=stats['max'],
            std_ndvi=stats['std'],
            valid_pixel_count=stats['valid_count'],
            total_pixel_count=stats['total_count'],
            valid_pixel_percentage=stats['valid_percentage'],
            threshold_passed=stats['threshold_passed'],
            threshold_value=threshold,
            metadata={
                'red_band_info': {
                    'shape': red_data.shape,
                    'scale_factor': red_band.scale_factor,
                    'nodata_value': red_band.nodata_value
                },
                'nir_band_info': {
                    'shape': nir_data.shape,
                    'scale_factor': nir_band.scale_factor,
                    'nodata_value': nir_band.nodata_value
                },
                'calculation_method': 'standard_ndvi_formula'
            }
        )
        
        logger.info(f"NDVI calculation complete. Mean: {stats['mean']:.4f}, "
                   f"Valid pixels: {stats['valid_count']}/{stats['total_count']} "
                   f"({stats['valid_percentage']:.1f}%)")
        
        return result
    
    def _compute_ndvi_formula(self, red_data: np.ndarray, nir_data: np.ndarray) -> np.ndarray:
        """Compute NDVI using the standard formula with robust handling of edge cases.
        
        Args:
            red_data: RED band reflectance values
            nir_data: NIR band reflectance values
            
        Returns:
            NDVI array with values clipped to [-1, 1] range
        """
        logger.debug("Computing NDVI formula: (NIR - RED) / (NIR + RED)")
        
        # Ensure we're working with float64 for precision
        red = red_data.astype(np.float64)
        nir = nir_data.astype(np.float64)
        
        # Calculate numerator and denominator
        numerator = nir - red
        denominator = nir + red
        
        # Handle division by zero and near-zero denominators
        # Set a small epsilon to avoid division by very small numbers
        epsilon = 1e-10
        
        # Create the NDVI array initialized with NaN
        ndvi = np.full_like(numerator, np.nan, dtype=np.float64)
        
        # Calculate NDVI only where denominator is significantly different from zero
        valid_mask = np.abs(denominator) > epsilon
        ndvi[valid_mask] = numerator[valid_mask] / denominator[valid_mask]
        
        # Handle special cases where both NIR and RED are zero (should be NaN)
        zero_both_mask = (np.abs(red) < epsilon) & (np.abs(nir) < epsilon)
        ndvi[zero_both_mask] = np.nan
        
        # Clip values to the theoretical NDVI range [-1, 1]
        # Values outside this range indicate data quality issues
        ndvi = np.clip(ndvi, -1.0, 1.0)
        
        # Log statistics about the calculation
        valid_pixels = ~np.isnan(ndvi)
        zero_denominator_count = np.sum(np.abs(denominator) <= epsilon)
        
        logger.debug(f"NDVI calculation stats: "
                    f"Valid pixels: {np.sum(valid_pixels)}, "
                    f"Zero/near-zero denominators: {zero_denominator_count}, "
                    f"Range: [{np.nanmin(ndvi):.4f}, {np.nanmax(ndvi):.4f}]")
        
        return ndvi
    
    def _calculate_statistics(self, ndvi_array: np.ndarray, threshold: float) -> Dict[str, Any]:
        """Calculate comprehensive statistics for the NDVI array.
        
        Args:
            ndvi_array: Array of NDVI values
            threshold: Threshold for vegetation classification
            
        Returns:
            Dictionary containing statistical measures
        """
        # Get valid (non-NaN) pixels
        valid_mask = ~np.isnan(ndvi_array)
        valid_values = ndvi_array[valid_mask]
        
        total_count = ndvi_array.size
        valid_count = len(valid_values)
        valid_percentage = (valid_count / total_count * 100) if total_count > 0 else 0.0
        
        if valid_count > 0:
            mean_val = float(np.mean(valid_values))
            min_val = float(np.min(valid_values))
            max_val = float(np.max(valid_values))
            std_val = float(np.std(valid_values))
            threshold_passed = mean_val >= threshold
        else:
            mean_val = min_val = max_val = std_val = 0.0
            threshold_passed = False
        
        return {
            'mean': mean_val,
            'min': min_val,
            'max': max_val,
            'std': std_val,
            'valid_count': valid_count,
            'total_count': total_count,
            'valid_percentage': valid_percentage,
            'threshold_passed': threshold_passed
        }
    
    def _validate_band_data(self, red_data: np.ndarray, nir_data: np.ndarray) -> None:
        """Validate that band data is suitable for NDVI calculation.
        
        Args:
            red_data: RED band data array
            nir_data: NIR band data array
            
        Raises:
            ValueError: If data is invalid or incompatible
        """
        # Check shapes match
        if red_data.shape != nir_data.shape:
            raise ValueError(f"Band shapes don't match: RED {red_data.shape} vs NIR {nir_data.shape}")
        
        # Check for completely empty arrays
        if red_data.size == 0 or nir_data.size == 0:
            raise ValueError("Band data arrays are empty")
        
        # Check data types
        if not np.issubdtype(red_data.dtype, np.number) or not np.issubdtype(nir_data.dtype, np.number):
            raise ValueError("Band data must be numeric")
        
        # Log warnings for potential data quality issues
        red_all_nan = np.all(np.isnan(red_data))
        nir_all_nan = np.all(np.isnan(nir_data))
        
        if red_all_nan:
            logger.warning("RED band contains only NaN values")
        if nir_all_nan:
            logger.warning("NIR band contains only NaN values")
        
        # Check for negative reflectance values (which shouldn't occur in properly processed data)
        red_valid = red_data[~np.isnan(red_data)]
        nir_valid = nir_data[~np.isnan(nir_data)]
        
        if len(red_valid) > 0 and np.any(red_valid < 0):
            logger.warning("RED band contains negative values, which may indicate data quality issues")
        if len(nir_valid) > 0 and np.any(nir_valid < 0):
            logger.warning("NIR band contains negative values, which may indicate data quality issues")
    
    def calculate_ndvi_from_files(
        self,
        red_file_path: str,
        nir_file_path: str,
        threshold: Optional[float] = None,
        tile_id: Optional[str] = None,
        cloud_mask_path: Optional[str] = None
    ) -> NDVIResult:
        """Calculate NDVI directly from file paths.
        
        Convenience method that handles band loading and NDVI calculation.
        
        Args:
            red_file_path: Path to RED band file
            nir_file_path: Path to NIR band file
            threshold: Threshold for vegetation classification
            tile_id: Optional tile identifier
            cloud_mask_path: Optional cloud mask file path
            
        Returns:
            NDVIResult containing calculated values and statistics
        """
        from .band_loader import BandLoader
        
        logger.info(f"Loading bands and calculating NDVI for tile: {tile_id or 'unknown'}")
        
        # Load bands
        loader = BandLoader()
        red_band, nir_band = loader.load_sentinel2_bands(
            red_path=red_file_path,
            nir_path=nir_file_path,
            cloud_mask_path=cloud_mask_path
        )
        
        # Calculate NDVI
        return self.calculate_ndvi(red_band, nir_band, threshold, tile_id)
    
    def batch_calculate_ndvi(
        self,
        tile_data: Dict[str, Dict[str, str]],
        threshold: Optional[float] = None
    ) -> Dict[str, NDVIResult]:
        """Calculate NDVI for multiple tiles in batch.
        
        Args:
            tile_data: Dictionary mapping tile_id to {'red': path, 'nir': path, 'cloud_mask': path}
            threshold: Threshold for vegetation classification
            
        Returns:
            Dictionary mapping tile_id to NDVIResult
        """
        results = {}
        
        for tile_id, paths in tile_data.items():
            try:
                logger.info(f"Processing tile {tile_id}")
                
                result = self.calculate_ndvi_from_files(
                    red_file_path=paths['red'],
                    nir_file_path=paths['nir'],
                    threshold=threshold,
                    tile_id=tile_id,
                    cloud_mask_path=paths.get('cloud_mask')
                )
                
                results[tile_id] = result
                
            except Exception as e:
                logger.error(f"Failed to process tile {tile_id}: {e}")
                # Continue with other tiles
                continue
        
        logger.info(f"Batch processing complete. Processed {len(results)}/{len(tile_data)} tiles successfully.")
        return results 