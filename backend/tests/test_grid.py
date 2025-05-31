"""Tests for the grid coordinate calculation module."""

import pytest
import numpy as np
from unittest.mock import Mock
from rasterio.transform import from_bounds
from rasterio.coords import BoundingBox

from src.sentinel.grid import (
    GridCalculator,
    TileCoordinates,
    GridError,
    calculate_grid_for_imagery
)


class TestGridCalculator:
    """Test cases for GridCalculator class."""
    
    @pytest.fixture
    def sample_imagery_metadata(self):
        """Create sample imagery metadata for testing."""
        # 10m resolution, 1km x 1km area
        # UTM coordinates: 400000-401000 E, 5000000-5001000 N
        transform = from_bounds(400000, 5000000, 401000, 5001000, 100, 100)
        
        return {
            'width': 100,
            'height': 100,
            'transform': transform,
            'bounds': BoundingBox(400000, 5000000, 401000, 5001000),
            'crs': 'EPSG:32633',
            'resolution': {'x': 10.0, 'y': 10.0}
        }
    
    @pytest.fixture
    def large_imagery_metadata(self):
        """Create larger imagery metadata for testing."""
        # 10m resolution, 10km x 10km area
        transform = from_bounds(400000, 5000000, 410000, 5010000, 1000, 1000)
        
        return {
            'width': 1000,
            'height': 1000,
            'transform': transform,
            'bounds': BoundingBox(400000, 5000000, 410000, 5010000),
            'crs': 'EPSG:32633',
            'resolution': {'x': 10.0, 'y': 10.0}
        }
    
    def test_init_default_parameters(self):
        """Test GridCalculator initialization with default parameters."""
        calculator = GridCalculator()
        
        assert calculator.grid_size == 32
        assert calculator.tile_size == 32
        assert calculator.total_tiles == 1024
    
    def test_init_custom_parameters(self):
        """Test GridCalculator initialization with custom parameters."""
        calculator = GridCalculator(grid_size=16, tile_size=64)
        
        assert calculator.grid_size == 16
        assert calculator.tile_size == 64
        assert calculator.total_tiles == 256
    
    def test_calculate_tile_bounds_success(self, large_imagery_metadata):
        """Test successful tile bounds calculation."""
        calculator = GridCalculator(grid_size=4, tile_size=32)
        
        tiles = calculator.calculate_tile_bounds(large_imagery_metadata)
        
        assert len(tiles) == 16  # 4x4 grid
        assert all(isinstance(tile, TileCoordinates) for tile in tiles)
        
        # Check first tile
        first_tile = tiles[0]
        assert first_tile.tile_id == "x00_y00"
        assert first_tile.grid_x == 0
        assert first_tile.grid_y == 0
        
        # Check last tile
        last_tile = tiles[-1]
        assert last_tile.tile_id == "x03_y03"
        assert last_tile.grid_x == 3
        assert last_tile.grid_y == 3
    
    def test_calculate_tile_bounds_empty_metadata(self):
        """Test tile bounds calculation with empty metadata."""
        calculator = GridCalculator()
        
        with pytest.raises(GridError, match="Imagery metadata is required"):
            calculator.calculate_tile_bounds({})
    
    def test_calculate_tile_bounds_missing_fields(self):
        """Test tile bounds calculation with missing required fields."""
        calculator = GridCalculator()
        incomplete_metadata = {'width': 100, 'height': 100}
        
        with pytest.raises(GridError, match="missing required fields"):
            calculator.calculate_tile_bounds(incomplete_metadata)
    
    def test_calculate_tile_bounds_too_small_image(self):
        """Test tile bounds calculation with image too small for grid."""
        calculator = GridCalculator(grid_size=32, tile_size=32)  # Needs 1024x1024
        small_metadata = {
            'width': 500,
            'height': 500,
            'transform': from_bounds(0, 0, 1000, 1000, 500, 500),
            'bounds': BoundingBox(0, 0, 1000, 1000)
        }
        
        with pytest.raises(GridError, match="too small for"):
            calculator.calculate_tile_bounds(small_metadata)
    
    def test_calculate_single_tile(self, large_imagery_metadata):
        """Test single tile coordinate calculation."""
        calculator = GridCalculator(grid_size=4, tile_size=32)
        transform = large_imagery_metadata['transform']
        
        tile = calculator._calculate_single_tile(
            grid_x=1, grid_y=2, start_x=100, start_y=200, transform=transform
        )
        
        assert tile.tile_id == "x01_y02"
        assert tile.grid_x == 1
        assert tile.grid_y == 2
        
        # Check pixel bounds
        expected_pixel_left = 100 + (1 * 32)  # 132
        expected_pixel_top = 200 + (2 * 32)   # 264
        assert tile.pixel_bounds == (132, 264, 164, 296)
        
        # Check that geographic bounds are reasonable
        assert tile.geo_bounds.left < tile.geo_bounds.right
        assert tile.geo_bounds.bottom < tile.geo_bounds.top
    
    def test_validate_grid_coverage_success(self, large_imagery_metadata):
        """Test successful grid coverage validation."""
        calculator = GridCalculator(grid_size=4, tile_size=32)
        tiles = calculator.calculate_tile_bounds(large_imagery_metadata)
        
        result = calculator.validate_grid_coverage(tiles, large_imagery_metadata['bounds'])
        assert result is True
    
    def test_validate_grid_coverage_wrong_tile_count(self, large_imagery_metadata):
        """Test grid coverage validation with wrong tile count."""
        calculator = GridCalculator(grid_size=4, tile_size=32)
        tiles = calculator.calculate_tile_bounds(large_imagery_metadata)
        
        # Remove one tile
        tiles = tiles[:-1]
        
        with pytest.raises(GridError, match="Expected 16 tiles, got 15"):
            calculator.validate_grid_coverage(tiles, large_imagery_metadata['bounds'])
    
    def test_get_tile_by_coordinates(self, large_imagery_metadata):
        """Test finding tile by geographic coordinates."""
        calculator = GridCalculator(grid_size=4, tile_size=32)
        tiles = calculator.calculate_tile_bounds(large_imagery_metadata)
        
        # Get coordinates within the first tile
        first_tile = tiles[0]
        center_lat, center_lon = first_tile.center_lat_lon
        
        found_tile = calculator.get_tile_by_coordinates(tiles, center_lat, center_lon)
        
        assert found_tile is not None
        assert found_tile.tile_id == first_tile.tile_id
    
    def test_get_tile_by_coordinates_not_found(self, large_imagery_metadata):
        """Test finding tile by coordinates outside the grid."""
        calculator = GridCalculator(grid_size=4, tile_size=32)
        tiles = calculator.calculate_tile_bounds(large_imagery_metadata)
        
        # Use coordinates far outside the grid
        found_tile = calculator.get_tile_by_coordinates(tiles, 0.0, 0.0)
        
        assert found_tile is None
    
    def test_get_neighboring_tiles(self, large_imagery_metadata):
        """Test finding neighboring tiles."""
        calculator = GridCalculator(grid_size=4, tile_size=32)
        tiles = calculator.calculate_tile_bounds(large_imagery_metadata)
        
        # Get neighbors of center tile (x01_y01)
        center_tile_id = "x01_y01"
        neighbors = calculator.get_neighboring_tiles(tiles, center_tile_id, distance=1)
        
        # Should have 8 neighbors (3x3 - 1 center)
        assert len(neighbors) == 8
        
        # Check that center tile is not included
        neighbor_ids = [tile.tile_id for tile in neighbors]
        assert center_tile_id not in neighbor_ids
        
        # Check some specific expected neighbors
        expected_neighbors = ["x00_y00", "x00_y01", "x00_y02", 
                             "x01_y00", "x01_y02",
                             "x02_y00", "x02_y01", "x02_y02"]
        assert all(nid in neighbor_ids for nid in expected_neighbors)
    
    def test_get_neighboring_tiles_edge_case(self, large_imagery_metadata):
        """Test finding neighbors for edge tile."""
        calculator = GridCalculator(grid_size=4, tile_size=32)
        tiles = calculator.calculate_tile_bounds(large_imagery_metadata)
        
        # Get neighbors of corner tile (x00_y00)
        corner_tile_id = "x00_y00"
        neighbors = calculator.get_neighboring_tiles(tiles, corner_tile_id, distance=1)
        
        # Should have 3 neighbors (only adjacent tiles within grid)
        assert len(neighbors) == 3
        
        neighbor_ids = [tile.tile_id for tile in neighbors]
        expected_neighbors = ["x00_y01", "x01_y00", "x01_y01"]
        assert all(nid in neighbor_ids for nid in expected_neighbors)
    
    def test_get_neighboring_tiles_nonexistent(self, large_imagery_metadata):
        """Test finding neighbors for non-existent tile."""
        calculator = GridCalculator(grid_size=4, tile_size=32)
        tiles = calculator.calculate_tile_bounds(large_imagery_metadata)
        
        neighbors = calculator.get_neighboring_tiles(tiles, "nonexistent", distance=1)
        
        assert len(neighbors) == 0
    
    def test_calculate_tile_statistics(self, large_imagery_metadata):
        """Test calculation of tile statistics."""
        calculator = GridCalculator(grid_size=4, tile_size=32)
        tiles = calculator.calculate_tile_bounds(large_imagery_metadata)
        
        stats = calculator.calculate_tile_statistics(tiles)
        
        assert stats['total_tiles'] == 16
        assert stats['grid_size'] == "4x4"
        assert stats['tile_size_pixels'] == "32x32"
        
        # Check that tile dimensions are reasonable
        tile_dims = stats['tile_dimensions_meters']
        assert tile_dims['width'] > 0
        assert tile_dims['height'] > 0
        assert tile_dims['area'] > 0
        
        # Check total coverage
        coverage = stats['total_coverage']
        assert coverage['area'] == tile_dims['area'] * 16
        assert coverage['width'] > 0
        assert coverage['height'] > 0
        
        # Check average center coordinates
        avg_center = stats['average_tile_center']
        assert 'lat' in avg_center
        assert 'lon' in avg_center
    
    def test_calculate_tile_statistics_empty(self):
        """Test tile statistics calculation with empty list."""
        calculator = GridCalculator()
        stats = calculator.calculate_tile_statistics([])
        
        assert stats == {}
    
    def test_validate_tile_adjacency_success(self, large_imagery_metadata):
        """Test successful tile adjacency validation."""
        calculator = GridCalculator(grid_size=4, tile_size=32)
        tiles = calculator.calculate_tile_bounds(large_imagery_metadata)
        
        # Should not raise an exception
        calculator._validate_tile_adjacency(tiles)
    
    def test_tile_coordinates_properties(self, large_imagery_metadata):
        """Test TileCoordinates named tuple properties."""
        calculator = GridCalculator(grid_size=2, tile_size=50)
        tiles = calculator.calculate_tile_bounds(large_imagery_metadata)
        
        tile = tiles[0]
        
        # Test all properties are accessible
        assert isinstance(tile.tile_id, str)
        assert isinstance(tile.grid_x, int)
        assert isinstance(tile.grid_y, int)
        assert isinstance(tile.pixel_bounds, tuple)
        assert len(tile.pixel_bounds) == 4
        assert isinstance(tile.geo_bounds, BoundingBox)
        assert isinstance(tile.center_lat_lon, tuple)
        assert len(tile.center_lat_lon) == 2


def test_calculate_grid_for_imagery_convenience_function():
    """Test the convenience function for grid calculation."""
    # Create large imagery metadata for this test
    transform = from_bounds(400000, 5000000, 410000, 5010000, 1000, 1000)
    
    large_imagery_metadata = {
        'width': 1000,
        'height': 1000,
        'transform': transform,
        'bounds': BoundingBox(400000, 5000000, 410000, 5010000),
        'crs': 'EPSG:32633',
        'resolution': {'x': 10.0, 'y': 10.0}
    }
    
    tiles = calculate_grid_for_imagery(large_imagery_metadata, grid_size=3, tile_size=64)
    
    assert len(tiles) == 9  # 3x3 grid
    assert all(isinstance(tile, TileCoordinates) for tile in tiles)
    
    # Check that first and last tiles are correct
    assert tiles[0].tile_id == "x00_y00"
    assert tiles[-1].tile_id == "x02_y02"


def test_calculate_grid_for_imagery_with_validation():
    """Test convenience function with validation."""
    metadata = {
        'width': 2000,
        'height': 2000,
        'transform': from_bounds(0, 0, 1000, 1000, 2000, 2000),
        'bounds': BoundingBox(0, 0, 1000, 1000)
    }
    
    tiles = calculate_grid_for_imagery(metadata, grid_size=4, tile_size=32)
    
    assert len(tiles) == 16
    
    # Verify that validation was performed (no exceptions raised)
    assert all(tile.tile_id.startswith('x') for tile in tiles)


def test_calculate_grid_for_imagery_error():
    """Test convenience function with invalid input."""
    with pytest.raises(GridError):
        calculate_grid_for_imagery({}, grid_size=32, tile_size=32) 