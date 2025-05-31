"""
Simplified Sentinel-2 data download from AWS S3 public bucket.
Downloads hardcoded cloud-free tiles for Sabangau National Park.
"""
import os
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path

import boto3
from botocore import UNSIGNED
from botocore.config import Config
import rasterio

from ..config import SENTINEL_DATA_DIR

logger = logging.getLogger(__name__)

# Configuration for Sabangau National Park demo
SABANGAU_CONFIG = {
    "tile_id": "49MCT",  # Updated to correct tile ID for Central Kalimantan
    "date": "2023/5/1",
    "bands": ["B04", "B08"],  # B04=Red, B08=NIR for NDVI calculation
    "s3_bucket": "sentinel-s2-l2a",
    "coverage_area": (10.24, 10.24),  # km x km
}


def get_s3_client():
    """
    Create an S3 client configured for unsigned requests (public bucket access).
    
    Returns:
        boto3.client: Configured S3 client
    """
    return boto3.client('s3', config=Config(signature_version=UNSIGNED))


def construct_s3_path(band: str) -> str:
    """
    Construct the S3 path for a specific band of the hardcoded tile.
    
    Args:
        band: Band identifier (e.g., 'B04', 'B08')
        
    Returns:
        str: S3 path to the band file
    """
    # Sentinel-2 S3 path structure: tiles/{UTM_ZONE}/{LATITUDE_BAND}/{SQUARE}/{YEAR}/{MONTH}/{DAY}/{SEQUENCE}/R10m/{BAND}.jp2
    config = SABANGAU_CONFIG
    tile_parts = list(config["tile_id"])  # Split '49MCT' into ['4', '9', 'M', 'C', 'T']
    utm_zone = ''.join(tile_parts[:2])  # '49'
    latitude_band = tile_parts[2]  # 'M'
    square = ''.join(tile_parts[3:])  # 'CT'
    
    # Parse date - use as-is, no leading zeros needed
    year, month, day = config["date"].split('/')
    
    # B04 and B08 are available at 10m resolution
    return f"tiles/{utm_zone}/{latitude_band}/{square}/{year}/{month}/{day}/0/R10m/{band}.jp2"


def download_band(s3_client, band: str, output_dir: Path) -> Optional[Path]:
    """
    Download a single band from S3.
    
    Args:
        s3_client: Configured boto3 S3 client
        band: Band identifier (e.g., 'B04', 'B08')
        output_dir: Directory to save downloaded files
        
    Returns:
        Path to downloaded file or None if download failed
    """
    s3_path = construct_s3_path(band)
    local_path = output_dir / f"{band}.jp2"
    
    try:
        logger.info(f"Downloading {band} from s3://{SABANGAU_CONFIG['s3_bucket']}/{s3_path}")
        print(f"DEBUG: Full S3 path: s3://{SABANGAU_CONFIG['s3_bucket']}/{s3_path}")  # Debug print
        s3_client.download_file(
            SABANGAU_CONFIG['s3_bucket'],
            s3_path,
            str(local_path)
        )
        logger.info(f"Successfully downloaded {band} to {local_path}")
        return local_path
    except Exception as e:
        logger.error(f"Failed to download {band}: {e}")
        print(f"DEBUG: Error details for {band}: {type(e).__name__}: {str(e)}")  # Debug print
        return None


def validate_band_file(file_path: Path) -> Dict[str, any]:
    """
    Validate a downloaded band file using rasterio.
    
    Args:
        file_path: Path to the band file
        
    Returns:
        Dict containing validation results
    """
    validation_result = {
        "path": str(file_path),
        "exists": file_path.exists(),
        "size_mb": 0,
        "readable": False,
        "crs": None,
        "bounds": None,
        "shape": None,
        "errors": []
    }
    
    if not file_path.exists():
        validation_result["errors"].append("File does not exist")
        return validation_result
    
    # Get file size
    validation_result["size_mb"] = file_path.stat().st_size / (1024 * 1024)
    
    # Try to open with rasterio
    try:
        with rasterio.open(file_path) as dataset:
            validation_result["readable"] = True
            validation_result["crs"] = str(dataset.crs)
            validation_result["bounds"] = dataset.bounds
            validation_result["shape"] = (dataset.height, dataset.width)
            
            # Basic sanity checks
            if dataset.height == 0 or dataset.width == 0:
                validation_result["errors"].append("Image has zero dimensions")
            
            if dataset.crs is None:
                validation_result["errors"].append("No coordinate reference system defined")
                
    except Exception as e:
        validation_result["errors"].append(f"Failed to read file: {str(e)}")
    
    return validation_result


def validate_downloaded_data(downloaded_files: List[Path]) -> Tuple[bool, Dict[str, any]]:
    """
    Validate all downloaded band files.
    
    Args:
        downloaded_files: List of paths to downloaded files
        
    Returns:
        Tuple of (is_valid, validation_report)
    """
    validation_report = {
        "total_files": len(downloaded_files),
        "valid_files": 0,
        "total_size_mb": 0,
        "band_validations": {},
        "overall_valid": False,
        "errors": []
    }
    
    for file_path in downloaded_files:
        band_name = file_path.stem  # Get filename without extension
        validation_result = validate_band_file(file_path)
        validation_report["band_validations"][band_name] = validation_result
        
        if validation_result["readable"] and not validation_result["errors"]:
            validation_report["valid_files"] += 1
        
        validation_report["total_size_mb"] += validation_result["size_mb"]
    
    # Check if all required bands are present and valid
    required_bands = set(SABANGAU_CONFIG["bands"])
    downloaded_bands = set(validation_report["band_validations"].keys())
    
    if required_bands != downloaded_bands:
        missing = required_bands - downloaded_bands
        validation_report["errors"].append(f"Missing required bands: {missing}")
    
    validation_report["overall_valid"] = (
        validation_report["valid_files"] == validation_report["total_files"] and
        len(validation_report["errors"]) == 0
    )
    
    return validation_report["overall_valid"], validation_report


def download_sentinel_imagery(output_dir: Optional[str] = None, 
                            retry_count: int = 3) -> Tuple[List[Path], Dict[str, any]]:
    """
    Download Sentinel-2 imagery for Sabangau National Park from AWS S3.
    
    This function downloads the hardcoded cloud-free tile (49MEB from 2023-05-01)
    including only the required bands for NDVI calculation (B04-Red and B08-NIR).
    
    Args:
        output_dir: Directory to save downloaded files (default: configured sentinel data dir)
        retry_count: Number of retry attempts for failed downloads
        
    Returns:
        Tuple of (list of downloaded file paths, download report)
    """
    if output_dir is None:
        output_dir = SENTINEL_DATA_DIR
    else:
        output_dir = Path(output_dir)
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize S3 client
    s3_client = get_s3_client()
    
    downloaded_files = []
    download_report = {
        "config": SABANGAU_CONFIG,
        "output_dir": str(output_dir),
        "downloads": {},
        "success": False
    }
    
    # Download each band
    for band in SABANGAU_CONFIG["bands"]:
        success = False
        attempts = 0
        
        while not success and attempts < retry_count:
            attempts += 1
            logger.info(f"Downloading {band} (attempt {attempts}/{retry_count})")
            
            result = download_band(s3_client, band, output_dir)
            if result:
                downloaded_files.append(result)
                download_report["downloads"][band] = {
                    "status": "success",
                    "path": str(result),
                    "attempts": attempts
                }
                success = True
            else:
                if attempts < retry_count:
                    logger.warning(f"Retrying download for {band}")
                else:
                    logger.error(f"Failed to download {band} after {retry_count} attempts")
                    download_report["downloads"][band] = {
                        "status": "failed",
                        "attempts": attempts
                    }
    
    # Validate downloaded data
    if downloaded_files:
        is_valid, validation_report = validate_downloaded_data(downloaded_files)
        download_report["validation"] = validation_report
        download_report["success"] = is_valid
    else:
        download_report["success"] = False
        download_report["validation"] = {"error": "No files downloaded"}
    
    return downloaded_files, download_report


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test the download function
    print("Starting Sentinel-2 download for Sabangau National Park...")
    print(f"Output directory: {SENTINEL_DATA_DIR}")
    files, report = download_sentinel_imagery()
    
    print(f"\nDownload complete!")
    print(f"Success: {report['success']}")
    print(f"Downloaded files: {[str(f) for f in files]}")
    
    if report.get('validation'):
        print(f"\nValidation report:")
        print(f"  Valid files: {report['validation']['valid_files']}/{report['validation']['total_files']}")
        print(f"  Total size: {report['validation']['total_size_mb']:.2f} MB") 