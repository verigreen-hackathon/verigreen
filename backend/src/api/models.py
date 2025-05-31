from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
import re
from config import GRID_CONFIG


class GridPoint(BaseModel):
    """A point in the 0-9 grid coordinate system"""
    x: int = Field(..., description="Grid X coordinate (0-9, where 0=west, 9=east)", ge=0, le=9)
    y: int = Field(..., description="Grid Y coordinate (0-9, where 0=south, 9=north)", ge=0, le=9)


class GridBounds(BaseModel):
    """Rectangle defined by southwest and northeast corner points"""
    southwest: GridPoint = Field(..., description="Southwest corner of the rectangular claim")
    northeast: GridPoint = Field(..., description="Northeast corner of the rectangular claim")

    @validator('northeast')
    def validate_rectangle(cls, v, values):
        if 'southwest' in values:
            sw = values['southwest']
            if v.x <= sw.x:
                raise ValueError('Northeast X must be greater than southwest X')
            if v.y <= sw.y:
                raise ValueError('Northeast Y must be greater than southwest Y')
        return v


class LandClaimRequest(BaseModel):
    """Request model for land claim endpoint"""
    owner_wallet: str = Field(..., description="Ethereum wallet address") 
    claim_bounds: GridBounds = Field(..., description="Rectangular claim area defined by two corner points")

    @validator('owner_wallet')
    def validate_wallet_address(cls, v):
        # Basic Ethereum address validation
        if not re.match(r'^0x[a-fA-F0-9]{40}$', v):
            raise ValueError('Invalid Ethereum wallet address format')
        return v.lower()  # Normalize to lowercase


class LandClaimResponse(BaseModel):
    """Response model for successful land claim"""
    claim_id: str = Field(..., description="Unique claim identifier")
    status: str = Field(..., description="Claim status")
    tiles_affected: int = Field(..., description="Number of grid tiles affected by this claim")
    claim_area_km2: float = Field(..., description="Area of this specific claim in square kilometers")
    estimated_completion_time: str = Field(..., description="Estimated processing completion time")
    filecoin_hash: Optional[str] = Field(None, description="Filecoin CID (pending until processing complete)")
    owner_wallet: str = Field(..., description="Owner's wallet address")
    
    # Grid coordinates (user-friendly)
    grid_bounds: GridBounds = Field(..., description="Corner points used in the request")
    
    # GPS coordinates (internal/technical)
    gps_bounds: dict = Field(..., description="Converted GPS coordinates for internal processing")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Grid context information
    grid_info: dict = Field(default_factory=lambda: {
        "total_grid_tiles": GRID_CONFIG["total_tiles"],
        "grid_coverage_km": GRID_CONFIG["total_area_km"],
        "tile_size_m": GRID_CONFIG["tile_size_meters"],
        "coordinate_system": "Two corner points: southwest (x,y) to northeast (x,y)"
    })


class LandClaimError(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message") 
    details: Optional[dict] = Field(None, description="Additional error details")


# ============================================================================
# NEW GLOBAL FOREST MONITORING MODELS
# ============================================================================

class GlobalForestRequest(BaseModel):
    """Request model for global forest monitoring endpoint"""
    bounding_box: List[float] = Field(
        ..., 
        description="Bounding box coordinates as [west, south, east, north] in decimal degrees",
        min_items=4,
        max_items=4
    )
    wallet_address: str = Field(..., description="Ethereum wallet address for data access")

    @validator('bounding_box')
    def validate_bounding_box(cls, v):
        if len(v) != 4:
            raise ValueError('Bounding box must contain exactly 4 coordinates: [west, south, east, north]')
        
        west, south, east, north = v
        
        # Validate longitude ranges
        if not (-180 <= west <= 180):
            raise ValueError(f'West longitude must be between -180 and 180, got {west}')
        if not (-180 <= east <= 180):
            raise ValueError(f'East longitude must be between -180 and 180, got {east}')
        
        # Validate latitude ranges
        if not (-90 <= south <= 90):
            raise ValueError(f'South latitude must be between -90 and 90, got {south}')
        if not (-90 <= north <= 90):
            raise ValueError(f'North latitude must be between -90 and 90, got {north}')
        
        # Validate bounding box logic
        if west >= east:
            raise ValueError(f'West longitude ({west}) must be less than east longitude ({east})')
        if south >= north:
            raise ValueError(f'South latitude ({south}) must be less than north latitude ({north})')
        
        # Check for reasonable bounding box size (prevent extremely large requests)
        lat_diff = north - south
        lon_diff = east - west
        if lat_diff > 10 or lon_diff > 10:
            raise ValueError('Bounding box too large. Maximum allowed size is 10 degrees in any direction.')
        
        return v

    @validator('wallet_address')
    def validate_wallet_address(cls, v):
        # Basic Ethereum address validation
        if not re.match(r'^0x[a-fA-F0-9]{40}$', v):
            raise ValueError('Invalid Ethereum wallet address format')
        return v.lower()  # Normalize to lowercase


class ForestTile(BaseModel):
    """Individual tile in the 10x10 forest grid"""
    tile_id: str = Field(..., description="Unique identifier for this tile (e.g., 'tile_0_0')")
    x: int = Field(..., description="X coordinate in the 10x10 grid (0-9)", ge=0, le=9)
    y: int = Field(..., description="Y coordinate in the 10x10 grid (0-9)", ge=0, le=9)
    health_score: float = Field(..., description="Forest health score (0.0-1.0)", ge=0.0, le=1.0)
    ndvi: float = Field(..., description="Normalized Difference Vegetation Index (-1.0 to 1.0)", ge=-1.0, le=1.0)
    coordinates: List[float] = Field(
        ..., 
        description="Geographic coordinates of tile center [longitude, latitude]",
        min_items=2,
        max_items=2
    )


class GlobalForestResponse(BaseModel):
    """Response model for global forest monitoring analysis"""
    analysis_id: str = Field(..., description="Unique identifier for this analysis")
    status: str = Field(..., description="Analysis status")
    forest_grid: List[ForestTile] = Field(
        ..., 
        description="Array of 100 forest tiles (10x10 grid)",
        min_items=100,
        max_items=100
    )
    filecoin_cid: Optional[str] = Field(None, description="Filecoin Content Identifier for the processed data")
    processing_time: float = Field(..., description="Processing time in seconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Analysis timestamp")
    bounding_box: List[float] = Field(..., description="Original bounding box coordinates")
    wallet_address: str = Field(..., description="Wallet address that requested the analysis")
    
    # Metadata
    metadata: dict = Field(default_factory=lambda: {
        "grid_size": "10x10",
        "total_tiles": 100,
        "coordinate_system": "WGS84",
        "data_source": "Sentinel-2",
        "api_version": "2.0.0"
    })

    @validator('forest_grid')
    def validate_grid_size(cls, v):
        if len(v) != 100:
            raise ValueError('Forest grid must contain exactly 100 tiles (10x10)')
        return v 