from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
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
# SIMPLIFIED GLOBAL FOREST MONITORING MODELS
# ============================================================================

class GlobalForestRequest(BaseModel):
    """Request model for global forest analysis"""
    bounding_box: List[float] = Field(
        description="Global coordinates [west, south, east, north] in decimal degrees",
        example=[-60.0, -3.0, -59.5, -2.5]
    )
    wallet_address: str = Field(
        description="User's wallet address for verification",
        example="0x742d35Cc6634C0532925a3b8D364B4a456fA4D42"
    )
    
    @validator('bounding_box')
    def validate_coordinates(cls, v):
        if len(v) != 4:
            raise ValueError('Bounding box must contain exactly 4 coordinates [west, south, east, north]')
        
        west, south, east, north = v
        
        # Validate longitude range
        if not (-180 <= west <= 180) or not (-180 <= east <= 180):
            raise ValueError('Longitude must be between -180 and 180 degrees')
        
        # Validate latitude range
        if not (-90 <= south <= 90) or not (-90 <= north <= 90):
            raise ValueError('Latitude must be between -90 and 90 degrees')
        
        # Validate bounding box logic
        if west >= east:
            raise ValueError('West coordinate must be less than east coordinate')
        if south >= north:
            raise ValueError('South coordinate must be less than north coordinate')
        
        return v


class ForestTile(BaseModel):
    """Individual forest tile in the 10x10 grid"""
    tile_id: int = Field(description="Numeric tile identifier (0-99)")
    x: int = Field(description="Grid X coordinate (0-9)", ge=0, le=9)
    y: int = Field(description="Grid Y coordinate (0-9)", ge=0, le=9)
    health_score: float = Field(
        description="Normalized health score (0-1)",
        example=0.85,
        ge=0, le=1
    )
    ndvi: float = Field(
        description="Mean NDVI value (-1 to 1)",
        example=0.78,
        ge=-1, le=1
    )
    coordinates: List[float] = Field(
        description="Center coordinates [lat, lon]",
        example=[45.123, -122.456]
    )


class GlobalForestResponse(BaseModel):
    """Simplified response model for global forest analysis"""
    
    forest_grid: List[ForestTile] = Field(
        description="Array of 100 forest tiles in 10x10 grid",
        min_items=100,
        max_items=100
    )
    
    filecoin_cid: Optional[str] = Field(
        description="Filecoin CID for permanent storage",
        example="bafybeig...",
        default=None
    )
    
    processing_time: str = Field(
        description="Processing time with units",
        example="1.13s"
    )
    
    timestamp: str = Field(
        description="ISO timestamp of completion",
        example="2025-05-31T19:43:44Z"
    )
    
    @validator('forest_grid')
    def validate_grid_size(cls, v):
        if len(v) != 100:
            raise ValueError('Forest grid must contain exactly 100 tiles')
        return v 