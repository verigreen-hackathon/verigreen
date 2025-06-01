"""
Global Sentinel-2 data fetcher for worldwide forest monitoring.
Adapts existing Sentinel-2 functionality to work with any global coordinates.
"""

import os
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta
import math

import boto3
from botocore import UNSIGNED
from botocore.config import Config
import rasterio
import mgrs

from config import SENTINEL_DATA_DIR
from sentinel.grid import GlobalGridCalculator, GlobalTileCoordinates

logger = logging.getLogger(__name__)

# Global Sentinel-2 Configuration
GLOBAL_SENTINEL_CONFIG = {
    "s3_bucket": "sentinel-s2-l2a",
    "bands": ["B04", "B08"],  # Red and NIR for NDVI calculation
    "cloud_cover_max": 20,  # Maximum acceptable cloud cover %
    "resolution": "R10m",   # 10m resolution for B04/B08
    "date_search_days": 30,  # Days to search back for recent imagery
    "fallback_days": 90,     # Extended search if no recent data found
}


class GlobalSentinelFetcher:
    """
    Fetches Sentinel-2 data for any global coordinates using MGRS tile system.
    """
    
    def __init__(self):
        """Initialize the global Sentinel-2 fetcher."""
        self.config = GLOBAL_SENTINEL_CONFIG
        self.grid_calculator = GlobalGridCalculator()
        self.s3_client = self._get_s3_client()
        self.mgrs_converter = mgrs.MGRS()
        logger.info("Initialized GlobalSentinelFetcher for worldwide coverage with proper MGRS")
    
    def _get_s3_client(self):
        """Create an S3 client for accessing Sentinel-2 public bucket."""
        return boto3.client('s3', config=Config(signature_version=UNSIGNED))
    
    def coordinates_to_mgrs_tiles(self, bounding_box: List[float]) -> List[str]:
        """
        Convert global coordinates to MGRS tile identifiers using proper MGRS library.
        
        Args:
            bounding_box: [west, south, east, north] in decimal degrees
            
        Returns:
            List of MGRS tile identifiers covering the area
        """
        west, south, east, north = bounding_box
        
        try:
            # Calculate multiple sample points across the bounding box
            sample_points = []
            
            # Sample points: corners + center
            sample_points.extend([
                (south, west),    # SW corner
                (south, east),    # SE corner  
                (north, west),    # NW corner
                (north, east),    # NE corner
                ((south + north) / 2, (west + east) / 2)  # Center
            ])
            
            # For larger areas, add more sample points
            lat_range = north - south
            lon_range = east - west
            if lat_range > 1.0 or lon_range > 1.0:
                # Add mid-points
                mid_lat = (south + north) / 2
                mid_lon = (west + east) / 2
                sample_points.extend([
                    (south, mid_lon),    # S mid
                    (north, mid_lon),    # N mid
                    (mid_lat, west),     # W mid  
                    (mid_lat, east),     # E mid
                ])
            
            mgrs_tiles = set()
            
            for lat, lon in sample_points:
                try:
                    # Convert lat/lon to MGRS
                    mgrs_coord = self.mgrs_converter.toMGRS(lat, lon, MGRSPrecision=0)
                    
                    # Extract the tile ID (first 5 characters: zone + band + square)
                    if len(mgrs_coord) >= 5:
                        tile_id = mgrs_coord[:5]
                        mgrs_tiles.add(tile_id)
                        logger.debug(f"Point ({lat:.3f}, {lon:.3f}) -> MGRS: {mgrs_coord} -> Tile: {tile_id}")
                
                except Exception as e:
                    logger.debug(f"MGRS conversion failed for ({lat}, {lon}): {e}")
                    continue
            
            result = list(mgrs_tiles)
            logger.info(f"Bounding box {bounding_box} covers MGRS tiles: {result}")
            return result
            
        except Exception as e:
            logger.error(f"MGRS calculation failed for {bounding_box}: {e}")
            # Fallback to center point only
            try:
                center_lat = (north + south) / 2
                center_lon = (east + west) / 2
                mgrs_coord = self.mgrs_converter.toMGRS(center_lat, center_lon, MGRSPrecision=0)
                if len(mgrs_coord) >= 5:
                    fallback_tile = mgrs_coord[:5]
                    logger.warning(f"Using fallback MGRS tile: {fallback_tile}")
                    return [fallback_tile]
            except:
                pass
            
            logger.error("Complete MGRS calculation failure - no tiles identified")
            return []
    
    def construct_s3_path(self, mgrs_tile: str, band: str, date: str) -> str:
        """
        Construct S3 path for Sentinel-2 data.
        
        Args:
            mgrs_tile: MGRS tile identifier (e.g., '30TUK')
            band: Band identifier (e.g., 'B04', 'B08')
            date: Date in format "YYYY/M/D"
            
        Returns:
            S3 path to the band file
        """
        # Parse MGRS tile
        utm_zone = mgrs_tile[:2]
        lat_band = mgrs_tile[2]
        grid_square = mgrs_tile[3:]
        
        # Parse date
        year, month, day = date.split('/')
        
        # Construct S3 path
        # Structure: tiles/{UTM_ZONE}/{LAT_BAND}/{GRID_SQUARE}/{YEAR}/{MONTH}/{DAY}/{SEQUENCE}/R10m/{BAND}.jp2
        return f"tiles/{utm_zone}/{lat_band}/{grid_square}/{year}/{month}/{day}/0/{self.config['resolution']}/{band}.jp2"
    
    def find_available_dates(self, mgrs_tile: str, max_days_back: int = None) -> List[str]:
        """
        Find available dates for a MGRS tile.
        
        Args:
            mgrs_tile: MGRS tile identifier
            max_days_back: Maximum days to search (default: config value)
            
        Returns:
            List of available dates in "YYYY/M/D" format
        """
        if max_days_back is None:
            max_days_back = self.config["date_search_days"]
        
        # Parse MGRS tile
        utm_zone = mgrs_tile[:2]
        lat_band = mgrs_tile[2]
        grid_square = mgrs_tile[3:]
        
        available_dates = []
        current_date = datetime.now()
        
        # Search backwards from current date
        for days_ago in range(max_days_back):
            check_date = current_date - timedelta(days=days_ago)
            year = check_date.year
            month = check_date.month
            day = check_date.day
            
            # Construct prefix for this date
            date_prefix = f"tiles/{utm_zone}/{lat_band}/{grid_square}/{year}/{month}/{day}/"
            
            try:
                # Check if data exists for this date
                response = self.s3_client.list_objects_v2(
                    Bucket=self.config["s3_bucket"],
                    Prefix=date_prefix,
                    MaxKeys=1
                )
                
                if response.get('Contents'):
                    date_str = f"{year}/{month}/{day}"
                    available_dates.append(date_str)
                    logger.debug(f"Found data for {mgrs_tile} on {date_str}")
                    
            except Exception as e:
                logger.debug(f"No data for {mgrs_tile} on {year}/{month}/{day}: {e}")
                continue
        
        return available_dates
    
    def find_best_date(self, mgrs_tile: str, required_bands: List[str] = None) -> Optional[str]:
        """
        Find the best available date with all required bands.
        
        Args:
            mgrs_tile: MGRS tile identifier
            required_bands: List of required bands (default: config bands)
            
        Returns:
            Best date string or None if no suitable date found
        """
        if required_bands is None:
            required_bands = self.config["bands"]
        
        # First search in recent period
        available_dates = self.find_available_dates(mgrs_tile, self.config["date_search_days"])
        
        # If no recent data, search further back
        if not available_dates:
            logger.info(f"No recent data for {mgrs_tile}, searching further back...")
            available_dates = self.find_available_dates(mgrs_tile, self.config["fallback_days"])
        
        if not available_dates:
            logger.warning(f"No data found for tile {mgrs_tile}")
            return None
        
        # Check each date for complete band set
        for date in available_dates:
            all_bands_available = True
            for band in required_bands:
                s3_path = self.construct_s3_path(mgrs_tile, band, date)
                try:
                    self.s3_client.head_object(Bucket=self.config["s3_bucket"], Key=s3_path)
                except self.s3_client.exceptions.ClientError:
                    all_bands_available = False
                    break
            
            if all_bands_available:
                logger.info(f"Found complete dataset for {mgrs_tile} on {date}")
                return date
        
        # If no complete dataset, return most recent anyway
        if available_dates:
            logger.warning(f"No complete dataset for {mgrs_tile}, using: {available_dates[0]}")
            return available_dates[0]
        
        return None
    
    def download_band(self, mgrs_tile: str, band: str, date: str, output_dir: Path) -> Optional[Path]:
        """
        Download a single band for a MGRS tile.
        
        Args:
            mgrs_tile: MGRS tile identifier
            band: Band identifier
            date: Date to download
            output_dir: Output directory
            
        Returns:
            Path to downloaded file or None if failed
        """
        s3_path = self.construct_s3_path(mgrs_tile, band, date)
        
        # Create output filename
        date_str = date.replace('/', '-')
        output_filename = f"{mgrs_tile}_{band}_{date_str}.jp2"
        output_path = output_dir / output_filename
        
        # Create output directory if needed
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            logger.info(f"Downloading {mgrs_tile} {band} for {date}")
            
            # Download from S3
            self.s3_client.download_file(
                self.config["s3_bucket"],
                s3_path,
                str(output_path)
            )
            
            # Validate downloaded file
            if output_path.exists() and output_path.stat().st_size > 0:
                logger.info(f"Successfully downloaded {output_filename}")
                return output_path
            else:
                logger.error(f"Downloaded file {output_filename} is invalid")
                return None
                
        except Exception as e:
            logger.error(f"Failed to download {s3_path}: {e}")
            return None
    
    def fetch_data_for_coordinates(self, bounding_box: List[float], 
                                 output_dir: Optional[str] = None) -> Tuple[List[Path], Dict]:
        """
        Fetch Sentinel-2 data for global coordinates.
        
        Args:
            bounding_box: [west, south, east, north] in decimal degrees
            output_dir: Output directory (default: config directory)
            
        Returns:
            Tuple of (downloaded_files, metadata)
        """
        if output_dir is None:
            output_dir = SENTINEL_DATA_DIR
        
        output_path = Path(output_dir)
        
        try:
            # Validate coordinates
            is_valid, error_msg = self.grid_calculator.validate_global_coordinates(bounding_box)
            if not is_valid:
                raise ValueError(f"Invalid coordinates: {error_msg}")
            
            # Get required MGRS tiles
            mgrs_tiles = self.coordinates_to_mgrs_tiles(bounding_box)
            logger.info(f"Fetching data for MGRS tiles: {mgrs_tiles}")
            
            downloaded_files = []
            tile_metadata = {}
            
            # Process each MGRS tile
            for mgrs_tile in mgrs_tiles:
                # Find best available date
                best_date = self.find_best_date(mgrs_tile, self.config["bands"])
                
                if not best_date:
                    logger.warning(f"No suitable date found for {mgrs_tile}")
                    continue
                
                tile_files = []
                # Download required bands
                for band in self.config["bands"]:
                    file_path = self.download_band(mgrs_tile, band, best_date, output_path)
                    if file_path:
                        tile_files.append(file_path)
                        downloaded_files.append(file_path)
                
                # Store metadata for this tile
                tile_metadata[mgrs_tile] = {
                    "date": best_date,
                    "bands": self.config["bands"],
                    "files": [str(f) for f in tile_files],
                    "file_count": len(tile_files)
                }
            
            # Calculate area statistics
            area_stats = self.grid_calculator.calculate_grid_area_km2(bounding_box)
            
            # Compile overall metadata
            metadata = {
                "bounding_box": bounding_box,
                "mgrs_tiles": mgrs_tiles,
                "total_files": len(downloaded_files),
                "area_statistics": area_stats,
                "tile_metadata": tile_metadata,
                "download_timestamp": datetime.now().isoformat(),
                "data_source": "Sentinel-2 L2A",
                "bands": self.config["bands"],
                "resolution": self.config["resolution"]
            }
            
            logger.info(f"Successfully fetched {len(downloaded_files)} files for global coordinates")
            return downloaded_files, metadata
            
        except Exception as e:
            logger.error(f"Failed to fetch Sentinel-2 data: {e}")
            return [], {"error": str(e), "bounding_box": bounding_box}
    
    def check_cache(self, bounding_box: List[float], max_age_days: int = 7) -> Optional[List[Path]]:
        """
        Check if cached data exists for the bounding box.
        
        Args:
            bounding_box: Coordinates to check
            max_age_days: Maximum age of cached data
            
        Returns:
            List of cached files or None if no valid cache
        """
        # Get MGRS tiles for this area
        mgrs_tiles = self.coordinates_to_mgrs_tiles(bounding_box)
        
        cached_files = []
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        
        output_path = Path(SENTINEL_DATA_DIR)
        
        for mgrs_tile in mgrs_tiles:
            for band in self.config["bands"]:
                # Look for files matching the tile and band pattern
                pattern = f"{mgrs_tile}_{band}_*.jp2"
                matching_files = list(output_path.glob(pattern))
                
                # Check if any files are recent enough
                for file_path in matching_files:
                    if file_path.stat().st_mtime > cutoff_time.timestamp():
                        cached_files.append(file_path)
        
        # Return cached files if we have complete coverage
        expected_files = len(mgrs_tiles) * len(self.config["bands"])
        if len(cached_files) >= expected_files:
            logger.info(f"Found {len(cached_files)} cached files for coordinates")
            return cached_files
        
        return None
    
    def get_or_fetch_data(self, bounding_box: List[float], 
                         force_download: bool = False,
                         max_cache_age_days: int = 7) -> Tuple[List[Path], Dict]:
        """
        Get cached data or fetch new data for coordinates.
        
        Args:
            bounding_box: [west, south, east, north] coordinates
            force_download: Force new download even if cache exists
            max_cache_age_days: Maximum age for cached data
            
        Returns:
            Tuple of (files, metadata)
        """
        if not force_download:
            cached_files = self.check_cache(bounding_box, max_cache_age_days)
            if cached_files:
                metadata = {
                    "data_source": "cached",
                    "file_count": len(cached_files),
                    "bounding_box": bounding_box,
                    "cache_hit": True
                }
                return cached_files, metadata
        
        # Fetch new data
        return self.fetch_data_for_coordinates(bounding_box)


# Global instance for easy access
global_sentinel_fetcher = GlobalSentinelFetcher() 