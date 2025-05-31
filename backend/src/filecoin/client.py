"""
Storacha (w3up) client for IPFS storage operations.

This module provides a Python client for interacting with Storacha's HTTP API Bridge,
enabling storage and retrieval of data on IPFS through Storacha's services.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from io import BytesIO

import aiohttp
import aiofiles
from multihash import decode as multihash_decode, encode as multihash_encode, SHA2_256

logger = logging.getLogger(__name__)


@dataclass
class StorachaConfig:
    """Configuration for Storacha client."""
    base_url: str = "https://up.storacha.network"
    auth_secret: Optional[str] = None
    auth_token: Optional[str] = None
    space_did: Optional[str] = None
    timeout: int = 30


@dataclass
class UploadResult:
    """Result of a successful upload to Storacha."""
    content_cid: str
    shard_cids: List[str]
    size: int


class StorachaError(Exception):
    """Base exception for Storacha client errors."""
    pass


class StorachaAuthError(StorachaError):
    """Authentication-related errors."""
    pass


class StorachaUploadError(StorachaError):
    """Upload-related errors."""
    pass


class StorachaClient:
    """
    Async client for Storacha/w3up HTTP API Bridge.
    
    Provides methods for storing and uploading data to IPFS via Storacha.
    Uses the HTTP API Bridge documented at:
    https://docs.storacha.network/reference/http-api/
    """
    
    def __init__(self, config: StorachaConfig):
        """
        Initialize the Storacha client.
        
        Args:
            config: StorachaConfig object with authentication and settings
        """
        self.config = config
        self._session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def _ensure_session(self):
        """Ensure aiohttp session is created."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
    
    async def close(self):
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get HTTP headers for Storacha API requests.
        
        Returns:
            Dict containing required headers including authentication
            
        Raises:
            StorachaAuthError: If authentication credentials are missing
        """
        if not self.config.auth_secret or not self.config.auth_token:
            raise StorachaAuthError(
                "Missing authentication credentials. Both auth_secret and auth_token are required."
            )
        
        return {
            "Content-Type": "application/json",
            "X-Auth-Secret": self.config.auth_secret,
            "Authorization": self.config.auth_token,
        }
    
    async def _make_request(
        self, 
        endpoint: str, 
        tasks: List[List[Any]], 
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make a request to the Storacha HTTP API Bridge.
        
        Args:
            endpoint: API endpoint path
            tasks: List of task arrays in format [capability, space_did, params]
            **kwargs: Additional arguments for aiohttp request
            
        Returns:
            JSON response from the API
            
        Raises:
            StorachaError: If the request fails
        """
        await self._ensure_session()
        
        url = f"{self.config.base_url}/{endpoint.lstrip('/')}"
        headers = self._get_headers()
        
        payload = {"tasks": tasks}
        
        logger.debug(f"Making request to {url} with {len(tasks)} tasks")
        
        try:
            async with self._session.post(url, json=payload, headers=headers, **kwargs) as response:
                response_text = await response.text()
                
                if not response.ok:
                    logger.error(f"Request failed: {response.status} - {response_text}")
                    raise StorachaError(f"HTTP {response.status}: {response_text}")
                
                try:
                    return json.loads(response_text)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode JSON response: {e}")
                    raise StorachaError(f"Invalid JSON response: {e}")
                    
        except aiohttp.ClientError as e:
            logger.error(f"Network error: {e}")
            raise StorachaError(f"Network error: {e}")
    
    def _create_simple_car(self, data: bytes) -> Tuple[bytes, str]:
        """
        Create a simple CAR file from raw data.
        
        This is a basic implementation that creates a minimal CAR file
        containing a single raw block.
        
        Args:
            data: Raw bytes to include in the CAR
            
        Returns:
            Tuple of (car_bytes, content_cid)
        """
        # For now, we'll create a very simple CAR structure
        # In a production environment, you'd want to use a proper CAR library
        
        # Calculate CID for the raw data
        hash_digest = multihash_encode(data, SHA2_256)
        
        # Create a simple CIDv1 for raw codec (0x55)
        # Format: version(1) + codec(raw=0x55) + multihash
        cid_bytes = bytes([0x01, 0x55]) + hash_digest
        content_cid = self._bytes_to_cid_string(cid_bytes)
        
        # Create minimal CAR structure
        # This is a simplified implementation - production would use proper CAR encoding
        car_header = self._create_car_header([content_cid])
        car_block = self._create_car_block(cid_bytes, data)
        
        car_data = car_header + car_block
        
        logger.debug(f"Created CAR file: {len(car_data)} bytes, CID: {content_cid}")
        return car_data, content_cid
    
    def _bytes_to_cid_string(self, cid_bytes: bytes) -> str:
        """
        Convert CID bytes to base32-encoded string.
        
        Args:
            cid_bytes: Raw CID bytes
            
        Returns:
            Base32-encoded CID string with 'b' prefix
        """
        import base64
        # For CIDv1, we use base32 encoding with 'b' prefix
        # This is a simplified version - production should use proper CID library
        encoded = base64.b32encode(cid_bytes).decode('ascii').lower().rstrip('=')
        return f"b{encoded}"
    
    def _create_car_header(self, roots: List[str]) -> bytes:
        """
        Create CAR header bytes.
        
        Args:
            roots: List of root CID strings
            
        Returns:
            Encoded CAR header bytes
        """
        # Simplified CAR header creation
        # Production implementation would use proper CAR encoding
        header_data = {"version": 1, "roots": roots}
        header_json = json.dumps(header_data).encode('utf-8')
        
        # Length-prefix the header (varint encoding)
        header_length = len(header_json)
        length_bytes = self._encode_varint(header_length)
        
        return length_bytes + header_json
    
    def _create_car_block(self, cid_bytes: bytes, data: bytes) -> bytes:
        """
        Create CAR block bytes.
        
        Args:
            cid_bytes: CID bytes for the block
            data: Block data
            
        Returns:
            Encoded CAR block bytes
        """
        # Block format: length(varint) + cid_length(varint) + cid + data
        cid_length = len(cid_bytes)
        block_length = len(self._encode_varint(cid_length)) + cid_length + len(data)
        
        length_bytes = self._encode_varint(block_length)
        cid_length_bytes = self._encode_varint(cid_length)
        
        return length_bytes + cid_length_bytes + cid_bytes + data
    
    def _encode_varint(self, value: int) -> bytes:
        """
        Encode integer as varint bytes.
        
        Args:
            value: Integer to encode
            
        Returns:
            Varint-encoded bytes
        """
        result = []
        while value >= 0x80:
            result.append((value & 0x7F) | 0x80)
            value >>= 7
        result.append(value & 0x7F)
        return bytes(result)
    
    async def store_add(self, data: bytes) -> str:
        """
        Store data and get a shard CID.
        
        This corresponds to the 'store/add' capability in Storacha.
        
        Args:
            data: Raw bytes to store
            
        Returns:
            Shard CID string
            
        Raises:
            StorachaError: If the store operation fails
        """
        if not self.config.space_did:
            raise StorachaAuthError("space_did is required for store operations")
        
        # Create CAR file from data
        car_data, content_cid = self._create_simple_car(data)
        
        # Prepare the store/add task
        tasks = [
            [
                "store/add",
                self.config.space_did,
                {
                    "car": car_data.hex(),  # Send as hex string
                    "size": len(car_data)
                }
            ]
        ]
        
        try:
            response = await self._make_request("bridge", tasks)
            
            # Extract shard CID from response
            if "results" in response and len(response["results"]) > 0:
                result = response["results"][0]
                if "ok" in result:
                    shard_cid = result["ok"].get("shard")
                    if shard_cid:
                        logger.info(f"Successfully stored data, shard CID: {shard_cid}")
                        return shard_cid
                
                # Handle error in result
                if "error" in result:
                    error_msg = result["error"]
                    raise StorachaUploadError(f"Store failed: {error_msg}")
            
            raise StorachaUploadError("Unexpected response format")
            
        except Exception as e:
            logger.error(f"Store operation failed: {e}")
            raise StorachaUploadError(f"Store operation failed: {e}")
    
    async def upload_add(self, content_cid: str, shard_cids: List[str]) -> bool:
        """
        Register an upload with content CID and associated shard CIDs.
        
        This corresponds to the 'upload/add' capability in Storacha.
        
        Args:
            content_cid: The content CID to register
            shard_cids: List of shard CIDs that contain the content
            
        Returns:
            True if successful
            
        Raises:
            StorachaError: If the upload registration fails
        """
        if not self.config.space_did:
            raise StorachaAuthError("space_did is required for upload operations")
        
        # Prepare the upload/add task
        tasks = [
            [
                "upload/add",
                self.config.space_did,
                {
                    "root": content_cid,
                    "shards": shard_cids
                }
            ]
        ]
        
        try:
            response = await self._make_request("bridge", tasks)
            
            # Check response
            if "results" in response and len(response["results"]) > 0:
                result = response["results"][0]
                if "ok" in result:
                    logger.info(f"Successfully registered upload: {content_cid}")
                    return True
                
                if "error" in result:
                    error_msg = result["error"]
                    raise StorachaUploadError(f"Upload registration failed: {error_msg}")
            
            raise StorachaUploadError("Unexpected response format")
            
        except Exception as e:
            logger.error(f"Upload registration failed: {e}")
            raise StorachaUploadError(f"Upload registration failed: {e}")
    
    async def upload_file(self, file_path: str) -> UploadResult:
        """
        Upload a file to Storacha.
        
        This is a convenience method that combines store/add and upload/add.
        
        Args:
            file_path: Path to the file to upload
            
        Returns:
            UploadResult with content CID, shard CIDs, and size
            
        Raises:
            StorachaError: If the upload fails
        """
        try:
            # Read file data
            async with aiofiles.open(file_path, 'rb') as f:
                data = await f.read()
            
            return await self.upload_data(data)
            
        except IOError as e:
            raise StorachaUploadError(f"Failed to read file {file_path}: {e}")
    
    async def upload_data(self, data: bytes) -> UploadResult:
        """
        Upload raw data to Storacha.
        
        This is a convenience method that combines store/add and upload/add.
        
        Args:
            data: Raw bytes to upload
            
        Returns:
            UploadResult with content CID, shard CIDs, and size
            
        Raises:
            StorachaError: If the upload fails
        """
        # Step 1: Store the data and get shard CID
        shard_cid = await self.store_add(data)
        
        # Step 2: Create content CID (for simplicity, using the same as shard for raw data)
        _, content_cid = self._create_simple_car(data)
        
        # Step 3: Register the upload
        await self.upload_add(content_cid, [shard_cid])
        
        return UploadResult(
            content_cid=content_cid,
            shard_cids=[shard_cid],
            size=len(data)
        )
    
    async def list_uploads(self) -> List[Dict[str, Any]]:
        """
        List uploads in the space.
        
        This corresponds to the 'upload/list' capability in Storacha.
        
        Returns:
            List of upload records
            
        Raises:
            StorachaError: If the list operation fails
        """
        if not self.config.space_did:
            raise StorachaAuthError("space_did is required for upload operations")
        
        tasks = [
            [
                "upload/list",
                self.config.space_did,
                {}
            ]
        ]
        
        try:
            response = await self._make_request("bridge", tasks)
            
            if "results" in response and len(response["results"]) > 0:
                result = response["results"][0]
                if "ok" in result:
                    uploads = result["ok"].get("uploads", [])
                    logger.info(f"Retrieved {len(uploads)} uploads")
                    return uploads
                
                if "error" in result:
                    error_msg = result["error"]
                    raise StorachaError(f"List uploads failed: {error_msg}")
            
            raise StorachaError("Unexpected response format")
            
        except Exception as e:
            logger.error(f"List uploads failed: {e}")
            raise StorachaError(f"List uploads failed: {e}")


# Utility functions for configuration management

def create_config_from_env() -> StorachaConfig:
    """
    Create StorachaConfig from environment variables.
    
    Expected environment variables:
    - STORACHA_AUTH_SECRET: X-Auth-Secret header value
    - STORACHA_AUTH_TOKEN: Authorization header value  
    - STORACHA_SPACE_DID: Space DID for operations
    - STORACHA_BASE_URL: Base URL (optional, defaults to production)
    
    Returns:
        StorachaConfig object
        
    Raises:
        StorachaAuthError: If required environment variables are missing
    """
    import os
    
    auth_secret = os.getenv("STORACHA_AUTH_SECRET")
    auth_token = os.getenv("STORACHA_AUTH_TOKEN") 
    space_did = os.getenv("STORACHA_SPACE_DID")
    base_url = os.getenv("STORACHA_BASE_URL", "https://up.storacha.network")
    
    if not auth_secret or not auth_token:
        raise StorachaAuthError(
            "Missing required environment variables: STORACHA_AUTH_SECRET and STORACHA_AUTH_TOKEN"
        )
    
    return StorachaConfig(
        base_url=base_url,
        auth_secret=auth_secret,
        auth_token=auth_token,
        space_did=space_did
    )


async def test_connection(config: StorachaConfig) -> bool:
    """
    Test connection to Storacha API.
    
    Args:
        config: StorachaConfig object
        
    Returns:
        True if connection is successful
        
    Raises:
        StorachaError: If connection fails
    """
    async with StorachaClient(config) as client:
        try:
            # Try to list uploads as a connection test
            await client.list_uploads()
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            raise StorachaError(f"Connection test failed: {e}") 