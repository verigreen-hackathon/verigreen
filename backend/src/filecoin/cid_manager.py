"""
CID (Content Identifier) Management System for Filecoin/IPFS.

This module provides comprehensive functionality for managing Content Identifiers,
including validation, formatting, registry management, and network availability checking.
"""

import json
import re
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import sqlite3

import aiohttp
import aiofiles
from multihash import decode as multihash_decode, encode as multihash_encode, SHA2_256

from .client import StorachaClient, StorachaConfig, StorachaError

logger = logging.getLogger(__name__)


@dataclass
class CIDInfo:
    """Information about a Content Identifier."""
    cid: str
    version: int  # 0 or 1
    multicodec: str
    multihash_algorithm: str
    multihash_digest: str
    base_encoding: str
    size: Optional[int] = None
    is_valid: bool = True
    validation_error: Optional[str] = None


@dataclass
class CIDRegistryEntry:
    """Entry in the CID registry mapping local files to network CIDs."""
    local_file_path: str
    content_cid: str
    shard_cids: List[str]
    file_size: int
    upload_timestamp: datetime
    last_verified: Optional[datetime] = None
    availability_status: str = "unknown"  # "available", "unavailable", "unknown"
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[Dict[str, str]] = None


@dataclass
class CIDAvailabilityResult:
    """Result of checking CID availability on the network."""
    cid: str
    is_available: bool
    last_checked: datetime
    response_time_ms: Optional[float] = None
    gateway_url: Optional[str] = None
    error_message: Optional[str] = None


class CIDValidationError(Exception):
    """Exception raised when CID validation fails."""
    pass


class CIDRegistryError(Exception):
    """Exception raised when CID registry operations fail."""
    pass


class CIDValidator:
    """Utility class for validating and parsing CIDs."""
    
    # CID format patterns
    CIDV0_PATTERN = re.compile(r'^Qm[1-9A-HJ-NP-Za-km-z]{44}$')
    CIDV1_PATTERN = re.compile(r'^[a-z2-7]{59}$')  # Base32 CIDv1
    
    # Base encodings
    BASE_ENCODINGS = {
        'base32': 'b',
        'base58btc': 'z', 
        'base64': 'm',
        'base64url': 'u',
        'base16': 'f',
    }
    
    @classmethod
    def is_valid_cid(cls, cid: str) -> bool:
        """
        Check if a string is a valid CID.
        
        Args:
            cid: String to validate
            
        Returns:
            True if valid CID, False otherwise
        """
        if not cid or not isinstance(cid, str):
            return False
        
        try:
            info = cls.parse_cid(cid)
            return info.is_valid
        except Exception:
            return False
    
    @classmethod
    def parse_cid(cls, cid: str) -> CIDInfo:
        """
        Parse a CID string and extract its components.
        
        Args:
            cid: CID string to parse
            
        Returns:
            CIDInfo object with parsed components
            
        Raises:
            CIDValidationError: If CID is invalid
        """
        if not cid or not isinstance(cid, str):
            raise CIDValidationError("CID must be a non-empty string")
        
        # Check for CIDv0 (Base58, starts with Qm)
        if cls.CIDV0_PATTERN.match(cid):
            return cls._parse_cidv0(cid)
        
        # Check for CIDv1 patterns
        if len(cid) > 10:  # Minimum reasonable length
            try:
                return cls._parse_cidv1(cid)
            except CIDValidationError:
                pass
        
        raise CIDValidationError(f"Invalid CID format: {cid}")
    
    @classmethod
    def _parse_cidv0(cls, cid: str) -> CIDInfo:
        """Parse a CIDv0 string."""
        try:
            # CIDv0 is just a base58-encoded SHA-256 multihash
            # For simplicity, we'll do basic validation
            if len(cid) != 46 or not cid.startswith('Qm'):
                raise CIDValidationError("Invalid CIDv0 format")
            
            return CIDInfo(
                cid=cid,
                version=0,
                multicodec="dag-pb",  # CIDv0 is always dag-pb
                multihash_algorithm="sha2-256",  # CIDv0 is always SHA-256
                multihash_digest=cid[2:],  # Simplified
                base_encoding="base58btc",
                is_valid=True
            )
        except Exception as e:
            raise CIDValidationError(f"Failed to parse CIDv0: {e}")
    
    @classmethod
    def _parse_cidv1(cls, cid: str) -> CIDInfo:
        """Parse a CIDv1 string."""
        try:
            # Basic CIDv1 validation
            # First character indicates base encoding
            base_char = cid[0]
            base_encoding = None
            
            for encoding, char in cls.BASE_ENCODINGS.items():
                if base_char == char:
                    base_encoding = encoding
                    break
            
            if not base_encoding:
                raise CIDValidationError(f"Unknown base encoding: {base_char}")
            
            # For base32 (most common CIDv1), do additional validation
            if base_encoding == "base32" and not cls.CIDV1_PATTERN.match(cid):
                raise CIDValidationError("Invalid base32 CIDv1 format")
            
            return CIDInfo(
                cid=cid,
                version=1,
                multicodec="unknown",  # Would need full CID parsing
                multihash_algorithm="unknown",  # Would need full CID parsing
                multihash_digest="unknown",  # Would need full CID parsing
                base_encoding=base_encoding,
                is_valid=True
            )
        except Exception as e:
            raise CIDValidationError(f"Failed to parse CIDv1: {e}")
    
    @classmethod
    def convert_cid_version(cls, cid: str, target_version: int) -> str:
        """
        Convert a CID between versions.
        
        Args:
            cid: Source CID
            target_version: Target version (0 or 1)
            
        Returns:
            Converted CID string
            
        Raises:
            CIDValidationError: If conversion fails
        """
        info = cls.parse_cid(cid)
        
        if info.version == target_version:
            return cid
        
        if target_version == 0:
            # Convert v1 to v0 (only possible for certain conditions)
            if info.multicodec == "dag-pb" and info.multihash_algorithm == "sha2-256":
                # This is a simplified conversion - real implementation would need proper CID library
                logger.warning("CID version conversion is simplified - use proper CID library for production")
                return cid  # Return as-is for now
            else:
                raise CIDValidationError("Cannot convert this CIDv1 to CIDv0")
        
        elif target_version == 1:
            # Convert v0 to v1
            # This is a simplified conversion - real implementation would need proper CID library
            logger.warning("CID version conversion is simplified - use proper CID library for production")
            return cid  # Return as-is for now
        
        else:
            raise CIDValidationError(f"Unsupported CID version: {target_version}")
    
    @classmethod
    def normalize_cid(cls, cid: str, preferred_version: int = 1, preferred_encoding: str = "base32") -> str:
        """
        Normalize a CID to a preferred version and encoding.
        
        Args:
            cid: Source CID
            preferred_version: Preferred CID version
            preferred_encoding: Preferred base encoding
            
        Returns:
            Normalized CID string
        """
        info = cls.parse_cid(cid)
        
        # If already in preferred format, return as-is
        if info.version == preferred_version and info.base_encoding == preferred_encoding:
            return cid
        
        # Convert version if needed
        if info.version != preferred_version:
            try:
                cid = cls.convert_cid_version(cid, preferred_version)
            except CIDValidationError:
                logger.debug(f"Cannot convert CID version, keeping original: {cid}")
        
        # Convert encoding if needed (simplified)
        # Real implementation would use proper CID library
        return cid


class CIDRegistry:
    """
    Registry for tracking CIDs and their associated local files.
    
    Provides mapping between local file paths and their IPFS CIDs,
    along with metadata and availability tracking.
    """
    
    def __init__(self, registry_path: Optional[str] = None):
        """
        Initialize the CID registry.
        
        Args:
            registry_path: Path to registry database file
        """
        self.registry_path = registry_path or "filecoin_cid_registry.db"
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize the SQLite database for the registry."""
        try:
            with sqlite3.connect(self.registry_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS cid_registry (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        local_file_path TEXT UNIQUE NOT NULL,
                        content_cid TEXT NOT NULL,
                        shard_cids TEXT NOT NULL,  -- JSON array
                        file_size INTEGER NOT NULL,
                        upload_timestamp TEXT NOT NULL,
                        last_verified TEXT,
                        availability_status TEXT DEFAULT 'unknown',
                        metadata TEXT,  -- JSON object
                        tags TEXT,  -- JSON object
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_content_cid ON cid_registry(content_cid)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_availability_status ON cid_registry(availability_status)
                """)
                
                conn.commit()
                logger.info(f"CID registry database initialized: {self.registry_path}")
                
        except Exception as e:
            raise CIDRegistryError(f"Failed to initialize registry database: {e}")
    
    async def register_cid(self, entry: CIDRegistryEntry) -> None:
        """
        Register a new CID in the registry.
        
        Args:
            entry: CID registry entry to add
            
        Raises:
            CIDRegistryError: If registration fails
        """
        try:
            # Validate CID
            if not CIDValidator.is_valid_cid(entry.content_cid):
                raise CIDRegistryError(f"Invalid content CID: {entry.content_cid}")
            
            # Validate shard CIDs
            for shard_cid in entry.shard_cids:
                if not CIDValidator.is_valid_cid(shard_cid):
                    raise CIDRegistryError(f"Invalid shard CID: {shard_cid}")
            
            with sqlite3.connect(self.registry_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO cid_registry (
                        local_file_path, content_cid, shard_cids, file_size,
                        upload_timestamp, last_verified, availability_status,
                        metadata, tags, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entry.local_file_path,
                    entry.content_cid,
                    json.dumps(entry.shard_cids),
                    entry.file_size,
                    entry.upload_timestamp.isoformat(),
                    entry.last_verified.isoformat() if entry.last_verified else None,
                    entry.availability_status,
                    json.dumps(entry.metadata) if entry.metadata else None,
                    json.dumps(entry.tags) if entry.tags else None,
                    datetime.utcnow().isoformat()
                ))
                
                conn.commit()
                logger.info(f"Registered CID {entry.content_cid} for file {entry.local_file_path}")
                
        except Exception as e:
            raise CIDRegistryError(f"Failed to register CID: {e}")
    
    async def get_cid_by_file_path(self, file_path: str) -> Optional[CIDRegistryEntry]:
        """
        Get CID registry entry by local file path.
        
        Args:
            file_path: Local file path
            
        Returns:
            CID registry entry if found, None otherwise
        """
        try:
            with sqlite3.connect(self.registry_path) as conn:
                cursor = conn.execute("""
                    SELECT local_file_path, content_cid, shard_cids, file_size,
                           upload_timestamp, last_verified, availability_status,
                           metadata, tags
                    FROM cid_registry 
                    WHERE local_file_path = ?
                """, (file_path,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                return self._row_to_entry(row)
                
        except Exception as e:
            logger.error(f"Failed to get CID by file path {file_path}: {e}")
            return None
    
    async def get_entry_by_cid(self, cid: str) -> Optional[CIDRegistryEntry]:
        """
        Get CID registry entry by content CID.
        
        Args:
            cid: Content CID
            
        Returns:
            CID registry entry if found, None otherwise
        """
        try:
            with sqlite3.connect(self.registry_path) as conn:
                cursor = conn.execute("""
                    SELECT local_file_path, content_cid, shard_cids, file_size,
                           upload_timestamp, last_verified, availability_status,
                           metadata, tags
                    FROM cid_registry 
                    WHERE content_cid = ?
                """, (cid,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                return self._row_to_entry(row)
                
        except Exception as e:
            logger.error(f"Failed to get entry by CID {cid}: {e}")
            return None
    
    async def list_all_entries(self, status_filter: Optional[str] = None) -> List[CIDRegistryEntry]:
        """
        List all CID registry entries.
        
        Args:
            status_filter: Optional availability status filter
            
        Returns:
            List of CID registry entries
        """
        try:
            with sqlite3.connect(self.registry_path) as conn:
                if status_filter:
                    cursor = conn.execute("""
                        SELECT local_file_path, content_cid, shard_cids, file_size,
                               upload_timestamp, last_verified, availability_status,
                               metadata, tags
                        FROM cid_registry 
                        WHERE availability_status = ?
                        ORDER BY upload_timestamp DESC
                    """, (status_filter,))
                else:
                    cursor = conn.execute("""
                        SELECT local_file_path, content_cid, shard_cids, file_size,
                               upload_timestamp, last_verified, availability_status,
                               metadata, tags
                        FROM cid_registry 
                        ORDER BY upload_timestamp DESC
                    """)
                
                return [self._row_to_entry(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to list registry entries: {e}")
            return []
    
    async def update_availability_status(self, cid: str, status: str, last_verified: Optional[datetime] = None) -> None:
        """
        Update the availability status of a CID.
        
        Args:
            cid: Content CID
            status: New availability status
            last_verified: Optional verification timestamp
        """
        try:
            with sqlite3.connect(self.registry_path) as conn:
                conn.execute("""
                    UPDATE cid_registry 
                    SET availability_status = ?, last_verified = ?, updated_at = ?
                    WHERE content_cid = ?
                """, (
                    status,
                    last_verified.isoformat() if last_verified else None,
                    datetime.utcnow().isoformat(),
                    cid
                ))
                
                conn.commit()
                logger.debug(f"Updated availability status for CID {cid}: {status}")
                
        except Exception as e:
            logger.error(f"Failed to update availability status for CID {cid}: {e}")
    
    async def remove_entry(self, cid: str) -> bool:
        """
        Remove a CID registry entry.
        
        Args:
            cid: Content CID to remove
            
        Returns:
            True if entry was removed, False if not found
        """
        try:
            with sqlite3.connect(self.registry_path) as conn:
                cursor = conn.execute("""
                    DELETE FROM cid_registry WHERE content_cid = ?
                """, (cid,))
                
                conn.commit()
                removed = cursor.rowcount > 0
                
                if removed:
                    logger.info(f"Removed CID registry entry: {cid}")
                else:
                    logger.debug(f"CID registry entry not found: {cid}")
                
                return removed
                
        except Exception as e:
            logger.error(f"Failed to remove CID registry entry {cid}: {e}")
            return False
    
    def _row_to_entry(self, row: Tuple) -> CIDRegistryEntry:
        """Convert database row to CIDRegistryEntry."""
        return CIDRegistryEntry(
            local_file_path=row[0],
            content_cid=row[1],
            shard_cids=json.loads(row[2]),
            file_size=row[3],
            upload_timestamp=datetime.fromisoformat(row[4]),
            last_verified=datetime.fromisoformat(row[5]) if row[5] else None,
            availability_status=row[6],
            metadata=json.loads(row[7]) if row[7] else None,
            tags=json.loads(row[8]) if row[8] else None
        )


class CIDNetworkChecker:
    """
    Utility for checking CID availability on IPFS/Filecoin networks.
    
    Provides methods to verify that CIDs are accessible through various gateways
    and retrieve file metadata from the network.
    """
    
    # Default IPFS gateways to check
    DEFAULT_GATEWAYS = [
        "https://ipfs.io/ipfs/{cid}",
        "https://gateway.pinata.cloud/ipfs/{cid}",
        "https://cloudflare-ipfs.com/ipfs/{cid}",
        "https://dweb.link/ipfs/{cid}",
    ]
    
    def __init__(self, custom_gateways: Optional[List[str]] = None, timeout: int = 30):
        """
        Initialize the network checker.
        
        Args:
            custom_gateways: Optional list of custom gateway URLs
            timeout: Request timeout in seconds
        """
        self.gateways = custom_gateways or self.DEFAULT_GATEWAYS
        self.timeout = timeout
    
    async def check_cid_availability(self, cid: str) -> CIDAvailabilityResult:
        """
        Check if a CID is available on the IPFS network.
        
        Args:
            cid: Content CID to check
            
        Returns:
            CID availability result
        """
        # Validate CID first
        if not CIDValidator.is_valid_cid(cid):
            return CIDAvailabilityResult(
                cid=cid,
                is_available=False,
                last_checked=datetime.utcnow(),
                error_message="Invalid CID format"
            )
        
        # Try each gateway
        for gateway_template in self.gateways:
            try:
                result = await self._check_gateway(cid, gateway_template)
                if result.is_available:
                    return result
            except Exception as e:
                logger.debug(f"Gateway check failed for {gateway_template}: {e}")
                continue
        
        # All gateways failed
        return CIDAvailabilityResult(
            cid=cid,
            is_available=False,
            last_checked=datetime.utcnow(),
            error_message="Not available on any checked gateway"
        )
    
    async def _check_gateway(self, cid: str, gateway_template: str) -> CIDAvailabilityResult:
        """Check a single gateway for CID availability."""
        gateway_url = gateway_template.format(cid=cid)
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.head(gateway_url) as response:
                    end_time = asyncio.get_event_loop().time()
                    response_time_ms = (end_time - start_time) * 1000
                    
                    is_available = response.status == 200
                    
                    return CIDAvailabilityResult(
                        cid=cid,
                        is_available=is_available,
                        last_checked=datetime.utcnow(),
                        response_time_ms=response_time_ms,
                        gateway_url=gateway_url,
                        error_message=None if is_available else f"HTTP {response.status}"
                    )
                    
        except Exception as e:
            end_time = asyncio.get_event_loop().time()
            response_time_ms = (end_time - start_time) * 1000
            
            return CIDAvailabilityResult(
                cid=cid,
                is_available=False,
                last_checked=datetime.utcnow(),
                response_time_ms=response_time_ms,
                gateway_url=gateway_url,
                error_message=str(e)
            )
    
    async def get_file_metadata_from_cid(self, cid: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve file metadata from a CID on the network.
        
        Args:
            cid: Content CID
            
        Returns:
            File metadata dictionary if available, None otherwise
        """
        # Check availability first
        availability = await self.check_cid_availability(cid)
        
        if not availability.is_available:
            logger.debug(f"CID {cid} not available for metadata retrieval")
            return None
        
        # Try to get basic file info from gateway
        try:
            gateway_url = availability.gateway_url
            if not gateway_url:
                gateway_url = self.gateways[0].format(cid=cid)
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.head(gateway_url) as response:
                    if response.status == 200:
                        metadata = {
                            "cid": cid,
                            "content_type": response.headers.get("Content-Type"),
                            "content_length": response.headers.get("Content-Length"),
                            "last_modified": response.headers.get("Last-Modified"),
                            "etag": response.headers.get("ETag"),
                            "gateway_url": gateway_url,
                            "retrieved_at": datetime.utcnow().isoformat()
                        }
                        
                        # Convert content length to int if present
                        if metadata["content_length"]:
                            try:
                                metadata["content_length"] = int(metadata["content_length"])
                            except ValueError:
                                pass
                        
                        return metadata
                        
        except Exception as e:
            logger.error(f"Failed to retrieve metadata for CID {cid}: {e}")
        
        return None


class CIDManager:
    """
    Comprehensive CID management system.
    
    Combines CID validation, registry management, and network checking
    into a unified interface for managing Content Identifiers.
    """
    
    def __init__(
        self, 
        registry_path: Optional[str] = None,
        storacha_config: Optional[StorachaConfig] = None,
        custom_gateways: Optional[List[str]] = None
    ):
        """
        Initialize the CID manager.
        
        Args:
            registry_path: Path to CID registry database
            storacha_config: Optional Storacha configuration
            custom_gateways: Optional custom IPFS gateways
        """
        self.validator = CIDValidator()
        self.registry = CIDRegistry(registry_path)
        self.network_checker = CIDNetworkChecker(custom_gateways)
        self.storacha_config = storacha_config
        self._client: Optional[StorachaClient] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        if self.storacha_config:
            self._client = StorachaClient(self.storacha_config)
            await self._client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.__aexit__(exc_type, exc_val, exc_tb)
    
    # CID Validation Methods
    
    def validate_cid(self, cid: str) -> CIDInfo:
        """
        Validate and parse a CID.
        
        Args:
            cid: CID string to validate
            
        Returns:
            CIDInfo object with validation results
        """
        return self.validator.parse_cid(cid)
    
    def is_valid_cid(self, cid: str) -> bool:
        """
        Check if a string is a valid CID.
        
        Args:
            cid: String to check
            
        Returns:
            True if valid CID, False otherwise
        """
        return self.validator.is_valid_cid(cid)
    
    def normalize_cid(self, cid: str, preferred_version: int = 1) -> str:
        """
        Normalize a CID to preferred format.
        
        Args:
            cid: Source CID
            preferred_version: Preferred CID version
            
        Returns:
            Normalized CID string
        """
        return self.validator.normalize_cid(cid, preferred_version)
    
    # Registry Management Methods
    
    async def register_upload(
        self, 
        file_path: str, 
        content_cid: str, 
        shard_cids: List[str],
        file_size: int,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Register a completed upload in the CID registry.
        
        Args:
            file_path: Local file path
            content_cid: Content CID from upload
            shard_cids: List of shard CIDs
            file_size: Size of uploaded file
            metadata: Optional metadata
            tags: Optional tags
        """
        entry = CIDRegistryEntry(
            local_file_path=file_path,
            content_cid=content_cid,
            shard_cids=shard_cids,
            file_size=file_size,
            upload_timestamp=datetime.utcnow(),
            metadata=metadata,
            tags=tags
        )
        
        await self.registry.register_cid(entry)
    
    async def get_cid_for_file(self, file_path: str) -> Optional[str]:
        """
        Get the content CID for a local file.
        
        Args:
            file_path: Local file path
            
        Returns:
            Content CID if found, None otherwise
        """
        entry = await self.registry.get_cid_by_file_path(file_path)
        return entry.content_cid if entry else None
    
    async def get_file_for_cid(self, cid: str) -> Optional[str]:
        """
        Get the local file path for a content CID.
        
        Args:
            cid: Content CID
            
        Returns:
            Local file path if found, None otherwise
        """
        entry = await self.registry.get_entry_by_cid(cid)
        return entry.local_file_path if entry else None
    
    async def list_managed_cids(self, status_filter: Optional[str] = None) -> List[CIDRegistryEntry]:
        """
        List all managed CIDs.
        
        Args:
            status_filter: Optional availability status filter
            
        Returns:
            List of CID registry entries
        """
        return await self.registry.list_all_entries(status_filter)
    
    # Network Status Methods
    
    async def check_cid_availability(self, cid: str, update_registry: bool = True) -> CIDAvailabilityResult:
        """
        Check if a CID is available on the IPFS network.
        
        Args:
            cid: Content CID to check
            update_registry: Whether to update registry with results
            
        Returns:
            CID availability result
        """
        result = await self.network_checker.check_cid_availability(cid)
        
        if update_registry:
            status = "available" if result.is_available else "unavailable"
            await self.registry.update_availability_status(cid, status, result.last_checked)
        
        return result
    
    async def verify_all_managed_cids(self) -> Dict[str, CIDAvailabilityResult]:
        """
        Verify availability of all managed CIDs.
        
        Returns:
            Dictionary mapping CIDs to availability results
        """
        entries = await self.registry.list_all_entries()
        results = {}
        
        for entry in entries:
            try:
                result = await self.check_cid_availability(entry.content_cid, update_registry=True)
                results[entry.content_cid] = result
                
                # Small delay to avoid overwhelming gateways
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Failed to verify CID {entry.content_cid}: {e}")
                results[entry.content_cid] = CIDAvailabilityResult(
                    cid=entry.content_cid,
                    is_available=False,
                    last_checked=datetime.utcnow(),
                    error_message=str(e)
                )
        
        return results
    
    async def get_file_metadata(self, cid: str) -> Optional[Dict[str, Any]]:
        """
        Get file metadata for a CID from the network.
        
        Args:
            cid: Content CID
            
        Returns:
            File metadata if available, None otherwise
        """
        return await self.network_checker.get_file_metadata_from_cid(cid)
    
    # Storacha Integration Methods
    
    async def get_storacha_file_info(self, cid: str) -> Optional[Dict[str, Any]]:
        """
        Get file information from Storacha for a CID.
        
        Args:
            cid: Content CID
            
        Returns:
            Storacha file info if available, None otherwise
        """
        if not self._client:
            logger.warning("Storacha client not available")
            return None
        
        try:
            uploads = await self._client.list_uploads()
            
            for upload in uploads:
                if upload.get("root") == cid:
                    return upload
            
            return None
            
        except StorachaError as e:
            logger.error(f"Failed to get Storacha file info for CID {cid}: {e}")
            return None
    
    # Utility Methods
    
    async def cleanup_unavailable_cids(self, days_threshold: int = 7) -> int:
        """
        Remove CIDs that have been unavailable for too long.
        
        Args:
            days_threshold: Number of days after which to remove unavailable CIDs
            
        Returns:
            Number of CIDs removed
        """
        threshold_date = datetime.utcnow() - timedelta(days=days_threshold)
        entries = await self.registry.list_all_entries("unavailable")
        
        removed_count = 0
        for entry in entries:
            if entry.last_verified and entry.last_verified < threshold_date:
                success = await self.registry.remove_entry(entry.content_cid)
                if success:
                    removed_count += 1
                    logger.info(f"Removed unavailable CID: {entry.content_cid}")
        
        return removed_count
    
    async def export_registry(self, export_path: str) -> None:
        """
        Export the CID registry to a JSON file.
        
        Args:
            export_path: Path to export file
        """
        entries = await self.registry.list_all_entries()
        
        export_data = {
            "export_timestamp": datetime.utcnow().isoformat(),
            "entry_count": len(entries),
            "entries": [asdict(entry) for entry in entries]
        }
        
        # Convert datetime objects to strings
        for entry_dict in export_data["entries"]:
            if entry_dict["upload_timestamp"]:
                entry_dict["upload_timestamp"] = entry_dict["upload_timestamp"].isoformat()
            if entry_dict["last_verified"]:
                entry_dict["last_verified"] = entry_dict["last_verified"].isoformat()
        
        async with aiofiles.open(export_path, 'w') as f:
            await f.write(json.dumps(export_data, indent=2))
        
        logger.info(f"Exported {len(entries)} CID registry entries to {export_path}")


# Utility functions for convenient access

async def validate_cid(cid: str) -> CIDInfo:
    """Validate a CID and return parsed information."""
    return CIDValidator.parse_cid(cid)


async def check_cid_available(cid: str, custom_gateways: Optional[List[str]] = None) -> bool:
    """Check if a CID is available on IPFS network."""
    checker = CIDNetworkChecker(custom_gateways)
    result = await checker.check_cid_availability(cid)
    return result.is_available


async def normalize_cid_format(cid: str, preferred_version: int = 1) -> str:
    """Normalize a CID to preferred format."""
    return CIDValidator.normalize_cid(cid, preferred_version) 