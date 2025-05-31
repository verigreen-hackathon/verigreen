"""Tests for the imagery loading and validation module."""

import pytest
import numpy as np
import tempfile
import rasterio
from pathlib import Path
from unittest.mock import Mock, patch
from rasterio.transform import from_bounds

from src.sentinel.imagery import (
    ImageryLoader, 
    ImageryValidator, 
    ImageryError,
    load_imagery_safely
)


class TestImageryValidator:
    """Test cases for ImageryValidator class."""
    
    def test_validate_file_format_success(self, tmp_path):
        """Test successful file format validation."""
        test_file = tmp_path / "test.tif"
        test_file.touch()
        
        result = ImageryValidator.validate_file_format(test_file)
        assert result is True
    
    def test_validate_file_format_missing_file(self, tmp_path):
        """Test file format validation with missing file."""
        test_file = tmp_path / "missing.tif"
        
        with pytest.raises(ImageryError, match="File does not exist"):
            ImageryValidator.validate_file_format(test_file)
    
    def test_validate_file_format_unsupported(self, tmp_path):
        """Test file format validation with unsupported format."""
        test_file = tmp_path / "test.txt"
        test_file.touch()
        
        with pytest.raises(ImageryError, match="Unsupported file format"):
            ImageryValidator.validate_file_format(test_file)
    
    def test_validate_crs_success(self):
        """Test successful CRS validation."""
        mock_dataset = Mock()
        mock_dataset.crs = rasterio.crs.CRS.from_epsg(32633)
        
        result = ImageryValidator.validate_crs(mock_dataset)
        assert result is True
    
    def test_validate_crs_none(self):
        """Test CRS validation with no CRS."""
        mock_dataset = Mock()
        mock_dataset.crs = None
        
        with pytest.raises(ImageryError, match="no coordinate reference system"):
            ImageryValidator.validate_crs(mock_dataset)
    
    def test_validate_resolution_success(self):
        """Test successful resolution validation."""
        mock_dataset = Mock()
        # 10m pixel size (typical for Sentinel-2)
        mock_dataset.transform = rasterio.transform.from_bounds(0, 0, 1000, 1000, 100, 100)
        
        result = ImageryValidator.validate_resolution(mock_dataset)
        assert result is True
    
    def test_validate_resolution_too_low(self):
        """Test resolution validation with too low resolution."""
        mock_dataset = Mock()
        # 1m pixel size (too high resolution)
        mock_dataset.transform = rasterio.transform.from_bounds(0, 0, 100, 100, 100, 100)
        
        with pytest.raises(ImageryError, match="outside acceptable range"):
            ImageryValidator.validate_resolution(mock_dataset)
    
    def test_validate_data_integrity_success(self):
        """Test successful data integrity validation."""
        mock_dataset = Mock()
        mock_dataset.width = 1000
        mock_dataset.height = 1000
        mock_dataset.count = 1
        mock_dataset.nodata = 0
        mock_dataset.read.return_value = np.ones((50, 50), dtype=np.uint16) * 100
        
        result = ImageryValidator.validate_data_integrity(mock_dataset)
        assert result is True
    
    def test_validate_data_integrity_zero_dimensions(self):
        """Test data integrity validation with zero dimensions."""
        mock_dataset = Mock()
        mock_dataset.width = 0
        mock_dataset.height = 1000
        mock_dataset.count = 1
        
        with pytest.raises(ImageryError, match="zero width or height"):
            ImageryValidator.validate_data_integrity(mock_dataset)


class TestImageryLoader:
    """Test cases for ImageryLoader class."""
    
    @pytest.fixture
    def mock_dataset(self):
        """Create a mock rasterio dataset."""
        dataset = Mock()
        dataset.width = 1000
        dataset.height = 1000
        dataset.count = 1
        dataset.dtypes = [np.dtype('uint16')]
        dataset.crs = rasterio.crs.CRS.from_epsg(32633)
        dataset.bounds = rasterio.coords.BoundingBox(400000, 5000000, 410000, 5010000)
        dataset.transform = from_bounds(400000, 5000000, 410000, 5010000, 1000, 1000)
        dataset.nodata = 0
        return dataset
    
    def test_load_imagery_success(self, tmp_path, mock_dataset):
        """Test successful imagery loading."""
        test_file = tmp_path / "test.tif"
        test_file.touch()
        
        loader = ImageryLoader(validate=False)
        
        with patch('rasterio.open', return_value=mock_dataset):
            result = loader.load_imagery(test_file)
        
        assert result['width'] == 1000
        assert result['height'] == 1000
        assert result['count'] == 1
        assert result['dtype'] == 'uint16'
        assert result['dataset'] == mock_dataset
    
    def test_load_imagery_with_validation(self, tmp_path, mock_dataset):
        """Test imagery loading with validation enabled."""
        test_file = tmp_path / "test.tif"
        test_file.touch()
        
        loader = ImageryLoader(validate=True)
        
        with patch('rasterio.open', return_value=mock_dataset):
            with patch.object(ImageryValidator, 'validate_file_format', return_value=True):
                with patch.object(ImageryValidator, 'validate_crs', return_value=True):
                    with patch.object(ImageryValidator, 'validate_resolution', return_value=True):
                        with patch.object(ImageryValidator, 'validate_data_integrity', return_value=True):
                            result = loader.load_imagery(test_file)
        
        assert result is not None
        assert result['width'] == 1000
    
    def test_load_imagery_rasterio_error(self, tmp_path):
        """Test imagery loading with rasterio error."""
        test_file = tmp_path / "test.tif"
        test_file.touch()
        
        loader = ImageryLoader(validate=False)
        
        with patch('rasterio.open', side_effect=rasterio.errors.RasterioIOError("Mock error")):
            with pytest.raises(ImageryError, match="Failed to open imagery file"):
                loader.load_imagery(test_file)
    
    def test_load_sentinel2_bands_success(self, tmp_path, mock_dataset):
        """Test successful Sentinel-2 bands loading."""
        # Create mock band files
        (tmp_path / "B04_10m.jp2").touch()
        (tmp_path / "B08_10m.jp2").touch()
        
        loader = ImageryLoader(validate=False)
        
        with patch('rasterio.open', return_value=mock_dataset):
            result = loader.load_sentinel2_bands(tmp_path, ['B04', 'B08'])
        
        assert 'B04' in result
        assert 'B08' in result
        assert result['B04']['width'] == 1000
        assert result['B08']['width'] == 1000
    
    def test_load_sentinel2_bands_missing_band(self, tmp_path):
        """Test Sentinel-2 bands loading with missing band."""
        # Only create B04, missing B08
        (tmp_path / "B04_10m.jp2").touch()
        
        loader = ImageryLoader(validate=False)
        
        # Mock rasterio.open to simulate valid B04 file but missing B08
        with patch('rasterio.open') as mock_open:
            # Create a mock dataset for B04
            mock_dataset = Mock()
            mock_dataset.width = 1000
            mock_dataset.height = 1000
            mock_dataset.count = 1
            mock_dataset.dtypes = [np.dtype('uint16')]
            mock_dataset.crs = rasterio.crs.CRS.from_epsg(32633)
            mock_dataset.bounds = rasterio.coords.BoundingBox(400000, 5000000, 410000, 5010000)
            mock_dataset.transform = from_bounds(400000, 5000000, 410000, 5010000, 1000, 1000)
            mock_dataset.nodata = 0
            mock_open.return_value = mock_dataset
            
            with pytest.raises(ImageryError, match="Could not find band B08"):
                loader.load_sentinel2_bands(tmp_path, ['B04', 'B08'])
    
    def test_validate_band_consistency_success(self, mock_dataset):
        """Test successful band consistency validation."""
        loader = ImageryLoader()
        
        bands_data = {
            'B04': {
                'width': 1000,
                'height': 1000,
                'crs': 'EPSG:32633',
                'bounds': (400000, 5000000, 410000, 5010000)
            },
            'B08': {
                'width': 1000,
                'height': 1000,
                'crs': 'EPSG:32633',
                'bounds': (400000, 5000000, 410000, 5010000)
            }
        }
        
        # Should not raise an exception
        loader._validate_band_consistency(bands_data)
    
    def test_validate_band_consistency_dimension_mismatch(self):
        """Test band consistency validation with dimension mismatch."""
        loader = ImageryLoader()
        
        bands_data = {
            'B04': {
                'width': 1000,
                'height': 1000,
                'crs': 'EPSG:32633',
                'bounds': (400000, 5000000, 410000, 5010000)
            },
            'B08': {
                'width': 500,  # Different width
                'height': 1000,
                'crs': 'EPSG:32633',
                'bounds': (400000, 5000000, 410000, 5010000)
            }
        }
        
        with pytest.raises(ImageryError, match="dimensions.*do not match"):
            loader._validate_band_consistency(bands_data)
    
    def test_close_datasets(self):
        """Test closing dataset references."""
        mock_dataset1 = Mock()
        mock_dataset2 = Mock()
        
        bands_data = {
            'B04': {'dataset': mock_dataset1},
            'B08': {'dataset': mock_dataset2}
        }
        
        loader = ImageryLoader()
        loader.close_datasets(bands_data)
        
        mock_dataset1.close.assert_called_once()
        mock_dataset2.close.assert_called_once()
        assert bands_data['B04']['dataset'] is None
        assert bands_data['B08']['dataset'] is None


def test_load_imagery_safely_success(tmp_path):
    """Test safe imagery loading with success."""
    test_file = tmp_path / "test.tif"
    test_file.touch()
    
    # Create mock dataset for this test
    mock_dataset = Mock()
    mock_dataset.width = 1000
    mock_dataset.height = 1000
    mock_dataset.count = 1
    mock_dataset.dtypes = [np.dtype('uint16')]
    mock_dataset.crs = rasterio.crs.CRS.from_epsg(32633)
    mock_dataset.bounds = rasterio.coords.BoundingBox(400000, 5000000, 410000, 5010000)
    mock_dataset.transform = from_bounds(400000, 5000000, 410000, 5010000, 1000, 1000)
    mock_dataset.nodata = 0
    
    with patch('rasterio.open', return_value=mock_dataset):
        with patch.object(ImageryValidator, 'validate_file_format', return_value=True):
            with patch.object(ImageryValidator, 'validate_crs', return_value=True):
                with patch.object(ImageryValidator, 'validate_resolution', return_value=True):
                    with patch.object(ImageryValidator, 'validate_data_integrity', return_value=True):
                        result = load_imagery_safely(test_file)
    
    assert result is not None
    assert result['width'] == 1000


def test_load_imagery_safely_failure(tmp_path):
    """Test safe imagery loading with failure."""
    test_file = tmp_path / "nonexistent.tif"
    
    result = load_imagery_safely(test_file)
    assert result is None 