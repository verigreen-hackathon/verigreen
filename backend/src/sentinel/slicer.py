"""Core slicing algorithm for extracting tiles from Sentinel-2 imagery."""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import rasterio
from rasterio.windows import Window
from rasterio.transform import from_bounds
from rasterio.coords import BoundingBox

from .imagery import ImageryLoader, ImageryError
from .grid import GridCalculator, TileCoordinates, GridError

logger = logging.getLogger(__name__)


class SlicingError(Exception):
    """Custom exception for slicing operation errors."""
    pass


class TileData:
    """Container for tile data and metadata."""
    
    def __init__(
        self, 
        coordinates: TileCoordinates, 
        data: np.ndarray, 
        metadata: Dict,
        bands: Optional[List[str]] = None
    ):
        """
        Initialize tile data container.
        
        Args:
            coordinates: TileCoordinates object with spatial information
            data: Numpy array containing the tile pixel data
            metadata: Dictionary with tile metadata
            bands: List of band names if multi-band data
        """
        self.coordinates = coordinates
        self.data = data
        self.metadata = metadata
        self.bands = bands or []
        
        # Validate data dimensions
        if data.ndim not in [2, 3]:
            raise SlicingError(f"Tile data must be 2D or 3D array, got {data.ndim}D")
        
        # For 3D data, first dimension should be bands
        if data.ndim == 3:
            self.num_bands, self.height, self.width = data.shape
        else:
            self.num_bands = 1
            self.height, self.width = data.shape
    
    @property
    def tile_id(self) -> str:
        """Get the tile ID."""
        return self.coordinates.tile_id
    
    @property
    def shape(self) -> Tuple[int, ...]:
        """Get the shape of the tile data."""
        return self.data.shape
    
    @property
    def size_bytes(self) -> int:
        """Get the size of the tile data in bytes."""
        return self.data.nbytes
    
    def get_band_data(self, band_index: int = 0) -> np.ndarray:
        """
        Get data for a specific band.
        
        Args:
            band_index: Index of the band to retrieve (0-based)
            
        Returns:
            2D numpy array with band data
        """
        if self.data.ndim == 2:
            if band_index != 0:
                raise SlicingError(f"Single band data, requested band {band_index}")
            return self.data
        else:
            if band_index >= self.num_bands:
                raise SlicingError(f"Band index {band_index} out of range (0-{self.num_bands-1})")
            return self.data[band_index]
    
    def calculate_statistics(self) -> Dict:
        """Calculate basic statistics for the tile data."""
        stats = {}
        
        if self.data.ndim == 2:
            # Single band
            valid_data = self.data[self.data != 0]  # Exclude nodata (assuming 0)
            if len(valid_data) > 0:
                stats['single_band'] = {
                    'min': float(np.min(valid_data)),
                    'max': float(np.max(valid_data)),
                    'mean': float(np.mean(valid_data)),
                    'std': float(np.std(valid_data)),
                    'valid_pixels': len(valid_data),
                    'total_pixels': self.data.size
                }
        else:
            # Multi-band
            for i in range(self.num_bands):
                band_data = self.data[i]
                valid_data = band_data[band_data != 0]
                band_name = self.bands[i] if i < len(self.bands) else f'band_{i}'
                
                if len(valid_data) > 0:
                    stats[band_name] = {
                        'min': float(np.min(valid_data)),
                        'max': float(np.max(valid_data)),
                        'mean': float(np.mean(valid_data)),
                        'std': float(np.std(valid_data)),
                        'valid_pixels': len(valid_data),
                        'total_pixels': band_data.size
                    }
        
        return stats


class ImageSlicer:
    """Main class for slicing imagery into tiles."""
    
    def __init__(
        self, 
        grid_size: int = 32, 
        tile_size: int = 32,
        output_dir: Optional[Union[str, Path]] = None,
        preserve_nodata: bool = True
    ):
        """
        Initialize the image slicer.
        
        Args:
            grid_size: Number of tiles per side (e.g., 32 for 32x32 grid)
            tile_size: Size of each tile in pixels (e.g., 32 for 32x32 pixel tiles)
            output_dir: Directory to save sliced tiles (optional)
            preserve_nodata: Whether to preserve nodata values in output tiles
        """
        self.grid_calculator = GridCalculator(grid_size, tile_size)
        self.imagery_loader = ImageryLoader(validate=True)
        self.output_dir = Path(output_dir) if output_dir else None
        self.preserve_nodata = preserve_nodata
        
        if self.output_dir:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Output directory: {self.output_dir}")
        
        logger.info(f"Initialized image slicer: {grid_size}x{grid_size} grid, {tile_size}x{tile_size} pixel tiles")
    
    def slice_imagery(
        self, 
        imagery_path: Union[str, Path], 
        bands: Optional[List[str]] = None
    ) -> List[TileData]:
        """
        Slice a single imagery file into tiles.
        
        Args:
            imagery_path: Path to the imagery file
            bands: List of band names for metadata (optional)
            
        Returns:
            List of TileData objects containing the sliced tiles
            
        Raises:
            SlicingError: If slicing fails
        """
        try:
            # Load imagery metadata
            imagery_metadata = self.imagery_loader.load_imagery(imagery_path)
            logger.info(f"Loaded imagery: {imagery_path}")
            
            # Calculate tile coordinates
            tile_coordinates = self.grid_calculator.calculate_tile_bounds(imagery_metadata)
            logger.info(f"Calculated {len(tile_coordinates)} tile coordinates")
            
            # Extract tiles
            tiles = []
            dataset = imagery_metadata['dataset']
            
            for coords in tile_coordinates:
                try:
                    tile_data = self._extract_single_tile(dataset, coords, imagery_metadata, bands)
                    tiles.append(tile_data)
                except Exception as e:
                    logger.warning(f"Failed to extract tile {coords.tile_id}: {str(e)}")
                    continue
            
            logger.info(f"Successfully extracted {len(tiles)} tiles")
            
            # Close the dataset
            dataset.close()
            
            return tiles
            
        except Exception as e:
            raise SlicingError(f"Failed to slice imagery {imagery_path}: {str(e)}")
    
    def slice_sentinel2_bands(
        self, 
        data_dir: Union[str, Path], 
        required_bands: List[str] = None
    ) -> Dict[str, List[TileData]]:
        """
        Slice multiple Sentinel-2 bands from a directory.
        
        Args:
            data_dir: Directory containing Sentinel-2 band files
            required_bands: List of required band identifiers (e.g., ['B04', 'B08'])
            
        Returns:
            Dictionary mapping band names to their list of TileData objects
            
        Raises:
            SlicingError: If slicing fails
        """
        if required_bands is None:
            required_bands = ['B04', 'B08']  # Red and NIR bands for NDVI
        
        try:
            # Load all bands
            bands_metadata = self.imagery_loader.load_sentinel2_bands(data_dir, required_bands)
            logger.info(f"Loaded {len(bands_metadata)} bands from {data_dir}")
            
            # Slice each band
            band_tiles = {}
            for band_name, band_metadata in bands_metadata.items():
                logger.info(f"Slicing band {band_name}")
                
                # Calculate tile coordinates (should be same for all bands)
                tile_coordinates = self.grid_calculator.calculate_tile_bounds(band_metadata)
                
                # Extract tiles for this band
                tiles = []
                dataset = band_metadata['dataset']
                
                for coords in tile_coordinates:
                    try:
                        tile_data = self._extract_single_tile(
                            dataset, coords, band_metadata, [band_name]
                        )
                        tiles.append(tile_data)
                    except Exception as e:
                        logger.warning(f"Failed to extract tile {coords.tile_id} from band {band_name}: {str(e)}")
                        continue
                
                band_tiles[band_name] = tiles
                dataset.close()
                
                logger.info(f"Extracted {len(tiles)} tiles from band {band_name}")
            
            # Close all datasets
            self.imagery_loader.close_datasets(bands_metadata)
            
            return band_tiles
            
        except Exception as e:
            raise SlicingError(f"Failed to slice Sentinel-2 bands from {data_dir}: {str(e)}")
    
    def _extract_single_tile(
        self, 
        dataset: rasterio.DatasetReader, 
        coordinates: TileCoordinates,
        imagery_metadata: Dict,
        bands: Optional[List[str]] = None
    ) -> TileData:
        """
        Extract a single tile from the dataset.
        
        Args:
            dataset: Open rasterio dataset
            coordinates: TileCoordinates for the tile to extract
            imagery_metadata: Metadata from the source imagery
            bands: List of band names for metadata
            
        Returns:
            TileData object containing the extracted tile
            
        Raises:
            SlicingError: If extraction fails
        """
        try:
            # Get pixel bounds
            left, top, right, bottom = coordinates.pixel_bounds
            
            # Create rasterio window
            window = Window(left, top, right - left, bottom - top)
            
            # Read data from the window
            tile_array = dataset.read(window=window)
            
            # Handle different array shapes
            if tile_array.ndim == 3 and tile_array.shape[0] == 1:
                # Single band, remove band dimension
                tile_array = tile_array[0]
            
            # Create tile metadata
            tile_metadata = {
                'source_file': imagery_metadata.get('file_path'),
                'source_crs': imagery_metadata.get('crs'),
                'source_resolution': imagery_metadata.get('resolution'),
                'window': {
                    'col_off': window.col_off,
                    'row_off': window.row_off,
                    'width': window.width,
                    'height': window.height
                },
                'nodata': dataset.nodata,
                'dtype': str(tile_array.dtype)
            }
            
            # Create and return TileData object
            tile_data = TileData(
                coordinates=coordinates,
                data=tile_array,
                metadata=tile_metadata,
                bands=bands
            )
            
            return tile_data
            
        except Exception as e:
            raise SlicingError(f"Failed to extract tile {coordinates.tile_id}: {str(e)}")
    
    def save_tile(self, tile_data: TileData, output_path: Optional[Union[str, Path]] = None) -> Path:
        """
        Save a tile to disk as a GeoTIFF file.
        
        Args:
            tile_data: TileData object to save
            output_path: Optional custom output path
            
        Returns:
            Path to the saved file
            
        Raises:
            SlicingError: If saving fails
        """
        if output_path is None:
            if self.output_dir is None:
                raise SlicingError("No output directory specified")
            output_path = self.output_dir / f"{tile_data.tile_id}.tif"
        else:
            output_path = Path(output_path)
        
        try:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Prepare data for writing
            if tile_data.data.ndim == 2:
                # Single band - add band dimension
                write_data = tile_data.data[np.newaxis, :, :]
                count = 1
            else:
                # Multi-band
                write_data = tile_data.data
                count = tile_data.num_bands
            
            # Create transform for the tile
            coords = tile_data.coordinates
            tile_transform = from_bounds(
                coords.geo_bounds.left,
                coords.geo_bounds.bottom,
                coords.geo_bounds.right,
                coords.geo_bounds.top,
                tile_data.width,
                tile_data.height
            )
            
            # Set up rasterio profile
            profile = {
                'driver': 'GTiff',
                'height': tile_data.height,
                'width': tile_data.width,
                'count': count,
                'dtype': write_data.dtype,
                'crs': tile_data.metadata.get('source_crs'),
                'transform': tile_transform,
                'compress': 'lzw',  # Use LZW compression
                'tiled': True,
                'blockxsize': min(512, tile_data.width),
                'blockysize': min(512, tile_data.height)
            }
            
            # Add nodata if specified
            if self.preserve_nodata and tile_data.metadata.get('nodata') is not None:
                profile['nodata'] = tile_data.metadata['nodata']
            
            # Write the tile
            with rasterio.open(output_path, 'w', **profile) as dst:
                dst.write(write_data)
                
                # Add tile metadata as tags
                dst.update_tags(
                    tile_id=tile_data.tile_id,
                    grid_x=str(coords.grid_x),
                    grid_y=str(coords.grid_y),
                    center_lat=str(coords.center_lat_lon[0]),
                    center_lon=str(coords.center_lat_lon[1])
                )
            
            logger.debug(f"Saved tile {tile_data.tile_id} to {output_path}")
            return output_path
            
        except Exception as e:
            raise SlicingError(f"Failed to save tile {tile_data.tile_id}: {str(e)}")
    
    def save_all_tiles(self, tiles: List[TileData], prefix: str = "") -> List[Path]:
        """
        Save all tiles to disk.
        
        Args:
            tiles: List of TileData objects to save
            prefix: Optional prefix for filenames
            
        Returns:
            List of paths to saved files
            
        Raises:
            SlicingError: If saving fails
        """
        if self.output_dir is None:
            raise SlicingError("No output directory specified")
        
        saved_paths = []
        
        for tile_data in tiles:
            filename = f"{prefix}{tile_data.tile_id}.tif" if prefix else f"{tile_data.tile_id}.tif"
            output_path = self.output_dir / filename
            
            try:
                saved_path = self.save_tile(tile_data, output_path)
                saved_paths.append(saved_path)
            except Exception as e:
                logger.error(f"Failed to save tile {tile_data.tile_id}: {str(e)}")
                continue
        
        logger.info(f"Saved {len(saved_paths)} tiles to {self.output_dir}")
        return saved_paths
    
    def calculate_slicing_statistics(self, tiles: List[TileData]) -> Dict:
        """
        Calculate statistics about the slicing operation.
        
        Args:
            tiles: List of TileData objects
            
        Returns:
            Dictionary containing slicing statistics
        """
        if not tiles:
            return {}
        
        total_pixels = sum(tile.data.size for tile in tiles)
        total_bytes = sum(tile.size_bytes for tile in tiles)
        
        # Calculate data type distribution
        dtypes = {}
        for tile in tiles:
            dtype_str = str(tile.data.dtype)
            dtypes[dtype_str] = dtypes.get(dtype_str, 0) + 1
        
        # Calculate tile size distribution
        shapes = {}
        for tile in tiles:
            shape_str = str(tile.shape)
            shapes[shape_str] = shapes.get(shape_str, 0) + 1
        
        # Get coordinate bounds
        min_x = min(tile.coordinates.grid_x for tile in tiles)
        max_x = max(tile.coordinates.grid_x for tile in tiles)
        min_y = min(tile.coordinates.grid_y for tile in tiles)
        max_y = max(tile.coordinates.grid_y for tile in tiles)
        
        return {
            'total_tiles': len(tiles),
            'total_pixels': total_pixels,
            'total_bytes': total_bytes,
            'average_pixels_per_tile': total_pixels / len(tiles),
            'average_bytes_per_tile': total_bytes / len(tiles),
            'data_types': dtypes,
            'tile_shapes': shapes,
            'grid_coverage': {
                'x_range': (min_x, max_x),
                'y_range': (min_y, max_y),
                'grid_width': max_x - min_x + 1,
                'grid_height': max_y - min_y + 1
            }
        }


def slice_imagery_file(
    imagery_path: Union[str, Path],
    output_dir: Union[str, Path],
    grid_size: int = 32,
    tile_size: int = 32,
    save_tiles: bool = True
) -> List[TileData]:
    """
    Convenience function to slice a single imagery file.
    
    Args:
        imagery_path: Path to the imagery file
        output_dir: Directory to save tiles
        grid_size: Number of tiles per side
        tile_size: Size of each tile in pixels
        save_tiles: Whether to save tiles to disk
        
    Returns:
        List of TileData objects
        
    Raises:
        SlicingError: If slicing fails
    """
    slicer = ImageSlicer(
        grid_size=grid_size,
        tile_size=tile_size,
        output_dir=output_dir if save_tiles else None
    )
    
    tiles = slicer.slice_imagery(imagery_path)
    
    if save_tiles:
        slicer.save_all_tiles(tiles)
    
    return tiles 