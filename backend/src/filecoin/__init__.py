"""
Filecoin storage integration package.

This package provides functionality for uploading and managing files
on Filecoin storage via Storacha's HTTP API Bridge.
"""

# Core client classes
from .client import (
    StorachaClient,
    StorachaConfig,
    StorachaError,
    StorachaAuthError,
    StorachaUploadError,
    UploadResult,
    create_config_from_env,
    test_connection
)

# Service layer classes
from .service import (
    FilecoinService,
    FileMetadata,
    UploadProgress,
    FilecoinUploadError,
    FilecoinValidationError,
    upload_single_file,
    create_progress_logger
)

# CID management classes
from .cid_manager import (
    CIDManager,
    CIDValidator,
    CIDRegistry,
    CIDNetworkChecker,
    CIDInfo,
    CIDRegistryEntry,
    CIDAvailabilityResult,
    CIDValidationError,
    CIDRegistryError,
    validate_cid,
    check_cid_available,
    normalize_cid_format
)

__version__ = "0.1.0"

__all__ = [
    # Client classes
    "StorachaClient",
    "StorachaConfig", 
    "StorachaError",
    "StorachaAuthError",
    "StorachaUploadError",
    "UploadResult",
    "create_config_from_env",
    "test_connection",
    
    # Service classes
    "FilecoinService",
    "FileMetadata",
    "UploadProgress", 
    "FilecoinUploadError",
    "FilecoinValidationError",
    "upload_single_file",
    "create_progress_logger",
    
    # CID management classes
    "CIDManager",
    "CIDValidator",
    "CIDRegistry", 
    "CIDNetworkChecker",
    "CIDInfo",
    "CIDRegistryEntry",
    "CIDAvailabilityResult",
    "CIDValidationError",
    "CIDRegistryError",
    "validate_cid",
    "check_cid_available",
    "normalize_cid_format",
] 