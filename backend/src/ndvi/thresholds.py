"""Threshold verification and classification module for NDVI data.

This module provides flexible threshold configuration, vegetation classification,
color map generation, and validation reporting for NDVI analysis.
"""

import logging
from typing import Optional, Dict, Any, List, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class VegetationClass(Enum):
    """Standard vegetation classification categories based on NDVI values."""
    WATER = "water"
    BARE_SOIL = "bare_soil"
    SPARSE_VEGETATION = "sparse_vegetation"
    MODERATE_VEGETATION = "moderate_vegetation"
    DENSE_VEGETATION = "dense_vegetation"
    VERY_DENSE_VEGETATION = "very_dense_vegetation"


@dataclass
class ThresholdDefinition:
    """Definition of a single threshold with associated properties."""
    
    name: str
    """Human-readable name for the threshold."""
    
    value: float
    """Threshold value (NDVI value between -1 and 1)."""
    
    vegetation_class: VegetationClass
    """Associated vegetation classification."""
    
    color: str = "#FFFFFF"
    """Hex color code for visualization."""
    
    description: str = ""
    """Optional description of what this threshold represents."""
    
    min_value: float = -1.0
    """Minimum NDVI value for this class (inclusive)."""
    
    max_value: float = 1.0
    """Maximum NDVI value for this class (exclusive, except for highest class)."""
    
    def __post_init__(self):
        """Validate threshold definition after creation."""
        if not (-1.0 <= self.value <= 1.0):
            raise ValueError(f"Threshold value {self.value} must be between -1 and 1")
        if not (-1.0 <= self.min_value <= 1.0):
            raise ValueError(f"Min value {self.min_value} must be between -1 and 1")
        if not (-1.0 <= self.max_value <= 1.0):
            raise ValueError(f"Max value {self.max_value} must be between -1 and 1")
        if self.min_value >= self.max_value:
            raise ValueError(f"Min value {self.min_value} must be less than max value {self.max_value}")


@dataclass
class ThresholdResult:
    """Result of threshold verification for NDVI data."""
    
    threshold_value: float
    """The threshold value that was applied."""
    
    passed: bool
    """Whether the data passes the threshold test."""
    
    pixels_above_threshold: int
    """Number of pixels above the threshold."""
    
    pixels_below_threshold: int
    """Number of pixels below the threshold."""
    
    percentage_above_threshold: float
    """Percentage of valid pixels above the threshold."""
    
    percentage_below_threshold: float
    """Percentage of valid pixels below the threshold."""
    
    mean_above_threshold: float
    """Mean NDVI value for pixels above threshold."""
    
    mean_below_threshold: float
    """Mean NDVI value for pixels below threshold."""
    
    total_valid_pixels: int
    """Total number of valid (non-NaN) pixels."""
    
    classification_map: Optional[np.ndarray] = None
    """Optional classification map array."""
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional metadata about the threshold verification."""


@dataclass
class ClassificationResult:
    """Result of vegetation classification based on multiple thresholds."""
    
    classification_map: np.ndarray
    """Array with vegetation class indices for each pixel."""
    
    class_statistics: Dict[VegetationClass, Dict[str, Any]]
    """Statistics for each vegetation class."""
    
    class_percentages: Dict[VegetationClass, float]
    """Percentage of pixels in each class."""
    
    dominant_class: VegetationClass
    """Most prevalent vegetation class."""
    
    total_valid_pixels: int
    """Total number of valid pixels classified."""
    
    threshold_definitions: List[ThresholdDefinition]
    """Threshold definitions used for classification."""


class ThresholdVerifier:
    """Flexible threshold verification and classification system for NDVI data."""
    
    def __init__(self):
        """Initialize the threshold verifier with default thresholds."""
        self.default_thresholds = self._create_default_thresholds()
        self.custom_thresholds = []
        
    def _create_default_thresholds(self) -> List[ThresholdDefinition]:
        """Create standard NDVI threshold definitions."""
        return [
            ThresholdDefinition(
                name="Water/Snow",
                value=-0.1,
                vegetation_class=VegetationClass.WATER,
                color="#0066CC",
                description="Water bodies, snow, ice, or built-up areas",
                min_value=-1.0,
                max_value=0.1
            ),
            ThresholdDefinition(
                name="Bare Soil",
                value=0.1,
                vegetation_class=VegetationClass.BARE_SOIL,
                color="#8B4513",
                description="Bare soil, rocks, urban areas",
                min_value=0.1,
                max_value=0.2
            ),
            ThresholdDefinition(
                name="Sparse Vegetation",
                value=0.2,
                vegetation_class=VegetationClass.SPARSE_VEGETATION,
                color="#FFD700",
                description="Sparse vegetation, grassland, crops in early growth",
                min_value=0.2,
                max_value=0.4
            ),
            ThresholdDefinition(
                name="Moderate Vegetation",
                value=0.4,
                vegetation_class=VegetationClass.MODERATE_VEGETATION,
                color="#9ACD32",
                description="Moderate vegetation density, healthy grassland",
                min_value=0.4,
                max_value=0.65
            ),
            ThresholdDefinition(
                name="Dense Vegetation",
                value=0.65,
                vegetation_class=VegetationClass.DENSE_VEGETATION,
                color="#228B22",
                description="Dense vegetation, healthy forests, crops at peak",
                min_value=0.65,
                max_value=0.8
            ),
            ThresholdDefinition(
                name="Very Dense Vegetation",
                value=0.8,
                vegetation_class=VegetationClass.VERY_DENSE_VEGETATION,
                color="#006400",
                description="Very dense vegetation, tropical forests",
                min_value=0.8,
                max_value=1.0
            )
        ]
    
    def verify_threshold(
        self,
        ndvi_array: np.ndarray,
        threshold: float,
        classification_method: str = "mean"
    ) -> ThresholdResult:
        """Verify NDVI data against a single threshold.
        
        Args:
            ndvi_array: Array of NDVI values
            threshold: Threshold value to test against
            classification_method: Method for determining pass/fail ('mean', 'percentage', 'median')
            
        Returns:
            ThresholdResult object with verification results
        """
        logger.debug(f"Verifying threshold {threshold} using method: {classification_method}")
        
        # Get valid pixels
        valid_mask = ~np.isnan(ndvi_array)
        valid_pixels = ndvi_array[valid_mask]
        total_valid_pixels = len(valid_pixels)
        
        if total_valid_pixels == 0:
            logger.warning("No valid pixels found for threshold verification")
            return self._empty_threshold_result(threshold)
        
        # Calculate threshold statistics
        above_mask = valid_pixels >= threshold
        below_mask = valid_pixels < threshold
        
        pixels_above = int(np.sum(above_mask))
        pixels_below = int(np.sum(below_mask))
        
        percentage_above = (pixels_above / total_valid_pixels * 100) if total_valid_pixels > 0 else 0.0
        percentage_below = (pixels_below / total_valid_pixels * 100) if total_valid_pixels > 0 else 0.0
        
        # Calculate means for pixels above/below threshold
        mean_above = float(np.mean(valid_pixels[above_mask])) if pixels_above > 0 else 0.0
        mean_below = float(np.mean(valid_pixels[below_mask])) if pixels_below > 0 else 0.0
        
        # Determine if threshold is passed based on classification method
        passed = self._determine_threshold_pass(
            valid_pixels, threshold, classification_method
        )
        
        # Create classification map
        classification_map = np.full_like(ndvi_array, -1, dtype=np.int8)  # -1 for invalid
        classification_map[valid_mask] = (ndvi_array[valid_mask] >= threshold).astype(np.int8)
        
        return ThresholdResult(
            threshold_value=threshold,
            passed=passed,
            pixels_above_threshold=pixels_above,
            pixels_below_threshold=pixels_below,
            percentage_above_threshold=percentage_above,
            percentage_below_threshold=percentage_below,
            mean_above_threshold=mean_above,
            mean_below_threshold=mean_below,
            total_valid_pixels=total_valid_pixels,
            classification_map=classification_map,
            metadata={
                'classification_method': classification_method,
                'threshold_type': 'single_threshold'
            }
        )
    
    def classify_vegetation(
        self,
        ndvi_array: np.ndarray,
        thresholds: Optional[List[ThresholdDefinition]] = None
    ) -> ClassificationResult:
        """Classify vegetation using multiple thresholds.
        
        Args:
            ndvi_array: Array of NDVI values
            thresholds: List of threshold definitions (uses defaults if None)
            
        Returns:
            ClassificationResult with vegetation classification
        """
        if thresholds is None:
            thresholds = self.default_thresholds
        
        logger.info(f"Classifying vegetation using {len(thresholds)} threshold classes")
        
        # Sort thresholds by value to ensure proper classification
        sorted_thresholds = sorted(thresholds, key=lambda x: x.min_value)
        
        # Initialize classification map
        classification_map = np.full_like(ndvi_array, -1, dtype=np.int8)  # -1 for invalid
        
        # Get valid pixels
        valid_mask = ~np.isnan(ndvi_array)
        total_valid_pixels = int(np.sum(valid_mask))
        
        if total_valid_pixels == 0:
            logger.warning("No valid pixels found for vegetation classification")
            return self._empty_classification_result(sorted_thresholds)
        
        # Classify each pixel
        for i, threshold_def in enumerate(sorted_thresholds):
            # Create mask for pixels in this class range
            class_mask = valid_mask & (ndvi_array >= threshold_def.min_value)
            
            # For the highest class, include the maximum value
            if i == len(sorted_thresholds) - 1:
                class_mask = class_mask & (ndvi_array <= threshold_def.max_value)
            else:
                class_mask = class_mask & (ndvi_array < threshold_def.max_value)
            
            classification_map[class_mask] = i
        
        # Calculate statistics for each class
        class_statistics = {}
        class_percentages = {}
        
        for i, threshold_def in enumerate(sorted_thresholds):
            class_mask = classification_map == i
            class_pixels = ndvi_array[class_mask]
            pixel_count = len(class_pixels)
            
            if pixel_count > 0:
                stats = {
                    'pixel_count': pixel_count,
                    'percentage': (pixel_count / total_valid_pixels * 100),
                    'mean_ndvi': float(np.mean(class_pixels)),
                    'std_ndvi': float(np.std(class_pixels)),
                    'min_ndvi': float(np.min(class_pixels)),
                    'max_ndvi': float(np.max(class_pixels))
                }
            else:
                stats = {
                    'pixel_count': 0,
                    'percentage': 0.0,
                    'mean_ndvi': 0.0,
                    'std_ndvi': 0.0,
                    'min_ndvi': 0.0,
                    'max_ndvi': 0.0
                }
            
            class_statistics[threshold_def.vegetation_class] = stats
            class_percentages[threshold_def.vegetation_class] = stats['percentage']
        
        # Determine dominant class
        dominant_class = max(class_percentages, key=class_percentages.get)
        
        return ClassificationResult(
            classification_map=classification_map,
            class_statistics=class_statistics,
            class_percentages=class_percentages,
            dominant_class=dominant_class,
            total_valid_pixels=total_valid_pixels,
            threshold_definitions=sorted_thresholds
        )
    
    def create_color_map(
        self,
        classification_result: ClassificationResult
    ) -> Dict[int, str]:
        """Create a color map for visualization based on classification results.
        
        Args:
            classification_result: Result from vegetation classification
            
        Returns:
            Dictionary mapping class indices to hex color codes
        """
        color_map = {-1: "#FFFFFF"}  # White for invalid/no-data pixels
        
        for i, threshold_def in enumerate(classification_result.threshold_definitions):
            color_map[i] = threshold_def.color
        
        return color_map
    
    def validate_thresholds(
        self,
        thresholds: List[ThresholdDefinition]
    ) -> Dict[str, Any]:
        """Validate a set of threshold definitions for consistency.
        
        Args:
            thresholds: List of threshold definitions to validate
            
        Returns:
            Dictionary with validation results and any errors found
        """
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        if not thresholds:
            validation_result['valid'] = False
            validation_result['errors'].append("No thresholds provided")
            return validation_result
        
        # Sort by min_value for validation
        sorted_thresholds = sorted(thresholds, key=lambda x: x.min_value)
        
        # Check for gaps and overlaps
        for i in range(len(sorted_thresholds) - 1):
            current = sorted_thresholds[i]
            next_threshold = sorted_thresholds[i + 1]
            
            # Check for gaps
            if current.max_value < next_threshold.min_value:
                validation_result['warnings'].append(
                    f"Gap between {current.name} (max: {current.max_value}) and "
                    f"{next_threshold.name} (min: {next_threshold.min_value})"
                )
            
            # Check for overlaps
            if current.max_value > next_threshold.min_value:
                validation_result['errors'].append(
                    f"Overlap between {current.name} and {next_threshold.name}"
                )
                validation_result['valid'] = False
        
        # Check coverage of NDVI range
        first_threshold = sorted_thresholds[0]
        last_threshold = sorted_thresholds[-1]
        
        if first_threshold.min_value > -1.0:
            validation_result['warnings'].append(
                f"NDVI range not fully covered: starts at {first_threshold.min_value} instead of -1.0"
            )
        
        if last_threshold.max_value < 1.0:
            validation_result['warnings'].append(
                f"NDVI range not fully covered: ends at {last_threshold.max_value} instead of 1.0"
            )
        
        return validation_result
    
    def _determine_threshold_pass(
        self,
        valid_pixels: np.ndarray,
        threshold: float,
        method: str
    ) -> bool:
        """Determine if data passes threshold based on specified method."""
        if method == "mean":
            return float(np.mean(valid_pixels)) >= threshold
        elif method == "median":
            return float(np.median(valid_pixels)) >= threshold
        elif method == "percentage":
            # Default: 50% of pixels must be above threshold
            percentage_above = np.sum(valid_pixels >= threshold) / len(valid_pixels) * 100
            return percentage_above >= 50.0
        else:
            logger.warning(f"Unknown classification method: {method}, using 'mean'")
            return float(np.mean(valid_pixels)) >= threshold
    
    def _empty_threshold_result(self, threshold: float) -> ThresholdResult:
        """Create empty threshold result for cases with no valid data."""
        return ThresholdResult(
            threshold_value=threshold,
            passed=False,
            pixels_above_threshold=0,
            pixels_below_threshold=0,
            percentage_above_threshold=0.0,
            percentage_below_threshold=0.0,
            mean_above_threshold=0.0,
            mean_below_threshold=0.0,
            total_valid_pixels=0,
            metadata={'no_valid_data': True}
        )
    
    def _empty_classification_result(
        self,
        thresholds: List[ThresholdDefinition]
    ) -> ClassificationResult:
        """Create empty classification result for cases with no valid data."""
        empty_stats = {}
        empty_percentages = {}
        
        for threshold_def in thresholds:
            empty_stats[threshold_def.vegetation_class] = {
                'pixel_count': 0,
                'percentage': 0.0,
                'mean_ndvi': 0.0,
                'std_ndvi': 0.0,
                'min_ndvi': 0.0,
                'max_ndvi': 0.0
            }
            empty_percentages[threshold_def.vegetation_class] = 0.0
        
        return ClassificationResult(
            classification_map=np.array([]),
            class_statistics=empty_stats,
            class_percentages=empty_percentages,
            dominant_class=VegetationClass.WATER,  # Default
            total_valid_pixels=0,
            threshold_definitions=thresholds
        ) 