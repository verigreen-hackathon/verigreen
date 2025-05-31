"""NDVI (Normalized Difference Vegetation Index) calculation module for VeriGreen.

This module provides functionality to calculate NDVI values from Sentinel-2 satellite imagery,
including band data loading, NDVI computation, statistical analysis, and threshold verification.
"""

from .band_loader import BandLoader, BandData
from .calculator import NDVICalculator, NDVIResult
from .statistics import NDVIStatistics
from .thresholds import ThresholdVerifier, VegetationClass

__all__ = [
    'BandLoader',
    'BandData', 
    'NDVICalculator',
    'NDVIResult',
    'NDVIStatistics',
    'ThresholdVerifier',
    'VegetationClass'
]

__version__ = '1.0.0' 