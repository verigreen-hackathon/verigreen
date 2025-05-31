"""
Grid mapping layer for Batang Toru Ecosystem.
Connects the 10x10 Batang Toru grid with the 32x32 Sentinel-2 grid system.
"""

import logging
import math
from typing import Dict, List, Tuple, Optional, NamedTuple
from rasterio.coords import BoundingBox

from ..utils.validation import grid_to_gps_coordinates
from .grid import TileCoordinates, GridCalculator
from ..config import GRID_CONFIG

logger = logging.getLogger(__name__)

# Batang Toru Sentinel-2 Configuration
BATANG_TORU_SENTINEL_CONFIG = {
    "tile_id": "47NQH",  # Sentinel-2 MGRS tile covering Batang Toru area
    "utm_zone": "47N",
    "grid_square": "QH",
    "center_lat": 1.2,
    "center_lon": 99.2,
    "coverage_area_km": 10.24,  # Standard Sentinel-2 tile size
}


class BatangToruGridMapper:
    """Maps between Batang Toru 10x10 grid and Sentinel-2 32x32 grid system."""
    
    def __init__(self):
        """Initialize the grid mapper with Batang Toru configuration."""
        self.grid_config = GRID_CONFIG
        self.sentinel_config = BATANG_TORU_SENTINEL_CONFIG
        self.grid_calculator = GridCalculator(grid_size=32, tile_size=32)
        logger.info(f"Initialized Batang Toru grid mapper for tile {self.sentinel_config['tile_id']}")
    
    def batang_toru_cell_to_gps(self, grid_x: int, grid_y: int) -> Tuple[float, float, float, float]:
        """
        Convert a single Batang Toru grid cell to GPS coordinates.
        
        Args:
            grid_x: X coordinate in Batang Toru grid (0-9)
            grid_y: Y coordinate in Batang Toru grid (0-9)
            
        Returns:
            Tuple of (north, south, east, west) GPS coordinates
        """
        return grid_to_gps_coordinates(grid_x, grid_y, grid_x, grid_y)
    
    def batang_toru_area_to_gps(self, southwest_x: int, southwest_y: int, 
                               northeast_x: int, northeast_y: int) -> Tuple[float, float, float, float]:
        """
        Convert Batang Toru grid area to GPS coordinates.
        
        Args:
            southwest_x, southwest_y: Southwest corner grid coordinates
            northeast_x, northeast_y: Northeast corner grid coordinates
            
        Returns:
            Tuple of (north, south, east, west) GPS coordinates
        """
        return grid_to_gps_coordinates(southwest_x, southwest_y, northeast_x, northeast_y)
    
    def gps_to_sentinel_tiles(self, north: float, south: float, east: float, west: float) -> List[str]:
        """
        Determine which Sentinel-2 tiles overlap with the given GPS area.
        
        Args:
            north, south, east, west: GPS boundaries
            
        Returns:
            List of Sentinel-2 tile IDs that overlap with the area
        """
        # For Batang Toru area, we primarily use the 47NQH tile
        # In a real implementation, you might need to check multiple tiles
        # for areas that cross tile boundaries
        
        # Check if the area is within our expected Batang Toru coverage
        batang_toru_bounds = self.grid_config["boundaries"]
        
        # Simple overlap check
        if (south <= batang_toru_bounds["north"] and north >= batang_toru_bounds["south"] and
            west <= batang_toru_bounds["east"] and east >= batang_toru_bounds["west"]):
            return [self.sentinel_config["tile_id"]]
        
        logger.warning(f"GPS area ({north}, {south}, {east}, {west}) is outside Batang Toru coverage")
        return []
    
    def batang_toru_claim_to_sentinel_tiles(self, southwest_x: int, southwest_y: int,
                                          northeast_x: int, northeast_y: int) -> List[str]:
        """
        Map a Batang Toru grid claim to required Sentinel-2 tiles.
        
        Args:
            southwest_x, southwest_y: Southwest corner of claim
            northeast_x, northeast_y: Northeast corner of claim
            
        Returns:
            List of Sentinel-2 tile IDs needed for processing
        """
        # Convert claim to GPS coordinates
        gps_north, gps_south, gps_east, gps_west = self.batang_toru_area_to_gps(
            southwest_x, southwest_y, northeast_x, northeast_y
        )
        
        # Get required Sentinel-2 tiles
        sentinel_tiles = self.gps_to_sentinel_tiles(gps_north, gps_south, gps_east, gps_west)
        
        logger.info(f"Batang Toru claim ({southwest_x},{southwest_y}) to ({northeast_x},{northeast_y}) "
                   f"requires Sentinel-2 tiles: {sentinel_tiles}")
        
        return sentinel_tiles
    
    def calculate_processing_area(self, claim_gps: Tuple[float, float, float, float]) -> Dict:
        """
        Calculate the processing area within Sentinel-2 imagery for a GPS claim area.
        
        Args:
            claim_gps: Tuple of (north, south, east, west) GPS coordinates
            
        Returns:
            Dictionary with processing area details
        """
        north, south, east, west = claim_gps
        
        # Calculate area dimensions
        lat_diff = north - south
        lon_diff = east - west
        
        # Rough conversion to meters (at equator: 1 degree ≈ 111km)
        # At 1.2°N latitude, longitude is slightly compressed
        lat_factor = 111000  # meters per degree latitude
        lon_factor = 111000 * math.cos(math.radians(1.2))  # adjust for latitude
        
        height_m = lat_diff * lat_factor
        width_m = lon_diff * lon_factor
        
        return {
            "gps_bounds": {
                "north": north,
                "south": south, 
                "east": east,
                "west": west
            },
            "dimensions_m": {
                "width": width_m,
                "height": height_m
            },
            "area_km2": (width_m * height_m) / 1_000_000,
            "sentinel_tiles": self.gps_to_sentinel_tiles(north, south, east, west),
            "center_point": {
                "lat": (north + south) / 2,
                "lon": (east + west) / 2
            }
        }
    
    def get_download_config_for_claim(self, southwest_x: int, southwest_y: int,
                                    northeast_x: int, northeast_y: int) -> Dict:
        """
        Generate download configuration for a specific claim.
        
        Args:
            southwest_x, southwest_y: Southwest corner of claim
            northeast_x, northeast_y: Northeast corner of claim
            
        Returns:
            Dictionary with download configuration
        """
        # Get GPS coordinates
        gps_coords = self.batang_toru_area_to_gps(southwest_x, southwest_y, northeast_x, northeast_y)
        
        # Get required tiles
        sentinel_tiles = self.batang_toru_claim_to_sentinel_tiles(
            southwest_x, southwest_y, northeast_x, northeast_y
        )
        
        # Calculate processing area
        processing_area = self.calculate_processing_area(gps_coords)
        
        return {
            "tile_ids": sentinel_tiles,
            "processing_area": processing_area,
            "bands": ["B04", "B08"],  # Red and NIR for NDVI
            "date_range": {
                "start": "2024-01-01",  # Use recent data
                "end": "2024-12-31"
            },
            "cloud_cover_max": 20,  # Maximum cloud cover percentage
            "s3_bucket": "sentinel-s2-l2a",
            "utm_zone": self.sentinel_config["utm_zone"],
            "grid_square": self.sentinel_config["grid_square"]
        }
    
    def validate_claim_coverage(self, southwest_x: int, southwest_y: int,
                              northeast_x: int, northeast_y: int) -> Tuple[bool, str]:
        """
        Validate that a claim is within our Batang Toru coverage area.
        
        Args:
            southwest_x, southwest_y: Southwest corner of claim
            northeast_x, northeast_y: Northeast corner of claim
            
        Returns:
            Tuple of (is_valid, message)
        """
        # Check grid coordinates are valid
        if not all(0 <= coord <= 9 for coord in [southwest_x, southwest_y, northeast_x, northeast_y]):
            return False, "Grid coordinates must be between 0 and 9"
        
        # Check that northeast is actually northeast of southwest
        if northeast_x <= southwest_x or northeast_y <= southwest_y:
            return False, "Northeast corner must be northeast of southwest corner"
        
        # Get GPS coordinates
        gps_coords = self.batang_toru_area_to_gps(southwest_x, southwest_y, northeast_x, northeast_y)
        
        # Check if we have Sentinel-2 coverage
        sentinel_tiles = self.gps_to_sentinel_tiles(*gps_coords)
        if not sentinel_tiles:
            return False, "Claim area is outside Batang Toru Sentinel-2 coverage"
        
        return True, "Claim is valid and within coverage area"


# Global instance for easy access
batang_toru_mapper = BatangToruGridMapper()


def get_claim_download_config(southwest_x: int, southwest_y: int,
                            northeast_x: int, northeast_y: int) -> Optional[Dict]:
    """
    Convenience function to get download configuration for a claim.
    
    Args:
        southwest_x, southwest_y: Southwest corner of claim
        northeast_x, northeast_y: Northeast corner of claim
        
    Returns:
        Download configuration dictionary or None if claim is invalid
    """
    is_valid, message = batang_toru_mapper.validate_claim_coverage(
        southwest_x, southwest_y, northeast_x, northeast_y
    )
    
    if not is_valid:
        logger.error(f"Invalid claim: {message}")
        return None
    
    return batang_toru_mapper.get_download_config_for_claim(
        southwest_x, southwest_y, northeast_x, northeast_y
    ) 