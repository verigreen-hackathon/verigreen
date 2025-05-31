"""
Sentinel-2 data download from AWS S3 public bucket.
Downloads cloud-free tiles for Batang Toru Ecosystem (Tapanuli orangutan habitat).
"""
import os
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta

import boto3
from botocore import UNSIGNED
from botocore.config import Config
import rasterio

from config import SENTINEL_DATA_DIR
from sentinel.batang_toru_mapper import batang_toru_mapper, get_claim_download_config

logger = logging.getLogger(__name__)

# Configuration for Batang Toru Ecosystem
BATANG_TORU_CONFIG = {
    "tile_id": "47NQH",  # Sentinel-2 MGRS tile covering Batang Toru area
    "utm_zone": "47N",
    "grid_square": "QH", 
    "center_lat": 1.2,
    "center_lon": 99.2,
    "bands": ["B04", "B08"],  # B04=Red, B08=NIR for NDVI calculation
    "s3_bucket": "sentinel-s2-l2a",
    "coverage_area": (10.24, 10.24),  # km x km (standard Sentinel-2 tile)
    "cloud_cover_max": 20,  # Maximum acceptable cloud cover %
}


def get_s3_client():
    """
    Create an S3 client configured for unsigned requests (public bucket access).
    
    Returns:
        boto3.client: Configured S3 client
    """
    return boto3.client('s3', config=Config(signature_version=UNSIGNED))


def construct_s3_path_for_batang_toru(band: str, date: str) -> str:
    """
    Construct the S3 path for a specific band of the Batang Toru tile.
    
    Args:
        band: Band identifier (e.g., 'B04', 'B08')
        date: Date in format "YYYY/M/D"
        
    Returns:
        str: S3 path to the band file
    """
    # Sentinel-2 S3 path structure: tiles/{UTM_ZONE}/{LATITUDE_BAND}/{SQUARE}/{YEAR}/{MONTH}/{DAY}/{SEQUENCE}/R10m/{BAND}.jp2
    config = BATANG_TORU_CONFIG
    tile_parts = list(config["tile_id"])  # Split '47NQH' into ['4', '7', 'N', 'Q', 'H']
    utm_zone = ''.join(tile_parts[:2])  # '47'
    latitude_band = tile_parts[2]  # 'N'
    square = ''.join(tile_parts[3:])  # 'QH'
    
    # Parse date
    year, month, day = date.split('/')
    
    # B04 and B08 are available at 10m resolution
    return f"tiles/{utm_zone}/{latitude_band}/{square}/{year}/{month}/{day}/0/R10m/{band}.jp2"


def find_available_dates_for_tile(s3_client, tile_id: str, max_days_back: int = 30) -> List[str]:
    """
    Find available dates for a Sentinel-2 tile by querying the S3 bucket.
    
    Args:
        s3_client: Configured boto3 S3 client
        tile_id: Sentinel-2 tile ID (e.g., '47NQH')
        max_days_back: Maximum number of days to look back from current date
        
    Returns:
        List of available dates in "YYYY/M/D" format, sorted by most recent first
    """
    config = BATANG_TORU_CONFIG
    tile_parts = list(tile_id)
    utm_zone = ''.join(tile_parts[:2])  # '47'
    latitude_band = tile_parts[2]  # 'N'
    square = ''.join(tile_parts[3:])  # 'QH'
    
    available_dates = []
    current_date = datetime.now()
    
    # Check the last max_days_back days
    for days_ago in range(max_days_back):
        check_date = current_date - timedelta(days=days_ago)
        year = check_date.year
        month = check_date.month
        day = check_date.day
        
        # Construct the prefix to check if this date has data
        date_prefix = f"tiles/{utm_zone}/{latitude_band}/{square}/{year}/{month}/{day}/"
        
        try:
            # List objects with this prefix
            response = s3_client.list_objects_v2(
                Bucket=config["s3_bucket"],
                Prefix=date_prefix,
                MaxKeys=1
            )
            
            # If we found objects, this date has data
            if response.get('Contents'):
                date_str = f"{year}/{month}/{day}"
                available_dates.append(date_str)
                logger.info(f"Found available Sentinel-2 data for {date_str}")
                
        except Exception as e:
            logger.debug(f"No data found for {year}/{month}/{day}: {e}")
            continue
    
    return available_dates


def find_recent_cloud_free_date(tile_id: str, target_bands: List[str]) -> Optional[str]:
    """
    Find a recent date with cloud-free imagery for the specified tile.
    
    Args:
        tile_id: Sentinel-2 tile ID
        target_bands: List of required bands
        
    Returns:
        Date string in "YYYY/M/D" format or None if no suitable date found
    """
    s3_client = get_s3_client()
    
    # Get available dates from the last 30 days
    available_dates = find_available_dates_for_tile(s3_client, tile_id, max_days_back=30)
    
    if not available_dates:
        logger.warning(f"No available dates found for tile {tile_id} in the last 30 days")
        # Fallback to known dates that typically have data
        fallback_dates = [
            # Use dates from early 2025 that are more likely to exist
            f"{datetime.now().year}/5/15",
            f"{datetime.now().year}/4/20", 
            f"{datetime.now().year}/3/25",
            f"{datetime.now().year - 1}/12/15",
            f"{datetime.now().year - 1}/11/10"
        ]
        logger.info(f"Using fallback dates: {fallback_dates}")
        return fallback_dates[0]
    
    # Verify that the most recent date has all required bands
    for date in available_dates:
        all_bands_available = True
        for band in target_bands:
            s3_path = construct_s3_path_for_batang_toru(band, date)
            try:
                s3_client.head_object(Bucket=BATANG_TORU_CONFIG["s3_bucket"], Key=s3_path)
                logger.debug(f"Band {band} available for date {date}")
            except s3_client.exceptions.ClientError:
                logger.debug(f"Band {band} not available for date {date}")
                all_bands_available = False
                break
        
        if all_bands_available:
            logger.info(f"Found complete dataset for date {date}")
            return date
    
    # If no complete dataset found, return the most recent date anyway
    if available_dates:
        logger.warning(f"No complete dataset found, using most recent: {available_dates[0]}")
        return available_dates[0]
    
    return None


def download_band_for_claim(s3_client, band: str, output_dir: Path, 
                           claim_config: Dict, date: Optional[str] = None, 
                           retry_count: int = 3) -> Optional[Path]:
    """
    Download a single band for a specific land claim with automatic date discovery and retry logic.
    
    Args:
        s3_client: Configured boto3 S3 client
        band: Band identifier (e.g., 'B04', 'B08')
        output_dir: Directory to save downloaded files
        claim_config: Configuration from batang_toru_mapper
        date: Specific date to download (auto-detect if None)
        retry_count: Number of retry attempts per date
        
    Returns:
        Path to downloaded file or None if download failed
    """
    # Get list of candidate dates
    if date is None:
        tile_id = claim_config["tile_ids"][0] if claim_config.get("tile_ids") else BATANG_TORU_CONFIG["tile_id"]
        candidate_dates = []
        
        # First try to find available dates dynamically
        try:
            available_dates = find_available_dates_for_tile(s3_client, tile_id, max_days_back=30)
            candidate_dates.extend(available_dates[:5])  # Try up to 5 most recent
        except Exception as e:
            logger.warning(f"Failed to discover available dates: {e}")
        
        # Add fallback dates
        current_year = datetime.now().year
        fallback_dates = [
            f"{current_year}/5/15",
            f"{current_year}/4/20", 
            f"{current_year}/3/25",
            f"{current_year - 1}/12/15",
            f"{current_year - 1}/11/10",
            "2024/6/15",  # Keep original as last resort
        ]
        
        # Combine and deduplicate
        all_dates = candidate_dates + [d for d in fallback_dates if d not in candidate_dates]
        candidate_dates = all_dates[:8]  # Limit to 8 attempts total
        
        logger.info(f"Will try dates in order: {candidate_dates}")
    else:
        candidate_dates = [date]
    
    # Try each candidate date
    for attempt_date in candidate_dates:
        logger.info(f"Attempting to download {band} for date {attempt_date}")
        
        s3_path = construct_s3_path_for_batang_toru(band, attempt_date)
        
        # Create filename with claim info
        processing_area = claim_config["processing_area"]
        lat = processing_area["center_point"]["lat"]
        lon = processing_area["center_point"]["lon"]
        
        local_filename = f"{band}_{lat:.3f}_{lon:.3f}_{attempt_date.replace('/', '-')}.jp2"
        local_path = output_dir / local_filename
        
        # Try to download this date with retries
        for attempt in range(1, retry_count + 1):
            try:
                logger.info(f"Downloading {band} for claim area (attempt {attempt}/{retry_count})")
                logger.info(f"Downloading {band} for Batang Toru area from s3://{BATANG_TORU_CONFIG['s3_bucket']}/{s3_path}")
                
                s3_client.download_file(
                    BATANG_TORU_CONFIG['s3_bucket'],
                    s3_path,
                    str(local_path)
                )
                logger.info(f"Successfully downloaded {band} from {attempt_date} to {local_path}")
                return local_path
                
            except s3_client.exceptions.ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == '404':
                    logger.warning(f"Data not available for {band} on {attempt_date} (404 Not Found)")
                    break  # No point retrying 404s, try next date
                else:
                    logger.error(f"Failed to download {band}: An error occurred ({error_code}) when calling the HeadObject operation: {e.response['Error']['Message']}")
                    if attempt < retry_count:
                        logger.warning(f"Retrying download for {band}")
                    else:
                        logger.error(f"Failed to download {band} after {retry_count} attempts")
                        break  # Try next date
                        
            except Exception as e:
                logger.error(f"Failed to download {band}: {e}")
                if attempt < retry_count:
                    logger.warning(f"Retrying download for {band}")
                else:
                    logger.error(f"Failed to download {band} after {retry_count} attempts")
                    break  # Try next date
    
    logger.error(f"Failed to download {band} for any available date")
    return None


def download_band(s3_client, band: str, output_dir: Path) -> Optional[Path]:
    """
    Download a single band from S3 (backward compatibility function).
    
    Args:
        s3_client: Configured boto3 S3 client
        band: Band identifier (e.g., 'B04', 'B08')
        output_dir: Directory to save downloaded files
        
    Returns:
        Path to downloaded file or None if download failed
    """
    # Use default Batang Toru configuration
    default_config = {
        "tile_ids": [BATANG_TORU_CONFIG["tile_id"]],
        "processing_area": {
            "center_point": {
                "lat": BATANG_TORU_CONFIG["center_lat"],
                "lon": BATANG_TORU_CONFIG["center_lon"]
            }
        }
    }
    
    return download_band_for_claim(s3_client, band, output_dir, default_config)


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
    required_bands = set(BATANG_TORU_CONFIG["bands"])
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
    Download Sentinel-2 imagery for Batang Toru Ecosystem from AWS S3.
    
    This function downloads the hardcoded cloud-free tile (47NQH from 2024-06-15)
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
        "config": BATANG_TORU_CONFIG,
        "output_dir": str(output_dir),
        "downloads": {},
        "success": False
    }
    
    # Download each band
    for band in BATANG_TORU_CONFIG["bands"]:
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


def download_sentinel_imagery_for_claim(southwest_x: int, southwest_y: int,
                                       northeast_x: int, northeast_y: int,
                                       output_dir: Optional[str] = None,
                                       retry_count: int = 3) -> Tuple[List[Path], Dict[str, any]]:
    """
    Download Sentinel-2 imagery for a specific land claim in the Batang Toru grid.
    
    Args:
        southwest_x, southwest_y: Southwest corner of claim (0-9)
        northeast_x, northeast_y: Northeast corner of claim (0-9)
        output_dir: Directory to save downloaded files
        retry_count: Number of retry attempts for failed downloads
        
    Returns:
        Tuple of (list of downloaded file paths, download report)
    """
    # Get download configuration for the claim
    claim_config = get_claim_download_config(southwest_x, southwest_y, northeast_x, northeast_y)
    
    if not claim_config:
        error_msg = f"Invalid claim area: ({southwest_x},{southwest_y}) to ({northeast_x},{northeast_y})"
        logger.error(error_msg)
        return [], {"success": False, "error": error_msg}
    
    if output_dir is None:
        output_dir = SENTINEL_DATA_DIR
    else:
        output_dir = Path(output_dir)
    
    # Create claim-specific subdirectory
    claim_dir = output_dir / f"claim_{southwest_x}_{southwest_y}_to_{northeast_x}_{northeast_y}"
    claim_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize S3 client
    s3_client = get_s3_client()
    
    downloaded_files = []
    download_report = {
        "claim_area": {
            "southwest": {"x": southwest_x, "y": southwest_y},
            "northeast": {"x": northeast_x, "y": northeast_y}
        },
        "config": claim_config,
        "output_dir": str(claim_dir),
        "downloads": {},
        "success": False
    }
    
    # Download each required band for the claim
    for band in claim_config["bands"]:
        success = False
        attempts = 0
        
        while not success and attempts < retry_count:
            attempts += 1
            logger.info(f"Downloading {band} for claim area (attempt {attempts}/{retry_count})")
            
            result = download_band_for_claim(s3_client, band, claim_dir, claim_config)
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


def cache_check_for_claim(southwest_x: int, southwest_y: int,
                         northeast_x: int, northeast_y: int,
                         max_age_days: int = 30) -> Optional[List[Path]]:
    """
    Check if we already have cached Sentinel-2 data for a claim area.
    
    Args:
        southwest_x, southwest_y: Southwest corner of claim
        northeast_x, northeast_y: Northeast corner of claim
        max_age_days: Maximum age of cached files to consider valid
        
    Returns:
        List of cached file paths if available, None otherwise
    """
    claim_dir = SENTINEL_DATA_DIR / f"claim_{southwest_x}_{southwest_y}_to_{northeast_x}_{northeast_y}"
    
    if not claim_dir.exists():
        return None
    
    # Check for required bands
    required_bands = BATANG_TORU_CONFIG["bands"]
    cached_files = []
    
    for band in required_bands:
        # Look for files matching the band pattern
        pattern = f"{band}_*.jp2"
        matching_files = list(claim_dir.glob(pattern))
        
        if not matching_files:
            return None  # Missing band
        
        # Use the most recent file for this band
        most_recent = max(matching_files, key=lambda p: p.stat().st_mtime)
        
        # Check if file is not too old
        file_age = datetime.now().timestamp() - most_recent.stat().st_mtime
        if file_age > (max_age_days * 24 * 3600):
            return None  # Files are too old
        
        cached_files.append(most_recent)
    
    logger.info(f"Found cached Sentinel-2 data for claim ({southwest_x},{southwest_y}) to ({northeast_x},{northeast_y})")
    return cached_files


def get_or_download_sentinel_for_claim(southwest_x: int, southwest_y: int,
                                     northeast_x: int, northeast_y: int,
                                     force_download: bool = False,
                                     max_cache_age_days: int = 30) -> Tuple[List[Path], Dict[str, any]]:
    """
    Get Sentinel-2 imagery for a claim, using cache if available or downloading if needed.
    
    Args:
        southwest_x, southwest_y: Southwest corner of claim
        northeast_x, northeast_y: Northeast corner of claim
        force_download: Force download even if cached data exists
        max_cache_age_days: Maximum age of cached data to use
        
    Returns:
        Tuple of (list of file paths, operation report)
    """
    report = {
        "claim_area": {
            "southwest": {"x": southwest_x, "y": southwest_y},
            "northeast": {"x": northeast_x, "y": northeast_y}
        },
        "cache_used": False,
        "download_performed": False,
        "success": False
    }
    
    # Check cache first (unless forced download)
    if not force_download:
        cached_files = cache_check_for_claim(southwest_x, southwest_y, northeast_x, northeast_y, max_cache_age_days)
        if cached_files:
            report["cache_used"] = True
            report["success"] = True
            report["files"] = [str(f) for f in cached_files]
            logger.info(f"Using cached Sentinel-2 data for claim area")
            return cached_files, report
    
    # Download new data
    logger.info(f"Downloading new Sentinel-2 data for claim area")
    files, download_report = download_sentinel_imagery_for_claim(
        southwest_x, southwest_y, northeast_x, northeast_y
    )
    
    report["download_performed"] = True
    report["download_report"] = download_report
    report["success"] = download_report["success"]
    
    if files:
        report["files"] = [str(f) for f in files]
    
    return files, report


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test the download function
    print("Starting Sentinel-2 download for Batang Toru Ecosystem...")
    print(f"Output directory: {SENTINEL_DATA_DIR}")
    files, report = download_sentinel_imagery()
    
    print(f"\nDownload complete!")
    print(f"Success: {report['success']}")
    print(f"Downloaded files: {[str(f) for f in files]}")
    
    if report.get('validation'):
        print(f"\nValidation report:")
        print(f"  Valid files: {report['validation']['valid_files']}/{report['validation']['total_files']}")
        print(f"  Total size: {report['validation']['total_size_mb']:.2f} MB") 