"""Tests for the core slicing algorithm module."""

import pytest
import numpy as np
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from rasterio.transform import from_bounds
from rasterio.coords import BoundingBox
from rasterio.windows import Window

from src.sentinel.slicer import (
    ImageSlicer,
    TileData,
    SlicingError,
    slice_imagery_file
)
from src.sentinel.grid import TileCoordinates


class TestTileData:
    """Test cases for TileData class."""
    
    @pytest.fixture
    def sample_coordinates(self):
        """Create sample tile coordinates."""
        return TileCoordinates(
            tile_id="x01_y02",
            grid_x=1,
            grid_y=2,
            pixel_bounds=(32, 64, 64, 96),
            geo_bounds=BoundingBox(400320, 5000640, 400640, 5000960),
            center_lat_lon=(50.0086, 7.0048)
        )
    
    def test_tile_data_2d_array(self, sample_coordinates):
        """Test TileData with 2D array (single band)."""
        data = np.random.randint(0, 1000, (32, 32), dtype=np.uint16)
        metadata = {'source_file': 'test.tif', 'nodata': 0}
        
        tile = TileData(sample_coordinates, data, metadata, ['B04'])
        
        assert tile.tile_id == "x01_y02"
        assert tile.shape == (32, 32)
        assert tile.num_bands == 1
        assert tile.height == 32
        assert tile.width == 32
        assert tile.size_bytes == data.nbytes
        assert tile.bands == ['B04']
    
    def test_tile_data_3d_array(self, sample_coordinates):
        """Test TileData with 3D array (multi-band)."""
        data = np.random.randint(0, 1000, (3, 32, 32), dtype=np.uint16)
        metadata = {'source_file': 'test.tif', 'nodata': 0}
        
        tile = TileData(sample_coordinates, data, metadata, ['B02', 'B03', 'B04'])
        
        assert tile.tile_id == "x01_y02"
        assert tile.shape == (3, 32, 32)
        assert tile.num_bands == 3
        assert tile.height == 32
        assert tile.width == 32
        assert tile.bands == ['B02', 'B03', 'B04']
    
    def test_tile_data_invalid_dimensions(self, sample_coordinates):
        """Test TileData with invalid array dimensions."""
        data = np.random.randint(0, 1000, (32,), dtype=np.uint16)  # 1D array
        metadata = {'source_file': 'test.tif'}
        
        with pytest.raises(SlicingError, match="must be 2D or 3D array"):
            TileData(sample_coordinates, data, metadata)
    
    def test_get_band_data_2d(self, sample_coordinates):
        """Test getting band data from 2D array."""
        data = np.random.randint(0, 1000, (32, 32), dtype=np.uint16)
        metadata = {'source_file': 'test.tif'}
        
        tile = TileData(sample_coordinates, data, metadata)
        
        band_data = tile.get_band_data(0)
        assert np.array_equal(band_data, data)
        
        with pytest.raises(SlicingError, match="Single band data"):
            tile.get_band_data(1)
    
    def test_get_band_data_3d(self, sample_coordinates):
        """Test getting band data from 3D array."""
        data = np.random.randint(0, 1000, (3, 32, 32), dtype=np.uint16)
        metadata = {'source_file': 'test.tif'}
        
        tile = TileData(sample_coordinates, data, metadata)
        
        band_0 = tile.get_band_data(0)
        assert np.array_equal(band_0, data[0])
        
        band_2 = tile.get_band_data(2)
        assert np.array_equal(band_2, data[2])
        
        with pytest.raises(SlicingError, match="out of range"):
            tile.get_band_data(3)
    
    def test_calculate_statistics_2d(self, sample_coordinates):
        """Test statistics calculation for 2D data."""
        # Create data with known values
        data = np.full((32, 32), 100, dtype=np.uint16)
        data[0:10, 0:10] = 0  # Add some nodata
        metadata = {'source_file': 'test.tif'}
        
        tile = TileData(sample_coordinates, data, metadata)
        stats = tile.calculate_statistics()
        
        assert 'single_band' in stats
        band_stats = stats['single_band']
        assert band_stats['min'] == 100.0
        assert band_stats['max'] == 100.0
        assert band_stats['mean'] == 100.0
        assert band_stats['valid_pixels'] == 924  # 32*32 - 10*10
        assert band_stats['total_pixels'] == 1024
    
    def test_calculate_statistics_3d(self, sample_coordinates):
        """Test statistics calculation for 3D data."""
        data = np.zeros((2, 32, 32), dtype=np.uint16)
        data[0] = 100  # First band
        data[1] = 200  # Second band
        metadata = {'source_file': 'test.tif'}
        
        tile = TileData(sample_coordinates, data, metadata, ['B04', 'B08'])
        stats = tile.calculate_statistics()
        
        assert 'B04' in stats
        assert 'B08' in stats
        assert stats['B04']['mean'] == 100.0
        assert stats['B08']['mean'] == 200.0


class TestImageSlicer:
    """Test cases for ImageSlicer class."""
    
    @pytest.fixture
    def mock_imagery_metadata(self):
        """Create mock imagery metadata."""
        transform = from_bounds(400000, 5000000, 401000, 5001000, 1000, 1000)
        
        return {
            'file_path': 'test.tif',
            'width': 1000,
            'height': 1000,
            'transform': transform,
            'bounds': BoundingBox(400000, 5000000, 401000, 5001000),
            'crs': 'EPSG:32633',
            'resolution': {'x': 1.0, 'y': 1.0},
            'nodata': 0,
            'dataset': Mock()
        }
    
    @pytest.fixture
    def mock_dataset(self):
        """Create a mock rasterio dataset."""
        dataset = Mock()
        dataset.read.return_value = np.random.randint(0, 1000, (32, 32), dtype=np.uint16)
        dataset.nodata = 0
        dataset.close = Mock()
        return dataset
    
    def test_image_slicer_init_default(self):
        """Test ImageSlicer initialization with default parameters."""
        slicer = ImageSlicer()
        
        assert slicer.grid_calculator.grid_size == 32
        assert slicer.grid_calculator.tile_size == 32
        assert slicer.output_dir is None
        assert slicer.preserve_nodata is True
    
    def test_image_slicer_init_with_output_dir(self, tmp_path):
        """Test ImageSlicer initialization with output directory."""
        output_dir = tmp_path / "tiles"
        slicer = ImageSlicer(output_dir=output_dir)
        
        assert slicer.output_dir == output_dir
        assert output_dir.exists()
    
    def test_slice_imagery_success(self, mock_imagery_metadata, mock_dataset):
        """Test successful imagery slicing."""
        slicer = ImageSlicer(grid_size=2, tile_size=32)
        
        # Mock the imagery loader
        with patch.object(slicer.imagery_loader, 'load_imagery') as mock_load:
            mock_load.return_value = mock_imagery_metadata
            mock_imagery_metadata['dataset'] = mock_dataset
            
            # Mock the grid calculator
            mock_coords = [
                TileCoordinates("x00_y00", 0, 0, (0, 0, 32, 32), 
                               BoundingBox(400000, 5000000, 400032, 5000032), (50.0, 7.0)),
                TileCoordinates("x01_y00", 1, 0, (32, 0, 64, 32), 
                               BoundingBox(400032, 5000000, 400064, 5000032), (50.0, 7.0)),
            ]
            
            with patch.object(slicer.grid_calculator, 'calculate_tile_bounds') as mock_bounds:
                mock_bounds.return_value = mock_coords
                
                tiles = slicer.slice_imagery('test.tif')
        
        assert len(tiles) == 2
        assert all(isinstance(tile, TileData) for tile in tiles)
        assert tiles[0].tile_id == "x00_y00"
        assert tiles[1].tile_id == "x01_y00"
        mock_dataset.close.assert_called_once()
    
    def test_slice_imagery_failure(self):
        """Test imagery slicing failure."""
        slicer = ImageSlicer()
        
        with patch.object(slicer.imagery_loader, 'load_imagery') as mock_load:
            mock_load.side_effect = Exception("Load failed")
            
            with pytest.raises(SlicingError, match="Failed to slice imagery"):
                slicer.slice_imagery('nonexistent.tif')
    
    def test_extract_single_tile(self, mock_imagery_metadata, mock_dataset):
        """Test single tile extraction."""
        slicer = ImageSlicer()
        
        coords = TileCoordinates(
            "x01_y02", 1, 2, (32, 64, 64, 96),
            BoundingBox(400032, 5000064, 400064, 5000096), (50.0, 7.0)
        )
        
        tile_data = slicer._extract_single_tile(
            mock_dataset, coords, mock_imagery_metadata, ['B04']
        )
        
        assert isinstance(tile_data, TileData)
        assert tile_data.tile_id == "x01_y02"
        assert tile_data.bands == ['B04']
        
        # Verify that dataset.read was called with correct window
        mock_dataset.read.assert_called_once()
        call_args = mock_dataset.read.call_args
        window = call_args[1]['window']
        assert window.col_off == 32
        assert window.row_off == 64
        assert window.width == 32
        assert window.height == 32
    
    def test_save_tile(self, tmp_path):
        """Test saving a tile to disk."""
        output_dir = tmp_path / "tiles"
        slicer = ImageSlicer(output_dir=output_dir)
        
        # Create sample tile data
        coords = TileCoordinates(
            "x01_y02", 1, 2, (32, 64, 64, 96),
            BoundingBox(400032, 5000064, 400064, 5000096), (50.0, 7.0)
        )
        data = np.random.randint(0, 1000, (32, 32), dtype=np.uint16)
        metadata = {'source_crs': 'EPSG:32633', 'nodata': 0}
        
        tile_data = TileData(coords, data, metadata, ['B04'])
        
        # Mock rasterio.open to avoid actual file I/O in test
        with patch('rasterio.open') as mock_open:
            mock_dst = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_dst
            
            saved_path = slicer.save_tile(tile_data)
        
        assert saved_path == output_dir / "x01_y02.tif"
        mock_dst.write.assert_called_once()
        mock_dst.update_tags.assert_called_once()
    
    def test_save_tile_no_output_dir(self):
        """Test saving tile without output directory."""
        slicer = ImageSlicer()  # No output directory
        
        coords = TileCoordinates(
            "x01_y02", 1, 2, (32, 64, 64, 96),
            BoundingBox(400032, 5000064, 400064, 5000096), (50.0, 7.0)
        )
        data = np.random.randint(0, 1000, (32, 32), dtype=np.uint16)
        metadata = {'source_crs': 'EPSG:32633'}
        
        tile_data = TileData(coords, data, metadata)
        
        with pytest.raises(SlicingError, match="No output directory specified"):
            slicer.save_tile(tile_data)
    
    def test_calculate_slicing_statistics(self):
        """Test calculation of slicing statistics."""
        slicer = ImageSlicer()
        
        # Create sample tiles
        tiles = []
        for i in range(3):
            coords = TileCoordinates(
                f"x{i:02d}_y00", i, 0, (i*32, 0, (i+1)*32, 32),
                BoundingBox(400000 + i*32, 5000000, 400032 + i*32, 5000032), (50.0, 7.0)
            )
            data = np.random.randint(0, 1000, (32, 32), dtype=np.uint16)
            metadata = {'source_file': 'test.tif'}
            
            tile_data = TileData(coords, data, metadata)
            tiles.append(tile_data)
        
        stats = slicer.calculate_slicing_statistics(tiles)
        
        assert stats['total_tiles'] == 3
        assert stats['total_pixels'] == 3 * 32 * 32
        assert stats['average_pixels_per_tile'] == 32 * 32
        assert stats['grid_coverage']['x_range'] == (0, 2)
        assert stats['grid_coverage']['y_range'] == (0, 0)
        assert stats['grid_coverage']['grid_width'] == 3
        assert stats['grid_coverage']['grid_height'] == 1
    
    def test_calculate_slicing_statistics_empty(self):
        """Test statistics calculation with empty tile list."""
        slicer = ImageSlicer()
        stats = slicer.calculate_slicing_statistics([])
        assert stats == {}


def test_slice_imagery_file_convenience_function(tmp_path):
    """Test the convenience function for slicing imagery files."""
    output_dir = tmp_path / "tiles"
    
    # Mock the ImageSlicer
    with patch('src.sentinel.slicer.ImageSlicer') as mock_slicer_class:
        mock_slicer = Mock()
        mock_slicer_class.return_value = mock_slicer
        
        # Create mock tiles
        mock_tiles = [Mock(), Mock()]
        mock_slicer.slice_imagery.return_value = mock_tiles
        
        tiles = slice_imagery_file(
            'test.tif', 
            output_dir, 
            grid_size=4, 
            tile_size=64, 
            save_tiles=True
        )
        
        # Verify ImageSlicer was created with correct parameters
        mock_slicer_class.assert_called_once_with(
            grid_size=4,
            tile_size=64,
            output_dir=output_dir
        )
        
        # Verify methods were called
        mock_slicer.slice_imagery.assert_called_once_with('test.tif')
        mock_slicer.save_all_tiles.assert_called_once_with(mock_tiles)
        
        assert tiles == mock_tiles


def test_slice_imagery_file_no_save(tmp_path):
    """Test convenience function without saving tiles."""
    with patch('src.sentinel.slicer.ImageSlicer') as mock_slicer_class:
        mock_slicer = Mock()
        mock_slicer_class.return_value = mock_slicer
        
        mock_tiles = [Mock()]
        mock_slicer.slice_imagery.return_value = mock_tiles
        
        tiles = slice_imagery_file(
            'test.tif', 
            tmp_path, 
            save_tiles=False
        )
        
        # Verify ImageSlicer was created with no output directory
        mock_slicer_class.assert_called_once_with(
            grid_size=32,
            tile_size=32,
            output_dir=None
        )
        
        # Verify save_all_tiles was not called
        mock_slicer.save_all_tiles.assert_not_called()
        
        assert tiles == mock_tiles 