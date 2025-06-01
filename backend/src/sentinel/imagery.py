"""Imagery data loading and validation module for Sentinel-2 data processing."""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import rasterio
import numpy as np
from rasterio.crs import CRS
from rasterio.errors import RasterioIOError

logger = logging.getLogger(__name__)


class ImageryError(Exception):
    """Custom exception for imagery processing errors."""
    pass


class ImageryValidator:
    """Validates geospatial imagery data for processing compatibility."""
    
    SUPPORTED_FORMATS = {'.tif', '.tiff', '.jp2', '.jpg', '.jpeg'}
    SENTINEL2_CRS = 'EPSG:32633'  # UTM Zone 33N for our area of interest
    MIN_RESOLUTION = 5.0  # Minimum resolution in meters
    MAX_RESOLUTION = 60.0  # Maximum resolution in meters
    
    @classmethod
    def validate_file_format(cls, file_path: Union[str, Path]) -> bool:
        """Validate that the file format is supported."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise ImageryError(f"File does not exist: {file_path}")
        
        suffix = file_path.suffix.lower()
        if suffix not in cls.SUPPORTED_FORMATS:
            raise ImageryError(
                f"Unsupported file format: {suffix}. "
                f"Supported formats: {', '.join(cls.SUPPORTED_FORMATS)}"
            )
        return True
    
    @classmethod
    def validate_crs(cls, dataset: rasterio.DatasetReader, expected_crs: Optional[str] = None) -> bool:
        """Validate the coordinate reference system of the dataset."""
        if expected_crs is None:
            expected_crs = cls.SENTINEL2_CRS
        
        if dataset.crs is None:
            raise ImageryError("Dataset has no coordinate reference system defined")
        
        # Convert to string for comparison
        dataset_crs = str(dataset.crs)
        if dataset_crs != expected_crs:
            logger.warning(
                f"CRS mismatch: expected {expected_crs}, got {dataset_crs}. "
                "Consider reprojecting the data."
            )
        return True
    
    @classmethod
    def validate_resolution(cls, dataset: rasterio.DatasetReader) -> bool:
        """Validate that the resolution is within acceptable bounds."""
        # Get pixel size (resolution) from transform
        transform = dataset.transform
        x_res = abs(transform[0])  # Pixel width
        y_res = abs(transform[4])  # Pixel height
        
        if x_res < cls.MIN_RESOLUTION or x_res > cls.MAX_RESOLUTION:
            raise ImageryError(
                f"X resolution {x_res}m is outside acceptable range "
                f"[{cls.MIN_RESOLUTION}, {cls.MAX_RESOLUTION}]"
            )
        
        if y_res < cls.MIN_RESOLUTION or y_res > cls.MAX_RESOLUTION:
            raise ImageryError(
                f"Y resolution {y_res}m is outside acceptable range "
                f"[{cls.MIN_RESOLUTION}, {cls.MAX_RESOLUTION}]"
            )
        
        logger.info(f"Dataset resolution: {x_res}m x {y_res}m")
        return True
    
    @classmethod
    def validate_data_integrity(cls, dataset: rasterio.DatasetReader) -> bool:
        """Validate data integrity and check for common issues."""
        # Check dimensions
        if dataset.width == 0 or dataset.height == 0:
            raise ImageryError("Dataset has zero width or height")
        
        # Check for bands
        if dataset.count == 0:
            raise ImageryError("Dataset has no bands")
        
        # Sample a small window to check for data
        try:
            # Read a small 100x100 window from the center
            center_x = dataset.width // 2
            center_y = dataset.height // 2
            window_size = min(100, dataset.width // 4, dataset.height // 4)
            
            window = rasterio.windows.Window(
                center_x - window_size // 2,
                center_y - window_size // 2,
                window_size,
                window_size
            )
            
            sample_data = dataset.read(1, window=window)
            
            # Check if all values are nodata
            if dataset.nodata is not None:
                valid_pixels = np.sum(sample_data != dataset.nodata)
                if valid_pixels == 0:
                    logger.warning("Sample region contains only nodata values")
            
        except Exception as e:
            raise ImageryError(f"Failed to read sample data: {str(e)}")
        
        return True


class ImageryLoader:
    """Loads and manages geospatial imagery data from various sources."""
    
    def __init__(self, validate: bool = True):
        """
        Initialize the imagery loader.
        
        Args:
            validate: Whether to perform validation checks on loaded imagery
        """
        self.validate = validate
        self.validator = ImageryValidator()
    
    def load_imagery(self, file_path: Union[str, Path]) -> Dict:
        """
        Load imagery data from a file with validation and metadata extraction.
        
        Args:
            file_path: Path to the imagery file
            
        Returns:
            Dictionary containing imagery metadata and dataset reference
            
        Raises:
            ImageryError: If file cannot be loaded or validation fails
        """
        file_path = Path(file_path)
        
        if self.validate:
            self.validator.validate_file_format(file_path)
        
        try:
            dataset = rasterio.open(file_path)
        except RasterioIOError as e:
            raise ImageryError(f"Failed to open imagery file: {str(e)}")
        
        if self.validate:
            self.validator.validate_crs(dataset)
            self.validator.validate_resolution(dataset)
            self.validator.validate_data_integrity(dataset)
        
        # Extract metadata
        metadata = {
            'file_path': str(file_path),
            'width': dataset.width,
            'height': dataset.height,
            'count': dataset.count,
            'dtype': str(dataset.dtypes[0]),
            'crs': str(dataset.crs) if dataset.crs else None,
            'bounds': dataset.bounds,
            'transform': dataset.transform,
            'nodata': dataset.nodata,
            'resolution': {
                'x': abs(dataset.transform[0]),
                'y': abs(dataset.transform[4])
            },
            'dataset': dataset  # Keep reference for further processing
        }
        
        logger.info(f"Loaded imagery: {file_path.name} ({dataset.width}x{dataset.height}, {dataset.count} bands)")
        
        return metadata
    
    def load_sentinel2_bands(self, data_dir: Union[str, Path], required_bands: List[str] = None) -> Dict:
        """
        Load specific Sentinel-2 bands from a directory.
        
        Args:
            data_dir: Directory containing Sentinel-2 band files
            required_bands: List of required band identifiers (e.g., ['B04', 'B08'])
            
        Returns:
            Dictionary mapping band names to their metadata
            
        Raises:
            ImageryError: If required bands are missing or cannot be loaded
        """
        if required_bands is None:
            required_bands = ['B04', 'B08']  # Red and NIR bands for NDVI
        
        data_dir = Path(data_dir)
        if not data_dir.exists():
            raise ImageryError(f"Data directory does not exist: {data_dir}")
        
        bands_data = {}
        
        for band in required_bands:
            # Look for band files with common naming patterns
            band_patterns = [
                f"*{band}*.tif",
                f"*{band}*.jp2",
                f"*{band}_10m.jp2",  # Sentinel-2 L2A naming
                f"*{band}_10m.tif"
            ]
            
            band_file = None
            for pattern in band_patterns:
                matching_files = list(data_dir.glob(pattern))
                if matching_files:
                    band_file = matching_files[0]
                    break
            
            if band_file is None:
                raise ImageryError(f"Could not find band {band} in directory {data_dir}")
            
            try:
                band_metadata = self.load_imagery(band_file)
                bands_data[band] = band_metadata
                logger.info(f"Loaded band {band}: {band_file.name}")
            except Exception as e:
                raise ImageryError(f"Failed to load band {band} from {band_file}: {str(e)}")
        
        # Validate that all bands have consistent properties
        self._validate_band_consistency(bands_data)
        
        return bands_data
    
    def _validate_band_consistency(self, bands_data: Dict) -> None:
        """Validate that all loaded bands have consistent properties."""
        if not bands_data:
            return
        
        reference_band = next(iter(bands_data.values()))
        ref_width = reference_band['width']
        ref_height = reference_band['height']
        ref_crs = reference_band['crs']
        ref_bounds = reference_band['bounds']
        
        for band_name, band_data in bands_data.items():
            if band_data['width'] != ref_width or band_data['height'] != ref_height:
                raise ImageryError(
                    f"Band {band_name} dimensions ({band_data['width']}x{band_data['height']}) "
                    f"do not match reference ({ref_width}x{ref_height})"
                )
            
            if band_data['crs'] != ref_crs:
                raise ImageryError(
                    f"Band {band_name} CRS ({band_data['crs']}) "
                    f"does not match reference ({ref_crs})"
                )
            
            # Check bounds are approximately equal (within small tolerance)
            bounds_diff = max(abs(a - b) for a, b in zip(band_data['bounds'], ref_bounds))
            if bounds_diff > 1.0:  # 1 meter tolerance
                raise ImageryError(
                    f"Band {band_name} bounds differ significantly from reference"
                )
    
    def close_datasets(self, bands_data: Dict) -> None:
        """Close all dataset references to free resources."""
        for band_data in bands_data.values():
            if 'dataset' in band_data and band_data['dataset']:
                band_data['dataset'].close()
                band_data['dataset'] = None
        logger.info("Closed all dataset references")


def load_imagery_safely(file_path: Union[str, Path], **kwargs) -> Optional[Dict]:
    """
    Safely load imagery with error handling.
    
    Args:
        file_path: Path to the imagery file
        **kwargs: Additional arguments for ImageryLoader
        
    Returns:
        Imagery metadata dictionary or None if loading fails
    """
    try:
        loader = ImageryLoader(**kwargs)
        return loader.load_imagery(file_path)
    except ImageryError as e:
        logger.error(f"Failed to load imagery {file_path}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error loading imagery {file_path}: {str(e)}")
        return None 