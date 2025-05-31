from fastapi import APIRouter, HTTPException, status
from backend.src.api.models import LandClaimRequest, LandClaimResponse, LandClaimError
from backend.src.utils.validation import (
    validate_grid_coordinates,
    grid_to_gps_coordinates,
    calculate_claim_area_km2,
    calculate_affected_tiles
)
from backend.src.utils.database import store_claim, get_claim, get_all_claims
from datetime import datetime, timedelta
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/land/claim", response_model=LandClaimResponse)
async def create_land_claim(request: LandClaimRequest):
    """
    Create a new land claim using corner point coordinates
    
    Grid coordinate system:
    - 0-9 for both X (west-east) and Y (south-north) 
    - (0,0) = southwest corner, (9,9) = northeast corner
    - Example: claim from southwest (3,5) to northeast (7,8)
    """
    claim_id = str(uuid.uuid4())
    
    try:
        logger.info(f"Processing land claim {claim_id} for wallet {request.owner_wallet}")
        
        # Extract corner coordinates
        southwest = request.claim_bounds.southwest
        northeast = request.claim_bounds.northeast
        
        # Validate grid coordinates
        grid_valid, grid_msg = validate_grid_coordinates(
            southwest.x, southwest.y, northeast.x, northeast.y
        )
        if not grid_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "invalid_grid_coordinates", "message": grid_msg}
            )
        
        # Convert grid coordinates to GPS coordinates
        gps_north, gps_south, gps_east, gps_west = grid_to_gps_coordinates(
            southwest.x, southwest.y, northeast.x, northeast.y
        )
        
        # Calculate claim metrics using GPS coordinates
        claim_area_km2 = calculate_claim_area_km2(gps_north, gps_south, gps_east, gps_west)
        affected_tiles = calculate_affected_tiles(gps_north, gps_south, gps_east, gps_west)
        
        # Create claim data
        claim_data = {
            "claim_id": claim_id,
            "status": "pending_processing",
            "owner_wallet": request.owner_wallet,
            
            # Store both grid and GPS coordinates
            "grid_bounds": {
                "southwest": {"x": southwest.x, "y": southwest.y},
                "northeast": {"x": northeast.x, "y": northeast.y}
            },
            "gps_bounds": {
                "north": gps_north,
                "south": gps_south,
                "east": gps_east,
                "west": gps_west
            },
            
            "claim_area_km2": claim_area_km2,
            "tiles_affected": affected_tiles,
            "created_at": datetime.utcnow().isoformat(),
            "estimated_completion": (datetime.utcnow() + timedelta(minutes=5)).isoformat(),
            "filecoin_hash": None  # Will be updated when processing completes
        }
        
        # Store claim
        store_claim(claim_data)
        logger.info(f"Successfully created claim {claim_id} from ({southwest.x},{southwest.y}) to ({northeast.x},{northeast.y})")
        
        # Return response
        return LandClaimResponse(
            claim_id=claim_id,
            status="pending_processing",
            tiles_affected=affected_tiles,
            claim_area_km2=claim_area_km2,
            estimated_completion_time="5 minutes",
            owner_wallet=request.owner_wallet,
            grid_bounds=request.claim_bounds,
            gps_bounds={
                "north": gps_north,
                "south": gps_south,
                "east": gps_east,
                "west": gps_west
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create claim {claim_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "processing_failed", "message": "Failed to process land claim"}
        )


@router.get("/land/claim/{claim_id}")
async def get_land_claim_status(claim_id: str):
    """
    Get the status of a specific land claim
    """
    try:
        claim = get_claim(claim_id)
        if not claim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "claim_not_found", "message": f"Claim {claim_id} not found"}
            )
        
        return claim
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve claim {claim_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "retrieval_failed", "message": "Failed to retrieve claim status"}
        )


@router.get("/land/claims")
async def list_all_claims():
    """
    List all land claims (for demo purposes)
    """
    try:
        claims = get_all_claims()
        return {
            "total_claims": len(claims),
            "claims": claims,
            "grid_info": {
                "coordinate_system": "Corner points: southwest (x,y) to northeast (x,y)",
                "grid_size": "10x10 tiles",
                "coverage_area": "6.4km x 6.4km",
                "tile_size": "640m x 640m"
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to list claims: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "listing_failed", "message": "Failed to retrieve claims list"}
        ) 