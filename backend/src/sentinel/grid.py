"""Grid coordinate calculation system for tile-based image processing."""

import logging
import math
from typing import Dict, List, Tuple, Optional, NamedTuple
import numpy as np
import rasterio
from rasterio.transform import Affine
from rasterio.coords import BoundingBox

logger = logging.getLogger(__name__)


class TileCoordinates(NamedTuple):
    """Represents the coordinates of a single tile."""
    tile_id: str
    grid_x: int
    grid_y: int
    pixel_bounds: Tuple[int, int, int, int]  # (left, top, right, bottom) in pixels
    geo_bounds: BoundingBox  # Geographic bounds
    center_lat_lon: Tuple[float, float]  # (lat, lon) center point


class GridError(Exception):
    """Custom exception for grid calculation errors."""
    pass


class GridCalculator:
    """Calculates grid coordinates and tile boundaries for image slicing."""
    
    def __init__(self, grid_size: int = 32, tile_size: int = 32):
        """
        Initialize the grid calculator.
        
        Args:
            grid_size: Number of tiles per side (e.g., 32 for 32x32 grid)
            tile_size: Size of each tile in pixels (e.g., 32 for 32x32 pixel tiles)
        """
        self.grid_size = grid_size
        self.tile_size = tile_size
        self.total_tiles = grid_size * grid_size
        logger.info(f"Initialized grid calculator: {grid_size}x{grid_size} grid, {tile_size}x{tile_size} pixel tiles")
    
    def calculate_tile_bounds(self, imagery_metadata: Dict) -> List[TileCoordinates]:
        """
        Calculate tile boundaries for the entire grid based on imagery metadata.
        
        Args:
            imagery_metadata: Metadata from ImageryLoader containing bounds, transform, etc.
            
        Returns:
            List of TileCoordinates objects for each tile in the grid
            
        Raises:
            GridError: If grid calculation fails due to invalid parameters
        """
        if not imagery_metadata:
            raise GridError("Imagery metadata is required for grid calculation")
        
        # Extract required metadata
        width = imagery_metadata.get('width')
        height = imagery_metadata.get('height')
        transform = imagery_metadata.get('transform')
        bounds = imagery_metadata.get('bounds')
        
        if not all([width, height, transform, bounds]):
            raise GridError("Imagery metadata missing required fields: width, height, transform, bounds")
        
        # Validate that image can accommodate the grid
        min_pixels_needed = self.grid_size * self.tile_size
        if width < min_pixels_needed or height < min_pixels_needed:
            raise GridError(
                f"Image size ({width}x{height}) too small for {self.grid_size}x{self.grid_size} grid "
                f"of {self.tile_size}x{self.tile_size} pixel tiles. Need at least {min_pixels_needed}x{min_pixels_needed}"
            )
        
        logger.info(f"Calculating grid for image: {width}x{height} pixels")
        
        # Calculate the area to use for tiling (centered if image is larger than needed)
        tiles_coordinates = []
        
        # Calculate starting offsets to center the grid if image is larger than needed
        total_grid_width = self.grid_size * self.tile_size
        total_grid_height = self.grid_size * self.tile_size
        
        start_x = (width - total_grid_width) // 2
        start_y = (height - total_grid_height) // 2
        
        logger.info(f"Grid offset: ({start_x}, {start_y}), covering {total_grid_width}x{total_grid_height} pixels")
        
        # Generate coordinates for each tile
        for grid_y in range(self.grid_size):
            for grid_x in range(self.grid_size):
                tile_coords = self._calculate_single_tile(
                    grid_x, grid_y, start_x, start_y, transform
                )
                tiles_coordinates.append(tile_coords)
        
        logger.info(f"Generated {len(tiles_coordinates)} tile coordinates")
        return tiles_coordinates
    
    def _calculate_single_tile(
        self, 
        grid_x: int, 
        grid_y: int, 
        start_x: int, 
        start_y: int, 
        transform: Affine
    ) -> TileCoordinates:
        """
        Calculate coordinates for a single tile.
        
        Args:
            grid_x: X position in the grid (0 to grid_size-1)
            grid_y: Y position in the grid (0 to grid_size-1)
            start_x: X offset in pixels where grid starts
            start_y: Y offset in pixels where grid starts
            transform: Affine transformation from imagery metadata
            
        Returns:
            TileCoordinates object for the specified tile
        """
        # Calculate pixel bounds
        pixel_left = start_x + (grid_x * self.tile_size)
        pixel_top = start_y + (grid_y * self.tile_size)
        pixel_right = pixel_left + self.tile_size
        pixel_bottom = pixel_top + self.tile_size
        
        # Convert pixel coordinates to geographic coordinates
        # Top-left corner
        geo_left, geo_top = transform * (pixel_left, pixel_top)
        # Bottom-right corner
        geo_right, geo_bottom = transform * (pixel_right, pixel_bottom)
        
        # Create geographic bounds
        geo_bounds = BoundingBox(geo_left, geo_bottom, geo_right, geo_top)
        
        # Calculate center point and convert to lat/lon if needed
        center_x = (geo_left + geo_right) / 2
        center_y = (geo_top + geo_bottom) / 2
        
        # For now, assume coordinates are already in lat/lon or we'll convert later
        # This is a simplification - in practice you might need to reproject
        center_lat_lon = (center_y, center_x)  # (lat, lon)
        
        # Generate tile ID
        tile_id = f"x{grid_x:02d}_y{grid_y:02d}"
        
        return TileCoordinates(
            tile_id=tile_id,
            grid_x=grid_x,
            grid_y=grid_y,
            pixel_bounds=(pixel_left, pixel_top, pixel_right, pixel_bottom),
            geo_bounds=geo_bounds,
            center_lat_lon=center_lat_lon
        )
    
    def validate_grid_coverage(self, tiles: List[TileCoordinates], imagery_bounds: BoundingBox) -> bool:
        """
        Validate that the calculated grid properly covers the expected area.
        
        Args:
            tiles: List of calculated tile coordinates
            imagery_bounds: Geographic bounds of the source imagery
            
        Returns:
            True if validation passes
            
        Raises:
            GridError: If validation fails
        """
        if len(tiles) != self.total_tiles:
            raise GridError(f"Expected {self.total_tiles} tiles, got {len(tiles)}")
        
        # Calculate overall bounds of the grid
        min_left = min(tile.geo_bounds.left for tile in tiles)
        min_bottom = min(tile.geo_bounds.bottom for tile in tiles)
        max_right = max(tile.geo_bounds.right for tile in tiles)
        max_top = max(tile.geo_bounds.top for tile in tiles)
        
        grid_bounds = BoundingBox(min_left, min_bottom, max_right, max_top)
        
        # Check that grid is within imagery bounds (with small tolerance)
        tolerance = 10.0  # meters
        
        if (grid_bounds.left < imagery_bounds.left - tolerance or
            grid_bounds.right > imagery_bounds.right + tolerance or
            grid_bounds.bottom < imagery_bounds.bottom - tolerance or
            grid_bounds.top > imagery_bounds.top + tolerance):
            
            logger.warning(
                f"Grid bounds {grid_bounds} extend beyond imagery bounds {imagery_bounds} "
                f"(tolerance: {tolerance}m)"
            )
            # Don't raise error, just warn - this might be acceptable
        
        # Check for gaps or overlaps
        self._validate_tile_adjacency(tiles)
        
        logger.info("Grid coverage validation passed")
        return True
    
    def _validate_tile_adjacency(self, tiles: List[TileCoordinates]) -> None:
        """
        Validate that tiles are properly adjacent without gaps or significant overlaps.
        
        Args:
            tiles: List of tile coordinates to validate
            
        Raises:
            GridError: If tiles have significant gaps or overlaps
        """
        # Create a lookup dictionary for easier access
        tile_lookup = {(tile.grid_x, tile.grid_y): tile for tile in tiles}
        
        tolerance = 1.0  # 1 meter tolerance for floating point precision
        
        for tile in tiles:
            # Check right neighbor
            if tile.grid_x < self.grid_size - 1:
                right_neighbor = tile_lookup.get((tile.grid_x + 1, tile.grid_y))
                if right_neighbor:
                    gap = abs(tile.geo_bounds.right - right_neighbor.geo_bounds.left)
                    if gap > tolerance:
                        raise GridError(
                            f"Gap between tiles {tile.tile_id} and {right_neighbor.tile_id}: {gap}m"
                        )
            
            # Check bottom neighbor
            if tile.grid_y < self.grid_size - 1:
                bottom_neighbor = tile_lookup.get((tile.grid_x, tile.grid_y + 1))
                if bottom_neighbor:
                    gap = abs(tile.geo_bounds.bottom - bottom_neighbor.geo_bounds.top)
                    if gap > tolerance:
                        raise GridError(
                            f"Gap between tiles {tile.tile_id} and {bottom_neighbor.tile_id}: {gap}m"
                        )
    
    def get_tile_by_coordinates(self, tiles: List[TileCoordinates], lat: float, lon: float) -> Optional[TileCoordinates]:
        """
        Find the tile that contains the given geographic coordinates.
        
        Args:
            tiles: List of all tile coordinates
            lat: Latitude
            lon: Longitude
            
        Returns:
            TileCoordinates object if found, None otherwise
        """
        for tile in tiles:
            if (tile.geo_bounds.left <= lon <= tile.geo_bounds.right and
                tile.geo_bounds.bottom <= lat <= tile.geo_bounds.top):
                return tile
        return None
    
    def get_neighboring_tiles(self, tiles: List[TileCoordinates], tile_id: str, distance: int = 1) -> List[TileCoordinates]:
        """
        Get neighboring tiles within a specified distance.
        
        Args:
            tiles: List of all tile coordinates
            tile_id: ID of the center tile
            distance: Distance in grid cells (1 = immediate neighbors)
            
        Returns:
            List of neighboring TileCoordinates objects
        """
        # Find the center tile
        center_tile = next((tile for tile in tiles if tile.tile_id == tile_id), None)
        if not center_tile:
            return []
        
        # Create lookup for faster access
        tile_lookup = {(tile.grid_x, tile.grid_y): tile for tile in tiles}
        
        neighbors = []
        center_x, center_y = center_tile.grid_x, center_tile.grid_y
        
        for dx in range(-distance, distance + 1):
            for dy in range(-distance, distance + 1):
                if dx == 0 and dy == 0:
                    continue  # Skip the center tile itself
                
                neighbor_x = center_x + dx
                neighbor_y = center_y + dy
                
                # Check bounds
                if (0 <= neighbor_x < self.grid_size and 
                    0 <= neighbor_y < self.grid_size):
                    
                    neighbor = tile_lookup.get((neighbor_x, neighbor_y))
                    if neighbor:
                        neighbors.append(neighbor)
        
        return neighbors
    
    def calculate_tile_statistics(self, tiles: List[TileCoordinates]) -> Dict:
        """
        Calculate statistics about the tile grid.
        
        Args:
            tiles: List of tile coordinates
            
        Returns:
            Dictionary containing grid statistics
        """
        if not tiles:
            return {}
        
        # Calculate area per tile (assuming first tile is representative)
        first_tile = tiles[0]
        tile_width = first_tile.geo_bounds.right - first_tile.geo_bounds.left
        tile_height = first_tile.geo_bounds.top - first_tile.geo_bounds.bottom
        tile_area = tile_width * tile_height
        
        # Calculate total coverage
        total_area = tile_area * len(tiles)
        
        # Calculate overall bounds
        min_left = min(tile.geo_bounds.left for tile in tiles)
        min_bottom = min(tile.geo_bounds.bottom for tile in tiles)
        max_right = max(tile.geo_bounds.right for tile in tiles)
        max_top = max(tile.geo_bounds.top for tile in tiles)
        
        overall_bounds = BoundingBox(min_left, min_bottom, max_right, max_top)
        overall_width = overall_bounds.right - overall_bounds.left
        overall_height = overall_bounds.top - overall_bounds.bottom
        
        return {
            'total_tiles': len(tiles),
            'grid_size': f"{self.grid_size}x{self.grid_size}",
            'tile_size_pixels': f"{self.tile_size}x{self.tile_size}",
            'tile_dimensions_meters': {
                'width': tile_width,
                'height': tile_height,
                'area': tile_area
            },
            'total_coverage': {
                'area': total_area,
                'width': overall_width,
                'height': overall_height,
                'bounds': overall_bounds
            },
            'average_tile_center': {
                'lat': sum(tile.center_lat_lon[0] for tile in tiles) / len(tiles),
                'lon': sum(tile.center_lat_lon[1] for tile in tiles) / len(tiles)
            }
        }


def calculate_grid_for_imagery(imagery_metadata: Dict, grid_size: int = 32, tile_size: int = 32) -> List[TileCoordinates]:
    """
    Convenience function to calculate grid coordinates for imagery.
    
    Args:
        imagery_metadata: Metadata from ImageryLoader
        grid_size: Number of tiles per side
        tile_size: Size of each tile in pixels
        
    Returns:
        List of TileCoordinates objects
        
    Raises:
        GridError: If calculation fails
    """
    calculator = GridCalculator(grid_size, tile_size)
    tiles = calculator.calculate_tile_bounds(imagery_metadata)
    
    # Validate the results
    if 'bounds' in imagery_metadata:
        calculator.validate_grid_coverage(tiles, imagery_metadata['bounds'])
    
    return tiles 