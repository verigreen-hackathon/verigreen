from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from api.models import (
    LandClaimRequest, LandClaimResponse, LandClaimError,
    GlobalForestRequest, GlobalForestResponse, ForestTile
)
from utils.validation import (
    validate_grid_coordinates,
    grid_to_gps_coordinates,
    calculate_claim_area_km2,
    calculate_affected_tiles
)
from utils.database import store_claim, get_claim, get_all_claims
from processing.claim_processor import ClaimProcessor, ProcessingResult
from sentinel.batang_toru_mapper import get_claim_download_config
from sentinel.grid import GlobalGridCalculator, GridError
from datetime import datetime, timedelta
import uuid
import logging
import asyncio
import time

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize the claim processor and global grid calculator
claim_processor = ClaimProcessor()
global_grid_calculator = GlobalGridCalculator()


# ============================================================================
# NEW GLOBAL FOREST MONITORING API
# ============================================================================

@router.post("/forest/analyze", response_model=GlobalForestResponse)
async def analyze_global_forest(request: GlobalForestRequest):
    """
    Analyze forest health for any global bounding box coordinates.
    
    This endpoint accepts a bounding box in decimal degrees and returns a 10x10 grid
    of forest health scores based on satellite imagery analysis.
    
    Args:
        request: GlobalForestRequest containing:
            - bounding_box: [west, south, east, north] in decimal degrees
            - wallet_address: Ethereum wallet for data access
    
    Returns:
        GlobalForestResponse with 100 forest tiles containing health scores
    """
    analysis_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        logger.info(f"Starting global forest analysis {analysis_id} for bounding box {request.bounding_box}")
        
        # Validate coordinates using our GlobalGridCalculator
        is_valid, error_msg = global_grid_calculator.validate_global_coordinates(request.bounding_box)
        if not is_valid:
            logger.warning(f"Invalid coordinates for analysis {analysis_id}: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "invalid_coordinates",
                    "message": error_msg,
                    "analysis_id": analysis_id
                }
            )
        
        # Generate the 10x10 grid using GlobalGridCalculator
        try:
            global_tiles = global_grid_calculator.calculate_global_grid(request.bounding_box)
        except GridError as e:
            logger.error(f"Grid calculation failed for analysis {analysis_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "grid_calculation_failed",
                    "message": str(e),
                    "analysis_id": analysis_id
                }
            )
        
        # Calculate area statistics
        area_stats = global_grid_calculator.calculate_grid_area_km2(request.bounding_box)
        logger.info(f"Grid covers {area_stats['total_area_km2']} km² with {area_stats['tile_area_km2']} km² per tile")
        
        # Convert GlobalTileCoordinates to ForestTile objects with mock NDVI data
        # TODO: In the next subtasks, we'll replace this with real Sentinel-2 processing
        forest_grid = []
        
        for global_tile in global_tiles:
            # Mock forest health calculation (will be replaced with real NDVI processing)
            # Generate varied but realistic values based on geographic position
            mock_ndvi = 0.3 + (0.4 * ((global_tile.grid_x + global_tile.grid_y) % 7) / 6)  # NDVI between 0.3-0.7
            mock_health_score = min(1.0, max(0.0, mock_ndvi + 0.1))  # Health score 0.4-0.8
            
            forest_tile = ForestTile(
                tile_id=global_tile.tile_id,
                x=global_tile.grid_x,
                y=global_tile.grid_y,
                health_score=round(mock_health_score, 3),
                ndvi=round(mock_ndvi, 3),
                coordinates=[
                    round(global_tile.center_lat_lon[1], 6),  # longitude
                    round(global_tile.center_lat_lon[0], 6)   # latitude
                ]
            )
            forest_grid.append(forest_tile)
        
        processing_time = time.time() - start_time
        
        # Get estimated MGRS tiles for future Sentinel-2 integration
        mgrs_tiles = global_grid_calculator.get_sentinel_mgrs_tiles(request.bounding_box)
        logger.info(f"Analysis {analysis_id} would require MGRS tiles: {mgrs_tiles}")
        
        # Create response
        response = GlobalForestResponse(
            analysis_id=analysis_id,
            status="completed",
            forest_grid=forest_grid,
            filecoin_cid=None,  # Will be populated when Filecoin integration is implemented
            processing_time=round(processing_time, 3),
            bounding_box=request.bounding_box,
            wallet_address=request.wallet_address
        )
        
        # Add area statistics and other metadata
        response.metadata = {
            "grid_size": "10x10",
            "total_tiles": 100,
            "coordinate_system": "WGS84",
            "data_source": "Sentinel-2",
            "api_version": "2.0.0",
            "area_statistics": area_stats,
            "estimated_mgrs_tiles": mgrs_tiles,
            "grid_calculator": "GlobalGridCalculator",
            "coordinate_validation": "passed"
        }
        
        logger.info(f"Completed global forest analysis {analysis_id} in {processing_time:.3f} seconds")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process global forest analysis {analysis_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "analysis_failed", 
                "message": "Failed to process global forest analysis",
                "analysis_id": analysis_id
            }
        )


# ============================================================================
# EXISTING LAND CLAIM API (Legacy)
# ============================================================================

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


# ============================================================================
# NEW API INTEGRATION LAYER - Batang Toru Processing Endpoints
# ============================================================================

@router.post("/land/claim/{claim_id}/process")
async def trigger_claim_processing(claim_id: str, background_tasks: BackgroundTasks):
    """
    Trigger satellite image processing for a specific land claim.
    
    This endpoint initiates the complete processing pipeline:
    1. Downloads Sentinel-2 data for the claimed Batang Toru area
    2. Slices imagery into tiles
    3. Calculates NDVI for tropical rainforest monitoring
    4. Generates conservation metrics for Tapanuli orangutan habitat
    """
    try:
        # Get the claim data
        claim = get_claim(claim_id)
        if not claim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "claim_not_found", "message": f"Claim {claim_id} not found"}
            )
        
        # Check if claim is already being processed
        if claim.get("status") == "processing":
            return {
                "message": "Processing already in progress",
                "claim_id": claim_id,
                "status": "processing"
            }
        
        # Update claim status to processing
        claim["status"] = "processing"
        claim["processing_started_at"] = datetime.utcnow().isoformat()
        store_claim(claim)
        
        # Add processing task to background
        grid_bounds = claim["grid_bounds"]
        background_tasks.add_task(
            process_claim_in_background,
            claim_id,
            grid_bounds["southwest"]["x"],
            grid_bounds["southwest"]["y"],
            grid_bounds["northeast"]["x"],
            grid_bounds["northeast"]["y"]
        )
        
        logger.info(f"Started background processing for claim {claim_id}")
        
        return {
            "message": "Processing started successfully",
            "claim_id": claim_id,
            "status": "processing",
            "estimated_completion": "2-5 minutes",
            "processing_stages": [
                "Downloading Sentinel-2 data for Batang Toru",
                "Slicing imagery into 10x10 grid tiles",
                "Calculating NDVI for forest health",
                "Generating conservation metrics",
                "Preparing data for Filecoin upload"
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start processing for claim {claim_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "processing_start_failed", "message": str(e)}
        )


@router.get("/land/claim/{claim_id}/processing-status")
async def get_processing_status(claim_id: str):
    """
    Get detailed processing status for a land claim including satellite data info.
    """
    try:
        claim = get_claim(claim_id)
        if not claim:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "claim_not_found", "message": f"Claim {claim_id} not found"}
            )
        
        # Get basic claim info
        response_data = {
            "claim_id": claim_id,
            "status": claim.get("status", "pending"),
            "grid_bounds": claim.get("grid_bounds"),
            "gps_bounds": claim.get("gps_bounds"),
            "claim_area_km2": claim.get("claim_area_km2"),
            "created_at": claim.get("created_at"),
            "processing_started_at": claim.get("processing_started_at"),
            "processing_completed_at": claim.get("processing_completed_at")
        }
        
        # Add satellite data configuration
        grid_bounds = claim["grid_bounds"]
        satellite_config = get_claim_download_config(
            grid_bounds["southwest"]["x"],
            grid_bounds["southwest"]["y"],
            grid_bounds["northeast"]["x"],
            grid_bounds["northeast"]["y"]
        )
        
        if satellite_config:
            response_data["satellite_data"] = {
                "sentinel_tiles": satellite_config["tile_ids"],
                "bands": satellite_config["bands"],
                "processing_area": satellite_config["processing_area"],
                "utm_zone": satellite_config["utm_zone"],
                "grid_square": satellite_config["grid_square"]
            }
        
        # Add processing results if available
        if "processing_result" in claim:
            processing_result = claim["processing_result"]
            response_data["processing_results"] = {
                "tiles_generated": processing_result.get("tiles_generated", 0),
                "mean_ndvi": processing_result.get("mean_ndvi", 0.0),
                "forest_health_score": processing_result.get("forest_health_score", 0.0),
                "conservation_metrics": processing_result.get("conservation_metrics", {}),
                "output_directory": processing_result.get("output_directory"),
                "processed_files": processing_result.get("processed_files", [])
            }
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get processing status for claim {claim_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "status_retrieval_failed", "message": str(e)}
        )


@router.get("/satellite/coverage/{grid_x}/{grid_y}")
async def get_satellite_coverage_info(grid_x: int, grid_y: int):
    """
    Get satellite coverage information for a specific Batang Toru grid cell.
    
    Args:
        grid_x: X coordinate in Batang Toru grid (0-9)
        grid_y: Y coordinate in Batang Toru grid (0-9)
    """
    try:
        # Validate coordinates
        if not (0 <= grid_x <= 9) or not (0 <= grid_y <= 9):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "invalid_coordinates", "message": "Grid coordinates must be 0-9"}
            )
        
        # Get satellite coverage for this cell (as 1x1 claim)
        coverage_config = get_claim_download_config(grid_x, grid_y, grid_x, grid_y)
        
        if not coverage_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "no_coverage", "message": "No satellite coverage for this area"}
            )
        
        return {
            "grid_cell": {"x": grid_x, "y": grid_y},
            "satellite_coverage": {
                "sentinel_tiles": coverage_config["tile_ids"],
                "bands_available": coverage_config["bands"],
                "utm_zone": coverage_config["utm_zone"],
                "grid_square": coverage_config["grid_square"],
                "processing_area": coverage_config["processing_area"]
            },
            "conservation_context": {
                "ecosystem": "Batang Toru",
                "location": "Sumatra, Indonesia", 
                "target_species": "Tapanuli orangutan (Pongo tapanuliensis)",
                "habitat_type": "Dense tropical rainforest",
                "elevation_range": "750-1,800m above sea level",
                "conservation_status": "Critically endangered habitat"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get satellite coverage for ({grid_x},{grid_y}): {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "coverage_retrieval_failed", "message": str(e)}
        )


@router.get("/processing/grid-mapping/{southwest_x}/{southwest_y}/{northeast_x}/{northeast_y}")
async def get_grid_mapping_info(southwest_x: int, southwest_y: int, northeast_x: int, northeast_y: int):
    """
    Get detailed grid mapping information for a claim area.
    Shows how Batang Toru 10x10 grid maps to Sentinel-2 32x32 system.
    """
    try:
        # Validate coordinates
        grid_valid, grid_msg = validate_grid_coordinates(southwest_x, southwest_y, northeast_x, northeast_y)
        if not grid_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "invalid_grid_coordinates", "message": grid_msg}
            )
        
        # Get GPS coordinates
        gps_north, gps_south, gps_east, gps_west = grid_to_gps_coordinates(
            southwest_x, southwest_y, northeast_x, northeast_y
        )
        
        # Get satellite mapping
        satellite_config = get_claim_download_config(southwest_x, southwest_y, northeast_x, northeast_y)
        
        return {
            "batang_toru_grid": {
                "southwest": {"x": southwest_x, "y": southwest_y},
                "northeast": {"x": northeast_x, "y": northeast_y},
                "cells_included": (northeast_x - southwest_x + 1) * (northeast_y - southwest_y + 1)
            },
            "gps_coordinates": {
                "north": gps_north,
                "south": gps_south,
                "east": gps_east,
                "west": gps_west
            },
            "sentinel_mapping": {
                "tile_ids": satellite_config["tile_ids"] if satellite_config else [],
                "utm_zone": satellite_config["utm_zone"] if satellite_config else None,
                "grid_square": satellite_config["grid_square"] if satellite_config else None,
                "processing_area": satellite_config["processing_area"] if satellite_config else None
            },
            "mapping_details": {
                "coordinate_system": "Batang Toru 10x10 grid → GPS coordinates → Sentinel-2 tiles",
                "tile_size": "640m x 640m per Batang Toru cell",
                "resolution": "10m per pixel (Sentinel-2 bands B04, B08)",
                "grid_system": "WGS84 geographic coordinates"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get grid mapping for claim area: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "mapping_retrieval_failed", "message": str(e)}
        )


# ============================================================================
# BACKGROUND PROCESSING FUNCTION
# ============================================================================

async def process_claim_in_background(claim_id: str, southwest_x: int, southwest_y: int, 
                                    northeast_x: int, northeast_y: int):
    """
    Background function to process a land claim with full satellite imagery pipeline.
    """
    try:
        logger.info(f"Starting background processing for claim {claim_id}")
        
        # Process the claim
        result = await claim_processor.process_claim(
            claim_id=claim_id,
            southwest_x=southwest_x,
            southwest_y=southwest_y,
            northeast_x=northeast_x,
            northeast_y=northeast_y
        )
        
        # Update claim with results
        claim = get_claim(claim_id)
        if claim:
            if result.success:
                claim["status"] = "completed"
                claim["processing_result"] = {
                    "tiles_generated": result.tiles_generated,
                    "mean_ndvi": result.mean_ndvi,
                    "forest_health_score": result.forest_health_score,
                    "conservation_metrics": result.conservation_metrics,
                    "output_directory": result.output_directory,
                    "processed_files": result.processed_files,
                    "processing_time": result.processing_time
                }
                logger.info(f"Successfully completed processing for claim {claim_id}")
            else:
                claim["status"] = "failed"
                claim["error_message"] = result.error_message
                logger.error(f"Processing failed for claim {claim_id}: {result.error_message}")
            
            claim["processing_completed_at"] = datetime.utcnow().isoformat()
            store_claim(claim)
    
    except Exception as e:
        # Update claim with error status
        claim = get_claim(claim_id)
        if claim:
            claim["status"] = "failed"
            claim["error_message"] = str(e)
            claim["processing_completed_at"] = datetime.utcnow().isoformat()
            store_claim(claim)
        
        logger.error(f"Background processing failed for claim {claim_id}: {str(e)}", exc_info=True) 