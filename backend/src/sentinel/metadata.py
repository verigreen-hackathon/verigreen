"""Metadata generation system for satellite imagery tiles."""

import logging
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, asdict
import rasterio
from rasterio.coords import BoundingBox
from rasterio.crs import CRS

from .grid import TileCoordinates
from .slicer import TileData

logger = logging.getLogger(__name__)


class MetadataError(Exception):
    """Custom exception for metadata generation errors."""
    pass


@dataclass
class SourceImageryMetadata:
    """Metadata about the source imagery from which tiles are derived."""
    file_path: str
    acquisition_date: Optional[str] = None
    satellite: Optional[str] = None
    instrument: Optional[str] = None
    processing_level: Optional[str] = None
    cloud_coverage: Optional[float] = None
    sun_azimuth: Optional[float] = None
    sun_elevation: Optional[float] = None
    spatial_resolution: Optional[float] = None
    crs: Optional[str] = None
    bounds: Optional[List[float]] = None  # [minx, miny, maxx, maxy]
    data_type: Optional[str] = None
    nodata_value: Optional[Union[int, float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return asdict(self)


@dataclass
class TileMetadata:
    """Comprehensive metadata for a single tile."""
    # Tile identification
    tile_id: str
    unique_id: str  # UUID for global uniqueness
    grid_position: Dict[str, int]  # {'x': grid_x, 'y': grid_y}
    
    # Spatial information
    crs: str
    bounds: List[float]  # [minx, miny, maxx, maxy]
    center_coordinates: List[float]  # [lat, lon]
    pixel_bounds: List[int]  # [left, top, right, bottom] in source image
    
    # Tile properties
    width: int
    height: int
    data_type: str
    bands: List[str]
    nodata_value: Optional[Union[int, float]]
    
    # Processing information
    created_at: str  # ISO 8601 timestamp
    processing_software: str
    processing_version: str
    source_imagery: SourceImageryMetadata
    
    # Statistics (optional)
    statistics: Optional[Dict[str, Any]] = None
    
    # Quality metrics (optional)
    quality_flags: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        result = asdict(self)
        # Convert source_imagery to dict if it's a dataclass
        if isinstance(result['source_imagery'], SourceImageryMetadata):
            result['source_imagery'] = result['source_imagery'].to_dict()
        return result
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    def to_geospatial_tags(self) -> Dict[str, str]:
        """Convert to tags suitable for GeoTIFF metadata."""
        return {
            'TILE_ID': self.tile_id,
            'UNIQUE_ID': self.unique_id,
            'GRID_X': str(self.grid_position['x']),
            'GRID_Y': str(self.grid_position['y']),
            'CENTER_LAT': str(self.center_coordinates[0]),
            'CENTER_LON': str(self.center_coordinates[1]),
            'CREATED_AT': self.created_at,
            'PROCESSING_SOFTWARE': self.processing_software,
            'SOURCE_FILE': self.source_imagery.file_path,
            'BANDS': ','.join(self.bands),
            'CRS': self.crs
        }


class MetadataGenerator:
    """Generates comprehensive metadata for satellite imagery tiles."""
    
    def __init__(
        self,
        processing_software: str = "VeriGreen",
        processing_version: str = "1.0.0",
        include_statistics: bool = True,
        include_quality_flags: bool = False
    ):
        """
        Initialize metadata generator.
        
        Args:
            processing_software: Name of the processing software
            processing_version: Version of the processing software
            include_statistics: Whether to include tile statistics in metadata
            include_quality_flags: Whether to include quality assessment flags
        """
        self.processing_software = processing_software
        self.processing_version = processing_version
        self.include_statistics = include_statistics
        self.include_quality_flags = include_quality_flags
        
        logger.info(f"Initialized metadata generator: {processing_software} v{processing_version}")
    
    def generate_tile_metadata(
        self,
        tile_data: TileData,
        source_metadata: Dict,
        source_imagery_info: Optional[SourceImageryMetadata] = None
    ) -> TileMetadata:
        """
        Generate comprehensive metadata for a single tile.
        
        Args:
            tile_data: TileData object containing the tile information
            source_metadata: Metadata from the source imagery
            source_imagery_info: Optional detailed source imagery metadata
            
        Returns:
            TileMetadata object with complete metadata
            
        Raises:
            MetadataError: If metadata generation fails
        """
        try:
            # Extract tile coordinates
            coords = tile_data.coordinates
            
            # Generate unique identifier
            unique_id = str(uuid.uuid4())
            
            # Get current timestamp
            created_at = datetime.now(timezone.utc).isoformat()
            
            # Process source imagery metadata
            if source_imagery_info is None:
                source_imagery_info = self._extract_source_metadata(source_metadata)
            
            # Calculate bounds as list
            bounds = [
                coords.geo_bounds.left,
                coords.geo_bounds.bottom,
                coords.geo_bounds.right,
                coords.geo_bounds.top
            ]
            
            # Calculate pixel bounds as list
            pixel_bounds = list(coords.pixel_bounds)
            
            # Get data type
            data_type = str(tile_data.data.dtype)
            
            # Get bands information
            bands = tile_data.bands if tile_data.bands else ['band_1']
            
            # Get nodata value
            nodata_value = source_metadata.get('nodata')
            
            # Create base metadata
            metadata = TileMetadata(
                tile_id=coords.tile_id,
                unique_id=unique_id,
                grid_position={'x': coords.grid_x, 'y': coords.grid_y},
                crs=source_metadata.get('crs', 'EPSG:4326'),
                bounds=bounds,
                center_coordinates=list(coords.center_lat_lon),
                pixel_bounds=pixel_bounds,
                width=tile_data.width,
                height=tile_data.height,
                data_type=data_type,
                bands=bands,
                nodata_value=nodata_value,
                created_at=created_at,
                processing_software=self.processing_software,
                processing_version=self.processing_version,
                source_imagery=source_imagery_info
            )
            
            # Add statistics if requested
            if self.include_statistics:
                try:
                    statistics = tile_data.calculate_statistics()
                    metadata.statistics = statistics
                except Exception as e:
                    logger.warning(f"Failed to calculate statistics for tile {coords.tile_id}: {e}")
            
            # Add quality flags if requested
            if self.include_quality_flags:
                try:
                    quality_flags = self._assess_tile_quality(tile_data)
                    metadata.quality_flags = quality_flags
                except Exception as e:
                    logger.warning(f"Failed to assess quality for tile {coords.tile_id}: {e}")
            
            logger.debug(f"Generated metadata for tile {coords.tile_id}")
            return metadata
            
        except Exception as e:
            raise MetadataError(f"Failed to generate metadata for tile: {str(e)}")
    
    def generate_batch_metadata(
        self,
        tiles: List[TileData],
        source_metadata: Dict,
        source_imagery_info: Optional[SourceImageryMetadata] = None
    ) -> List[TileMetadata]:
        """
        Generate metadata for multiple tiles in batch.
        
        Args:
            tiles: List of TileData objects
            source_metadata: Metadata from the source imagery
            source_imagery_info: Optional detailed source imagery metadata
            
        Returns:
            List of TileMetadata objects
            
        Raises:
            MetadataError: If batch metadata generation fails
        """
        metadata_list = []
        failed_tiles = []
        
        for tile_data in tiles:
            try:
                tile_metadata = self.generate_tile_metadata(
                    tile_data, source_metadata, source_imagery_info
                )
                metadata_list.append(tile_metadata)
            except Exception as e:
                failed_tiles.append(tile_data.tile_id)
                logger.error(f"Failed to generate metadata for tile {tile_data.tile_id}: {e}")
        
        if failed_tiles:
            logger.warning(f"Failed to generate metadata for {len(failed_tiles)} tiles: {failed_tiles}")
        
        logger.info(f"Generated metadata for {len(metadata_list)} tiles")
        return metadata_list
    
    def _extract_source_metadata(self, source_metadata: Dict) -> SourceImageryMetadata:
        """Extract source imagery metadata from source metadata dictionary."""
        # Convert bounds to list if it's a BoundingBox
        bounds = source_metadata.get('bounds')
        if isinstance(bounds, BoundingBox):
            bounds = [bounds.left, bounds.bottom, bounds.right, bounds.top]
        elif bounds is not None:
            bounds = list(bounds)
        
        # Extract resolution information
        resolution = source_metadata.get('resolution', {})
        spatial_resolution = None
        if isinstance(resolution, dict):
            # Use average of x and y resolution
            x_res = resolution.get('x')
            y_res = resolution.get('y')
            if x_res and y_res:
                spatial_resolution = (x_res + y_res) / 2
        elif isinstance(resolution, (int, float)):
            spatial_resolution = resolution
        
        return SourceImageryMetadata(
            file_path=source_metadata.get('file_path', ''),
            spatial_resolution=spatial_resolution,
            crs=source_metadata.get('crs'),
            bounds=bounds,
            data_type=source_metadata.get('dtype'),
            nodata_value=source_metadata.get('nodata')
        )
    
    def _assess_tile_quality(self, tile_data: TileData) -> Dict[str, Any]:
        """Assess quality metrics for a tile."""
        quality_flags = {
            'has_data': True,
            'data_completeness': 1.0,
            'nodata_percentage': 0.0,
            'data_range_valid': True
        }
        
        try:
            # Check for nodata pixels
            if tile_data.data.size > 0:
                nodata_count = 0
                total_pixels = tile_data.data.size
                
                # Check for common nodata values
                nodata_values = [0, -9999, -32768, 65535]
                for nodata_val in nodata_values:
                    nodata_count += (tile_data.data == nodata_val).sum()
                
                nodata_percentage = (nodata_count / total_pixels) * 100
                quality_flags['nodata_percentage'] = float(nodata_percentage)
                quality_flags['data_completeness'] = float((total_pixels - nodata_count) / total_pixels)
                quality_flags['has_data'] = nodata_count < total_pixels
                
                # Check data range validity (for typical satellite imagery)
                if tile_data.data.dtype in ['uint8', 'uint16']:
                    valid_data = tile_data.data[tile_data.data > 0]
                    if len(valid_data) > 0:
                        min_val = float(valid_data.min())
                        max_val = float(valid_data.max())
                        
                        # For 16-bit imagery, expect values in reasonable range
                        if tile_data.data.dtype == 'uint16':
                            quality_flags['data_range_valid'] = 0 < min_val < 15000 and max_val < 65000
                        else:
                            quality_flags['data_range_valid'] = 0 < min_val < 250 and max_val <= 255
            else:
                quality_flags['has_data'] = False
                quality_flags['data_completeness'] = 0.0
                
        except Exception as e:
            logger.warning(f"Quality assessment failed: {e}")
            quality_flags['assessment_error'] = str(e)
        
        return quality_flags
    
    def save_metadata_json(
        self,
        metadata: Union[TileMetadata, List[TileMetadata]],
        output_path: Union[str, Path]
    ) -> Path:
        """
        Save metadata to JSON file.
        
        Args:
            metadata: Single metadata object or list of metadata objects
            output_path: Path where to save the JSON file
            
        Returns:
            Path to the saved file
            
        Raises:
            MetadataError: If saving fails
        """
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if isinstance(metadata, list):
                data = [meta.to_dict() for meta in metadata]
            else:
                data = metadata.to_dict()
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved metadata to {output_path}")
            return output_path
            
        except Exception as e:
            raise MetadataError(f"Failed to save metadata to {output_path}: {str(e)}")
    
    def create_collection_metadata(
        self,
        tiles_metadata: List[TileMetadata],
        collection_name: str = "VeriGreen Tiles"
    ) -> Dict[str, Any]:
        """
        Create collection-level metadata for a set of tiles.
        
        Args:
            tiles_metadata: List of tile metadata objects
            collection_name: Name for the tile collection
            
        Returns:
            Dictionary containing collection metadata
        """
        if not tiles_metadata:
            return {}
        
        # Calculate overall bounds
        all_bounds = [meta.bounds for meta in tiles_metadata]
        min_x = min(bounds[0] for bounds in all_bounds)
        min_y = min(bounds[1] for bounds in all_bounds)
        max_x = max(bounds[2] for bounds in all_bounds)
        max_y = max(bounds[3] for bounds in all_bounds)
        
        # Get common properties
        first_tile = tiles_metadata[0]
        crs = first_tile.crs
        
        # Calculate grid extent
        grid_positions = [meta.grid_position for meta in tiles_metadata]
        min_grid_x = min(pos['x'] for pos in grid_positions)
        max_grid_x = max(pos['x'] for pos in grid_positions)
        min_grid_y = min(pos['y'] for pos in grid_positions)
        max_grid_y = max(pos['y'] for pos in grid_positions)
        
        # Get all unique bands
        all_bands = set()
        for meta in tiles_metadata:
            all_bands.update(meta.bands)
        
        collection_metadata = {
            'collection_name': collection_name,
            'tile_count': len(tiles_metadata),
            'created_at': datetime.now(timezone.utc).isoformat(),
            'spatial_extent': {
                'bounds': [min_x, min_y, max_x, max_y],
                'crs': crs
            },
            'grid_extent': {
                'x_range': [min_grid_x, max_grid_x],
                'y_range': [min_grid_y, max_grid_y],
                'grid_size': [max_grid_x - min_grid_x + 1, max_grid_y - min_grid_y + 1]
            },
            'bands': sorted(list(all_bands)),
            'tile_size': {
                'width': first_tile.width,
                'height': first_tile.height
            },
            'data_type': first_tile.data_type,
            'processing_info': {
                'software': first_tile.processing_software,
                'version': first_tile.processing_version
            },
            'source_imagery': first_tile.source_imagery.to_dict(),
            'tiles': [meta.to_dict() for meta in tiles_metadata]
        }
        
        return collection_metadata


def create_source_imagery_metadata(
    file_path: Union[str, Path],
    acquisition_date: Optional[str] = None,
    satellite: Optional[str] = None,
    **kwargs
) -> SourceImageryMetadata:
    """
    Create SourceImageryMetadata from file and optional parameters.
    
    Args:
        file_path: Path to the source imagery file
        acquisition_date: ISO 8601 date string
        satellite: Satellite name (e.g., "Sentinel-2A")
        **kwargs: Additional metadata fields
        
    Returns:
        SourceImageryMetadata object
    """
    # Try to extract metadata from file if it's a real file
    file_path = str(file_path)
    
    metadata = SourceImageryMetadata(
        file_path=file_path,
        acquisition_date=acquisition_date,
        satellite=satellite
    )
    
    # Update with any additional kwargs
    for key, value in kwargs.items():
        if hasattr(metadata, key):
            setattr(metadata, key, value)
    
    return metadata


def generate_tile_metadata(
    tile_data: TileData,
    source_metadata: Dict,
    **kwargs
) -> TileMetadata:
    """
    Convenience function to generate metadata for a single tile.
    
    Args:
        tile_data: TileData object
        source_metadata: Source imagery metadata dictionary
        **kwargs: Additional options for MetadataGenerator
        
    Returns:
        TileMetadata object
    """
    generator = MetadataGenerator(**kwargs)
    return generator.generate_tile_metadata(tile_data, source_metadata) 