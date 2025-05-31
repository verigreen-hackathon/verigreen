"""Tests for the metadata generation module."""

import pytest
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch
import numpy as np
from rasterio.coords import BoundingBox

from src.sentinel.metadata import (
    MetadataGenerator,
    TileMetadata,
    SourceImageryMetadata,
    MetadataError,
    create_source_imagery_metadata,
    generate_tile_metadata
)
from src.sentinel.grid import TileCoordinates
from src.sentinel.slicer import TileData


class TestSourceImageryMetadata:
    """Test cases for SourceImageryMetadata class."""
    
    def test_source_imagery_metadata_creation(self):
        """Test creating SourceImageryMetadata with various parameters."""
        metadata = SourceImageryMetadata(
            file_path="test.tif",
            acquisition_date="2024-01-15T10:30:00Z",
            satellite="Sentinel-2A",
            spatial_resolution=10.0,
            crs="EPSG:32633"
        )
        
        assert metadata.file_path == "test.tif"
        assert metadata.acquisition_date == "2024-01-15T10:30:00Z"
        assert metadata.satellite == "Sentinel-2A"
        assert metadata.spatial_resolution == 10.0
        assert metadata.crs == "EPSG:32633"
    
    def test_source_imagery_metadata_to_dict(self):
        """Test converting SourceImageryMetadata to dictionary."""
        metadata = SourceImageryMetadata(
            file_path="test.tif",
            satellite="Sentinel-2A",
            spatial_resolution=10.0
        )
        
        result = metadata.to_dict()
        
        assert isinstance(result, dict)
        assert result['file_path'] == "test.tif"
        assert result['satellite'] == "Sentinel-2A"
        assert result['spatial_resolution'] == 10.0
        assert 'acquisition_date' in result  # Should include None fields


class TestTileMetadata:
    """Test cases for TileMetadata class."""
    
    @pytest.fixture
    def sample_source_metadata(self):
        """Create sample source imagery metadata."""
        return SourceImageryMetadata(
            file_path="sentinel2.tif",
            satellite="Sentinel-2A",
            spatial_resolution=10.0,
            crs="EPSG:32633"
        )
    
    @pytest.fixture
    def sample_tile_metadata(self, sample_source_metadata):
        """Create sample tile metadata."""
        return TileMetadata(
            tile_id="x01_y02",
            unique_id=str(uuid.uuid4()),
            grid_position={'x': 1, 'y': 2},
            crs="EPSG:32633",
            bounds=[400320, 5000640, 400640, 5000960],
            center_coordinates=[50.0086, 7.0048],
            pixel_bounds=[32, 64, 64, 96],
            width=32,
            height=32,
            data_type="uint16",
            bands=["B04"],
            nodata_value=0,
            created_at=datetime.now(timezone.utc).isoformat(),
            processing_software="VeriGreen",
            processing_version="1.0.0",
            source_imagery=sample_source_metadata
        )
    
    def test_tile_metadata_creation(self, sample_tile_metadata):
        """Test creating TileMetadata object."""
        metadata = sample_tile_metadata
        
        assert metadata.tile_id == "x01_y02"
        assert metadata.grid_position == {'x': 1, 'y': 2}
        assert metadata.crs == "EPSG:32633"
        assert metadata.width == 32
        assert metadata.height == 32
        assert metadata.bands == ["B04"]
        assert metadata.processing_software == "VeriGreen"
    
    def test_tile_metadata_to_dict(self, sample_tile_metadata):
        """Test converting TileMetadata to dictionary."""
        result = sample_tile_metadata.to_dict()
        
        assert isinstance(result, dict)
        assert result['tile_id'] == "x01_y02"
        assert result['grid_position'] == {'x': 1, 'y': 2}
        assert result['width'] == 32
        assert result['height'] == 32
        assert 'source_imagery' in result
        assert isinstance(result['source_imagery'], dict)
    
    def test_tile_metadata_to_json(self, sample_tile_metadata):
        """Test converting TileMetadata to JSON string."""
        json_str = sample_tile_metadata.to_json()
        
        assert isinstance(json_str, str)
        
        # Parse back to verify it's valid JSON
        parsed = json.loads(json_str)
        assert parsed['tile_id'] == "x01_y02"
        assert parsed['width'] == 32
    
    def test_tile_metadata_to_geospatial_tags(self, sample_tile_metadata):
        """Test converting TileMetadata to geospatial tags."""
        tags = sample_tile_metadata.to_geospatial_tags()
        
        assert isinstance(tags, dict)
        assert tags['TILE_ID'] == "x01_y02"
        assert tags['GRID_X'] == "1"
        assert tags['GRID_Y'] == "2"
        assert tags['CENTER_LAT'] == "50.0086"
        assert tags['CENTER_LON'] == "7.0048"
        assert tags['PROCESSING_SOFTWARE'] == "VeriGreen"
        assert tags['BANDS'] == "B04"
        assert tags['CRS'] == "EPSG:32633"


class TestMetadataGenerator:
    """Test cases for MetadataGenerator class."""
    
    @pytest.fixture
    def sample_tile_data(self):
        """Create sample tile data."""
        coords = TileCoordinates(
            tile_id="x01_y02",
            grid_x=1,
            grid_y=2,
            pixel_bounds=(32, 64, 64, 96),
            geo_bounds=BoundingBox(400320, 5000640, 400640, 5000960),
            center_lat_lon=(50.0086, 7.0048)
        )
        
        data = np.random.randint(100, 1000, (32, 32), dtype=np.uint16)
        metadata = {'source_file': 'test.tif', 'nodata': 0}
        
        return TileData(coords, data, metadata, ['B04'])
    
    @pytest.fixture
    def sample_source_metadata(self):
        """Create sample source metadata dictionary."""
        return {
            'file_path': 'sentinel2.tif',
            'width': 1000,
            'height': 1000,
            'crs': 'EPSG:32633',
            'bounds': BoundingBox(400000, 5000000, 410000, 5010000),
            'resolution': {'x': 10.0, 'y': 10.0},
            'dtype': 'uint16',
            'nodata': 0
        }
    
    def test_metadata_generator_init_default(self):
        """Test MetadataGenerator initialization with default parameters."""
        generator = MetadataGenerator()
        
        assert generator.processing_software == "VeriGreen"
        assert generator.processing_version == "1.0.0"
        assert generator.include_statistics is True
        assert generator.include_quality_flags is False
    
    def test_metadata_generator_init_custom(self):
        """Test MetadataGenerator initialization with custom parameters."""
        generator = MetadataGenerator(
            processing_software="CustomSoft",
            processing_version="2.1.0",
            include_statistics=False,
            include_quality_flags=True
        )
        
        assert generator.processing_software == "CustomSoft"
        assert generator.processing_version == "2.1.0"
        assert generator.include_statistics is False
        assert generator.include_quality_flags is True
    
    def test_generate_tile_metadata_success(self, sample_tile_data, sample_source_metadata):
        """Test successful tile metadata generation."""
        generator = MetadataGenerator()
        
        with patch('uuid.uuid4') as mock_uuid:
            mock_uuid.return_value = Mock()
            mock_uuid.return_value.__str__ = Mock(return_value="test-uuid-123")
            
            with patch('src.sentinel.metadata.datetime') as mock_datetime:
                mock_now = Mock()
                mock_now.isoformat.return_value = "2024-01-15T10:30:00Z"
                mock_datetime.now.return_value = mock_now
                mock_datetime.timezone = timezone
                
                metadata = generator.generate_tile_metadata(
                    sample_tile_data, sample_source_metadata
                )
        
        assert isinstance(metadata, TileMetadata)
        assert metadata.tile_id == "x01_y02"
        assert metadata.unique_id == "test-uuid-123"
        assert metadata.grid_position == {'x': 1, 'y': 2}
        assert metadata.crs == "EPSG:32633"
        assert metadata.width == 32
        assert metadata.height == 32
        assert metadata.bands == ['B04']
        assert metadata.processing_software == "VeriGreen"
        assert metadata.created_at == "2024-01-15T10:30:00Z"
        assert metadata.statistics is not None  # Should include statistics
    
    def test_generate_tile_metadata_with_source_imagery_info(self, sample_tile_data, sample_source_metadata):
        """Test tile metadata generation with provided source imagery info."""
        generator = MetadataGenerator()
        
        source_imagery_info = SourceImageryMetadata(
            file_path="custom.tif",
            satellite="Sentinel-2B",
            acquisition_date="2024-01-01T12:00:00Z"
        )
        
        metadata = generator.generate_tile_metadata(
            sample_tile_data, sample_source_metadata, source_imagery_info
        )
        
        assert metadata.source_imagery.file_path == "custom.tif"
        assert metadata.source_imagery.satellite == "Sentinel-2B"
        assert metadata.source_imagery.acquisition_date == "2024-01-01T12:00:00Z"
    
    def test_generate_tile_metadata_with_quality_flags(self, sample_tile_data, sample_source_metadata):
        """Test tile metadata generation with quality flags enabled."""
        generator = MetadataGenerator(include_quality_flags=True)
        
        metadata = generator.generate_tile_metadata(
            sample_tile_data, sample_source_metadata
        )
        
        assert metadata.quality_flags is not None
        assert 'has_data' in metadata.quality_flags
        assert 'data_completeness' in metadata.quality_flags
        assert 'nodata_percentage' in metadata.quality_flags
        assert 'data_range_valid' in metadata.quality_flags
    
    def test_generate_batch_metadata(self, sample_source_metadata):
        """Test batch metadata generation."""
        generator = MetadataGenerator()
        
        # Create multiple tile data objects
        tiles = []
        for i in range(3):
            coords = TileCoordinates(
                tile_id=f"x{i:02d}_y00",
                grid_x=i,
                grid_y=0,
                pixel_bounds=(i*32, 0, (i+1)*32, 32),
                geo_bounds=BoundingBox(400000 + i*320, 5000000, 400320 + i*320, 5000320),
                center_lat_lon=(50.0, 7.0 + i*0.01)
            )
            
            data = np.random.randint(100, 1000, (32, 32), dtype=np.uint16)
            metadata = {'source_file': 'test.tif'}
            
            tile_data = TileData(coords, data, metadata, ['B04'])
            tiles.append(tile_data)
        
        metadata_list = generator.generate_batch_metadata(tiles, sample_source_metadata)
        
        assert len(metadata_list) == 3
        assert all(isinstance(meta, TileMetadata) for meta in metadata_list)
        assert metadata_list[0].tile_id == "x00_y00"
        assert metadata_list[1].tile_id == "x01_y00"
        assert metadata_list[2].tile_id == "x02_y00"
    
    def test_assess_tile_quality(self, sample_tile_data):
        """Test tile quality assessment."""
        generator = MetadataGenerator()
        
        quality_flags = generator._assess_tile_quality(sample_tile_data)
        
        assert isinstance(quality_flags, dict)
        assert 'has_data' in quality_flags
        assert 'data_completeness' in quality_flags
        assert 'nodata_percentage' in quality_flags
        assert 'data_range_valid' in quality_flags
        
        # For sample data with no zeros, should have complete data
        assert quality_flags['has_data'] == True
        assert quality_flags['data_completeness'] == 1.0
        assert quality_flags['nodata_percentage'] == 0.0
    
    def test_assess_tile_quality_with_nodata(self):
        """Test quality assessment with nodata values."""
        generator = MetadataGenerator()
        
        # Create tile with some nodata (zero) values
        coords = TileCoordinates(
            tile_id="x01_y02",
            grid_x=1,
            grid_y=2,
            pixel_bounds=(32, 64, 64, 96),
            geo_bounds=BoundingBox(400320, 5000640, 400640, 5000960),
            center_lat_lon=(50.0086, 7.0048)
        )
        
        data = np.ones((32, 32), dtype=np.uint16) * 100
        data[:10, :10] = 0  # Set some pixels to nodata
        
        tile_data = TileData(coords, data, {}, ['B04'])
        
        quality_flags = generator._assess_tile_quality(tile_data)
        
        assert quality_flags['has_data'] == True
        assert quality_flags['data_completeness'] < 1.0
        assert quality_flags['nodata_percentage'] > 0.0
        # 100 pixels out of 1024 total = 9.765625%
        assert abs(quality_flags['nodata_percentage'] - 9.765625) < 0.1
    
    def test_save_metadata_json_single(self, sample_tile_data, sample_source_metadata, tmp_path):
        """Test saving single metadata to JSON file."""
        generator = MetadataGenerator()
        metadata = generator.generate_tile_metadata(sample_tile_data, sample_source_metadata)
        
        output_path = tmp_path / "metadata.json"
        result_path = generator.save_metadata_json(metadata, output_path)
        
        assert result_path == output_path
        assert output_path.exists()
        
        # Read and verify content
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert data['tile_id'] == "x01_y02"
        assert data['width'] == 32
        assert data['height'] == 32
    
    def test_save_metadata_json_multiple(self, sample_source_metadata, tmp_path):
        """Test saving multiple metadata objects to JSON file."""
        generator = MetadataGenerator()
        
        # Create multiple metadata objects
        metadata_list = []
        for i in range(2):
            coords = TileCoordinates(
                tile_id=f"x{i:02d}_y00",
                grid_x=i,
                grid_y=0,
                pixel_bounds=(i*32, 0, (i+1)*32, 32),
                geo_bounds=BoundingBox(400000, 5000000, 400320, 5000320),
                center_lat_lon=(50.0, 7.0)
            )
            
            data = np.ones((32, 32), dtype=np.uint16) * 100
            tile_data = TileData(coords, data, {}, ['B04'])
            
            metadata = generator.generate_tile_metadata(tile_data, sample_source_metadata)
            metadata_list.append(metadata)
        
        output_path = tmp_path / "batch_metadata.json"
        result_path = generator.save_metadata_json(metadata_list, output_path)
        
        assert result_path == output_path
        assert output_path.exists()
        
        # Read and verify content
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]['tile_id'] == "x00_y00"
        assert data[1]['tile_id'] == "x01_y00"
    
    def test_create_collection_metadata(self, sample_source_metadata):
        """Test creating collection-level metadata."""
        generator = MetadataGenerator()
        
        # Create multiple metadata objects
        metadata_list = []
        for i in range(4):
            for j in range(2):
                coords = TileCoordinates(
                    tile_id=f"x{i:02d}_y{j:02d}",
                    grid_x=i,
                    grid_y=j,
                    pixel_bounds=(i*32, j*32, (i+1)*32, (j+1)*32),
                    geo_bounds=BoundingBox(400000 + i*320, 5000000 + j*320, 400320 + i*320, 5000320 + j*320),
                    center_lat_lon=(50.0 + j*0.01, 7.0 + i*0.01)
                )
                
                data = np.ones((32, 32), dtype=np.uint16) * 100
                tile_data = TileData(coords, data, {}, ['B04'])
                
                metadata = generator.generate_tile_metadata(tile_data, sample_source_metadata)
                metadata_list.append(metadata)
        
        collection_metadata = generator.create_collection_metadata(
            metadata_list, "Test Collection"
        )
        
        assert collection_metadata['collection_name'] == "Test Collection"
        assert collection_metadata['tile_count'] == 8
        assert 'created_at' in collection_metadata
        assert 'spatial_extent' in collection_metadata
        assert 'grid_extent' in collection_metadata
        assert collection_metadata['bands'] == ['B04']
        assert collection_metadata['tile_size'] == {'width': 32, 'height': 32}
        
        # Check spatial extent
        spatial_extent = collection_metadata['spatial_extent']
        assert 'bounds' in spatial_extent
        assert spatial_extent['crs'] == 'EPSG:32633'
        
        # Check grid extent
        grid_extent = collection_metadata['grid_extent']
        assert grid_extent['x_range'] == [0, 3]
        assert grid_extent['y_range'] == [0, 1]
        assert grid_extent['grid_size'] == [4, 2]


def test_create_source_imagery_metadata_function():
    """Test the convenience function for creating source imagery metadata."""
    metadata = create_source_imagery_metadata(
        file_path="test.tif",
        acquisition_date="2024-01-15T10:30:00Z",
        satellite="Sentinel-2A",
        spatial_resolution=10.0
    )
    
    assert isinstance(metadata, SourceImageryMetadata)
    assert metadata.file_path == "test.tif"
    assert metadata.acquisition_date == "2024-01-15T10:30:00Z"
    assert metadata.satellite == "Sentinel-2A"
    assert metadata.spatial_resolution == 10.0


def test_generate_tile_metadata_convenience_function():
    """Test the convenience function for generating tile metadata."""
    coords = TileCoordinates(
        tile_id="x01_y02",
        grid_x=1,
        grid_y=2,
        pixel_bounds=(32, 64, 64, 96),
        geo_bounds=BoundingBox(400320, 5000640, 400640, 5000960),
        center_lat_lon=(50.0086, 7.0048)
    )
    
    data = np.ones((32, 32), dtype=np.uint16) * 100
    tile_data = TileData(coords, data, {}, ['B04'])
    
    source_metadata = {
        'file_path': 'test.tif',
        'crs': 'EPSG:32633',
        'resolution': {'x': 10.0, 'y': 10.0}
    }
    
    metadata = generate_tile_metadata(
        tile_data, source_metadata, include_statistics=False
    )
    
    assert isinstance(metadata, TileMetadata)
    assert metadata.tile_id == "x01_y02"
    assert metadata.statistics is None  # Should be None since include_statistics=False 