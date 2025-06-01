"""
Filecoin storage service implementation.

This module provides high-level services for uploading and managing files
on Filecoin storage via Storacha, built on top of the StorachaClient.
"""

import asyncio
import mimetypes
import os
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass, asdict
import aiofiles

from .client import (
    StorachaClient, 
    StorachaConfig, 
    StorachaError, 
    UploadResult,
    create_config_from_env
)

logger = logging.getLogger(__name__)


@dataclass
class FileMetadata:
    """Metadata for an uploaded file."""
    filename: str
    file_size: int
    content_type: str
    checksum_sha256: str
    upload_timestamp: datetime
    content_cid: str
    shard_cids: List[str]
    file_path: Optional[str] = None
    tags: Optional[Dict[str, str]] = None


@dataclass
class UploadProgress:
    """Progress information for file upload."""
    filename: str
    total_bytes: int
    uploaded_bytes: int
    percentage: float
    stage: str  # 'preparing', 'uploading', 'verifying', 'complete'
    estimated_time_remaining: Optional[float] = None
    current_chunk: Optional[int] = None
    total_chunks: Optional[int] = None


class FilecoinUploadError(Exception):
    """Exception raised when file upload fails."""
    pass


class FilecoinValidationError(Exception):
    """Exception raised when file validation fails."""
    pass


class FilecoinService:
    """
    High-level service for managing file uploads to Filecoin via Storacha.
    
    Provides methods for single file uploads with progress tracking,
    metadata generation, and validation.
    """
    
    def __init__(self, storacha_config: Optional[StorachaConfig] = None):
        """
        Initialize the FilecoinService.
        
        Args:
            storacha_config: Optional StorachaConfig. If None, loads from environment.
        """
        self.config = storacha_config or create_config_from_env()
        self._client: Optional[StorachaClient] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self._client = StorachaClient(self.config)
        await self._client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.__aexit__(exc_type, exc_val, exc_tb)
    
    @property
    def client(self) -> StorachaClient:
        """Get the StorachaClient instance."""
        if self._client is None:
            raise RuntimeError("FilecoinService must be used as async context manager")
        return self._client
    
    def _detect_content_type(self, file_path: str) -> str:
        """
        Detect the MIME type of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            MIME type string
        """
        content_type, _ = mimetypes.guess_type(file_path)
        if content_type is None:
            # Default to binary if we can't detect
            content_type = "application/octet-stream"
        
        logger.debug(f"Detected content type for {file_path}: {content_type}")
        return content_type
    
    async def _calculate_file_checksum(self, file_path: str) -> str:
        """
        Calculate SHA256 checksum of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Hexadecimal SHA256 checksum
        """
        sha256_hash = hashlib.sha256()
        
        # Read file in chunks to handle large files efficiently
        def read_file_sync():
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    sha256_hash.update(chunk)
        
        await asyncio.to_thread(read_file_sync)
        
        checksum = sha256_hash.hexdigest()
        logger.debug(f"Calculated checksum for {file_path}: {checksum}")
        return checksum
    
    def _validate_file(self, file_path: str) -> None:
        """
        Validate that a file exists and is readable.
        
        Args:
            file_path: Path to the file to validate
            
        Raises:
            FilecoinValidationError: If the file is invalid
        """
        if not os.path.exists(file_path):
            raise FilecoinValidationError(f"File does not exist: {file_path}")
        
        if not os.path.isfile(file_path):
            raise FilecoinValidationError(f"Path is not a file: {file_path}")
        
        if not os.access(file_path, os.R_OK):
            raise FilecoinValidationError(f"File is not readable: {file_path}")
        
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise FilecoinValidationError(f"File is empty: {file_path}")
        
        logger.debug(f"File validation passed for {file_path} ({file_size} bytes)")
    
    async def _prepare_file_metadata(
        self, 
        file_path: str, 
        tags: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Prepare comprehensive metadata for a file.
        
        Args:
            file_path: Path to the file
            tags: Optional tags to associate with the file
            
        Returns:
            Dictionary containing file metadata
        """
        # Validate file first
        self._validate_file(file_path)
        
        # Gather file information
        file_stat = os.stat(file_path)
        filename = os.path.basename(file_path)
        file_size = file_stat.st_size
        content_type = self._detect_content_type(file_path)
        
        # Calculate checksum
        checksum = await self._calculate_file_checksum(file_path)
        
        # Prepare metadata
        metadata = {
            "filename": filename,
            "file_path": file_path,
            "file_size": file_size,
            "content_type": content_type,
            "checksum_sha256": checksum,
            "created_time": datetime.fromtimestamp(file_stat.st_ctime),
            "modified_time": datetime.fromtimestamp(file_stat.st_mtime),
            "tags": tags or {}
        }
        
        logger.info(f"Prepared metadata for {filename}: {file_size} bytes, {content_type}")
        return metadata
    
    async def _track_upload_progress(
        self,
        filename: str,
        file_size: int,
        stage: str,
        progress_callback: Optional[Callable[[UploadProgress], None]] = None
    ) -> None:
        """
        Track and report upload progress.
        
        Args:
            filename: Name of the file being uploaded
            file_size: Total file size in bytes
            stage: Current stage of upload
            progress_callback: Optional callback to receive progress updates
        """
        if progress_callback:
            # For single file uploads, we'll track basic stages
            percentage = {
                'preparing': 10.0,
                'uploading': 50.0,
                'verifying': 90.0,
                'complete': 100.0
            }.get(stage, 0.0)
            
            progress = UploadProgress(
                filename=filename,
                total_bytes=file_size,
                uploaded_bytes=int(file_size * percentage / 100),
                percentage=percentage,
                stage=stage
            )
            
            try:
                progress_callback(progress)
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")
    
    async def upload_file(
        self,
        file_path: str,
        tags: Optional[Dict[str, str]] = None,
        progress_callback: Optional[Callable[[UploadProgress], None]] = None,
        validate_upload: bool = True
    ) -> FileMetadata:
        """
        Upload a single file to Filecoin storage.
        
        This method handles the complete upload process including:
        - File validation and preparation
        - Content type detection
        - Metadata generation
        - Progress tracking
        - Upload to Storacha
        - Result validation
        
        Args:
            file_path: Path to the file to upload
            tags: Optional tags to associate with the file
            progress_callback: Optional callback for progress updates
            validate_upload: Whether to validate the upload succeeded
            
        Returns:
            FileMetadata object with upload results
            
        Raises:
            FilecoinValidationError: If file validation fails
            FilecoinUploadError: If upload fails
            StorachaError: If Storacha API calls fail
        """
        logger.info(f"Starting upload for file: {file_path}")
        
        try:
            # Stage 1: Prepare file and metadata
            await self._track_upload_progress(
                os.path.basename(file_path), 
                0, 
                'preparing', 
                progress_callback
            )
            
            metadata = await self._prepare_file_metadata(file_path, tags)
            filename = metadata["filename"]
            file_size = metadata["file_size"]
            
            # Stage 2: Upload to Storacha
            await self._track_upload_progress(filename, file_size, 'uploading', progress_callback)
            
            # Read file data
            async with aiofiles.open(file_path, 'rb') as f:
                file_data = await f.read()
            
            # Upload data to Storacha
            upload_result = await self.client.upload_data(file_data, filename)
            
            # Stage 3: Verify upload
            await self._track_upload_progress(filename, file_size, 'verifying', progress_callback)
            
            if validate_upload:
                await self._validate_upload_result(upload_result, metadata)
            
            # Stage 4: Complete
            await self._track_upload_progress(filename, file_size, 'complete', progress_callback)
            
            # Create final metadata object
            file_metadata = FileMetadata(
                filename=filename,
                file_size=file_size,
                content_type=metadata["content_type"],
                checksum_sha256=metadata["checksum_sha256"],
                upload_timestamp=datetime.utcnow(),
                content_cid=upload_result.content_cid,
                shard_cids=[upload_result.shard_cid],
                file_path=file_path,
                tags=tags
            )
            
            logger.info(
                f"Successfully uploaded {filename} to Filecoin. "
                f"CID: {upload_result.content_cid}, Size: {file_size} bytes"
            )
            
            return file_metadata
            
        except (FilecoinValidationError, FilecoinUploadError):
            # Re-raise our custom exceptions as-is
            raise
        except StorachaError as e:
            # Wrap Storacha errors
            raise FilecoinUploadError(f"Storacha upload failed: {e}")
        except Exception as e:
            # Wrap any other unexpected errors
            logger.error(f"Unexpected error during upload: {e}")
            raise FilecoinUploadError(f"Unexpected upload error: {e}")
    
    async def _validate_upload_result(
        self, 
        upload_result: UploadResult, 
        file_metadata: Dict[str, Any]
    ) -> None:
        """
        Validate that the upload result is consistent.
        
        Args:
            upload_result: Result from Storacha upload
            file_metadata: Original file metadata
            
        Raises:
            FilecoinValidationError: If validation fails
        """
        # Basic validation
        if not upload_result.content_cid:
            raise FilecoinValidationError("Upload result missing content CID")
        
        if not upload_result.shard_cid:
            raise FilecoinValidationError("Upload result missing shard CID")
        
        # Size validation (allowing for CAR overhead)
        original_size = file_metadata["file_size"]
        if upload_result.size < original_size:
            raise FilecoinValidationError(
                f"Upload size ({upload_result.size}) is smaller than original file ({original_size})"
            )
        
        # Additional validation could include:
        # - Retrieving the file and comparing checksums
        # - Verifying the CID format
        # - Checking that shards are accessible
        
        logger.debug(
            f"Upload validation passed. CID: {upload_result.content_cid}, "
            f"Shard: {upload_result.shard_cid}"
        )
    
    async def get_file_info(self, content_cid: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve information about a previously uploaded file.
        
        Args:
            content_cid: Content CID of the file
            
        Returns:
            File information if found, None otherwise
            
        Raises:
            StorachaError: If API call fails
        """
        try:
            uploads = await self.client.list_uploads()
            
            # Find the upload with matching CID
            for upload in uploads:
                if upload.get("root") == content_cid:
                    return upload
            
            logger.debug(f"No upload found with CID: {content_cid}")
            return None
            
        except StorachaError as e:
            logger.error(f"Failed to retrieve file info for CID {content_cid}: {e}")
            raise
    
    async def list_uploaded_files(self) -> List[Dict[str, Any]]:
        """
        List all files uploaded to the current space.
        
        Returns:
            List of upload records from Storacha
            
        Raises:
            StorachaError: If API call fails
        """
        try:
            uploads = await self.client.list_uploads()
            logger.info(f"Retrieved {len(uploads)} uploaded files")
            return uploads
            
        except StorachaError as e:
            logger.error(f"Failed to list uploaded files: {e}")
            raise
    
    async def test_service(self) -> bool:
        """
        Test the FilecoinService connectivity and configuration.
        
        Returns:
            True if service is working correctly
            
        Raises:
            StorachaError: If service test fails
        """
        try:
            # Test basic connectivity
            await self.client.list_uploads()
            logger.info("FilecoinService test successful")
            return True
            
        except StorachaError as e:
            logger.error(f"FilecoinService test failed: {e}")
            raise


# Utility functions

async def upload_single_file(
    file_path: str,
    storacha_config: Optional[StorachaConfig] = None,
    tags: Optional[Dict[str, str]] = None,
    progress_callback: Optional[Callable[[UploadProgress], None]] = None
) -> FileMetadata:
    """
    Convenience function to upload a single file.
    
    Args:
        file_path: Path to the file to upload
        storacha_config: Optional StorachaConfig (loads from env if None)
        tags: Optional tags to associate with the file
        progress_callback: Optional callback for progress updates
        
    Returns:
        FileMetadata object with upload results
        
    Raises:
        FilecoinValidationError: If file validation fails
        FilecoinUploadError: If upload fails
        StorachaError: If Storacha API calls fail
    """
    async with FilecoinService(storacha_config) as service:
        return await service.upload_file(
            file_path=file_path,
            tags=tags,
            progress_callback=progress_callback
        )


def create_progress_logger() -> Callable[[UploadProgress], None]:
    """
    Create a simple progress callback that logs to the logger.
    
    Returns:
        Progress callback function
    """
    def log_progress(progress: UploadProgress) -> None:
        logger.info(
            f"Upload progress for {progress.filename}: "
            f"{progress.percentage:.1f}% ({progress.stage})"
        )
    
    return log_progress 