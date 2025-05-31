"""Statistical analysis module for NDVI data.

This module provides comprehensive statistical analysis capabilities for NDVI arrays,
including descriptive statistics, spatial aggregation, histograms, and zonal statistics.
"""

import logging
from typing import Optional, Dict, Any, List, Tuple, Union
from dataclasses import dataclass
import numpy as np
from enum import Enum

logger = logging.getLogger(__name__)


class StatisticalMethod(Enum):
    """Enumeration of available statistical methods."""
    MEAN = "mean"
    MEDIAN = "median"
    STD = "std"
    VAR = "var"
    MIN = "min"
    MAX = "max"
    PERCENTILE = "percentile"
    MODE = "mode"
    SKEWNESS = "skewness"
    KURTOSIS = "kurtosis"


@dataclass
class NDVIStatisticalSummary:
    """Container for comprehensive NDVI statistical analysis."""
    
    # Basic descriptive statistics
    mean: float
    median: float
    std: float
    variance: float
    min_value: float
    max_value: float
    range_value: float
    
    # Distribution characteristics
    skewness: float
    kurtosis: float
    
    # Percentiles
    percentiles: Dict[int, float]
    quartiles: Dict[str, float]  # Q1, Q2, Q3, IQR
    
    # Count statistics
    total_pixels: int
    valid_pixels: int
    invalid_pixels: int
    valid_percentage: float
    
    # Histogram data
    histogram: Dict[str, Any]
    
    # Spatial statistics (if available)
    spatial_autocorrelation: Optional[float] = None
    spatial_variability: Optional[float] = None
    
    # Threshold analysis
    above_threshold_count: Optional[int] = None
    above_threshold_percentage: Optional[float] = None
    threshold_value: Optional[float] = None


@dataclass
class ZonalStatistics:
    """Container for zonal statistics (statistics within specific zones)."""
    
    zone_id: Union[int, str]
    zone_area_pixels: int
    statistics: NDVIStatisticalSummary
    zone_bounds: Optional[Tuple[float, float, float, float]] = None  # (minx, miny, maxx, maxy)


class NDVIStatistics:
    """Advanced statistical analysis for NDVI data."""
    
    def __init__(self):
        """Initialize the NDVI statistics calculator."""
        self.default_percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
        
    def calculate_comprehensive_statistics(
        self,
        ndvi_array: np.ndarray,
        threshold: Optional[float] = None,
        percentiles: Optional[List[int]] = None,
        include_spatial: bool = False
    ) -> NDVIStatisticalSummary:
        """Calculate comprehensive statistical summary for NDVI array.
        
        Args:
            ndvi_array: Array of NDVI values
            threshold: Optional threshold for binary classification analysis
            percentiles: List of percentile values to calculate (0-100)
            include_spatial: Whether to calculate spatial statistics
            
        Returns:
            NDVIStatisticalSummary object with comprehensive statistics
        """
        if percentiles is None:
            percentiles = self.default_percentiles
            
        logger.debug(f"Calculating comprehensive statistics for array shape: {ndvi_array.shape}")
        
        # Get valid (non-NaN) values
        valid_mask = ~np.isnan(ndvi_array)
        valid_values = ndvi_array[valid_mask]
        
        total_pixels = ndvi_array.size
        valid_pixels = len(valid_values)
        invalid_pixels = total_pixels - valid_pixels
        valid_percentage = (valid_pixels / total_pixels * 100) if total_pixels > 0 else 0.0
        
        if valid_pixels == 0:
            logger.warning("No valid pixels found in NDVI array")
            return self._empty_statistics_summary(total_pixels)
        
        # Basic descriptive statistics
        mean_val = float(np.mean(valid_values))
        median_val = float(np.median(valid_values))
        std_val = float(np.std(valid_values))
        var_val = float(np.var(valid_values))
        min_val = float(np.min(valid_values))
        max_val = float(np.max(valid_values))
        range_val = max_val - min_val
        
        # Distribution characteristics
        skewness_val = self._calculate_skewness(valid_values)
        kurtosis_val = self._calculate_kurtosis(valid_values)
        
        # Percentiles and quartiles
        percentile_values = {}
        for p in percentiles:
            percentile_values[p] = float(np.percentile(valid_values, p))
        
        quartiles = {
            'Q1': float(np.percentile(valid_values, 25)),
            'Q2': median_val,  # Q2 is the median
            'Q3': float(np.percentile(valid_values, 75)),
        }
        quartiles['IQR'] = quartiles['Q3'] - quartiles['Q1']
        
        # Histogram
        histogram = self._calculate_histogram(valid_values)
        
        # Threshold analysis
        above_threshold_count = None
        above_threshold_percentage = None
        if threshold is not None:
            above_threshold_count = int(np.sum(valid_values >= threshold))
            above_threshold_percentage = (above_threshold_count / valid_pixels * 100)
        
        # Spatial statistics (if requested)
        spatial_autocorr = None
        spatial_variability = None
        if include_spatial and ndvi_array.ndim == 2:
            spatial_autocorr = self._calculate_spatial_autocorrelation(ndvi_array)
            spatial_variability = self._calculate_spatial_variability(ndvi_array)
        
        return NDVIStatisticalSummary(
            mean=mean_val,
            median=median_val,
            std=std_val,
            variance=var_val,
            min_value=min_val,
            max_value=max_val,
            range_value=range_val,
            skewness=skewness_val,
            kurtosis=kurtosis_val,
            percentiles=percentile_values,
            quartiles=quartiles,
            total_pixels=total_pixels,
            valid_pixels=valid_pixels,
            invalid_pixels=invalid_pixels,
            valid_percentage=valid_percentage,
            histogram=histogram,
            spatial_autocorrelation=spatial_autocorr,
            spatial_variability=spatial_variability,
            above_threshold_count=above_threshold_count,
            above_threshold_percentage=above_threshold_percentage,
            threshold_value=threshold
        )
    
    def _empty_statistics_summary(self, total_pixels: int) -> NDVIStatisticalSummary:
        """Create an empty statistics summary for cases with no valid data."""
        return NDVIStatisticalSummary(
            mean=0.0, median=0.0, std=0.0, variance=0.0,
            min_value=0.0, max_value=0.0, range_value=0.0,
            skewness=0.0, kurtosis=0.0,
            percentiles={}, quartiles={},
            total_pixels=total_pixels, valid_pixels=0,
            invalid_pixels=total_pixels, valid_percentage=0.0,
            histogram={'bins': [], 'counts': [], 'bin_edges': []}
        )
    
    def _calculate_skewness(self, values: np.ndarray) -> float:
        """Calculate skewness of the distribution."""
        if len(values) < 3:
            return 0.0
        
        mean_val = np.mean(values)
        std_val = np.std(values)
        
        if std_val == 0:
            return 0.0
        
        # Third moment skewness formula
        skewness = np.mean(((values - mean_val) / std_val) ** 3)
        return float(skewness)
    
    def _calculate_kurtosis(self, values: np.ndarray) -> float:
        """Calculate kurtosis of the distribution."""
        if len(values) < 4:
            return 0.0
        
        mean_val = np.mean(values)
        std_val = np.std(values)
        
        if std_val == 0:
            return 0.0
        
        # Fourth moment kurtosis formula (excess kurtosis)
        kurtosis = np.mean(((values - mean_val) / std_val) ** 4) - 3
        return float(kurtosis)
    
    def _calculate_histogram(
        self, 
        values: np.ndarray, 
        bins: Union[int, str] = 'auto'
    ) -> Dict[str, Any]:
        """Calculate histogram for NDVI values."""
        try:
            counts, bin_edges = np.histogram(values, bins=bins)
            
            # Calculate bin centers
            bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
            
            return {
                'counts': counts.tolist(),
                'bin_edges': bin_edges.tolist(),
                'bin_centers': bin_centers.tolist(),
                'total_count': len(values),
                'bin_width': float(bin_edges[1] - bin_edges[0]) if len(bin_edges) > 1 else 0.0
            }
        except Exception as e:
            logger.warning(f"Failed to calculate histogram: {e}")
            return {'counts': [], 'bin_edges': [], 'bin_centers': []}
    
    def _calculate_spatial_autocorrelation(self, ndvi_array: np.ndarray) -> float:
        """Calculate spatial autocorrelation (Moran's I) for 2D NDVI array."""
        try:
            # Simple implementation using adjacent neighbors
            valid_mask = ~np.isnan(ndvi_array)
            if np.sum(valid_mask) < 10:  # Need sufficient valid pixels
                return 0.0
            
            # Calculate local spatial autocorrelation using 4-connectivity
            rows, cols = ndvi_array.shape
            total_pairs = 0
            sum_products = 0.0
            mean_val = np.nanmean(ndvi_array)
            
            for i in range(1, rows - 1):
                for j in range(1, cols - 1):
                    if valid_mask[i, j]:
                        center_val = ndvi_array[i, j] - mean_val
                        
                        # Check 4 neighbors
                        neighbors = [
                            (i-1, j), (i+1, j), (i, j-1), (i, j+1)
                        ]
                        
                        for ni, nj in neighbors:
                            if valid_mask[ni, nj]:
                                neighbor_val = ndvi_array[ni, nj] - mean_val
                                sum_products += center_val * neighbor_val
                                total_pairs += 1
            
            if total_pairs == 0:
                return 0.0
            
            # Simplified Moran's I calculation
            autocorr = sum_products / total_pairs
            variance = np.nanvar(ndvi_array)
            
            if variance > 0:
                autocorr = autocorr / variance
            
            return float(np.clip(autocorr, -1.0, 1.0))
            
        except Exception as e:
            logger.warning(f"Failed to calculate spatial autocorrelation: {e}")
            return 0.0
    
    def _calculate_spatial_variability(self, ndvi_array: np.ndarray) -> float:
        """Calculate spatial variability using coefficient of variation of local gradients."""
        try:
            # Calculate gradients in x and y directions
            grad_y, grad_x = np.gradient(ndvi_array)
            
            # Calculate magnitude of gradient at each pixel
            gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
            
            # Remove NaN values
            valid_gradients = gradient_magnitude[~np.isnan(gradient_magnitude)]
            
            if len(valid_gradients) == 0:
                return 0.0
            
            # Calculate coefficient of variation
            mean_grad = np.mean(valid_gradients)
            std_grad = np.std(valid_gradients)
            
            if mean_grad > 0:
                cv = std_grad / mean_grad
            else:
                cv = 0.0
            
            return float(cv)
            
        except Exception as e:
            logger.warning(f"Failed to calculate spatial variability: {e}")
            return 0.0 