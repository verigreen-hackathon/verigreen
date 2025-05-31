"""
Storacha (w3up) client for IPFS storage operations.

This module provides a Python client for interacting with Storacha's HTTP API Bridge,
enabling storage and retrieval of data on IPFS through Storacha's services.
"""

import asyncio
import json
import logging
import os
import subprocess
import tempfile
import hashlib
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import aiohttp
import aiofiles
import certifi
import ssl
from multihash import decode as multihash_decode, encode as multihash_encode, constants

logger = logging.getLogger(__name__)


@dataclass
class StorachaConfig:
    """Configuration for Storacha client."""
    auth_secret: str
    auth_token: str
    space_did: str
    base_url: str = "https://up.storacha.network"
    timeout: int = 300  # 5 minutes


@dataclass
class UploadResult:
    """Result of a successful upload operation."""
    content_cid: str  # The CID of the original content (root)
    shard_cid: str    # The CID of the CAR file (shard)
    size: int         # Size of the original data


class StorachaError(Exception):
    """Base exception for Storacha operations."""
    pass


class StorachaAuthError(StorachaError):
    """Authentication/authorization related errors."""
    pass


class StorachaUploadError(StorachaError):
    """Upload operation related errors."""
    pass


def create_config_from_env() -> StorachaConfig:
    """
    Create StorachaConfig from environment variables.
    
    Returns:
        StorachaConfig instance
        
    Raises:
        StorachaAuthError: If required environment variables are missing
    """
    auth_secret = os.getenv("STORACHA_AUTH_SECRET")
    auth_token = os.getenv("STORACHA_AUTH_TOKEN")
    space_did = os.getenv("STORACHA_SPACE_DID")
    base_url = os.getenv("STORACHA_BASE_URL", "https://up.storacha.network")
    
    if not all([auth_secret, auth_token, space_did]):
        missing = []
        if not auth_secret:
            missing.append("STORACHA_AUTH_SECRET")
        if not auth_token:
            missing.append("STORACHA_AUTH_TOKEN")
        if not space_did:
            missing.append("STORACHA_SPACE_DID")
        
        raise StorachaAuthError(
            f"Missing required environment variables: {', '.join(missing)}"
        )
    
    return StorachaConfig(
        auth_secret=auth_secret,
        auth_token=auth_token,
        space_did=space_did,
        base_url=base_url
    )


class StorachaClient:
    """
    Client for interacting with Storacha/web3.storage HTTP API.
    
    Implements the complete upload flow:
    1. Create CAR file from data
    2. store/add - Allocate space and get upload URL
    3. PUT CAR file to provided S3 URL  
    4. upload/add - Register the upload
    """
    
    def __init__(self, config: StorachaConfig):
        self.config = config
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def _ensure_session(self):
        """Ensure aiohttp session is created with proper SSL configuration."""
        if self._session is None or self._session.closed:
            # Create SSL context with proper certificate verification
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            
            # Create connector with SSL context
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector
            )
    
    def _create_car_file(self, data: bytes, filename: str = None) -> Tuple[str, str, int]:
        """
        Create a CAR file from data using ipfs-car CLI.
        
        Args:
            data: Raw bytes to convert to CAR
            filename: Optional filename for the data
            
        Returns:
            Tuple of (car_file_path, content_cid, car_size)
            
        Raises:
            StorachaError: If CAR creation fails
        """
        try:
            # Create temporary file for the data
            with tempfile.NamedTemporaryFile(
                mode='wb', 
                delete=False, 
                suffix=f"_{filename}" if filename else ""
            ) as tmp_data:
                tmp_data.write(data)
                tmp_data_path = tmp_data.name
            
            # Create temporary CAR file
            tmp_car_path = tmp_data_path + ".car"
            
            # Use ipfs-car pack to create CAR file
            result = subprocess.run(
                ["ipfs-car", "pack", tmp_data_path, "--output", tmp_car_path],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Extract content CID from stdout
            content_cid = result.stdout.strip()
            
            # Get CAR file size
            car_size = os.path.getsize(tmp_car_path)
            
            # Clean up original data file
            os.unlink(tmp_data_path)
            
            logger.info(f"Created CAR file: {tmp_car_path} (size: {car_size}, content CID: {content_cid})")
            
            return tmp_car_path, content_cid, car_size
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create CAR file: {e.stderr}")
            raise StorachaError(f"CAR creation failed: {e.stderr}")
        except Exception as e:
            logger.error(f"Unexpected error creating CAR file: {e}")
            raise StorachaError(f"CAR creation failed: {e}")
    
    def _get_car_cid(self, car_file_path: str) -> str:
        """
        Get the CID of a CAR file using ipfs-car hash.
        
        Args:
            car_file_path: Path to the CAR file
            
        Returns:
            CID of the CAR file (starts with 'bag...')
            
        Raises:
            StorachaError: If CID calculation fails
        """
        try:
            result = subprocess.run(
                ["ipfs-car", "hash", car_file_path],
                capture_output=True,
                text=True,
                check=True
            )
            
            car_cid = result.stdout.strip()
            logger.info(f"CAR file CID: {car_cid}")
            
            return car_cid
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to calculate CAR CID: {e.stderr}")
            raise StorachaError(f"CAR CID calculation failed: {e.stderr}")
    
    async def _make_bridge_request(self, tasks: List[List]) -> List[Dict[str, Any]]:
        """
        Make a request to the Storacha bridge API.
        
        Args:
            tasks: List of tasks in the format specified by Storacha API
            
        Returns:
            Response from the bridge API
            
        Raises:
            StorachaError: If the request fails
        """
        await self._ensure_session()
        
        headers = {
            "X-Auth-Secret": self.config.auth_secret,
            "Authorization": self.config.auth_token,
            "Content-Type": "application/json"
        }
        
        payload = {"tasks": tasks}
        
        try:
            async with self._session.post(
                f"{self.config.base_url}/bridge",
                json=payload,
                headers=headers
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Bridge API error {response.status}: {error_text}")
                    raise StorachaError(f"Bridge API error {response.status}: {error_text}")
                
                # Handle the DAG-JSON content type that Storacha returns
                response_text = await response.text()
                try:
                    result = json.loads(response_text)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse response as JSON: {e}")
                    logger.error(f"Response text: {response_text}")
                    raise StorachaError(f"Invalid JSON response: {e}")
                
                logger.debug(f"Bridge API response: {result}")
                
                return result
                
        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error: {e}")
            raise StorachaError(f"HTTP client error: {e}")
    
    async def _store_add(self, car_cid: str, car_size: int) -> Dict[str, Any]:
        """
        Step 1: Allocate space for the CAR file.
        
        Args:
            car_cid: CID of the CAR file
            car_size: Size of the CAR file in bytes
            
        Returns:
            Response from store/add operation
            
        Raises:
            StorachaUploadError: If space allocation fails
        """
        tasks = [
            [
                "store/add",
                self.config.space_did,
                {
                    "link": {"/": car_cid},
                    "size": car_size
                }
            ]
        ]
        
        try:
            response = await self._make_bridge_request(tasks)
            
            if isinstance(response, list) and len(response) > 0:
                result_item = response[0]
                
                if 'p' in result_item and 'out' in result_item['p']:
                    out = result_item['p']['out']
                    if 'ok' in out:
                        return out['ok']
                    elif 'error' in out:
                        error_msg = out['error']
                        raise StorachaUploadError(f"store/add failed: {error_msg}")
            
            raise StorachaUploadError(f"Unexpected store/add response format: {response}")
            
        except StorachaError:
            raise
        except Exception as e:
            logger.error(f"store/add operation failed: {e}")
            raise StorachaUploadError(f"store/add operation failed: {e}")
    
    async def _upload_car_to_s3(self, car_file_path: str, upload_url: str, headers: Dict[str, str]) -> None:
        """
        Step 2: Upload CAR file to the provided S3 URL.
        
        Args:
            car_file_path: Path to the CAR file
            upload_url: S3 upload URL
            headers: Headers required for the upload
            
        Raises:
            StorachaUploadError: If S3 upload fails
        """
        await self._ensure_session()
        
        try:
            async with aiofiles.open(car_file_path, 'rb') as f:
                car_data = await f.read()
            
            async with self._session.put(
                upload_url,
                data=car_data,
                headers=headers
            ) as response:
                
                if response.status not in [200, 201]:
                    error_text = await response.text()
                    logger.error(f"S3 upload failed {response.status}: {error_text}")
                    raise StorachaUploadError(f"S3 upload failed {response.status}: {error_text}")
                
                logger.info(f"Successfully uploaded CAR file to S3")
                
        except aiohttp.ClientError as e:
            logger.error(f"S3 upload error: {e}")
            raise StorachaUploadError(f"S3 upload error: {e}")
    
    async def _upload_add(self, content_cid: str, car_cid: str) -> Dict[str, Any]:
        """
        Step 3: Register the upload in the space.
        
        Args:
            content_cid: CID of the original content
            car_cid: CID of the CAR file
            
        Returns:
            Response from upload/add operation
            
        Raises:
            StorachaUploadError: If upload registration fails
        """
        tasks = [
            [
                "upload/add",
                self.config.space_did,
                {
                    "root": {"/": content_cid},
                    "shards": [{"/": car_cid}]
                }
            ]
        ]
        
        try:
            response = await self._make_bridge_request(tasks)
            
            if isinstance(response, list) and len(response) > 0:
                result_item = response[0]
                
                if 'p' in result_item and 'out' in result_item['p']:
                    out = result_item['p']['out']
                    if 'ok' in out:
                        return out['ok']
                    elif 'error' in out:
                        error_msg = out['error']
                        raise StorachaUploadError(f"upload/add failed: {error_msg}")
            
            raise StorachaUploadError(f"Unexpected upload/add response format: {response}")
            
        except StorachaError:
            raise
        except Exception as e:
            logger.error(f"upload/add operation failed: {e}")
            raise StorachaUploadError(f"upload/add operation failed: {e}")
    
    async def upload_data(self, data: bytes, filename: str = None) -> UploadResult:
        """
        Upload data to Storacha following the complete flow.
        
        This method implements the full Storacha upload process:
        1. Create CAR file from data
        2. store/add - Allocate space and get upload URL
        3. PUT CAR file to S3 URL
        4. upload/add - Register the upload
        
        Args:
            data: Raw bytes to upload
            filename: Optional filename for the data
            
        Returns:
            UploadResult containing CIDs and metadata
            
        Raises:
            StorachaUploadError: If upload fails at any step
        """
        if not self.config.space_did:
            raise StorachaAuthError("space_did is required for upload operations")
        
        car_file_path = None
        
        try:
            # Step 1: Create CAR file
            logger.info(f"Creating CAR file for {len(data)} bytes")
            car_file_path, content_cid, car_size = self._create_car_file(data, filename)
            car_cid = self._get_car_cid(car_file_path)
            
            # Step 2: Allocate space (store/add)
            logger.info(f"Allocating space for CAR file: {car_cid}")
            store_result = await self._store_add(car_cid, car_size)
            
            # Check if we need to upload or if it's already stored
            if store_result.get("status") == "done":
                logger.info("File already exists in Storacha, skipping upload")
            elif store_result.get("status") == "upload":
                # Step 3: Upload CAR file to S3
                upload_url = store_result["url"]
                upload_headers = store_result["headers"]
                
                logger.info(f"Uploading CAR file to S3: {upload_url}")
                await self._upload_car_to_s3(car_file_path, upload_url, upload_headers)
            else:
                raise StorachaUploadError(f"Unexpected store status: {store_result.get('status')}")
            
            # Step 4: Register upload (upload/add)
            logger.info(f"Registering upload: content={content_cid}, shard={car_cid}")
            upload_result = await self._upload_add(content_cid, car_cid)
            
            logger.info(f"✅ Upload complete! Content CID: {content_cid}")
            
            return UploadResult(
                content_cid=content_cid,
                shard_cid=car_cid,
                size=len(data)
            )
            
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            raise StorachaUploadError(f"Upload failed: {e}")
        
        finally:
            # Clean up temporary CAR file
            if car_file_path and os.path.exists(car_file_path):
                try:
                    os.unlink(car_file_path)
                    logger.debug(f"Cleaned up temporary CAR file: {car_file_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up CAR file {car_file_path}: {e}")
    
    async def list_uploads(self) -> List[Dict[str, Any]]:
        """
        List uploads in the space.
        
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
            response = await self._make_bridge_request(tasks)
            
            if isinstance(response, list) and len(response) > 0:
                result_item = response[0]
                
                if 'p' in result_item and 'out' in result_item['p']:
                    out = result_item['p']['out']
                    if 'ok' in out:
                        uploads = out['ok'].get('results', [])
                        logger.info(f"Found {len(uploads)} uploads")
                        return uploads
                    elif 'error' in out:
                        error_msg = out['error']
                        raise StorachaError(f"upload/list failed: {error_msg}")
            
            raise StorachaError(f"Unexpected upload/list response format: {response}")
            
        except StorachaError:
            raise
        except Exception as e:
            logger.error(f"list_uploads operation failed: {e}")
            raise StorachaError(f"list_uploads operation failed: {e}")


async def test_connection(config: StorachaConfig) -> bool:
    """
    Test connection to Storacha service.
    
    Args:
        config: Storacha configuration
        
    Returns:
        True if connection successful, False otherwise
    """
    try:
        async with StorachaClient(config) as client:
            uploads = await client.list_uploads()
            logger.info(f"✅ Connection successful! Found {len(uploads)} uploads")
            return True
    except Exception as e:
        logger.error(f"❌ Connection test failed: {e}")
        return False 