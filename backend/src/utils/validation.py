"""
Validation utilities for land claims and grid operations.
"""
import math
from typing import Tuple

# Fixed import - using absolute path
from backend.src.config import GRID_CONFIG, CLAIM_VALIDATION


def grid_to_gps_coordinates(southwest_x: int, southwest_y: int, northeast_x: int, northeast_y: int) -> Tuple[float, float, float, float]:
    """
    Convert corner points from 0-9 grid coordinates to real GPS coordinates
    
    Args:
        southwest_x, southwest_y: Southwest corner grid coordinates (0-9)
        northeast_x, northeast_y: Northeast corner grid coordinates (0-9)
        
    Returns:
        Tuple of (gps_north, gps_south, gps_east, gps_west) in decimal degrees
    """
    grid_bounds = GRID_CONFIG["boundaries"]
    
    # Calculate grid dimensions in degrees
    total_lat_range = grid_bounds["north"] - grid_bounds["south"]  # Total latitude span
    total_lon_range = grid_bounds["east"] - grid_bounds["west"]    # Total longitude span
    
    # Each grid cell size in degrees
    cell_lat_size = total_lat_range / 10  # 10x10 grid
    cell_lon_size = total_lon_range / 10
    
    # Convert grid coordinates to GPS coordinates
    # Grid Y: 0 = southernmost, 9 = northernmost
    gps_south = grid_bounds["south"] + (southwest_y * cell_lat_size)
    gps_north = grid_bounds["south"] + ((northeast_y + 1) * cell_lat_size)
    
    # Grid X: 0 = westernmost, 9 = easternmost  
    gps_west = grid_bounds["west"] + (southwest_x * cell_lon_size)
    gps_east = grid_bounds["west"] + ((northeast_x + 1) * cell_lon_size)
    
    return gps_north, gps_south, gps_east, gps_west


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth
    Returns distance in kilometers
    """
    R = 6371  # Earth's radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c


def calculate_claim_area_km2(north: float, south: float, east: float, west: float) -> float:
    """
    Calculate the area of a rectangular claim in km²
    Uses haversine distance for more accurate area calculation
    """
    # Calculate width (east-west distance) at the center latitude
    center_lat = (north + south) / 2
    width_km = haversine_distance(center_lat, west, center_lat, east)
    
    # Calculate height (north-south distance)
    height_km = haversine_distance(south, (east + west) / 2, north, (east + west) / 2)
    
    return width_km * height_km


def calculate_affected_tiles(north: float, south: float, east: float, west: float) -> int:
    """
    Calculate which grid tiles are affected by a land claim (using GPS coordinates)
    Returns the number of tiles that intersect with the claim area
    """
    grid_bounds = GRID_CONFIG["boundaries"]
    
    # Calculate grid dimensions
    grid_width = grid_bounds["east"] - grid_bounds["west"]
    grid_height = grid_bounds["north"] - grid_bounds["south"]
    
    # Each grid cell size in degrees
    cell_width = grid_width / 10  # 10x10 grid
    cell_height = grid_height / 10
    
    # Find which tiles the claim intersects
    start_col = max(0, int((west - grid_bounds["west"]) / cell_width))
    end_col = min(9, int((east - grid_bounds["west"]) / cell_width))
    start_row = max(0, int((south - grid_bounds["south"]) / cell_height))
    end_row = min(9, int((north - grid_bounds["south"]) / cell_height))
    
    # Count affected tiles
    affected_tiles = (end_col - start_col + 1) * (end_row - start_row + 1)
    
    return max(1, affected_tiles)  # At least 1 tile


def validate_grid_coordinates(southwest_x: int, southwest_y: int, northeast_x: int, northeast_y: int) -> Tuple[bool, str]:
    """
    Validate corner point grid coordinates
    Returns (is_valid, error_message)
    """
    # Check if coordinates are within 0-9 range
    if not (0 <= southwest_x <= 9):
        return False, f"Southwest X coordinate must be 0-9, got {southwest_x}"
    
    if not (0 <= southwest_y <= 9):
        return False, f"Southwest Y coordinate must be 0-9, got {southwest_y}"
        
    if not (0 <= northeast_x <= 9):
        return False, f"Northeast X coordinate must be 0-9, got {northeast_x}"
        
    if not (0 <= northeast_y <= 9):
        return False, f"Northeast Y coordinate must be 0-9, got {northeast_y}"
    
    # Check rectangle dimensions make sense
    if northeast_x <= southwest_x:
        return False, "Northeast X must be greater than southwest X"
    
    if northeast_y <= southwest_y:
        return False, "Northeast Y must be greater than southwest Y"
    
    return True, "Valid grid coordinates"


def validate_claim_bounds(north: float, south: float, east: float, west: float) -> Tuple[bool, str]:
    """
    Validate that a land claim is within acceptable parameters (GPS coordinates)
    Returns (is_valid, error_message)
    """
    grid_bounds = GRID_CONFIG["boundaries"]
    
    # Check if claim is within grid boundaries
    if (north > grid_bounds["north"] or south < grid_bounds["south"] or
        east > grid_bounds["east"] or west < grid_bounds["west"]):
        return False, "Claim must be within the predefined grid coverage area"
    
    # Check claim dimensions
    if north <= south:
        return False, "North boundary must be greater than south boundary"
    
    if east <= west:
        return False, "East boundary must be greater than west boundary"
    
    return True, "Valid claim" 