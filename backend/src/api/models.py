from pydantic import BaseModel, Field, validator
from typing import Optional
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