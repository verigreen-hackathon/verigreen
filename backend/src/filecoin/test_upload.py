#!/usr/bin/env python3
"""
Test script for Filecoin upload functionality.

This script demonstrates how to use the FilecoinService to upload files
and validates that the implementation works correctly.
"""

import asyncio
import os
import logging
import tempfile
from pathlib import Path

from . import (
    FilecoinService,
    upload_single_file,
    create_progress_logger,
    create_config_from_env,
    FilecoinUploadError,
    FilecoinValidationError
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_basic_functionality():
    """Test basic functionality without actually uploading."""
    logger.info("Testing basic FilecoinService functionality...")
    
    try:
        # Test configuration loading (will fail if env vars not set, which is expected)
        try:
            config = create_config_from_env()
            logger.info("Configuration loaded successfully")
        except Exception as e:
            logger.info(f"Expected configuration error (env vars not set): {e}")
            return False
        
        # Test service initialization
        async with FilecoinService(config) as service:
            logger.info("FilecoinService initialized successfully")
            
            # Test connection (will fail without proper auth, which is expected)
            try:
                await service.test_service()
                logger.info("Service test passed")
                return True
            except Exception as e:
                logger.info(f"Expected service test error (auth not configured): {e}")
                return False
                
    except Exception as e:
        logger.error(f"Unexpected error in basic functionality test: {e}")
        return False


async def test_file_validation():
    """Test file validation functionality."""
    logger.info("Testing file validation...")
    
    try:
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is a test file for upload validation.")
            test_file_path = f.name
        
        try:
            # Test with mock config (won't actually upload due to auth issues)
            from .client import StorachaConfig
            mock_config = StorachaConfig(
                auth_secret="test_secret",
                auth_token="test_token", 
                space_did="test_space_did"
            )
            
            async with FilecoinService(mock_config) as service:
                # Test file preparation (this should work)
                metadata = await service._prepare_file_metadata(test_file_path)
                
                logger.info(f"File metadata prepared successfully:")
                logger.info(f"  Filename: {metadata['filename']}")
                logger.info(f"  Size: {metadata['file_size']} bytes")
                logger.info(f"  Content type: {metadata['content_type']}")
                logger.info(f"  Checksum: {metadata['checksum_sha256']}")
                
                # Test with invalid file path
                try:
                    await service._prepare_file_metadata("/nonexistent/file.txt")
                    logger.error("Expected validation error for nonexistent file")
                    return False
                except FilecoinValidationError:
                    logger.info("Correctly caught validation error for nonexistent file")
                
                return True
                
        finally:
            # Clean up temporary file
            os.unlink(test_file_path)
            
    except Exception as e:
        logger.error(f"Error in file validation test: {e}")
        return False


async def test_progress_tracking():
    """Test progress tracking functionality."""
    logger.info("Testing progress tracking...")
    
    try:
        progress_updates = []
        
        def collect_progress(progress):
            progress_updates.append(progress)
            logger.info(
                f"Progress: {progress.filename} - {progress.percentage:.1f}% ({progress.stage})"
            )
        
        # Create mock config
        from .client import StorachaConfig
        mock_config = StorachaConfig(
            auth_secret="test_secret",
            auth_token="test_token",
            space_did="test_space_did"
        )
        
        # Test progress tracking
        async with FilecoinService(mock_config) as service:
            await service._track_upload_progress("test.txt", 1000, "preparing", collect_progress)
            await service._track_upload_progress("test.txt", 1000, "uploading", collect_progress)
            await service._track_upload_progress("test.txt", 1000, "verifying", collect_progress)
            await service._track_upload_progress("test.txt", 1000, "complete", collect_progress)
        
        if len(progress_updates) == 4:
            logger.info("Progress tracking test passed")
            return True
        else:
            logger.error(f"Expected 4 progress updates, got {len(progress_updates)}")
            return False
            
    except Exception as e:
        logger.error(f"Error in progress tracking test: {e}")
        return False


async def demo_upload_interface():
    """Demonstrate the upload interface (without actual upload)."""
    logger.info("Demonstrating upload interface...")
    
    try:
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is a demo file for the upload interface.")
            test_file_path = f.name
        
        try:
            # Show how the interface would be used with real credentials
            logger.info("Example usage with real credentials:")
            logger.info("""
# Set environment variables:
export STORACHA_AUTH_SECRET="your_auth_secret"
export STORACHA_AUTH_TOKEN="your_auth_token"  
export STORACHA_SPACE_DID="your_space_did"

# Then use the service:
async with FilecoinService() as service:
    metadata = await service.upload_file(
        file_path="path/to/file.txt",
        tags={"project": "verigreen", "type": "satellite_data"},
        progress_callback=create_progress_logger()
    )
    print(f"Uploaded: {metadata.content_cid}")
    
# Or use the convenience function:
metadata = await upload_single_file(
    "path/to/file.txt",
    tags={"project": "verigreen"},
    progress_callback=create_progress_logger()
)
""")
            
            return True
            
        finally:
            # Clean up temporary file
            os.unlink(test_file_path)
            
    except Exception as e:
        logger.error(f"Error in upload interface demo: {e}")
        return False


async def main():
    """Run all tests."""
    logger.info("Starting Filecoin upload functionality tests...")
    
    tests = [
        ("Basic Functionality", test_basic_functionality),
        ("File Validation", test_file_validation),
        ("Progress Tracking", test_progress_tracking),
        ("Upload Interface Demo", demo_upload_interface),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running test: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = await test_func()
            results.append((test_name, result))
            status = "PASSED" if result else "FAILED"
            logger.info(f"Test {test_name}: {status}")
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("All tests passed! The implementation is working correctly.")
    else:
        logger.warning("Some tests failed. Check the logs above for details.")


if __name__ == "__main__":
    asyncio.run(main()) 