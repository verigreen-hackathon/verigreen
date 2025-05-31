"""Band data loading module for reading and preprocessing satellite imagery bands.

This module handles loading of NIR and RED band data from satellite imagery files,
with support for various formats, coordinate systems, cloud masking, and data validation.
"""

import logging
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
from dataclasses import dataclass
import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.mask import mask as rasterio_mask
import rasterio.features

logger = logging.getLogger(__name__)


@dataclass
class BandData:
    """Container for band data and metadata."""
    
    data: np.ndarray
    """The band data as a numpy array."""
    
    transform: rasterio.Affine
    """Geospatial transformation matrix."""
    
    crs: rasterio.CRS
    """Coordinate reference system."""
    
    nodata_value: Optional[float]
    """No-data value for the band."""
    
    scale_factor: float = 1.0
    """Scale factor to apply to the data."""
    
    offset: float = 0.0
    """Offset to apply to the data."""
    
    cloud_mask: Optional[np.ndarray] = None
    """Optional cloud mask (True = cloudy, False = clear)."""
    
    def get_scaled_data(self) -> np.ndarray:
        """Return data with scale factor and offset applied."""
        scaled_data = (self.data.astype(np.float64) * self.scale_factor) + self.offset
        
        # Apply no-data mask
        if self.nodata_value is not None:
            scaled_data = np.where(self.data == self.nodata_value, np.nan, scaled_data)
        
        # Apply cloud mask
        if self.cloud_mask is not None:
            scaled_data = np.where(self.cloud_mask, np.nan, scaled_data)
            
        return scaled_data


class BandLoader:
    """Loader for satellite imagery band data with preprocessing capabilities."""
    
    def __init__(self):
        """Initialize the band loader."""
        self.supported_formats = {'.tif', '.tiff', '.jp2', '.hdf', '.h5'}
        
    def load_band(
        self,
        file_path: str | Path,
        band_number: int = 1,
        scale_factor: float = 1.0,
        offset: float = 0.0,
        target_crs: Optional[str] = None,
        target_resolution: Optional[Tuple[float, float]] = None
    ) -> BandData:
        """Load a single band from a raster file.
        
        Args:
            file_path: Path to the raster file
            band_number: Band number to read (1-indexed)
            scale_factor: Scale factor for the data (e.g., 0.0001 for Sentinel-2 L2A)
            offset: Offset to apply to the data
            target_crs: Target CRS for reprojection (optional)
            target_resolution: Target resolution (x, y) in target CRS units (optional)
            
        Returns:
            BandData object containing the loaded band information
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file format is not supported or band number is invalid
            rasterio.errors.RasterioError: For rasterio-related errors
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Band file not found: {file_path}")
            
        if file_path.suffix.lower() not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
            
        logger.info(f"Loading band {band_number} from {file_path}")
        
        try:
            with rasterio.open(file_path) as src:
                # Validate band number
                if band_number < 1 or band_number > src.count:
                    raise ValueError(f"Invalid band number {band_number}. File has {src.count} bands.")
                
                # Read band data
                data = src.read(band_number)
                transform = src.transform
                crs = src.crs
                nodata_value = src.nodata
                
                logger.debug(f"Loaded band shape: {data.shape}, dtype: {data.dtype}")
                
                # Handle reprojection if needed
                if target_crs and str(crs) != target_crs:
                    data, transform = self._reproject_band(
                        data, src.transform, src.crs, target_crs, target_resolution
                    )
                    crs = rasterio.CRS.from_string(target_crs)
                
                return BandData(
                    data=data,
                    transform=transform,
                    crs=crs,
                    nodata_value=nodata_value,
                    scale_factor=scale_factor,
                    offset=offset
                )
                
        except rasterio.errors.RasterioError as e:
            logger.error(f"Error reading raster file {file_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error loading band from {file_path}: {e}")
            raise
    
    def load_sentinel2_bands(
        self,
        red_path: str | Path,
        nir_path: str | Path,
        cloud_mask_path: Optional[str | Path] = None
    ) -> Tuple[BandData, BandData]:
        """Load Sentinel-2 RED and NIR bands with appropriate preprocessing.
        
        Args:
            red_path: Path to RED band file (B04)
            nir_path: Path to NIR band file (B08)
            cloud_mask_path: Optional path to cloud mask file
            
        Returns:
            Tuple of (red_band_data, nir_band_data)
        """
        logger.info("Loading Sentinel-2 RED and NIR bands")
        
        # Sentinel-2 L2A scale factor (reflectance values are scaled by 10000)
        scale_factor = 0.0001
        
        # Load RED band (B04)
        red_band = self.load_band(red_path, scale_factor=scale_factor)
        
        # Load NIR band (B08)
        nir_band = self.load_band(nir_path, scale_factor=scale_factor)
        
        # Validate that bands have compatible dimensions and CRS
        self._validate_band_compatibility(red_band, nir_band)
        
        # Load cloud mask if provided
        if cloud_mask_path:
            cloud_mask = self._load_cloud_mask(cloud_mask_path, red_band.data.shape)
            red_band.cloud_mask = cloud_mask
            nir_band.cloud_mask = cloud_mask
        
        return red_band, nir_band
    
    def _reproject_band(
        self,
        data: np.ndarray,
        transform: rasterio.Affine,
        src_crs: rasterio.CRS,
        target_crs: str,
        target_resolution: Optional[Tuple[float, float]] = None
    ) -> Tuple[np.ndarray, rasterio.Affine]:
        """Reproject band data to target CRS."""
        logger.debug(f"Reprojecting from {src_crs} to {target_crs}")
        
        dst_crs = rasterio.CRS.from_string(target_crs)
        
        # Calculate target transform and dimensions
        if target_resolution:
            dst_width = int(np.ceil((transform.c - transform.f) / target_resolution[0]))
            dst_height = int(np.ceil((transform.f - transform.c) / target_resolution[1]))
            dst_transform = rasterio.Affine(
                target_resolution[0], 0.0, transform.c,
                0.0, -target_resolution[1], transform.f
            )
        else:
            dst_transform, dst_width, dst_height = calculate_default_transform(
                src_crs, dst_crs, data.shape[1], data.shape[0], *rasterio.transform.array_bounds(data.shape[0], data.shape[1], transform)
            )
        
        # Create destination array
        dst_data = np.empty((dst_height, dst_width), dtype=data.dtype)
        
        # Perform reprojection
        reproject(
            source=data,
            destination=dst_data,
            src_transform=transform,
            src_crs=src_crs,
            dst_transform=dst_transform,
            dst_crs=dst_crs,
            resampling=Resampling.bilinear
        )
        
        return dst_data, dst_transform
    
    def _load_cloud_mask(self, mask_path: str | Path, target_shape: Tuple[int, int]) -> np.ndarray:
        """Load and process cloud mask data."""
        logger.debug(f"Loading cloud mask from {mask_path}")
        
        try:
            with rasterio.open(mask_path) as src:
                mask_data = src.read(1)
                
                # Resize mask if needed to match target shape
                if mask_data.shape != target_shape:
                    logger.warning(f"Cloud mask shape {mask_data.shape} doesn't match band shape {target_shape}")
                    # For now, just resize. In production, might want to reproject properly
                    from scipy.ndimage import zoom
                    zoom_factors = (target_shape[0] / mask_data.shape[0], target_shape[1] / mask_data.shape[1])
                    mask_data = zoom(mask_data, zoom_factors, order=0) > 0  # Nearest neighbor, convert to boolean
                
                # Convert to boolean mask (True = cloudy)
                return mask_data.astype(bool)
                
        except Exception as e:
            logger.warning(f"Could not load cloud mask from {mask_path}: {e}")
            return None
    
    def _validate_band_compatibility(self, band1: BandData, band2: BandData) -> None:
        """Validate that two bands are compatible for processing."""
        if band1.data.shape != band2.data.shape:
            raise ValueError(f"Band shapes don't match: {band1.data.shape} vs {band2.data.shape}")
        
        if band1.crs != band2.crs:
            logger.warning(f"Band CRS don't match: {band1.crs} vs {band2.crs}")
        
        # Check if transforms are similar (allowing for small floating point differences)
        if not np.allclose(band1.transform[:6], band2.transform[:6], rtol=1e-10):
            logger.warning("Band transforms don't match exactly")
    
    def validate_file_integrity(self, file_path: str | Path) -> Dict[str, Any]:
        """Validate file integrity and return metadata.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            Dictionary containing file metadata and validation results
        """
        file_path = Path(file_path)
        
        result = {
            'file_path': str(file_path),
            'exists': file_path.exists(),
            'is_valid': False,
            'metadata': {},
            'errors': []
        }
        
        if not result['exists']:
            result['errors'].append(f"File does not exist: {file_path}")
            return result
        
        try:
            with rasterio.open(file_path) as src:
                result['metadata'] = {
                    'width': src.width,
                    'height': src.height,
                    'count': src.count,
                    'dtype': str(src.dtype),
                    'crs': str(src.crs) if src.crs else None,
                    'transform': list(src.transform),
                    'nodata': src.nodata,
                    'bounds': src.bounds
                }
                result['is_valid'] = True
                
        except Exception as e:
            result['errors'].append(f"Error reading file: {e}")
            
        return result 