#!/usr/bin/env python3
"""
Test script for CID Management System.

This script demonstrates and tests the CID validation, registry management,
and network checking functionality.
"""

import asyncio
import os
import logging
import tempfile
from datetime import datetime
from pathlib import Path

from . import (
    CIDManager,
    CIDValidator,
    CIDRegistry,
    CIDNetworkChecker,
    CIDInfo,
    CIDRegistryEntry,
    CIDAvailabilityResult,
    validate_cid,
    check_cid_available,
    normalize_cid_format
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_cid_validation():
    """Test CID validation functionality."""
    logger.info("Testing CID validation...")
    
    # Test valid CIDs
    valid_cids = [
        "QmYjtig7VJQ6XsnUjqqJvj7QaMcCAwtrgNdahSiFofrE7o",  # CIDv0
        "bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi",  # CIDv1 base32
        "zdj7WWeQ43G6JJvLWQWZpyHuAMq6uYWRjkBXFad11vE2LHhQ7",  # CIDv1 base58btc
    ]
    
    # Test invalid CIDs
    invalid_cids = [
        "invalid-cid",
        "QmInvalid",  # Too short
        "bafyinvalid",  # Invalid base32
        "",  # Empty
        None,  # None
        123  # Not a string
    ]
    
    validator = CIDValidator()
    
    # Test valid CIDs
    for cid in valid_cids:
        try:
            if validator.is_valid_cid(cid):
                info = validator.parse_cid(cid)
                logger.info(f"✅ Valid CID: {cid}")
                logger.info(f"   Version: {info.version}, Encoding: {info.base_encoding}")
            else:
                logger.error(f"❌ CID marked as invalid but should be valid: {cid}")
                return False
        except Exception as e:
            logger.error(f"❌ Error validating valid CID {cid}: {e}")
            return False
    
    # Test invalid CIDs
    for cid in invalid_cids:
        try:
            if validator.is_valid_cid(cid):
                logger.error(f"❌ CID marked as valid but should be invalid: {cid}")
                return False
            else:
                logger.info(f"✅ Correctly identified invalid CID: {cid}")
        except Exception as e:
            logger.debug(f"Expected error for invalid CID {cid}: {e}")
    
    logger.info("CID validation tests passed!")
    return True


async def test_cid_registry():
    """Test CID registry functionality."""
    logger.info("Testing CID registry...")
    
    # Create temporary registry
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
        registry_path = temp_db.name
    
    try:
        registry = CIDRegistry(registry_path)
        
        # Test registering a CID
        test_entry = CIDRegistryEntry(
            local_file_path="/test/file.txt",
            content_cid="QmYjtig7VJQ6XsnUjqqJvj7QaMcCAwtrgNdahSiFofrE7o",
            shard_cids=["QmYwAPJzv5CZsnA625s3Xf2nemtYgPpHdWEz79ojWnPbdG", "QmPCwvzNxWqmgNkMTF1QCKKhEh1aK1HJMTjQQ8r9U4qJ1h"],
            file_size=1024,
            upload_timestamp=datetime.utcnow(),
            metadata={"test": "data"},
            tags={"project": "verigreen"}
        )
        
        await registry.register_cid(test_entry)
        logger.info("✅ CID registered successfully")
        
        # Test retrieving by file path
        retrieved_entry = await registry.get_cid_by_file_path("/test/file.txt")
        if retrieved_entry and retrieved_entry.content_cid == test_entry.content_cid:
            logger.info("✅ CID retrieved by file path successfully")
        else:
            logger.error("❌ Failed to retrieve CID by file path")
            return False
        
        # Test retrieving by CID
        retrieved_by_cid = await registry.get_entry_by_cid(test_entry.content_cid)
        if retrieved_by_cid and retrieved_by_cid.local_file_path == test_entry.local_file_path:
            logger.info("✅ Entry retrieved by CID successfully")
        else:
            logger.error("❌ Failed to retrieve entry by CID")
            return False
        
        # Test listing entries
        all_entries = await registry.list_all_entries()
        if len(all_entries) == 1 and all_entries[0].content_cid == test_entry.content_cid:
            logger.info("✅ Registry listing works correctly")
        else:
            logger.error("❌ Registry listing failed")
            return False
        
        # Test updating availability status
        await registry.update_availability_status(
            test_entry.content_cid, 
            "available", 
            datetime.utcnow()
        )
        
        updated_entry = await registry.get_entry_by_cid(test_entry.content_cid)
        if updated_entry.availability_status == "available":
            logger.info("✅ Availability status updated successfully")
        else:
            logger.error("❌ Failed to update availability status")
            return False
        
        # Test removing entry
        removed = await registry.remove_entry(test_entry.content_cid)
        if removed:
            logger.info("✅ Entry removed successfully")
        else:
            logger.error("❌ Failed to remove entry")
            return False
        
        # Verify entry is gone
        check_entry = await registry.get_entry_by_cid(test_entry.content_cid)
        if check_entry is None:
            logger.info("✅ Entry removal verified")
        else:
            logger.error("❌ Entry still exists after removal")
            return False
        
        logger.info("CID registry tests passed!")
        return True
        
    finally:
        # Clean up temporary file
        try:
            os.unlink(registry_path)
        except:
            pass


async def test_network_checker():
    """Test CID network checking functionality."""
    logger.info("Testing CID network checker...")
    
    # Use a well-known CID that should be available
    # This is the CID for the IPFS README file
    test_cid = "QmYwAPJzv5CZsnA625s3Xf2nemtYgPpHdWEz79ojWnPbdG"
    
    checker = CIDNetworkChecker(timeout=10)
    
    # Test availability check
    result = await checker.check_cid_availability(test_cid)
    
    logger.info(f"CID: {result.cid}")
    logger.info(f"Available: {result.is_available}")
    logger.info(f"Response time: {result.response_time_ms}ms")
    logger.info(f"Gateway: {result.gateway_url}")
    
    if result.error_message:
        logger.info(f"Error: {result.error_message}")
    
    # Test with invalid CID
    invalid_cid = "invalid-cid-format"
    invalid_result = await checker.check_cid_availability(invalid_cid)
    
    if not invalid_result.is_available and "Invalid CID format" in invalid_result.error_message:
        logger.info("✅ Invalid CID correctly handled")
    else:
        logger.error("❌ Invalid CID not handled correctly")
        return False
    
    # Test metadata retrieval (only if CID is available)
    if result.is_available:
        metadata = await checker.get_file_metadata_from_cid(test_cid)
        if metadata:
            logger.info("✅ File metadata retrieved successfully")
            logger.info(f"   Content Type: {metadata.get('content_type')}")
            logger.info(f"   Content Length: {metadata.get('content_length')}")
        else:
            logger.warning("⚠️  No metadata retrieved (may be expected)")
    
    logger.info("CID network checker tests completed!")
    return True


async def test_cid_manager_integration():
    """Test the integrated CID manager functionality."""
    logger.info("Testing CID manager integration...")
    
    # Create temporary registry
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
        registry_path = temp_db.name
    
    try:
        async with CIDManager(registry_path=registry_path) as manager:
            # Test CID validation through manager
            test_cid = "QmYjtig7VJQ6XsnUjqqJvj7QaMcCAwtrgNdahSiFofrE7o"
            
            if manager.is_valid_cid(test_cid):
                logger.info("✅ CID validation through manager works")
            else:
                logger.error("❌ CID validation through manager failed")
                return False
            
            # Test CID normalization
            normalized = manager.normalize_cid(test_cid)
            logger.info(f"✅ CID normalized: {normalized}")
            
            # Test registering an upload
            await manager.register_upload(
                file_path="/test/integration.txt",
                content_cid=test_cid,
                shard_cids=["QmYwAPJzv5CZsnA625s3Xf2nemtYgPpHdWEz79ojWnPbdG", "QmPCwvzNxWqmgNkMTF1QCKKhEh1aK1HJMTjQQ8r9U4qJ1h"],
                file_size=2048,
                metadata={"source": "integration_test"},
                tags={"test": "integration"}
            )
            logger.info("✅ Upload registered through manager")
            
            # Test getting CID for file
            retrieved_cid = await manager.get_cid_for_file("/test/integration.txt")
            if retrieved_cid == test_cid:
                logger.info("✅ CID retrieved for file path")
            else:
                logger.error("❌ Failed to retrieve CID for file path")
                return False
            
            # Test getting file for CID
            retrieved_file = await manager.get_file_for_cid(test_cid)
            if retrieved_file == "/test/integration.txt":
                logger.info("✅ File path retrieved for CID")
            else:
                logger.error("❌ Failed to retrieve file path for CID")
                return False
            
            # Test listing managed CIDs
            managed_cids = await manager.list_managed_cids()
            if len(managed_cids) == 1 and managed_cids[0].content_cid == test_cid:
                logger.info("✅ Managed CIDs listed correctly")
            else:
                logger.error("❌ Failed to list managed CIDs correctly")
                return False
            
            # Test availability check through manager
            availability = await manager.check_cid_availability(test_cid)
            logger.info(f"✅ Availability check completed: {availability.is_available}")
            
            # Test export
            export_path = registry_path + ".export.json"
            await manager.export_registry(export_path)
            
            if os.path.exists(export_path):
                logger.info("✅ Registry exported successfully")
                os.unlink(export_path)  # Clean up
            else:
                logger.error("❌ Registry export failed")
                return False
        
        logger.info("CID manager integration tests passed!")
        return True
        
    finally:
        # Clean up temporary files
        try:
            os.unlink(registry_path)
        except:
            pass


async def test_utility_functions():
    """Test utility functions."""
    logger.info("Testing utility functions...")
    
    # Test validate_cid function
    test_cid = "QmYjtig7VJQ6XsnUjqqJvj7QaMcCAwtrgNdahSiFofrE7o"
    cid_info = await validate_cid(test_cid)
    
    if cid_info.is_valid and cid_info.cid == test_cid:
        logger.info("✅ validate_cid utility function works")
    else:
        logger.error("❌ validate_cid utility function failed")
        return False
    
    # Test normalize_cid_format function
    normalized = await normalize_cid_format(test_cid)
    logger.info(f"✅ normalize_cid_format works: {normalized}")
    
    # Test check_cid_available function (with timeout)
    try:
        is_available = await asyncio.wait_for(
            check_cid_available(test_cid), 
            timeout=10
        )
        logger.info(f"✅ check_cid_available works: {is_available}")
    except asyncio.TimeoutError:
        logger.warning("⚠️  check_cid_available timed out (may be expected)")
    
    logger.info("Utility function tests completed!")
    return True


async def demo_usage_examples():
    """Demonstrate typical usage patterns."""
    logger.info("Demonstrating usage examples...")
    
    logger.info("""
## Example Usage Patterns for CID Management:

### 1. Basic CID Validation:
```python
from filecoin import CIDValidator, validate_cid

# Quick validation
is_valid = CIDValidator.is_valid_cid("QmYjtig7VJQ6XsnUjqqJvj7QaMcCAwtrgNdahSiFofrE7o")

# Detailed validation with info
cid_info = await validate_cid("QmYjtig7VJQ6XsnUjqqJvj7QaMcCAwtrgNdahSiFofrE7o")
print(f"Version: {cid_info.version}, Encoding: {cid_info.base_encoding}")
```

### 2. CID Registry Management:
```python
from filecoin import CIDRegistry, CIDRegistryEntry
from datetime import datetime

registry = CIDRegistry("my_project_registry.db")

# Register a file upload
entry = CIDRegistryEntry(
    local_file_path="data/satellite_image.jpg",
    content_cid="bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi",
    shard_cids=["shard1_cid", "shard2_cid"],
    file_size=1048576,
    upload_timestamp=datetime.utcnow(),
    tags={"project": "verigreen", "type": "satellite_data"}
)

await registry.register_cid(entry)

# Look up files by CID
file_path = await registry.get_cid_by_file_path("data/satellite_image.jpg")
```

### 3. Network Availability Checking:
```python
from filecoin import CIDNetworkChecker, check_cid_available

# Quick availability check
is_available = await check_cid_available("QmYjtig7VJQ6XsnUjqqJvj7QaMcCAwtrgNdahSiFofrE7o")

# Detailed availability check
checker = CIDNetworkChecker()
result = await checker.check_cid_availability("QmYjtig7VJQ6XsnUjqqJvj7QaMcCAwtrgNdahSiFofrE7o")
print(f"Available: {result.is_available}, Response time: {result.response_time_ms}ms")
```

### 4. Integrated CID Management:
```python
from filecoin import CIDManager

async with CIDManager(registry_path="verigreen_cids.db") as manager:
    # Register upload results
    await manager.register_upload(
        file_path="uploads/tile_001.png",
        content_cid="bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi",
        shard_cids=["shard1", "shard2"],
        file_size=524288,
        tags={"tile": "001", "processed": "true"}
    )
    
    # Check what files are managed
    managed_files = await manager.list_managed_cids()
    
    # Verify all CIDs are still available
    results = await manager.verify_all_managed_cids()
    
    # Export registry for backup
    await manager.export_registry("backup/cid_registry_backup.json")
```

### 5. Integration with File Upload Service:
```python
from filecoin import FilecoinService, CIDManager

async with FilecoinService() as upload_service, \\
           CIDManager() as cid_manager:
    
    # Upload file
    metadata = await upload_service.upload_file("data/satellite.jpg")
    
    # Register in CID management
    await cid_manager.register_upload(
        file_path="data/satellite.jpg",
        content_cid=metadata.content_cid,
        shard_cids=metadata.shard_cids,
        file_size=metadata.file_size,
        tags={"source": "satellite", "processed": "false"}
    )
    
    # Later: check if file is still available
    availability = await cid_manager.check_cid_availability(metadata.content_cid)
    if availability.is_available:
        print("File is accessible on IPFS network")
```
""")
    
    return True


async def main():
    """Run all CID management tests."""
    logger.info("Starting CID Management System tests...")
    
    tests = [
        ("CID Validation", test_cid_validation),
        ("CID Registry", test_cid_registry),
        ("Network Checker", test_network_checker),
        ("CID Manager Integration", test_cid_manager_integration),
        ("Utility Functions", test_utility_functions),
        ("Usage Examples", demo_usage_examples),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'='*60}")
        logger.info(f"Running test: {test_name}")
        logger.info(f"{'='*60}")
        
        try:
            result = await test_func()
            results.append((test_name, result))
            status = "PASSED" if result else "FAILED"
            logger.info(f"Test {test_name}: {status}")
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("CID MANAGEMENT SYSTEM TEST SUMMARY")
    logger.info(f"{'='*60}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All CID management tests passed! The system is working correctly.")
    else:
        logger.warning("⚠️  Some tests failed. Check the logs above for details.")


if __name__ == "__main__":
    asyncio.run(main()) 