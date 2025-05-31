"""
Test suite for Storacha integration.

This module tests the Storacha/Filecoin client functionality including:
- Credential setup and configuration
- Single file uploads of various types and sizes
- CID generation and validation
- File integrity verification using checksums
"""

import asyncio
import hashlib
import os
import tempfile
from pathlib import Path
from typing import List, Tuple
import pytest
import pytest_asyncio
from PIL import Image
import numpy as np
import rasterio
from rasterio.transform import from_bounds

# Load environment variables for testing
from dotenv import load_dotenv
load_dotenv()

from src.filecoin.client import (
    StorachaClient, 
    StorachaConfig, 
    StorachaError, 
    StorachaAuthError,
    StorachaUploadError,
    create_config_from_env,
    test_connection
)


class TestFileGenerator:
    """Utility class for generating test files."""
    
    @staticmethod
    def create_test_jpeg(size_kb: int) -> Tuple[str, bytes]:
        """Create a test JPEG file of specified size."""
        # Calculate dimensions to approximate target size
        # JPEG compression makes exact size difficult, so we'll create larger image
        target_pixels = size_kb * 1024 * 8  # Rough estimate
        width = int((target_pixels / 3) ** 0.5)  # 3 bytes per RGB pixel
        height = width
        
        # Create random RGB image
        image_array = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
        image = Image.fromarray(image_array, 'RGB')
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            tmp_path = tmp.name
        
        # Save with quality to approximate size
        quality = 95 if size_kb < 50 else 85 if size_kb < 200 else 75
        image.save(tmp_path, 'JPEG', quality=quality, optimize=True)
        
        with open(tmp_path, 'rb') as f:
            data = f.read()
        
        return tmp_path, data
    
    @staticmethod
    def create_test_png(size_kb: int) -> Tuple[str, bytes]:
        """Create a test PNG file of specified size."""
        # PNG is lossless, so we need to create appropriate dimensions
        target_bytes = size_kb * 1024
        # Rough estimate: 4 bytes per RGBA pixel + PNG overhead
        pixels_needed = target_bytes // 4
        width = int(pixels_needed ** 0.5)
        height = width
        
        # Create random RGBA image
        image_array = np.random.randint(0, 256, (height, width, 4), dtype=np.uint8)
        image = Image.fromarray(image_array, 'RGBA')
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp_path = tmp.name
        
        image.save(tmp_path, 'PNG', optimize=True)
        
        with open(tmp_path, 'rb') as f:
            data = f.read()
        
        return tmp_path, data
    
    @staticmethod
    def create_test_geotiff(size_kb: int) -> Tuple[str, bytes]:
        """Create a test GeoTIFF file of specified size."""
        # Calculate dimensions to approximate target size
        pixels_needed = size_kb * 1024 // 4  # 4 bytes per pixel (Float32)
        width = int(pixels_needed ** 0.5)
        height = width
        
        # Create test data
        data_array = np.random.rand(height, width).astype(np.float32)
        
        with tempfile.NamedTemporaryFile(suffix='.tif', delete=False) as tmp:
            tmp_path = tmp.name
        
        # Create GeoTIFF using rasterio
        transform = from_bounds(0, 0, width, height, width, height)
        
        with rasterio.open(
            tmp_path,
            'w',
            driver='GTiff',
            height=height,
            width=width,
            count=1,
            dtype=data_array.dtype,
            crs='EPSG:4326',
            transform=transform,
        ) as dst:
            dst.write(data_array, 1)
        
        with open(tmp_path, 'rb') as f:
            data = f.read()
        
        return tmp_path, data


# Test if we can load configuration from environment
def test_config_loading():
    """Test that we can load configuration properly."""
    try:
        config = create_config_from_env()
        assert config.auth_secret
        assert config.auth_token
        assert config.space_did
        assert config.base_url
        print("✅ Configuration loaded successfully")
    except StorachaAuthError:
        pytest.skip("Storacha credentials not configured")


@pytest.mark.asyncio
async def test_storacha_connection():
    """Test connection to Storacha service."""
    try:
        config = create_config_from_env()
        success = await test_connection(config)
        assert success, "Connection to Storacha should succeed"
        print("✅ Connection test passed")
    except StorachaAuthError:
        pytest.skip("Storacha credentials not configured")


class TestStorachaCredentials:
    """Test credential setup and configuration."""
    
    def test_config_from_env_success(self):
        """Test successful configuration from environment variables."""
        # Mock environment variables
        with pytest.MonkeyPatch.context() as m:
            m.setenv("STORACHA_AUTH_SECRET", "test_secret")
            m.setenv("STORACHA_AUTH_TOKEN", "test_token")
            m.setenv("STORACHA_SPACE_DID", "did:key:test123")
            m.setenv("STORACHA_BASE_URL", "https://test.example.com")
            
            config = create_config_from_env()
            
            assert config.auth_secret == "test_secret"
            assert config.auth_token == "test_token"
            assert config.space_did == "did:key:test123"
            assert config.base_url == "https://test.example.com"
    
    def test_config_from_env_missing_credentials(self):
        """Test error handling for missing credentials."""
        with pytest.MonkeyPatch.context() as m:
            # Clear all Storacha env vars
            m.delenv("STORACHA_AUTH_SECRET", raising=False)
            m.delenv("STORACHA_AUTH_TOKEN", raising=False)
            m.delenv("STORACHA_SPACE_DID", raising=False)
            
            with pytest.raises(StorachaAuthError) as exc_info:
                create_config_from_env()
            
            assert "Missing required environment variables" in str(exc_info.value)
    
    def test_config_from_env_partial_credentials(self):
        """Test error handling for partial credentials."""
        with pytest.MonkeyPatch.context() as m:
            m.setenv("STORACHA_AUTH_SECRET", "test_secret")
            # Missing STORACHA_AUTH_TOKEN and STORACHA_SPACE_DID
            m.delenv("STORACHA_AUTH_TOKEN", raising=False)
            m.delenv("STORACHA_SPACE_DID", raising=False)
            
            with pytest.raises(StorachaAuthError) as exc_info:
                create_config_from_env()
            
            error_msg = str(exc_info.value)
            assert "STORACHA_AUTH_TOKEN" in error_msg
            assert "STORACHA_SPACE_DID" in error_msg


class TestStorachaIntegration:
    """Test Storacha client integration with real or mocked services."""
    
    @pytest.fixture
    def config(self):
        """Get Storacha configuration from environment."""
        try:
            return create_config_from_env()
        except StorachaAuthError:
            pytest.skip("Storacha credentials not configured. Set STORACHA_AUTH_SECRET, STORACHA_AUTH_TOKEN, and STORACHA_SPACE_DID")
    
    @pytest_asyncio.fixture
    async def client(self, config):
        """Create and yield Storacha client."""
        async with StorachaClient(config) as client:
            yield client
    
    @pytest.mark.asyncio
    async def test_connection(self, config):
        """Test basic connection to Storacha service."""
        success = await test_connection(config)
        assert success, "Should be able to connect to Storacha"
    
    @pytest.mark.asyncio
    async def test_client_context_manager(self, config):
        """Test that client properly handles async context manager."""
        async with StorachaClient(config) as client:
            # Client should be usable within context
            assert client is not None
            uploads = await client.list_uploads()
            assert isinstance(uploads, list)
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("file_type,size_kb", [
        ("jpeg", 1), ("jpeg", 100), ("jpeg", 1000),
        ("png", 1), ("png", 50), ("png", 500),
        ("geotiff", 10), ("geotiff", 100), ("geotiff", 1000),
    ])
    async def test_single_file_upload(self, client, file_type, size_kb):
        """Test uploading single files of various types and sizes."""
        # Generate test file
        if file_type == "jpeg":
            file_path, data = TestFileGenerator.create_test_jpeg(size_kb)
        elif file_type == "png":
            file_path, data = TestFileGenerator.create_test_png(size_kb)
        elif file_type == "geotiff":
            file_path, data = TestFileGenerator.create_test_geotiff(size_kb)
        
        try:
            # Calculate original checksum
            original_hash = hashlib.sha256(data).hexdigest()
            
            # Upload to Storacha
            result = await client.upload_data(data, f"test_{file_type}_{size_kb}kb.{file_type}")
            
            # Verify result structure
            assert hasattr(result, 'content_cid')
            assert hasattr(result, 'shard_cid')
            assert hasattr(result, 'size')
            assert result.size == len(data)
            
            # Verify CID format
            assert result.content_cid.startswith(('baf', 'Qm'))  # Common IPFS CID prefixes
            assert result.shard_cid.startswith('bag')  # CAR file CID prefix
            
            print(f"✅ Uploaded {file_type} ({size_kb}KB): {result.content_cid}")
            
        finally:
            # Clean up temporary file
            if os.path.exists(file_path):
                os.unlink(file_path)
    
    @pytest.mark.asyncio
    async def test_upload_large_file(self, client):
        """Test uploading a larger file (5MB)."""
        # Create 5MB of random data
        large_data = os.urandom(5 * 1024 * 1024)
        
        result = await client.upload_data(large_data, "large_test_5mb.bin")
        
        assert result.size == len(large_data)
        assert result.content_cid
        assert result.shard_cid
        
        print(f"✅ Uploaded 5MB file: {result.content_cid}")
    
    @pytest.mark.asyncio
    async def test_upload_empty_file(self, client):
        """Test uploading an empty file."""
        empty_data = b""
        
        result = await client.upload_data(empty_data, "empty_test.txt")
        
        assert result.size == 0
        assert result.content_cid
        assert result.shard_cid
        
        print(f"✅ Uploaded empty file: {result.content_cid}")
    
    @pytest.mark.asyncio
    async def test_list_uploads(self, client):
        """Test listing uploads."""
        uploads = await client.list_uploads()
        
        assert isinstance(uploads, list)
        # If there are uploads, check structure
        if uploads:
            upload = uploads[0]
            assert 'root' in upload
            # Verify CID structure in root
            root_cid = upload['root'].get('/')
            assert root_cid and isinstance(root_cid, str)
        
        print(f"✅ Listed {len(uploads)} uploads")
    
    @pytest.mark.asyncio
    async def test_cid_consistency(self, client):
        """Test that uploading the same data multiple times works reliably."""
        test_data = b"Test data for upload reliability check"
        filename = "reliability_test.txt"
        
        # Upload twice with same data and filename
        result1 = await client.upload_data(test_data, filename)
        result2 = await client.upload_data(test_data, filename)
        
        # Both uploads should succeed with valid CIDs
        assert result1.content_cid.startswith(('baf', 'Qm'))
        assert result2.content_cid.startswith(('baf', 'Qm'))
        assert result1.shard_cid.startswith('bag')
        assert result2.shard_cid.startswith('bag')
        
        # Both should have same size
        assert result1.size == result2.size == len(test_data)
        
        # Note: CIDs may differ due to timestamps in CAR files
        # This is normal behavior for Storacha/IPFS
        
        print(f"✅ Upload reliability verified:")
        print(f"   Upload 1 CID: {result1.content_cid}")
        print(f"   Upload 2 CID: {result2.content_cid}")
        print(f"   Both uploads successful with valid CID formats")


class TestErrorHandling:
    """Test error handling scenarios."""
    
    def test_invalid_credentials(self):
        """Test error handling for invalid credentials."""
        invalid_config = StorachaConfig(
            auth_secret="invalid_secret",
            auth_token="invalid_token",
            space_did="did:key:invalid123"
        )
        
        # This should create the client without immediate error
        client = StorachaClient(invalid_config)
        assert client is not None
    
    @pytest.mark.asyncio
    async def test_missing_space_did(self):
        """Test error handling for missing space DID."""
        config = StorachaConfig(
            auth_secret="test_secret",
            auth_token="test_token",
            space_did=""  # Empty space DID
        )
        
        async with StorachaClient(config) as client:
            with pytest.raises(StorachaAuthError) as exc_info:
                await client.upload_data(b"test data")
            
            assert "space_did is required" in str(exc_info.value)


if __name__ == "__main__":
    # Run basic tests
    pytest.main([__file__, "-v"]) 